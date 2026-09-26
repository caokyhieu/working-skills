---
name: research-map
description: Build and maintain research-map.md, the bridge between company priorities and the language of research papers — one canonical problem formulation per priority, with purpose and mechanism, sub-problems, bridging concepts to adjacent fields, anchor papers, near-miss examples and the acceptable transfer distance. Use before scouting or aligning papers, when the company direction changes, or when the agent keeps surfacing unrelated papers or misses why a paper matters.
---

# Research Map

`company-context.md` says what the company needs in business terms. Papers say what they do in problem terms. The research map translates one into the other once, with the user, so that scouting, alignment and extension match on **problem structure** instead of vocabulary [TM-1, TM-2, TM-5 in research-poc/references/thinking-models.md].

Write `research-map.md` at the workspace root from [templates/research-map.md](templates/research-map.md). Agents propose entries; the user confirms every problem block before it is used. Never invent company facts: every "serves" and "what is binding" line cites a `company-context.md` section.

## 1. Read the context

Read `company-context.md` fully: priorities, products and pain points, data assets, constraints, what counts as a win, past attempts. List which sections are `UNKNOWN`; if priorities or pain points are unknown, stop and ask — the map cannot be built from guesses.

## 2. Draft one problem block per research problem

For each ranked priority and each measured pain point, propose a research problem R*n*:

1. **Purpose** — what a solution is *for*, in one sentence a domain outsider understands [TM-2].
2. **Canonical formulation** — inputs, outputs, objective, constraints, regime [TM-5]. Write it the way a paper's problem statement would, with no company nouns. This is the field that gets matched later, so make it precise: "minimise p99 latency of top-k retrieval over 10⁸ vectors under 8 GB RAM with hourly inserts" is usable; "make search faster" is not.
3. **What is binding today** — the one constraint that actually limits the product now. A paper that relaxes a non-binding constraint is a near-miss.
4. **Mechanisms already in use or tried** — so the scout can recognise "same-purpose, different-mechanism" hits [TM-2] and skip what failed internally.
5. **Sub-problems** — 2–5, each a smaller formulation. Sources are matched at sub-problem level.
6. **Same formulation appears in / bridging concepts** — the names adjacent fields use for the same structure, and the quantities or structures a paper might share without naming our problem [TM-4]. This is where cross-domain hits come from; spend real effort here and use web search on the public terms if available.
7. **Acceptable transfer distance** — `direct`, `adjacent-field` or `analogy` [TM-3]. Default: accept up to `adjacent-field`; allow `analogy` only for problems where known mechanisms have plateaued.
8. **TRL band wanted** [TM-8].
9. **What counts as a win** — copied from `company-context.md §6`, per metric.
10. **Public search terms** — 3–8 generic phrases with synonyms from adjacent communities. No company names, products, metrics or internal numbers.
11. **Anchor sources** — ask the user for 3–10 sources that define "on-direction" for this problem. If the user has none, propose candidates from the search terms and let the user pick. Anchors drive citation-graph scouting.
12. **Near-misses** — at least 2 per problem: things that would score high on keywords and are wrong, with the reason. Ask the user: "what has the agent (or a colleague) suggested before that was off?"

Two problems that share a mechanism should say so in *Cross-problem notes*; a source may serve both.

## 3. Confirm with the user

Present each block and ask the user to confirm, edit or drop. Record the confirmation date. Do not proceed to scouting with unconfirmed blocks; mark them `[draft]`.

## 4. Maintain

The map changes when:

- `company-context.md` changes → re-check the *serves* and *what is binding* lines of affected problems; the research-poc orchestrator marks `aligned` stale automatically because `research-map.md` is one of its inputs.
- The user overrules a scouting or alignment verdict → source-scout writes the rule to `scouting/calibration.md`; when a rule generalises, fold it into the problem's near-misses or bridging concepts here and note it in the change log.
- A promoted idea finishes → add what was learned about the formulation (e.g. "regime assumption X was wrong") under the problem.

Keep problem ids stable. Retire instead of renumbering.

## Rules

- Formulations use public, generic terms; company facts live only in the *serves* / *binding* / *win* lines, which cite `company-context.md`. When in doubt about whether a phrase is confidential, ask.
- A block without anchors and near-misses is incomplete; say so rather than silently shipping it.
- Don't rank problems here; priority order comes from `company-context.md`.
