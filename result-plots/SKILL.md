---
name: result-plots
description: Turn benchmark run records into honest, publication- and deck-ready figures and an improvement summary — mean with 95% CI across seeds, change vs baseline with confidence intervals, trade-off curves, and claims that each link to a figure and to runs. Use after experiments finish, when plotting results, showing improvement over a baseline, or preparing figures for insight-ppt.
---

# Result Plots

Show what the experiments actually found, clearly enough that a reviewer believes the improvement and sees its limits. Every number in a figure or claim comes from `results/runs.jsonl`. Never type numbers by hand, and never use numbers remembered from chat.

Follow the research-poc workspace contract. Read `ideas/proposal.md` (hypothesis, threshold, falsification), `experiments/extension.md` and `results/runs.jsonl`. Write `figures/` and `results/summary.md` using [templates/summary.md](templates/summary.md).

## 1. Check the data first

If bench-setup is installed, run its `scripts/check_results.py` on the run records. Schema errors must be fixed upstream before plotting. List any warnings in the summary under Caveats. Plotting bad data carefully is still wrong.

## 2. Generate the standard figures

```sh
python <skill-dir>/scripts/plot_results.py results/runs.jsonl --baseline <method> --out figures \
  --table results/improvements.md [--metrics ...] [--lower-is-better ...] [--tradeoff X Y]
```

The script needs matplotlib. If it's missing, install it in the project environment or a virtual environment; don't modify the system Python. It writes, for each metric: grouped bars with 95% CIs, a `delta_<metric>` chart of the relative change against baseline with the CI of the difference, a CSV of the plotted numbers, an improvement table, and optional trade-off scatter plots. Differences are paired on seeds when the seed sets match, and use a Welch test otherwise.

Check the inferred metric directions printed at the end of the table and override them with `--lower-is-better` or `--higher-is-better` when they're wrong. Pass `--baseline` as the strongest fair baseline, not the weakest.

## 3. Add figures the claim needs

Read [references/plot-style.md](references/plot-style.md). The standard figures cover most main comparisons. Write extra plotting code in `figures/src/` (reading `runs.jsonl`, same style) when the hypothesis needs:

- **Trade-off / Pareto curves** (recall vs QPS, accuracy vs cost, quality vs latency): plot the whole curve over parameter sweeps, not a single operating point.
- **Scaling**: metric vs data size, model size or load, on log axes when the range covers orders of magnitude.
- **Ablations**: delta chart where each ablation removes one component.
- **Sensitivity**: metric vs hyperparameter, with the chosen value marked.
- **Per-slice breakdown**: where the extension helps and where it hurts (dataset, query type, length bucket).

Keep the plotting source for every figure. insight-ppt may need to redraw a chart as a native, editable one.

## 4. Write the summary

Test the hypothesis against the pre-registered threshold and falsification criterion from `proposal.md` using the improvement table:

- **Supported:** the lower CI bound of the improvement meets the threshold on the benchmarks named in the hypothesis.
- **Partially supported:** the improvement is clear but below the threshold, or holds on only some benchmarks.
- **Not supported:** no clear difference, or the falsification criterion is met.

Write one bullet per claim with the numbers, the figure and the source runs. Fill in **Where it does not help** from rows marked `worse` or `no clear difference`, and include the costs the extension adds. Don't lead with the best-looking dataset if the hypothesis names several.

## Honesty rules

- Never change the threshold, baseline, metric or dataset list after seeing results. If one of them was wrong, say so in the summary and keep the original verdict alongside.
- Don't start axes at a misleading value to make gaps look bigger. Use the delta chart to show small differences instead.
- Don't drop seeds, datasets or failed runs from figures. Mark missing data.
- `no clear difference` is not "slightly better". Don't describe noise as a trend.
- Keep `[reported]` numbers out of measured figures, or plot them with a distinct marker and a label.

## Done when

`summary.md` has a verdict against the proposal's exact threshold, every claim links to a figure and to runs, *Where it does not help* is filled from `runs.jsonl`, the figure source is saved, and the research-poc orchestrator has been told so it can run stage-critic (it recomputes two claims from `runs.jsonl` and checks axes and intervals) and complete the `plotted` stage. For the deck, hand insight-ppt `alignment.md`, `proposal.md`, `summary.md` and `figures/`.

## Update mode

When the research-poc workflow starts this stage with `mode: update` (a stale or reopened stage), follow the update-mode contract in research-poc's `references/workflow.md`:
- Read the previous output and the brief's `why` list. When `why` names a stage-critic review (`review revise: reviews/<stage>-<n>.md`), address every blocker and major at the location it cites, and record in the change log which were fixed and which are disputed, with the reason. Never edit the review file.
- Make the smallest correct change and leave unaffected content byte-identical.
- Add a Change log entry.
- If nothing needs to change, leave the file untouched and report that.

Report back to the orchestrator; don't mark the stage complete yourself.

For result-plots in particular: regenerate figures from `runs.jsonl` rather than editing them, and re-test the verdict against the current (approved) proposal threshold.
