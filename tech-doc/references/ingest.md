# Ingesting existing documents

Read this in Phase 1 whenever the user names existing docs as sources, and again
before drafting any section whose `Sources:` line lists one.

A source document is **raw material and evidence — not truth, and not a link target**.
Code is truth. A doc tells you what someone believed at the time they wrote it; the
wiring tells you what runs today. Every claim lifted from a doc is unverified until you
have seen it in the code.

The output replaces the source docs for its reader. It never says "see X.md", never
names an ingested doc, and never assumes the reader has one. Content worth keeping is
verified, rewritten, and carried in. Content not worth keeping is dropped.

## Authority levels

Classify each source document once, in `SOURCES.md`. The level decides how much
verification a claim needs before it enters the target doc.

| Level | Means | What you may carry without re-deriving |
|---|---|---|
| `measured` | Benchmark results, test output, captured logs | Numbers, together with the run conditions that produced them |
| `authored` | A design spec, RFC, or ADR written by the team | Intent, rationale, rejected alternatives, naming |
| `derived` | A doc describing code someone read | Nothing. Treat as a hypothesis to check |
| `external` | Vendor or upstream docs (Arrow ADBC spec, Druid docs) | Protocol and API facts about that vendor only |

Rationale is the one thing code cannot tell you. An `authored` doc is the only place
"why" legitimately comes from. Carry it in as a stated design decision — the reader
does not need to know which doc it came from.

Numbers from a `measured` doc must carry their conditions *into the target doc*: row
count, query shape, hardware, version. A throughput figure without them is a rumour,
and the reader has no source doc to look them up in.

`external` is the one exception to the no-link rule: a public upstream spec (a vendor
API reference, a protocol spec) may be linked as further reading. The target doc still
states every fact it relies on.

## Procedure

### 1. Inventory

Find candidates and show the user the list before reading them in full:

```bash
find docs -name '*.md' -not -path '*/.techdoc/*' | sort
git log --oneline -1 --format='%ad %s' --date=short -- <doc>   # per doc: how stale?
```

Read each candidate's headings first — cheap, and enough to scope it:

```bash
grep -n '^#\+ ' <doc>
```

### 2. Map to the outline

Every source doc gets a row in `SOURCES.md` mapping it to the sections that will carry
its content. Do this **before** drafting, because it changes the outline: a doc may
supply a whole section, a companion file, or reveal an area the outline missed.

Decide per doc, and record the verdict:

| Verdict | When | Effect on the target doc |
|---|---|---|
| `absorb` | The doc covers part of the design the reader must understand | Its verified claims are rewritten into main-file sections |
| `split` | The doc is deep reference material: full benchmark tables, exhaustive config, per-backend detail | Its verified content is rewritten into a companion file of the document set |
| `extract` | Only its numbers or conclusions are needed | Those facts become table rows in a section, with their conditions |
| `supersede` | The doc is wrong or stale | Nothing is carried; the code supplies the content. Conflicts logged |
| `drop` | Out of scope for this document | Nothing is carried. Reason logged |

A doc may take two verdicts for different parts: `absorb` the rationale, `split` the
result tables. Record both in its `### ` block.

Length is not a reason to link out. A long doc is condensed: take its claims, drop its
narration. If its detail is reference material, it goes to a companion file; if not,
most of it was narration.

### 3. Extract, do not paste

Take the claims, not the prose. For each passage you intend to carry:

1. List the facts it states: components, behaviors, values, conditions, decisions.
2. Verify each fact at its authority level (§4). Drop the ones that fail.
3. Write the survivors in this doc's style (`style.md`) and names (`CONTEXT.md`).

A lifted paragraph carries the source's spelling of every component name and its
padding. It will contradict `CONTEXT.md` within two sections, and it fails the
precision rules in `style.md`.

Reconcile names as you go. If the source doc calls it `ShardingGate` and the code
calls it `ShardingGate` but a third doc says `sharding gate`, the code wins and the
spelling goes in `CONTEXT.md`.

Diagrams do not survive absorption. Redraw to the rules in `style.md` rather than
pasting a source diagram; a source diagram was drawn to answer a different question.

Tables of measured numbers may be carried nearly whole, into a companion if long —
but re-typed into this doc's column names and units, with a condition line above each
table.

### 4. Verify before you carry

For each claim you intend to carry over, at the authority level's required depth:

```bash
grep -rn '<ClassName>' --include=*.java --include=*.rs .    # does it exist?
grep -rn '<ClassName>' --include=*.java . | grep -v '/test/' # is it reachable?
```

The second command is the one that matters. A component with no non-test caller is
dormant: the doc describing it may be entirely accurate about code that never runs.
Say so in the target doc rather than silently repeating the source.

Record every claim you could not verify in `state.json` under `open_questions`, and
either ask the user or leave it out. Never launder an unverified source claim into the
target doc's confident voice.

### 5. Conflicts

| Conflict | Resolution |
|---|---|
| Doc vs. code | Code wins. Always. |
| Doc vs. doc, both `authored` | Ask the user. Do not pick by recency alone |
| Doc vs. doc, different levels | Higher authority wins for its own subject |
| Two `measured` docs disagree | Both are true for their conditions. Carry both, each with its conditions |

When code wins over a doc, the target doc describes the code. It does not mention that
a source doc disagrees — the reader never sees that doc. Record the disagreement in the
`Conflicts` line of the doc's `SOURCES.md` block, then offer the user the choice
**before** editing anything outside the target path:

1. **Correct at source** — edit the source doc. Needs consent, since it is outside the
   scope you were given.
2. **Leave it** — the target doc is correct; the source doc stays stale. Listed in the
   Phase 4 report as superseded-but-uncorrected.
3. **Defer** — log in `QUESTIONS.md`, `<!-- TODO(user): ... -->` in the target.

Log the choice in `state.json` under `resolved` so a later session does not
re-litigate it.

## Provenance

Provenance is for maintainers, so it lives in the workspace, not in the output.

Every section file records where its content came from, as an HTML comment at the top:

```markdown
<!-- sources: docs/RESULTS.md (measured, extract); connectors/druid-adbc/src/lib.rs (code) -->
```

Phase 4 strips these comments from the output. They stay in `sections/`, so when a
source doc changes, `grep` tells you which sections to revisit:

```bash
grep -l 'RESULTS.md' docs/.techdoc/<slug>/sections/*.md
```

In the reader-facing text, never link to or name an ingested doc — not as a citation,
not as "further reading", not as "the design spec says". `metrics.py` gates this as
`source_links`. Credibility comes from precision instead: a measured number with its
conditions, a behavior with the class that implements it.

## Non-English sources

Terminology comes from the code, not from a translation. Keep identifiers verbatim
and record the term pair in `CONTEXT.md` so the same concept does not appear under two
names across sections:

```markdown
## Term pairs (source doc → this doc)
| 连接器 (设计说明书) | connector |
```

Translate claims; do not translate diagrams' node labels into a mix of both languages.
