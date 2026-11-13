#!/usr/bin/env python3
"""Workspace helper for ub-sched-research. Standard library only.

  init    create ub-sched/ with the ontology, engine ontologies and templates
  check   validate card front matter against ontology.md and engines.md
  matrix  write matrix.md: per-source coverage, concept gaps, crosswalk gaps
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TERM_ROW = re.compile(r"^\|\s*`([A-Za-z][\w:]*)`\s*\|")
ENGINE_HEAD = re.compile(r"^##\s+\d+\.\s+(\w+)\s+ontology\b", re.I)
LAYER_HEAD = re.compile(r"^###\s+(L[1-5])\b")

ENUMS = {
    "type": {"paper", "oss", "code", "doc", "blog"},
    "evidence": {"peer-reviewed", "working-code", "self-reported", "claim-only"},
    "pattern": {"A", "B", "C", "n/a"},
    "locality_model": {"none", "node-local", "hierarchical", "numa-aware",
                       "network-aware", "disaggregated", "composable"},
    "separates": {"yes", "partial", "no"},
    "ub_transfer": {"holds", "partial", "breaks", "unknown"},
    "visibility": {"public", "internal"},
}
LIST_ENUMS = {"level": {"cluster", "application", "task"},
              "layers": {"L1", "L2", "L3", "L4", "L5"}}
REQUIRED = ["source_id", "type", "evidence", "layers", "concepts",
            "locality_model", "separates", "ub_transfer"]


def parse_ontology(path):
    """Return ({class: layer}, {relation})."""
    classes, relations, layer, section = {}, set(), None, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = "relations" if "Relations" in line else "classes" if "Classes" in line else None
            layer = None
            continue
        m = LAYER_HEAD.match(line)
        if m:
            layer = m.group(1)
            continue
        m = TERM_ROW.match(line)
        if not m:
            continue
        if section == "classes" and layer:
            classes[m.group(1)] = layer
        elif section == "relations":
            relations.add(m.group(1))
    return classes, relations


def parse_engines(path):
    """Return ({'Engine:Term'}, [(engine_term, ub_concept, fidelity)])."""
    terms, crosswalk, engine, in_classes, in_cross = set(), [], None, False, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            m = ENGINE_HEAD.match(line)
            engine = m.group(1) if m else None
            in_cross = "Crosswalk" in line
            in_classes = False
            continue
        if line.startswith("### "):
            in_classes = engine is not None and "Classes" in line
            continue
        if in_classes:
            m = TERM_ROW.match(line)
            if m:
                terms.add(f"{engine}:{m.group(1)}")
        elif in_cross and line.startswith("|") and "`" in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3:
                crosswalk.append((cells[0].strip("`"), cells[1], cells[2]))
    return terms, crosswalk


def parse_front_matter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
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
    return data


def load(ws):
    onto, eng = ws / "ontology.md", ws / "engines.md"
    for p in (onto, eng):
        if not p.exists():
            sys.exit(f"missing {p}; run `ub_sched.py init --dir {ws}` first")
    classes, relations = parse_ontology(onto)
    terms, crosswalk = parse_engines(eng)
    cards = []
    for p in sorted((ws / "cards").glob("*.md")):
        fm = parse_front_matter(p)
        cards.append((p, fm))
    return classes, relations, terms, crosswalk, cards


def validate(fm, classes, relations, terms):
    problems = []
    if fm is None:
        return ["no front matter"]
    for key in REQUIRED:
        if not fm.get(key):
            problems.append(f"missing {key}")
    for key, allowed in ENUMS.items():
        if fm.get(key) and fm[key] not in allowed:
            problems.append(f"{key}={fm[key]!r} not in {sorted(allowed)}")
    for key, allowed in LIST_ENUMS.items():
        for v in fm.get(key) or []:
            if v not in allowed:
                problems.append(f"{key}: {v!r} not in {sorted(allowed)}")
    for c in fm.get("concepts") or []:
        if c not in classes:
            problems.append(f"unknown concept {c!r} (add to ontology.md or fix)")
    for r in fm.get("relations") or []:
        if r not in relations:
            problems.append(f"unknown relation {r!r}")
    for t in fm.get("engine_terms") or []:
        if t not in terms:
            problems.append(f"unknown engine term {t!r} (use Engine:Term from engines.md)")
    if fm.get("engines") and not fm.get("level"):
        problems.append("engine-specific card without level [O7]")
    return problems


def cmd_init(args):
    ws = Path(args.dir)
    (ws / "cards").mkdir(parents=True, exist_ok=True)
    (ws / "designs").mkdir(exist_ok=True)
    copies = {
        SKILL / "references/ontology.md": ws / "ontology.md",
        SKILL / "references/engines.md": ws / "engines.md",
        SKILL / "templates/facts.md": ws / "facts.md",
        SKILL / "templates/questions.md": ws / "questions.md",
    }
    for src, dst in copies.items():
        if dst.exists():
            print(f"keep     {dst}")
        else:
            shutil.copyfile(src, dst)
            print(f"created  {dst}")
    print(f"ready    {ws}/cards/ and {ws}/designs/")


def cmd_check(args):
    ws = Path(args.dir)
    classes, relations, terms, _, cards = load(ws)
    bad = 0
    for path, fm in cards:
        problems = validate(fm, classes, relations, terms)
        if problems:
            bad += 1
            print(f"{path.name}:")
            for p in problems:
                print(f"  - {p}")
    print(f"{len(cards)} cards, {bad} with problems; ontology: {len(classes)} classes, "
          f"{len(relations)} relations; engines: {len(terms)} terms")
    return 1 if bad else 0


def cmd_matrix(args):
    ws = Path(args.dir)
    classes, relations, terms, crosswalk, cards = load(ws)
    good = [(p, fm) for p, fm in cards if fm]
    out = ["# Coverage matrix", "",
           "> Generated by `ub_sched.py matrix`; do not edit. Re-run after adding or changing cards.", ""]

    out += ["## Sources", "",
            "| Source | Type | Evidence | Engines | Level | Pattern | L1 | L2 | L3 | L4 | L5 | Locality | Separates | UB transfer |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, fm in good:
        layers = set(fm.get("layers") or [])
        marks = ["✓" if f"L{i}" in layers else "" for i in range(1, 6)]
        out.append("| " + " | ".join([
            fm.get("source_id", "?"), fm.get("type", ""), fm.get("evidence", ""),
            ", ".join(fm.get("engines") or []) or "—", ", ".join(fm.get("level") or []) or "—",
            fm.get("pattern", ""), *marks, fm.get("locality_model", ""),
            fm.get("separates", ""), fm.get("ub_transfer", "")]) + " |")

    out += ["", "## UB concept coverage", "",
            "Concepts with no card are gaps in what the team has read.", "",
            "| Layer | Concept | Cards |", "|---|---|---|"]
    for concept, layer in sorted(classes.items(), key=lambda kv: (kv[1], kv[0])):
        ids = [fm["source_id"] for _, fm in good if concept in (fm.get("concepts") or []) and fm.get("source_id")]
        out.append(f"| {layer} | `{concept}` | {', '.join(ids) if ids else '**none**'} |")

    out += ["", "## Crosswalk gaps", "",
            "Lossy or missing engine-to-UB mappings (engines.md §5) and the cards that touch the engine concept.", "",
            "| Engine concept | UB concept | Fidelity | Cards |", "|---|---|---|---|"]
    for eterm, ub, fid in crosswalk:
        if fid.split()[0] not in {"lossy", "none", "degenerate"}:
            continue
        ids = [fm["source_id"] for _, fm in good
               if eterm in (fm.get("engine_terms") or []) and fm.get("source_id")]
        name = f"`{eterm}`" if ":" in eterm else eterm
        out.append(f"| {name} | {ub} | {fid} | {', '.join(ids) if ids else '**none**'} |")

    out += ["", "## Engine-term coverage", "", "| Engine term | Cards |", "|---|---|"]
    for t in sorted(terms):
        ids = [fm["source_id"] for _, fm in good if t in (fm.get("engine_terms") or []) and fm.get("source_id")]
        if ids:
            out.append(f"| `{t}` | {', '.join(ids)} |")

    warnings = [(p.name, validate(fm, classes, relations, terms)) for p, fm in cards]
    warnings = [(n, w) for n, w in warnings if w]
    if warnings:
        out += ["", "## Card problems (run `ub_sched.py check`)", ""]
        out += [f"- {n}: {'; '.join(w)}" for n, w in warnings]

    (ws / "matrix.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {ws / 'matrix.md'} ({len(good)} cards)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("init", cmd_init), ("check", cmd_check), ("matrix", cmd_matrix)):
        p = sub.add_parser(name)
        p.add_argument("--dir", default="ub-sched", help="workspace directory (default: ub-sched)")
        p.set_defaults(fn=fn)
    args = ap.parse_args()
    sys.exit(args.fn(args) or 0)


if __name__ == "__main__":
    main()
