#!/usr/bin/env python3
"""Validate run records, aggregate metrics across seeds, and check paper targets.

Usage:
    check_results.py results/runs.jsonl [--targets experiments/reported_targets.json]
                     [--min-seeds 3] [--include-smoke]

Prints a Markdown report. Exit code 1 if schema errors are found, else 0.
Standard library only.
"""

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict

REQUIRED = {
    "run_id": str, "timestamp": str, "role": str, "method": str, "dataset": str,
    "split": str, "seed": int, "config_path": str, "config_hash": str,
    "git_commit": str, "git_dirty": bool, "budget": dict, "status": str, "metrics": dict,
}
ROLES = {"repro_baseline", "baseline", "extension", "ablation", "smoke"}
STATUSES = {"ok", "failed"}


def load_records(path):
    records, errors = [], []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"line {lineno}: invalid JSON ({e.msg})")
                continue
            if not isinstance(rec, dict):
                errors.append(f"line {lineno}: record is not a JSON object")
                continue
            rec["_line"] = lineno
            records.append(rec)
    return records, errors


def validate(records):
    errors, seen = [], {}
    for rec in records:
        where = f"line {rec['_line']} ({rec.get('run_id', '?')})"
        for key, typ in REQUIRED.items():
            if key not in rec:
                errors.append(f"{where}: missing `{key}`")
            elif not isinstance(rec[key], typ) or (typ is int and isinstance(rec[key], bool)):
                errors.append(f"{where}: `{key}` should be {typ.__name__}")
        if rec.get("role") not in ROLES:
            errors.append(f"{where}: unknown role `{rec.get('role')}`")
        if rec.get("status") not in STATUSES:
            errors.append(f"{where}: unknown status `{rec.get('status')}`")
        if rec.get("status") == "failed" and not rec.get("error"):
            errors.append(f"{where}: failed run without `error`")
        for name, value in (rec.get("metrics") or {}).items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
                errors.append(f"{where}: metric `{name}` is not a finite number")
        rid = rec.get("run_id")
        if rid in seen:
            errors.append(f"{where}: duplicate run_id (first at line {seen[rid]})")
        elif rid is not None:
            seen[rid] = rec["_line"]
    return errors


def active_records(records, include_smoke):
    superseded = set()
    for rec in records:
        superseded.update(rec.get("supersedes") or [])
    return [
        r for r in records
        if r.get("run_id") not in superseded and (include_smoke or r.get("role") != "smoke")
    ], len(superseded)


def fairness_warnings(records):
    warnings = []
    hashes, budgets, pairs = defaultdict(set), defaultdict(dict), defaultdict(list)
    for r in records:
        cell = (r.get("role"), r.get("method"), r.get("dataset"), r.get("split"))
        hashes[cell].add(r.get("config_hash"))
        if r.get("git_dirty") and r.get("role") != "smoke":
            warnings.append(f"`{r.get('run_id')}`: non-smoke run from a dirty git tree")
        if r.get("status") == "ok":
            pairs[(r.get("config_hash"), r.get("seed"))].append(r.get("run_id"))
            if r.get("role") in {"baseline", "extension"}:
                budget = json.dumps(r.get("budget"), sort_keys=True)
                budgets[(r.get("dataset"), r.get("split"))].setdefault(budget, set()).add(r.get("method"))
    for cell, hs in sorted(hashes.items(), key=str):
        if len(hs) > 1:
            warnings.append(f"{'/'.join(map(str, cell))}: {len(hs)} different config_hash values across runs")
    for (dataset, split), by_budget in sorted(budgets.items(), key=str):
        if len(by_budget) > 1:
            detail = "; ".join(f"{sorted(m)} -> {b}" for b, m in by_budget.items())
            warnings.append(f"{dataset}/{split}: baseline/extension budgets differ: {detail}")
    for (h, seed), ids in sorted(pairs.items(), key=str):
        if len(ids) > 1:
            warnings.append(f"config_hash {h} seed {seed}: {len(ids)} ok runs ({', '.join(map(str, ids))})")
    return warnings


