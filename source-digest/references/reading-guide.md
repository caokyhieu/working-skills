# Reading guide

## Pass order — paper

1. **Abstract, intro, conclusion**: the claimed contribution. Write down the claims as a list; later sections must support each one.
2. **Method**: rewrite the mechanism in your own words with pseudocode. If you can't, something is missing. Record what.
3. **Experiments + appendix**: extract the protocol (below) and copy the results.
4. **Related work**: note the 3–5 closest prior works and how the paper claims to differ. idea-extension reuses this.
5. **Code**: compare the configs and evaluation scripts against the paper text.

## Pass order — open-source project

1. **README, docs, design/architecture notes**: what it claims to do and why it exists. List the claims.
2. **Mechanism in code**: find the files implementing the core idea; record paths and the commit. Summarise the algorithm and data structures in your own words. Note configuration flags that change behaviour.
3. **Benchmarks**: benchmark scripts, CI perf jobs, published numbers in docs/blog/release notes, with the commit and hardware if stated. Check what baselines were compared and how they were configured.
4. **Changelog, issues, PRs, discussions**: known limitations, regressions, disputed numbers, roadmap. Maintainer replies in issues are often the best statement of assumptions.
5. **Adoption signals**: stars are weak; production users, dependents, and release cadence are stronger. Record licence.

## Pass order — technical blog post

1. **Who wrote it and why**: vendor marketing, engineering team write-up, independent benchmark, or personal post. Record any conflict of interest.
2. **Claims**: list them; separate measured from asserted.
3. **Setup**: hardware, versions, data, workload, and whether code or notebooks are linked. A post without a reproducible setup is `claim-only`.
4. **Underlying source**: if it summarises a paper or a release, digest that as well or link to its digest and note differences.
5. **Discussion**: comments, Hacker News / Reddit / mailing-list threads and follow-up posts often surface counter-evidence. Record the strongest objection.

## Formulation pass (all types)

After the mechanism is clear, step back [TM-5]: state the problem the way a textbook would, with no reference to the paper's domain nouns. Inputs, outputs, objective, constraints, regime. Then ask which other fields solve the same formulation and what they call it (ML ↔ DB ↔ systems ↔ IR ↔ OR). Two minutes here is what makes a paper from another field findable for a company problem later.

## Claim check

For each claim in the intro, record which experiment supports it and how strong the support is: `strong` (multiple datasets, variance reported, fair baselines), `moderate`, `weak` (single dataset, no variance, untuned baselines) or `unsupported`. Weakly supported claims are extension opportunities, and they are also risks for reproduction.

## Protocol checklist

### ML / AI papers
- Datasets: name, version, source URL, size, splits (official or custom), filtering, tokenization, augmentation
- Model: architecture, parameter count, initialization or pretrained checkpoint (exact name)
- Training: optimizer, LR and schedule, batch size, epochs or steps, regularization, mixed precision, early stopping, checkpoint selection
- Tuning: search space, number of trials, selection metric, whether baselines were tuned equally
- Evaluation: metric definitions (macro or micro, k, normalization), test-time settings (decoding, temperature, prompts), number of seeds, how variance is reported
- LLM papers: model versions and dates, prompts (copy them), judge models, contamination checks, API vs local
- Compute: GPU type and count, training time, inference cost

### Database / systems papers
- Workloads: benchmark (TPC-H/DS, JOB, YCSB, SIFT/GIST/Deep1B, …), scale factor, query set, data distribution and skew, read/write mix
- System: engine and version, configuration knobs, index settings, memory/buffer size, storage medium
- Hardware: CPU model, cores/threads, RAM, disk/SSD/NVMe, network, NUMA pinning
- Measurement: warmup, repetitions, cold vs warm cache, reported statistic (mean/median/p99), timeouts
- Metrics: throughput, latency percentiles, build time, memory footprint, index size, recall/accuracy trade-off curve parameters
- Baselines: versions and tuning (were they run at their best settings?)

### Open-source / blog sources
- Benchmarks run by the project on hardware favourable to it; baselines at default settings
- Numbers from a demo dataset rather than a standard benchmark
- No variance, single run, or "up to N×" phrasing
- Behaviour that depends on flags not mentioned in the headline claim

## Red flags to record

- Baselines copied from other papers under different settings
- Best-of-N seeds, or no variance reported
- Test-set tuning, or selection criteria not stated
- Numbers that differ between tables or between paper and code
- Cost left out (build time, memory, training compute) when the method trades cost for quality
- A benchmark subset chosen without justification
