---
name: field-atlas
description: Build a persistent, evidence-backed atlas of a research field from selected peer-reviewed venues plus citation-following — papers with versions, dates, reviews, repositories and citations kept with provenance; overlapping facets by domain, problem, technique, setting and constraint; per-paper extraction cards on a shared ontology of problems, methods, mechanisms, assumptions, claims and evidence — then explain how the field developed (changes with evidence of influence, not chronology), keep attention, momentum and progress separate, and propose testable cross-domain transfers with a structural mapping, compatibility checks, a prior-art search and an experiment with a rejection criterion. Use when the user wants to map a research area over several years, understand how it evolved, find what is gaining attention versus making progress, compare two fields, or find techniques that could transfer from one field to another. For a quick catch-up on one conference edition use conference-radar instead.
---

# Field Atlas

Answer four different questions, and never let one answer stand in for another:

| Question | Output |
|---|---|
| What does this area contain? | a map of problems, methods, assumptions, datasets and findings, by several facets |
| How has it developed? | a timeline of **changes**, each with its evidence of influence |
| What is gaining attention or making progress? | separate views: reading priority, attention, momentum, progress |
| What could transfer between areas? | hypotheses with a structural mapping, compatibility gaps, prior-art check and an experiment |

A highly ranked paper, a growing topic and a promising transfer are different things. The design rests on one idea: cross-domain discovery needs the **structure of the problem** and the **assumptions of the technique**, not topic labels [TM-1, TM-2]. So cards record problems, mechanisms and assumptions as shared ontology concepts, and transfers are proposed from those.

Rules from [research-poc/references/thinking-models.md](../research-poc/references/thinking-models.md) are cited as `[TM-n]`.

## Workspace

```text
atlas/
  ontology.md            # shared schema + concepts, versioned (seeded from references/ontology.md)
  playbook.md            # procedural memory: validated rules only
  hypotheses/H-nnn-*.md  # hypothesis store (templates/transfer.md)
  graph.jsonl            # compiled from all cards (generated)
  bridges.md, changes.md # transfer leads, development candidates (generated)
  eval/                  # extraction audits and other stage checks
  <field-id>/
    scope.md             # contract, venue policy, rubrics (templates/scope.md); confirmed before fetching
    papers.jsonl         # evidence store (script-written; never edit by hand, use `set`)
    raw/                 # fetched listings, OpenReview dumps, search results
    fulltext/            # PDFs or text you saved
    cards/<paper-id>.md  # extraction cards (templates/card.md)
    log.md               # episodic memory: searches, extraction failures, outcomes
    atlas.md             # the report (templates/atlas-report.md)
```

Run `python <skill-dir>/scripts/atlas.py <command>` (standard library only; `--root` changes the workspace). One atlas holds several fields; the ontology is shared so fields can be compared.

## Depth

| Depth | Collection | Cards (full text) | Transfer |
|---|---|---|---|
| `skim` | one venue series, 2–3 years, facets from abstracts | 0–5 | leads only |
| `standard` | 2–4 venues, 3–5 years, + citation-following from 5–10 anchors | 15–30 | 2–4 hypotheses with prior-art checks |
| `deep` | as standard, + workshops / findings, reviews, repos, two observation rounds | 40–80 | full shortlist, extraction audit, backtest |

## 1. Scope (ask before fetching)

Run `atlas.py init --field <field-id>`. Read `atlas/playbook.md`. Then agree on the contract and write `scope.md`: the question, what the answer is for, the venue policy (venue, years, tracks in and out, proceedings dates), outside-policy routes (anchors for citation-following, alias queries), review rubrics, time range, date basis, depth, budget, and which other fields or target problem the transfers should connect to. If `research-map.md` exists, a target problem can be one of its R-problems. **Confirm the scope before fetching.**

On the first run, walk the user through `ontology.md` §2–§5: keep, rename or retire the seed concepts, add the problem and technique concepts the question needs, and mark it confirmed.

## 2. Collect the evidence store

Follow [references/evidence.md](references/evidence.md):

1. Fetch each venue edition into `raw/` with conference-radar's `radar.py`, one file per edition, and `ingest` each with `--proceedings-date`. Ingest merges arXiv, proceedings and OpenReview versions of the same paper into one record and keeps every venue appearance.
2. Follow citations and alias searches outside the venues with source-scout's `scholar_search.py`; ingest with `--via citation` or `--via search`.
3. `dates` (arXiv v1 first-public dates), `reviews` (OpenReview, needs a login in the environment), `cites` (Semantic Scholar). Verify repositories before recording them (`set ... repo.status=official repo.evidence=...`), then `repos`.
4. Log every search in `log.md`. Run `status` and report coverage to the user.

Missing values stay missing. Acceptance is evidence about a paper, not proof of its claims.

## 3. Classify along several facets

Read the collection in batches (`show --offset N --limit 40 --abstracts`), never by loading the JSON. For each paper, assign overlapping facet values — domain, problem, technique, setting, constraint — and a 0–3 `relevance` to the question, as JSON lines (`{"id": ..., "domain": [...], "problem": [...], ..., "relevance": 2}`) imported with `atlas.py facets <file> --field F`. A paper usually belongs to several groups; assigning it only a domain hides exactly the connections transfer needs.

