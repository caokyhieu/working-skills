#!/usr/bin/env python3
"""Plot benchmark results from runs.jsonl and compute improvements over a baseline.

Usage:
    plot_results.py results/runs.jsonl --baseline hnsw --out figures \
        [--roles baseline,extension,ablation] [--metrics recall@10,latency_p99_ms] \
        [--lower-is-better latency_p99_ms] [--tradeoff throughput_qps recall@10] \
        [--min-seeds 3] [--table results/improvements.md]

Outputs per metric: <out>/<metric>.svg/.png (grouped bars, mean with 95% CI),
<out>/<metric>.csv (plotted numbers), and <out>/delta_<metric>.svg/.png (relative
change vs baseline with 95% CI of the difference). Optional trade-off scatter.
Writes a Markdown improvement table (default <out>/improvements.md).
Requires matplotlib; statistics use the standard library only.
"""

import argparse
import csv
import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict

# 0.975 quantile of Student's t for df = 1..30
T975 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
        2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
        2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]

LOWER_HINT = re.compile(r"(latency|time|_ms$|_s$|memory|mem_|size|loss|error|err$|perplexity|cost|mse|mae|rmse)", re.I)

CHARCOAL, RED, GREY = "#363338", "#983C45", "#8C8A8E"
BASELINE_COLORS = [CHARCOAL, GREY, "#5E6B73", "#B5B3B7", "#4A5A52"]
EXTENSION_COLORS = [RED, "#6E2A31", "#B8505A"]
ABLATION_COLORS = ["#D98E94", "#E8B9BD", "#C77A80"]


def t_crit(df):
    if df < 1:
        return float("nan")
    df = int(math.floor(df))
    if df <= 30:
        return T975[df - 1]
    return 2.000 if df <= 60 else 1.980 if df <= 120 else 1.960


def load_ok_runs(path, roles):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"warning: skipping invalid JSON line: {line[:60]}", file=sys.stderr)
    superseded = {rid for r in records for rid in (r.get("supersedes") or [])}
    return [r for r in records
            if r.get("status") == "ok" and r.get("role") in roles and r.get("run_id") not in superseded]


def collect(runs):
    """values[(metric, dataset, split)][method] = {seed: value}; role_of[method] = role."""
    values = defaultdict(lambda: defaultdict(dict))
    role_of = {}
    for r in runs:
        method = r["method"]
        if role_of.setdefault(method, r["role"]) != r["role"]:
            sys.exit(f"error: method `{method}` appears with roles {role_of[method]} and {r['role']}; "
                     "rename one so plots are unambiguous")
        for metric, v in (r.get("metrics") or {}).items():
            if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
                cell = values[(metric, r["dataset"], r.get("split", "test"))][method]
                if r["seed"] in cell:
                    print(f"warning: duplicate seed {r['seed']} for {method}/{r['dataset']}/{metric}; "
                          "keeping the later record", file=sys.stderr)
                cell[r["seed"]] = v
    return values, role_of


def summarize(vals):
    n = len(vals)
    mean = statistics.fmean(vals)
    std = statistics.stdev(vals) if n > 1 else float("nan")
    half = t_crit(n - 1) * std / math.sqrt(n) if n > 1 else float("nan")
    return n, mean, std, half


def compare(base, other, lower_is_better, min_seeds):
    """Difference other - base with 95% CI; paired on shared seeds when all seeds match."""
    b, o = list(base.values()), list(other.values())
    diff = statistics.fmean(o) - statistics.fmean(b)
    rel = diff / abs(statistics.fmean(b)) if statistics.fmean(b) != 0 else float("nan")
    if len(b) < min_seeds or len(o) < min_seeds:
        return diff, rel, float("nan"), "unpaired", "too few seeds"
    if set(base) == set(other):
        d = [other[s] - base[s] for s in base]
        n = len(d)
        sd = statistics.stdev(d)
        half = t_crit(n - 1) * sd / math.sqrt(n)
        test = "paired"
    else:
        vb, vo = statistics.variance(b), statistics.variance(o)
        se2 = vb / len(b) + vo / len(o)
        denom = (vb / len(b)) ** 2 / (len(b) - 1) + (vo / len(o)) ** 2 / (len(o) - 1)
        df = se2 ** 2 / denom if denom > 0 else len(b) + len(o) - 2
        half = t_crit(df) * math.sqrt(se2)
        test = "welch"
    lo, hi = diff - half, diff + half
    if lo <= 0 <= hi:
        verdict = "no clear difference"
    else:
        better = (hi < 0) if lower_is_better else (lo > 0)
        verdict = "better" if better else "worse"
    return diff, rel, half, test, verdict


