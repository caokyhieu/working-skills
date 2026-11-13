#!/usr/bin/env python3
"""Workspace helper for field-atlas. Standard library only.

Evidence store
  init      create atlas/ (shared ontology, playbook, hypotheses) and atlas/<field>/
  ingest    import conference-radar / scholar_search records into <field>/papers.jsonl, merging versions
  dates     fill first-public dates from arXiv (v1 submission date)
  reviews   attach OpenReview reviews and decisions (login via env; or --from-file)
  repos     record dated GitHub star observations for verified repositories
  cites     record dated citation counts from Semantic Scholar
  set       set fields on one paper (repo.url=..., repo.status=official, proceedings_date=...)
  facets    import facet assignments and relevance from a JSON-lines file
  show      print papers compactly, in batches
  status    counts and coverage per field

Semantic layer and analysis
  check     validate cards and hypotheses against ontology.md
  graph     compile all cards into atlas/graph.jsonl
  share     topic share per period, with n and coverage
  rank      reading | attention | momentum | transfer views, with visible weights
  changes   candidate development events (domain moves, relaxed assumptions), sequence vs influence
  bridges   cross-domain transfer leads: methods used on a problem in one domain but not another
  audit     sample claims and evidence rows for a human extraction check
"""
import argparse
import collections
import datetime as dt
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
UA = "field-atlas/1.0 (research workspace helper)"
FACETS = ["domain", "problem", "technique", "setting", "constraint"]
STATUSES = {"accepted", "claimed", "preprint", "rejected", "withdrawn", "unknown"}
VIA = {"policy", "citation", "search", "user"}
REPO_STATUS = {"official", "claimed", "unverified", "none"}
EVIDENCE_LEVEL = {"strong": 3, "mixed": 2, "weak": 1, "claim-only": 0}
HYP_STATUS = {"lead", "proposed", "prior-art-found", "testing", "supported", "rejected", "parked"}
PRIOR_ART = {"not-searched", "none-found", "partial", "known"}
COST = {"low": 3, "medium": 2, "high": 1}
TERM_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|")
TODAY = dt.date.today().isoformat()


# ---------------------------------------------------------------- io

def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tmp.replace(path)


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def card_name(pid):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", pid) + ".md"


_last_call = collections.defaultdict(float)


def http(url, data=None, headers=None, spacing=0.0, retries=4, method=None):
    """GET/POST returning bytes. Falls back to curl when a front end rejects Python's client."""
    host = urllib.parse.urlparse(url).netloc
    hdr = {"User-Agent": UA, **(headers or {})}
    body = json.dumps(data).encode() if isinstance(data, (dict, list)) else data
    if body is not None:
        hdr.setdefault("Content-Type", "application/json")
    for i in range(retries):
        time.sleep(max(0.0, _last_call[host] + spacing - time.time()))
        req = urllib.request.Request(url, data=body, headers=hdr, method=method)
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                out = r.read()
            _last_call[host] = time.time()
            return out
        except urllib.error.HTTPError as e:
            _last_call[host] = time.time()
            if e.code in (403, 406) and body is None and shutil.which("curl"):
                cmd = ["curl", "-sSfL", "--max-time", "90", "-A", UA]
                for k, v in hdr.items():
                    if k != "User-Agent":
                        cmd += ["-H", f"{k}: {v}"]
                r = subprocess.run(cmd + [url], capture_output=True)
                if r.returncode == 0:
                    return r.stdout
            if e.code in (429, 500, 502, 503) and i < retries - 1:
                time.sleep((15 if "arxiv" in host else 3) * (i + 1))
                continue
            raise SystemExit(f"HTTP {e.code} for {url}: {e.read()[:300].decode('utf-8', 'replace')}")
        except urllib.error.URLError as e:
            if i < retries - 1:
                time.sleep(3 * (i + 1))
                continue
            raise SystemExit(f"network error for {url}: {e.reason}")


# ---------------------------------------------------------------- workspace

def root_of(a):
    return Path(a.root)


def field_dir(a, field=None):
    f = field or a.field
    if not f:
        raise SystemExit("pass --field <field-id>")
    d = root_of(a) / f
    if not d.exists():
        raise SystemExit(f"{d} does not exist; run `atlas.py init --field {f}` first")
    return d


def fields(a):
    r = root_of(a)
    return sorted(p.name for p in r.iterdir() if p.is_dir() and (p / "papers.jsonl").exists()) if r.exists() else []


def load_papers(a, field=None):
    return read_jsonl(field_dir(a, field) / "papers.jsonl")


def save_papers(a, rows, field=None):
    write_jsonl(field_dir(a, field) / "papers.jsonl", rows)


def all_papers(a):
    out = {}
    for f in fields(a):
        for p in read_jsonl(root_of(a) / f / "papers.jsonl"):
            p["_field"] = f
            out.setdefault(p["id"], p)
    return out


def new_paper(**kw):
    p = {"id": "", "title": "", "authors": [], "abstract": "",
         "ids": {"arxiv": "", "doi": "", "openreview": "", "acl": "", "s2": ""},
         "versions": [], "appearances": [], "collected_via": "policy",
         "first_public": {"date": None, "source": None}, "proceedings_date": None,
         "reviews": [], "repo": {"url": "", "status": "none", "evidence": ""},
         "repo_obs": [], "citations": [], "fulltext": "",
         "facets": {f: [] for f in FACETS}, "facets_by": "", "relevance": None, "notes": []}
    p.update(kw)
    return p


def paper_keys(p):
    ids = p.get("ids", {})
    keys = [f"{k}:{v.lower()}" for k, v in ids.items() if v and k in ("arxiv", "doi", "openreview", "acl")]
    if norm_title(p.get("title")):
        keys.append("title:" + norm_title(p["title"]))
    return keys


def index_papers(rows):
    idx = {}
    for p in rows:
        for k in paper_keys(p):
            idx.setdefault(k, p)
    return idx


# ---------------------------------------------------------------- ontology

def parse_ontology(path):
    """Return dict: version, types, relations {(name, from, to)}, facets, concepts {name: (type, {facets}, aliases)}."""
    onto = {"version": None, "types": set(), "relations": set(), "facets": set(), "concepts": {}}
    section = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^version:\s*(\d+)", line)
        if m:
            onto["version"] = int(m.group(1))
        if line.startswith("## "):
            low = line.lower()
            section = ("types" if "entity types" in low else "relations" if "relations" in low
                       else "facets" if "facet" in low and "dimension" in low else "concepts" if "concepts" in low else None)
            continue
        m = TERM_ROW.match(line)
        if not m or not section:
            continue
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        if section == "types":
            onto["types"].add(cells[0])
        elif section == "facets":
            onto["facets"].add(cells[0])
        elif section == "relations" and len(cells) >= 3:
            onto["relations"].add((cells[0], cells[1], cells[2]))
        elif section == "concepts" and len(cells) >= 3:
            facets = {f.strip().strip("`") for f in cells[2].split(",") if f.strip() and f.strip() not in ("—", "-")}
            aliases = cells[4] if len(cells) > 4 else ""
            onto["concepts"][cells[0]] = (cells[1], facets, aliases)
    return onto


def load_ontology(a):
    path = root_of(a) / "ontology.md"
    if not path.exists():
        raise SystemExit(f"missing {path}; run `atlas.py init` first")
    return parse_ontology(path)


# ---------------------------------------------------------------- cards

