---
name: bench-setup
description: Build and run a benchmark for an ML, AI, or database research idea — first reproduce the original paper's baseline on its own benchmark, then evaluate the proposed extension, ablations, and baselines in the same harness under equal budgets with multiple seeds and append-only run records. Use for setting up benchmark code, reproducing paper numbers, running experiment sweeps, or checking whether results are trustworthy.
---

# Bench Setup

Produce results a skeptical reviewer would accept. The deliverable is a comparison that is reproducible and fair, not a large number. Use the paper's own benchmark unless the approved proposal says otherwise. Reproduce before extending: an extension measured in a harness that cannot match the paper's baseline shows nothing.

This skill works inside the research-poc workspace. If `poc/<idea-id>/` exists, follow its `workspace-contract.md` for paths and file formats. If not, use the same layout under the current directory and tell the user.

## 1. Plan before code

Read the paper's `digest.md` (§7 benchmark protocol, §8 reported results, §9 protocol gaps) and `ideas/proposal.md` (§4 hypothesis, §5 falsification, §6 experiments, and the *mid-term exam* — the early kill test — from §0). If either is missing, extract the protocol from the paper directly and flag it.

Write `experiments/plan.md` from [templates/experiment-plan.md](templates/experiment-plan.md) and `experiments/reported_targets.json` with the numbers to reproduce. Resolve every protocol gap: take it from the official code or artifact, ask the user, or pick a documented default labelled `[assumption]`. Estimate compute for the smoke test, the reproduction and the full sweep. Ask for approval before the full sweep, and before any run that needs more compute than the user has already authorised.

## 2. Build the harness

Read [references/harness.md](references/harness.md). Prefer the authors' official code and baselines, pinned to a commit, over reimplementation. Wrap them; don't fork their logic. Put the extension behind a config switch in the same code path, so the only difference between baseline and extension is the method itself.

Every run is driven by a config file and appends one record to `results/runs.jsonl` using [references/results-schema.md](references/results-schema.md). Never type metric values by hand, and never edit or delete earlier records. Mark superseded runs by appending a new record, as the schema describes.

Run a `smoke` config (tiny data, one seed, a few minutes) end to end, including metric computation and the results check, before any real run.

## 3. Reproduce the baseline (workflow stage `reproduced`, gate)

Read [references/reproduction.md](references/reproduction.md). Run the paper's baseline, and the paper's own method if it is not the baseline, with `role: repro_baseline` on the required seeds. Then check:

```sh
python <skill-dir>/scripts/check_results.py results/runs.jsonl --targets experiments/reported_targets.json
```

Write `experiments/reproduction.md` with the verdict `REPRODUCED`, `PARTIAL` or `FAILED`, the checker output, every deviation from the paper, and a diagnosis for each miss. The orchestrator runs stage-critic on it (rubric: targets match the digest, tolerance not widened after the fact, baselines tuned as in the paper, every number traceable to run ids) before asking the user. Stop at this gate. Continue to the extension only on `REPRODUCED`, or on `PARTIAL` when the user explicitly accepts the caveats. The orchestrator records that decision as the `reproduced` gate approval. On `FAILED`, report back; do not tune the baseline until it matches, and do not adjust targets.

## 4. Run the extension (workflow stage `extended`)

Run the extension, the baselines and the ablations from the proposal under the same budget, data, splits, seeds and tuning effort. Tuning the extension harder than the baseline is a fairness violation. Either give both the same search space size and trial count, or use the paper's baseline hyperparameters and freeze the extension's before looking at test results.

Pick hyperparameters on validation data only. Report test results once per final config. If you had to look at test results to make a decision, say so in `extension.md`.

Run `check_results.py` again. It must report no schema errors, no fairness warnings left unexplained, and at least the planned number of seeds for every reported cell. Write `experiments/extension.md` covering what was run, the failures, the deviations from the plan, the checker output, and a first-pass verdict on the hypothesis against its falsification criterion. Leave charts and polished tables to result-plots.

## Honesty rules

- Report failed, crashed and diverged runs; don't rerun seeds until a good one appears.
- If the extension loses on some datasets or metrics, say so plainly.
- Keep `[reported]` numbers and `[measured]` numbers in separate columns. Never mix them in one comparison without labelling.
- An improvement smaller than the run-to-run std across seeds is not an improvement. Call it `no clear difference`.
- Do not claim a run finished, or a number exists, until the record is in `runs.jsonl`.

## Update mode

When the research-poc workflow starts this stage with `mode: update` (a stale or reopened stage), follow the update-mode contract in research-poc's `references/workflow.md`:
- Read the previous output and the brief's `why` list. When `why` names a stage-critic review (`review revise: reviews/<stage>-<n>.md`), address every blocker and major at the location it cites, and record in the change log which were fixed and which are disputed, with the reason. Never edit the review file.
- Make the smallest correct change and leave unaffected content byte-identical.
- Add a Change log entry.
- If nothing needs to change, leave the file untouched and report that.

Report back to the orchestrator; don't mark the stage complete yourself.

For bench-setup in particular: never delete or rewrite run records; append superseding runs. Re-run only the configs affected by the change, and re-state the compute estimate before running. A critic objection about a config difference between baseline and extension, or about a widened tolerance, is a blocker: fix the harness or record the justification in `plan.md`, don't argue it in the review.