def fmt(x, digits=4):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{digits}g}"


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)


def method_order(methods, role_of, baseline):
    rank = {"baseline": 0, "repro_baseline": 0, "extension": 1, "ablation": 2}
    return sorted(methods, key=lambda m: (m != baseline, rank.get(role_of[m], 1), m))


def colors_for(methods, role_of):
    colors, bi, ei, ai = {}, 0, 0, 0
    for m in methods:
        if role_of[m] == "extension":
            colors[m] = EXTENSION_COLORS[ei % len(EXTENSION_COLORS)]
            ei += 1
        elif role_of[m] == "ablation":
            colors[m] = ABLATION_COLORS[ai % len(ABLATION_COLORS)]
            ai += 1
        else:
            colors[m] = BASELINE_COLORS[bi % len(BASELINE_COLORS)]
            bi += 1
    return colors


def setup_matplotlib():
    try:
        import matplotlib
    except ImportError:
        sys.exit("error: matplotlib is required (pip install matplotlib)")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
        "font.size": 11, "axes.titlesize": 13, "axes.labelsize": 11,
        "axes.edgecolor": CHARCOAL, "axes.labelcolor": CHARCOAL,
        "xtick.color": CHARCOAL, "ytick.color": CHARCOAL, "text.color": CHARCOAL,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "axes.grid.axis": "y", "grid.color": "#E4E2E5", "grid.linewidth": 0.8,
        "legend.frameon": False, "svg.fonttype": "none", "savefig.dpi": 200,
    })
    return plt


def save(fig, out, stem):
    for ext in ("svg", "png"):
        fig.savefig(os.path.join(out, f"{stem}.{ext}"), bbox_inches="tight")


