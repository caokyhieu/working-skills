---
name: idea-alignment
description: Map research ideas from source digests onto the company's research problems by matching problem structure (canonical formulation, purpose and mechanism, bridging concepts) rather than vocabulary, write the ground point of each match as an argument that could be rebutted, score and rank the matches for impact, feasibility, effort and risk, and synthesise where the field is moving relative to the company. Use after digesting sources, when deciding which research idea is worth pursuing for the business, or when asked why a paper matters for the company.
---

# Idea Alignment

Find where a source's insight solves a real company problem, say exactly what the shared structure is, and throw out matches that only sound related. A good match names a research-map sub-problem, the relational structure the paper and the problem share, what transfers as-is, what must change, and the condition under which the transfer would fail. The models behind these rules are in [research-poc/references/thinking-models.md](../research-poc/references/thinking-models.md), cited as `[TM-n]`.

Follow the research-poc workspace contract. Read `sources/*/digest.md` (§2b formulation, §5 assumptions, §6 weak spots, §12 hooks), `research-map.md`, `company-context.md` and `scouting/calibration.md` when present. Write `poc/<idea-id>/ideas/alignment.md` using [templates/alignment.md](templates/alignment.md).

## Inputs

`company-context.md` is the only source of company facts; `research-map.md` is the only source of problem formulations. If the map is missing or the relevant problem blocks are `[draft]`, stop and route to research-map: aligning without it degrades to keyword matching. If the context sections you need are `UNKNOWN`, list them and ask. You may draft candidate matches marked `[needs context]`, but the gate cannot pass until the user confirms. Never invent products, data or metrics. Never send company context to public tools.

## 1. Abstract both sides [TM-5]

For each digest, copy its §2b canonical formulation and purpose–mechanism lines into the alignment file. For each candidate research-map problem, copy its formulation. Match on these, not on abstracts or pain-point prose. If a digest lacks §2b, write it now from the digest and mark it `[inference]`; note it in the change log so the digest can be fixed.

## 2. Generate candidates [TM-14]

From three directions, then dedupe, aiming for 3–8 candidates per digest:

1. **Same purpose, different mechanism** [TM-2]: which sub-problem has the same purpose as the paper? The paper is a new way to solve it.
2. **Same mechanism, different purpose** [TM-2]: which sub-problem could reuse the paper's mechanism even though the paper's purpose differs? Use the map's *bridging concepts* and the digest's *same formulation appears in* line [TM-4].
3. **Constraint-first**: where do our binding constraints (map: *what is binding today*) make the paper's trade-off especially valuable or especially harmful?

Check every candidate against the map's near-misses and against `calibration.md`. A candidate that matches a near-miss pattern is listed under *Rejected* with that reason, not silently dropped.

## 3. Write the relevance chain [TM-1, TM-3]

For each surviving candidate:

```
Paper formulation:      <from digest §2b>
Company sub-problem:    R<n>.<x> — <its formulation, from research-map.md>
Shared structure:       <same objective? same binding constraint? same bottleneck quantity?>  ← must be relational, not topical
Transfer distance:      direct | adjacent-field | analogy
Bridging concept (B):   <required when distance ≠ direct> [TM-4]
Transfers as-is:        <mechanism parts that apply unchanged>
Must change:            <parts that depend on an assumption that breaks for us>
Does not transfer:      <parts that are irrelevant or harmful here>
```

If *Shared structure* can only be filled with topic words ("both are about retrieval"), the candidate is rejected with reason `vocabulary-only`. Prefer intermediate distance [TM-3]: a `direct` hit is a reproduction candidate and should say so; an `analogy` hit without a named B is rejected.

## 4. Assumption check

For each paper assumption (digest §5), record company reality (cite `company-context.md` or `research-map.md`) and `holds` / `breaks` / `unknown`. An assumption that breaks is either a reason to reject or the seed of an extension: say which. `unknown` is allowed only when neither file answers it; list what would answer it.

## 5. Ground point [TM-6]

Write the match as an argument the critic can attack:

- **Claim:** mechanism M from <source> improves <metric> for R<n>.<x>.
- **Grounds:** digest §8 results under conditions <C>.
- **Warrant:** the shared structure above; why results under <C> should carry to our regime.
- **Qualifier:** how far this is expected to hold (scale, data, drift).
- **Rebuttal:** the company condition under which it fails (the assumption most likely to break).

One paragraph in this order. A match whose warrant is empty is rejected.

## 6. Score and rank

Score 1–5 with one line each, citing sections:

- **Impact:** size of improvement on a metric the company cares about × reach (products, users, cost)
- **Feasibility:** data access, system access, skills, compute
- **Effort** (5 = low): time to a convincing POC
- **Risk** (5 = low): technical uncertainty, dependency on assumptions, regulatory or licensing issues
- **Strategic fit:** matches a ranked priority via the map's *serves* line, not merely "AI-related"

Feasibility and effort weigh at least as much as novelty [TM-16]. Rank by impact × feasibility, effort and risk to break ties, and show the arithmetic. With more than three matches, settle the top order by **pairwise comparison** with one line per pair [TM-9]; record the pairs. Scores are a discussion aid, not a decision.

Don't pad the list. Three strong matches beat ten weak ones. Keep rejected matches with reasons so they aren't proposed again. Check "initiatives already funded" and "past internal attempts".

## 7. Direction synthesis (when ≥ 3 digests)

Group the digests by sub-problem. For each group, state in a few lines: what the field is converging on, which assumptions all the papers share (a shared assumption that breaks for us is the strongest extension seed), and where the company sits relative to it (ahead, behind, orthogonal). Name 1–3 extension directions per group for idea-extension to start from; this is where "what direction can extend" is answered, before any single paper is chosen.

## Gate

Present the ranked table, the ground point of each top match, and the direction synthesis; ask the user which match(es) to take forward. Record the selection, the user's reason and the date in `alignment.md`; the orchestrator runs stage-critic and records the gate approval. Don't start idea-extension before the user selects.

If the user rejects a match the agent ranked highly, ask for the reason and record it in `scouting/calibration.md` (`scout_log.py override`) so the scout and the critic learn from it.

## Update mode

When the research-poc workflow starts this stage with `mode: update` (a stale or reopened stage, or a `revise` review), follow the update-mode contract in research-poc's `references/workflow.md`:
- Read the previous output, the brief's `why` list and any review it names.
- Make the smallest correct change and leave unaffected content byte-identical.
- Add a Change log entry.
- If nothing needs to change, leave the file untouched and report that.

Report back to the orchestrator; don't mark the stage complete yourself.

For idea-alignment in particular: when `company-context.md` or `research-map.md` changed, re-check each match's relevance chain, scores and assumption table against the changed sections only. Keep the user's previous selection unless the change undermines it, and flag that explicitly. When the trigger is a critic review, address each blocker and major at its location and say in the change log which were addressed and which were disputed, with the reason.
