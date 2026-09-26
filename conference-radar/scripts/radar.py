#!/usr/bin/env python3
"""Fetch, filter and compare accepted-paper lists from ML / AI venues for a conference radar.

Usage:
  radar.py fetch virtual --conf icml --year 2026 --out papers.jsonl       # ICLR/ICML/NeurIPS/CVPR/ICCV/ECCV/AISTATS
  radar.py fetch acl --volume 2025.emnlp-main [--volume 2025.findings-emnlp] --out papers.jsonl
  radar.py fetch arxiv --comment "NeurIPS 2026" [--cat cs.LG] [--query "abs:diffusion"] [--max 1000] --out papers.jsonl
  radar.py enrich shortlist.jsonl [--workers 4]        # fill missing abstracts; find arXiv id + PDF
  radar.py stats papers.jsonl [--by topic|track|venue|affiliation] [--top 25]
  radar.py trends papers.jsonl --baseline last-year.jsonl [--min-count 10] [--top 30]
  radar.py filter papers.jsonl --any "diffusion|flow matching" [--all ...] [--none ...] [--track oral,spotlight]
                  [--topic REGEX] [--skip seen.jsonl ...] --out shortlist.jsonl
  radar.py show shortlist.jsonl [--offset 0] [--limit 40] [--chars 500]

Records are JSON lines: id, venue, year, title, authors, affiliations, abstract, topic, keywords, track,
url, pdf, arxiv, source, also. `fetch` merges into --out and de-duplicates by normalised title.
Standard library only. Downloads are cached under <out-dir>/.cache/. Only public listings are queried.
"""

import argparse
import collections
import concurrent.futures
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (conference-radar; research reading list)"
VIRTUAL_HOSTS = {
    "iclr": "iclr.cc", "icml": "icml.cc", "neurips": "neurips.cc",
    "cvpr": "cvpr.thecvf.com", "iccv": "iccv.thecvf.com", "eccv": "eccv.ecva.net",
    "aistats": "virtual.aistats.org",
}
ARXIV_API = "https://export.arxiv.org/api/query"
ATOM = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
TRACK_ORDER = {"award": 0, "oral": 1, "spotlight": 2, "poster": 3, "main": 3, "findings": 4, "preprint": 5}
STOP = set("""a an the of for and or in on to with by from via at as is are be we our this that these those its it
using based towards toward into over under than more less new novel approach method methods model models learning
paper propose proposed show shows results result task tasks can which while also both such their they through across
large language llm llms data deep neural network networks framework study analysis via improving improved efficient
effective simple however not no without when where how what between within each only first two one has have been
existing further various different often well even most many may has also paper work""".split())


# ---------- io ----------

class FetchError(Exception):
    def __init__(self, code, url):
        self.code, self.url = code, url
        hint = (" The site wants a browser challenge or login; use another backend (see references/venues.md)."
                if code == 403 else " arXiv refused the request; wait a few minutes and rerun (finished records are kept)."
                if "arxiv" in url else "")
        super().__init__(f"HTTP {code} for {url}.{hint}")


def curl_get(url):
    r = subprocess.run(["curl", "-sSfL", "--max-time", "90", "-A", UA, url], capture_output=True)
    return r.stdout if r.returncode == 0 else None


_arxiv_lock = threading.Lock()
_arxiv_last = [0.0]


