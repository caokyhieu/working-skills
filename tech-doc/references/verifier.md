# Verifier

The drafter cannot see its own errors: it remembers what it meant, so it reads that
instead of what it wrote. The verifier is a second agent that starts cold. It has the
section, the glossary, and the code — not the drafter's reasoning — and it checks every
claim against the code itself.

Run it on every section, after the self-check and before the user checkpoint
(Phase 3 step 6), and once on the whole document set at assembly (Phase 4 step 5).

## Spawning

- **Claude Code** — the `Agent` tool, `subagent_type: general-purpose`,
  `run_in_background: false` (the checkpoint waits on it). Not `Explore`: it reads
  excerpts, and verification needs whole files.
- **Other harnesses** — whatever spawns a fresh-context agent with file read and shell.
- **No subagent available** — run the pass yourself, but only after re-reading the
  section file and the code from disk, and label the report `self-verified`. Tell the
  user at the checkpoint; it is weaker than an independent pass.

Give the verifier paths, not content, and nothing from your own reasoning. Do not tell
it what you believe the code does — that is the thing under test.

## Prompt — per section

Fill the `<...>` fields and send as-is:

```
You are verifying one section of a technical design document before a human reviews
it. You did not write it. Assume it contains errors; your job is to find them.

Repo root: <abs path>
Section:   docs/.techdoc/<slug>/sections/<NN-slug>.md
Glossary:  docs/.techdoc/<slug>/CONTEXT.md
Code map:  docs/.techdoc/<slug>/CODEMAP.md — entries for this section: <names>
Ingested source docs (the section must NOT reference these): <paths>
Primary code for this section: <paths>

Do not edit the section. Write your report to docs/.techdoc/<slug>/verify/<NN-slug>.md
in the format given in the tech-doc skill's references/verifier.md, and return only
its last line.

1. Claims. List every factual claim the section makes — prose, bullets, table cells,
   diagram edge labels, example values, config defaults. Check each against the code,
   reading whole files rather than grepping one term. Verdict per claim:
   OK          code confirms it; give file:line
   WRONG       code says otherwise; give file:line and what the code does
   UNSUPPORTED no code or measured evidence found; say where you looked
   Numbers from benchmarks are OK only if their run conditions are stated in the section.
2. Self-containment. Flag every link to, mention of, or dependence on an ingested
   source doc, and any sentence a reader cannot understand without one ("as described
   in the design", "see the benchmark report").
3. Precision. Flag VAGUE sentences (no concrete subject, condition or value — "handles
   errors appropriately") and PADDING (restates the heading, a table or a diagram;
   preamble; summary; transition; a mechanism already explained in another section).
   Quote the sentence and give the precise rewrite or "delete".
4. Completeness. For each code-map entry listed above, is it carried by the section?
   For a mechanism section, check: classes and methods named, state transitions with
   triggers, thread/pool, config keys with defaults, failure modes with fallback.
   Anything in the primary code that a reader of this section would need and does not
   get is MISSING.
5. Glossary. Flag any component or term spelled differently from CONTEXT.md.
```

## Prompt — whole document (Phase 4)

Same header, with the assembled main file and companion files in place of the section,
and these checks instead of 1 and 4:

```
1. Contradiction: two places making incompatible claims about one component, value or
   behavior. Resolve against the code and say which one is right.
2. Duplication: the same mechanism explained in two places.
3. Self-containment and precision checks as for a section, across all files.
4. Every internal link (§N, companion file links) resolves.
```

## Report format — `verify/NN-slug.md`

```markdown
# Verify: 07-cache-lifecycle   (round 1, independent)

## Claims
| # | Claim (quoted or paraphrased) | Verdict | Evidence | Fix |
|---|---|---|---|---|
| 1 | SHADOW → WARMING after `promoteThreshold` misses | OK | CacheManager.java:212 | |
| 2 | eviction grace default 30 s | WRONG | CacheConfig.java:41 — default is 10 s | "10 s" |
| 3 | edge `READY -->|drain| DRAINING` | UNSUPPORTED | no DRAINING transition from READY in CacheManager | ask user / remove |

## Self-containment
- L14 "see cache-design.md for the promotion rules" — carry the rules in, delete the link.

## Precision
- VAGUE L22 "errors are handled appropriately" → "`loadEntry` failure returns the entry to SHADOW (CacheManager.java:260)."
- PADDING L3 "This section describes the cache lifecycle." → delete.

## Missing
- `shadowTtlSeconds` (CODEMAP) not mentioned.

VERDICT: fix-required   (1 WRONG, 1 UNSUPPORTED, 1 self-containment, 2 precision, 1 missing)
```

`VERDICT: pass` only when there are no `WRONG`, `UNSUPPORTED`, self-containment or
`MISSING` findings. `VAGUE` and `PADDING` findings alone still require the drafter to
act, but do not block a pass.

## Acting on the report

1. Fix every `WRONG`, `UNSUPPORTED`, self-containment and `MISSING` finding. An
   `UNSUPPORTED` claim is removed, or becomes a question to the user — never kept
   because you remember it being true.
2. Apply every `VAGUE` and `PADDING` rewrite, or reject it with a reason.
3. If you dispute a finding, you need file:line evidence. Write the rebuttal under the
   finding in the report. Do not silently overrule it.
4. Re-verify: spawn a fresh verifier (round 2) on the revised section. At most two
   rounds. Findings still open after round 2 go to the checkpoint and `QUESTIONS.md`.
5. At the checkpoint, report: rounds run, findings per category, what you changed, and
   anything disputed or still open.

Keep every report in `verify/`. A later session that re-opens a section reads its last
report first, so the same error is not reintroduced.
