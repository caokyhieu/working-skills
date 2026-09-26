---
name: tech-doc
description: Write or update a long, self-contained technical document (system design doc, README, API guide) in markdown — precise prose, simplified mermaid diagrams, runnable API examples, SQL use cases with table schemas. Ingests existing docs (design specs, benchmarks, ADRs, per-component notes) as raw material, verified against the code, and rewrites their content into the new document instead of linking to them. Structure-first, section-by-section, each section checked by an independent verifier agent, interactive checkpoints, resumable across sessions. Use when asked to write/draft/continue technical documentation, or to consolidate several existing docs into one.
---

# tech-doc

Produce one self-contained technical document set through a resumable, structure-first
workflow. Never draft the whole document in one pass. Never invent behavior — read the code.

Three rules shape everything below:

- **Self-contained.** The finished document never sends the reader to an ingested doc.
  Ingested docs are raw material: their content is verified, rewritten, and carried into
  the document set. A reader holding only the output has everything.
- **Code is truth.** Existing docs are evidence, not truth. Code is also a source in its
  own right: it carries mechanisms — lifecycles, state machines, threading, config
  surface, failure paths, transport internals — that no source doc mentions. A section
  that omits a mechanism its area implements is incomplete, even when every sentence in
  it is correct.
- **Precise, not wordy.** Every sentence states a fact about the system: a component, a
  condition, a value. A sentence that states no such fact is deleted (`references/style.md`).

Review what you already wrote before writing the next section — drift is invisible from
inside the section that caused it. Then let a second agent check what you just wrote —
errors are invisible to the one who made them.

## Output layout

The document set is one main file plus optional companion files, all written fresh:

```
docs/query-engine.md                  main document — the design, read top to bottom
docs/query-engine/benchmarks.md       companion — reference material looked up, not read
docs/query-engine/config-reference.md companion
```

Links between the main file and its companions are internal and allowed. Links to an
ingested source doc are not. Put content in a companion when the reader looks it up
rather than reads it through: full result tables, exhaustive config lists, per-backend
detail. Anything needed to understand the design stays in the main file.

## Workspace

All state lives beside the target doc, in `docs/.techdoc/<slug>/`:

| File | Role |
|---|---|
| `state.json` | phase, section list + status, target path, companion files |
| `OUTLINE.md` | approved structure (source of truth for scope and file placement) |
| `CONTEXT.md` | frozen glossary: component names, term spellings, table schemas, endpoint names, diagram legend |
| `SOURCES.md` | every ingested document: authority level, verdict, which sections take its content |
| `CODEMAP.md` | mechanisms found by reading the code: per component its lifecycle/state transitions, threading, config keys + defaults, exceptions + fallback, transport/wire internals. Each entry maps to an outline section or is listed as deliberately dropped. |
| `sections/NN-slug.md` | one drafted section each |
| `verify/NN-slug.md` | the verifier's report for that section |
| `QUESTIONS.md` | open decisions awaiting the user |

`CONTEXT.md` is what keeps a long doc consistent. Re-read it before drafting every
section — it survives context compaction; your memory of section 2 does not.
`references/review.md` and the verifier are what catch it when that fails.

## Phase 0 — Resume

Always run first.

```bash
ls docs/.techdoc/*/state.json 2>/dev/null
```

If a state file exists, read `state.json` + `OUTLINE.md` + `CONTEXT.md` + `SOURCES.md`
+ `CODEMAP.md` (if present), report to the user:

```
Resuming <doc>: <n>/<total> sections approved. Next: <NN-slug>.
Sources: <n> ingested, <n> superseded-but-uncorrected
Open questions: <count>
```

If the user is resuming to add a newly written document, that is Phase 1b for that one
doc, then a return to the recorded phase — not a restart.

Then resolve open questions (Phase 3 checkpoint) and continue from the recorded phase.
If none exists, go to Phase 1.

## Phase 1 — Scope

Use **AskUserQuestion** (one call, batched). Do not guess these:

1. Document type + target path (system design doc / feature design spec / README /
   API reference / ops runbook). A feature design spec uses
   `references/template-design-spec.md` as its outline — confirm rather than re-derive.
2. Audience (new contributor / integrator calling the API / operator / reviewer).
3. Source of truth — which dirs, specs, or existing docs to read. Offer what you found,
   code and docs as separate options, so the answer says which existing docs are in.
4. What is explicitly out of scope.
5. Which mechanisms must be covered in depth. Offer the candidates you can see —
   transport internals (e.g. ADBC vs JDBC: connection open, pooling, timeouts, driver
   resolution, catalog sync), lifecycle / state machines, threading model, error and
   fallback paths, cache routing. The answer sets which sections Phase 2 types as
   `Type: mechanism`.