def http_get(url, cache_dir=None, retries=4, binary=False):
    path = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        path = os.path.join(cache_dir, re.sub(r"[^A-Za-z0-9._-]+", "_", url)[-180:])
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            return data if binary else data.decode("utf-8", "replace")
    is_arxiv = "arxiv.org" in url
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(retries):
        try:
            if is_arxiv:  # arXiv API etiquette: one request at a time, 3 s apart, whatever the worker count
                with _arxiv_lock:
                    time.sleep(max(0.0, _arxiv_last[0] + 3.1 - time.time()))
                    try:
                        with urllib.request.urlopen(req, timeout=90) as r:
                            data = r.read()
                    finally:
                        _arxiv_last[0] = time.time()
            else:
                with urllib.request.urlopen(req, timeout=90) as r:
                    data = r.read()
            break
        except urllib.error.HTTPError as e:
            # Some front ends (arXiv's among them) reject Python's TLS client with 403/406 but serve curl.
            if e.code in (403, 406) and shutil.which("curl"):
                data = curl_get(url)
                if data is not None:
                    break
            if e.code in (429, 500, 502, 503) and i < retries - 1:
                time.sleep((15 if is_arxiv else 3) * (i + 1))
                continue
            raise FetchError(e.code, url)
        except urllib.error.URLError as e:
            if i < retries - 1:
                time.sleep(3 * (i + 1))
                continue
            raise FetchError(str(e.reason), url)
    if path:
        with open(path, "wb") as f:
            f.write(data)
    return data if binary else data.decode("utf-8", "replace")


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def clean(s):
    s = html.unescape(html.unescape(re.sub(r"<[^>]+>", "", s or "")))  # some listings double-escape
    return re.sub(r"\s+", " ", s).strip()


def record(**kw):
    base = {"id": "", "venue": "", "year": None, "title": "", "authors": [], "affiliations": [], "abstract": "",
            "topic": "", "keywords": [], "track": "", "url": "", "pdf": "", "arxiv": "", "source": "", "also": []}
    base.update({k: v for k, v in kw.items() if v not in (None, "")})
    return base


def merge_into(out_path, new_rows):
    """Merge by normalised title; richer fields win, extra venues go to `also`, best track is kept."""
    rows = read_jsonl(out_path)
    index = {norm_title(r["title"]): r for r in rows}
    added = merged = 0
    for n in new_rows:
        key = norm_title(n["title"])
        if not key:
            continue
        old = index.get(key)
        if old is None:
            index[key] = n
            rows.append(n)
            added += 1
            continue
        merged += 1
        for k, v in n.items():
            if k in ("id", "venue", "also", "track", "source"):
                continue
            if v and not old.get(k):
                old[k] = v
        if TRACK_ORDER.get(n["track"], 9) < TRACK_ORDER.get(old["track"], 9) and n["venue"] == old["venue"]:
            old["track"] = n["track"]
        if n["venue"] != old["venue"] and n["venue"] not in old["also"]:
            old["also"].append(n["venue"])
    write_jsonl(out_path, rows)
    print(f"{out_path}: +{added} new, {merged} merged into existing, {len(rows)} total", file=sys.stderr)


# ---------- fetch backends ----------

def track_from(decision, eventtype):
    d = f"{decision or ''} {eventtype or ''}".lower()
    for t in ("award", "oral", "spotlight"):
        if t in d:
            return t
    return "poster"


def fetch_virtual(a, cache):
    conf = a.conf.lower()
    host = a.host or VIRTUAL_HOSTS.get(conf)
    if not host:
        raise SystemExit(f"unknown conference '{conf}'; pass --host (e.g. --host iclr.cc)")
    url = f"https://{host}/static/virtual/data/{conf}-{a.year}-orals-posters.json"
    data = json.loads(http_get(url, cache))
    items = data.get("results", data) if isinstance(data, dict) else data
    venue = f"{conf.upper() if conf != 'neurips' else 'NeurIPS'} {a.year}"
    rows = []
    for x in items:
        if not x.get("name"):
            continue
        authors = x.get("authors") or []
        forum = x.get("paper_url") or ""
        m = re.search(r"id=([\w-]+)", forum)
        rows.append(record(
            id=f"{conf}{a.year}:{m.group(1) if m else x.get('id')}", venue=venue, year=int(a.year),
            title=clean(x["name"]), authors=[clean(au.get("fullname", "")) for au in authors],
            affiliations=sorted({clean(au["institution"]) for au in authors if au.get("institution")}),
            abstract=clean(x.get("abstract")), topic=x.get("topic") or "", keywords=x.get("keywords") or [],
            track=track_from(x.get("decision"), x.get("eventtype")),
            url=forum or (f"https://{host}{x['virtualsite_url']}" if x.get("virtualsite_url") else ""),
            pdf=x.get("paper_pdf_url") or "", source=f"https://{host}{x.get('virtualsite_url') or ''}"))
    return rows


