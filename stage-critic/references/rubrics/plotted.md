# Rubric — plots and summary

Inputs to read: `results/runs.jsonl`, `results/summary.md`, `figures/*.csv` (the data behind each figure), `ideas/proposal.md` §4–§5.

1. **Claims carry numbers and run filters.** Each bullet in `summary.md` has mean ± std, n seeds, figure path and the run-id filter. Recompute two claims from `runs.jsonl`; a mismatch is a blocker.
2. **Hypothesis verdict stated.** `summary.md` says whether Y was reached against Z on B under C, using the proposal's exact threshold. Hedged wording that avoids the verdict is a major.
3. **Intervals shown.** Every comparison plot shows CI or std; single-run bars without variance are a blocker.
4. **Axis honesty.** No truncated y-axes on bar charts, no log axes without a label, no cherry-picked subset of datasets without the full set in an appendix figure.
5. **"Where it does not help" filled.** Empty only if every setting improved; check `runs.jsonl` for settings where the extension lost.
6. **Cost plotted.** If the method trades cost (time, memory, index size) for quality, is the trade-off plotted, not only the quality?
7. **Figures reproducible.** Each figure has a `.csv` and a source script under `figures/src/`.
