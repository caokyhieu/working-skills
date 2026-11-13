#!/usr/bin/env python3
"""Card store helper for code-cards. Standard library only.

  init     create docs/cards/ with config, system card and a proposed module split
  status   stale cards (source changed since stamp), uncovered and double-covered files
  diff     files changed under one card since its stamp, with the git diff stat
  stamp    record the source fingerprint of cards after they were updated and checked
  check    lint cards: front matter, sections, anchors, signatures, imports vs depends_on
  graph    mermaid of a module's file imports (or of all modules), derived from the code
  judge    prepare independent judge runs for a card: claim lines, shards, planted canaries
  verdict  grade the judges' reports; a card is stamped only after a passing verdict
  history  versions of a card (or the project changelog); --diff between two versions
  release  freeze every current card into releases/<name>/ with a manifest
  readme   write the generated section between markers in README.md (--check: fail if stale)
"""
import argparse
import datetime
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import judge  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
START = "<!-- code-cards:start -->"
END = "<!-- code-cards:end -->"
NOTICE = "<!-- generated from {cards} by code-cards; edit the cards, then run cards.py readme -->"
SYSTEM = "_system.md"
STAMPS = "stamps.json"
RESERVED = {"CHANGELOG.md", "README.md", "MANIFEST.md"}
SIG_EXT = {"py", "pyx", "js", "jsx", "ts", "tsx", "mjs", "java", "kt", "scala"}

DEFAULT_CONFIG = {
    "readme": "README.md",
    "readme_heading": "Architecture",
    "readme_sections": ["Summary", "Runtime view", "Flows", "Run and test"],
    "source_globs": ["**/*." + e for e in (
        "py", "pyx", "js", "jsx", "ts", "tsx", "mjs", "go", "rs", "java", "kt", "scala",
        "c", "cc", "cpp", "h", "hpp", "cs", "rb", "php", "swift", "sql", "sh", "proto")],
    "ignore_globs": ["docs/**", "**/tests/**", "tests/**", "**/test/**", "**/test_*",
                     "**/*_test.*", "**/*.test.*", "**/*.spec.*", "**/migrations/**",
                     "**/vendor/**", "**/node_modules/**", "**/.venv/**", "**/build/**",
                     "**/dist/**", ".claude/**", ".agents/**"],
    "max_card_lines": 150,
    "max_diagram_nodes": 12,
    "mmdc": "mmdc",
}
REQUIRED = ["Purpose", "Interface", "Flow", "Invariants", "Failure modes", "Dependencies"]
VAGUE = ["various", "appropriately", "properly", "as needed", "etc.", "and so on",
         "a number of", "in some cases", "robust", "seamless", "powerful", "simply",
         "easily", "comprehensive", "leverage", "handles errors", "if necessary"]
ANCHOR = re.compile(r"`([\w./-]+\.[A-Za-z0-9]+)(?:::([\w.]+)|:(\d+)(?:-\d+)?)?`")
GROUP_DIRS = {"src", "lib", "pkg", "app", "apps", "packages", "internal", "cmd", "services"}


# ---------- small utilities ----------

def git(root, *args):
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    except FileNotFoundError:
        return None
    return r.stdout if r.returncode == 0 else None


def glob_re(pattern):
    out, i = "", 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif c == "*":
            out, i = out + "[^/]*", i + 1
        elif c == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(c), i + 1
    return re.compile(out + r"\Z")


def matcher(patterns):
    regs = [glob_re(p.rstrip("/") + ("/**" if p.endswith("/") else "")) for p in patterns]
    return lambda path: any(r.match(path) for r in regs)


ARTIFACTS = matcher(["**/__pycache__/**", "**/*.pyc", "**/*.pyo", "**/*.class", "**/*.o", "**/*.so",
                     "**/.DS_Store", "**/node_modules/**", "**/.pytest_cache/**", "**/.mypy_cache/**",
                     "**/target/**", "**/*.egg-info/**"])