def fetch_acl(a, cache):
    rows = []
    for vol in a.volume:
        page = http_get(f"https://aclanthology.org/volumes/{vol}/", cache)
        year = int(vol[:4]) if vol[:4].isdigit() else None
        name = vol.split(".", 1)[-1]
        venue_name = re.sub(r"-(long|short|main|demo|industry|srw)$", "", name).replace("findings-", "Findings ").upper()
        venue = f"{venue_name} {year}".replace("FINDINGS ", "Findings of ")
        track = "findings" if "findings" in name else "main"
        # one chunk per paper: from its title anchor to the next paper's title anchor
        anchor = re.compile(r'<strong><a class=align-middle href=/(' + re.escape(vol) + r'\.\d+)/>')
        marks = list(anchor.finditer(page))
        for k, m in enumerate(marks):
            pid = m.group(1)
            chunk = page[m.end(): marks[k + 1].start() if k + 1 < len(marks) else len(page)]
            if pid.endswith(".0"):
                continue  # front matter
            title, _, rest = chunk.partition("</a></strong>")
            people, _, _ = rest.partition("abstract-collapse")
            authors = [clean(x) for x in re.findall(r"<a href=/people/[^>]+>(.*?)</a>", people)]
            ab = re.search(r'<div class="card-body p-3 small">(.*?)</div>', rest, re.S)
            abstract = ab.group(1) if ab else ""
            rows.append(record(id=f"acl:{pid}", venue=venue, year=year, title=clean(title), authors=authors,
                               abstract=clean(abstract), track=track, url=f"https://aclanthology.org/{pid}/",
                               pdf=f"https://aclanthology.org/{pid}.pdf", source=f"https://aclanthology.org/volumes/{vol}/"))
        print(f"{vol}: {sum(1 for r in rows if r['source'].endswith(vol + '/'))} papers", file=sys.stderr)
    return rows


def parse_arxiv_feed(xml_text):
    root = ET.fromstring(xml_text)
    out = []
    for e in root.findall("a:entry", ATOM):
        aid = re.sub(r"v\d+$", "", e.findtext("a:id", "", ATOM).rsplit("/abs/", 1)[-1])
        if not aid:
            continue
        comment = e.findtext("arxiv:comment", "", ATOM) or ""
        out.append(record(
            id=f"arxiv:{aid}", title=clean(e.findtext("a:title", "", ATOM)),
            authors=[clean(x.findtext("a:name", "", ATOM)) for x in e.findall("a:author", ATOM)],
            abstract=clean(e.findtext("a:summary", "", ATOM)), arxiv=aid,
            url=f"https://arxiv.org/abs/{aid}", pdf=f"https://arxiv.org/pdf/{aid}",
            topic=(e.find("arxiv:primary_category", ATOM).get("term") if e.find("arxiv:primary_category", ATOM) is not None else ""),
            year=int(e.findtext("a:published", "0000", ATOM)[:4]), keywords=[comment] if comment else []))
    return out


def fetch_arxiv(a, cache):
    parts = []
    if a.comment:
        parts.append(f'co:"{a.comment}"')
    if a.cat:
        parts.append("(" + " OR ".join(f"cat:{c}" for c in a.cat) + ")")
    if a.query:
        parts.append(f"({a.query})")
    if not parts:
        raise SystemExit("give at least one of --comment, --cat, --query")
    q = " AND ".join(parts)
    venue = a.venue or (f"{a.comment} (arXiv)" if a.comment else "arXiv")
    rows, start = [], 0
    while start < a.max:
        n = min(100, a.max - start)
        url = f"{ARXIV_API}?" + urllib.parse.urlencode({"search_query": q, "start": start, "max_results": n,
                                                      "sortBy": "submittedDate", "sortOrder": "descending"})
        batch = parse_arxiv_feed(http_get(url))
        for r in batch:
            r["venue"], r["source"] = venue, "arxiv-api"
            r["track"] = "preprint"
        if a.since:
            batch = [r for r in batch if str(r["year"]) >= a.since[:4]]
        rows.extend(batch)
        print(f"arxiv: {len(rows)} so far", file=sys.stderr)
        if len(batch) < n:
            break
        start += n
    if a.comment:  # the co: field is fuzzy; keep only comments that really name the venue
        key = norm_title(a.comment)
        rows = [r for r in rows if key in norm_title(" ".join(r["keywords"]))]
    return rows


