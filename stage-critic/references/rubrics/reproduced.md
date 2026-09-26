# Rubric — reproduction

Inputs to read: `sources/*/digest.md` §7–§9, `experiments/plan.md`, `experiments/reported_targets.json`, `experiments/reproduction.md`, `results/runs.jsonl` (`role: repro_baseline`).

1. **Targets from the digest.** Each target value and location in `reported_targets.json` matches the digest §8. A target not in the digest is a blocker.
2. **Tolerance justified.** `abs` = 2× reported std where std exists; otherwise the `rel` value has a written reason. Tolerance widened after seeing results is a blocker unless the change log records why.
3. **Protocol matches.** For each §7 row, does `plan.md` use the same value, or record a deviation with reason? Silent deviations are major; a deviation in metric definition or test split is a blocker.
4. **Baselines at their best.** Were baselines tuned as the paper tuned them (or better)? A baseline at defaults when the paper tuned it is a blocker for later fairness.
5. **Seeds and variance.** ≥ 3 seeds (or the paper's count, whichever is higher) with std in the verdict.
6. **Verdict honest.** `PARTIAL` caveats name which targets missed and by how much; nothing is rounded into `PASS`.
7. **Runs traceable.** Every number in `reproduction.md` has run ids that exist in `runs.jsonl` with `status: ok`, `git_dirty: false`.
8. **Compute recorded.** Hardware and wall-clock recorded so the extension's cost can be compared.