def list_files(root):
    out = git(root, "ls-files", "--cached", "--others", "--exclude-standard")
    if out is not None:
        return sorted(p for p in out.splitlines() if p and not ARTIFACTS(p) and (root / p).is_file())
    files = []
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x not in ("node_modules", "__pycache__")]
        files += [str((Path(d) / n).relative_to(root)).replace(os.sep, "/") for n in names]
    return sorted(f for f in files if not ARTIFACTS(f))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def parse_value(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        return [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
    return v.strip("'\"")


def parse_card(path):
    """Return (front matter dict, {section: body}, body line count)."""
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            key = None
            for line in text[4:end].splitlines():
                if re.match(r"^\s+-\s+", line) and key:
                    meta.setdefault(key, [])
                    if isinstance(meta[key], list):
                        meta[key].append(line.split("-", 1)[1].strip().strip("'\""))
                elif ":" in line and not line.startswith(" "):
                    key, v = line.split(":", 1)
                    key = key.strip()
                    meta[key] = parse_value(v) if v.strip() else []
            body = text[end + 4:].lstrip("\n")
    sections, cur = {}, None
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1)
            sections[cur] = []
        elif cur:
            sections[cur].append(line)
    sections = {k: "\n".join(v).strip() for k, v in sections.items()}
    return meta, sections, len(body.splitlines())


def as_list(v):
    return v if isinstance(v, list) else ([v] if v else [])


# ---------- the card store ----------

class Store:
    def __init__(self, root, cards):
        self.root = Path(root).resolve()
        self.dir = (self.root / cards).resolve()
        self.rel = str(self.dir.relative_to(self.root))
        cfg = self.dir / "config.json"
        self.config = dict(DEFAULT_CONFIG)
        if cfg.exists():
            self.config.update(json.loads(cfg.read_text(encoding="utf-8")))
        sp = self.dir / STAMPS
        self.stamps = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {"cards": {}}
        self._files = None

    @property
    def files(self):
        if self._files is None:
            self._files = list_files(self.root)
        return self._files

    def cards(self):
        out = {}
        if not self.dir.is_dir():
            return out
        for p in sorted(self.dir.glob("*.md")):
            if p.name.startswith("_") or p.name in RESERVED:
                continue
            meta, sections, n = parse_card(p)
            out[meta.get("module") or p.stem] = {"path": p, "meta": meta, "sections": sections, "lines": n}
        return out

    def card_files(self, card):
        inc = matcher(as_list(card["meta"].get("paths")))
        exc = matcher(as_list(card["meta"].get("exclude")))
        return [f for f in self.files if inc(f) and not exc(f)]

    def fingerprint(self, card):
        return {f: sha(self.root / f) for f in self.card_files(card)}

    def system_shape(self, cards):
        edges = sorted(f"{m}->{d}" for m, c in cards.items() for d in as_list(c["meta"].get("depends_on")))
        return hashlib.sha256(json.dumps([sorted(cards), edges]).encode()).hexdigest()[:16]

    def files_hash(self, module, cards):
        if module == "_system":
            return self.system_shape(cards)
        fp = self.fingerprint(cards[module])
        return hashlib.sha256(json.dumps(fp, sort_keys=True).encode()).hexdigest()[:16]

    def card_path(self, module, cards):
        return self.dir / SYSTEM if module == "_system" else cards[module]["path"]

    def save_stamps(self):
        (self.dir / STAMPS).write_text(json.dumps(self.stamps, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compare(old, new):
    changed = sorted(f for f in new if f in old and old[f] != new[f])
    added = sorted(f for f in new if f not in old)
    removed = sorted(f for f in old if f not in new)
    return changed, added, removed


# ---------- commands ----------

def cmd_init(st, args):
    st.dir.mkdir(parents=True, exist_ok=True)
    cfg = st.dir / "config.json"
    if not cfg.exists():
        cfg.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {st.rel}/config.json")
    sysc = st.dir / SYSTEM
    if not sysc.exists():
        shutil.copy(SKILL / "templates" / "system-card.md", sysc)
        print(f"wrote {st.rel}/{SYSTEM}")
    src, ign = matcher(st.config["source_globs"]), matcher(st.config["ignore_globs"])
    groups = {}
    for f in st.files:
        if not src(f) or ign(f):
            continue
        parts = f.split("/")
        if len(parts) == 1:
            key = "."
        elif parts[0] in GROUP_DIRS and len(parts) > 2:
            key = "/".join(parts[:2])
        else:
            key = parts[0]
        groups.setdefault(key, []).append(f)
    print("\nProposed modules (one card each; merge or split before drafting):\n")
    print(f"{'module':24} {'paths':36} files")
    template = (SKILL / "templates" / "module-card.md").read_text(encoding="utf-8")
    for key, fs in sorted(groups.items()):
        name = "root" if key == "." else key.split("/")[-1]
        paths = [f for f in fs] if key == "." else [key + "/**"]
        print(f"{name:24} {', '.join(paths)[:36]:36} {len(fs)}")
        card = st.dir / f"{name}.md"
        if args.write and not card.exists():
            fm = f"module: {name}\npaths: [{', '.join(paths)}]"
            card.write_text(template.replace("module: TBD\npaths: [TBD]", fm), encoding="utf-8")
    if args.write:
        print(f"\nwrote skeleton cards into {st.rel}/ (existing cards untouched)")
    else:
        print("\nre-run with --write to create skeleton cards for these modules")


def cmd_graph(st, args):
    cards = st.cards()
    if not args.module:
        edges = [(m, d) for m, c in cards.items() for d in as_list(c["meta"].get("depends_on")) if d in cards]
        ident = {m: re.sub(r"\W", "_", m) for m in cards}
        print("```mermaid\nflowchart LR")
        for m in cards:
            print(f'  {ident[m]}["{m}"]')
        for a, b in edges:
            print(f"  {ident[a]} --> {ident[b]}")
        print("```")
        return 0
    if args.module not in cards:
        sys.exit(f"unknown module {args.module}")
    owners = {}
    for m, c in cards.items():
        for f in st.card_files(c):
            owners.setdefault(f, m)
    lines, n, e = judge.import_graph(st.root, st.card_files(cards[args.module]), set(st.files), owners, args.module)
    print("```mermaid\n" + "\n".join(lines) + "\n```")
    print(f"<!-- {n} nodes, {e} edges, from static imports; [[x]] = another module -->", file=sys.stderr)
    if n > st.config["max_diagram_nodes"]:
        print(f"over {st.config['max_diagram_nodes']} nodes: draw the main path only, or split the module",
              file=sys.stderr)
    return 0


def cmd_status(st, args):
    cards = st.cards()
    if not cards:
        print(f"no cards in {st.rel}/ — run init first")
        return 1
    problems = 0
    print(f"{'module':24} {'state':10} detail")
    for m, c in cards.items():
        now = st.fingerprint(c)
        rec = st.stamps["cards"].get(m)
        if not now:
            state, detail = "no-files", "paths match no file"
        elif rec is None:
            state, detail = "unstamped", f"{len(now)} files"
        else:
            ch, ad, rm = compare(rec["files"], now)
            if ch or ad or rm:
                state = "stale"
                detail = f"{len(ch)} changed, {len(ad)} added, {len(rm)} removed since {rec['stamped']}"
            elif rec.get("card_sha") and rec["card_sha"] != text_sha(c["path"]):
                state, detail = "edited", "card text changed since stamp; re-judge the changed lines"
            else:
                state, detail = "ok", f"v{rec.get('version', 0):03d} stamped {rec['stamped']}, judge: {rec.get('judge', '?')}"
        problems += state != "ok"
        print(f"{m:24} {state:10} {detail}")
    sysrec = st.stamps.get("system")
    shape = st.system_shape(cards)
    if (st.dir / SYSTEM).exists():
        if sysrec is None:
            print(f"{'_system':24} unstamped  stamp after the module cards")
            problems += 1
        elif sysrec["shape"] != shape:
            print(f"{'_system':24} stale      modules or depends_on changed since {sysrec['stamped']}")
            problems += 1
        elif sysrec.get("card_sha") and sysrec["card_sha"] != text_sha(st.dir / SYSTEM):
            print(f"{'_system':24} edited     card text changed since stamp")
            problems += 1
    owners = {}
    for m, c in cards.items():
        for f in st.card_files(c):
            owners.setdefault(f, []).append(m)
    src, ign = matcher(st.config["source_globs"]), matcher(st.config["ignore_globs"])
    uncovered = [f for f in st.files if src(f) and not ign(f) and f not in owners]
    overlap = {f: ms for f, ms in owners.items() if len(ms) > 1}
    if uncovered:
        problems += 1
        print(f"\nuncovered source files ({len(uncovered)}) — add to a card's paths or to ignore_globs:")
        for f in uncovered[:40]:
            print("  " + f)
        if len(uncovered) > 40:
            print(f"  ... {len(uncovered) - 40} more")
    if overlap:
        problems += 1
        print(f"\nfiles owned by more than one card ({len(overlap)}) — narrow paths or add exclude:")
        for f, ms in list(overlap.items())[:20]:
            print(f"  {f}: {', '.join(ms)}")
    if not problems:
        print("\nall cards current")
    return 1 if (problems and args.strict) else 0


def cmd_diff(st, args):
    cards = st.cards()
    if args.module not in cards:
        sys.exit(f"unknown module {args.module}; known: {', '.join(cards)}")
    c = cards[args.module]
    rec = st.stamps["cards"].get(args.module)
    now = st.fingerprint(c)
    if rec is None:
        print(f"{args.module} was never stamped; document all {len(now)} files:")
        for f in sorted(now):
            print("  " + f)
        return 0
    ch, ad, rm = compare(rec["files"], now)
    for label, fs in (("changed", ch), ("added", ad), ("removed", rm)):
        for f in fs:
            print(f"{label:8} {f}")
    if not (ch or ad or rm):
        print("no source change since stamp")
        return 0
    commit = rec.get("commit")
    if commit and git(st.root, "cat-file", "-e", commit) is not None:
        stat = git(st.root, "diff", "--stat", commit, "--", *(ch + rm + ad))
        if stat:
            print(f"\ngit diff --stat {commit[:10]} (stamp commit; includes uncommitted work):\n" + stat.rstrip())
        print(f"\nfull diff: git diff {commit[:10]} -- {' '.join(ch + ad + rm)}")
    return 0


def lint_diagrams(st, text, render, max_nodes=None):
    errs, warns = [], []
    mmdc = shutil.which(st.config["mmdc"]) if render else None
    if render and not mmdc:
        warns.append(f"--render: '{st.config['mmdc']}' not found (npm i -g @mermaid-js/mermaid-cli); structural lint only")
    for start, body in judge.mermaid_blocks(text):
        e, w = judge.lint_mermaid(start, body, max_nodes or st.config["max_diagram_nodes"])
        errs += e
        warns += w
        if mmdc and not e:
            bad = judge.render_check(body, mmdc)
            if bad:
                errs.append(f"L{start}: mermaid does not parse: {bad}")
    return errs, warns


def check_card(st, m, c, known):
    errs, warns = [], []
    meta, sections = c["meta"], c["sections"]
    if not as_list(meta.get("paths")):
        errs.append("front matter has no paths")
    elif not st.card_files(c):
        errs.append("paths match no file")
    for s in REQUIRED:
        if s not in sections:
            errs.append(f"missing section ## {s}")
        elif not sections[s]:
            errs.append(f"empty section ## {s} (write 'None.' if that is the fact)")
    for d in as_list(meta.get("depends_on")):
        if d not in known:
            errs.append(f"depends_on names unknown module '{d}'")
    text = c["path"].read_text(encoding="utf-8")
    tbd = [str(i) for i, l in enumerate(text.splitlines(), 1) if "TBD" in l]
    if tbd:
        errs.append(f"unfilled template text (TBD) on lines {', '.join(tbd[:10])}"
                    + (" ..." if len(tbd) > 10 else ""))
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        for w in VAGUE:
            if re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", low):
                warns.append(f"line {i}: vague word '{w}'")
    for m2 in ANCHOR.finditer(text):
        path, symbol, line = m2.groups()
        if "/" not in path and not (st.root / path).exists():
            continue  # a file name in prose, not an anchor
        target = st.root / path
        if not target.is_file():
            errs.append(f"anchor `{m2.group(1)}`: file not found")
            continue
        if symbol:
            src = target.read_text(encoding="utf-8", errors="replace")
            if not re.search(r"\b" + re.escape(symbol.split(".")[-1]) + r"\b", src):
                errs.append(f"anchor `{path}::{symbol}`: symbol not found in file")
        elif line:
            n = len(target.read_text(encoding="utf-8", errors="replace").splitlines())
            if int(line) > n:
                errs.append(f"anchor `{path}:{line}`: file has {n} lines")
            else:
                warns.append(f"anchor `{path}:{line}`: line anchors drift; prefer path::symbol")
    rows = [r for r in sections.get("Interface", "").splitlines()
            if r.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", r)][1:]
    for r in rows:
        if not ANCHOR.search(r):
            warns.append(f"Interface row without anchor: {r[:60]}")
    de, dw = lint_diagrams(st, text, getattr(st, "render", False))
    errs += de
    warns += dw
    # signatures: card parameters must exist in the definition
    for r in rows:
        cells = [x.strip() for x in r.strip().strip("|").split("|")]
        a = ANCHOR.search(cells[0]) if cells else None
        if not a or not a.group(2) or len(cells) < 2 or a.group(1).rsplit(".", 1)[-1] not in SIG_EXT:
            continue
        want = judge.card_params(cells[1].strip("`"))
        have = judge.def_params(st.root, a.group(1), a.group(2))
        if want is None or have is None:
            continue
        for name in want:
            if not re.search(r"\b" + re.escape(name) + r"\b", have):
                errs.append(f"signature of `{a.group(2)}`: parameter '{name}' not in the definition")
    # dependencies: real imports vs depends_on, and Uses / Used by agreement
    owners = {}
    for m2_, c2 in known.items():
        for f in st.card_files(c2):
            owners.setdefault(f, m2_)
    fileset = set(st.files)
    found = {}
    for f in st.card_files(c):
        for g in judge.imports(st.root, f, fileset):
            o = owners.get(g)
            if o and o != m:
                found.setdefault(o, f"{f} imports {g}")
    declared = set(as_list(meta.get("depends_on")))
    for o, why in sorted(found.items()):
        if o not in declared:
            errs.append(f"code depends on '{o}' but depends_on omits it ({why})")
    for d in sorted(declared - set(found)):
        if d in known:
            warns.append(f"depends_on lists '{d}' but no static import was found (fine for RPC/plugins; else remove)")
    for d in declared:
        if d in known and not re.search(r"\b" + re.escape(m) + r"\b", known[d]["sections"].get("Dependencies", "")):
            warns.append(f"'{d}' card's Dependencies does not list '{m}' under Used by")
    cap = st.config["max_card_lines"]
    if c["lines"] > 2 * cap:
        errs.append(f"{c['lines']} lines, over twice the {cap}-line budget: split the module")
    elif c["lines"] > cap:
        warns.append(f"{c['lines']} lines, over the {cap}-line budget: cut or split")
    return errs, warns


def cmd_check(st, args):
    st.render = args.render
    cards = st.cards()
    pick = [m for m in args.modules if m != "_system"] or ([] if args.modules else list(cards))
    total = 0
    for m in pick:
        if m not in cards:
            print(f"{m}: unknown module")
            total += 1
            continue
        errs, warns = check_card(st, m, cards[m], cards)
        total += len(errs)
        status = "FAIL" if errs else ("warn" if warns else "ok")
        print(f"{m}: {status}")
        for e in errs:
            print("  error  " + e)
        for w in warns:
            print("  warn   " + w)
    sysp = st.dir / SYSTEM
    if (not args.modules or "_system" in args.modules) and sysp.exists():
        stext = sysp.read_text(encoding="utf-8")
        tbd = [i for i, l in enumerate(stext.splitlines(), 1) if "TBD" in l]
        errs, warns = lint_diagrams(st, stext, args.render, st.config["max_diagram_nodes"] + 6)
        if tbd:
            errs.insert(0, f"unfilled template text (TBD) on lines {', '.join(map(str, tbd[:10]))}")
        print(f"_system: {'FAIL' if errs else ('warn' if warns else 'ok')}")
        for e in errs:
            print("  error  " + e)
        for w in warns:
            print("  warn   " + w)
        total += len(errs)
    return 1 if total else 0


def versions(st, module):
    h = st.dir / "history" / module
    return sorted(d for d in h.iterdir() if d.is_dir() and re.match(r"v\d{3}_", d.name)) if h.is_dir() else []


def write_version(st, m, path, old, new, note, owned):
    """Freeze the card as history/<m>/vNNN_<date>_<commit>/ with its judge evidence and
    a changelog entry. Returns the version number."""
    prev = versions(st, m)
    n = int(prev[-1].name[1:4]) + 1 if prev else 1
    c7 = (new["commit"] or "nogit")[:7]
    dirty = bool(owned) and bool((git(st.root, "status", "--porcelain", "--", *owned) or "").strip())
    code = c7 + ("-dirty" if dirty else "")
    set_managed(path, {"version": n, "updated": new["stamped"], "code_commit": code})
    d = st.dir / "history" / m / f"v{n:03d}_{new['stamped']}_{code}"
    forced = new["judge"] == "forced"
    (d / "judge").mkdir(parents=True, exist_ok=True) if not forced else d.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, d / "card.md")
    run = {} if forced else (load_prep(st, m) or {})
    if not forced:
        for f in (st.dir / "verify" / m).glob("s*.report.md"):
            shutil.copy(f, d / "judge" / f.name)
        if run:
            shutil.copy(st.dir / "verify" / m / "run.json", d / "judge" / "verdict.json")
    secs_now = parse_card(path)[1]
    secs_old = parse_card(prev[-1] / "card.md")[1] if prev else {}
    changed = [s for s in secs_now if secs_old.get(s) != secs_now[s]]
    removed = [s for s in secs_old if s not in secs_now]
    if old and "files" in old:
        ch, ad, rm = compare(old["files"], new["files"])
        code_line = ", ".join([f"~{f}" for f in ch] + [f"+{f}" for f in ad] + [f"-{f}" for f in rm]) or "none"
    else:
        code_line = "first version" if not old else "n/a"
    res = run.get("results") or []
    canaries = [r["canary"] for r in res if r["canary"] is not None]
    if forced:
        judge_line = "FORCED: no passing verdict"
    else:
        judge_line = (f"{new['judge']}, tier {run.get('tier', '?')}, {len(res)} judge(s), canaries "
                      f"{sum(canaries)}/{len(canaries)} caught, {len(run.get('findings', []))} findings "
                      f"({len(run.get('waived', {}))} waived)")
    rel = f"{d.name}/card.md"
    evidence = "" if forced else f" · evidence: [{d.name}/judge/]({d.name}/judge/)"
    entry = "\n".join([
        f"## v{n:03d} — {new['stamped']} — code {code}",
        "",
        f"- Note: {note or '—'}",
        f"- Card sections changed: {', '.join(changed) or 'none'}" + (f"; removed: {', '.join(removed)}" if removed else ""),
        f"- Code changed since previous version: {code_line}",
        f"- Judge: {judge_line}",
        f"- Snapshot: [{rel}]({rel}){evidence}",
        "", ""])
    log = st.dir / "history" / m / "CHANGELOG.md"
    head = (f"# {m}: card history\n\nNewest first. Each version folder holds the card as stamped "
            "and the judge reports that passed it.\n\n")
    body = log.read_text(encoding="utf-8")[len(head):] if log.exists() else ""
    log.write_text(head + entry + body, encoding="utf-8")
    glog = st.dir / "CHANGELOG.md"
    rows = glog.read_text(encoding="utf-8")[len(GLOG_HEAD):] if glog.exists() else ""
    row = (f"| {new['stamped']} | [{m}](history/{m}/CHANGELOG.md) | [v{n:03d}](history/{m}/{rel}) | "
           f"`{code}` | {(note or '—').replace('|', '/')} |\n")
    glog.write_text(GLOG_HEAD + row + rows, encoding="utf-8")
    return n


GLOG_HEAD = ("# Code cards changelog\n\nNewest first. One row per stamped card version or release.\n\n"
             "| Date | Card | Version | Code | Note |\n|---|---|---|---|---|\n")


def cmd_history(st, args):
    if not args.module:
        g = st.dir / "CHANGELOG.md"
        print(g.read_text(encoding="utf-8") if g.exists() else "no versions yet")
        return 0
    vs = versions(st, args.module)
    if not vs:
        sys.exit(f"no versions of {args.module}")
    if not args.diff:
        for d in vs:
            vf = d / "judge" / "verdict.json"
            ver = json.loads(vf.read_text(encoding="utf-8")) if vf.exists() else {}
            print(f"{d.name:40} judge {ver.get('judge', 'forced'):9} tier {ver.get('tier', '-')}")
        print(f"\nchangelog: {(st.dir / 'history' / args.module / 'CHANGELOG.md').relative_to(st.root)}")
        return 0

    def pick(tag):
        if tag in ("current", "now"):
            return st.card_path(args.module, st.cards())
        want = tag if tag.startswith("v") else f"v{int(tag):03d}"
        hit = [d for d in vs if d.name.startswith(want)]
        if not hit:
            sys.exit(f"no version {tag}; have {', '.join(d.name[:4] for d in vs)}")
        return hit[0] / "card.md"
    a = pick(args.diff[0])
    b = pick(args.diff[1] if len(args.diff) > 1 else "current")
    diff = difflib.unified_diff(a.read_text(encoding="utf-8").splitlines(), b.read_text(encoding="utf-8").splitlines(),
                                str(a.relative_to(st.root)), str(b.relative_to(st.root)), lineterm="")
    print("\n".join(diff) or "identical")
    return 0


def cmd_release(st, args):
    cards = st.cards()
    out = st.dir / "releases" / args.name
    if out.exists():
        sys.exit(f"{out.relative_to(st.root)} exists; releases are immutable, pick a new name")
    def problem(m):
        rec = st.stamps["cards"].get(m)
        if not rec:
            return "UNSTAMPED"
        if rec["files"] != st.fingerprint(cards[m]):
            return "STALE"
        return None if verified(st, m, cards)["ok"] else "NOT JUDGED"
    flags = {m: problem(m) for m in cards}
    bad = [m for m, f in flags.items() if f]
    if bad and not args.force:
        sys.exit(f"not current: {', '.join(bad)}; update and stamp them first, or --force")
    out.mkdir(parents=True)
    commit = ((git(st.root, "rev-parse", "HEAD") or "").strip() or "nogit")[:7]
    today = datetime.date.today().isoformat()

    def row(name, path, judge_kind, flag):
        meta = parse_card(path)[0]
        v = int(meta.get("version") or 0) if str(meta.get("version") or "0").isdigit() else 0
        return (f"| [{name}]({path.name}) | v{v:03d} | {meta.get('updated', '-')} | "
                f"`{meta.get('code_commit', '-')}` | {judge_kind} | {flag} |")
    rows = []
    for m, c in sorted(cards.items()):
        shutil.copy(c["path"], out / c["path"].name)
        rows.append(row(m, c["path"], st.stamps["cards"].get(m, {}).get("judge", "-"),
                        flags[m] or ""))
    if (st.dir / SYSTEM).exists():
        shutil.copy(st.dir / SYSTEM, out / SYSTEM)
        rows.append(row("_system", st.dir / SYSTEM, st.stamps.get("system", {}).get("judge", "-"), ""))
    (out / "MANIFEST.md").write_text(
        f"# Release {args.name}\n\n- Frozen: {today}\n- Code at release: `{commit}`\n- Note: {args.note or '—'}\n\n"
        "| Card | Version | Updated | Code checked | Judge | |\n|---|---|---|---|---|---|\n"
        + "\n".join(rows) + "\n", encoding="utf-8")
    glog = st.dir / "CHANGELOG.md"
    text = glog.read_text(encoding="utf-8") if glog.exists() else GLOG_HEAD
    rel_row = (f"| {today} | **release** | [{args.name}](releases/{args.name}/MANIFEST.md) | `{commit}` | "
               f"{(args.note or '—').replace('|', '/')} |\n")
    glog.write_text(GLOG_HEAD + rel_row + text[len(GLOG_HEAD):], encoding="utf-8")
    print(f"froze {len(rows)} cards into {out.relative_to(st.root)}/ (MANIFEST.md)")
    return 0


def cmd_stamp(st, args):
    cards = st.cards()
    pick = list(cards) if args.all else args.modules
    commit = (git(st.root, "rev-parse", "HEAD") or "").strip() or None
    today = datetime.date.today().isoformat()
    for m in pick:
        if m == "_system":
            continue
        if m not in cards:
            sys.exit(f"unknown module {m}")
        errs, _ = check_card(st, m, cards[m], cards)
        if errs and not args.force:
            sys.exit(f"{m}: check fails ({len(errs)} errors); fix, or --force")
        v = verified(st, m, cards)
        if not v["ok"] and not args.force:
            sys.exit(f"{m}: {v['why']}; run `judge {m}` and `verdict {m}`, or --force with the user's OK")
        old = st.stamps["cards"].get(m)
        new = {"stamped": today, "commit": commit, "files": st.fingerprint(cards[m]),
               "card_sha": text_sha(cards[m]["path"]),
               "judge": v.get("judge", "forced") if v["ok"] else "forced"}
        new["version"] = write_version(st, m, cards[m]["path"], old, new, args.note, list(new["files"]))
        st.stamps["cards"][m] = new
        print(f"stamped {m} v{new['version']:03d} ({len(new['files'])} files, judge: {new['judge']})")
    if args.all or "_system" in pick:
        v = verified(st, "_system", cards)
        if not v["ok"] and not args.force:
            sys.exit(f"_system: {v['why']}; run `judge _system` and `verdict _system`, or --force")
        old = st.stamps.get("system")
        new = {"stamped": today, "commit": commit, "shape": st.system_shape(cards),
               "card_sha": text_sha(st.dir / SYSTEM),
               "judge": v.get("judge", "forced") if v["ok"] else "forced"}
        new["version"] = write_version(st, "_system", st.dir / SYSTEM, old, new, args.note, [])
        st.stamps["system"] = new
        print(f"stamped _system v{new['version']:03d} (judge: {new['judge']})")
    for m in list(st.stamps["cards"]):
        if m not in cards:
            del st.stamps["cards"][m]
            print(f"dropped stamp of deleted card {m}")
    st.save_stamps()
    return 0


MANAGED = ("version", "updated", "code_commit")
MANAGED_LINE = re.compile(r"^(?:%s):.*\n" % "|".join(MANAGED), re.M)


def split_fm(text):
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[:end + 1], text[end + 1:]
    return "", text


def text_sha(path):
    """Sha of a card's text, ignoring the version fields stamp writes."""
    if not path.exists():
        return None
    fm, body = split_fm(path.read_text(encoding="utf-8"))
    return hashlib.sha256((MANAGED_LINE.sub("", fm) + body).encode()).hexdigest()[:16]


def set_managed(path, fields):
    text = path.read_text(encoding="utf-8")
    fm, body = split_fm(text)
    if not fm:
        fm, body = "---\n", "---\n\n" + body
    for k, v in fields.items():
        line = f"{k}: {v}\n"
        fm, n = re.subn(r"^%s:.*\n" % k, line, fm, flags=re.M)
        if not n:
            fm += line
    path.write_text(fm + body, encoding="utf-8")


def vdir(st, module):
    d = st.dir / "verify" / module
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_prep(st, module):
    p = st.dir / "verify" / module / "run.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def verified(st, module, cards):
    prep = load_prep(st, module)
    if not prep or not prep.get("passed"):
        return {"ok": False, "why": "no passing judge verdict"}
    if prep["card_sha"] != text_sha(st.card_path(module, cards)):
        return {"ok": False, "why": "card edited after its verdict"}
    if prep["files_hash"] != st.files_hash(module, cards):
        return {"ok": False, "why": "code changed after its verdict"}
    return {"ok": True, "judge": prep["judge"]}


def cmd_judge(st, args):
    cards, m = st.cards(), args.module
    if m != "_system" and m not in cards:
        sys.exit(f"unknown module {m}; known: {', '.join(cards)}, _system")
    path = st.card_path(m, cards)
    if not path.exists():
        sys.exit(f"{path} not found")
    vd = vdir(st, m)
    text = path.read_text(encoding="utf-8")
    claims = judge.claim_lines(text)
    fh = st.files_hash(m, cards)
    prev = load_prep(st, m)
    judged = vd / "judged.md"
    carried = set()
    if prev and not args.full and prev.get("files_hash") == fh and judged.exists():
        carried = judge.carried_lines(judged.read_text(encoding="utf-8"), text, set(prev.get("ok_lines", [])))
    required = [(l, s) for l, s in claims if l not in carried]
    if m == "_system":
        files = [str(c["path"].relative_to(st.root)) for c in cards.values()]
        tier, metrics = "medium", {"cards": len(cards)}
    else:
        files = st.card_files(cards[m])
        tier, metrics = judge.complexity(st.root, files)
    if not required:
        if not prev:
            sys.exit("card has no claim lines")
        prev.update(passed=True, card_sha=text_sha(path))
        (vd / "run.json").write_text(json.dumps(prev, indent=2) + "\n", encoding="utf-8")
        print(f"{m}: every claim line is unchanged and was judged OK with the same code; verdict carried")
        return 0
    if args.self_judge:
        shards = [[l for l, _ in required]]
    elif args.shards:
        n = max(1, args.shards)
        shards = [s for s in ([l for l, _ in required][i::n] for i in range(n)) if s]
    else:
        shards = judge.plan_shards(tier, metrics, required)
    full = not carried
    probe_n = judge.PROBES[tier] if full else (2 if tier == "complex" else 0)
    sections = dict(required)
    template = (SKILL / "references" / "verifier-prompt.md").read_text(encoding="utf-8")
    prep_id = hashlib.sha256(os.urandom(16)).hexdigest()[:12]
    rec = {"prep": prep_id, "module": m, "created": datetime.datetime.now().isoformat(timespec="seconds"),
           "card_sha": text_sha(path), "files_hash": fh, "tier": tier, "metrics": metrics,
           "judge": "self" if args.self_judge else "subagent", "probe_n": probe_n,
           "carried": sorted(carried), "passed": False, "shards": []}
    print(f"{m}: tier {tier} {metrics}")
    print(f"claim lines {len(claims)}: {len(required)} to judge, {len(carried)} carried from the last verdict")
    for k, lines in enumerate(shards, 1):
        body, canary = (text, None) if args.self_judge else judge.plant(text, lines)
        inp, report, prompt = (vd / f"s{k}.{x}.md" for x in ("input", "report", "prompt"))
        inp.write_text(body, encoding="utf-8")
        if report.exists():
            report.unlink()
        notes = []
        if len(shards) > 1:
            notes.append(f"You are judge {k} of {len(shards)}; other judges cover the other lines independently.")
        if carried:
            notes.append(f"{len(carried)} unlisted lines were judged OK earlier and are unchanged; "
                         "flag one only if it contradicts a line you judge.")
        if m == "_system":
            notes.append("This is the SYSTEM card. Check every flow step and cross-module rule against the "
                         "module cards listed above AND the code they own. Flag contradictions between cards "
                         "(Uses vs Used by, names spelled differently, a flow step no card describes).")
        has_flow = any(sections[l].startswith("Flow") for l in lines)
        trace_rule = ("Required for this module: for every Flow step on your lines, write the call chain you "
                      "followed, e.g. `entry (path::sym) -> callee (path::sym) -> ...`."
                      if tier == "complex" and has_flow else
                      'Optional: the call chains you followed, or "None."')
        prompt.write_text(template.format(
            root=st.root, input=inp, skill=SKILL, module=m, shard=f"{k}/{len(shards)}", prep=prep_id,
            files="\n".join(f"  - {f}" for f in files) + "\n  (and anything they call into)",
            lines=", ".join(f"L{l}" for l in lines), scope_note="\n".join(notes),
            verify_dir=vd, report=report, probe_n=probe_n, trace_rule=trace_rule,
            depth=judge.DEPTH_CHECKLIST if tier == "complex" else ""), encoding="utf-8")
        rec["shards"].append({"k": k, "lines": lines, "canary": canary, "trace": tier == "complex" and has_flow,
                              "input": str(inp.relative_to(st.root)), "report": str(report.relative_to(st.root)),
                              "prompt": str(prompt.relative_to(st.root))})
        print(f"  judge {k}: {len(lines)} lines -> prompt {prompt.relative_to(st.root)}")
    (vd / "run.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    if args.self_judge:
        print("self-judging: re-read the card and code from disk, follow the prompt, write the report; "
              "no canary is planted, and the stamp records judge: self")
    else:
        print(f"spawn {len(shards)} fresh judge agent(s), one per prompt file, in parallel; send the prompt "
              f"file's content and nothing else; then run: verdict {m}")
    return 0


def cmd_verdict(st, args):
    cards, m = st.cards(), args.module
    rec = load_prep(st, m)
    if not rec:
        sys.exit(f"no judge run for {m}; run `judge {m}` first")
    path = st.card_path(m, cards)
    if rec["card_sha"] != text_sha(path):
        sys.exit("the card changed while it was being judged; run `judge` again")
    if rec["files_hash"] != st.files_hash(m, cards):
        sys.exit("the code changed while the card was being judged; run `judge` again")
    waivers = {}
    for w in args.waive:
        k, _, reason = w.partition("=")
        if not reason.strip():
            sys.exit(f"--waive {w}: give a reason, e.g. s1:M2=\"private helper\"")
        waivers[k.strip()] = reason.strip()
    findings, hard, ok_lines, results = [], [], set(rec["carried"]), []
    for sh in rec["shards"]:
        k, lines, canary = sh["k"], set(sh["lines"]), sh["canary"]
        rp = st.root / sh["report"]
        if not rp.exists():
            hard.append(f"judge {k}: no report at {sh['report']}")
            continue
        r = judge.parse_report(rp.read_text(encoding="utf-8"))
        if r["prep"] != rec["prep"]:
            hard.append(f"judge {k}: report is for prep {r['prep']}, not {rec['prep']} (stale report)")
            continue
        covered = {l for c in r["claims"] for l in c["lines"]}
        gaps = sorted(lines - covered)
        if gaps:
            hard.append(f"judge {k}: no verdict for lines {', '.join('L%d' % l for l in gaps)}")
        caught = None
        if canary:
            caught = any(c["verdict"] == "WRONG" and canary["line"] in c["lines"] for c in r["claims"])
            if not caught:
                hard.append(f"judge {k}: missed the planted error on L{canary['line']} "
                            f"(\"{canary['mutated'].strip()[:70]}\"); report rejected, run a fresh judge")
        line_ok = {}
        for c in r["claims"]:
            for l in c["lines"]:
                if canary and l == canary["line"]:
                    continue
                fid = f"s{k}:L{l}"
                good = c["verdict"] == "OK"
                if good and judge.evidence_locations(c["evidence"]) == 0:
                    findings.append((fid, "OK without a code location", c["claim"]))
                    good = False
                elif good and rec["tier"] == "complex" and c["section"].lower().startswith("failure") \
                        and judge.evidence_locations(c["evidence"]) < 2:
                    findings.append((fid, "failure mode not traced to raise AND handler", c["claim"]))
                    good = False
                elif not good:
                    findings.append((fid, c["verdict"], f"{c['claim']} — {c['evidence']}"))
                line_ok[l] = line_ok.get(l, True) and good
        for mi in r["missing"]:
            findings.append((f"s{k}:{mi['id']}", "MISSING", mi["text"]))
        if len(r["probes"]) < rec["probe_n"]:
            findings.append((f"s{k}:probe", "probe incomplete", f"{len(r['probes'])}/{rec['probe_n']} questions"))
        for pr in r["probes"]:
            if canary and canary["line"] in pr["card_lines"]:
                continue  # answered from the planted line
            if pr["verdict"] != "OK":
                findings.append((f"s{k}:{pr['id']}", pr["verdict"] or "no verdict", pr["question"]))
        if sh.get("trace"):
            if len(r["trace"].strip()) < 20 or r["trace"].strip().lower().startswith("none"):
                findings.append((f"s{k}:trace", "trace missing", "complex module: call chains required"))
        results.append({"k": k, "claims": len(r["claims"]), "canary": None if canary is None else bool(caught)})
        shard_rejected = canary and not caught
        if not shard_rejected:
            ok_lines |= {l for l, g in line_ok.items() if g}
        print(f"judge {k}: {len(r['claims'])} claims on {len(covered & lines)}/{len(lines)} lines; "
              f"canary {'caught' if caught else 'MISSED' if canary else 'none'}; {r['verdict_line'] or 'no VERDICT line'}")
    open_ = [f for f in findings if f[0] not in waivers]
    if findings:
        print("\nfindings:")
        for fid, kind, text in findings:
            tag = f"waived: {waivers[fid]}" if fid in waivers else "open"
            print(f"  {fid:12} {kind:28} {text[:90]}  [{tag}]")
    for h in hard:
        print("  BLOCKED  " + h)
    rec["passed"] = not hard and not open_
    rec["ok_lines"] = sorted(ok_lines)
    rec["findings"] = [list(f) for f in findings]
    rec["waived"] = waivers
    rec["results"] = results
    rec["verdict_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    (vdir(st, m) / "run.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    (vdir(st, m) / "judged.md").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    if rec["passed"]:
        print(f"\n{m}: PASS (judge: {rec['judge']}, tier {rec['tier']}); stamp it after the user approves")
        return 0
    print(f"\n{m}: FAIL — fix the card (or the code, with the user), then `judge {m}` again; "
          "unchanged lines judged OK carry over")
    return 1


def first_sentence(text):
    text = " ".join(l.strip() for l in text.splitlines() if l.strip() and not l.startswith(("|", "```", "<!--")))
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return (m.group(1) if m else text).replace("|", "\\|")


def build_block(st, readme_dir):
    cards = st.cards()
    lines = [START, NOTICE.format(cards=st.rel), "", f"## {st.config['readme_heading']}", ""]
    sysp = st.dir / SYSTEM
    sys_sections = parse_card(sysp)[1] if sysp.exists() else {}
    if "Summary" in st.config["readme_sections"] and sys_sections.get("Summary"):
        lines += [sys_sections["Summary"], ""]
    edges = [(m, d) for m, c in cards.items() for d in as_list(c["meta"].get("depends_on")) if d in cards]
    if edges:
        ids = {m: "m" + str(i) for i, m in enumerate(cards)}
        lines += ["```mermaid", "flowchart LR"]
        lines += [f'  {ids[m]}["{m}"]' for m in cards]
        lines += [f"  {ids[a]} --> {ids[b]}" for a, b in edges]
        lines += ["```", "", "Arrows point from a module to the modules it calls.", ""]
    order = sorted(cards, key=lambda m: (int(cards[m]["meta"].get("order") or 999), m))
    stamped = [r for r in st.stamps["cards"].values() if r.get("version")]
    if stamped:
        last = max(stamped, key=lambda r: r["stamped"])
        lines += [f"<sub>Cards checked against the code up to {last['stamped']} (commit "
                  f"`{(last.get('commit') or 'nogit')[:7]}`). History: [{st.rel}/CHANGELOG.md]"
                  f"({os.path.relpath(st.dir / 'CHANGELOG.md', readme_dir)}).</sub>", ""]
    lines += ["| Module | Purpose | Entry points | Version |", "|---|---|---|---|"]
    for m in order:
        c = cards[m]
        link = os.path.relpath(c["path"], readme_dir).replace(os.sep, "/")
        entries = as_list(c["meta"].get("entry_points"))
        if not entries:
            for r in c["sections"].get("Interface", "").splitlines()[2:5]:
                a = ANCHOR.search(r)
                if a:
                    entries.append(a.group(2) or a.group(1))
        ent = ", ".join(f"`{e}`" for e in entries[:3])
        ver = c["meta"].get("version")
        verc = f"v{int(ver):03d} · {c['meta'].get('updated', '')}" if ver and str(ver).isdigit() and int(ver) else "—"
        lines.append(f"| [{m}]({link}) | {first_sentence(c['sections'].get('Purpose', ''))} | {ent} | {verc} |")
    lines.append("")
    for name in st.config["readme_sections"]:
        if name == "Summary" or not sys_sections.get(name):
            continue
        body = re.sub(r"^(#{3,5}) ", lambda x: "#" + x.group(1) + " ", sys_sections[name], flags=re.M)
        lines += [f"### {name}", "", body, ""]
    lines.append(END)
    return "\n".join(lines) + "\n"


def cmd_readme(st, args):
    readme = st.root / (args.readme or st.config["readme"])
    block = build_block(st, readme.parent)
    old = readme.read_text(encoding="utf-8") if readme.exists() else ""
    if START in old and END in old:
        a, b = old.index(START), old.index(END) + len(END)
        tail = old[b:]
        new = old[:a] + block.rstrip("\n") + (tail if tail.startswith("\n") else "\n" + tail)
    elif args.insert_after:
        ls = old.splitlines(keepends=True)
        idx = next((i for i, l in enumerate(ls) if l.strip().lstrip("#").strip() == args.insert_after
                    and l.startswith("#")), None)
        if idx is None:
            sys.exit(f"heading '{args.insert_after}' not found in {readme.name}")
        level = len(ls[idx]) - len(ls[idx].lstrip("#"))
        j = next((k for k in range(idx + 1, len(ls)) if re.match(r"^#{1,%d} " % level, ls[k])), len(ls))
        new = "".join(ls[:j]).rstrip("\n") + "\n\n" + block + ("\n" + "".join(ls[j:]) if j < len(ls) else "")
    else:
        new = (old.rstrip("\n") + "\n\n" if old else "") + block
    if args.check:
        if new == old:
            print(f"{readme.name}: generated section is current")
            return 0
        diff = difflib.unified_diff(old.splitlines(), new.splitlines(), "README (now)", "README (from cards)", lineterm="", n=1)
        print("\n".join(list(diff)[:60]))
        return 1
    readme.write_text(new, encoding="utf-8")
    print(f"wrote generated section into {readme.relative_to(st.root)}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=None, help="project root (default: git toplevel or cwd)")
    ap.add_argument("--cards", default="docs/cards", help="card directory relative to root")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("--write", action="store_true")
    p = sub.add_parser("status"); p.add_argument("--strict", action="store_true", help="exit 1 on any problem")
    p = sub.add_parser("diff"); p.add_argument("module")
    p = sub.add_parser("check"); p.add_argument("modules", nargs="*")
    p.add_argument("--render", action="store_true", help="also parse every mermaid block with mermaid-cli (mmdc)")
    p = sub.add_parser("graph"); p.add_argument("module", nargs="?")
    p = sub.add_parser("stamp"); p.add_argument("modules", nargs="*")
    p.add_argument("--all", action="store_true"); p.add_argument("--force", action="store_true")
    p.add_argument("--note", help="why this version: shown in the changelogs")
    p = sub.add_parser("history"); p.add_argument("module", nargs="?")
    p.add_argument("--diff", nargs="+", metavar="VERSION", help="v001 [v003|current]")
    p = sub.add_parser("release"); p.add_argument("name"); p.add_argument("--note")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("judge"); p.add_argument("module")
    p.add_argument("--self", dest="self_judge", action="store_true",
                   help="no subagent available: you judge it yourself (no canary; recorded as self)")
    p.add_argument("--shards", type=int, help="override the number of independent judges")
    p.add_argument("--full", action="store_true", help="judge every line, ignore lines carried from the last verdict")
    p = sub.add_parser("verdict"); p.add_argument("module")
    p.add_argument("--waive", action="append", default=[], metavar='ID="reason"',
                   help="accept one finding (e.g. s1:M2=\"private helper\"); WRONG only with the user's OK")
    p = sub.add_parser("readme"); p.add_argument("--readme")
    p.add_argument("--insert-after", metavar="HEADING"); p.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = args.root or (git(Path.cwd(), "rev-parse", "--show-toplevel") or "").strip() or os.getcwd()
    st = Store(root, args.cards)
    if args.cmd == "stamp" and not (args.modules or args.all):
        sys.exit("name modules to stamp, or --all")
    sys.exit(globals()["cmd_" + args.cmd](st, args) or 0)


if __name__ == "__main__":
    main()
