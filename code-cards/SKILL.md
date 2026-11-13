---
name: code-cards
description: Keep short, precise documentation of a fast-growing (often AI-generated) codebase — one card per module (purpose, interface with code anchors, flow, invariants, failure modes, dependencies, gotchas, mermaid diagrams) plus one system card with a runtime view — every claim and every diagram edge checked against the code by independent judge agents (full line coverage, planted canary errors, probe questions, deeper multi-judge review for complex modules) and by script checks (anchors, signatures, imports vs dependencies), re-synced after every change by file fingerprints, and assembled into a generated architecture section of the project README. Use after an AI coding session or a merge to update the docs for what changed, to document an existing codebase module by module, to find which docs are stale or which files are undocumented, or to refresh the README architecture section.
---

# code-cards

Documentation that stays true while code grows. The unit is a **card**: one short file
per module, every claim traceable to the code, anchored by `path::symbol`. A script
fingerprints the files each card owns, so after any change it says exactly which cards
are stale and which files no card covers. The README's architecture section is
generated from the cards, never written by hand.

No card is trusted on the writer's word. An independent **judge** agent (several, for
complex code) checks every claim line and every diagram edge against the code, and the
script tests the judge itself with a planted error. `stamp` refuses a card without a
passing verdict (`references/verifier.md`).

Four rules:

- **Code is truth.** Read the code before writing a claim. Never document from the
  prompt that generated the code, from a commit message, or from memory of a file read
  earlier. Where intent and code differ, the card says what the code does and flags it
  (`references/card-format.md` §Document behavior, not intent).
- **Condensed.** A card is a reference, not an essay: tables and numbered steps, one
  fact per sentence, a 150-line budget. If removing a sentence loses no fact, remove it.
- **Incremental.** After a change, update only the stale cards, only the affected
  sections. Never regenerate a card from scratch when a diff will do — rewriting
  verified text re-opens it to error.
- **Judged, not asserted.** The writer never grades its own card. Judges get paths, not
  the writer's explanation; a judge that misses its canary is replaced, not argued with.

## Layout

```
docs/cards/
├── config.json                 readme path + heading, source/ignore globs, line and diagram budgets
├── _system.md                  current system card: summary, runtime view, flows, glossary, decisions, run/test
├── <module>.md                 current card per module; front matter carries version, updated, code_commit
├── stamps.json                 per card: version, date, commit, sha of every owned file, card sha, judge kind
├── CHANGELOG.md                project timeline: one row per card version or release, newest first
├── history/<module>/
│   ├── CHANGELOG.md            this card's versions: note, sections changed, code files changed, judge summary
│   └── v003_2026-11-13_abc1234/
│       ├── card.md             the card exactly as stamped (frozen)
│       └── judge/              the reports and verdict.json that passed this version
├── releases/<name>/            every card frozen at a release, plus MANIFEST.md (versions, commits)
└── verify/<module>/            the current judging round (prompts, judge copies, reports, run.json)
README.md                       section between <!-- code-cards:start --> and <!-- code-cards:end -->
```

Commit all of it. The current cards are what people read; `history/` and `releases/`
answer "what did the docs say, and against which code, at that time".

## Versions

Every `stamp` creates a version; nothing else does. Drafts and judging rounds stay in
`verify/` until a card passes.

- **Version folder** `history/<module>/vNNN_<date>_<commit>/`: the card as stamped and
  the judge evidence. `-dirty` after the commit means the owned code had uncommitted
  changes at stamp time; commit first when you can, so the version points at real code.
- **Card front matter** gets `version`, `updated`, `code_commit`, written by `stamp`
  (never by hand; they do not count as card edits).
- **Changelogs**: `history/<module>/CHANGELOG.md` per card and `CHANGELOG.md` for the
  project, both newest first. Each entry records the `--note` (why), the card sections
  changed, the code files changed since the previous version, and the judge summary.
  Always pass `--note`: say what changed in the code, not "updated docs".
- **Releases**: `cards release <name> --note "..."` at a tag, sprint end or hand-over
  freezes every current card into `releases/<name>/` with a manifest. It refuses while
  a card is stale or unjudged. Release folders are never edited.
- **Tracing**: `cards history` (project timeline), `cards history <module>` (versions
  with judge kind and tier), `cards history <module> --diff v002 v005` or
  `--diff v002` (against current). To see the code a version described:
  `git show <code_commit>:<path>`.
- The README table shows each card's version and date, plus the date and commit the
  cards were last checked at, with a link to `CHANGELOG.md`.

