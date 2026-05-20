"""Phase 1 pipeline: Tasks 1–7. Saves all outputs; idempotent via LLM cache."""

import json
import os
import sys
import re
from dataclasses import asdict
from pathlib import Path
from collections import Counter

# Ensure project src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from threads import build_threads, stratified_sample, STUDY_WINDOWS
from llm_client import call

BASE = Path(__file__).resolve().parent.parent
INT  = BASE / "data/interim"
REP  = BASE / "reports"
PROMPTS = BASE / "prompts"

INT.mkdir(parents=True, exist_ok=True)

MINI_SAMPLE_PATH   = INT / "phase1_mini_sample.jsonl"
CODING_NOTES_PATH  = INT / "phase1_open_coding_notes.jsonl"
SCHEMA_PATH        = INT / "phase1_proposed_schema.json"
CHECKS_PATH        = INT / "phase1_schema_checks.json"
FAILURES_PATH      = INT / "phase1_coding_failures.jsonl"


# ─────────────────────────────────────────────
# Task 1 + 2 — Build eligible threads, sample
# ─────────────────────────────────────────────
def run_tasks_1_2():
    if MINI_SAMPLE_PATH.exists():
        print("Tasks 1+2: mini-sample already exists, loading.")
        sample = []
        with open(MINI_SAMPLE_PATH) as f:
            for line in f:
                sample.append(json.loads(line))
        return sample

    print("Task 1: Building author-thread units...")
    all_threads = {}
    for sub in ["investimentos", "farialimabets"]:
        print(f"  Streaming {sub}...")
        threads = build_threads(sub)
        all_threads[sub] = threads
        by_window = Counter(t.window for t in threads)
        print(f"  {sub}: {len(threads)} eligible threads | " +
              " | ".join(f"W{w}={by_window[w]}" for w in "ABC"))

    print("\nTask 2: Stratified mini-sample (50 per cell = 300 total)...")
    sample_records = []
    for sub in ["investimentos", "farialimabets"]:
        threads = all_threads[sub]
        for w in "ABC":
            cell = [t for t in threads if t.window == w]
            sampled = stratified_sample(cell, n=50, seed=42)
            print(f"  r/{sub} Window {w}: {len(cell)} eligible → {len(sampled)} sampled"
                  f" | mean unit_len={sum(len(t.unit_text) for t in sampled)//max(1,len(sampled))}"
                  f" | mean_comments={sum(t.num_comments for t in sampled)//max(1,len(sampled))}")
            for t in sampled:
                d = asdict(t)
                d["cell"] = f"{sub}_W{w}"
                sample_records.append(d)

    with open(MINI_SAMPLE_PATH, "w") as f:
        for r in sample_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n  → Saved {len(sample_records)} threads to phase1_mini_sample.jsonl")
    return sample_records


