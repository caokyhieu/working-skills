# Plot style

These match insight-ppt's default V4 deck style, so figures drop into slides without restyling.

## Colors

| Use | Color |
|---|---|
| Primary text, axes, main baseline | charcoal `#363338` |
| Proposed extension (the method being argued for) | muted red `#983C45` |
| Additional extensions | `#6E2A31`, `#B8505A` |
| Ablations (variants of the extension) | light red `#D98E94`, `#E8B9BD` |
| Other baselines | grey `#8C8A8E`, `#5E6B73`, `#B5B3B7` |
| Grid | `#E4E2E5` |

Only the proposed method gets strong red. Use at most ~5 series per chart; split into panels beyond that. Keep each method's color the same across all figures. If a series is distinguished only by lightness, also use marker shape or direct labels.

## Layout

- Font: Arial (fall back to Liberation Sans / DejaVu Sans), 11 pt labels, 13 pt title
- Top and right spines off; light horizontal grid (both axes for scatter plots)
- Title states what is plotted and the uncertainty: `recall@10: mean ± 95% CI across seeds`
- Axis labels include units and direction: `latency p99 (ms, ↓ better)`
- Legend below the plot or direct labels; no box
- Export SVG (editable, text kept as text) + PNG at 200 dpi; keep source in `figures/src/`
- Size for slides: about 5×3.6 in for one chart and 10×3.6 in for a wide panel

## Chart choice

| Message | Chart |
|---|---|
| Method A vs B across datasets | grouped bars with CI; delta chart when the gap is small relative to the value |
| How much better, and how sure | delta chart (Δ% with CI of difference, zero line) |
| Quality vs cost trade-off | Pareto/trade-off curve over a parameter sweep, one line per method |
| Behavior as scale grows | line chart, log x-axis when needed, CI band |
| Which component matters | ablation delta chart, sorted by effect |
| Distribution across queries/seeds | box or violin plot with points |
| Latency | percentile (p50/p95/p99) bars or CDF; never mean latency alone |

## Integrity checks before export

- [ ] Bars start at zero; use a delta chart instead of cutting the axis
- [ ] Error bars defined in the title or caption (95% CI, n seeds)
- [ ] Same seeds and same budget for every plotted method (see check_results warnings)
- [ ] Log scales labelled
- [ ] Metric direction is correct
- [ ] Cells with fewer than the minimum seeds are marked
