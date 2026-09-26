# Self-review

A long document does not drift all at once. It drifts one section at a time, and every
drift is invisible from inside the section that caused it. This file is the counter-check.

Two rules make it worth doing:

- **Review before drafting, not only after.** A contradiction found before you write
  section 9 costs one paragraph. Found after, it costs section 9 and everything that
  cited it.
- **Cheap and always beats thorough and skipped.** The look-back runs every section.
  The full sweep runs every third. Do not swap them around.

## A. Look-back — before drafting each section

Read, in this order, and spend no more than a few minutes:

1. `CONTEXT.md` — the whole file.
2. The previous section's file.
3. Every section named in this section's `Depends on:` line.

Then ask three questions, and only these three:

| Question | If the answer is bad |
|---|---|
| Does the previous section already answer this section's purpose sentence? | Merge them, or narrow this section's purpose. Two sections answering one question is the most common structural defect |
| Does this section need a term the reader has not met yet? | Define it here in one clause, or move this section later. Never assume a later section |
| Did the previous section promise something ("§9 covers the matrix") that is still true? | Fix the promise or fulfil it |

## B. Self-check — after drafting, before the user checkpoint

Never show a section you have not checked. The user is the last line of defence, not
the first.

- [ ] Every component name matches `CONTEXT.md` exactly. Not "roughly".
- [ ] Every claim about behavior traces to a file you read **in this session**, not to
      memory of it. Memory of section 2's code is the least reliable thing you have.
- [ ] **Every diagram edge label is a claim — verify each one separately.** An edge
      says "X sends Y to Z over W". Prose gets reviewed; edge labels get skimmed, so
      they are where wrong assertions survive longest.
- [ ] Every number carries its conditions or a link to them.
- [ ] Nothing is stated more confidently than the evidence supports. "Dormant" needs a
      grep for non-test callers; "streams over ADBC" needs the call site, not a comment
      in a descriptor claiming it does.
- [ ] No link to, mention of, or dependence on an ingested doc. The content is carried in.
- [ ] Every sentence passes the deletion test in `style.md`: removing it would lose a fact.
- [ ] No vague word from `style.md` survives. Every behavior has a named subject and,
      where one exists, its condition and value.
- [ ] The heading number matches the filename.

**Depth checklist — every `Type: mechanism` section, before the checkpoint:**

- [ ] Names the classes and methods that implement the behavior, not just the concept.
- [ ] States the state transitions, with the trigger for each — or says "stateless".
- [ ] Names the thread or pool it runs on, and what is not thread-safe.
- [ ] Lists the config keys it involves, each with its default.
- [ ] States the failure mode and the fallback for it.
- [ ] For a transport section: connection open, pooling, timeout, driver resolution.
- [ ] Could not have been written from the source docs alone. If it could, it is too
      shallow — read the class and redraft, do not approve.

The self-check does not replace the verifier (`verifier.md`). It exists so the verifier
spends its pass on the errors you could not see, not the ones you could.

## C. Sweep — every third approved section, and always before Phase 4

Mechanical checks first. They are exhaustive where a re-read is not.