# ─────────────────────────────────────────────
# Task 3 — Open coding via Claude Haiku
# ─────────────────────────────────────────────
def run_task_3(sample_records):
    system_prompt = (PROMPTS / "01_open_coding.md").read_text()
    # Remove the {unit_text} placeholder line — system stays fixed, user gets unit
    system_clean = system_prompt.replace("{unit_text}", "").strip()
    # Actually: prompt has "Postagem:\n{unit_text}" at the end. Keep system as everything before that.
    # Split at "Postagem:"
    if "Postagem:" in system_clean:
        system_clean = system_clean[:system_clean.rfind("Postagem:")].strip()

    # Load already-coded notes
    coded_ids = set()
    if CODING_NOTES_PATH.exists():
        with open(CODING_NOTES_PATH) as f:
            for line in f:
                rec = json.loads(line)
                coded_ids.add(rec["thread_id"])

    failures = []
    total_cost = 0.0
    total_input = 0
    total_output = 0
    success = 0

    print(f"\nTask 3: Open coding ({len(sample_records)} threads, model=claude-haiku-4-5)")
    print(f"  Already coded: {len(coded_ids)}")

    with open(CODING_NOTES_PATH, "a") as out_f, \
         open(FAILURES_PATH, "a") as fail_f:

        for i, rec in enumerate(sample_records):
            tid = rec["thread_id"]
            if tid in coded_ids:
                success += 1
                continue

            unit_text = rec["unit_text"]
            user_msg  = f"Postagem:\n{unit_text}"

            parsed = None
            for attempt in range(2):
                result = call(
                    system=system_clean,
                    user_text=user_msg,
                    model="claude-haiku-4-5",
                    temperature=0.1,
                    max_tokens=800,
                    phase="1",
                    task="open_coding",
                    notes=f"{rec['subreddit']} W{rec['window']} {tid}",
                )
                total_cost   += result["cost"]
                total_input  += result["input_tokens"]
                total_output += result["output_tokens"]

                try:
                    raw = result["text"].strip()
                    # Strip markdown fences if present (safety)
                    raw = re.sub(r"^```[a-z]*\n?", "", raw)
                    raw = re.sub(r"\n?```$", "", raw)
                    parsed = json.loads(raw)
                    break
                except (json.JSONDecodeError, ValueError):
                    if attempt == 1:
                        failures.append({"thread_id": tid, "raw": result["text"]})
                        fail_f.write(json.dumps({"thread_id": tid, "raw": result["text"][:500]},
                                                ensure_ascii=False) + "\n")

            if parsed is not None:
                note_rec = {
                    "thread_id":   tid,
                    "subreddit":   rec["subreddit"],
                    "window":      rec["window"],
                    "created_utc": rec["created_utc"],
                    "open_coding": parsed,
                }
                out_f.write(json.dumps(note_rec, ensure_ascii=False) + "\n")
                success += 1
                coded_ids.add(tid)

            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(sample_records)}] coded={success} "
                      f"cost=${total_cost:.4f} input_tok={total_input:,}")

    print(f"\n  Total coded: {success}/{len(sample_records)}"
          f" | failures: {len(failures)}"
          f" | total_tokens: {total_input+total_output:,}"
          f" | total_cost: ${total_cost:.4f}")
    return success, len(failures), total_input, total_output, total_cost


# ─────────────────────────────────────────────
# Task 4 — Schema synthesis via Claude Sonnet
# ─────────────────────────────────────────────
def run_task_4():
    if SCHEMA_PATH.exists():
        print("\nTask 4: Schema already exists, loading.")
        return json.loads(SCHEMA_PATH.read_text())

    print("\nTask 4: Schema synthesis (model=claude-sonnet-4-6)...")

    # Load all coding notes
    notes = []
    with open(CODING_NOTES_PATH) as f:
        for line in f:
            notes.append(json.loads(line))

    # Build aggregated context — omit situacao_resumida to keep input tokens manageable
    entries = []
    for n in notes:
        oc = n["open_coding"]
        entries.append({
            "sub": n["subreddit"],
            "w":   n["window"],
            "dims": oc.get("dimensoes_observadas", []),
            "dor":  oc.get("dor_principal", "nenhuma"),
        })

    aggregated_notes = json.dumps(entries, ensure_ascii=False, separators=(",", ":"))

    synthesis_prompt = (PROMPTS / "02_schema_synthesis.md").read_text()
    system_clean     = synthesis_prompt[:synthesis_prompt.rfind("Notas de open coding")].strip()
    user_msg         = f"Notas de open coding ({len(notes)} entradas, campos: sub/w/dims/dor):\n{aggregated_notes}"

    result = call(
        system=system_clean,
        user_text=user_msg,
        model="claude-sonnet-4-6",
        temperature=0.3,
        max_tokens=8192,
        phase="1",
        task="schema_synthesis",
        notes=f"{len(notes)} open-coding notes",
    )

    raw = result["text"].strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    schema = json.loads(raw)
    SCHEMA_PATH.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
    print(f"  → Schema saved | fields={len(schema.get('fields',[]))}"
          f" | cost=${result['cost']:.4f}")
    return schema


