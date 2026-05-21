"""
Phase 2 — Tasks 4 & 5: Full Extraction, Reliability Check, Feature Config

Tasks:
  Task 4 : Full attribute extraction for all 3,600 working-sample threads.
           102 calibration threads reused from file cache; remaining ~3,498
           are new API calls with server-side prompt caching enabled.
           Saves data/processed/extracted_attributes.parquet.
  Task 4b: Full-corpus missingness report and field arbitration
           (relacao_com_selic and perfil_tributario final verdict).
  Task 4c: Write data/processed/clustering_features.json.
  Task 5 : Reliability check — 150-thread re-extraction with fresh calls.
           Per-field agreement stats; flags fields below reliability thresholds.

Run:
  python notebooks/02b_phase2_extraction.py

Halts after producing reports/phase2_full_summary.md and reports/reliability_check.jsonl.
"""

import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
import llm_client

PROCESSED = BASE / "data/processed"
REPORTS   = BASE / "reports"
PROMPTS   = BASE / "prompts"

WORKING_SAMPLE         = PROCESSED / "working_sample.jsonl"
CALIB_RESULTS          = PROCESSED / "calibration_results.jsonl"
EXTRACTED_PARQUET      = PROCESSED / "extracted_attributes.parquet"
EXTRACTION_JSONL       = PROCESSED / "extracted_attributes.jsonl"
EXTRACTION_FAILURES    = PROCESSED / "extraction_failures.jsonl"
CLUSTERING_FEATURES    = PROCESSED / "clustering_features.json"
RELIABILITY_JSONL      = PROCESSED / "reliability_reextraction.jsonl"
PHASE2_FULL_SUMMARY    = REPORTS   / "phase2_full_summary.md"

SEED          = 42
MODEL         = "claude-haiku-4-5-20251001"
TEMP          = 0.1
MAX_TOKENS    = 1200
RELIABILITY_N = 150
RELIABILITY_SALT = "rchk_v1"

# ── Schema definitions ────────────────────────────────────────────────────────

ORDINAL_FIELDS = [
    "sofisticacao_tecnica",
    "tolerancia_risco_declarada_ou_inferida",
    "ceticismo_institucional",
    "exposicao_a_cripto_e_especulacao",
    "identidade_comunitaria",
]
ORDINAL_REQUIRED = {    # these do NOT allow desconhecido
    "sofisticacao_tecnica",
    "tolerancia_risco_declarada_ou_inferida",
    "ceticismo_institucional",
}
CONFIANCA_FIELD = "confianca_extracao"

CATEGORICAL_VALID = {
    "fase_acumulacao": {
        "pre_inicio","acumulacao_inicial","acumulacao_ativa","consolidacao",
        "distribuicao_renda_passiva","preservacao_patrimonial","desconhecido",
    },
    "estrategia_principal": {
        "renda_fixa_conservadora","dividendos_buy_hold","growth_valorizacao",
        "especulacao_curto_prazo","investimento_exterior","imobiliario_direto_ou_fii",
        "sem_estrategia_definida","desconhecido",
    },
    "relacao_com_selic_e_renda_fixa": {
        "ancora_principal","reserva_e_transicao","obstaculo_a_superar",
        "indiferente_ou_desconhece","otimizador_ativo","desconhecido",
    },
    "perfil_tributario_e_fiscal": {
        "desconhece_ou_ignora","conformidade_basica","otimizador_fiscal",
        "cross_border_ou_pj","evasao_ou_zona_cinzenta","desconhecido",
    },
    "relacao_com_imovel_e_heranca": {
        "sem_exposicao_ou_irrelevante","imovel_como_moradia_apenas",
        "imovel_como_investimento_ativo","planejamento_sucessorio_relevante",
        "transicao_imovel_para_financeiro","desconhecido",
    },
    "relacao_com_instituicoes_financeiras": {
        "dependente_de_bancao","migrando_para_corretora","multiplaforma_ativo",
        "desconfiado_de_todos","diy_sem_intermediario","desconhecido",
    },
    "estado_emocional_predominante": {
        "ansioso_ou_inseguro","confiante_ou_assertivo","frustrado_ou_resignado",
        "euforico_ou_impulsivo","cinico_ou_ironico","curioso_ou_exploratorio",
        "equilibrado_ou_neutro","desconhecido",
    },
    "fonte_primaria_de_informacao": {
        "comunidade_online_forum","influenciadores_youtube_instagram",
        "assessor_ou_profissional","analise_propria_e_fontes_primarias",
        "familia_ou_rede_proxima","sem_fonte_estruturada","desconhecido",
    },
    "vinculo_empregaticio_e_renda": {
        "clt_empregado","servidor_publico","pj_autonomo_mei","empresario_socio",
        "renda_exterior_ou_remoto_internacional","sem_renda_ou_dependente",
        "aposentado_ou_rentista","desconhecido",
    },
    "objetivo_financeiro_primario": {
        "reserva_de_emergencia","compra_de_imovel",
        "aposentadoria_independencia_financeira","renda_passiva_imediata",
        "acumulacao_sem_objetivo_claro","educacao_ou_projeto_especifico",
        "sucessao_ou_doacao_familiar","desconhecido",
    },
}
ALL_ATTR_FIELDS = ORDINAL_FIELDS + list(CATEGORICAL_VALID.keys())