def aggregate(records):
    values, failed = defaultdict(list), defaultdict(int)
    for r in records:
        cell = (r.get("role"), r.get("method"), r.get("dataset"), r.get("split"))
        if r.get("status") != "ok":
            failed[cell] += 1
            continue
        for name, value in (r.get("metrics") or {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value):
                values[cell + (name,)].append(value)
    rows = []
    for key in sorted(values, key=str):
        v = values[key]
        std = statistics.stdev(v) if len(v) > 1 else float("nan")
        rows.append({"key": key, "n": len(v), "mean": statistics.fmean(v), "std": std,
                     "failed": failed[key[:4]]})
    return rows, failed


def check_targets(targets, rows, min_seeds):
    by_key = {r["key"]: r for r in rows}
    out, verdicts = [], []
    for t in targets:
        key = ("repro_baseline", t["method"], t["dataset"], t.get("split", "test"), t["metric"])
        tol = t.get("tolerance") or {"rel": 0.02}
        allowed = tol["abs"] if "abs" in tol else abs(t["value"]) * tol["rel"]
        row = by_key.get(key)
        if row is None:
            verdicts.append("missing")
            out.append((t, None, None, allowed, "MISSING"))
            continue
        delta = row["mean"] - t["value"]
        if row["n"] < min_seeds:
            status = "TOO FEW SEEDS"
            verdicts.append("missing")
        elif abs(delta) <= allowed:
            status = "within"
            verdicts.append("within")
        else:
            worse = (delta < 0) == t.get("higher_is_better", True)
            status = "MISS (worse)" if worse else "MISS (better)"
            verdicts.append("miss")
        out.append((t, row, delta, allowed, status))
    if not verdicts:
        overall = "no targets"
    elif all(v == "within" for v in verdicts):
        overall = "REPRODUCED"
    elif "missing" in verdicts:
        overall = "INCOMPLETE (runs or seeds missing)"
    else:
        overall = "PARTIAL or FAILED — decide with reproduction.md diagnosis"
    return out, overall


def fmt(x, digits=4):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{digits}g}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs")
    ap.add_argument("--targets")
    ap.add_argument("--min-seeds", type=int, default=3)
    ap.add_argument("--include-smoke", action="store_true")
    args = ap.parse_args()

    records, parse_errors = load_records(args.runs)
    errors = parse_errors + validate(records)
    active, n_superseded = active_records(records, args.include_smoke)
    warnings = fairness_warnings(active)
    rows, failed = aggregate(active)

    print(f"# Results check: `{args.runs}`\n")
    print(f"- Records: {len(records)} total, {len(active)} active, {n_superseded} superseded ids")
    print(f"- Failed runs (active): {sum(failed.values())}")
    print(f"- Schema errors: {len(errors)}")
    print(f"- Warnings: {len(warnings)}\n")

    if errors:
        print("## Schema errors\n")
        print("\n".join(f"- {e}" for e in errors) + "\n")
    if warnings:
        print("## Warnings\n")
        print("\n".join(f"- {w}" for w in warnings) + "\n")

    print("## Aggregates (ok runs)\n")
    print("| role | method | dataset | split | metric | n | mean | std | failed |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        flag = " ⚠" if r["n"] < args.min_seeds else ""
        print("| " + " | ".join(map(str, r["key"])) +
              f" | {r['n']}{flag} | {fmt(r['mean'])} | {fmt(r['std'])} | {r['failed']} |")
    print()

    if args.targets:
        with open(args.targets, encoding="utf-8") as f:
            targets = json.load(f)
        results, overall = check_targets(targets, rows, args.min_seeds)
        print("## Reproduction targets\n")
        print("| method | dataset | metric | [reported] | [measured] mean ± std (n) | delta | tolerance | status | source |")
        print("|---|---|---|---|---|---|---|---|---|")
        for t, row, delta, allowed, status in results:
            measured = "—" if row is None else f"{fmt(row['mean'])} ± {fmt(row['std'])} ({row['n']})"
            print(f"| {t['method']} | {t['dataset']} | {t['metric']} | {fmt(t['value'])} | {measured} | "
                  f"{fmt(delta)} | ±{fmt(allowed)} | {status} | {t.get('source', '')} |")
        print(f"\n**Suggested verdict:** {overall}\n")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
