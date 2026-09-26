# Harness design

## Layout

```text
experiments/code/
  third_party/<paper-repo>/   # official code, pinned (git submodule or recorded commit)
  bench/
    run.py                    # single entry point: run.py --config <path> [--seed N]
    methods/                  # baseline adapters + extension, one module each
    data.py                   # dataset loading, splits, preprocessing (deterministic)
    metrics.py                # metric implementations, matching paper definitions
    record.py                 # builds and appends the run record
  environment.lock            # uv.lock / requirements.txt with hashes / conda env export
experiments/configs/
  smoke.yaml
  repro/<method>-<dataset>.yaml
  main/<method>-<dataset>.yaml
  ablation/<name>-<dataset>.yaml
```

Adapt to the paper's language and ecosystem, for example C++/Rust for database engines. Keep the rules below regardless.

## Rules

1. **One entry point, config-driven.** A run is completely determined by (config file, seed, git commit, environment). No hidden command-line overrides. If an override is needed, write a new config.
2. **Config hash.** Hash the resolved config (after defaults are merged, seed excluded) and store it as `config_hash`. The same method and dataset must have the same hash across seeds.
3. **Determinism.** Seed every source of randomness (Python, NumPy, framework, data loader workers, data sampling). Record where full determinism isn't possible (for example, cuDNN nondeterministic kernels, multithreaded query execution).
4. **Metrics match the paper.** Implement the exact definitions from the digest (averaging, k, tie handling, units, percentile method, warm or cold cache). If unsure, use the official evaluation script. Unit-test metrics on a tiny hand-computed example.
5. **Equal budgets.** Record `budget` on every run (epochs, trials, wall-clock limit, memory limit, hardware, threads). Baseline and extension on the same dataset must have equal budgets unless the proposal specifies otherwise.
6. **Systems benchmarks** (database, indexing, serving): report hardware model, CPU pinning, thread count, memory or cache settings, data size, and warmup vs measured iterations. Repeat enough times to report median and p95/p99 where relevant. Don't run other heavy jobs on the machine at the same time. Record `load_note` if the machine is shared.
7. **Clean commits.** Official runs require `git_dirty: false`. Dirty runs are allowed only with `role: smoke`.
8. **Failures are records.** Crashes, OOM, timeouts and divergence append a record with `status: failed` and an `error` message.
9. **No data leakage.** Fit preprocessing on train only. Never tune on test. Check that splits don't overlap with a hash check and log the result.
10. **Resumable sweeps.** Before launching, skip (config_hash, seed) pairs that already have an `ok` record, so reruns don't duplicate data.

## Seeds

Default: 5 seeds for ML training results, or 3 if a single run costs more than about 4 GPU-hours and the user agrees. Use the paper's count if it is higher. For deterministic systems benchmarks, use ≥ 5 repetitions per configuration. Use the same seed list for every method.

## Smoke test checklist

- [ ] Runs end to end in under 10 minutes
- [ ] Writes a valid record (`check_results.py` has no schema errors)
- [ ] Metric values are in a plausible range
- [ ] Rerunning with the same seed gives the same metrics, or the difference is documented