def cmd_fetch(a):
    cache = os.path.join(os.path.dirname(os.path.abspath(a.out)), ".cache")
    rows = {"virtual": fetch_virtual, "acl": fetch_acl, "arxiv": fetch_arxiv}[a.backend](a, cache)
    if not rows:
        raise SystemExit("no papers parsed; the listing format may have changed (see references/venues.md)")
    no_abs = sum(1 for r in rows if not r["abstract"])
    print(f"fetched {len(rows)} records ({no_abs} without abstract)", file=sys.stderr)
    merge_into(a.out, rows)


# ---------- enrich ----------

def enrich_one(r):
    notes = []
    if not r["abstract"] and "/virtual/" in r.get("source", ""):
        try:
            page = http_get(r["source"])
            m = re.search(r'class="abstract-text-inner">(.*?)</div>', page, re.S)
            if m and clean(m.group(1)):
                r["abstract"] = clean(m.group(1))
                notes.append("abstract:virtual")
        except FetchError:
            notes.append("virtual:error")
    if not r["arxiv"]:
        t = re.sub(r'["\\:]', " ", r["title"])
        url = f"{ARXIV_API}?" + urllib.parse.urlencode({"search_query": f'ti:"{t}"', "max_results": 3})
        try:
            hits = parse_arxiv_feed(http_get(url))
        except (FetchError, ET.ParseError):
            hits = None
            notes.append("arxiv:error")
        for h in hits or []:
            if norm_title(h["title"]) == norm_title(r["title"]):
                r["arxiv"] = h["arxiv"]
                if not r["pdf"]:
                    r["pdf"] = h["pdf"]
                if not r["abstract"]:
                    r["abstract"] = h["abstract"]
                    notes.append("abstract:arxiv")
                notes.append("arxiv")
                break
        else:
            if hits is not None:
                notes.append("arxiv:not-found")
    return r, notes


def cmd_enrich(a):
    rows = read_jsonl(a.file)
    todo = [r for r in rows if (not r["abstract"] or not r["arxiv"])][: a.limit or None]
    print(f"enriching {len(todo)} of {len(rows)} records", file=sys.stderr)
    counts = collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for i, (_, notes) in enumerate(ex.map(enrich_one, todo), 1):
            counts.update(notes)
            if i % 20 == 0:
                print(f"  {i}/{len(todo)}", file=sys.stderr)
                write_jsonl(a.file, rows)
    write_jsonl(a.file, rows)
    missing = sum(1 for r in rows if not r["abstract"])
    print(f"done: {dict(counts)}; still without abstract: {missing}", file=sys.stderr)
    if counts["arxiv:error"] or counts["virtual:error"]:
        print("some lookups failed (rate limit or network); rerun enrich later to retry only those", file=sys.stderr)


# ---------- stats / trends ----------

def cmd_stats(a):
    rows = read_jsonl(a.file)
    c = collections.Counter()
    for r in rows:
        if a.by == "affiliation":
            c.update(r["affiliations"] or ["(none)"])
        elif a.by == "topic":
            c[(r["topic"] or "(none)").split("->")[0] if a.coarse else (r["topic"] or "(none)")] += 1
        else:
            c[r.get(a.by) or "(none)"] += 1
    print(f"{len(rows)} papers · by {a.by}\n")
    print(f"| {a.by} | papers | share |\n|---|---:|---:|")
    for k, v in c.most_common(a.top):
        print(f"| {k} | {v} | {100 * v / max(len(rows), 1):.1f}% |")