If any existing document is named, run Phase 1b before proposing structure. Otherwise
read the code sources directly. Run Phase 1c always. Either way, write `CONTEXT.md` with
names and terms as the code actually spells them.

## Phase 1b — Ingest existing documents

Skip only if no existing doc is in scope. Read `references/ingest.md` first.

A system rarely has one document. Benchmarks, design specs, ADRs, and per-component
notes each cover a slice. The target doc reconciles them into one voice and one set of
names, and replaces them for the reader.

1. Inventory the candidates and show the user the list before reading them in full.
2. Classify each: authority level (`measured` / `authored` / `derived` / `external`)
   and verdict (`absorb` / `split` / `extract` / `supersede` / `drop`).
3. Write `SOURCES.md`. Map each doc to the outline sections that will carry its
   content — this runs before Phase 2 because a source doc changes what the outline
   should contain.
4. Merge each doc's terminology into `CONTEXT.md`, spelled as the code spells it.

Three failure modes to avoid:

- **Pointing.** "See `design-spec.md` for details." The reader of the output does not
  have that doc, or has a copy that will drift. Carry the content in, or drop it.
- **Pasting.** Copying a source doc's prose verbatim. It carries the source's names,
  length and diagrams, which contradict `CONTEXT.md` within two sections. Take the
  claims, not the prose — rewrite each one in this doc's style.
- **Laundering.** Repeating a source doc's claim in the target doc's confident voice
  without checking the code. Docs describe what someone believed; verify, then write.

## Phase 1c — Code walk

Always run, right after Phase 1b. This is the pass that finds what the docs left out.
Read `references/codewalk.md`.

For each component or area in scope, open its primary class(es) and read them end to
end — constructor, fields, public methods, exception sites — not a grep for one term.
For each, record in `CODEMAP.md`: lifecycle / state, threading, config surface, failure
modes, transport / wire, and surprises.

Then map every `CODEMAP.md` entry to the outline section that will carry it, or list it
under a **Deliberately dropped** heading with a one-line reason. This runs before
Phase 2 because an unmapped mechanism means the outline is missing a section.

Depth bar: if a drafted section could have been written from the source docs alone,
without opening the code, `CODEMAP.md` did not feed it and the section is too shallow.

## Phase 2 — Structure first

If the doc type has a template (`references/template-design-spec.md`), instantiate its
spine and fill in only the variable subsections. Otherwise build the outline from scratch.

Write `OUTLINE.md`. Per section, one line each:

```markdown
## NN. <Title>
- Purpose: <one sentence — the question this section answers>
- Type: <overview | mechanism>
- File: <main | companion: benchmarks.md>
- Diagram: <none | mermaid flowchart of X | sequence of Y | stateDiagram of Z>
- Examples: <none | curl+response for /foo | SQL: orders x customers>
- Sources: <code paths | ingested docs from SOURCES.md | both>
- CODEMAP: <the CODEMAP.md entries this section carries — none only for pure overview>
- Depends on: <sections it must stay consistent with>
```

Rules:
- A section that needs more than one diagram is two sections.
- Every ingested doc with verdict `absorb`, `split` or `extract` has its content land in
  some section. No section exists only to point at a source doc.
- Cut any section whose purpose sentence duplicates another's.
- `Type: mechanism` for any section carrying a lifecycle, threading model, transport
  path, config surface, or failure/fallback logic. It must pass the depth checklist
  (`references/review.md` §B) and may use a `stateDiagram` and a slightly larger
  diagram (see `references/style.md`).
- `File: companion` only for lookup material. The main file carries the design.
- Every `CODEMAP.md` entry appears on some section's `CODEMAP:` line, or under the
  outline's `Deliberately dropped` list. An unplaced mechanism is a missing section.
- Order: what it is → how it fits → how to use it → reference → operations.
- A functional area with several flows becomes numbered scenarios, one diagram each —
  that is the decomposition rule, not a longer diagram.

There are no word budgets. Length follows from content: a section is as long as its
facts require. The precision rules in `references/style.md` and the verifier keep it
tight.

Present the outline and get explicit approval before drafting. Record it in `state.json`.

## Phase 3 — Draft, verify, checkpoint — one section per turn

For each pending section, in order:

0. **Look back** (`references/review.md` §A). Re-read the previous section and every
   section in this one's `Depends on:` line. Three questions: is this section's purpose
   already answered, does it need an undefined term, is the previous section's promise
   still true? Fix the outline now if any answer is bad — not after drafting.
1. Re-read `CONTEXT.md`, the outline entry, the section's rows in `SOURCES.md`, and its
   `CODEMAP:` entries in `CODEMAP.md`.
2. Read the primary class(es) for this section end to end — constructor, fields,
   lifecycle methods, exception sites — not a grep for one claim. Then the ingested
   docs mapped to it. Verify each doc claim you intend to carry against the code
   (`references/ingest.md` §4). An unverifiable claim is an open question, not prose.
   Before drafting a `Type: mechanism` section, answer its depth checklist
   (`references/review.md` §B). A blank answer is a gap to fill by reading more code,
   not to skip.
