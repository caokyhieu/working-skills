# Experiment plan — <idea-id>

**Hypothesis (from proposal):**
**Falsification criterion:**
**Approved by / date:**

## Benchmark

| Item | Paper protocol | Our setup | Source / `[assumption]` |
|---|---|---|---|
| Datasets & versions | | | |
| Splits / workloads | | | |
| Preprocessing | | | |
| Metrics (exact definition) | | | |
| Baselines & versions | | | |
| Hyperparameters | | | |
| Tuning procedure & budget | | | |
| Seeds / repetitions | | | |
| Hardware | | | |
| Software versions | | | |

## Protocol gaps and resolutions

| Gap | Resolution | Source (official code / user / assumption) |
|---|---|---|

## Runs

| Group | Role | Methods | Datasets | Seeds | Config dir | Est. compute |
|---|---|---|---|---|---|---|
| smoke | smoke | | | 1 | configs/smoke.yaml | |
| reproduction | repro_baseline | | | | configs/repro/ | |
| main | baseline, extension | | | | configs/main/ | |
| ablations | ablation | | | | configs/ablation/ | |

**Total estimated compute:**
**Compute authorised by user:**

## Fairness

- Budget parity:
- Tuning parity (search space, trials, selection metric on validation):
- Anything the extension gets that baselines don't (extra data, features, compute):

## Reproduction targets

See `reported_targets.json`. Tolerances fixed on <date> before any run.
