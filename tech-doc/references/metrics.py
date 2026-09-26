#!/usr/bin/env python3
"""Score a tech-doc workspace on consistency, precision and self-containment.

Usage:
    python3 references/metrics.py docs/.techdoc/<slug>           # per-section + totals
    python3 references/metrics.py docs/.techdoc/<slug> --verbose # list the offenders
    python3 references/metrics.py docs/.techdoc/<slug> --strict  # exit 1 if any gate fails

Every metric is computed from the section files, CONTEXT.md, OUTLINE.md and SOURCES.md.
Hedge density is a heuristic and is printed as such. Everything else is exact. A gate
that fails is a defect, not a style preference. There is deliberately no length gate:
length follows from content, and padding is caught by the filler and sentence gates.
"""
import sys, re, os, glob, json
from collections import Counter

BANNED = ["powerful", "seamless", "robust", "simply", "easy", "comprehensive",
          "leverage", "cutting-edge", "state-of-the-art", "blazing"]
VAGUE = ["various", "several", "etc", "appropriate", "appropriately", "properly",
         "as needed", "and so on", "a number of", "in some cases", "relevant"]
FILLER = [r"in this section", r"this section (?:describes|covers|explains|presents)",
          r"in order to", r"it is (?:important|worth) (?:to note|noting)",
          r"it should be noted", r"note that", r"as (?:mentioned|described|discussed) (?:above|earlier|before|previously)",
          r"let'?s", r"let us", r"we will", r"in summary", r"to summari[sz]e"]
HEDGES = ["generally", "typically", "usually", "arguably", "essentially", "basically",
          "somewhat", "fairly", "rather", "presumably", "likely", "probably"]

# Gates are defects. A failure means something is wrong, not merely unlovely.
GATES = {  # metric: (comparison, threshold)
    "heading_mismatch":   ("==", 0),
    "dangling_refs":      ("==", 0),
    "duplicate_headings": ("==", 0),
    "source_links":       ("==", 0),
    "banned_words":       ("==", 0),
    "vague_words":        ("==", 0),
    "filler_phrases":     ("==", 0),
    "unlabeled_edges":    ("==", 0),
    "oversized_diagrams": ("==", 0),
    "pct_long_sentences": ("<=", 5.0),
    "mean_sentence_len":  ("<=", 20.0),
}

# Reported, never gated: these need judgment a script cannot supply.
#   term_drift    - `ClusterIdentity` the class vs "cluster identity" the concept is a
#                   legitimate distinction. Read the offenders; fix only the accidents.
#   cites_per_1k  - a reference section is denser than an overview by design.
#   hedge_per_1k  - one honest "probably" beats a false certainty.


def strip_noise(t):
    """Prose only: no code fences, tables, headings, HTML comments or link targets."""
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"^\s*\|.*$", " ", t, flags=re.M)      # tables
    t = re.sub(r"^\s*#{1,6} .*$", " ", t, flags=re.M)  # headings
    t = re.sub(r"`[^`]*`", "CODE", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)     # keep link text
    return t


