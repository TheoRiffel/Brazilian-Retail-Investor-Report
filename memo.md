# Brazilian retail on Reddit: three personas, one product

**Decade partner brief — Phase 4 deliverable** · 2026-05-21

**TL;DR.** Brazilian retail investors on Reddit divide into three posture-led
personas — **Em Busca de Sossego** (the Sossego-Seeker, 47.6%), **O Sardinha**
(the euphoric speculator, 18.4%), and **O Cético Irônico** (the ironic
skeptic, 30.0%). **Build an integrated income-tax (IR) preparation tool for
the Sossego-Seeker** — the largest, most stable, and most addressable
persona — as the wedge into a broader pre-decision-validation product.

**The signature insight.** Brazilian retail investors on Reddit sort by
**emotional posture**, not by capital or knowledge. The dominant clustering
axis carries roughly 3.8× the weight of the next; the classical
"beginner / intermediate / advanced" axes sit in the bottom half. Any
segmentation that ignores posture misses the signal.

**Caveat.** Scope is Reddit-active investors (2020–2024, r/investimentos +
r/farialimabets) — younger, more online, more vocal than the median
Brazilian. Findings are hypothesis-generating, not demographic truth.

## The three personas

- **Em Busca de Sossego (47.6%)** — cautious, validation-seeking, mainstream.
  Invests to stop worrying about money, not to maximize return.
  > *"estou juntando uma grana para futuramente conseguir ter um pouco de
  > sossego em questões financeiras"* — `ipn9s4`

  Stable across all macro windows. **High confidence — all three methods agree.**

- **O Sardinha (18.4%)** — euphoric retail speculator, farialimabets-native,
  crypto-heavy. **Shrinking 51% → 16% as Selic rose (A→C).** They don't
  graduate; they thin out. High confidence.

- **O Cético Irônico (30.0%)** — defensively-ironic, system-distrusting.
  **Growing 29.5% → 38%** — as speculators thin out, the cynical posture
  absorbs. **Real posture, fuzzy boundaries** (posture-reading methods agree;
  topic method does not isolate it).

## The opportunity — Sossego-Seeker, via IR

The Sossego-Seeker's most concrete recurring pain is **April**. Every year
they discover that investing came with a tax obligation no one front-loaded,
that brokers don't auto-calculate, and B3 doesn't either.

> *"Eu também achava que as corretoras e/ou a B3 iriam calcular
> automaticamente"* — `1aopejb`

This is the wedge: **specific, annual, high-stakes**. The same user spends
eleven more months on softer paralysis pain — capital parked while they wait
for personalized validation — which the IR product can expand into once
trust is earned.

**Why now.** The Selic cycle is doing segmentation work: speculators
thinning (51% → 16% A→C); cautious investors are the baseline that grows as
fixed income reclaims relevance. The macro regime favors the largest, most
stable persona.

## What we'd build

An **integrated IR-preparation tool** that ingests broker
`informes-de-rendimentos`, reconciles holdings across institutions, and
outputs a plain-language, pre-filled income-tax declaration the user can
submit with confidence. **Wedge:** the April moment. **Expansion:**
year-round pre-decision validation — *"yes, this fits you"* — the deeper
pain the user is already publicly asking for.

**Defensibility.** No single broker has an incentive to reconcile across
competitors; the cross-institution layer is the natural moat. The trust
earned at the annual moment opens the expansion into year-round validation
that no single-broker product can replicate.

**Validate first.** The IR pain is documented in 2020–2024 corpus; broker
and B3 IR-automation may have advanced since. Quick desk check of the top
brokers and Receita's IR program before committing build.

## Why not the other two

- **Not O Sardinha.** Real pains, but the ethical response is **harm
  reduction and off-ramps, not "trade better" tools**. Smaller and shrinking.
- **O Cético Irônico — win later, via earned credibility.** Large and
  growing, but marketing-resistant; the path is to earn their respect by
  quietly executing on the Sossego-Seeker product first, then expand. When
  reached, tax friction must stay **painless compliance, never
  facilitation** — the corpus contains tax gray-zone behavior; we observe
  it, we never build for it.

## Method + scope

Three independent clustering methods (attribute / embedding / LLM-summary)
over ~3,600 stratified Reddit threads; persona percentages use the
attribute-partition as a single denominator. Methodology, hypothesis tests
(H1–H4), persona profiles, pains/needs, and cost log in `reports/phase3*.md`
and `reports/phase4{a,b,c}_*.md`.