The script (`scripts/cards.py`, standard library) is run from the project root;
below, `cards` means `python3 <skill dir>/scripts/cards.py`.

| Command | Does |
|---|---|
| `cards init [--write]` | create `docs/cards/`, propose a module split from the tree; `--write` adds skeleton cards |
| `cards status [--strict]` | per card `ok / stale / unstamped`; uncovered and double-owned files |
| `cards diff <module>` | files changed, added, removed since the card's stamp, and the git diff stat |
| `cards check [modules] [--render]` | lint: sections, anchors resolve, Interface parameters exist in the definition, real imports vs `depends_on`, Uses/Used by agree, mermaid structure (`--render`: parse with mermaid-cli), vague words, length, `TBD` |
| `cards graph [module]` | mermaid of the module's file imports, or of all modules, from the code |
| `cards judge <module> [--self] [--shards N] [--full]` | complexity tier → N judge prompts, each with its lines and a planted canary |
| `cards verdict <module> [--waive ID=reason]` | grade the reports: coverage, canary, evidence, findings → PASS / FAIL |
| `cards stamp <modules> \| --all --note "why"` | record fingerprints and write a new version + changelog entries; refuses without passing `check` and a passing verdict |
| `cards history [module] [--diff vA [vB]]` | project timeline, a card's versions, or a diff between versions |
| `cards release <name> [--note]` | freeze all current cards into `releases/<name>/` with a manifest |
| `cards readme [--insert-after H] [--check]` | write the generated section into the README; `--check` exits 1 if stale |

## Step 0 — Orient

Always first:

```bash
cards status
```

- No `docs/cards/` → **Bootstrap**.
- Stale, edited, unstamped or uncovered → **Update**.
- All `ok` and the user asked for the README → **README**.

Report the status table to the user in one block before doing anything else.

## Bootstrap — document an existing codebase

1. `cards init`. Show the proposed module split.
2. Ask once (AskUserQuestion, batched): the module split (merge/split/rename), which
   paths are out of scope (add to `ignore_globs`), where the README section goes
   (heading to insert after, or the end), and whether to add the agent rule to
   `CLAUDE.md` / `AGENTS.md` (see *Keep it in the loop*).
3. `cards init --write`, then edit each card's front matter to the agreed split.
   Run `cards status` until there are no uncovered or double-owned files.
4. For each module, in dependency order (leaves first, so `Used by` and `Uses` agree):
   1. Read every owned file end to end — constructor, public functions, exception sites,
      config reads, module-level state. Not a grep.
   2. Fill the card per `references/card-format.md`. Anchor every Interface row,
      invariant, failure mode and config key. Add a diagram where it says more than the
      steps (§Diagrams): start from `cards graph <module>` and the calls you followed,
      never from memory.
   3. `cards check <module>`; fix every error.
   4. **Judge** (`references/verifier.md`): `cards judge <module>`, spawn one fresh
      agent per prompt file in parallel, `cards verdict <module>`. On FAIL, fix from
      the code and judge again (only changed lines are re-judged). A judge that missed
      its canary is replaced by a fresh one.
   5. Show the card to the user with the judge summary (tier, judges, canaries caught,
      findings fixed, waivers). On approval, `cards stamp <module> --note "first version"`.

   For more than about five modules, show cards in batches of three and ask
   approve / revise per card.
5. Write `_system.md` last, from the approved cards: Summary, Runtime view (processes,
   modules and external systems, every cross-process edge labelled with its protocol),
   cross-module Flows (each step names a module, one sequenceDiagram per flow),
   Cross-module invariants, Glossary, Decisions, Run and test (run each command; record
   only what worked). Ask the user for rationale the code and history do not show —
   never invent it. `cards judge _system` (the judge also checks it against the module
   cards), `cards verdict _system`, `cards stamp _system`.
6. **README** step.

## Update — after a coding session, merge or refactor

This is the normal loop. Do it after every substantial AI-generated change.

1. `cards status`. For each stale card, `cards diff <module>`; read the full diff
   (`git diff <commit> -- <files>`) and then the changed files themselves.
2. Decide per card which sections the change touches:

   | Change in code | Sections to revisit |
   |---|---|
   | public signature added / removed / changed | Interface, Flow, `entry_points`; callers' cards (grep for the symbol) |
   | new branch, exception, retry, fallback | Failure modes, Flow |
   | new config read or default changed | Config |
   | new state, schema, file, table | State and data, Invariants |
   | new import of another module | `depends_on`, Dependencies (both cards) |
   | internal refactor, same behavior | nothing but anchors — run `check` |
   | tests only | Tests |

   Edit only those sections. Keep verified text that is still true word for word.
