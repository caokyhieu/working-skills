"""Judge support for code-cards: claim lines, complexity tiers, canaries, report parsing,
and the mechanical checks that need no model (imports vs depends_on, signatures).
Standard library only; imported by cards.py.
"""
import math
import os
import random
import re

RNG = random.SystemRandom()
ANCHOR_IN_CELL = re.compile(r"[\w./-]+\.[A-Za-z0-9]+(?:::[\w.]+|:\d+)")
SWAPS = [("True", "False"), ("true", "false"), ("at most", "at least"), ("before", "after"),
         ("fails open", "fails closed"), ("inclusive", "exclusive"), ("retries", "does not retry"),
         ("never", "always"), ("increments", "decrements"), ("first", "last"),
         ("minimum", "maximum"), ("reads", "writes"), ("blocks", "does not block"),
         ("synchronously", "asynchronously"), ("ascending", "descending")]
CONCURRENCY = re.compile(r"\b(thread|threading|lock|mutex|async|await|synchronized|volatile|"
                         r"atomic|executor|semaphore|condition|goroutine|chan\b|future|"
                         r"completablefuture|multiprocessing|queue)\b", re.I)
BRANCH = re.compile(r"\b(if|elif|else|case|switch|match|catch|except|while|for|when)\b")
RAISE = re.compile(r"\b(raise|throw|throws|panic)\b")
DEPTH_CHECKLIST = """\
This module is COMPLEX. In addition to the rules above:
- Trace, do not sample. For every Flow step, follow the call into the callee, across
  files and into other modules when needed, and write the chain in the Trace section.
- Failure modes: for each row, cite the site that raises/returns the error AND the site
  that handles it (two locations). Look for errors swallowed between them.
- Concurrency: which thread or task runs each step; which lock guards which state;
  what happens on concurrent calls; callbacks run on whose thread.
- Lifecycle: every state and the transition that enters and leaves it; what happens on
  close/shutdown mid-operation; resources opened and where they are released.
- Config: where each key is read, precedence (env / file / default), and whether a
  default in the card matches every place the key is read.
- Boundaries: empty input, zero, max size, timeout expiry, retry exhaustion.
- Where a behavioral claim can be confirmed by running a small throwaway probe
  (e.g. python -c, a unit test run), run it and mark the evidence (ran)."""


MERMAID_STRUCTURE = re.compile(
    r"^(flowchart|graph|sequenceDiagram|stateDiagram(-v2)?|erDiagram|classDiagram)\b|"
    r"^(end|else|direction\s+\w+|autonumber|%%.*|classDef\b.*|class\s.*|style\s.*|linkStyle\s.*)$|"
    r"^(participant|actor)\s+\w+$")
MERMAID_TYPES = ("flowchart", "graph", "sequenceDiagram", "stateDiagram", "stateDiagram-v2", "erDiagram")
EDGE = re.compile(r"(-->|---|-\.->|==>|--[ox]|->>|-->>|-\)|-x)")


# ---------- card lines ----------

def claim_lines(text):
    """[(lineno, section)] of lines carrying claims: inside a ## section, not headings,
    table headers/separators, fences or comments. Line numbers are 1-based, whole file."""
    lines = text.splitlines()
    out, section, start = [], None, 0
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        start = text[:end + 4].count("\n") + 1 if end != -1 else 0
    fence = None
    for i in range(start, len(lines)):
        l = lines[i].strip()
        if l.startswith("```"):
            fence = None if fence else (l[3:].strip() or "text")
            continue
        if fence == "mermaid":
            if l and not MERMAID_STRUCTURE.match(l):
                out.append((i + 1, section or "Diagram"))
            continue
        if l.startswith("## ") and not fence:
            section = l[3:].strip()
            continue
        if not section or not l or l.startswith(("#", "<!--")):
            continue
        if l.startswith("|"):
            if re.match(r"^\|[\s:|-]+\|$", l):
                continue
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if re.match(r"^\|[\s:|-]+\|$", nxt):
                continue  # header row
        out.append((i + 1, section))
    return out