def bar_plot(plt, metric, cells, role_of, baseline, lower, out, min_seeds):
    datasets = sorted({(d, s) for (d, s) in cells})
    methods = method_order({m for c in cells.values() for m in c}, role_of, baseline)
    colors = colors_for(methods, role_of)
    width = 0.8 / max(len(methods), 1)
    fig, ax = plt.subplots(figsize=(max(4.5, 1.6 * len(datasets) + 1.5), 3.6))
    rows = []
    for i, m in enumerate(methods):
        xs, means, errs = [], [], []
        for j, key in enumerate(datasets):
            seeds = cells[key].get(m)
            if not seeds:
                continue
            n, mean, std, half = summarize(list(seeds.values()))
            xs.append(j - 0.4 + width * (i + 0.5))
            means.append(mean)
            errs.append(0 if math.isnan(half) else half)
            rows.append([m, role_of[m], key[0], key[1], n, mean, std, half])
        ax.bar(xs, means, width * 0.92, yerr=errs, capsize=3, color=colors[m],
               error_kw={"elinewidth": 1, "ecolor": CHARCOAL}, label=m)
    ax.set_xticks(range(len(datasets)))
    ax.set_xticklabels([d if s == "test" else f"{d}\n({s})" for d, s in datasets])
    arrow = "↓ lower is better" if lower else "↑ higher is better"
    ax.set_ylabel(f"{metric}  ({arrow})")
    few = [r for r in rows if r[4] < min_seeds]
    note = f"\nwarning: {len(few)} bar(s) with < {min_seeds} seeds" if few else ""
    ax.set_title(f"{metric}: mean ± 95% CI across seeds{note}", loc="left")
    ax.legend(ncol=min(len(methods), 4), loc="upper left", bbox_to_anchor=(0, -0.12))
    stem = safe_name(metric)
    save(fig, out, stem)
    plt.close(fig)
    with open(os.path.join(out, f"{stem}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["method", "role", "dataset", "split", "n", "mean", "std", "ci95_half"])
        w.writerows(rows)
    return stem


def delta_plot(plt, metric, deltas, role_of, baseline, lower, out):
    """deltas: list of (dataset, split, method, rel_pct, rel_half_pct, verdict)."""
    datasets = sorted({(d, s) for d, s, *_ in deltas})
    methods = method_order({m for _, _, m, *_ in deltas}, role_of, baseline)
    colors = colors_for(methods, role_of)
    step = 0.7 / max(len(methods), 1)
    fig, ax = plt.subplots(figsize=(max(4.5, 1.6 * len(datasets) + 1.5), 3.4))
    ax.axhline(0, color=CHARCOAL, linewidth=1)
    for i, m in enumerate(methods):
        pts = [(datasets.index((d, s)), r, h) for d, s, mm, r, h, _ in deltas if mm == m]
        for x, r, h in pts:
            x = x - 0.35 + step * (i + 0.5)
            few = math.isnan(h)  # too few seeds: hollow marker, no CI
            ax.errorbar([x], [r], yerr=None if few else [h], fmt="o", ms=7, capsize=4, color=colors[m],
                        ecolor=colors[m], mfc="white" if few else colors[m],
                        label=m if x == min(xx - 0.35 + step * (i + 0.5) for xx, _, _ in pts) else None)

    ax.set_xticks(range(len(datasets)))
    ax.set_xticklabels([d if s == "test" else f"{d}\n({s})" for d, s in datasets])
    ax.set_xlim(-0.5, len(datasets) - 0.5)
    ax.set_ylabel(f"Δ% vs {baseline}  ({'↓' if lower else '↑'} better)")
    note = "\nhollow marker = too few seeds, no CI" if any(math.isnan(h) for *_, h, _ in deltas) else ""
    ax.set_title(f"{metric}: change vs {baseline}, 95% CI{note}", loc="left")
    ax.legend(ncol=min(len(methods), 4), loc="upper left", bbox_to_anchor=(0, -0.12))
    stem = safe_name(f"delta_{metric}")
    save(fig, out, stem)
    plt.close(fig)
    return stem


def tradeoff_plot(plt, xm, ym, values, role_of, baseline, out):
    by_dataset = defaultdict(dict)
    for (metric, d, s), cell in values.items():
        if metric in (xm, ym):
            for m, seeds in cell.items():
                by_dataset[(d, s)].setdefault(m, {})[metric] = list(seeds.values())
    stems = []
    for (d, s), methods in sorted(by_dataset.items()):
        methods = {m: v for m, v in methods.items() if xm in v and ym in v}
        if not methods:
            continue
        order = method_order(methods, role_of, baseline)
        colors = colors_for(order, role_of)
        fig, ax = plt.subplots(figsize=(5, 3.8))
        for m in order:
            _, mx, _, hx = summarize(methods[m][xm])
            _, my, _, hy = summarize(methods[m][ym])
            ax.errorbar(mx, my, xerr=0 if math.isnan(hx) else hx, yerr=0 if math.isnan(hy) else hy,
                        fmt="o", ms=7, color=colors[m], ecolor=colors[m], capsize=3, label=m)
        ax.grid(True, axis="both")
        ax.set_xlabel(xm)
        ax.set_ylabel(ym)
        ax.set_title(f"{ym} vs {xm} — {d}" + ("" if s == "test" else f" ({s})"), loc="left")
        ax.legend(loc="best")
        stem = safe_name(f"tradeoff_{ym}_vs_{xm}_{d}_{s}")
        save(fig, out, stem)
        plt.close(fig)
        stems.append(stem)
    return stems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs")
    ap.add_argument("--baseline", required=True, help="method name to compare against")
    ap.add_argument("--out", default="figures")
    ap.add_argument("--roles", default="baseline,extension,ablation")
    ap.add_argument("--metrics", help="comma-separated; default all")
    ap.add_argument("--lower-is-better", default="", help="comma-separated metrics; overrides name heuristic")
    ap.add_argument("--higher-is-better", default="", help="comma-separated metrics; overrides name heuristic")
    ap.add_argument("--tradeoff", nargs=2, metavar=("X_METRIC", "Y_METRIC"))
    ap.add_argument("--min-seeds", type=int, default=3)
    ap.add_argument("--table", help="Markdown improvement table path (default <out>/improvements.md)")
    args = ap.parse_args()

    roles = set(args.roles.split(","))
    runs = load_ok_runs(args.runs, roles)
    if not runs:
        sys.exit("error: no ok runs for the selected roles")
    values, role_of = collect(runs)
    if args.baseline not in role_of:
        sys.exit(f"error: baseline `{args.baseline}` not found; methods: {sorted(role_of)}")

    lower_set = set(filter(None, args.lower_is_better.split(",")))
    higher_set = set(filter(None, args.higher_is_better.split(",")))
    wanted = set(args.metrics.split(",")) if args.metrics else {k[0] for k in values}

    def is_lower(metric):
        if metric in lower_set:
            return True
        if metric in higher_set:
            return False
        return bool(LOWER_HINT.search(metric))

    os.makedirs(args.out, exist_ok=True)
    plt = setup_matplotlib()

    by_metric = defaultdict(dict)
    for (metric, d, s), cell in values.items():
        if metric in wanted:
            by_metric[metric][(d, s)] = cell

    figures = []
    for metric in sorted(by_metric):
        figures.append(bar_plot(plt, metric, by_metric[metric], role_of, args.baseline,
                                is_lower(metric), args.out, args.min_seeds))
    if args.tradeoff:
        figures += tradeoff_plot(plt, *args.tradeoff, values, role_of, args.baseline, args.out)

    lines = [f"# Improvements over `{args.baseline}`", "",
             f"Source: `{args.runs}` · roles: {', '.join(sorted(roles))} · 95% CI of the difference "
             f"(paired on matching seeds, else Welch) · min seeds {args.min_seeds}", "",
             "| metric | dataset | split | method | role | baseline mean ± std (n) | method mean ± std (n) "
             "| Δ | Δ% | 95% CI of Δ | test | verdict | figure |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    heuristic = []
    for metric in sorted(by_metric):
        lower = is_lower(metric)
        deltas = []
        if metric not in lower_set | higher_set:
            heuristic.append(f"{metric}: {'lower' if lower else 'higher'} is better")
        for (d, s), cell in sorted(by_metric[metric].items()):
            base = cell.get(args.baseline)
            if not base:
                continue
            _, bm, bs, _ = summarize(list(base.values()))
            for m in method_order(cell, role_of, args.baseline):
                if m == args.baseline:
                    continue
                n, mm, ms, _ = summarize(list(cell[m].values()))
                diff, rel, half, test, verdict = compare(base, cell[m], lower, args.min_seeds)
                ci = "—" if math.isnan(half) else f"[{fmt(diff - half)}, {fmt(diff + half)}]"
                if bm != 0:
                    deltas.append((d, s, m, 100 * diff / abs(bm), 100 * half / abs(bm), verdict))
                lines.append(f"| {metric} | {d} | {s} | {m} | {role_of[m]} | {fmt(bm)} ± {fmt(bs)} ({len(base)}) "
                             f"| {fmt(mm)} ± {fmt(ms)} ({n}) | {fmt(diff)} | {fmt(100 * rel, 3)}% | {ci} "
                             f"| {test} | {verdict} | delta_{safe_name(metric)}.svg |")
        if deltas:
            figures.append(delta_plot(plt, metric, deltas, role_of, args.baseline, lower, args.out))
    if heuristic:
        lines += ["", "Metric direction inferred from names (check, override with --lower/--higher-is-better):", ""]
        lines += [f"- {h}" for h in heuristic]
    table = args.table or os.path.join(args.out, "improvements.md")
    os.makedirs(os.path.dirname(table) or ".", exist_ok=True)
    with open(table, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"figures: {', '.join(figures)} in {args.out}/")
    print(f"improvement table: {table}")


if __name__ == "__main__":
    main()
