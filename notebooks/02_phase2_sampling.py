"""
Phase 2 — Full Sampling & Attribute Extraction (Calibration Checkpoint)

Tasks:
  Task 1: Build stratified working sample (~3,600 threads across 6 cells)
  Task 3: Run calibration batch (100 threads) and produce reports/phase2_calibration.md

Run:
  python notebooks/02_phase2_sampling.py

The script halts after Task 3. Task 4 (full extraction) is NOT run here.
"""

import json
import random
import sys
import time
import statistics
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))

import threads as th
import llm_client

PROCESSED   = BASE / "data/processed"
INTERIM     = BASE / "data/interim"
REPORTS     = BASE / "reports"
PROMPTS     = BASE / "prompts"

PROCESSED.mkdir(parents=True, exist_ok=True)

WORKING_SAMPLE  = PROCESSED / "working_sample.jsonl"
CALIB_SAMPLE    = PROCESSED / "calibration_sample.jsonl"
CALIB_RESULTS   = PROCESSED / "calibration_results.jsonl"
CALIB_FAILURES  = PROCESSED / "calibration_failures.jsonl"
CALIB_REPORT    = REPORTS   / "phase2_calibration.md"

SEED           = 42
N_PER_CELL     = 600
CALIB_PER_CELL = 17      # 17 × 6 = 102 ≈ 100 threads
CALIB_MODEL    = "claude-haiku-4-5-20251001"
CALIB_TEMP     = 0.1
CALIB_TOKENS   = 1200

PHASE1_MINI_SAMPLE = INTERIM / "phase1_mini_sample.jsonl"