def parse_front_matter(text):
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    data = {}
    for raw in text[3:end].splitlines():
        line = raw.split(" #", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            data[key.strip()] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        else:
            data[key.strip()] = value.strip("'\"")
    return data, text[end + 4:]


def parse_tables(body):
    """Return {section heading (lowercase): [row dicts]} for every pipe table under a '## ' heading."""
    out, section, header = {}, None, None
    for line in body.splitlines():
        if line.startswith("## "):
            section, header = line[3:].strip().lower(), None
            continue
        if not line.startswith("|") or section is None:
            header = None if not line.startswith("|") else header
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        row = dict(zip(header, cells))
        if any(v and not v.startswith("<") for v in row.values()):
            out.setdefault(section, []).append(row)
    return out


def find_table(tables, word):
    for k, v in tables.items():
        if word in k:
            return v
    return []


def clean_cell(v):
    v = (v or "").strip().strip("`").strip()
    return "" if v in ("—", "-", "") else v


def load_cards(a):
    cards = []
    for f in fields(a):
        for p in sorted((root_of(a) / f / "cards").glob("*.md")):
            fm, body = parse_front_matter(p.read_text(encoding="utf-8"))
            tables = parse_tables(body)
            ents = [{k: clean_cell(v) for k, v in r.items()} for r in find_table(tables, "entities")]
            rels = [{k: clean_cell(v) for k, v in r.items()} for r in find_table(tables, "relations")]
            cards.append({"path": p, "field": f, "fm": fm, "entities": ents, "relations": rels})
    return cards


def validate_card(c, onto, papers):
    probs = []
    fm = c["fm"]
    if fm is None:
        return ["no front matter"]
    for key in ("paper_id", "read", "evidence", "ontology_version"):
        if not fm.get(key):
            probs.append(f"missing {key}")
    if fm.get("paper_id") and fm["paper_id"] not in papers:
        probs.append(f"paper_id {fm['paper_id']!r} not in any papers.jsonl")
    if fm.get("read") and fm["read"] not in ("full", "partial", "abstract"):
        probs.append(f"read={fm['read']!r} not in full|partial|abstract")
    if fm.get("evidence") and fm["evidence"] not in EVIDENCE_LEVEL:
        probs.append(f"evidence={fm['evidence']!r} not in {sorted(EVIDENCE_LEVEL)}")
    if fm.get("read") == "abstract" and fm.get("evidence") not in (None, "claim-only"):
        probs.append("read=abstract must have evidence=claim-only")
    if onto["version"] and fm.get("ontology_version") and fm["ontology_version"] != str(onto["version"]):
        probs.append(f"ontology_version {fm['ontology_version']} != current {onto['version']} (re-check the card)")
    for dim in FACETS:
        for v in fm.get(dim) or []:
            con = onto["concepts"].get(v)
            if not con:
                probs.append(f"{dim}: unknown concept {v!r}")
            elif dim not in con[1]:
                probs.append(f"{dim}: concept {v!r} is not allowed in facet {dim} (allowed: {sorted(con[1]) or 'none'})")
    ids = {}
    for e in c["entities"]:
        eid, et = e.get("id"), e.get("type")
        if not eid:
            probs.append("entity row without id")
            continue
        ids[eid] = et
        if et not in onto["types"]:
            probs.append(f"{eid}: unknown type {et!r}")
        con = e.get("concept")
        if con and con not in onto["concepts"]:
            probs.append(f"{eid}: unknown concept {con!r} (propose it in §Ontology gaps, or leave blank)")
        elif con and onto["concepts"][con][0] not in (et, "any"):
            probs.append(f"{eid}: concept {con!r} has type {onto['concepts'][con][0]}, entity is {et}")
        if et in ("Claim", "Evidence"):
            if not e.get("where"):
                probs.append(f"{eid}: {et} without a source location")
            if e.get("kind") not in ("assertion", "result"):
                probs.append(f"{eid}: {et} kind must be assertion|result")
        if e.get("conf") and e["conf"] not in ("high", "medium", "low"):
            probs.append(f"{eid}: conf must be high|medium|low")
        if fm.get("read") == "abstract" and e.get("kind") == "result":
            probs.append(f"{eid}: kind=result from an abstract-only read; use assertion")
    sigs = {(r, f, t) for r, f, t in onto["relations"]}
    for r in c["relations"]:
        src, rel, dst = r.get("from"), r.get("relation"), r.get("to")
        if not (src and rel and dst):
            probs.append(f"incomplete relation row {r}")
            continue
        ft = ids.get(src)
        tt = "Paper" if dst.startswith("paper:") else ids.get(dst)
        if ft is None:
            probs.append(f"relation from unknown entity {src!r}")
        if tt is None:
            probs.append(f"relation to unknown entity {dst!r}")
        if ft and tt and (rel, ft, tt) not in sigs:
            probs.append(f"{src} {rel} {dst}: ({rel}, {ft}, {tt}) is not a relation in ontology.md")
        if dst.startswith("paper:") and not r.get("where"):
            probs.append(f"{src} {rel} {dst}: influence edge without the citing location")
    return probs


def load_hypotheses(a):
    out = []
    for p in sorted((root_of(a) / "hypotheses").glob("*.md")):
        fm, _ = parse_front_matter(p.read_text(encoding="utf-8"))
        out.append((p, fm or {}))
    return out


def validate_hyp(fm):
    probs = []
    for key in ("id", "status", "source_method", "target_problem", "prior_art"):
        if not fm.get(key):
            probs.append(f"missing {key}")
    if fm.get("status") and fm["status"] not in HYP_STATUS:
        probs.append(f"status={fm['status']!r} not in {sorted(HYP_STATUS)}")
    if fm.get("prior_art") and fm["prior_art"] not in PRIOR_ART:
        probs.append(f"prior_art={fm['prior_art']!r} not in {sorted(PRIOR_ART)}")
    if fm.get("adaptation_cost") and fm["adaptation_cost"] not in COST:
        probs.append("adaptation_cost must be low|medium|high")
    for k in ("compatibility", "evidence"):
        if fm.get(k) and fm[k] not in ("0", "1", "2", "3"):
            probs.append(f"{k} must be 0-3")
    if fm.get("status") in ("proposed", "testing") and fm.get("prior_art") == "not-searched":
        probs.append("a proposed hypothesis needs a prior-art search (prior_art is not-searched)")
    if fm.get("status") in ("proposed", "testing") and not fm.get("rejection_criterion"):
        probs.append("missing rejection_criterion")
    return probs


# ---------------------------------------------------------------- init

def cmd_init(a):
    r = root_of(a)
    (r / "hypotheses").mkdir(parents=True, exist_ok=True)
    (r / "eval").mkdir(exist_ok=True)
    seeds = {SKILL / "references/ontology.md": r / "ontology.md",
             SKILL / "templates/playbook.md": r / "playbook.md"}
    if a.field:
        d = r / a.field
        for sub in ("cards", "raw", "fulltext"):
            (d / sub).mkdir(parents=True, exist_ok=True)
        seeds[SKILL / "templates/scope.md"] = d / "scope.md"
        seeds[SKILL / "templates/log.md"] = d / "log.md"
        if not (d / "papers.jsonl").exists():
            (d / "papers.jsonl").write_text("", encoding="utf-8")
            print(f"created  {d / 'papers.jsonl'}")
    for src, dst in seeds.items():
        if dst.exists():
            print(f"keep     {dst}")
        else:
            shutil.copyfile(src, dst)
            print(f"created  {dst}")


# ---------------------------------------------------------------- ingest

VENUE_RE = re.compile(r"^(Findings of\s+)?(.+?)\s+(\d{4})(\s*\(arXiv\))?$")


def is_s2(r):
    return "influential" in r or bool(re.fullmatch(r"[0-9a-f]{40}", str(r.get("id") or "")))


def from_s2(r, via):
    """A source-scout/scripts/scholar_search.py record (citation-following or keyword search)."""
    ids = {"arxiv": re.sub(r"v\d+$", "", r.get("arxiv") or ""), "doi": (r.get("doi") or "").lower(),
           "openreview": "", "acl": "", "s2": r.get("id") or ""}
    venue = (r.get("venue") or "").strip()
    versions = [{"kind": "s2", "label": "Semantic Scholar", "url": r.get("url") or ""}]
    if ids["arxiv"]:
        versions.append({"kind": "arxiv", "label": f"arXiv:{ids['arxiv']}", "url": f"https://arxiv.org/abs/{ids['arxiv']}"})
    appearances = []
    if venue and venue.lower() not in ("arxiv", "arxiv.org"):
        appearances.append({"venue": venue, "year": r.get("year"), "track": "unknown", "status": "unknown",
                            "source": "semantic-scholar venue field (unverified)"})
    p = new_paper(id=f"arxiv:{ids['arxiv']}" if ids["arxiv"] else f"s2:{ids['s2']}", title=r.get("title") or "",
                  authors=r.get("authors") or [], abstract=r.get("abstract") or "", ids=ids, versions=versions,
                  appearances=appearances, collected_via=via, fulltext=r.get("pdf") or "")
    if r.get("date"):
        p["first_public"] = {"date": r["date"], "source": "semantic-scholar publicationDate (may be the venue date)"}
    if r.get("citations") is not None:
        p["citations"] = [{"date": TODAY, "count": r["citations"], "source": "semantic-scholar"}]
    return p


def from_record(r, via, proceedings_date, status_override):
    """Convert a conference-radar or scholar_search record into a canonical paper."""
    if is_s2(r):
        return from_s2(r, via)
    venue_str = r.get("venue") or ""
    m = VENUE_RE.match(venue_str.strip())
    track = r.get("track") or ""
    if m:
        venue, year = m.group(2).strip(), int(m.group(3))
        if m.group(1):
            track = "findings"
        claimed = bool(m.group(4))
    else:
        venue, year, claimed = venue_str or "arXiv", r.get("year"), False
    if claimed or track == "preprint":
        status = "claimed" if claimed else "preprint"
    elif venue.lower() in ("arxiv", ""):
        status = "preprint"
    else:
        status = "accepted"
    if status_override:
        status = status_override
    url = r.get("url") or ""
    mm = re.search(r"openreview\.net/(?:forum|pdf)\?id=([\w-]+)", url)
    rid = str(r.get("id") or "")
    ids = {"arxiv": re.sub(r"v\d+$", "", r.get("arxiv") or ""), "doi": "", "openreview": mm.group(1) if mm else "",
           "acl": rid[4:] if rid.startswith("acl:") else "", "s2": ""}
    versions = []
    if ids["arxiv"]:
        versions.append({"kind": "arxiv", "label": f"arXiv:{ids['arxiv']}", "url": f"https://arxiv.org/abs/{ids['arxiv']}"})
    if url and "arxiv.org" not in url:
        versions.append({"kind": "openreview" if mm else "proceedings", "label": venue_str, "url": url})
    appearances = []
    if status != "preprint":
        appearances.append({"venue": venue, "year": year, "track": track or "unknown", "status": status,
                            "date": proceedings_date, "source": r.get("source") or url})
    for other in r.get("also") or []:
        mo = VENUE_RE.match(other.strip())
        if mo:
            appearances.append({"venue": mo.group(2).strip(), "year": int(mo.group(3)),
                                "track": "findings" if mo.group(1) else "unknown",
                                "status": "claimed" if mo.group(4) else "accepted", "source": "conference-radar:also"})
    return new_paper(id=rid or (f"arxiv:{ids['arxiv']}" if ids["arxiv"] else ""), title=r.get("title") or "",
                     authors=r.get("authors") or [], abstract=r.get("abstract") or "", ids=ids, versions=versions,
                     appearances=appearances, collected_via=via,
                     proceedings_date=proceedings_date if status in ("accepted", "claimed") else None,
                     fulltext=r.get("pdf") or "")


def merge(old, new):
    for k, v in new["ids"].items():
        if v and not old["ids"].get(k):
            old["ids"][k] = v
    seen = {(v["kind"], v["url"]) for v in old["versions"]}
    old["versions"] += [v for v in new["versions"] if (v["kind"], v["url"]) not in seen]
    have = {(x["venue"].lower(), x["year"], x["track"]) for x in old["appearances"]}
    for ap in new["appearances"]:
        key = (ap["venue"].lower(), ap["year"], ap["track"])
        same_ed = [x for x in old["appearances"] if (x["venue"].lower(), x["year"]) == key[:2]]
        if key in have:
            continue
        if same_ed and ap["track"] == "unknown":
            continue
        for x in same_ed:  # a known track replaces an unknown one for the same edition
            if x["track"] == "unknown":
                old["appearances"].remove(x)
        old["appearances"].append(ap)
    # a paper first found by citation-following and later in the venue policy is a policy paper
    if new["collected_via"] == "policy":
        old["collected_via"] = "policy"
    for k in ("abstract", "fulltext"):
        if new.get(k) and not old.get(k):
            old[k] = new[k]
    if new.get("proceedings_date"):  # the earliest acceptance is the paper's proceedings date
        old["proceedings_date"] = min(filter(None, [old.get("proceedings_date"), new["proceedings_date"]]))
    if new["first_public"]["date"] and not old["first_public"]["date"]:
        old["first_public"] = new["first_public"]
    if len(new["authors"]) > len(old["authors"]):
        old["authors"] = new["authors"]


def cmd_ingest(a):
    rows = load_papers(a)
    idx = index_papers(rows)
    src = read_jsonl(a.file)
    added = merged = 0
    for r in src:
        p = from_record(r, a.via, a.proceedings_date, a.status)
        if not norm_title(p["title"]):
            continue
        hit = next((idx[k] for k in paper_keys(p) if k in idx), None)
        if hit is None:
            rows.append(p)
            added += 1
        else:
            merge(hit, p)
            merged += 1
            p = hit
        for k in paper_keys(p):
            idx.setdefault(k, p)
    save_papers(a, rows)
    print(f"{a.file}: {len(src)} records -> +{added} new, {merged} merged; {len(rows)} papers in {a.field}")
    log_line(a, f"ingest {a.file} via={a.via}: {len(src)} records, +{added} new, {merged} merged")


def log_line(a, text):
    p = field_dir(a) / "log.md"
    if p.exists():
        with p.open("a", encoding="utf-8") as f:
            f.write(f"- {TODAY} [script] {text}\n")


# ---------------------------------------------------------------- dates (arXiv)

ATOM = {"a": "http://www.w3.org/2005/Atom"}


def cmd_dates(a):
    rows = load_papers(a)
    todo = [p for p in rows if p["ids"].get("arxiv") and (a.force or not p["first_public"]["date"])]
    todo = todo[: a.limit] if a.limit else todo
    print(f"looking up {len(todo)} arXiv v1 dates (3 s between calls)", file=sys.stderr)
    by_id = {p["ids"]["arxiv"]: p for p in todo}
    ids = list(by_id)
    got = 0
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(
            {"id_list": ",".join(chunk), "max_results": len(chunk)})
        try:
            root = ET.fromstring(http(url, spacing=3.1))
        except SystemExit as e:
            print(f"stopped: {e}. Finished records are saved; rerun `dates` later to continue.", file=sys.stderr)
            break
        for e in root.findall("a:entry", ATOM):
            aid = re.sub(r"v\d+$", "", e.findtext("a:id", "", ATOM).rsplit("/abs/", 1)[-1])
            pub = e.findtext("a:published", "", ATOM)[:10]
            if aid in by_id and pub:
                by_id[aid]["first_public"] = {"date": pub, "source": f"arXiv v1 ({aid})"}
                got += 1
        save_papers(a, rows)
    print(f"filled {got} first-public dates; {sum(1 for p in rows if not p['first_public']['date'])} papers still undated")


# ---------------------------------------------------------------- reviews (OpenReview)

RATING_FIELDS = ["rating", "recommendation", "overall_rating", "overall_assessment", "score", "overall_recommendation"]


def or_value(content, key):
    v = (content or {}).get(key)
    return v.get("value") if isinstance(v, dict) else v


def leading_number(v):
    if isinstance(v, (int, float)):
        return float(v)
    m = re.match(r"\s*(-?\d+(?:\.\d+)?)", str(v or ""))
    return float(m.group(1)) if m else None


def openreview_token(api):
    if os.environ.get("OPENREVIEW_TOKEN"):
        return os.environ["OPENREVIEW_TOKEN"]
    user, pw = os.environ.get("OPENREVIEW_USERNAME"), os.environ.get("OPENREVIEW_PASSWORD")
    if not (user and pw):
        return None
    out = json.loads(http(f"{api}/login", data={"id": user, "password": pw}))
    return out.get("token")


def fetch_openreview(a):
    api = a.api.rstrip("/")
    token = openreview_token(api)
    if not token:
        print("no OpenReview credentials (OPENREVIEW_USERNAME/OPENREVIEW_PASSWORD or OPENREVIEW_TOKEN); "
              "anonymous requests are usually refused", file=sys.stderr)
    hdr = {"Authorization": f"Bearer {token}"} if token else {}
    notes, offset = [], 0
    inv = a.invitation or f"{a.venue_id}/-/{a.submission_name}"
    while True:
        url = f"{api}/notes?" + urllib.parse.urlencode(
            {"invitation": inv, "details": "replies", "offset": offset, "limit": 1000})
        batch = json.loads(http(url, headers=hdr, spacing=1.0)).get("notes", [])
        notes += batch
        print(f"  {len(notes)} submissions", file=sys.stderr)
        if len(batch) < 1000:
            break
        offset += 1000
    return notes


def parse_submission(n, rating_fields):
    replies = (n.get("details") or {}).get("replies") or (n.get("details") or {}).get("directReplies") or []
    scores, confs, decision, field_used = [], [], None, None
    for r in replies:
        invs = r.get("invitations") or [r.get("invitation", "")]
        tail = " ".join(i.rsplit("/-/", 1)[-1] for i in invs if i)
        c = r.get("content") or {}
        if "Review" in tail and "Meta" not in tail:
            for f in rating_fields:
                v = leading_number(or_value(c, f))
                if v is not None:
                    scores.append(v)
                    field_used = field_used or f
                    break
            cv = leading_number(or_value(c, "confidence"))
            if cv is not None:
                confs.append(cv)
        elif "Decision" in tail:
            decision = or_value(c, "decision") or decision
    venue_label = or_value(n.get("content"), "venue") or ""
    return {"forum": n.get("forum") or n.get("id"), "title": or_value(n.get("content"), "title") or "",
            "scores": scores, "confidence": confs, "field": field_used, "decision": decision,
            "venue_label": venue_label}


def cmd_reviews(a):
    rows = load_papers(a)
    idx = index_papers(rows)
    if a.from_file:
        raw = json.loads(Path(a.from_file).read_text(encoding="utf-8"))
        notes = raw.get("notes", raw) if isinstance(raw, dict) else raw
    else:
        notes = fetch_openreview(a)
        if a.save:
            Path(a.save).parent.mkdir(parents=True, exist_ok=True)
            Path(a.save).write_text(json.dumps({"notes": notes, "retrieved": TODAY, "venue_id": a.venue_id}),
                                    encoding="utf-8")
    rating_fields = a.rating_field.split(",") if a.rating_field else RATING_FIELDS
    parsed = [parse_submission(n, rating_fields) for n in notes]
    means = [sum(x["scores"]) / len(x["scores"]) for x in parsed if x["scores"]]
    stats = None
    if len(means) >= 10:  # reference population: every scored submission in the review group, not just ours
        mu = sum(means) / len(means)
        stats = {"n": len(means), "mean": round(mu, 4),
                 "sd": round(math.sqrt(sum((m - mu) ** 2 for m in means) / (len(means) - 1)), 4)}
    matched = unmatched = with_scores = 0
    for s in parsed:
        p = idx.get(f"openreview:{s['forum'].lower()}") or idx.get("title:" + norm_title(s["title"]))
        if p is None:
            unmatched += 1
            continue
        matched += 1
        if not p["ids"].get("openreview"):
            p["ids"]["openreview"] = s["forum"]
        entry = {"venue_id": a.venue_id, "review_group": a.review_group, "field": s["field"],
                 "scale": a.scale or "unknown", "scores": s["scores"], "confidence": s["confidence"],
                 "decision": s["decision"], "venue_label": s["venue_label"], "group_stats": stats, "retrieved": TODAY,
                 "source": f"https://openreview.net/forum?id={s['forum']}"}
        p["reviews"] = [r for r in p["reviews"] if r.get("venue_id") != a.venue_id] + [entry]
        with_scores += bool(s["scores"])
    save_papers(a, rows)
    msg = (f"{len(notes)} submissions ({len(means)} scored): {matched} matched to papers ({with_scores} with scores), "
           f"{unmatched} not in this field's collection; group stats: {stats or 'too few scored submissions'}")
    print(msg)
    if not a.scale:
        print("note: --scale not given; record the rubric scale before normalising (scope.md → Review rubrics)")
    log_line(a, f"reviews {a.venue_id}: {msg}")


# ---------------------------------------------------------------- repos (GitHub)

def cmd_repos(a):
    rows = load_papers(a)
    hdr = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        hdr["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    statuses = set(a.status.split(","))
    todo = [p for p in rows if p["repo"].get("url") and p["repo"].get("status") in statuses]
    by_repo = collections.defaultdict(list)
    for p in todo:
        m = re.search(r"github\.com/([^/\s]+)/([^/\s#?]+)", p["repo"]["url"])
        if m:
            by_repo[(m.group(1), m.group(2).removesuffix(".git"))].append(p)
    print(f"observing {len(by_repo)} repositories for {len(todo)} papers", file=sys.stderr)
    for (owner, name), ps in by_repo.items():
        try:
            info = json.loads(http(f"https://api.github.com/repos/{owner}/{name}", headers=hdr, spacing=0.5))
        except SystemExit as e:
            print(f"  {owner}/{name}: {e}", file=sys.stderr)
            continue
        obs = {"date": TODAY, "stars": info.get("stargazers_count"), "forks": info.get("forks_count"),
               "created": (info.get("created_at") or "")[:10], "pushed": (info.get("pushed_at") or "")[:10],
               "shared_with": len(ps)}
        for p in ps:
            p["repo_obs"] = [o for o in p["repo_obs"] if o["date"] != TODAY] + [obs]
    save_papers(a, rows)
    shared = {k: len(v) for k, v in by_repo.items() if len(v) > 1}
    if shared:
        print("repositories shared by several papers (stars are not per-paper):",
              ", ".join(f"{o}/{n} ({c})" for (o, n), c in shared.items()))


# ---------------------------------------------------------------- citations (Semantic Scholar)

def cmd_cites(a):
    rows = load_papers(a)
    hdr = {"x-api-key": os.environ["S2_API_KEY"]} if os.environ.get("S2_API_KEY") else {}
    def s2id(p):
        i = p["ids"]
        return (i.get("s2") or (f"ARXIV:{i['arxiv']}" if i.get("arxiv") else "")
                or (f"DOI:{i['doi']}" if i.get("doi") else "") or (f"ACL:{i['acl']}" if i.get("acl") else ""))
    todo = [p for p in rows if s2id(p)]
    got = 0
    for i in range(0, len(todo), 400):
        chunk = todo[i:i + 400]
        url = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=citationCount,paperId"
        res = json.loads(http(url, data={"ids": [s2id(p) for p in chunk]}, headers=hdr, spacing=1.5))
        for p, r in zip(chunk, res):
            if not r or r.get("citationCount") is None:
                continue
            p["ids"]["s2"] = p["ids"].get("s2") or r.get("paperId", "")
            p["citations"] = [c for c in p["citations"] if c["date"] != TODAY] + [
                {"date": TODAY, "count": r["citationCount"], "source": "semantic-scholar"}]
            got += 1
        save_papers(a, rows)
    print(f"citation counts for {got} of {len(rows)} papers ({len(rows) - len(todo)} have no usable id)")


# ---------------------------------------------------------------- set / facets / show

def coerce(v):
    if v in ("null", "None", ""):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if v.startswith("[") or v.startswith("{"):
        return json.loads(v)
    return v


def cmd_set(a):
    rows = load_papers(a)
    p = next((x for x in rows if x["id"] == a.id), None)
    if p is None:
        raise SystemExit(f"no paper {a.id!r} in {a.field}")
    for kv in a.assign:
        key, _, val = kv.partition("=")
        if key == "note":
            p["notes"].append(f"{TODAY}: {val}")
            continue
        parts, cur = key.split("."), p
        for k in parts[:-1]:
            cur = cur.setdefault(k, {})
        cur[parts[-1]] = coerce(val)
    if p["repo"].get("status") not in REPO_STATUS:
        raise SystemExit(f"repo.status must be one of {sorted(REPO_STATUS)}")
    if p["repo"].get("status") in ("official", "claimed") and not p["repo"].get("evidence"):
        print("warning: repo.status set without repo.evidence (where the link was found)", file=sys.stderr)
    save_papers(a, rows)
    print(json.dumps({k: p[k] for k in ("id", "first_public", "proceedings_date", "repo", "collected_via")}, ensure_ascii=False))


def cmd_facets(a):
    rows = load_papers(a)
    byid = {p["id"]: p for p in rows}
    onto = load_ontology(a)
    bad, n = [], 0
    for r in read_jsonl(a.file):
        p = byid.get(r.get("id"))
        if p is None:
            bad.append(f"{r.get('id')}: not in {a.field}")
            continue
        for dim in FACETS:
            if dim not in r:
                continue
            vals = r[dim] if isinstance(r[dim], list) else [r[dim]]
            for v in vals:
                con = onto["concepts"].get(v)
                if not con or dim not in con[1]:
                    bad.append(f"{p['id']}: {dim}={v!r} is not a concept allowed in that facet")
            p["facets"][dim] = [v for v in vals if v in onto["concepts"] and dim in onto["concepts"][v][1]]
        if "relevance" in r:
            p["relevance"] = r["relevance"]
        p["facets_by"] = r.get("by", a.by)
        p["facets_version"] = onto["version"]
        n += 1
    save_papers(a, rows)
    print(f"facets for {n} papers")
    for b in bad[:50]:
        print("  -", b)
    if bad:
        print(f"{len(bad)} values rejected; add concepts via the ontology extension procedure or fix them")
    return 1 if bad else 0


def cmd_show(a):
    rows = load_papers(a)
    if a.missing:
        rows = [p for p in rows if not any(p["facets"].values())]
    if a.via:
        rows = [p for p in rows if p["collected_via"] == a.via]
    for p in rows[a.offset:a.offset + a.limit]:
        ap = "; ".join(f"{x['venue']} {x['year']} {x['track']}" for x in p["appearances"]) or "preprint"
        line = f"{p['id']} | {p['first_public']['date'] or '?'} | {ap} | {p['title']}"
        if a.abstracts and p["abstract"]:
            line += f"\n    {p['abstract'][:a.chars]}"
        fac = {k: v for k, v in p["facets"].items() if v}
        if fac:
            line += f"\n    facets: {json.dumps(fac)}"
        print(line)
    print(f"-- shown {min(a.limit, max(0, len(rows) - a.offset))} of {len(rows)}")


# ---------------------------------------------------------------- status

def cmd_status(a):
    hyps = load_hypotheses(a)
    print("| Field | Papers | Policy | Cited/search | Dated (first-public) | Reviews | Verified repo | Citations | Facets | Cards |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for f in fields(a):
        rows = load_papers(a, f)
        n = len(rows)
        cards = len(list((root_of(a) / f / "cards").glob("*.md")))
        c = lambda pred: sum(1 for p in rows if pred(p))
        print(f"| {f} | {n} | {c(lambda p: p['collected_via'] == 'policy')} | "
              f"{c(lambda p: p['collected_via'] != 'policy')} | {c(lambda p: p['first_public']['date'])} | "
              f"{c(lambda p: any(r['scores'] for r in p['reviews']))} | "
              f"{c(lambda p: p['repo'].get('status') == 'official')} | {c(lambda p: p['citations'])} | "
              f"{c(lambda p: any(p['facets'].values()))} | {cards} |")
    st = collections.Counter(fm.get("status", "?") for _, fm in hyps)
    print(f"\nhypotheses: {len(hyps)} " + (json.dumps(dict(st)) if st else ""))


# ---------------------------------------------------------------- check / graph

def cmd_check(a):
    onto = load_ontology(a)
    papers = all_papers(a)
    bad = 0
    cards = [c for c in load_cards(a) if not a.field or c["field"] == a.field]
    for c in cards:
        probs = validate_card(c, onto, papers)
        if probs:
            bad += 1
            print(f"{c['field']}/cards/{c['path'].name}:")
            for p in probs:
                print(f"  - {p}")
    hyps = load_hypotheses(a)
    for p, fm in hyps:
        probs = validate_hyp(fm)
        if probs:
            bad += 1
            print(f"hypotheses/{p.name}:")
            for x in probs:
                print(f"  - {x}")
    used = {e.get("concept") for c in cards for e in c["entities"] if e.get("concept")}
    print(f"{len(cards)} cards, {len(hyps)} hypotheses, {bad} with problems; ontology v{onto['version']}: "
          f"{len(onto['types'])} types, {len(onto['relations'])} relation signatures, {len(onto['concepts'])} concepts "
          f"({len(used)} used in cards)")
    return 1 if bad else 0


def build_graph(a):
    papers = all_papers(a)
    nodes, edges = [], []
    for c in load_cards(a):
        fm = c["fm"] or {}
        pid = fm.get("paper_id", c["path"].stem)
        p = papers.get(pid, {})
        domains = fm.get("domain") or p.get("facets", {}).get("domain") or []
        date = (p.get("first_public") or {}).get("date")
        for e in c["entities"]:
            nodes.append({"node": f"{pid}#{e.get('id')}", "paper": pid, "field": c["field"], "type": e.get("type"),
                          "concept": e.get("concept") or None, "text": e.get("text") or "", "where": e.get("where") or "",
                          "kind": e.get("kind") or None, "conf": e.get("conf") or None,
                          "domains": domains, "date": date, "evidence": fm.get("evidence")})
        for r in c["relations"]:
            dst = r["to"] if r.get("to", "").startswith("paper:") else f"{pid}#{r.get('to')}"
            edges.append({"src": f"{pid}#{r.get('from')}", "rel": r.get("relation"), "dst": dst,
                          "where": r.get("where") or "", "paper": pid})
    return nodes, edges


def cmd_graph(a):
    nodes, edges = build_graph(a)
    out = root_of(a) / "graph.jsonl"
    write_jsonl(out, [{"kind": "node", **n} for n in nodes] + [{"kind": "edge", **e} for e in edges])
    unmapped = sum(1 for n in nodes if not n["concept"] and n["type"] in ("Problem", "Method", "Mechanism", "Assumption", "Constraint"))
    print(f"wrote {out}: {len(nodes)} nodes, {len(edges)} edges; {unmapped} structural entities without a concept "
          "(they cannot take part in bridges; map or propose concepts)")


# ---------------------------------------------------------------- share

def date_of(p, basis):
    if basis == "first_public":
        return p["first_public"]["date"]
    if p.get("proceedings_date"):
        return p["proceedings_date"]
    acc = [x for x in p["appearances"] if x["status"] == "accepted"]
    return str(min(x["year"] for x in acc)) if acc else None


def period_of(d, period):
    if not d:
        return None
    if period == "year":
        return d[:4]
    if len(d) < 7:
        return None
    if period == "half":
        return f"{d[:4]}-H{1 if int(d[5:7]) <= 6 else 2}"
    return f"{d[:4]}-Q{(int(d[5:7]) - 1) // 3 + 1}"


def cmd_share(a):
    rows = load_papers(a)
    eligible = [p for p in rows if p["collected_via"] == "policy" or a.include_cited]
    if a.cutoff:
        eligible = [p for p in eligible if (date_of(p, "first_public") or "9999") <= a.cutoff]
    undated = [p for p in eligible if not period_of(date_of(p, a.date), a.period)]
    groups = collections.defaultdict(list)
    for p in eligible:
        per = period_of(date_of(p, a.date), a.period)
        if per:
            groups[per].append(p)
    pers = sorted(groups)
    counts = {per: collections.Counter(v for p in groups[per] for v in p["facets"].get(a.dim, [])) for per in pers}
    assigned = {per: sum(1 for p in groups[per] if any(p["facets"].values())) for per in pers}
    concepts = sorted({c for per in pers for c in counts[per]},
                      key=lambda c: -sum(counts[per][c] for per in pers))
    concepts = [c for c in concepts if sum(counts[per][c] for per in pers) >= a.min_count]
    print(f"# Topic share by {a.dim} — date basis: {a.date}; period: {a.period}"
          + (f"; cutoff {a.cutoff}" if a.cutoff else ""))
    print(f"\nEligible = {'all collected' if a.include_cited else 'venue-policy'} papers. Share = papers with the concept / "
          "papers with facets assigned in the period. Overlapping facets: shares do not sum to 1.")
    print(f"Excluded for missing {a.date} date: {len(undated)}.\n")
    print("| Concept | " + " | ".join(pers) + " |")
    print("|---|" + "---|" * len(pers))
    print("| *n eligible* | " + " | ".join(str(len(groups[per])) for per in pers) + " |")
    print("| *n with facets* | " + " | ".join(str(assigned[per]) for per in pers) + " |")
    for c in concepts:
        cells = []
        for per in pers:
            k, n = counts[per][c], assigned[per]
            cells.append(f"{k / n:.1%} ({k})" if n else "—")
        print(f"| `{c}` | " + " | ".join(cells) + " |")
    low = [per for per in pers if groups[per] and assigned[per] / len(groups[per]) < 0.9]
    small = [per for per in pers if assigned[per] < 30]
    if low:
        print(f"\nwarning: facet coverage below 90% in {', '.join(low)}; shares there are biased")
    if small:
        print(f"warning: fewer than 30 assigned papers in {', '.join(small)}; treat changes as leads")
    venues = {per: sorted({f"{x['venue']}" for p in groups[per] for x in p['appearances']}) for per in pers}
    if len({tuple(v) for v in venues.values()}) > 1:
        print("warning: the venue mix changes across periods: " +
              "; ".join(f"{per}: {', '.join(v) or 'preprints'}" for per, v in venues.items()))


# ---------------------------------------------------------------- rank

def years_since(d):
    try:
        then = dt.date.fromisoformat(d[:10]) if len(d) >= 10 else dt.date(int(d[:4]), 7, 1)
    except (TypeError, ValueError):
        return None
    return max(0.5, (dt.date.today() - then).days / 365.25)


def growth(obs, key):
    obs = sorted((o for o in obs if o.get(key) is not None), key=lambda o: o["date"])
    if len(obs) < 2:
        return None
    d = (dt.date.fromisoformat(obs[-1]["date"]) - dt.date.fromisoformat(obs[0]["date"])).days
    if d < 7:
        return None
    return (obs[-1][key] - obs[0][key]) * 30.0 / d


def review_z(rows):
    """z-score of a paper's mean review within its review group (venue_id, review_group, field, scale).

    Uses the group statistics stored by `reviews` (all scored submissions, accepted or not); otherwise falls back to
    the papers in this collection, if at least 10 are scored. Several groups for one paper: the mean of their z."""
    z = collections.defaultdict(list)
    groups = collections.defaultdict(list)
    for p in rows:
        for r in p["reviews"]:
            if not r["scores"] or r.get("scale") == "unknown":
                continue
            st = r.get("group_stats")
            if st and st.get("sd"):
                z[p["id"]].append((sum(r["scores"]) / len(r["scores"]) - st["mean"]) / st["sd"])
            else:
                groups[(r["venue_id"], r["review_group"], r["field"], r["scale"])].append(
                    (p["id"], sum(r["scores"]) / len(r["scores"])))
    for g, vals in groups.items():
        if len(vals) < 10:
            continue
        xs = [v for _, v in vals]
        mu = sum(xs) / len(xs)
        sd = math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)) or 1.0
        for pid, v in vals:
            z[pid].append((v - mu) / sd)
    return {pid: sum(v) / len(v) for pid, v in z.items()}


def evidence_by_paper(a):
    out = {}
    for c in load_cards(a):
        fm = c["fm"] or {}
        if fm.get("paper_id") and fm.get("evidence") in EVIDENCE_LEVEL:
            out[fm["paper_id"]] = EVIDENCE_LEVEL[fm["evidence"]]
    return out


def percentile(values):
    have = sorted(v for v in values.values() if v is not None)
    if not have:
        return {k: None for k in values}
    def pr(v):
        below = sum(1 for x in have if x < v)
        equal = sum(1 for x in have if x == v)
        return (below + 0.5 * equal) / len(have)
    return {k: (pr(v) if v is not None else None) for k, v in values.items()}


DEFAULT_WEIGHTS = {"reading": "relevance=0.5,evidence=0.3,review=0.2",
                   "attention": "citations_per_year=0.6,stars_per_year=0.4",
                   "momentum": "star_growth=0.5,citation_growth=0.5",
                   "transfer": "compatibility=0.4,evidence=0.3,cost=0.3"}


def parse_weights(s):
    w = {}
    for part in s.split(","):
        k, _, v = part.partition("=")
        w[k.strip()] = float(v)
    return w


def cmd_rank(a):
    w = parse_weights(a.weights or DEFAULT_WEIGHTS[a.view])
    if a.view == "transfer":
        return rank_transfer(a, w)
    rows = load_papers(a)
    comp = {k: {} for k in w}
    zs = review_z(rows) if "review" in w else {}
    ev = evidence_by_paper(a) if "evidence" in w else {}
    repo_count = collections.Counter(p["repo"]["url"] for p in rows if p["repo"].get("url"))
    for p in rows:
        pid = p["id"]
        cites = p["citations"][-1]["count"] if p["citations"] else None
        age = years_since(p["first_public"]["date"] or date_of(p, "proceedings") or "")
        shared = p["repo"].get("url") and repo_count[p["repo"]["url"]] > 1
        # stars of a repository that serves several papers say nothing about any one of them
        stars = p["repo_obs"][-1] if p["repo_obs"] and p["repo"].get("status") == "official" and not shared else None
        vals = {"relevance": p.get("relevance"), "evidence": ev.get(pid), "review": zs.get(pid),
                "citations_per_year": (cites / age) if cites is not None and age else None,
                "stars_per_year": (stars["stars"] / years_since(stars["created"] or "")) if stars and stars.get("created") else None,
                "star_growth": growth(p["repo_obs"], "stars") if stars else None,
                "citation_growth": growth(p["citations"], "count")}
        for k in w:
            if k not in vals:
                raise SystemExit(f"unknown component {k!r} for view {a.view}; known: {sorted(vals)}")
            comp[k][pid] = vals[k]
    pct = {k: percentile(v) for k, v in comp.items()}
    out = []
    for p in rows:
        pid = p["id"]
        have = {k: pct[k][pid] for k in w if pct[k][pid] is not None}
        if not have:
            continue
        total_w = sum(w[k] for k in have)
        score = sum(w[k] * have[k] for k in have) / total_w if total_w else 0
        missing = [k for k in w if k not in have]
        out.append((score, p, missing))
    out.sort(key=lambda t: -t[0])
    print(f"# {a.view} ranking — field {a.field}\n")
    print("Weights: " + ", ".join(f"{k}={v}" for k, v in w.items()) +
          ". Each component is a percentile within this field; the score is the weighted mean over the components a "
          "paper has. Missing components are listed, not counted as zero.\n")
    print("| # | Paper | Score | " + " | ".join(w) + " | Missing | Flags |")
    print("|---|---|---|" + "---|" * len(w) + "---|---|")
    for i, (score, p, missing) in enumerate(out[: a.top], 1):
        flags = []
        if p["repo"].get("url") and repo_count[p["repo"]["url"]] > 1:
            flags.append(f"repo shared by {repo_count[p['repo']['url']]} (stars not counted)")
        if p["collected_via"] != "policy":
            flags.append(p["collected_via"])
        raw = []
        for k in w:
            v = comp[k][p["id"]]
            raw.append("—" if v is None else f"{v:.2f}" if isinstance(v, float) else str(v))
        title = p["title"][:70]
        print(f"| {i} | {p['id']} {title} | {score:.2f} | " + " | ".join(raw) + f" | {', '.join(missing) or '—'} | {'; '.join(flags) or '—'} |")
    print(f"\n{len(out)} of {len(rows)} papers have at least one component.")


def rank_transfer(a, w):
    out = []
    for path, fm in load_hypotheses(a):
        vals = {"compatibility": int(fm["compatibility"]) / 3 if fm.get("compatibility", "").isdigit() else None,
                "evidence": int(fm["evidence"]) / 3 if fm.get("evidence", "").isdigit() else None,
                "cost": COST[fm["adaptation_cost"]] / 3 if fm.get("adaptation_cost") in COST else None}
        have = {k: vals.get(k) for k in w if vals.get(k) is not None}
        score = sum(w[k] * v for k, v in have.items()) / sum(w[k] for k in have) if have else None
        out.append((score, path, fm, [k for k in w if k not in have]))
    order = {"none-found": 0, "partial": 1, "not-searched": 2, "known": 3}
    out.sort(key=lambda t: (order.get(t[2].get("prior_art"), 2), -(t[0] or -1)))
    print("# Transfer ranking\n")
    print("Weights: " + ", ".join(f"{k}={v}" for k, v in w.items()) +
          ". Sorted by prior art first (none-found, partial, not-searched, known), then score.\n")
    print("| Hypothesis | Status | Prior art | Score | Compat. | Evidence | Cost | Missing |")
    print("|---|---|---|---|---|---|---|---|")
    for score, path, fm, missing in out:
        print(f"| {fm.get('id', path.stem)} {fm.get('title', '')} | {fm.get('status', '?')} | {fm.get('prior_art', '?')} | "
              f"{'—' if score is None else f'{score:.2f}'} | {fm.get('compatibility', '—')} | {fm.get('evidence', '—')} | "
              f"{fm.get('adaptation_cost', '—')} | {', '.join(missing) or '—'} |")


# ---------------------------------------------------------------- changes

def cmd_changes(a):
    papers = all_papers(a)
    nodes, edges = build_graph(a)
    cites = collections.defaultdict(list)  # citing paper -> [(cited paper, where)]
    for e in edges:
        if e["dst"].startswith("paper:") and e["rel"] in ("builds-on", "contrasts-with"):
            cites[e["paper"]].append((e["dst"][6:], e["where"]))
    def influence(later, earlier):
        hits = [w for c, w in cites.get(later, []) if c == earlier]
        return f"influence: cites at {hits[0]}" if hits else "sequence only"
    out = [f"# Candidate development events", "",
           f"> Generated by `atlas.py changes` on {TODAY}. Candidates, not findings: confirm each in the papers before it "
           "enters the timeline. 'sequence only' means no card records the later paper building on the earlier one.", ""]

    # 1. technique moves into a new domain (facet level, all papers)
    first = {}
    for p in papers.values():
        d = p["first_public"]["date"] or date_of(p, "proceedings")
        if not d:
            continue
        for t in p["facets"].get("technique", []):
            for dom in p["facets"].get("domain", []):
                key = (t, dom)
                if key not in first or d < first[key][0]:
                    first[key] = (d, p["id"])
    by_tech = collections.defaultdict(list)
    for (t, dom), (d, pid) in first.items():
        by_tech[t].append((d, dom, pid))
    out += ["## 1. Technique enters a new domain (facet level)", "",
            "| Technique | Origin (earliest) | Moves to | First paper there | Lag | Evidence of influence |",
            "|---|---|---|---|---|---|"]
    for t, lst in sorted(by_tech.items()):
        if len(lst) < 2:
            continue
        lst.sort()
        d0, dom0, p0 = lst[0]
        for d, dom, pid in lst[1:]:
            lag = (years_since(d0) or 0) - (years_since(d) or 0)
            out.append(f"| `{t}` | {dom0} ({p0}, {d0}) | {dom} | {pid} ({d}) | {lag:.1f} y | {influence(pid, p0)} |")

    # 2. assumption relaxed (card level)
    required = collections.defaultdict(list)
    relaxed = collections.defaultdict(list)
    ntype = {n["node"]: n for n in nodes}
    for e in edges:
        dst = ntype.get(e["dst"])
        if not dst or not dst["concept"]:
            continue
        if e["rel"] == "requires":
            required[dst["concept"]].append((dst["date"] or "?", dst["paper"]))
        elif e["rel"] == "relaxes":
            relaxed[dst["concept"]].append((dst["date"] or "?", dst["paper"], e["where"]))
    out += ["", "## 2. Assumption relaxed (card level)", "",
            "| Assumption | Required by (earlier) | Relaxed by | Where | Evidence of influence |", "|---|---|---|---|---|"]
    for con, rel in sorted(relaxed.items()):
        for d, pid, where in sorted(rel):
            earlier = sorted(x for x in required.get(con, []) if x[0] <= d and x[1] != pid)
            req = ", ".join(f"{q} ({qd})" for qd, q in earlier[:4]) or "no card records it as required"
            infl = "; ".join(influence(pid, q) for _, q in earlier[:4]) or "—"
            out.append(f"| `{con}` | {req} | {pid} ({d}) | {where} | {infl} |")

    # 3. evaluation moves (dataset concepts by first use)
    ds_first = {}
    for n in nodes:
        if n["type"] == "Dataset" and n["concept"] and n["date"]:
            if n["concept"] not in ds_first or n["date"] < ds_first[n["concept"]][0]:
                ds_first[n["concept"]] = (n["date"], n["paper"])
    out += ["", "## 3. Evaluation settings by first appearance (card level)", "",
            "Read with the ontology's dataset notes: a move from synthetic to realistic settings is a change worth "
            "explaining; a new benchmark name alone is not.", "", "| Dataset / environment | First used | Paper |", "|---|---|---|"]
    for con, (d, pid) in sorted(ds_first.items(), key=lambda kv: kv[1]):
        out.append(f"| `{con}` | {d} | {pid} |")
    dest = root_of(a) / "changes.md"
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {dest}")


# ---------------------------------------------------------------- bridges

def cmd_bridges(a):
    onto = load_ontology(a)
    papers = all_papers(a)
    nodes, edges = build_graph(a)
    node = {n["node"]: n for n in nodes}
    # card level: Method (its concept, or the concepts of the mechanisms it uses) addresses Problem (concept P)
    uses = collections.defaultdict(lambda: collections.defaultdict(set))   # (P, M) -> domain -> papers
    prob_dom = collections.defaultdict(lambda: collections.defaultdict(set))  # P -> domain -> papers
    needs = collections.defaultdict(set)  # M -> assumption concepts
    seen_assump = collections.defaultdict(set)  # domain -> assumption/constraint concepts mentioned
    supported = collections.defaultdict(set)  # (paper) with result evidence
    for n in nodes:
        if n["type"] == "Problem" and n["concept"]:
            for d in n["domains"] or ["(no domain)"]:
                prob_dom[n["concept"]][d].add(n["paper"])
        if n["type"] in ("Assumption", "Constraint") and n["concept"]:
            for d in n["domains"]:
                seen_assump[d].add(n["concept"])
        if n["type"] == "Evidence" and n["kind"] == "result":
            supported[n["paper"]].add(n["node"])
    mechs = collections.defaultdict(set)  # method node -> mechanism concepts it uses
    reqs = collections.defaultdict(set)   # method node -> assumption concepts it requires
    for e in edges:
        s, t = node.get(e["src"]), node.get(e["dst"])
        if s and t and t["concept"] and s["type"] == "Method":
            if e["rel"] == "uses" and t["type"] == "Mechanism":
                mechs[s["node"]].add(t["concept"])
            elif e["rel"] == "requires":
                reqs[s["node"]].add(t["concept"])
    for e in edges:
        s, t = node.get(e["src"]), node.get(e["dst"])
        if not s or not t or e["rel"] != "addresses" or not t["concept"]:
            continue
        # what can transfer: the method concept and each mechanism the method uses
        for item in ([s["concept"]] if s["concept"] else []) + sorted(mechs[s["node"]]):
            for d in s["domains"] or ["(no domain)"]:
                uses[(t["concept"], item)][d].add(s["paper"])
            needs[item] |= reqs[s["node"]]
    leads = []
    for (P, M), doms in uses.items():
        for target, tpapers in prob_dom[P].items():
            if target in doms or target == "(no domain)":
                continue
            src_papers = set().union(*doms.values())
            n_ev = sum(1 for q in src_papers if supported.get(q))
            ass = sorted(needs.get(M, ()))
            ass_cells = ", ".join(f"`{x}` {'seen' if x in seen_assump[target] else 'unseen'}" for x in ass) or "none recorded"
            leads.append((len(src_papers), n_ev, len(tpapers), P, M, sorted(doms), target, sorted(tpapers), ass_cells, "card"))
    # facet level: technique T co-assigned with problem P in a domain, P present elsewhere without T
    if a.facets:
        tech_pd = collections.defaultdict(lambda: collections.defaultdict(set))
        p_dom = collections.defaultdict(lambda: collections.defaultdict(set))
        for p in papers.values():
            f = p["facets"]
            for P in f.get("problem", []):
                for d in f.get("domain", []):
                    p_dom[P][d].add(p["id"])
                    for T in f.get("technique", []):
                        tech_pd[(P, T)][d].add(p["id"])
        have = {(P, M) for _, _, _, P, M, *_ in leads}
        for (P, T), doms in tech_pd.items():
            if (P, T) in have:
                continue
            for target, tpapers in p_dom[P].items():
                if target in doms:
                    continue
                src = set().union(*doms.values())
                if len(src) < a.min_papers:
                    continue
                leads.append((len(src), 0, len(tpapers), P, T, sorted(doms), target, sorted(tpapers), "not extracted", "facet"))
    leads = [l for l in leads if l[0] >= a.min_papers or l[-1] == "card"]
    leads.sort(key=lambda l: (l[-1] != "card", -l[1], -l[0], -l[2]))
    out = ["# Cross-domain transfer leads", "",
           f"> Generated by `atlas.py bridges` on {TODAY} from {len(nodes)} card entities. A lead is a method used on a "
           "problem in one domain and not recorded for the same problem in another. **An absent link is a search lead, "
           "not a discovery**: the collection may simply not contain the paper that did it. Run the prior-art loop "
           "(references/transfer.md §4) with every alias before writing a hypothesis.", "",
           "| # | Level | Problem | Method / technique | Used in | Target domain | Target papers | Source papers (with result evidence) | Method's assumptions in target | Aliases to search |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for i, (ns, nev, nt, P, M, doms, target, tp, ass, lvl) in enumerate(leads[: a.top], 1):
        aliases = "; ".join(x for x in (onto["concepts"].get(P, ("", set(), ""))[2], onto["concepts"].get(M, ("", set(), ""))[2]) if x)
        out.append(f"| L{i} | {lvl} | `{P}` | `{M}` | {', '.join(doms)} | {target} | {nt}: {', '.join(tp[:3])}{'…' if nt > 3 else ''} | "
                   f"{ns} ({nev}) | {ass} | {aliases or '—'} |")
    shared = [(P, d) for P, d in prob_dom.items() if len([x for x in d if x != '(no domain)']) > 1]
    out += ["", "## Problems shared across domains", "",
            "The ground for any transfer: the same problem concept extracted in more than one domain.", "",
            "| Problem | Domains (papers) |", "|---|---|"]
    for P, d in sorted(shared, key=lambda t: -len(t[1])):
        out.append(f"| `{P}` | " + "; ".join(f"{k} ({len(v)})" for k, v in sorted(d.items())) + " |")
    dest = root_of(a) / "bridges.md"
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {dest}: {len(leads)} leads ({sum(1 for l in leads if l[-1] == 'card')} card-level), "
          f"{len(shared)} problems shared across domains")


# ---------------------------------------------------------------- audit

def cmd_audit(a):
    nodes, _ = build_graph(a)
    pool = [n for n in nodes if n["type"] in ("Claim", "Evidence", "Assumption", "Limitation")
            and (not a.field or n["field"] == a.field)]
    rng = random.Random(a.seed)
    sample = rng.sample(pool, min(a.n, len(pool)))
    dest = root_of(a) / "eval" / f"extraction-audit-{TODAY}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Extraction audit {TODAY}", "",
             f"{len(sample)} rows sampled at random (seed {a.seed}) from {len(pool)} claim, evidence, assumption and "
             "limitation rows. For each, open the paper at the location and mark the verdict: `supported`, "
             "`partly` (say what is off), `unsupported`, or `wrong-type`. The checker must not be the agent that "
             "wrote the card.", "",
             "| Row | Type | Kind | Text | Where | Conf | Verdict | Note |", "|---|---|---|---|---|---|---|---|"]
    for n in sample:
        lines.append(f"| {n['node']} | {n['type']} | {n['kind'] or '—'} | {n['text']} | {n['where']} | {n['conf'] or '—'} | | |")
    lines += ["", "Summary (fill in): supported __ / partly __ / unsupported __ / wrong-type __. "
              "Record the rate and the failure patterns in playbook.md → Evaluation history."]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {dest}")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default="atlas", help="atlas workspace directory (default: atlas)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def cmd(name, fn, field=True, field_required=False):
        p = sub.add_parser(name)
        p.add_argument("--root", default=argparse.SUPPRESS)
        if field:
            p.add_argument("--field", required=field_required)
        p.set_defaults(fn=fn)
        return p

    cmd("init", cmd_init)
    p = cmd("ingest", cmd_ingest, field_required=True)
    p.add_argument("file")
    p.add_argument("--via", default="policy", choices=sorted(VIA))
    p.add_argument("--proceedings-date", help="YYYY-MM-DD the proceedings appeared (conference start date)")
    p.add_argument("--status", choices=sorted(STATUSES), help="override the inferred acceptance status")
    p = cmd("dates", cmd_dates, field_required=True)
    p.add_argument("--limit", type=int)
    p.add_argument("--force", action="store_true")
    p = cmd("reviews", cmd_reviews, field_required=True)
    p.add_argument("--venue-id", required=True, help="e.g. ICLR.cc/2025/Conference")
    p.add_argument("--review-group", default="main",
                   help="papers reviewed under one process and rubric (main, datasets-benchmarks, workshop-x)")
    p.add_argument("--scale", help="rubric scale as given by the venue, e.g. '1,3,5,6,8,10'")
    p.add_argument("--rating-field", help="comma list of review fields to read as the score")
    p.add_argument("--submission-name", default="Submission")
    p.add_argument("--invitation", help="full submission invitation, overrides --venue-id/-/--submission-name")
    p.add_argument("--api", default="https://api2.openreview.net", help="use https://api.openreview.net for pre-2024 venues")
    p.add_argument("--from-file", help="saved JSON of submission notes with details.replies")
    p.add_argument("--save", help="save the fetched notes to this path for provenance")
    p = cmd("repos", cmd_repos, field_required=True)
    p.add_argument("--status", default="official", help="repo statuses to observe (default official)")
    cmd("cites", cmd_cites, field_required=True)
    p = cmd("set", cmd_set, field_required=True)
    p.add_argument("id")
    p.add_argument("assign", nargs="+", help="dotted.key=value; 'note=text' appends a dated note")
    p = cmd("facets", cmd_facets, field_required=True)
    p.add_argument("file")
    p.add_argument("--by", default="agent-abstract", help="who assigned: agent-abstract, agent-fulltext, user")
    p = cmd("show", cmd_show, field_required=True)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--abstracts", action="store_true")
    p.add_argument("--chars", type=int, default=600)
    p.add_argument("--missing", action="store_true", help="only papers without facets")
    p.add_argument("--via", choices=sorted(VIA))
    cmd("status", cmd_status, field=False)
    cmd("check", cmd_check)
    cmd("graph", cmd_graph, field=False)
    p = cmd("share", cmd_share, field_required=True)
    p.add_argument("--dim", default="problem", choices=FACETS)
    p.add_argument("--period", default="year", choices=("year", "half", "quarter"))
    p.add_argument("--date", default="first_public", choices=("first_public", "proceedings"))
    p.add_argument("--cutoff", help="use only papers public on or before this date (backtesting)")
    p.add_argument("--min-count", type=int, default=3)
    p.add_argument("--include-cited", action="store_true", help="count citation-followed papers too")
    p = cmd("rank", cmd_rank)
    p.add_argument("--view", required=True, choices=("reading", "attention", "momentum", "transfer"))
    p.add_argument("--weights", help="e.g. relevance=0.6,evidence=0.4 (printed with the result)")
    p.add_argument("--top", type=int, default=30)
    cmd("changes", cmd_changes, field=False)
    p = cmd("bridges", cmd_bridges, field=False)
    p.add_argument("--min-papers", type=int, default=2)
    p.add_argument("--facets", action="store_true", help="also list facet-level leads (weaker)")
    p.add_argument("--top", type=int, default=40)
    p = cmd("audit", cmd_audit)
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    if a.cmd == "rank" and a.view != "transfer" and not a.field:
        ap.error("rank --view reading|attention|momentum needs --field")
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()
