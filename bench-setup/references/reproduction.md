# Reproduction protocol

## Targets

Build `reported_targets.json` from the digest's reported results. Include the main baseline(s) and the paper's own method on at least the datasets the extension will use. Record the table or figure each number comes from. Values read off a plot get `"source": "Figure N (read from plot)"` and a wider tolerance.

Default tolerance, unless the user sets one:

- The paper reports std or CI: `{"abs": 2 * std}`.
- Accuracy-type metrics in [0, 1] with no variance reported: `{"abs": 0.01}`.
- Other metrics with no variance reported: `{"rel": 0.02}`.
- Systems throughput or latency on different hardware: compare the **relative** ordering and ratio between methods, not absolute values. Record the target as a ratio against a reference method and explain this in `reproduction.md`.

Write down tolerances **before** running. Never loosen them after seeing results. If one seems unreasonable afterwards, record the original verdict and the proposed change and ask the user.

## Verdicts

- **REPRODUCED**: every target is within tolerance, with the required number of seeds.
- **PARTIAL**: most targets are within tolerance, or the ordering and conclusions of the paper hold but some absolute values miss.
- **FAILED**: key targets miss and the paper's main conclusion does not hold in our harness.

## Diagnosing a miss

Work through these in order and record what you checked:

1. Metric definition (averaging, k, units, filtering, tie handling) matches the paper and official script
2. Dataset version, split, preprocessing and filtering
3. Hyperparameters, including defaults hidden in the official code that differ from the paper text
4. Training or tuning budget, early-stopping rule, checkpoint selection
5. Software versions (framework, CUDA, BLAS, compiler flags)
6. Hardware effects (systems papers), thread counts, memory limits
7. Seed variance: are the paper's numbers within our seed spread?
8. Known issues in the official repo (open GitHub issues, errata, later versions of the paper)

A fix is legitimate only if it moves the harness closer to the paper's **documented** protocol. Tuning the baseline until the number matches is not reproduction. If done, report it as tuning.

## `reproduction.md` structure

1. Verdict
2. Targets vs measured table: method, dataset, metric, `[reported]` value, `[measured]` mean ± std (n), delta, within tolerance?
3. Checker output (verbatim)
4. Deviations from the paper protocol, and why
5. Diagnosis of each miss
6. Implication for the extension stage