def carried_lines(old_text, new_text, ok_lines):
    """Line numbers in new_text that are unchanged from old_text and were judged OK there."""
    sm = __import__("difflib").SequenceMatcher(a=old_text.splitlines(), b=new_text.splitlines(), autojunk=False)
    carried = set()
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == "equal":
            for k in range(a1 - a0):
                if (a0 + k + 1) in ok_lines:
                    carried.add(b0 + k + 1)
    return carried


# ---------- complexity ----------

def complexity(root, files):
    m = {"files": len(files), "loc": 0, "branches": 0, "raises": 0, "concurrency": 0}
    for f in files:
        try:
            t = (root / f).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        code = [l for l in t.splitlines() if l.strip() and not l.strip().startswith(("#", "//", "*", "/*"))]
        m["loc"] += len(code)
        body = "\n".join(code)
        m["branches"] += len(BRANCH.findall(body))
        m["raises"] += len(RAISE.findall(body))
        m["concurrency"] += len(CONCURRENCY.findall(body))
    if m["loc"] > 1500 or m["concurrency"] >= 5 or m["branches"] > 250 or m["files"] > 15:
        tier = "complex"
    elif m["loc"] > 400 or m["branches"] > 60 or m["concurrency"] > 0:
        tier = "medium"
    else:
        tier = "small"
    return tier, m


def plan_shards(tier, metrics, required):
    """Split required [(line, section)] into shards by section, balanced by line count."""
    if tier == "complex":
        n = max(2, min(4, math.ceil(metrics["loc"] / 1500)))
    else:
        n = 1
    n = max(1, min(n, len(required) // 8 or 1))
    by_sec = {}
    for ln, sec in required:
        by_sec.setdefault(sec, []).append(ln)
    shards = [[] for _ in range(n)]
    for sec, lns in sorted(by_sec.items(), key=lambda kv: -len(kv[1])):
        min(shards, key=len).extend(lns)
    return [sorted(s) for s in shards if s]


PROBES = {"small": 3, "medium": 5, "complex": 6}


# ---------- canary ----------

def _outside_ticks(line):
    """[(start, end)] spans of line outside backticks."""
    spans, pos, inside = [], 0, False
    for m in re.finditer("`", line):
        if not inside:
            spans.append((pos, m.start()))
        pos, inside = m.end(), not inside
    if not inside:
        spans.append((pos, len(line)))
    return spans


def _mutations(line):
    out = []
    lead = re.match(r"^\s*(\d+\.\s|[-*]\s|\|)?", line).end()
    for a, b in _outside_ticks(line):
        a = max(a, lead)
        for m in re.finditer(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])", line[a:b]):
            s, e = a + m.start(1), a + m.end(1)
            v = m.group(1)
            if "." in v:
                new = f"{float(v) * 2:g}"
            else:
                n = int(v)
                new = str(n + 1 if n < 10 else n * 2)
            out.append(line[:s] + new + line[e:])
        for x, y in SWAPS:
            for w, r in ((x, y), (y, x)):
                for m in re.finditer(r"\b" + re.escape(w) + r"\b", line[a:b]):
                    s, e = a + m.start(), a + m.end()
                    out.append(line[:s] + r + line[e:])
    return [o for o in out if o != line]


def plant(text, candidate_lines):
    """Mutate one claim on one candidate line. Return (new_text, canary) or (text, None)."""
    lines = text.splitlines()
    options = []
    for ln in candidate_lines:
        for mut in _mutations(lines[ln - 1]):
            weight = 3 if lines[ln - 1].lstrip().startswith("|") else 1
            options += [(ln, mut)] * weight
    if not options:
        return text, None
    ln, mut = RNG.choice(options)
    canary = {"line": ln, "original": lines[ln - 1], "mutated": mut}
    lines[ln - 1] = mut
    return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), canary


# ---------- report ----------

VERDICTS = {"OK", "WRONG", "UNSUPPORTED"}
PROBE_VERDICTS = {"OK", "MISLEADING", "UNANSWERED"}