CELLS = [
    ("investimentos", "A"),
    ("investimentos", "B"),
    ("investimentos", "C"),
    ("farialimabets", "A"),
    ("farialimabets", "B"),
    ("farialimabets", "C"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_phase1_ids() -> set[str]:
    ids = set()
    with open(PHASE1_MINI_SAMPLE) as f:
        for line in f:
            t = json.loads(line)
            ids.add(t["thread_id"])
    return ids


def load_prompt() -> tuple[str, str]:
    """Return (system_prompt, user_template) from prompts/03_attribute_extraction.md."""
    text = (PROMPTS / "03_attribute_extraction.md").read_text()
    parts = text.split("--- USER ---")
    system = parts[0].replace("--- SYSTEM ---", "").strip()
    user_tpl = parts[1].strip()
    return system, user_tpl


def stratified_cell_sample(
    pool: list,
    n: int,
    rng: random.Random,
) -> list:
    """
    Sample n threads from pool with 40/30/30 stratification:
      30% from top tercile by num_comments (high-engagement)
      30% from middle tercile by num_comments
      40% uniform from the remainder (skip bottom tercile)
    """
    if len(pool) <= n:
        return pool[:]

    sorted_by_nc = sorted(pool, key=lambda t: t.num_comments)
    total = len(sorted_by_nc)
    t1 = total // 3        # 33rd percentile cutoff index
    t2 = (total * 2) // 3  # 67th percentile cutoff index

    top_q = sorted_by_nc[t2:]    # top tercile
    mid_q = sorted_by_nc[t1:t2]  # middle tercile

    n_top = min(round(n * 0.30), len(top_q))
    n_mid = min(round(n * 0.30), len(mid_q))
    n_uni = n - n_top - n_mid

    s_top = rng.sample(top_q, n_top)
    s_mid = rng.sample(mid_q, n_mid)
    used  = {t.thread_id for t in s_top + s_mid}
    pool_uni = [t for t in pool if t.thread_id not in used]
    s_uni = rng.sample(pool_uni, min(n_uni, len(pool_uni)))

    combined = s_top + s_mid + s_uni
    rng.shuffle(combined)
    return combined


def parse_extraction(text: str) -> dict | None:
    """Parse JSON from LLM response, returning None on failure."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(l for l in lines if not l.startswith("```"))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


REQUIRED_FIELDS = [
    "sofisticacao_tecnica",
    "fase_acumulacao",
    "estrategia_principal",
    "tolerancia_risco_declarada_ou_inferida",
    "relacao_com_selic_e_renda_fixa",
    "perfil_tributario_e_fiscal",
    "relacao_com_imovel_e_heranca",
    "relacao_com_instituicoes_financeiras",
    "estado_emocional_predominante",
    "fonte_primaria_de_informacao",
    "vinculo_empregaticio_e_renda",
    "objetivo_financeiro_primario",
    "ceticismo_institucional",
    "exposicao_a_cripto_e_especulacao",
    "identidade_comunitaria",
    "confianca_extracao",
]

ORDINAL_FIELDS = {
    "sofisticacao_tecnica",
    "tolerancia_risco_declarada_ou_inferida",
    "ceticismo_institucional",
    "exposicao_a_cripto_e_especulacao",
    "identidade_comunitaria",
    "confianca_extracao",
}

CATEGORICAL_FIELDS = {
    "fase_acumulacao": ["pre_inicio","acumulacao_inicial","acumulacao_ativa","consolidacao",
                        "distribuicao_renda_passiva","preservacao_patrimonial","desconhecido"],
    "estrategia_principal": ["renda_fixa_conservadora","dividendos_buy_hold","growth_valorizacao",
                             "especulacao_curto_prazo","investimento_exterior","imobiliario_direto_ou_fii",
                             "sem_estrategia_definida","desconhecido"],
    "relacao_com_selic_e_renda_fixa": ["ancora_principal","reserva_e_transicao","obstaculo_a_superar",
                                       "indiferente_ou_desconhece","otimizador_ativo","desconhecido"],
    "perfil_tributario_e_fiscal": ["desconhece_ou_ignora","conformidade_basica","otimizador_fiscal",
                                   "cross_border_ou_pj","evasao_ou_zona_cinzenta","desconhecido"],
    "relacao_com_imovel_e_heranca": ["sem_exposicao_ou_irrelevante","imovel_como_moradia_apenas",
                                     "imovel_como_investimento_ativo","planejamento_sucessorio_relevante",
                                     "transicao_imovel_para_financeiro","desconhecido"],
    "relacao_com_instituicoes_financeiras": ["dependente_de_bancao","migrando_para_corretora",
                                              "multiplaforma_ativo","desconfiado_de_todos",
                                              "diy_sem_intermediario","desconhecido"],
    "estado_emocional_predominante": ["ansioso_ou_inseguro","confiante_ou_assertivo",
                                      "frustrado_ou_resignado","euforico_ou_impulsivo",
                                      "cinico_ou_ironico","curioso_ou_exploratorio",
                                      "equilibrado_ou_neutro","desconhecido"],
    "fonte_primaria_de_informacao": ["comunidade_online_forum","influenciadores_youtube_instagram",
                                     "assessor_ou_profissional","analise_propria_e_fontes_primarias",
                                     "familia_ou_rede_proxima","sem_fonte_estruturada","desconhecido"],
    "vinculo_empregaticio_e_renda": ["clt_empregado","servidor_publico","pj_autonomo_mei",
                                     "empresario_socio","renda_exterior_ou_remoto_internacional",
                                     "sem_renda_ou_dependente","aposentado_ou_rentista","desconhecido"],
    "objetivo_financeiro_primario": ["reserva_de_emergencia","compra_de_imovel",
                                     "aposentadoria_independencia_financeira","renda_passiva_imediata",
                                     "acumulacao_sem_objetivo_claro","educacao_ou_projeto_especifico",
                                     "sucessao_ou_doacao_familiar","desconhecido"],
}


# ── Task 1: Build working sample ──────────────────────────────────────────────

def task1_build_working_sample():
    print("\n" + "="*60)
    print("TASK 1: Building stratified working sample")
    print("="*60)

    phase1_ids = load_phase1_ids()
    print(f"  Phase 1 mini-sample size (to exclude): {len(phase1_ids)}")

    rng = random.Random(SEED)

    all_threads_by_cell: dict[tuple, list] = defaultdict(list)

    for subreddit in ("investimentos", "farialimabets"):
        print(f"\n  Streaming {subreddit}...")
        sub_threads = th.build_threads(subreddit)
        print(f"    Raw eligible threads: {len(sub_threads)}")
        for t in sub_threads:
            all_threads_by_cell[(subreddit, t.window)].append(t)

    sample_rows = []
    cell_stats = []
    total_excluded = 0

    for subreddit, window in CELLS:
        cell_key = f"{subreddit}_{window}"
        pool_all = all_threads_by_cell[(subreddit, window)]

        # Exclude Phase 1 threads
        pool = [t for t in pool_all if t.thread_id not in phase1_ids]
        n_excluded = len(pool_all) - len(pool)
        total_excluded += n_excluded

        cell_sample = stratified_cell_sample(pool, N_PER_CELL, rng)
        n_sampled = len(cell_sample)

        unit_lens = [len(t.unit_text) for t in cell_sample]
        nc_vals   = [t.num_comments for t in cell_sample]

        import datetime
        dates = [
            datetime.datetime.fromtimestamp(t.created_utc, datetime.timezone.utc).strftime("%Y-%m")
            for t in cell_sample
        ]
        date_min = min(dates)
        date_max = max(dates)

        cell_stats.append({
            "cell": cell_key,
            "eligible_all": len(pool_all),
            "eligible_after_p1_excl": len(pool),
            "p1_excluded": n_excluded,
            "sampled": n_sampled,
            "shortfall": max(0, N_PER_CELL - n_sampled),
            "mean_unit_len": round(statistics.mean(unit_lens)),
            "median_unit_len": round(statistics.median(unit_lens)),
            "mean_comments": round(statistics.mean(nc_vals), 1),
            "median_comments": round(statistics.median(nc_vals), 1),
            "date_range": f"{date_min} – {date_max}",
        })

        for t in cell_sample:
            row = asdict(t)
            row["cell"] = cell_key
            sample_rows.append(row)

        print(f"  {cell_key}: eligible={len(pool)} → sampled={n_sampled} "
              f"(excluded {n_excluded} Phase 1 threads)")

    with open(WORKING_SAMPLE, "w") as f:
        for row in sample_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\n  TOTAL sampled: {len(sample_rows)} threads across {len(CELLS)} cells")
    print(f"  Total Phase 1 threads excluded: {total_excluded}")
    print(f"  Saved → {WORKING_SAMPLE}")

    print("\n  Cell statistics:")
    print(f"  {'Cell':<28} {'Eligible':>9} {'Sampled':>8} {'Shortfall':>10} "
          f"{'MeanLen':>8} {'MeanNC':>7} Date range")
    print("  " + "-"*90)
    for s in cell_stats:
        print(f"  {s['cell']:<28} {s['eligible_after_p1_excl']:>9} {s['sampled']:>8} "
              f"{s['shortfall']:>10} {s['mean_unit_len']:>8} {s['mean_comments']:>7} "
              f"{s['date_range']}")

    return sample_rows, cell_stats


# ── Task 3: Calibration batch ─────────────────────────────────────────────────

def task3_calibration_batch(sample_rows: list) -> None:
    print("\n" + "="*60)
    print("TASK 3: Calibration batch extraction")
    print("="*60)

    rng = random.Random(SEED)

    # Group by cell
    by_cell: dict[str, list] = defaultdict(list)
    for row in sample_rows:
        by_cell[row["cell"]].append(row)

    # Draw calibration subsample (~17 per cell)
    calib_rows = []
    for subreddit, window in CELLS:
        cell_key = f"{subreddit}_{window}"
        pool = by_cell[cell_key]
        n = min(CALIB_PER_CELL, len(pool))
        calib_rows.extend(rng.sample(pool, n))

    print(f"  Calibration subsample: {len(calib_rows)} threads")

    with open(CALIB_SAMPLE, "w") as f:
        for row in calib_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    system_prompt, user_tpl = load_prompt()

    results    = []
    failures   = []
    total_cost = 0.0
    total_in   = 0
    total_out  = 0

    print(f"  Running extraction on {len(calib_rows)} threads "
          f"(model={CALIB_MODEL}, temp={CALIB_TEMP}) ...")

    for i, row in enumerate(calib_rows):
        thread_id = row["thread_id"]
        cell      = row["cell"]
        unit_text = row["unit_text"]

        user_msg = user_tpl.replace("{unit_text}", unit_text)

        resp = llm_client.call(
            system    = system_prompt,
            user_text = user_msg,
            model     = CALIB_MODEL,
            temperature = CALIB_TEMP,
            max_tokens  = CALIB_TOKENS,
            phase       = "2",
            task        = "calibration_extraction",
            notes       = f"{cell} {thread_id}",
        )

        parsed = parse_extraction(resp["text"])

        if parsed is None:
            # Retry once
            resp2 = llm_client.call(
                system    = system_prompt,
                user_text = user_msg + "\n\nIMPORTANTE: Responda APENAS o objeto JSON. Sem texto adicional.",
                model     = CALIB_MODEL,
                temperature = CALIB_TEMP,
                max_tokens  = CALIB_TOKENS,
                phase       = "2",
                task        = "calibration_extraction_retry",
                notes       = f"{cell} {thread_id} retry",
            )
            parsed = parse_extraction(resp2["text"])
            if parsed is None:
                failures.append({"thread_id": thread_id, "cell": cell,
                                 "raw_response": resp2["text"]})
                print(f"  [{i+1}/{len(calib_rows)}] PARSE FAIL {thread_id}")
                continue
            cost = resp2["cost"]
            tok_in  = resp2["input_tokens"]
            tok_out = resp2["output_tokens"]
            from_cache = resp2["from_cache"]
        else:
            cost    = resp["cost"]
            tok_in  = resp["input_tokens"]
            tok_out = resp["output_tokens"]
            from_cache = resp["from_cache"]

        total_cost += cost
        total_in   += tok_in
        total_out  += tok_out

        record = {
            "thread_id":    thread_id,
            "cell":         cell,
            "subreddit":    row["subreddit"],
            "window":       row["window"],
            "from_cache":   from_cache,
            "cost":         cost,
            "input_tokens": tok_in,
            "output_tokens": tok_out,
            "attributes":   parsed,
            "unit_text":    unit_text,
        }
        results.append(record)

        cache_tag = "[CACHED]" if from_cache else ""
        print(f"  [{i+1}/{len(calib_rows)}] {thread_id} ({cell}) "
              f"conf={parsed.get('confianca_extracao','?')} "
              f"cost=${cost:.5f} {cache_tag}")

    with open(CALIB_RESULTS, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(CALIB_FAILURES, "w") as f:
        for r in failures:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n  Done. Successes={len(results)}, Failures={len(failures)}")
    print(f"  Total cost: ${total_cost:.4f}  "
          f"({total_in} input tokens, {total_out} output tokens)")

    build_calibration_report(results, failures, calib_rows,
                              total_cost, total_in, total_out)


# ── Report builder ────────────────────────────────────────────────────────────

def build_calibration_report(
    results: list,
    failures: list,
    calib_rows: list,
    total_cost: float,
    total_in: int,
    total_out: int,
) -> None:
    n_total    = len(results) + len(failures)
    n_ok       = len(results)
    parse_rate = n_ok / n_total * 100 if n_total else 0.0

    lines = []
    A = lines.append

    A("# Phase 2 Calibration Report")
    A("")
    A(f"**Date:** 2026-05-20  ")
    A(f"**Status: AWAITING SUPERVISOR REVIEW — do not proceed to full extraction**")
    A("")
    A("---")
    A("")
    A("## 1. Parse Success & Cost")
    A("")
    A(f"| Metric | Value |")
    A(f"|--------|-------|")
    A(f"| Threads attempted | {n_total} |")
    A(f"| Parse successes | {n_ok} ({parse_rate:.1f}%) |")
    A(f"| Parse failures | {len(failures)} |")
    A(f"| Total input tokens | {total_in:,} |")
    A(f"| Total output tokens | {total_out:,} |")
    A(f"| Estimated cost (calibration) | ${total_cost:.4f} |")
    A(f"| Model | {CALIB_MODEL} |")
    A(f"| Temperature | {CALIB_TEMP} |")
    A("")

    if failures:
        A("### Parse Failures")
        A("")
        for f in failures:
            A(f"- `{f['thread_id']}` ({f['cell']})")
        A("")

    A("---")
    A("")
    A("## 2. Field Value Distributions")
    A("")
    A("### 2a. Ordinal Fields (value counts)")
    A("")

    attrs_list = [r["attributes"] for r in results]

    for field in ORDINAL_FIELDS:
        counts: dict[str, int] = defaultdict(int)
        for a in attrs_list:
            v = a.get(field, "missing")
            counts[str(v)] += 1
        A(f"**{field}**")
        A("")
        A("| Value | Count | % |")
        A("|-------|-------|---|")
        for k in sorted(counts.keys()):
            pct = counts[k] / n_ok * 100 if n_ok else 0
            A(f"| {k} | {counts[k]} | {pct:.1f}% |")
        A("")

    A("### 2b. Categorical Fields (value counts)")
    A("")

    for field in CATEGORICAL_FIELDS:
        counts: dict[str, int] = defaultdict(int)
        for a in attrs_list:
            v = a.get(field, "missing")
            counts[str(v)] += 1
        A(f"**{field}**")
        A("")
        A("| Value | Count | % |")
        A("|-------|-------|---|")
        all_vals = sorted(counts.keys(), key=lambda x: -counts[x])
        for k in all_vals:
            pct = counts[k] / n_ok * 100 if n_ok else 0
            A(f"| {k} | {counts[k]} | {pct:.1f}% |")
        A("")

    A("---")
    A("")
    A("## 3. Desconhecido Rate by Field & Subreddit")
    A("")
    A("Fields with >70% desconhecido rate flagged with ⚠️ (pre-registered threshold).")
    A("")

    inv_results = [r for r in results if r["subreddit"] == "investimentos"]
    fari_results = [r for r in results if r["subreddit"] == "farialimabets"]

    A("| Field | Overall % desconh | r/investimentos % | r/farialimabets % | Flag |")
    A("|-------|-------------------|-------------------|-------------------|------|")

    all_optional = list(CATEGORICAL_FIELDS.keys()) + [
        f for f in ORDINAL_FIELDS if f != "confianca_extracao"
    ]

    for field in REQUIRED_FIELDS:
        if field == "confianca_extracao":
            continue

        def rate(rlist):
            if not rlist:
                return 0.0
            n_unk = sum(1 for r in rlist if str(r["attributes"].get(field,"")) == "desconhecido")
            return n_unk / len(rlist) * 100

        ov   = rate(results)
        inv  = rate(inv_results)
        fari = rate(fari_results)
        flag = "⚠️ >70%" if ov > 70 else ""
        A(f"| {field} | {ov:.1f}% | {inv:.1f}% | {fari:.1f}% | {flag} |")
    A("")

    A("---")
    A("")
    A("## 4. Emotional Distribution by Subreddit")
    A("")
    A("Key calibration check: does r/farialimabets show emotional variety, or did it collapse to `cinico_ou_ironico`?")
    A("")

    for sub, sub_results in [("r/investimentos", inv_results), ("r/farialimabets", fari_results)]:
        counts: dict[str, int] = defaultdict(int)
        for r in sub_results:
            v = r["attributes"].get("estado_emocional_predominante", "missing")
            counts[str(v)] += 1
        total_sub = len(sub_results)
        A(f"**{sub}** (n={total_sub})")
        A("")
        A("| Emotion | Count | % |")
        A("|---------|-------|---|")
        for k in sorted(counts.keys(), key=lambda x: -counts[x]):
            pct = counts[k] / total_sub * 100 if total_sub else 0
            A(f"| {k} | {counts[k]} | {pct:.1f}% |")
        A("")

    A("---")
    A("")
    A("## 5. Self-Confidence Distribution (confianca_extracao)")
    A("")
    counts_conf: dict[str, int] = defaultdict(int)
    for a in attrs_list:
        v = a.get("confianca_extracao", "missing")
        counts_conf[str(v)] += 1
    A("| Score | Count | % |")
    A("|-------|-------|---|")
    for k in sorted(counts_conf.keys()):
        pct = counts_conf[k] / n_ok * 100 if n_ok else 0
        A(f"| {k} | {counts_conf[k]} | {pct:.1f}% |")
    A("")
    conf_vals = [r["attributes"].get("confianca_extracao") for r in results
                 if isinstance(r["attributes"].get("confianca_extracao"), int)]
    if conf_vals:
        A(f"Mean confidence: {statistics.mean(conf_vals):.2f}  "
          f"Median: {statistics.median(conf_vals):.1f}")
    A("")

    A("---")
    A("")
    A("## 6. Ten Full Extraction Outputs (manual review)")
    A("")
    A("Selected across cells; at least 2 r/farialimabets humor threads for emotion-coding verification.")
    A("")

    fari_humor = [r for r in results if r["subreddit"] == "farialimabets"][:2]
    others = [r for r in results
              if r not in fari_humor
              and r.get("subreddit") != "farialimabets"][:8]
    review_set = (fari_humor + others)[:10]

    for i, r in enumerate(review_set, 1):
        A(f"### Example {i} — {r['thread_id']} ({r['cell']})")
        A("")
        A("**unit_text (first 600 chars):**")
        A("```")
        A(r["unit_text"][:600])
        A("```")
        A("")
        A("**Extracted attributes:**")
        A("```json")
        A(json.dumps(r["attributes"], ensure_ascii=False, indent=2))
        A("```")
        A("")

    A("---")
    A("")
    A("## 7. Reviewer Checklist")
    A("")
    A("Before approving for full extraction (Task 4), please verify:")
    A("")
    A("- [ ] Parse success rate is acceptable (>95%?)")
    A("- [ ] No field collapses to a single value (>80% modal) — check Section 2")
    A("- [ ] Fields above 70% desconhecido rate are identified and disposition decided")
    A("- [ ] r/farialimabets shows emotional variety, not just cinico_ou_ironico collapse")
    A("- [ ] The 10 hand-reviewed examples (Section 6) look plausible to a domain expert")
    A("- [ ] Self-confidence distribution is informative (not all 5s, not all 1s)")
    A("- [ ] Estimated cost for full extraction is acceptable")
    A("")
    A("**Estimated cost for full extraction (~3,600 threads at same rate):**")
    if n_ok > 0:
        cost_per_thread = total_cost / n_ok
        est_full_cost   = cost_per_thread * 3600
        A(f"~${est_full_cost:.2f} (based on ${cost_per_thread:.5f}/thread calibration average)")
    A("")
    A("**→ Hard stop. Do not run Task 4 until supervisor approves this report.**")

    CALIB_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Calibration report → {CALIB_REPORT}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Phase 2 — Sampling & Calibration")
    print(f"Working directory: {BASE}")

    sample_rows, cell_stats = task1_build_working_sample()
    task3_calibration_batch(sample_rows)

    print("\n" + "="*60)
    print("CHECKPOINT: Tasks 1 and 3 complete.")
    print("→ Review reports/phase2_calibration.md before proceeding.")
    print("→ Task 4 (full extraction) is BLOCKED pending supervisor review.")
    print("="*60)


if __name__ == "__main__":
    main()
