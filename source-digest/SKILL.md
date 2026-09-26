---
name: source-digest
description: Read a technical source — a top-tier ML, AI, or database paper, an open-source project, or an engineering/technical blog post — and write a structured digest of its key insight, mechanism, assumptions, weak spots, and the exact benchmark protocol and reported results needed to reproduce it. Use when the user shares a paper, arXiv link, GitHub repository, release notes, or blog post to read, summarize, or mine for ideas.
---

# Source Digest

A digest serves two readers later: the agent that proposes an extension, and the agent that reproduces the benchmark. Write it so neither has to reopen the source for the basics, and so everything unknown is clearly marked as unknown. Accuracy beats brevity.

Follow the research-poc workspace contract when it exists. Write to `poc/<idea-id>/sources/<source-id>/digest.md` using [templates/digest.md](templates/digest.md). Without a workspace, write `sources/<source-id>/digest.md` in the current directory. `source-id` is `<author-or-org><year>-<short-title>`, e.g. `leis2018-learned-index`, `duckdb2026-external-agg`, `cloudflare2025-vector-index`.

## Source types

The same template applies to all types. Read [references/reading-guide.md](references/reading-guide.md) for the type-specific reading order, the protocol checklist and the red flags.

| Type | Read | Treat the evidence as |
|---|---|---|
| **Paper** | full text, appendix, supplementary material, official code, newer versions and errata | peer-reviewed but possibly cherry-picked; check baselines and variance |
| **Open-source project** | README, design docs, architecture files, benchmark scripts, changelog and release notes, key source files of the mechanism, issues and PRs discussing it | working code is strong evidence of feasibility; published numbers are usually self-reported and one-off |
| **Technical blog post** | the post, linked code or notebooks, the follow-up discussion, any paper it summarises | anecdotal unless the setup and numbers are reproducible; distinguish marketing from measurement |

Set the **Evidence level** in the header: `peer-reviewed`, `working-code`, `self-reported`, or `claim-only`. Later stages use it to decide how much reproduction is needed.

Read the full source. If only an abstract, README or HTML snippet is available, say so at the top and don't fill protocol sections from memory. Check for a newer version (arXiv v2+, camera-ready, later release) and record the version, commit or post date you digested.

## Writing

- Fill **§2b Purpose, mechanism, canonical formulation** with care: it is the block alignment matches on [TM-2, TM-5 in research-poc/references/thinking-models.md]. Write the formulation as the paper's problem statement would, in generic terms (inputs, outputs, objective, constraints, regime), and name the quantity the mechanism makes cheaper. Then list adjacent fields where the same formulation appears under other names; that line is what lets a paper from another field be found for a company problem. Leave company words out.
- Tag claims: `[src §x / Table y]`, `[code: path@commit]`, `[post: section]` for anything stated, and `[inference]` for your own reasoning.
- Copy numbers exactly with their location. Values read off a plot are marked `(read from plot, ±approx)`.
- Separate the authors' stated limitations from your own critique. Look hard for weak spots: untested regimes, strong assumptions, unreported costs, missing or weakly tuned baselines, benchmarks that favour the method.
- Keep **Protocol gaps** complete. It feeds bench-setup's plan directly. For a repo or post with no benchmark, write the protocol you would need to build and mark it `[inference]`.
- End with **Extension hooks**: 3–6 short leads, each tied to a weak spot or assumption. Company alignment belongs to idea-alignment; don't read `company-context.md` here.

## Multiple sources

For a batch, write one digest per source, then `sources/INDEX.md`: source-id, type, venue/org and date, evidence level, purpose, mechanism, key insight, benchmark, reproducibility (code? data? compute?), most promising hook. Don't rank sources for company fit at this stage.

## Done when

Every template section is filled or explicitly marked `not reported`, reported results are copied with locations, and the version, commit or post date and access date are recorded. If a research-poc workspace exists, report back to its orchestrator, which runs stage-critic on the digest (rubric: numbers spot-checked against the source, formulation not a restated title, weak spots not restated limitations) and records the `digest` stage with `poc_state.py`.

## Update mode

When the research-poc workflow starts this stage with `mode: update` (a stale or reopened stage), follow the update-mode contract in research-poc's `references/workflow.md`:
- Read the previous output and the brief's `why` list. When `why` names a stage-critic review (`review revise: reviews/<stage>-<n>.md`), address every blocker and major at the location it cites, and record in the change log which were fixed and which are disputed, with the reason. Never edit the review file.
- Make the smallest correct change and leave unaffected content byte-identical.
- Add a Change log entry.
- If nothing needs to change, leave the file untouched and report that.

Report back to the orchestrator; don't mark the stage complete yourself.

For source-digest in particular: if a newer version, release or commit is the trigger, record the version change and update only the affected sections (often the protocol and results).