METADATA_COLS = [
    "thread_id","subreddit_origem","window","score","num_comments",
    "is_link_post","created_utc","unit_text",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_prompt():
    text = (PROMPTS / "03_attribute_extraction.md").read_text()
    parts = text.split("--- USER ---")
    system = parts[0].replace("--- SYSTEM ---", "").strip()
    user_tpl = parts[1].strip()
    return system, user_tpl


def parse_json(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(l for l in lines if not l.startswith("```"))
    try:
        return json.loads(text)
    except Exception:
        return None


def validate_and_coerce(attrs: dict) -> tuple[dict, list[str]]:
    """
    Validate extracted attributes against schema.
    Coerces out-of-schema values to desconhecido (or None for required ordinals).
    Returns (coerced_attrs, list_of_violation_descriptions).
    """
    violations = []
    out = {}

    # Ordinal fields
    for field in ORDINAL_FIELDS:
        raw = attrs.get(field)
        try:
            val = int(raw)
            if 1 <= val <= 5:
                out[field] = val
            else:
                violations.append(f"{field}={raw!r} out of 1-5 range")
                out[field] = None
        except (TypeError, ValueError):
            if str(raw) == "desconhecido" and field not in ORDINAL_REQUIRED:
                out[field] = None
            else:
                violations.append(f"{field}={raw!r} not a valid integer 1-5")
                out[field] = None

    # confianca_extracao (always required, 1-5)
    raw = attrs.get(CONFIANCA_FIELD)
    try:
        val = int(raw)
        out[CONFIANCA_FIELD] = val if 1 <= val <= 5 else None
        if not (1 <= val <= 5):
            violations.append(f"{CONFIANCA_FIELD}={raw!r} out of 1-5 range")
    except (TypeError, ValueError):
        violations.append(f"{CONFIANCA_FIELD}={raw!r} not a valid integer 1-5")
        out[CONFIANCA_FIELD] = None

    # Categorical fields
    for field, valid_set in CATEGORICAL_VALID.items():
        raw = attrs.get(field, "desconhecido")
        val = str(raw) if raw is not None else "desconhecido"
        if val in valid_set:
            out[field] = val
        else:
            violations.append(f"{field}={raw!r} not in valid set")
            out[field] = "desconhecido"

    return out, violations


# ── Task 4: Full extraction ───────────────────────────────────────────────────

def task4_full_extraction():
    print("\n" + "="*60)
    print("TASK 4: Full attribute extraction (~3,600 threads)")
    print("="*60)

    # Load working sample
    rows = []
    with open(WORKING_SAMPLE) as f:
        for line in f:
            rows.append(json.loads(line))
    print(f"  Working sample: {len(rows)} threads")

    # Load already-extracted calibration results → these are in file cache;
    # calling llm_client will return them instantly without new API calls.
    calib_ids = set()
    with open(CALIB_RESULTS) as f:
        for line in f:
            r = json.loads(line)
            calib_ids.add(r["thread_id"])
    print(f"  Calibration threads (from file cache): {len(calib_ids)}")
    print(f"  New API calls expected: {len(rows) - len(calib_ids)}")

    system_prompt, user_tpl = load_prompt()

    results     = []
    failures    = []
    total_cost  = total_in = total_out = 0
    cache_write = cache_read = 0
    n_file_cache = 0

    print(f"\n  Extracting with prompt caching enabled (model={MODEL})...")

    for i, row in enumerate(rows):
        tid  = row["thread_id"]
        cell = row["cell"]
        sub  = row["subreddit"]
        win  = row["window"]

        user_msg = user_tpl.replace("{unit_text}", row["unit_text"])

        resp = llm_client.call(
            system          = system_prompt,
            user_text       = user_msg,
            model           = MODEL,
            temperature     = TEMP,
            max_tokens      = MAX_TOKENS,
            phase           = "2",
            task            = "full_extraction",
            notes           = f"{cell} {tid}",
            use_prompt_cache = True,
        )

        if resp["from_cache"]:
            n_file_cache += 1
            parsed = parse_json(resp["text"])
        else:
            parsed = parse_json(resp["text"])
            total_cost  += resp["cost"]
            total_in    += resp["input_tokens"]
            total_out   += resp["output_tokens"]
            cache_write += resp.get("cache_write_tokens", 0)
            cache_read  += resp.get("cache_read_tokens", 0)

        if parsed is None:
            # Retry once
            resp2 = llm_client.call(
                system          = system_prompt,
                user_text       = user_msg + "\n\nIMPORTANTE: Responda APENAS o objeto JSON.",
                model           = MODEL,
                temperature     = TEMP,
                max_tokens      = MAX_TOKENS,
                phase           = "2",
                task            = "full_extraction_retry",
                notes           = f"{cell} {tid} retry",
                use_prompt_cache = True,
            )
            parsed = parse_json(resp2["text"])
            if not resp2["from_cache"]:
                total_cost  += resp2["cost"]
                total_in    += resp2["input_tokens"]
                total_out   += resp2["output_tokens"]
                cache_write += resp2.get("cache_write_tokens", 0)
                cache_read  += resp2.get("cache_read_tokens", 0)
            if parsed is None:
                failures.append({"thread_id": tid, "cell": cell,
                                 "raw_response": resp2["text"]})
                if (i + 1) % 100 == 0:
                    print(f"  [{i+1:>4}/{len(rows)}] ... (running)")
                print(f"  PARSE FAIL: {tid}")
                continue

        attrs, violations = validate_and_coerce(parsed)

        results.append({
            "thread_id":       tid,
            "subreddit_origem": sub,
            "window":          win,
            "cell":            cell,
            "score":           row["score"],
            "num_comments":    row["num_comments"],
            "is_link_post":    row["is_link_post"],
            "created_utc":     row["created_utc"],
            "unit_text":       row["unit_text"],
            "attributes":      attrs,
            "violations":      violations,
            "from_cache":      resp["from_cache"],
        })

        if violations:
            print(f"  [{i+1:>4}/{len(rows)}] COERCE {tid}: {violations}")
        elif (i + 1) % 200 == 0 or i < 5:
            fc = "[C]" if resp["from_cache"] else "   "
            print(f"  [{i+1:>4}/{len(rows)}] {fc} {tid} ({cell})")

    print(f"\n  Done. Extracted={len(results)} Failures={len(failures)}")
    print(f"  File-cache hits: {n_file_cache}")
    print(f"  New API cost: ${total_cost:.4f} "
          f"({total_in:,} input, {total_out:,} output, "
          f"{cache_write:,} cache-write, {cache_read:,} cache-read tokens)")

    with open(EXTRACTION_JSONL, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(EXTRACTION_FAILURES, "w") as f:
        for r in failures:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return results, failures, {
        "total_cost": total_cost, "total_in": total_in, "total_out": total_out,
        "cache_write": cache_write, "cache_read": cache_read,
        "n_file_cache": n_file_cache, "n_api": len(results) - n_file_cache,
    }


# ── Task 4 → Parquet + validation ─────────────────────────────────────────────

def build_parquet(results: list, failures: list) -> pd.DataFrame:
    print("\n  Building parquet...")

    violation_log = []
    rows_flat = []
    for r in results:
        row = {
            "thread_id":       r["thread_id"],
            "subreddit_origem": r["subreddit_origem"],
            "window":          r["window"],
            "score":           r["score"],
            "num_comments":    r["num_comments"],
            "is_link_post":    r["is_link_post"],
            "created_utc":     r["created_utc"],
            "unit_text":       r["unit_text"],
        }
        attrs = r["attributes"]
        for field in ORDINAL_FIELDS:
            row[field] = attrs.get(field)     # int or None
        row[CONFIANCA_FIELD] = attrs.get(CONFIANCA_FIELD)
        for field in CATEGORICAL_VALID:
            row[field] = attrs.get(field, "desconhecido")
        if r["violations"]:
            for v in r["violations"]:
                violation_log.append({"thread_id": r["thread_id"], "violation": v})
        rows_flat.append(row)

    df = pd.DataFrame(rows_flat)

    # Type coercion
    int_cols = ORDINAL_FIELDS + [CONFIANCA_FIELD]
    for col in int_cols:
        df[col] = pd.array(df[col], dtype=pd.Int8Dtype())

    df.to_parquet(EXTRACTED_PARQUET, index=False)
    print(f"  Parquet saved: {EXTRACTED_PARQUET}  shape={df.shape}")

    n_violations = sum(len(r["violations"]) for r in results)
    n_threads_with_violations = sum(1 for r in results if r["violations"])
    print(f"  Schema violations: {n_violations} across {n_threads_with_violations} threads "
          f"({n_threads_with_violations/len(results)*100:.1f}% of threads)")

    return df, violation_log


# ── Task 4b: Missingness report + field arbitration ───────────────────────────

MISSINGNESS_THRESHOLD = 0.70   # pre-registered

def task4b_missingness(df: pd.DataFrame) -> dict:
    print("\n" + "="*60)
    print("TASK 4b: Full-corpus missingness report")
    print("="*60)

    # Fields that can be "desconhecido"
    optional_fields = list(CATEGORICAL_VALID.keys()) + [
        f for f in ORDINAL_FIELDS if f not in ORDINAL_REQUIRED
    ]

    # Compute missingness by subreddit × window × overall
    stats = {}
    for field in optional_fields:
        if field in CATEGORICAL_VALID:
            n_unk = (df[field] == "desconhecido").sum()
        else:
            n_unk = df[field].isna().sum()

        n_total = len(df)
        rate_overall = n_unk / n_total

        by_sub = {}
        for sub in ("investimentos", "farialimabets"):
            sub_df = df[df["subreddit_origem"] == sub]
            if field in CATEGORICAL_VALID:
                n = (sub_df[field] == "desconhecido").sum()
            else:
                n = sub_df[field].isna().sum()
            by_sub[sub] = n / len(sub_df) if len(sub_df) else 0.0

        by_win = {}
        for win in ("A", "B", "C"):
            win_df = df[df["window"] == win]
            if field in CATEGORICAL_VALID:
                n = (win_df[field] == "desconhecido").sum()
            else:
                n = win_df[field].isna().sum()
            by_win[win] = n / len(win_df) if len(win_df) else 0.0

        stats[field] = {
            "overall": rate_overall,
            "by_sub": by_sub,
            "by_win": by_win,
        }

    # Arbitrate the two pending fields
    verdicts = {}
    for field in ("relacao_com_selic_e_renda_fixa", "perfil_tributario_e_fiscal"):
        rate = stats[field]["overall"]
        if rate <= MISSINGNESS_THRESHOLD:
            verdict = "INCLUDE_AS_CLUSTERING_FEATURE"
        else:
            verdict = "DEMOTE_TO_FLAG"
        verdicts[field] = {"rate": rate, "verdict": verdict}
        print(f"  {field}: {rate*100:.1f}% desconhecido → {verdict}")

    return stats, verdicts


# ── Task 4c: Clustering features config ───────────────────────────────────────

def task4c_feature_config(verdicts: dict):
    print("\n" + "="*60)
    print("TASK 4c: Writing clustering_features.json")
    print("="*60)

    confirmed = [
        "sofisticacao_tecnica",
        "fase_acumulacao",
        "estrategia_principal",
        "tolerancia_risco_declarada_ou_inferida",
        "relacao_com_instituicoes_financeiras",
        "estado_emocional_predominante",
        "objetivo_financeiro_primario",
        "ceticismo_institucional",
        "exposicao_a_cripto_e_especulacao",
        "identidade_comunitaria",
    ]

    # Pending fields become confirmed or demoted based on verdict
    for field, info in verdicts.items():
        if info["verdict"] == "INCLUDE_AS_CLUSTERING_FEATURE":
            confirmed.append(field)

    demoted = [
        "subreddit_origem",
        "window",
        "relacao_com_imovel_e_heranca",
        "vinculo_empregaticio_e_renda",
        "fonte_primaria_de_informacao",
        "confianca_extracao",
    ]
    for field, info in verdicts.items():
        if info["verdict"] == "DEMOTE_TO_FLAG":
            demoted.append(field)

    config = {
        "schema_version": "1.1",
        "verdict_date": "2026-05-20",
        "decision_rule": "pre-registered: optional field demoted if full-corpus desconhecido >70%",
        "clustering_features": confirmed,
        "metadata_and_flags": demoted,
        "field_verdicts": {
            f: {
                "decision": info["verdict"],
                "full_corpus_desconhecido_rate": round(info["rate"], 4),
            }
            for f, info in verdicts.items()
        },
    }

    CLUSTERING_FEATURES.write_text(json.dumps(config, ensure_ascii=False, indent=2))
    print(f"  Saved: {CLUSTERING_FEATURES}")
    print(f"  Clustering features ({len(confirmed)}): {confirmed}")
    print(f"  Demoted to flags ({len(demoted)}): {demoted}")
    return config


# ── Task 5: Reliability check ─────────────────────────────────────────────────

def task5_reliability(df: pd.DataFrame, results: list):
    print("\n" + "="*60)
    print("TASK 5: Reliability check (150-thread re-extraction)")
    print("="*60)

    # Sample 150 threads from full results, seed=42
    rng = random.Random(SEED)
    sample_records = rng.sample(results, min(RELIABILITY_N, len(results)))
    print(f"  Reliability sample: {len(sample_records)} threads (salt='{RELIABILITY_SALT}')")

    system_prompt, user_tpl = load_prompt()

    re_results = []
    total_cost = total_in = total_out = 0

    for i, r in enumerate(sample_records):
        tid      = r["thread_id"]
        user_msg = user_tpl.replace("{unit_text}", r["unit_text"])

        resp = llm_client.call(
            system           = system_prompt,
            user_text        = user_msg,
            model            = MODEL,
            temperature      = TEMP,
            max_tokens       = MAX_TOKENS,
            phase            = "2",
            task             = "reliability_check",
            notes            = f"{r['cell']} {tid}",
            use_prompt_cache = True,
            salt             = RELIABILITY_SALT,
        )

        parsed = parse_json(resp["text"])
        if parsed is None:
            resp2 = llm_client.call(
                system           = system_prompt,
                user_text        = user_msg + "\n\nIMPORTANTE: Responda APENAS o objeto JSON.",
                model            = MODEL,
                temperature      = TEMP,
                max_tokens       = MAX_TOKENS,
                phase            = "2",
                task             = "reliability_check_retry",
                notes            = f"{r['cell']} {tid} retry",
                use_prompt_cache = True,
                salt             = RELIABILITY_SALT,
            )
            parsed = parse_json(resp2["text"])
            if not resp2["from_cache"]:
                total_cost += resp2["cost"]
                total_in   += resp2["input_tokens"]
                total_out  += resp2["output_tokens"]
            if parsed is None:
                print(f"  [{i+1}/{len(sample_records)}] FAIL {tid}")
                continue

        if not resp["from_cache"]:
            total_cost += resp["cost"]
            total_in   += resp["input_tokens"]
            total_out  += resp["output_tokens"]

        attrs, _ = validate_and_coerce(parsed)
        re_results.append({
            "thread_id": tid,
            "attributes_rerun": attrs,
        })

        if (i + 1) % 50 == 0 or i < 3:
            print(f"  [{i+1:>3}/{len(sample_records)}] {tid}")

    with open(RELIABILITY_JSONL, "w") as f:
        for r in re_results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n  Re-extractions done: {len(re_results)}  cost=${total_cost:.4f}")

    # Build lookup: thread_id → original attributes (from parquet)
    orig_lookup = {}
    for r in results:
        orig_lookup[r["thread_id"]] = r["attributes"]

    rerun_lookup = {r["thread_id"]: r["attributes_rerun"] for r in re_results}

    # Compute per-field agreement
    field_agreement = {}
    for field in ORDINAL_FIELDS:
        pairs = [
            (orig_lookup[r["thread_id"]].get(field),
             rerun_lookup[r["thread_id"]].get(field))
            for r in re_results
            if r["thread_id"] in orig_lookup
        ]
        # Keep only pairs where BOTH are non-None integers
        valid = [(o, n) for o, n in pairs if isinstance(o, int) and isinstance(n, int)]
        if len(valid) < 5:
            field_agreement[field] = {"n_valid": len(valid), "kappa": None,
                                       "exact_match": None, "type": "ordinal"}
            continue
        orig_v, new_v = zip(*valid)
        kappa = cohen_kappa_score(orig_v, new_v, weights="linear",
                                  labels=[1,2,3,4,5])
        exact = sum(o == n for o, n in valid) / len(valid)
        field_agreement[field] = {
            "n_valid": len(valid), "kappa": round(kappa, 3),
            "exact_match": round(exact, 3), "type": "ordinal",
        }

    for field in CATEGORICAL_VALID:
        pairs = [
            (orig_lookup[r["thread_id"]].get(field, "desconhecido"),
             rerun_lookup[r["thread_id"]].get(field, "desconhecido"))
            for r in re_results
            if r["thread_id"] in orig_lookup
        ]
        if not pairs:
            field_agreement[field] = {"n_valid": 0, "agreement": None, "type": "categorical"}
            continue
        agreement = sum(o == n for o, n in pairs) / len(pairs)
        field_agreement[field] = {
            "n_valid": len(pairs), "agreement": round(agreement, 3),
            "type": "categorical",
        }

    # Flag low-reliability fields
    low_reliability = []
    for field, fa in field_agreement.items():
        if fa["type"] == "ordinal":
            k = fa.get("kappa")
            if k is not None and k < 0.40:
                low_reliability.append((field, f"kappa={k:.3f} < 0.40"))
        else:
            a = fa.get("agreement")
            if a is not None and a < 0.60:
                low_reliability.append((field, f"agreement={a:.3f} < 0.60"))

    return field_agreement, low_reliability, total_cost, total_in, total_out


# ── Full summary report ───────────────────────────────────────────────────────

def build_full_summary(
    df: pd.DataFrame,
    results: list,
    failures: list,
    cost_stats: dict,
    violation_log: list,
    miss_stats: dict,
    verdicts: dict,
    feature_config: dict,
    field_agreement: dict,
    low_reliability: list,
    task5_cost: float,
    task5_in: int,
    task5_out: int,
):
    n_total    = len(results) + len(failures)
    n_ok       = len(results)
    parse_rate = n_ok / n_total * 100 if n_total else 0.0

    lines = []
    A = lines.append

    A("# Phase 2 Full Extraction Summary")
    A("")
    A("**Date:** 2026-05-20  ")
    A("**Status: AWAITING SUPERVISOR REVIEW — Phase 3 is blocked pending approval**")
    A("")
    A("---")
    A("")
    A("## 1. Extraction Statistics")
    A("")
    A("| Metric | Value |")
    A("|--------|-------|")
    A(f"| Working sample size | {n_total} |")
    A(f"| Successful extractions | {n_ok} ({parse_rate:.1f}%) |")
    A(f"| Parse failures | {len(failures)} |")
    A(f"| File-cache hits (calibration) | {cost_stats['n_file_cache']} |")
    A(f"| New API calls | {cost_stats['n_api']} |")
    A(f"| New API input tokens | {cost_stats['total_in']:,} |")
    A(f"| New API output tokens | {cost_stats['total_out']:,} |")
    A(f"| Prompt-cache write tokens | {cost_stats['cache_write']:,} |")
    A(f"| Prompt-cache read tokens | {cost_stats['cache_read']:,} |")
    A(f"| Task 4 cost (new API calls) | ${cost_stats['total_cost']:.4f} |")
    A(f"| Task 5 cost (reliability) | ${task5_cost:.4f} |")
    A(f"| **Phase 2 total (Tasks 3–5)** | **${cost_stats['total_cost'] + task5_cost + 0.8106:.4f}** (includes calibration $0.81) |")
    A("")

    # Schema violations
    n_viol_threads = sum(1 for r in results if r["violations"])
    n_viol_total   = sum(len(r["violations"]) for r in results)
    A(f"**Schema validation:** {n_viol_total} out-of-schema values across "
      f"{n_viol_threads} threads ({n_viol_threads/n_ok*100:.1f}% of threads). "
      f"All coerced to `desconhecido`.")
    A("")
    if violation_log:
        A("Top violation types (all unique):")
        A("")
        from collections import Counter
        violation_fields = Counter(v["violation"].split("=")[0] for v in violation_log)
        for field, cnt in violation_fields.most_common(10):
            A(f"- `{field}`: {cnt} occurrences")
        A("")

    if failures:
        A("**Parse failures:**")
        for f in failures:
            A(f"- `{f['thread_id']}` ({f['cell']})")
        A("")

    A("---")
    A("")
    A("## 2. Full-Corpus Field Distributions")
    A("")
    A("### 2a. Ordinal Fields")
    A("")
    for field in ORDINAL_FIELDS + [CONFIANCA_FIELD]:
        col = df[field].dropna()
        counts = col.value_counts().sort_index()
        A(f"**{field}** (n={len(col)}, {df[field].isna().sum()} null)")
        A("")
        A("| Value | Count | % |")
        A("|-------|-------|---|")
        for v, c in counts.items():
            A(f"| {v} | {c} | {c/len(col)*100:.1f}% |")
        if len(col) > 0:
            A(f"Mean: {col.mean():.2f}  Median: {col.median():.1f}")
        A("")

    A("### 2b. Categorical Fields")
    A("")
    for field in CATEGORICAL_VALID:
        vc = df[field].value_counts()
        n = len(df)
        A(f"**{field}**")
        A("")
        A("| Value | Count | % |")
        A("|-------|-------|---|")
        for v, c in vc.items():
            A(f"| {v} | {c} | {c/n*100:.1f}% |")
        A("")

    A("---")
    A("")
    A("## 3. Missingness Report & Field Arbitration")
    A("")
    A("Pre-registered rule: optional field with full-corpus desconhecido >70% is demoted to flag.")
    A("")
    A("| Field | Overall | r/inv | r/fari | Win A | Win B | Win C | Verdict |")
    A("|-------|---------|-------|--------|-------|-------|-------|---------|")
    for field, st in miss_stats.items():
        ov   = st["overall"]
        iv   = st["by_sub"].get("investimentos", 0)
        fv   = st["by_sub"].get("farialimabets", 0)
        wa   = st["by_win"].get("A", 0)
        wb   = st["by_win"].get("B", 0)
        wc   = st["by_win"].get("C", 0)
        if field in verdicts:
            verd = verdicts[field]["verdict"].replace("_", " ")
        elif ov > MISSINGNESS_THRESHOLD:
            verd = "DEMOTE (pre-cal)"
        else:
            verd = "OK"
        A(f"| {field} | {ov*100:.1f}% | {iv*100:.1f}% | {fv*100:.1f}% | "
          f"{wa*100:.1f}% | {wb*100:.1f}% | {wc*100:.1f}% | {verd} |")
    A("")
    A("### Arbitration verdicts for pending fields")
    A("")
    for field, info in verdicts.items():
        v = info["verdict"]
        r = info["rate"]
        A(f"**{field}**: {r*100:.1f}% desconhecido → **{v}**")
        if v == "DEMOTE_TO_FLAG":
            A(f"  → Excluded from clustering feature matrix; retained as incidence flag.")
        else:
            A(f"  → Included in clustering feature matrix.")
    A("")

    A("---")
    A("")
    A("## 4. Confirmed Feature Set")
    A("")
    A(f"### Clustering features ({len(feature_config['clustering_features'])} fields)")
    A("")
    for f in feature_config["clustering_features"]:
        A(f"- `{f}`")
    A("")
    A(f"### Metadata & flags ({len(feature_config['metadata_and_flags'])} fields)")
    A("")
    for f in feature_config["metadata_and_flags"]:
        A(f"- `{f}` ({'demoted by 70% rule' if f in [vf for vf in verdicts if verdicts[vf]['verdict']=='DEMOTE_TO_FLAG'] else 'pre-designated flag'})")
    A("")

    A("---")
    A("")
    A("## 5. Task 5 — Reliability Check")
    A("")
    A(f"Re-extracted {RELIABILITY_N} threads with salt='{RELIABILITY_SALT}' (fresh API calls, "
      f"same prompt). Cost: ${task5_cost:.4f}.")
    A("")
    A("### Per-Field Agreement")
    A("")
    A("| Field | Type | N valid | Score | Threshold | Status |")
    A("|-------|------|---------|-------|-----------|--------|")
    for field in ORDINAL_FIELDS:
        fa = field_agreement.get(field, {})
        score = fa.get("kappa")
        n = fa.get("n_valid", 0)
        score_str = f"κ={score:.3f}" if score is not None else "N/A"
        status = "⚠️ LOW" if score is not None and score < 0.40 else "OK"
        A(f"| {field} | ordinal | {n} | {score_str} | κ≥0.40 | {status} |")
    for field in CATEGORICAL_VALID:
        fa = field_agreement.get(field, {})
        score = fa.get("agreement")
        n = fa.get("n_valid", 0)
        score_str = f"{score*100:.1f}%" if score is not None else "N/A"
        status = "⚠️ LOW" if score is not None and score < 0.60 else "OK"
        A(f"| {field} | categorical | {n} | {score_str} | ≥60% | {status} |")
    A("")

    if low_reliability:
        A("### Low-Reliability Fields (caution notes for Phase 3)")
        A("")
        for field, reason in low_reliability:
            A(f"- **`{field}`** ({reason}): interpret cluster separation on this field with caution; "
              f"it is noisier than average. Do not anchor personas solely on this field.")
        A("")
    else:
        A("No fields fell below reliability thresholds.")
        A("")

    A("---")
    A("")
    A("## 6. Reviewer Checklist")
    A("")
    A("- [ ] Field arbitration verdicts in Section 3 are accepted")
    A("- [ ] Confirmed feature set in Section 4 is accepted")
    A("- [ ] Reliability results in Section 5 are acceptable for Phase 3")
    A("- [ ] Parse failure rate is acceptable")
    A("- [ ] Schema violation rate is acceptable")
    A("- [ ] Total cost is within budget")
    A("")
    A("**→ Hard stop. Phase 3 is BLOCKED until supervisor approves this report.**")

    PHASE2_FULL_SUMMARY.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Report: {PHASE2_FULL_SUMMARY}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Phase 2 — Tasks 4, 4b, 4c, 5")
    print(f"Base: {BASE}")

    # Task 4
    results, failures, cost_stats = task4_full_extraction()

    # Parquet + validation
    df, violation_log = build_parquet(results, failures)

    # Task 4b
    miss_stats, verdicts = task4b_missingness(df)

    # Task 4c
    feature_config = task4c_feature_config(verdicts)

    # Task 5
    field_agreement, low_reliability, t5_cost, t5_in, t5_out = task5_reliability(df, results)

    # Full summary report
    build_full_summary(
        df, results, failures, cost_stats, violation_log,
        miss_stats, verdicts, feature_config,
        field_agreement, low_reliability, t5_cost, t5_in, t5_out,
    )

    print("\n" + "="*60)
    print("CHECKPOINT: Phase 2 Tasks 4-5 complete.")
    print("→ Review reports/phase2_full_summary.md before Phase 3.")
    print("→ Phase 3 is BLOCKED pending supervisor approval.")
    print("="*60)


if __name__ == "__main__":
    main()
