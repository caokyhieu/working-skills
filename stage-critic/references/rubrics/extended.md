# Rubric — extension runs

Inputs to read: `ideas/proposal.md` §4–§6 (hypothesis, falsification, experiment table), `experiments/extension.md`, `results/runs.jsonl`.

1. **Hypothesis unchanged.** X, M, Z, B, C, Y in `extension.md` are byte-identical to the approved proposal, or the proposal's change log records an approved change. Silent change is a blocker.
2. **Every planned group ran.** main, ablation, sensitivity (and company variant if planned) each have runs; missing groups are named with a reason.
3. **Same harness as reproduction.** Extension and baseline runs share config except the mechanism under test; diff the configs. A second difference is a blocker.
4. **Seeds match the plan.** Same seeds for baseline and extension; per-seed results present.
5. **Failures kept.** Runs with `status: failed` or `timeout` are reported, not filtered.
6. **No peeking.** Selection of the reported configuration was not made on the test split; tuning trials are in `runs.jsonl` with `role: ablation` or `smoke`.
7. **Falsifier evaluated.** `extension.md` states explicitly whether the falsification criterion from the proposal was met.
