"""Thin Anthropic SDK wrapper with caching, cost logging, and retry."""

import asyncio
import hashlib
import json
import os
import time
import random
from datetime import datetime, timezone
from pathlib import Path

import anthropic

BASE = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE / "data/interim/llm_cache"
COST_LOG  = BASE / "reports/cost_log.md"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Pricing per million tokens (from Anthropic docs, May 2026)
PRICING = {
    "claude-haiku-4-5":          {"input": 1.00,  "output": 5.00,  "cache_write": 1.25,  "cache_read": 0.10},
    "claude-haiku-4-5-20251001": {"input": 1.00,  "output": 5.00,  "cache_write": 1.25,  "cache_read": 0.10},
    "claude-sonnet-4-6":         {"input": 3.00,  "output": 15.00, "cache_write": 3.75,  "cache_read": 0.30},
}


def _est_cost(model: str, input_tok: int, output_tok: int,
              cache_write_tok: int = 0, cache_read_tok: int = 0) -> float:
    rates = PRICING.get(model, {"input": 0.0, "output": 0.0, "cache_write": 0.0, "cache_read": 0.0})
    return round(
        (input_tok        / 1_000_000) * rates["input"]
        + (output_tok     / 1_000_000) * rates["output"]
        + (cache_write_tok / 1_000_000) * rates["cache_write"]
        + (cache_read_tok  / 1_000_000) * rates["cache_read"],
        6,
    )


def _cache_key(model: str, system: str, user_text: str, salt: str = "") -> str:
    raw = json.dumps(
        {"model": model, "system": system, "user": user_text, "salt": salt},
        ensure_ascii=False, sort_keys=True,
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def _load_cache(key: str):
    p = _cache_path(key)
    if p.exists():
        return json.loads(p.read_text())
    return None


def _save_cache(key: str, payload: dict):
    _cache_path(key).write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def _append_cost_log(phase: str, task: str, model: str,
                     input_tok: int, output_tok: int, cost: float, notes: str):
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    row = f"| {date} | {phase} | {task} | {model} | {input_tok} | {output_tok} | {cost:.6f} | {notes} |\n"
    with open(COST_LOG, "a") as f:
        f.write(row)


def _mark_cached(cached: dict) -> dict:
    cached["from_cache"] = True
    cached.setdefault("cache_write_tokens", 0)
    cached.setdefault("cache_read_tokens", 0)
    return cached


def _cache_hit_note(notes: str) -> str:
    return f"{notes} cached: true".strip()


def call(
    system: str,
    user_text: str,
    model: str = "claude-haiku-4-5",
    temperature: float = 0.1,
    max_tokens: int = 800,
    phase: str = "1",
    task: str = "open_coding",
    notes: str = "",
    max_retries: int = 4,
    use_prompt_cache: bool = False,
    salt: str = "",
) -> dict:
    """
    Call the Anthropic API with file caching, cost logging, and optional prompt caching.

    Args:
        use_prompt_cache: If True, sends the system prompt with cache_control so
            Anthropic's server caches it across calls (saves cost on repeated calls
            with the same large system prompt). Does not affect the file-cache key.
        salt: Appended to the file-cache key only. Use to force fresh API calls
            (e.g., reliability checks) while sending the same prompt content.

    Returns dict: text, input_tokens, output_tokens, cost, from_cache,
                  cache_write_tokens, cache_read_tokens.
    """
    key = _cache_key(model, system, user_text, salt)
    cached = _load_cache(key)
    if cached:
        cached = _mark_cached(cached)
        _append_cost_log(
            phase, task, model,
            cached.get("input_tokens", 0),
            cached.get("output_tokens", 0),
            0.0,
            _cache_hit_note(notes),
        )
        return cached

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Build system parameter — list format required for prompt caching
    if use_prompt_cache:
        system_param = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
    else:
        system_param = system

    last_exc = None
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_param,
                messages=[{"role": "user", "content": user_text}],
            )
            break
        except (anthropic.RateLimitError, anthropic.APIStatusError) as e:
            last_exc = e
            if isinstance(e, anthropic.APIStatusError) and e.status_code < 500:
                raise
            delay = min(2 ** attempt + random.uniform(0, 1), 60)
            time.sleep(delay)
    else:
        raise last_exc

    text = next((b.text for b in response.content if b.type == "text"), "")
    input_tok       = response.usage.input_tokens
    output_tok      = response.usage.output_tokens
    cache_write_tok = getattr(response.usage, "cache_creation_input_tokens", 0) or 0
    cache_read_tok  = getattr(response.usage, "cache_read_input_tokens", 0) or 0
    cost = _est_cost(model, input_tok, output_tok, cache_write_tok, cache_read_tok)

    cache_note = ""
    if cache_write_tok:
        cache_note = f" cache_write={cache_write_tok}"
    elif cache_read_tok:
        cache_note = f" cache_read={cache_read_tok}"

    result = {
        "text":               text,
        "input_tokens":       input_tok,
        "output_tokens":      output_tok,
        "cache_write_tokens": cache_write_tok,
        "cache_read_tokens":  cache_read_tok,
        "cost":               cost,
        "from_cache":         False,
    }
    _save_cache(key, result)
    _append_cost_log(phase, task, model, input_tok, output_tok, cost,
                     notes + cache_note)
    return result