3. Draft to `sections/NN-slug.md` following `references/style.md`, opening the file
   with its provenance comment (workspace-only; stripped at assembly):
   `<!-- sources: docs/RESULTS.md (measured, extract); path/to/File.java (code) -->`
   Carry the content of every mapped source doc into the section itself. Never write a
   link to, or a mention of, an ingested doc.
4. Append any new canonical names/schemas to `CONTEXT.md`.
5. **Self-check** (`references/review.md` §B). Verify every diagram edge label as a
   separate claim. Confirm every behavioral claim traces to a file read in this
   session, not to memory of it.
6. **Verify** (`references/verifier.md`). Spawn an independent verifier agent on the
   section. It re-reads the code itself and writes `verify/NN-slug.md`. Fix every
   `WRONG`, `UNSUPPORTED` and self-containment finding, tighten every `PADDING` and
   `VAGUE` one, then re-verify. At most two rounds; a finding you dispute with
   file:line evidence goes to the checkpoint, not silently overruled.
7. Set status `verified` in `state.json`.
8. Checkpoint: show the section, ask **approve / revise / defer**. Report what the
   self-check and the verifier found, and what you changed — including "nothing".
   Silence reads as "not run".

After every third approved section, run the **sweep** (`references/review.md` §C):
mechanical checks for heading/filename mismatch, duplicate headings, dangling `§N`
references and spelling drift, then a read for contradiction, duplication and unbacked
confidence, then `python3 references/metrics.py docs/.techdoc/<slug>` for the scored
gates (§F). Never loosen a gate to make the document pass. Log what it finds per §E.
Renumbering follows §D, always — it is the most reliable way to silently break a
finished document.

Stop and ask (AskUserQuestion, log in `QUESTIONS.md`) when:
- The code contradicts an ingested doc. Code wins in the target doc. Whether to also
  correct the source doc is the user's call.
- Two ingested docs contradict each other and neither outranks the other.
- The code is ambiguous.
- A design rationale is not recoverable from the code or any `authored` doc.
- A decision would change the outline.
- A value is environment-specific (ports, hosts, credentials, limits).

Never fill such a gap with a plausible guess. Write `<!-- TODO(user): ... -->` only if
the user chose to defer.

## Phase 4 — Assemble

1. Write the main file: approved `File: main` sections, in outline order. Write each
   companion file from its sections, in outline order. The main file's table of contents
   lists every section; companion sections link to their file.
2. Strip every provenance comment (`<!-- sources: ... -->`) from the output. Provenance
   stays in the workspace.
3. Consistency pass against `CONTEXT.md`: one spelling per component, one name per
   concept, no term used before it is defined.
4. Run the full sweep (`references/review.md` §C) one last time, and
   `metrics.py <workspace> --strict` (§F). `source_links` must be 0. Report the metric
   line with the finished doc.
5. Run the verifier once more on the assembled document set, in whole-document mode
   (`references/verifier.md` §Whole-document). It looks for cross-section contradiction
   and any content that still depends on an ingested doc.
6. Verify every mermaid block parses and every internal link resolves.
7. Verify each code/SQL example against the real schema or signature; run it if runnable.
8. Source coverage pass: every `SOURCES.md` row with verdict `absorb`, `split` or
   `extract` has its `Take:` content present in the named sections. Same pass for
   `CODEMAP.md`: every entry is carried by a section or is on the outline's
   `Deliberately dropped` list.
9. Report leftover TODOs, unanswered questions, and any source doc left superseded but
   uncorrected.

Keep the workspace after assembly — updates resume from it.

## References

- `references/ingest.md` — authority levels, verdicts, extraction, conflict rules,
  provenance. Read in Phase 1b and before drafting any section with an ingested source.
- `references/codewalk.md` — how to read a class for `CODEMAP.md`: the six things to
  record, and the depth bar. Read in Phase 1c and before drafting a mechanism section.
- `references/style.md` — precision rules, self-containment, mermaid, API and SQL
  examples. Read before Phase 3.
- `references/review.md` — look-back, self-check, sweep, renumbering, metrics, and what
  to record. Read before Phase 3; re-read at every sweep.
- `references/verifier.md` — the verifier agent's brief, prompt, report format, and how
  to act on it. Read before the first section's verify step.
- `references/metrics.py` — scored consistency / precision / self-containment gates. Run
  at every sweep and before assembly.
- `references/templates.md` — state.json, SOURCES.md, CODEMAP.md, CONTEXT.md shapes and
  section skeletons.
- `references/template-design-spec.md` — the house format for release feature design
  specs. Read in Phase 2 whenever the target is one.
