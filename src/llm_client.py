"""Thin Anthropic SDK wrapper with caching, cost logging, and retry."""

import hashlib
import json
import os
import time
import random
from datetime import datetime, UTC
from pathlib import Path

import anthropic

BASE = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE / "data/interim/llm_cache"
COST_LOG  = BASE / "reports/cost_log.md"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Pricing per million tokens (from Anthropic docs, April 2026)
PRICING = {
    "claude-haiku-4-5":          {"input": 1.00,  "output": 5.00},
    "claude-haiku-4-5-20251001": {"input": 1.00,  "output": 5.00},
    "claude-sonnet-4-6":         {"input": 3.00,  "output": 15.00},
}


def _est_cost(model: str, input_tok: int, output_tok: int) -> float:
    rates = PRICING.get(model, {"input": 0.0, "output": 0.0})
    return round(
        (input_tok / 1_000_000) * rates["input"]
        + (output_tok / 1_000_000) * rates["output"],
        6,
    )


def _cache_key(model: str, system: str, user_text: str) -> str:
    raw = json.dumps({"model": model, "system": system, "user": user_text},
                     ensure_ascii=False, sort_keys=True)
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
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    row = f"| {date} | {phase} | {task} | {model} | {input_tok} | {output_tok} | {cost:.6f} | {notes} |\n"
    with open(COST_LOG, "a") as f:
        f.write(row)


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
) -> dict:
    """
    Call the Anthropic API with caching and cost logging.

    Returns dict with keys: text, input_tokens, output_tokens, cost, from_cache.
    """
    key = _cache_key(model, system, user_text)
    cached = _load_cache(key)
    if cached:
        cached["from_cache"] = True
        return cached

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    last_exc = None
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
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
    input_tok  = response.usage.input_tokens
    output_tok = response.usage.output_tokens
    cost = _est_cost(model, input_tok, output_tok)

    result = {
        "text": text,
        "input_tokens": input_tok,
        "output_tokens": output_tok,
        "cost": cost,
        "from_cache": False,
    }
    _save_cache(key, result)
    _append_cost_log(phase, task, model, input_tok, output_tok, cost, notes)
    return result