Name problem concepts by structure, without domain nouns [TM-5]. When no concept fits, do not invent one in place: note it, finish the batch, and propose concepts through ontology.md §6. Facets are revisable; re-import when the ontology changes.

If embeddings are available in the environment, use them to propose candidate groups; the facets, not the clusters, are what get recorded, because they say *why* papers belong together.

## 4. Extract cards

Choose papers with `rank --view reading` plus coverage: every important problem concept and every candidate transfer needs at least one carded paper on each side. At `standard` depth and above, **show the user the reading list before reading.**

Read the full text and write `cards/<paper-id>.md` from [templates/card.md](templates/card.md): entities with ontology concepts and source locations, relations, ontology gaps, an evidence verdict. Every Claim and Evidence row has a location and a kind (`assertion` = the authors say so; `result` = an outcome you can point to). Record `builds-on` / `contrasts-with` edges to earlier papers with the citing sentence's location: they are the only evidence of influence. Abstract-only reads are `read: abstract`, `evidence: claim-only`.

Run `atlas.py check` after each batch and fix what it reports. Log extraction failures in `log.md`.

## 5. Measure attention and progress, separately

`rank --view reading | attention | momentum` (weights are printed; copy them into the report), `share` for topic activity. Read [references/evidence.md §6–§7](references/evidence.md) first. Progress is judged only from comparable benchmark results under matched protocols, taken from cards, never from stars or citations. Directions with attention but thin evidence go under *Attention without progress*.

## 6. Explain the development

Read [references/development.md](references/development.md). `atlas.py graph` then `atlas.py changes` proposes candidate events: techniques entering new domains, assumptions relaxed, evaluation settings changing. Confirm each in the papers. The timeline lists changes by type, each with `influence: <card, location>` or **sequence only**. Report topic shares with n, facet coverage, the venue mix and the date basis.

## 7. Propose transfers

Read [references/transfer.md](references/transfer.md). `atlas.py bridges` lists methods recorded on a problem in one domain and not in another, with the method's assumptions. For the most promising leads (and any the user brings):

1. map the roles of the shared problem structure, source to target;
2. check every required assumption and the usual breaks; score compatibility;
3. run the prior-art loop with every alias; an absent link in the atlas is a search lead, not a discovery;
4. write `hypotheses/H-nnn-<slug>.md` from [templates/transfer.md](templates/transfer.md), with an experiment and a rejection criterion fixed in advance.

`rank --view transfer` orders them. Present the shortlist and let the user choose which to pursue. A hypothesis that turns out to be `known` is a result; record what the existing work found.

## 8. Report and hand off

Write `atlas.md` from [templates/atlas-report.md](templates/atlas-report.md). Before delivering, check that:

- every map entry and finding cites cards with locations; `claim-only` and `[inference]` are marked where used;
- the four rankings are separate and show their weights; trend figures carry n, coverage and the date basis;
- every timeline change says influence or sequence only;
- every hypothesis has a prior-art verdict, its gaps and a rejection criterion, and is labelled as a hypothesis.

Give the user the TL;DR, the top changes and the transfer shortlist in the reply, with the path. If the audience is a team, offer to publish the report as a page.

Hand-offs, when the user picks them: a hypothesis to develop → **idea-extension** (novelty loop, Heilmeier) inside **research-poc**; an experiment → **bench-setup**; a paper to read in depth → **source-digest**; a cluster to watch → `scouting/watchlist.md` for **source-scout**; a deck → **lit-review-deck**. When `research-map.md` exists, offer new bridging concepts and aliases to its problem blocks; **research-map** owns that file.

## 9. Learn from the run

Read [references/learning.md](references/learning.md). Record investigation outcomes and hypothesis status changes in `log.md`. When a failure pattern repeats, propose a playbook rule and test it on held-out cases before adopting it. At `deep` depth, run `atlas.py audit` and have someone other than the card author check it.

## Rules

- **Four questions, four answers.** Never present attention, momentum, quality and transfer potential as one score. Any combined score shows its weights.
- **Provenance or nothing.** Dates, scores, stars and citations carry their source and observation date. Missing stays missing; never fill from memory.
- **Sequence is not influence.** "B developed from A" needs a citing location in a card.
- **Counts are leads.** No trend without n, coverage, date basis and a check of the matching papers.
- **Hypotheses are not knowledge.** They live in `hypotheses/`, are labelled as such wherever they appear, and never become findings without an experiment or a paper.
- **No novelty from memory.** An absent link is a lead; novelty needs the prior-art loop.
- **Ontology changes go through the user**, with a version bump when types, relations or names change. Never add a concept silently from a card.
- **Mind the context budget.** The script stores, merges and counts; read papers in batches of 40.
- **Public terms only** in searches. `company-context.md` content and internal facts never leave the workspace.
- **Be polite to the sites.** Cache listings, keep arXiv calls 3 s apart, never bulk-download a venue's PDFs.