3. **Uncovered files**: assign each to an existing card's `paths`, or create a new card
   (Bootstrap step 4 for that module), or add it to `ignore_globs` with the user's OK.
4. **Removed modules**: delete the card; drop it from other cards' `depends_on`.
5. `cards check` on every edited card, then judge each one (`judge` → judges →
   `verdict`). If the code changed, every line of the card is re-judged, since unchanged
   text can have become false; if only the card changed, only the edited lines are.
   Diagrams on a changed path are re-drawn from the code, not patched by hand.
6. Look for drift the diff introduced: a new duplicate helper, a swallowed exception, a
   stub returning a constant, behavior that contradicts what the user said they asked
   for. Record it under Gotchas and tell the user — that is a code finding, not only
   a doc edit.
7. If modules or `depends_on` changed, revisit `_system.md` (Flows, Summary).
8. Show the user a compact change report, then stamp and refresh:

   ```
   Cards updated: ingest (Interface, Failure modes), storage (Config)
   New card: export   Unchanged but re-anchored: api
   Judges: ingest (complex, 3 judges, canaries 3/3) 41 OK, 2 WRONG fixed; export (small) 11 OK
   Code findings: export.write_csv swallows OSError (export.py::write_csv)
   ```

   ```bash
   cards stamp ingest storage export api [_system] --note "export: CSV writer, retry on OSError"
   cards readme
   ```

   Each stamped card gets a new version folder and changelog entry. At a tag or
   hand-over, also `cards release <name>`.

## README — integrate into the project README

```bash
cards readme --insert-after "Installation"   # first time; places the section after that heading's section
cards readme                                 # afterwards; replaces only the marked block
```

The generated block contains: the system Summary, a mermaid graph of modules from
`depends_on` (confirmed against the real imports by `check`), a module table (name →
card link, Purpose first sentence, entry points), and the system-card sections listed
in `config.json` → `readme_sections` (default Summary, Runtime view, Flows, Run and
test), diagrams included. Only judged and stamped content reaches the README. Everything outside the markers is the user's and
is never touched. Never hand-edit inside the markers: edit the card, re-run `readme`.

If the README already has a hand-written architecture section, show it to the user and
ask whether to replace it with the generated one, keep both, or move its unique facts
into `_system.md` first (verify each against the code before moving it).

## Keep it in the loop

Offer, during Bootstrap, to add this to the project's `CLAUDE.md` / `AGENTS.md` so
every coding agent uses the cards as context and keeps them current:

```markdown
## Code cards
- Before changing a module, read `docs/cards/<module>.md` and `docs/cards/_system.md`.
- After changing code, run the code-cards Update loop for the stale cards
  (`cards status`), then `cards readme`.
```

And for CI or a pre-commit hook, both exit non-zero when docs lag the code:

```bash
python3 .claude/skills/code-cards/scripts/cards.py status --strict
python3 .claude/skills/code-cards/scripts/cards.py readme --check
```

## Stop and ask

- Code contradicts what the user says it should do.
- A design rationale is not in the code, comments or history.
- A module boundary is unclear (a file fits two cards).
- A value is environment-specific (hosts, credentials, limits per deployment).

Never fill these with a plausible guess.

## Related skills

- `tech-doc`: long, narrative design documents (onboarding guide, feature design
  spec). Its ingest phase can take stamped cards as sources: they are already judged
  against the code, and their anchors point it to the code to read. The diagram rules
  here follow its `references/style.md` §Mermaid diagrams, so both look alike. Cards
  stay the short, always-current layer; tech-doc builds the long read from them.
- `insight-ppt`: to present the architecture as slides, take the system card's Runtime
  view and Flows (judged diagrams) and redraw them with
  `insight-ppt/references/diagram-styles.md`; the slide shows only nodes and edges the
  card has.
- When installed beside this skill, read the referenced file from the sibling folder;
  if it is missing, the rules in `references/card-format.md` are enough on their own.

## References

- `references/card-format.md` — front matter, sections, anchors, diagrams, precision
  rules, behavior vs intent, system card, a complete example. Read before writing any card.
- `references/verifier.md` — judge layers, tiers, spawning, what `verdict` enforces,
  rounds, waivers, the checkpoint report. Read before the first `judge`.
- `references/verifier-prompt.md` — the judge's brief; `cards judge` fills it in.
- `templates/module-card.md`, `templates/system-card.md` — skeletons `init` copies.