def _cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def parse_report(text):
    rep = {"prep": None, "claims": [], "missing": [], "probes": [], "trace": "", "verdict_line": None}
    m = re.search(r"^prep:\s*(\S+)", text, re.M)
    rep["prep"] = m.group(1) if m else None
    section = None
    for line in text.splitlines():
        h = re.match(r"^##\s+(\w+)", line)
        if h:
            section = h.group(1).lower()
            continue
        if line.startswith("VERDICT:"):
            rep["verdict_line"] = line.strip()
        if section == "claims" and line.startswith("|"):
            c = _cells(line)
            lns = [int(x) for x in re.findall(r"L(\d+)", c[0])] if c else []
            v = next((x for x in c if x in VERDICTS), None)
            if lns and v:
                rep["claims"].append({"lines": lns, "section": c[1] if len(c) > 1 else "",
                                      "claim": c[2] if len(c) > 2 else "", "verdict": v,
                                      "evidence": c[-1]})
        elif section == "missing":
            mm = re.match(r"^\s*-\s*(M\d+)\s*:\s*(.+)", line)
            if mm:
                rep["missing"].append({"id": mm.group(1), "text": mm.group(2)})
        elif section == "probe" and line.startswith("|"):
            c = _cells(line)
            if c and re.match(r"^P\d+$", c[0]):
                v = next((x for x in reversed(c) if x in PROBE_VERDICTS), None)
                rep["probes"].append({"id": c[0], "question": c[1] if len(c) > 1 else "", "verdict": v,
                                      "card_lines": [int(x) for x in re.findall(r"L(\d+)", c[2] if len(c) > 2 else "")]})
        elif section == "trace":
            rep["trace"] += line + "\n"
    return rep


def evidence_locations(cell):
    """Code locations cited. For negative claims ("None.") a whole file read, or a search
    or probe the judge ran, counts as one."""
    n = len(ANCHOR_IN_CELL.findall(cell))
    if n:
        return n
    return 1 if re.search(r"\(ran\b", cell) or re.search(r"[\w-]+/[\w./-]+\.[A-Za-z0-9]+", cell) else 0


# ---------- mechanical checks ----------

def _py_candidates(spec_dots, mod, names, relfile):
    bases = []
    if spec_dots:
        d = os.path.dirname(relfile)
        for _ in range(len(spec_dots) - 1):
            d = os.path.dirname(d)
        bases.append(d)
    else:
        bases += ["", "src", "lib"]
    parts = [p for p in mod.split(".") if p]
    out = []
    for b in bases:
        stems = ["/".join([b] + parts).strip("/")] if parts else [b]
        stems += ["/".join([b] + parts + [n]).strip("/") for n in names]
        for i in range(len(parts) - 1, 0, -1):
            stems.append("/".join([b] + parts[:i]).strip("/"))
        for s in stems:
            if s:
                out += [s + ".py", s + "/__init__.py"]
    return out


def imports(root, relfile, fileset):
    """Project files imported by relfile (Python, JS/TS, Java/Kotlin). Others: empty."""
    try:
        text = (root / relfile).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return set()
    ext = relfile.rsplit(".", 1)[-1]
    cands = []
    if ext in ("py", "pyx"):
        for m in re.finditer(r"^[ \t]*from[ \t]+(\.*)([\w.]*)[ \t]+import[ \t]+(?:\(([^)]*)\)|([^\n#]+))", text, re.M):
            names = [n.split()[0] for n in (m.group(3) or m.group(4)).split(",") if n.split()]
            cands += _py_candidates(m.group(1), m.group(2), [n for n in names if n and n != "*"], relfile)
        for m in re.finditer(r"^[ \t]*import[ \t]+([\w., \t]+)", text, re.M):
            for mod in m.group(1).split(","):
                cands += _py_candidates("", mod.strip().split(" ")[0], [], relfile)
    elif ext in ("js", "jsx", "ts", "tsx", "mjs"):
        for m in re.finditer(r"""(?:from|import|require\()\s*['"](\.{1,2}/[^'"]+)['"]""", text):
            base = os.path.normpath(os.path.join(os.path.dirname(relfile), m.group(1))).replace(os.sep, "/")
            cands.append(base)
            for e in ("ts", "tsx", "js", "jsx", "mjs"):
                cands += [f"{base}.{e}", f"{base}/index.{e}"]
    elif ext in ("java", "kt", "scala"):
        for m in re.finditer(r"^\s*import\s+(?:static\s+)?([\w.]+?)(?:\.\*)?;?\s*$", text, re.M):
            p = m.group(1).replace(".", "/")
            for r in ("", "src/main/java/", "src/main/kotlin/", "src/"):
                for e in ("java", "kt", "scala"):
                    cands.append(f"{r}{p}.{e}")
                    cands.append(f"{r}{p.rsplit('/', 1)[0]}.{e}")
            # also any module root: */src/main/java/<p>.java
            tail = f"/src/main/java/{p}.java"
            cands += [f for f in fileset if f.endswith(tail)]
    return {c for c in cands if c in fileset and c != relfile}