def terms(r, ngrams):
    words = [w for w in re.findall(r"[a-z][a-z0-9\-]+", f"{r['title']} {r['abstract']}".lower())]
    out = set()
    for n in ngrams:
        for i in range(len(words) - n + 1):
            g = words[i:i + n]
            if g[0] in STOP or g[-1] in STOP or any(len(w) < 3 for w in g):
                continue
            out.add(" ".join(g))
    return out


def doc_freq(rows, ngrams):
    df = collections.Counter()
    for r in rows:
        df.update(terms(r, ngrams))
    return df


def cmd_trends(a):
    cur, base = read_jsonl(a.file), read_jsonl(a.baseline)
    ng = [int(x) for x in a.ngram.split(",")]
    has_abs = lambda rows: sum(1 for r in rows if r["abstract"]) / max(len(rows), 1)
    titles_only = a.titles_only or min(has_abs(cur), has_abs(base)) < 0.8
    if titles_only and not a.titles_only:
        print(f"Abstract coverage is {has_abs(cur):.0%} vs {has_abs(base):.0%}; comparing titles only so the two "
              "sets are counted the same way.\n")
    if titles_only:
        for r in cur + base:
            r["abstract"] = ""
    dc, db = doc_freq(cur, ng), doc_freq(base, ng)
    nc, nb = len(cur), len(base)
    rows = []
    for t in set(dc) | set(db):
        c, b = dc[t], db[t]
        if max(c, b) < a.min_count:
            continue
        # smoothed log ratio of document shares
        lr = math.log(((c + 1) / (nc + 1)) / ((b + 1) / (nb + 1)))
        rows.append((lr, t, c, b))
    fmt = lambda x: f"| {x[1]} | {x[2]} ({100 * x[2] / nc:.1f}%) | {x[3]} ({100 * x[3] / nb:.1f}%) | ×{math.exp(x[0]):.2f} |"
    head = f"| term | {os.path.basename(a.file)} (n={nc}) | {os.path.basename(a.baseline)} (n={nb}) | share ratio |\n|---|---:|---:|---:|"
    print(f"## Rising (min count {a.min_count})\n\n{head}")
    for x in sorted(rows, reverse=True)[: a.top]:
        print(fmt(x))
    print(f"\n## Fading\n\n{head}")
    for x in sorted(rows)[: a.top]:
        print(fmt(x))
    print("\nCounts are papers whose title or abstract contains the term. A ratio is a lead to read, not a finding.")


# ---------- filter / show ----------

def cmd_filter(a):
    rows = read_jsonl(a.file)
    skip = set()
    for s in a.skip or []:
        skip |= {norm_title(r["title"]) for r in read_jsonl(s)}
    rx = lambda p: re.compile(p, re.I)
    anys, alls, nones = [rx(p) for p in a.any or []], [rx(p) for p in a.all or []], [rx(p) for p in a.none or []]
    tracks = set(a.track.split(",")) if a.track else None
    topic = rx(a.topic) if a.topic else None
    out = []
    for r in rows:
        text = " ".join([r["title"], "" if a.titles_only else r["abstract"], r["topic"], " ".join(r["keywords"])])
        if norm_title(r["title"]) in skip:
            continue
        if tracks and r["track"] not in tracks:
            continue
        if topic and not topic.search(r["topic"] or ""):
            continue
        if anys and not any(p.search(text) for p in anys):
            continue
        if any(not p.search(text) for p in alls) or any(p.search(text) for p in nones):
            continue
        out.append(r)
    out.sort(key=lambda r: (TRACK_ORDER.get(r["track"], 9), r["title"]))
    write_jsonl(a.out, out)
    by = collections.Counter(r["track"] for r in out)
    print(f"{len(out)} of {len(rows)} kept → {a.out}  ({', '.join(f'{k}: {v}' for k, v in by.most_common())})", file=sys.stderr)