```bash
cd docs/.techdoc/<slug>

# heading number vs filename — catches every renumber
for f in sections/*.md; do
  n=$(basename "$f" | cut -d- -f1)
  grep -q "^## ${n#0}\. " "$f" || echo "MISMATCH: $f"
done

# duplicate headings across sections
grep -h '^#\{2,4\} ' sections/*.md | sort | uniq -d

# cross-references to sections that do not exist
grep -oh '§[0-9]\+' sections/*.md | sort -u

# links to or mentions of ingested source docs (outside provenance comments)
for d in $(grep -o '^| `[^`]*`' SOURCES.md | tr -d '|` '); do
  sed 's/<!--.*-->//' sections/*.md | grep -n "$(basename "$d")"
done

# terms in CONTEXT.md spelled differently elsewhere
# (run per term; case-insensitive match that is not an exact match)
grep -rin 'sharding.gate' sections/ | grep -v 'ShardingGate'
```

Then, by reading:

| Check | Looking for |
|---|---|
| Contradiction | Two sections making incompatible claims about one component. Resolve against the code, not against whichever you wrote later |
| Duplication | The same mechanism explained twice. Keep the explanation where the reader first needs it; cross-reference from the other |
| Orphan | A term defined in `CONTEXT.md` that no section uses, or used by one section and defined by none |
| Drift from outline | A section that grew a purpose its `OUTLINE.md` entry does not describe. Update the outline or cut the section |
| Unbacked confidence | Anything that reads as certain but was inherited from a source doc without verification |
| Pointing | A sentence that depends on an ingested doc the reader does not have |
| Padding | Sentences that restate a heading, table or diagram; the same idea said twice across sections |
| Shallow mechanism | A `Type: mechanism` section that fails the §B depth checklist — no class names, no config defaults, no failure mode, no thread. Reopen it |
| Unplaced mechanism | A `CODEMAP.md` entry whose `Feeds:` section does not actually carry it, and that is not on the outline's `Deliberately dropped` list |

## D. Renumbering

Renumbering is the single most reliable way to break a finished document, because the
damage is silent and spread across every file.

Never renumber by hand. When sections are inserted, removed, or reordered:

1. Rename the section files.
2. Rewrite the `## N.` heading inside each renamed file.
3. Rewrite every `§N` cross-reference in every section.
4. Rebuild `OUTLINE.md` — regenerate the whole list, do not patch it. A regex that
   edits one entry silently drops another.
5. Rebuild the target doc's table of contents from the section headings.
6. Re-run the sweep in §C. All of it.

## E. Recording what the review found

A drift found and fixed silently will be reintroduced by the next session.

- Fixed a contradiction → one line in `state.json` under `resolved`.
- Settled a spelling or a name → `CONTEXT.md`, so it is settled permanently.
- Found drift you did not fix → `state.json` under `open_questions`, and tell the user.
- Corrected a claim that came from a source doc → the `Conflicts` line of that doc's
  entry in `SOURCES.md`.

Report what the review found at each checkpoint, including when it found nothing.
"Sweep clean" is information. Silence is not.

## F. Metrics

`references/metrics.py` scores the workspace. Run it at every sweep and before Phase 4:

```bash
python3 <skill-dir>/references/metrics.py docs/.techdoc/<slug>
python3 <skill-dir>/references/metrics.py docs/.techdoc/<slug> --verbose   # list the offenders
python3 <skill-dir>/references/metrics.py docs/.techdoc/<slug> --strict    # exit 1 on any gate failure
```

**Gates — a failure is a defect, not a preference.**

| Metric | Gate | Why it is a defect |
|---|---|---|
| `heading_mismatch` | 0 | The `## N.` inside a file disagrees with its filename. Renumbering broke |
| `dangling_refs` | 0 | A `§N` points at a section that does not exist |
| `duplicate_headings` | 0 | Two sections answer the same question |
| `source_links` | 0 | A section links to or names an ingested doc (non-`external`). The output must be self-contained |
| `banned_words` | 0 | Marketing words from `style.md` |
| `vague_words` | 0 | Vague words from `style.md` (various, appropriately, etc.). A sentence without a concrete value |
| `filler_phrases` | 0 | Preambles and filler ("in this section", "in order to", "it is important to note") |
| `unlabeled_edges` | 0 | An unlabeled arrow asserts a relationship without naming it |
| `oversized_diagrams` | 0 | Over 9 nodes / 12 edges (overview) or 14 nodes / 18 edges (a `Type: mechanism` section). Decompose, per `style.md` |
| `mean_sentence_len` | ≤ 20 | `style.md`'s sentence rule, measured |
| `pct_long_sentences` | ≤ 5% | Sentences over 30 words. The mean hides these |

There is no length gate. Length follows from content; padding is caught by
`filler_phrases`, the sentence gates, and the verifier's `PADDING` findings.

**Reported, never gated** — these need judgment a script cannot supply:

- `term_drift` — `ClusterIdentity` the class and "cluster identity" the concept are a
  legitimate distinction. Read `--verbose` output; fix the accidents, keep the rest.
- `cites_per_1k` — a reference section is denser than an overview by design.
- `hedge_per_1k` — one honest "probably" beats a false certainty.

Two rules on gates:

1. **Never loosen a gate to make a document pass.** If a doc fails `pct_long_sentences`,
   the sentences are long. Change the doc, or say plainly that you are not going to.
2. **A gate can still be wrong for a section the user chose.** If the user explicitly
   approved a section that fails a gate, record that in `state.json` under `resolved` and
   report the failure as expected rather than silently exempting it.

Report the metric line at every checkpoint. A number the user never sees changes nothing.
