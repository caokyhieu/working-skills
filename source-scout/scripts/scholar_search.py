#!/usr/bin/env python3
"""Semantic Scholar queries for scouting: keyword search and citation-graph expansion from anchors.

Usage:
  scholar_search.py search  --query "learned cardinality estimation" [--since 2025] [--limit 30] [--fields cs.DB]
  scholar_search.py expand  --id arXiv:2502.18864 [--edge citations|references|recommendations] [--since 2025] [--limit 50]
  scholar_search.py paper   --id DOI:10.1145/3274300
  scholar_search.py anchors --map research-map.md --problem R1 [--edge citations] [--since 2025] [--limit 50]

Ids: S2 paperId, "arXiv:<id>", "DOI:<doi>", "ACL:<id>", "URL:<url>". Output is JSON lines unless --md.
Set S2_API_KEY for a higher rate limit. Standard library only. Public queries only: never put company
context into --query.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.semanticscholar.org/graph/v1"
FIELDS = "paperId,title,year,venue,citationCount,influentialCitationCount,externalIds,url,abstract,authors,publicationDate,openAccessPdf"


def get(path, params=None, retries=4):
    url = f"{API}{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": "source-scout/1.0"})
    if os.environ.get("S2_API_KEY"):
        req.add_header("x-api-key", os.environ["S2_API_KEY"])
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and i < retries - 1:
                time.sleep(2 ** i + 1)
                continue
            sys.exit(f"error {e.code} for {url}: {e.read().decode(errors='replace')[:200]}")
    return None


def norm(p):
    ext = p.get("externalIds") or {}
    return {
        "id": p.get("paperId"), "title": p.get("title"), "year": p.get("year"), "date": p.get("publicationDate"),
        "venue": p.get("venue") or "", "citations": p.get("citationCount"), "influential": p.get("influentialCitationCount"),
        "arxiv": ext.get("ArXiv"), "doi": ext.get("DOI"), "url": p.get("url"),
        "pdf": (p.get("openAccessPdf") or {}).get("url"),
        "authors": [a.get("name") for a in (p.get("authors") or [])][:6],
        "abstract": p.get("abstract"),
    }


def emit(rows, md, show_abstract):
    if not md:
        for r in rows:
            if not show_abstract:
                r = {k: v for k, v in r.items() if k != "abstract"}
            print(json.dumps(r, ensure_ascii=False))
        return
    print("| year | title | venue | cites | id | link |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        link = f"https://arxiv.org/abs/{r['arxiv']}" if r["arxiv"] else (r["url"] or "")
        ident = f"arXiv:{r['arxiv']}" if r["arxiv"] else (f"DOI:{r['doi']}" if r["doi"] else r["id"])
        print(f"| {r['year'] or ''} | {(r['title'] or '').replace('|', '/')} | {r['venue'].replace('|', '/')} | {r['citations'] or 0} | {ident} | {link} |")
        if show_abstract and r["abstract"]:
            print(f"|  | _{r['abstract'][:400].replace('|', '/')}…_ |  |  |  |  |")


def since_ok(r, since):
    return not since or (r["year"] or 0) >= since


def cmd_search(a):
    params = {"query": a.query, "limit": min(a.limit, 100), "fields": FIELDS}
    if a.since:
        params["year"] = f"{a.since}-"
    if a.fields:
        params["fieldsOfStudy"] = a.fields
    data = get("/paper/search", params) or {}
    return [norm(p) for p in data.get("data", [])]


def cmd_expand(a, ident=None):
    ident = ident or a.id
    if a.edge == "recommendations":
        data = get(f"/recommendations/v1/papers/forpaper/{urllib.parse.quote(ident, safe=':')}",
                   {"limit": min(a.limit, 100), "fields": FIELDS}) or {}
        rows = [norm(p) for p in data.get("recommendedPapers", [])]
    else:
        key = "citingPaper" if a.edge == "citations" else "citedPaper"
        rows, offset = [], 0
        while len(rows) < a.limit:
            data = get(f"/paper/{urllib.parse.quote(ident, safe=':')}/{a.edge}",
                       {"limit": 100, "offset": offset, "fields": FIELDS}) or {}
            batch = [norm(x[key]) for x in data.get("data", []) if x.get(key, {}).get("paperId")]
            rows += batch
            if "next" not in data or not batch:
                break
            offset = data["next"]
    rows = [r for r in rows if since_ok(r, a.since)]
    rows.sort(key=lambda r: (-(r["influential"] or 0), -(r["citations"] or 0)))
    return rows[: a.limit]


def anchors_from_map(path, problem):
    """Pull anchor ids (arXiv:/DOI:/S2 ids or URLs) from the problem's block in research-map.md."""
    text = open(path, encoding="utf-8").read()
    m = re.search(rf"^### {re.escape(problem)}\b.*?(?=^### |\Z)", text, re.S | re.M)
    if not m:
        sys.exit(f"problem {problem} not found in {path}")
    block = m.group(0)
    ids = set(re.findall(r"arXiv:\s?(\d{4}\.\d{4,5})", block, re.I))
    ids |= set(re.findall(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", block, re.I))
    out = [f"arXiv:{i}" for i in sorted(ids)]
    out += [f"DOI:{d}" for d in re.findall(r"(?:DOI:|doi\.org/)\s?(10\.\d{4,9}/[^\s|)]+)", block, re.I)]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--since", type=int); common.add_argument("--limit", type=int, default=30)
    common.add_argument("--md", action="store_true"); common.add_argument("--abstract", action="store_true")
    p = sub.add_parser("search", parents=[common]); p.add_argument("--query", required=True); p.add_argument("--fields")
    p = sub.add_parser("expand", parents=[common]); p.add_argument("--id", required=True)
    p.add_argument("--edge", default="citations", choices=("citations", "references", "recommendations"))
    p = sub.add_parser("paper", parents=[common]); p.add_argument("--id", required=True)
    p = sub.add_parser("anchors", parents=[common]); p.add_argument("--map", required=True); p.add_argument("--problem", required=True)
    p.add_argument("--edge", default="citations", choices=("citations", "references", "recommendations"))
    a = ap.parse_args()

    if a.cmd == "search":
        emit(cmd_search(a), a.md, a.abstract)
    elif a.cmd == "expand":
        emit(cmd_expand(a), a.md, a.abstract)
    elif a.cmd == "paper":
        emit([norm(get(f"/paper/{urllib.parse.quote(a.id, safe=':')}", {"fields": FIELDS}))], a.md, True)
    elif a.cmd == "anchors":
        ids = anchors_from_map(a.map, a.problem)
        if not ids:
            sys.exit(f"no arXiv/DOI anchors found under {a.problem}; add them to the research map first")
        seen, rows = set(), []
        for ident in ids:
            for r in cmd_expand(a, ident):
                if r["id"] not in seen:
                    seen.add(r["id"]); r["via_anchor"] = ident; rows.append(r)
            time.sleep(1)
        rows.sort(key=lambda r: (-(r["influential"] or 0), -(r["citations"] or 0)))
        emit(rows[: a.limit], a.md, a.abstract)
    return 0


if __name__ == "__main__":
    sys.exit(main())
