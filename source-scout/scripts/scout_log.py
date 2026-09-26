#!/usr/bin/env python3
"""Append-only record of screened sources (scouting/screened.jsonl) and shortlist views.

Usage:
  scout_log.py <scouting-dir> init
  scout_log.py <scouting-dir> add --id ID --type paper|oss|blog --url URL --title T --verdict keep|maybe|drop
                --reason R [--venue V] [--date YYYY-MM-DD] [--topic T] [--related ID] [--version V]
                [--problem R1.a] [--distance direct|adjacent-field|analogy] [--structure "shared objective/constraint"]
                [--bridge "concept B"] [--trl N] [--via anchor-id]
                [--fit N --evidence N --repro N --novelty N --effort N] [--by NAME]
                (a `keep` needs --problem, --distance and --structure; adjacent-field/analogy also need --bridge)
  scout_log.py <scouting-dir> override --id ID --verdict keep|maybe|drop --reason R --rule "generalisable rule" [--by NAME] [chain flags]
                # user overrules an agent verdict; appends the record and writes the rule to calibration.md
  scout_log.py <scouting-dir> rules                    # print calibration.md rules
  scout_log.py <scouting-dir> seen <url-or-id>          # exit 0 + record if seen, exit 1 if new
  scout_log.py <scouting-dir> promote --id ID --idea IDEA-ID [--by NAME]
  scout_log.py <scouting-dir> candidates [--write]      # keep + maybe not yet promoted; --write regenerates candidates.md
  scout_log.py <scouting-dir> last-run
  scout_log.py <scouting-dir> stats

Standard library only.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

TYPES = ("paper", "oss", "blog")
VERDICTS = ("keep", "maybe", "drop")
SCORES = ("fit", "evidence", "repro", "novelty", "effort")
DISTANCES = ("direct", "adjacent-field", "analogy")
CHAIN = ("problem", "distance", "structure", "bridge", "trl", "via")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm_url(u):
    u = (u or "").strip().lower()
    u = re.sub(r"^https?://(www\.)?", "", u)
    u = re.sub(r"[#?].*$", "", u)
    u = re.sub(r"(arxiv\.org/(abs|pdf)/\d+\.\d+)v\d+", r"\1", u)
    return u.rstrip("/").removesuffix(".pdf")


class Log:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.path = os.path.join(self.root, "screened.jsonl")

    def records(self):
        if not os.path.exists(self.path):
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]

    def append(self, rec):
        os.makedirs(self.root, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def latest(self):
        """Latest record per id, with promotions applied."""
        out = {}
        for r in self.records():
            if r.get("event") == "promote":
                if r["id"] in out:
                    out[r["id"]] = {**out[r["id"]], "promoted_to": r["idea"], "promoted_at": r["at"]}
            else:
                out[r["id"]] = r  # an override record carries the full source and supersedes
        return out

    def find(self, key):
        k, ku = key.strip(), norm_url(key)
        for r in self.latest().values():
            if r["id"] == k or (ku and norm_url(r.get("url")) == ku):
                return r
        return None


def check_chain(a):
    """A keep must carry a relevance chain (research-map sub-problem, distance, shared structure)."""
    if a.verdict != "keep":
        return
    missing = [k for k in ("problem", "distance", "structure") if not getattr(a, k)]
    if missing:
        sys.exit(f"refused: a keep needs --{' --'.join(missing)} (relevance chain); use maybe if it cannot be stated yet")
    if a.distance != "direct" and not a.bridge:
        sys.exit("refused: a keep at adjacent-field/analogy distance needs --bridge (the shared concept)")


def cmd_add(log, a):
    if a.id in log.latest() and not a.version:
        sys.exit(f"refused: {a.id} already recorded; pass --version to record a new version")
    check_chain(a)
    rec = {"at": now(), "id": a.id, "type": a.type, "url": a.url, "title": a.title, "venue": a.venue,
           "date": a.date, "topic": a.topic, "verdict": a.verdict, "reason": a.reason, "related": a.related,
           "version": a.version, "by": a.by, "scores": {s: getattr(a, s) for s in SCORES if getattr(a, s) is not None},
           "chain": {k: getattr(a, k) for k in CHAIN if getattr(a, k) is not None}}
    log.append(rec)
    print(f"recorded {a.id}: {a.verdict}")


def cmd_override(log, a):
    prev = log.latest().get(a.id)
    if not prev:
        sys.exit(f"refused: {a.id} not in screened.jsonl")
    chain = {**prev.get("chain", {}), **{k: getattr(a, k) for k in CHAIN if getattr(a, k, None) is not None}}
    rec = {**prev, "at": now(), "event": "override", "verdict": a.verdict, "reason": a.reason,
           "overrides": prev.get("verdict"), "rule": a.rule, "by": a.by, "chain": chain}
    log.append(rec)
    path = os.path.join(log.root, "calibration.md")
    new = not os.path.exists(path)
    n = 1 if new else 1 + sum(1 for l in open(path, encoding="utf-8") if l.startswith("| C"))
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write("# Calibration rules\n\n> Rules learned from the user's overrules of agent verdicts. source-scout, "
                    "idea-alignment and stage-critic read this before screening or matching. When a rule generalises, "
                    "fold it into research-map.md (near-misses or bridging concepts) and mark it `[in map]`.\n\n"
                    "| id | date | source | agent said | user said | rule |\n|---|---|---|---|---|---|\n")
        f.write(f"| C{n} | {now()[:10]} | {a.id} | {prev.get('verdict')} | {a.verdict} | {a.rule} |\n")
    print(f"{a.id}: {prev.get('verdict')} -> {a.verdict}; rule C{n} written to {path}")


def cmd_seen(log, key):
    r = log.find(key)
    if r:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    print("new")
    return 1


def cmd_promote(log, a):
    r = log.latest().get(a.id)
    if not r:
        sys.exit(f"refused: {a.id} not in screened.jsonl")
    log.append({"at": now(), "event": "promote", "id": a.id, "idea": a.idea, "by": a.by})
    print(f"{a.id} promoted to poc/{a.idea}")


def candidates_md(log):
    rows = [r for r in log.latest().values() if r.get("verdict") in ("keep", "maybe") and not r.get("promoted_to")]
    rows.sort(key=lambda r: (r["verdict"] != "keep", -(r.get("scores", {}).get("fit", 0)), r.get("date") or ""))
    lines = [f"# Candidates\n", f"_Generated {now()} from screened.jsonl; regenerate with `scout_log.py candidates --write`_\n"]
    for verdict in ("keep", "maybe"):
        group = [r for r in rows if r["verdict"] == verdict]
        lines.append(f"\n## {verdict} ({len(group)})\n")
        lines.append("| source-id | type | title | venue / org, date | problem | distance | shared structure / bridge | trl | fit | evid | repro | nov | effort | reason |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in group:
            s, c = r.get("scores", {}), r.get("chain", {})
            sc = " | ".join(str(s.get(k, "")) for k in SCORES)
            struct = c.get("structure", "") + (f" (B: {c['bridge']})" if c.get("bridge") else "")
            lines.append(f"| {r['id']} | {r['type']} | [{r['title']}]({r['url']}) | {r.get('venue') or ''}, {r.get('date') or ''} | "
                         f"{c.get('problem') or r.get('topic') or ''} | {c.get('distance', '')} | {struct} | {c.get('trl', '')} | {sc} | {r['reason']} |")
    return "\n".join(lines) + "\n"


def cmd_stats(log):
    recs = log.latest().values()
    by = {}
    for r in recs:
        if "verdict" in r:
            by.setdefault(r["type"], {}).setdefault(r["verdict"], 0)
            by[r["type"]][r["verdict"]] += 1
    promoted = sum(1 for r in recs if r.get("promoted_to"))
    print(json.dumps({"by_type": by, "promoted": promoted, "total": len(recs)}, indent=2))


def cmd_last_run(log):
    dates = sorted(f[:-3] for f in os.listdir(os.path.join(log.root, "runs")) if f.endswith(".md")) \
        if os.path.isdir(os.path.join(log.root, "runs")) else []
    print(dates[-1] if dates else "none")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scouting_dir")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("add")
    p.add_argument("--id", required=True); p.add_argument("--type", required=True, choices=TYPES)
    p.add_argument("--url", required=True); p.add_argument("--title", required=True)
    p.add_argument("--verdict", required=True, choices=VERDICTS); p.add_argument("--reason", required=True)
    for opt in ("--venue", "--date", "--topic", "--related", "--version", "--by"):
        p.add_argument(opt)
    for s in SCORES:
        p.add_argument(f"--{s}", type=int, choices=range(1, 6))
    p.add_argument("--problem"); p.add_argument("--distance", choices=DISTANCES); p.add_argument("--structure")
    p.add_argument("--bridge"); p.add_argument("--trl", type=int, choices=range(1, 10)); p.add_argument("--via")
    p = sub.add_parser("override"); p.add_argument("--id", required=True); p.add_argument("--verdict", required=True, choices=VERDICTS)
    p.add_argument("--reason", required=True); p.add_argument("--rule", required=True); p.add_argument("--by")
    p.add_argument("--problem"); p.add_argument("--distance", choices=DISTANCES); p.add_argument("--structure")
    p.add_argument("--bridge"); p.add_argument("--trl", type=int, choices=range(1, 10)); p.add_argument("--via")
    sub.add_parser("rules")
    p = sub.add_parser("seen"); p.add_argument("key")
    p = sub.add_parser("promote"); p.add_argument("--id", required=True); p.add_argument("--idea", required=True); p.add_argument("--by")
    p = sub.add_parser("candidates"); p.add_argument("--write", action="store_true")
    sub.add_parser("last-run"); sub.add_parser("stats")
    a = ap.parse_args()
    log = Log(a.scouting_dir)

    if a.cmd == "init":
        os.makedirs(os.path.join(log.root, "runs"), exist_ok=True)
        os.makedirs(os.path.join(log.root, "sources"), exist_ok=True)
        open(log.path, "a").close()
        tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "watchlist.md")
        wl = os.path.join(log.root, "watchlist.md")
        if not os.path.exists(wl) and os.path.exists(tpl):
            with open(tpl, encoding="utf-8") as f, open(wl, "w", encoding="utf-8") as g:
                g.write(f.read())
        print(f"initialised {log.root}")
    elif a.cmd == "add":
        cmd_add(log, a)
    elif a.cmd == "override":
        cmd_override(log, a)
    elif a.cmd == "rules":
        path = os.path.join(log.root, "calibration.md")
        print(open(path, encoding="utf-8").read() if os.path.exists(path) else "no calibration rules yet")
    elif a.cmd == "seen":
        return cmd_seen(log, a.key)
    elif a.cmd == "promote":
        cmd_promote(log, a)
    elif a.cmd == "candidates":
        md = candidates_md(log)
        if a.write:
            with open(os.path.join(log.root, "candidates.md"), "w", encoding="utf-8") as f:
                f.write(md)
            print(f"wrote {os.path.join(log.root, 'candidates.md')}")
        else:
            print(md)
    elif a.cmd == "last-run":
        cmd_last_run(log)
    elif a.cmd == "stats":
        cmd_stats(log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