def cmd_show(a):
    rows = read_jsonl(a.file)
    part = rows[a.offset: a.offset + a.limit]
    for i, r in enumerate(part, a.offset + 1):
        aff = ", ".join(r["affiliations"][:3])
        abstract = r["abstract"][: a.chars] + ("…" if len(r["abstract"]) > a.chars else "") if r["abstract"] else "(no abstract)"
        also = f" · also {', '.join(r['also'])}" if r["also"] else ""
        print(f"{i}. **{r['title']}** — {r['venue']} {r['track']}{also} · `{r['id']}`")
        print(f"   {', '.join(r['authors'][:4])}{' et al.' if len(r['authors']) > 4 else ''}{' · ' + aff if aff else ''}"
              f"{' · ' + r['topic'] if r['topic'] else ''}")
        print(f"   {abstract}\n")
    print(f"[{a.offset + 1}–{a.offset + len(part)} of {len(rows)}]")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch")
    fs = f.add_subparsers(dest="backend", required=True)
    v = fs.add_parser("virtual", help="conference virtual-site JSON (ICLR, ICML, NeurIPS, CVPR, ICCV, ECCV, AISTATS)")
    v.add_argument("--conf", required=True)
    v.add_argument("--year", required=True)
    v.add_argument("--host", help="override the host, e.g. for a venue on the same platform")
    ac = fs.add_parser("acl", help="ACL Anthology volume pages (ACL, EMNLP, NAACL, EACL, COLING, Findings)")
    ac.add_argument("--volume", action="append", required=True, help="e.g. 2025.acl-long; repeatable")
    ar = fs.add_parser("arxiv", help="arXiv API by comment ('Accepted at NeurIPS 2026'), category or query")
    ar.add_argument("--comment")
    ar.add_argument("--cat", action="append")
    ar.add_argument("--query", help="raw arXiv query, e.g. 'abs:\"state space\"'")
    ar.add_argument("--since", help="YYYY; drop older submissions")
    ar.add_argument("--venue", help="label for these records")
    ar.add_argument("--max", type=int, default=500)
    for s in (v, ac, ar):
        s.add_argument("--out", required=True)
    f.set_defaults(fn=cmd_fetch)

    e = sub.add_parser("enrich")
    e.add_argument("file")
    e.add_argument("--workers", type=int, default=2)
    e.add_argument("--limit", type=int, default=0)
    e.set_defaults(fn=cmd_enrich)

    s = sub.add_parser("stats")
    s.add_argument("file")
    s.add_argument("--by", default="topic", choices=["topic", "track", "venue", "affiliation"])
    s.add_argument("--coarse", action="store_true", help="topic: first level only")
    s.add_argument("--top", type=int, default=25)
    s.set_defaults(fn=cmd_stats)

    t = sub.add_parser("trends")
    t.add_argument("file")
    t.add_argument("--baseline", required=True)
    t.add_argument("--ngram", default="1,2")
    t.add_argument("--min-count", type=int, default=10)
    t.add_argument("--top", type=int, default=30)
    t.add_argument("--titles-only", action="store_true")
    t.set_defaults(fn=cmd_trends)

    fl = sub.add_parser("filter")
    fl.add_argument("file")
    fl.add_argument("--any", action="append", help="regex; keep if any --any matches")
    fl.add_argument("--all", action="append", help="regex; every --all must match")
    fl.add_argument("--none", action="append", help="regex; drop if any matches")
    fl.add_argument("--track", help="comma list: award,oral,spotlight,poster,main,findings,preprint")
    fl.add_argument("--topic", help="regex on the venue's topic label")
    fl.add_argument("--titles-only", action="store_true")
    fl.add_argument("--skip", action="append", help="jsonl of papers already covered; repeatable")
    fl.add_argument("--out", required=True)
    fl.set_defaults(fn=cmd_filter)

    sh = sub.add_parser("show")
    sh.add_argument("file")
    sh.add_argument("--offset", type=int, default=0)
    sh.add_argument("--limit", type=int, default=40)
    sh.add_argument("--chars", type=int, default=500)
    sh.set_defaults(fn=cmd_show)

    a = p.parse_args()
    try:
        a.fn(a)
    except FetchError as e:
        raise SystemExit(str(e))


if __name__ == "__main__":
    main()