def _balanced(text, i):
    """Content of the paren group opening at text[i] == '('."""
    depth = 0
    for j in range(i, min(len(text), i + 4000)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return text[i + 1:j], j
    return None, None


def def_params(root, path, symbol):
    """Parameter text of symbol's definition, or None if not found / a class."""
    try:
        text = (root / path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    name = symbol.split(".")[-1]
    if re.search(r"\b(class|interface|struct|enum|record)\s+" + re.escape(name) + r"\b", text):
        return None
    for pat in (r"\bdef\s+" + re.escape(name) + r"\s*\(",
                r"\bfunction\s*\*?\s*" + re.escape(name) + r"\s*\(",
                r"\bfunc\s+(?:\([^)]*\)\s*)?" + re.escape(name) + r"\s*\(",
                r"\bfn\s+" + re.escape(name) + r"\s*[<(]",
                r"\b" + re.escape(name) + r"\s*=\s*(?:async\s*)?\("):
        m = re.search(pat, text)
        if m:
            k = text.index("(", m.end() - 1)
            return _balanced(text, k)[0]
    for m in re.finditer(r"\b" + re.escape(name) + r"\s*\(", text):
        inner, j = _balanced(text, m.end() - 1)
        if inner is None:
            continue
        after = text[j + 1:j + 40].lstrip()
        if after.startswith(("{", ":", "->", "throws", "=>")) and not text[:m.start()].rstrip().endswith(("new", "return", "=", ".")):
            return inner
    return None


def card_params(sig):
    m = re.search(r"\(", sig)
    if not m:
        return None
    inner, _ = _balanced(sig, m.start())
    if inner is None or not inner.strip() or inner.strip() in ("...", "…"):
        return [] if inner is not None and not inner.strip() else None
    out, depth, cur = [], 0, ""
    for ch in inner:
        if ch in "([{<":
            depth += 1
        elif ch in ")]}>":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    names = []
    for p in out:
        p = p.strip().lstrip("*&").split("=")[0].split(":")[0].strip()
        if not p or p in ("self", "cls", "/", "...", "…", "this"):
            continue
        ids = re.findall(r"[A-Za-z_]\w*", p)
        if ids:
            names.append(ids[-1])
    return names


# ---------- diagrams ----------

def mermaid_blocks(text):
    """[(start_line, [lines])] of ```mermaid blocks; start_line is the first body line."""
    out, cur, start = [], None, 0
    for i, l in enumerate(text.splitlines(), 1):
        s = l.strip()
        if cur is None and s.startswith("```mermaid"):
            cur, start = [], i + 1
        elif cur is not None and s.startswith("```"):
            out.append((start, cur))
            cur = None
        elif cur is not None:
            cur.append(l)
    return out


def _node_ids(line):
    ids = set()
    for m in re.finditer(r"(?:^|[\s>|&-])([A-Za-z_][\w]*)\s*(?=[\[({]|-->|---|-\.|==>|$|\s*&|\s*-)", line):
        if m.group(1) not in ("end", "subgraph", "direction", "flowchart", "graph", "click", "style", "class"):
            ids.add(m.group(1))
    return ids


def lint_mermaid(start, body, max_nodes):
    """(errors, warnings) for one block. Structural checks only; render with mmdc for a parse."""
    errs, warns = [], []
    rows = [(start + i, l.strip()) for i, l in enumerate(body) if l.strip() and not l.strip().startswith("%%")]
    if not rows:
        return [f"L{start}: empty mermaid block"], []
    kind = rows[0][1].split()[0]
    if kind not in MERMAID_TYPES:
        return [f"L{start}: diagram type '{kind}' not one of flowchart, sequenceDiagram, stateDiagram-v2, erDiagram"], []
    depth = 0
    opener = re.compile(r"^(subgraph|alt|opt|loop|par|critical|break|rect|box)\b") if kind != "erDiagram" else None
    nodes, out_edges = set(), {}
    for n, l in rows[1:]:
        ln = f"L{n}"
        for o, c in ("[]", "()", "{}"):
            if l.count(o) != l.count(c):
                errs.append(f"{ln}: unbalanced {o}{c} in: {l[:60]}")
        if l.count('"') % 2:
            errs.append(f"{ln}: unbalanced quote in: {l[:60]}")
        if opener and opener.match(l):
            depth += 1
        elif l == "end":
            depth -= 1
            if depth < 0:
                errs.append(f"{ln}: 'end' without an opening subgraph/alt/loop")
                depth = 0
        if re.match(r"^(style|classDef|linkStyle)\b", l):
            warns.append(f"{ln}: styling in a diagram; structure carries the meaning")
        if kind in ("flowchart", "graph"):
            if not l.startswith(("subgraph", "end", "direction")):
                nodes |= _node_ids(l)
            m = re.match(r"^([A-Za-z_]\w*)\b.*?(-->|-\.->|==>)\s*(\|[^|]*\|)?", l)
            if m:
                out_edges.setdefault(m.group(1), []).append(bool(m.group(3)) or "-- " in l or '-- "' in l)
        elif kind.startswith("stateDiagram"):
            if "-->" in l and ":" not in l and "[*]" not in l:
                warns.append(f"{ln}: state transition without a trigger label (`A --> B : event`)")
            nodes |= set(re.findall(r"([A-Za-z_]\w*)\s*(?:-->|$)", l))
        elif kind == "sequenceDiagram":
            m = re.match(r"^(participant|actor)\s+(\w+)", l)
            if m:
                nodes.add(m.group(2))
            if re.search(r"-[->x)]+", l) and ":" not in l:
                warns.append(f"{ln}: message without a label (`A->>B: call()`)")
    if depth:
        errs.append(f"L{start}: {depth} subgraph/alt/loop block(s) not closed with 'end'")
    if len(nodes) > max_nodes:
        warns.append(f"L{start}: {len(nodes)} nodes, over {max_nodes}; split into an overview plus one diagram per part")
    for src, labelled in out_edges.items():
        if len(labelled) > 1 and not all(labelled):
            warns.append(f"L{start}: '{src}' has {len(labelled)} outgoing edges, not all labelled; label each choice")
    return errs, warns


def render_check(body, mmdc):
    """Parse one block with mermaid-cli. Return an error string or None."""
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        src, out = os.path.join(d, "d.mmd"), os.path.join(d, "d.svg")
        with open(src, "w", encoding="utf-8") as f:
            f.write("\n".join(body) + "\n")
        r = subprocess.run([mmdc, "-i", src, "-o", out, "-q"], capture_output=True, text=True)
        if r.returncode != 0:
            return (r.stderr or r.stdout).strip().splitlines()[-1][:160] if (r.stderr or r.stdout).strip() else "mmdc failed"
    return None


def import_graph(root, files, fileset, owners, module):
    """Mermaid flowchart of file-level imports inside a module plus edges to other modules."""
    ids, edges = {}, set()
    def nid(key):
        return ids.setdefault(key, f"n{len(ids)}")
    for f in files:
        nid(f)
        for g in imports(root, f, fileset):
            o = owners.get(g)
            if o == module:
                edges.add((f, g))
            elif o:
                nid("module:" + o)
                edges.add((f, "module:" + o))
    lines = ["flowchart LR"]
    for key, i in ids.items():
        label = key[7:] if key.startswith("module:") else key.rsplit("/", 1)[-1]
        shape = f'{i}[["{label}"]]' if key.startswith("module:") else f'{i}["{label}"]'
        lines.append("  " + shape)
    for a, b in sorted(edges):
        lines.append(f"  {nid(a)} --> {nid(b)}")
    return lines, len(ids), len(edges)
