# Screening rubric

Two passes. Pass 1 drops on title and abstract. Pass 2 writes the relevance chain for the survivors and only then scores. Don't digest during screening.

## Relevance chain (pass 2, required for every keep) [TM-1, TM-3, TM-4, TM-8]

| Field | What to write | Rejects the source when |
|---|---|---|
| **Problem** | research-map sub-problem id, e.g. `R1.b` | no sub-problem fits — say "no formulation match", it is useful next run |
| **Shared structure** | the *relation* both share: same objective, same binding constraint, or same bottleneck quantity. Restate the source's formulation (inputs → outputs, objective, constraints, regime) from the abstract and put it next to the map's | only topic words fit ("both are about retrieval", "both use LLMs") → `vocabulary-only`, drop or maybe |
| **Transfer distance** | `direct` (same formulation, same field) · `adjacent-field` (same formulation, other field or other name) · `analogy` (different formulation, shared structure through a bridging concept) | distance exceeds the map's *acceptable transfer distance* for that problem |
| **Bridging concept (B)** | required at `adjacent-field` and `analogy`: the concept the source and the sub-problem share without naming each other (the map lists candidates) | none can be named |
| **TRL** | 1–9 estimate with a reason (theory / simulation / public benchmark / deployed) | outside the map's wanted band without saying so |
| **Near-miss check** | compare against the problem's near-miss table and `calibration.md` rules | matches one — drop with the rule id |

**Fit is derived**, not guessed: `direct` with matching binding constraint = 5; `direct` on objective only, or `adjacent-field` with B named = 4; `analogy` with B named and a concrete transfer = 3; shared structure stated but weak = 2; vocabulary-only = 1. Prefer the 3–4 band for research directions [TM-3]; a 5 is often a reproduction candidate rather than an extension.

## Scores (pass 2)

| Criterion | 1 | 3 | 5 |
|---|---|---|---|
| **Fit** | vocabulary-only | adjacent-field or analogy with a named bridge | direct on objective and binding constraint |
| **Evidence** | claim-only, marketing | self-reported numbers with setup, or working code without benchmarks | peer-reviewed with variance, or independent reproduction |
| **Reproducibility** | no code, no data, unknown setup | code or data available, protocol partly specified | public code + standard benchmark + stated hardware; feasible on our compute |
| **Novelty potential** | already known or already done internally | incremental hooks only | clear weak spots or untested regimes that match our data or constraints |
| **Effort** (5 = low) | months of engineering before any measurement | weeks | days to a smoke test |

## Verdicts

- **keep**: fit ≥ 3 with a complete relevance chain, and evidence + reproducibility ≥ 6, and novelty ≥ 3. Or the user asked for this topic explicitly.
- **maybe**: chain plausible but the shared structure can't be stated from a skim (needs a digest), or strong on fit but weak on evidence or reproducibility (revisit when code or an independent benchmark appears).
- **drop**: fit ≤ 2, a near-miss or calibration rule matches, already screened (same idea, older version), or overlaps a funded initiative or a failed past attempt without addressing why it failed.

Be strict on structure, generous on field. A great paper with no formulation match is a drop with the reason "no formulation match"; a modest paper from another field that shares our binding constraint through a named bridge is a keep at fit 3–4.

## Pairwise ordering (when > 5 keeps) [TM-9]

Compare the top candidates in pairs: "which would we rather digest first, and why" — one line per pair, in the run report. Absolute scores are for screening; the order shown to the user comes from the pairs.

## Duplicate and version handling

- Same idea in several forms (paper + repo + blog post): record one entry per form, but link them with `--related <source-id>` and keep only the strongest evidence form as `keep`.
- Newer version of a screened source: add a new record with the version and a reason such as "v2 adds code"; the older record stays for history.

## Per-type checks

**Paper**: venue tier, baselines named, benchmarks standard, code link present, appendix has hyperparameters.
**Open-source**: licence compatible with company use, active maintenance (commits in last 6 months), benchmarks reproducible from the repo, production users named.
**Blog post**: author's affiliation and incentive, setup and versions stated, raw numbers or code linked, quality of the discussion thread.

## Reason line

Write it so a reader can decide without opening the source, chain first: `keep R1.b adjacent-field (B: density estimation): learned join-order model attacks the same cardinality-error bottleneck; JOB benchmark, code public, TRL 4; weak spot: static data only`.