def sentences(prose):
    """Split into sentences, treating list items and blank lines as hard boundaries.

    A lead-in followed by bullets is several units, not one long sentence. Without
    this the metric reports false positives on every enumerated passage.
    """
    units, out = [], []
    for block in re.split(r"\n\s*\n", prose):
        cur = []
        for line in block.splitlines():
            line = re.sub(r"^\s*>\s?", "", line)
            if re.match(r"\s*(?:[-*+]|\d+[.)])\s+", line):   # list item starts a unit
                if cur:
                    units.append(" ".join(cur))
                cur = [re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", line)]
            else:
                cur.append(line)
        if cur:
            units.append(" ".join(cur))
    for u in units:
        u = u.strip().rstrip(":")
        if not u:
            continue
        # a closing **, quote or paren may sit between the stop and the space
        for s in re.split(r"(?<=[.!?])(?:\*\*|[)\"'\u201d])?\s+(?=[A-Z(*\u201c\u00a7\d])", u):
            s = s.strip()
            if len(s.split()) >= 3:
                out.append(s)
    return out


def diagrams(t):
    out = []
    for body in re.findall(r"```mermaid\n(.*?)```", t, re.S):
        lines = [l.strip() for l in body.strip().splitlines()
                 if l.strip() and not l.strip().startswith("%%")]
        kind = lines[0].split()[0] if lines else ""
        edges, unlabeled, nodes = 0, 0, set()
        flow = []  # (src, dst, labelled) for flowcharts, to find branches and fan-ins
        for l in lines[1:]:
            if kind.startswith("stateDiagram"):
                m = re.match(r"([\w\[\]*]+)\s*-->\s*([\w\[\]*]+)\s*(?::(.*))?$", l)
                if m:
                    edges += 1
                    for side in (m.group(1), m.group(2)):
                        if side not in ("[*]",):
                            nodes.add(side)
                    # the initial/terminal pseudo-state edge carries no choice
                    if m.group(1) != "[*]" and not (m.group(3) or "").strip():
                        unlabeled += 1
                else:
                    for m2 in re.finditer(r"^\s*state\s+\"?([\w ]+)\"?", l):
                        nodes.add(m2.group(1).strip())
            elif kind == "sequenceDiagram":
                m = re.match(r"([\w]+)\s*(-->>|->>|-->|--x|-x)\s*([\w]+)\s*:(.*)", l)
                if m:
                    edges += 1
                    nodes |= {m.group(1), m.group(3)}
                    if not m.group(4).strip():
                        unlabeled += 1
                for m2 in re.finditer(r"^\s*participant\s+(\w+)", l):
                    nodes.add(m2.group(1))
            else:
                m = re.match(r'(.+?)\s*(-{2,3}>|-{2,3}|==>|-\.->)\s*(?:\|(.*?)\|\s*)?(.+)', l)
                if m:
                    edges += 1
                    for side in (m.group(1), m.group(4)):
                        nid = re.match(r'\s*([\w]+)', side)
                        if nid:
                            nodes.add(nid.group(1))
                    src = re.match(r"\s*([\w]+)", m.group(1))
                    dst = re.match(r"\s*([\w]+)", m.group(4))
                    flow.append((src.group(1) if src else "?",
                                 dst.group(1) if dst else "?",
                                 bool((m.group(3) or "").strip())))
        # A bare arrow between one step and the next means "then", and style.md forbids
        # diagramming what a sentence already says. A label is required only where the
        # edge is one of several leaving a node, or one of several arriving at a node:
        # there the arrow makes a choice, and an unnamed choice is an unstated claim.
        outdeg, indeg = Counter(a for a, _, _ in flow), Counter(b for _, b, _ in flow)
        for a, b, labelled in flow:
            if not labelled and (outdeg[a] > 1 or indeg[b] > 1):
                unlabeled += 1
        out.append({"kind": kind, "nodes": len(nodes), "edges": edges,
                    "unlabeled": unlabeled})
    return out


def context_terms(ws):
    """Backticked identifiers from CONTEXT.md — the canonical spellings."""
    p = os.path.join(ws, "CONTEXT.md")
    if not os.path.exists(p):
        return []
    terms = set(re.findall(r"`([A-Za-z][\w.]{3,})`", open(p, encoding="utf-8").read()))
    return sorted(t for t in terms if re.search(r"[a-z][A-Z]|_|\.", t))


def section_types(ws):
    """Returns {section_num: "overview"|"mechanism"} from OUTLINE.md."""
    p = os.path.join(ws, "OUTLINE.md")
    if not os.path.exists(p):
        return {}
    types, cur = {}, None
    for line in open(p, encoding="utf-8"):
        h = re.match(r"## (\d+)\.", line)
        if h:
            cur = int(h.group(1))
        t = re.search(r"Type:\s*(overview|mechanism)", line, re.I)
        if t and cur:
            types[cur] = t.group(1).lower()
    return types


def ingested_docs(ws):
    """Basenames of ingested docs the output must not reference (all but `external`).

    Read from the first column of SOURCES.md's table, `| `path` | level | ...`, plus
    state.json's "sources" list. A companion file must not share a basename with one.
    """
    names = set()
    p = os.path.join(ws, "SOURCES.md")
    if os.path.exists(p):
        for m in re.finditer(r"^\|\s*`([^`]+)`\s*\|\s*(\w+)", open(p, encoding="utf-8").read(), re.M):
            if m.group(2).lower() != "external":
                names.add(os.path.basename(m.group(1)))
    p = os.path.join(ws, "state.json")
    if os.path.exists(p):
        try:
            for src in json.load(open(p, encoding="utf-8")).get("sources", []):
                if src.get("level") != "external" and src.get("path"):
                    names.add(os.path.basename(src["path"]))
        except (ValueError, AttributeError):
            pass
    return sorted(names)


def phrase_hits(prose, phrases, is_regex=False):
    hits = []
    for w in phrases:
        pat = w if is_regex else re.escape(w)
        hits += [m.group(0) for m in re.finditer(rf"\b{pat}\b", prose, re.I)]
    return hits


def main():
    ws = sys.argv[1].rstrip("/")
    strict = "--strict" in sys.argv
    files = sorted(glob.glob(os.path.join(ws, "sections", "*.md")))
    if not files:
        sys.exit(f"no sections in {ws}/sections/")

    terms = context_terms(ws)
    sec_types = section_types(ws)
    sources = ingested_docs(ws)
    agg = Counter()
    all_sent, headings, rows, sec_nums = [], [], [], []

    for f in files:
        raw = open(f, encoding="utf-8").read()
        base = os.path.basename(f)
        num = int(base.split("-")[0])
        sec_nums.append(num)
        prose = strip_noise(raw)
        sents = sentences(prose)
        all_sent += sents
        words = len(prose.split())

        r = {"file": base, "words": words}
        r["mismatch"] = 0 if re.search(rf"^## {num}\. ", raw, re.M) else 1
        r["banned"] = sum(len(re.findall(rf"\b{w}\b", prose, re.I)) for w in BANNED)
        vague, filler = phrase_hits(prose, VAGUE), phrase_hits(prose, FILLER, True)
        r["vague"], r["_vague"] = len(vague), vague
        r["filler"], r["_filler"] = len(filler), filler
        # provenance comments are workspace-only and stripped at assembly; skip them
        visible = re.sub(r"<!--.*?-->", " ", raw, flags=re.S)
        srcs = [n for n in sources for _ in re.finditer(re.escape(n), visible)]
        r["srclinks"], r["_srclinks"] = len(srcs), srcs
        r["hedges"] = sum(len(re.findall(rf"\b{w}\b", prose, re.I)) for w in HEDGES)
        long_s = [s for s in sents if len(s.split()) > 30]
        r["long"], r["_long"] = len(long_s), long_s
        r["sents"] = len(sents)
        d = diagrams(raw)
        r["diagrams"] = len(d)
        r["unlabeled"] = sum(x["unlabeled"] for x in d)
        r["_diag"] = [f"{x['kind']} {x['nodes']}n/{x['edges']}e, {x['unlabeled']} unlabeled"
                      for x in d if x["unlabeled"]]
        mech = sec_types.get(num) == "mechanism"
        max_n, max_e = (14, 18) if mech else (9, 12)
        r["oversized"] = sum(1 for x in d if x["nodes"] > max_n or x["edges"] > max_e)
        r["cites"] = len(re.findall(r"\]\([^)]+\)|`[\w/]+\.(?:java|rs|conf|kts|md|toml)`", raw))
        drift, drifts = 0, []
        for t in terms:
            loose = re.sub(r"([a-z])([A-Z])", r"\1[ _-]?\2", t).replace(".", r"\.")
            for m in re.finditer(loose, raw, re.I):
                if m.group(0) != t:
                    drift += 1
                    drifts.append(f"{t} -> {m.group(0)!r}")
        r["drift"] = drift
        r["_drift"] = drifts
        headings += re.findall(r"^#{2,4} (.+)$", raw, re.M)
        rows.append(r)
        for k in ("mismatch", "banned", "vague", "filler", "srclinks", "hedges", "long",
                  "sents", "unlabeled", "oversized", "cites", "drift", "words", "diagrams"):
            agg[k] += r[k]

    dup = [h for h, c in Counter(headings).items() if c > 1]
    body = "\n".join(open(f, encoding="utf-8").read() for f in files)
    refs = {int(x[1:]) for x in re.findall(r"§\d+", body)}
    dangling = sorted(refs - set(sec_nums))

    m = {
        "heading_mismatch": agg["mismatch"],
        "dangling_refs": len(dangling),
        "duplicate_headings": len(dup),
        "term_drift": agg["drift"],
        "source_links": agg["srclinks"],
        "banned_words": agg["banned"],
        "vague_words": agg["vague"],
        "filler_phrases": agg["filler"],
        "unlabeled_edges": agg["unlabeled"],
        "oversized_diagrams": agg["oversized"],
        "mean_sentence_len": round(sum(len(s.split()) for s in all_sent) / max(len(all_sent), 1), 1),
        "pct_long_sentences": round(100 * agg["long"] / max(agg["sents"], 1), 1),
        "hedge_per_1k": round(1000 * agg["hedges"] / max(agg["words"], 1), 1),
        "cites_per_1k": round(1000 * agg["cites"] / max(agg["words"], 1), 1),
    }

    w = max(len(r["file"]) for r in rows)
    flagged = ("mismatch", "srclinks", "unlabeled", "oversized", "banned", "vague",
               "filler", "drift")
    print(f"{'section'.ljust(w)}  words  sent  >30w  diag  unlbl  src  vague  fill  drift  hedge")
    for r in rows:
        bad = [k for k in flagged if r[k]]
        flag = "  <-- " + " ".join(bad) if bad else ""
        print(f"{r['file'].ljust(w)}  {r['words']:5}  {r['sents']:4}  {r['long']:4}  "
              f"{r['diagrams']:4}  {r['unlabeled']:5}  {r['srclinks']:3}  {r['vague']:5}  "
              f"{r['filler']:4}  {r['drift']:5}  {r['hedges']:5}{flag}")

    print("\n--- consistency (exact) ---")
    for k in ("heading_mismatch", "dangling_refs", "duplicate_headings"):
        print(f"  {k:22} {m[k]}")
    if dangling:
        print(f"    dangling: {dangling}")
    if dup:
        print(f"    duplicate headings: {dup[:5]}")
    print("--- self-containment (exact) ---")
    print(f"  {'source_links':22} {m['source_links']}   ({len(sources)} ingested docs checked)")
    print("--- precision (exact) ---")
    for k in ("mean_sentence_len", "pct_long_sentences", "banned_words", "vague_words",
              "filler_phrases", "oversized_diagrams"):
        print(f"  {k:22} {m[k]}")
    print("--- needs judgment (never gated) ---")
    print(f"  {'term_drift':22} {m['term_drift']}   (run --verbose; class vs concept is legitimate)")
    print(f"  {'cites_per_1k':22} {m['cites_per_1k']}   (code paths + internal links; higher is better)")
    print(f"  {'hedge_per_1k':22} {m['hedge_per_1k']}   (heuristic: lower is better)")
    print("--- diagrams (exact) ---")
    print(f"  {'unlabeled_edges':22} {m['unlabeled_edges']}")

    failed = []
    for k, (op, thr) in GATES.items():
        v = m[k]
        if (op == "==" and v != thr) or (op == "<=" and v > thr):
            failed.append(f"{k}={v} (gate {op} {thr})")
    if "--verbose" in sys.argv:
        print("\n--- offenders ---")
        for r in rows:
            out = []
            if r["_srclinks"]:
                out.append("source refs: " + ", ".join(sorted(set(r["_srclinks"]))))
            if r["_vague"]:
                out.append("vague: " + ", ".join(sorted(set(x.lower() for x in r["_vague"]))))
            if r["_filler"]:
                out.append("filler: " + ", ".join(sorted(set(x.lower() for x in r["_filler"]))))
            if r["_diag"]:
                out.append("diagrams: " + "; ".join(r["_diag"]))
            for s in r["_long"]:
                out.append(f">30w ({len(s.split())}): {s[:90]}...")
            if r["_drift"]:
                out.append("drift: " + "; ".join(sorted(set(r["_drift"]))))
            if out:
                print(f"  {r['file']}")
                for o in out:
                    print(f"    {o}")

    print("\nGATES: " + ("PASS" if not failed else "FAIL — " + "; ".join(failed)))
    if strict and failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