# ─────────────────────────────────────────────
# Task 5 — Schema sanity checks
# ─────────────────────────────────────────────
def run_task_5(schema):
    print("\nTask 5: Schema sanity checks...")
    checks = {}
    fields = schema.get("fields", [])
    names  = [f.get("name","") for f in fields]

    # 1. Field count
    n = len(fields)
    checks["field_count"] = {
        "pass": 8 <= n <= 15,
        "value": n,
        "note": f"{n} fields (required: 8–15)",
    }

    # 2. All required keys present
    required_keys = {"name","tipo","descricao","valores","permite_desconhecido","justificativa"}
    missing_any = []
    for f in fields:
        missing = required_keys - set(f.keys())
        if missing:
            missing_any.append(f"{f.get('name','?')}: missing {missing}")
    checks["required_keys"] = {
        "pass": len(missing_any) == 0,
        "issues": missing_any,
    }

    # 3. No duplicate or near-duplicate names
    seen = set()
    dups = []
    for name in names:
        n_clean = re.sub(r"[_\s]", "", name.lower())
        if n_clean in seen:
            dups.append(name)
        seen.add(n_clean)
    checks["no_duplicate_names"] = {
        "pass": len(dups) == 0,
        "duplicates": dups,
    }

    # 4. Emotional dimension
    emotion_kw = ["emoc", "ansied", "confian", "frustr", "eufori", "postur", "sentin",
                  "afetiv", "resigna", "otimis", "pessim", "humor"]
    has_emotion = any(
        any(kw in (f.get("name","") + f.get("descricao","")).lower() for kw in emotion_kw)
        for f in fields
    )
    checks["has_emotional_field"] = {
        "pass": has_emotion,
        "note": "Looked for emotion-related keywords in name/descricao",
    }

    # 5. Capital range field
    capital_kw = ["capital", "patrimonio", "investido", "montante", "valor", "ativo"]
    has_capital = any(
        any(kw in (f.get("name","") + f.get("descricao","")).lower() for kw in capital_kw)
        for f in fields
    )
    checks["has_capital_field"] = {
        "pass": has_capital,
        "note": "Looked for capital/patrimônio keywords",
    }

    # 6. Goal/objective field
    goal_kw = ["objetivo", "meta", "renda", "passiva", "aposentad", "independenc",
               "reserva", "crescimento"]
    has_goal = any(
        any(kw in (f.get("name","") + f.get("descricao","")).lower() for kw in goal_kw)
        for f in fields
    )
    checks["has_goal_field"] = {
        "pass": has_goal,
        "note": "Looked for goal/objective keywords",
    }

    # 7. Brazil-specific field
    br_kw = ["selic", "fii", "previdencia", "imposto", "banco", "corretora", "cdi",
             "tesouro", "clt", "pj", "bovespa", "b3"]
    has_brazil = any(
        any(kw in (f.get("name","") + f.get("descricao","") + f.get("justificativa","")).lower()
            for kw in br_kw)
        for f in fields
    )
    checks["has_brazil_specific_field"] = {
        "pass": has_brazil,
        "note": "Looked for Selic/FII/previdência/imposto etc.",
    }

    # Summary
    passes = sum(1 for v in checks.values() if v.get("pass"))
    total  = len(checks)
    print(f"  Results: {passes}/{total} checks passed")
    for name, c in checks.items():
        icon = "✓" if c.get("pass") else "✗"
        print(f"  {icon} {name}")

    CHECKS_PATH.write_text(json.dumps(checks, ensure_ascii=False, indent=2))
    return checks


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    sample = run_tasks_1_2()
    success, failures, in_tok, out_tok, cost = run_task_3(sample)
    schema = run_task_4()
    checks = run_task_5(schema)
    print("\n=== Phase 1 pipeline complete ===")
    print(f"Mini-sample: {len(sample)} threads")
    print(f"Open coding: {success} coded, {failures} failures")
    print(f"Schema: {len(schema.get('fields',[]))} fields")
    print(f"Checks: {sum(1 for v in checks.values() if v.get('pass'))}/{len(checks)} passed")