# ── Async variant ──────────────────────────────────────────────────────────────

# Module-level lock so concurrent coroutines don't interleave cost-log writes.
_log_lock = asyncio.Lock()


async def async_call(
    system: str,
    user_text: str,
    model: str = "claude-haiku-4-5",
    temperature: float = 0.1,
    max_tokens: int = 800,
    phase: str = "1",
    task: str = "open_coding",
    notes: str = "",
    max_retries: int = 4,
    use_prompt_cache: bool = False,
    salt: str = "",
) -> dict:
    """
    Async version of call().  Uses AsyncAnthropic; file cache and cost log are
    identical to the sync version.  Safe to call from multiple concurrent coroutines
    — file-cache reads/writes are fast disk ops; cost-log appends are serialised
    via _log_lock.
    """
    key    = _cache_key(model, system, user_text, salt)
    cached = _load_cache(key)
    if cached:
        cached = _mark_cached(cached)
        async with _log_lock:
            _append_cost_log(
                phase, task, model,
                cached.get("input_tokens", 0),
                cached.get("output_tokens", 0),
                0.0,
                _cache_hit_note(notes),
            )
        return cached

    if use_prompt_cache:
        system_param = [{"type": "text", "text": system,
                         "cache_control": {"type": "ephemeral"}}]
    else:
        system_param = system

    client   = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    last_exc = None

    for attempt in range(max_retries):
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_param,
                messages=[{"role": "user", "content": user_text}],
            )
            break
        except (anthropic.RateLimitError, anthropic.APIStatusError) as e:
            last_exc = e
            if isinstance(e, anthropic.APIStatusError) and e.status_code < 500:
                raise
            delay = min(2 ** attempt + random.uniform(0, 1), 60)
            await asyncio.sleep(delay)
    else:
        raise last_exc

    text            = next((b.text for b in response.content if b.type == "text"), "")
    input_tok       = response.usage.input_tokens
    output_tok      = response.usage.output_tokens
    cache_write_tok = getattr(response.usage, "cache_creation_input_tokens", 0) or 0
    cache_read_tok  = getattr(response.usage, "cache_read_input_tokens", 0) or 0
    cost            = _est_cost(model, input_tok, output_tok,
                                cache_write_tok, cache_read_tok)

    cache_note = ""
    if cache_write_tok:
        cache_note = f" cache_write={cache_write_tok}"
    elif cache_read_tok:
        cache_note = f" cache_read={cache_read_tok}"

    result = {
        "text":               text,
        "input_tokens":       input_tok,
        "output_tokens":      output_tok,
        "cache_write_tokens": cache_write_tok,
        "cache_read_tokens":  cache_read_tok,
        "cost":               cost,
        "from_cache":         False,
    }
    _save_cache(key, result)

    async with _log_lock:
        _append_cost_log(phase, task, model, input_tok, output_tok, cost,
                         notes + cache_note)

    return result
