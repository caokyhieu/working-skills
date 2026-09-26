---
name: conference-radar
description: Catch up on the new research ideas at top ML and AI conferences — fetch the full accepted-paper list of a venue edition (ICLR, ICML, NeurIPS, CVPR, ICCV, ECCV, AISTATS, ACL, EMNLP, NAACL, plus "accepted at" arXiv preprints for venues whose proceedings are not out yet), measure what is rising against the previous edition, cluster the papers by the mechanism they share rather than by topic label, read the representative papers in full, and write a radar report of idea clusters, must-reads, hype checks and idea seeds. Works without a company context or research map. Use when the user asks what is new at a conference, wants to catch up on a venue or a field, asks for the hot topics or trends at ICML/NeurIPS/ICLR/etc., or wants new research ideas from recent papers.
---

# Conference Radar

Answer one question: **what new ideas came out of this venue, and which ones are worth my time?**

The unit is the **idea**, not the paper. A venue with 6,000 accepted papers carries perhaps 10–20 ideas worth knowing; the job is to find them, say how solid each one is, and point to the two or three papers that show it best. Topic labels ("LLM reasoning", "diffusion") are where the search starts, never what the report says: a cluster is named by its mechanism ("RL on verifiable rewards with self-generated curricula").

This skill does not need `company-context.md` or `research-map.md`. When they exist, it tags clusters with the priorities or problems they touch, and the hand-offs at the end feed the rest of the workflow.

## Workspace

```text
radar/
  interests.md                 # standing profile: areas, ideas already known, what to ignore (templates/interests.md)
  <radar-id>/                  # icml-2026, neurips-2025-agents, 2026-h1-efficient-inference
    scope.md                   # venues, editions, interests, depth, audience; confirmed before fetching
    papers.jsonl               # every accepted paper fetched (script-written)
    baseline.jsonl             # previous edition, for trends (optional, script-written)
    shortlist.jsonl            # papers matching the interests (script-written)
    triage.md                  # clusters, members and the pick for each, with reasons
    cards/<paper-id>.md        # one idea card per paper read (templates/idea-card.md)
    radar.md                   # the report (templates/radar-report.md)
    .cache/                    # raw listings; safe to delete
```

Run the script as `python <skill-dir>/scripts/radar.py <command>`. It uses only the standard library. It also uses `curl`, when present, for sites that reject Python's HTTP client.

## 1. Scope (ask before fetching)

Read `radar/interests.md` if it exists; otherwise draft it with the user from [templates/interests.md](templates/interests.md). The profile includes the **ideas the user already knows**, so the report doesn't spend space re-explaining them.

Then agree on:

| Question | Default |
|---|---|
| Venues and editions | the most recent edition of ICLR, ICML and NeurIPS that has taken place, plus "accepted at" arXiv preprints for the next one if its decisions are out |
| Interests | `interests.md` areas; "broad" means the whole venue at skim depth |
| Depth | `standard` |
| Audience | the user alone; a team changes the report's tone and makes it worth publishing |

| Depth | What it produces | Full-text reads |
|---|---|---|
| `skim` | venue at a glance, trends, clusters from abstracts, must-read list | 0 (all cards are `CLAIM-ONLY`) |
| `standard` | all of `skim` + idea cards for the cluster representatives + seeds | 8–15 |
| `deep` | all of `standard` + cross-cluster synthesis, closest-prior check for every card, more seeds | 20–30 |

Write `radar/<radar-id>/scope.md` from [templates/scope.md](templates/scope.md) and **confirm it before fetching**. Read [references/venues.md](references/venues.md) to pick the backend for each venue and to check whether its listing has abstracts.

## 2. Fetch the accepted papers

```sh
R=radar/<radar-id>
python <skill-dir>/scripts/radar.py fetch virtual --conf icml --year 2026 --out $R/papers.jsonl
python <skill-dir>/scripts/radar.py fetch virtual --conf icml --year 2025 --out $R/baseline.jsonl     # for trends
python <skill-dir>/scripts/radar.py fetch acl --volume 2025.emnlp-main --volume 2025.findings-emnlp --out $R/papers.jsonl
python <skill-dir>/scripts/radar.py fetch arxiv --comment "NeurIPS 2026" --max 2000 --out $R/papers.jsonl
```

`fetch` merges into the output and de-duplicates by title, so a paper seen at two venues keeps one record, with the second venue listed under `also`. It prints how many records lack an abstract. Some listings have none (ICLR 2026 and ICML 2026 at the time of writing); for those, filter on titles first and then `enrich` only the shortlist (step 3). Never `enrich` a whole venue.

For a venue with no backend, follow the manual route in `venues.md`: save the accepted-paper page and write records in the same JSON-lines schema, and every later command works on them.

## 3. Triage the whole venue, then shortlist

Look at the whole venue before narrowing to your interests. The shape of the venue is part of the news.

```sh
python <skill-dir>/scripts/radar.py stats $R/papers.jsonl --by topic --coarse
python <skill-dir>/scripts/radar.py stats $R/papers.jsonl --by track
python <skill-dir>/scripts/radar.py trends $R/papers.jsonl --baseline $R/baseline.jsonl --min-count 15
```

`trends` compares the share of papers mentioning each term with the baseline edition. It falls back to titles only when abstract coverage differs between the two sets. A rising term is a **lead to read**, not a finding: check a sample of the matching titles before a term goes into the report, and always report `n` and the method with it.

Turn the interests into public regex terms and filter. Use titles only when the listing has no abstracts:

```sh
python <skill-dir>/scripts/radar.py filter $R/papers.jsonl --any "speculative decod|kv.?cache|quantiz" \
  --none "survey" [--track oral,spotlight] [--titles-only] [--skip radar/<older-id>/shortlist.jsonl] --out $R/shortlist.jsonl
python <skill-dir>/scripts/radar.py enrich $R/shortlist.jsonl      # abstracts + arXiv ids/PDFs where missing
```

Aim for 80–300 papers in the shortlist at `standard` depth. If there are too many, restrict to orals and spotlights first and widen afterwards. If there are too few, loosen the terms, then add synonyms from adjacent communities. `--skip` hides papers an earlier radar already covered.

**Read the shortlist in batches**, with `show --offset N --limit 40`, never by loading the JSON into context. While reading, assign each paper to a cluster in `triage.md`. Follow the rules in [references/reading-ideas.md](references/reading-ideas.md): cluster by mechanism, count independent groups, label maturity, and note hype cues. A paper that fits no cluster goes under *singletons*; one strong singleton can be the most important item in the report.

## 4. Pick and read

For each cluster, pick one to three representatives. Rank the candidates by, in order:

1. **the clearest statement of the mechanism**, meaning the paper that makes the idea easiest to reuse;
2. **evidence cues**: an ablation isolating the idea, tuned baselines, released code, and a stated scope;
3. **venue signal**: an award, oral or spotlight. Verify awards on the venue's awards page; the listing does not carry them;
4. **diversity**: across clusters, prefer different groups and different settings.

Author or lab fame is not a criterion. Record each pick and each notable non-pick with a one-line reason in `triage.md`. At `standard` and `deep` depth, **show the user the cluster list and the picks before reading**; this is the cheapest point for them to redirect.

Read the full text, at least the introduction, method and experiments, then write `cards/<paper-id>.md` from [templates/idea-card.md](templates/idea-card.md). Sources for the PDF, in order: the record's `pdf` field (ACL, arXiv), then the arXiv PDF that `enrich` found, then the paper's project page. OpenReview PDFs need a browser login. If no full text is reachable, write the card from the abstract and tag it `CLAIM-ONLY`. When a paper has already been digested under `scouting/sources/` or `poc/*/sources/`, build the card from that digest.

## 5. Write the radar

Write `radar.md` from [templates/radar-report.md](templates/radar-report.md):

- **TL;DR**: five lines or fewer. Each line is an idea and a verdict, not a topic.
- **The venue at a glance**: size, track split, topic shares and the rising and fading terms, each with `n`.
- **Idea clusters**, most important first. For each: the idea in one sentence, why it works (the mechanism), why now, maturity, evidence quality, representative cards, and which interests or priorities it touches.
- **Must-reads**: at most five, each with why *this* paper rather than another in its cluster.
- **Hype check**: popular directions whose evidence is thin, each with the specific gap.
- **Idea seeds**: see `reading-ideas.md` → Seeds. Each seed gets an observation, the gap, the cheapest test that would tell whether it works, and the cluster it came from.
- **Coverage and gaps**: what was fetched, filtered, read and skipped; listings without abstracts; `CLAIM-ONLY` cards.

## 6. Check, deliver, hand off

Before delivering, check that:

- every cluster names a mechanism, and none is just a topic label or a restated title;
- every number in the report is copied from a card and carries its location; trend figures carry `n` and the method;
- every awards claim links to the venue's page, and no affiliation is guessed;
- `CLAIM-ONLY` cards and our own reasoning (`[inference]`) are marked wherever they are used;
- ideas listed as known in `interests.md` are not re-explained, only updated if something changed.

Give the user the TL;DR and the must-reads in the reply, with the path to `radar.md`. If the audience is a team, offer to publish the report as a page, or to turn the chosen papers into a deck with **lit-review-deck**.

Hand-offs, only when the user picks them:

- a seed or a paper to pursue → **research-poc** (`init`, or **source-digest** first);
- a cluster to track → add its queries and anchor papers to `scouting/watchlist.md` for **source-scout**;
- a team presentation → **lit-review-deck**, reusing the cards.

Finally, append the ideas the user now knows to `interests.md` → *Known ideas*, with the radar id, so the next radar builds on this one.

## Rules

- **An abstract is a claim.** A card says what was read. Anything built only on abstracts is marked `CLAIM-ONLY`, in the card and in the report.
- **Acceptance tier is a signal, not a verdict.** Orals can be wrong and posters can carry the idea of the year. Say which evidence made you rank something high.
- **Counts are leads.** Never write "X grew 7×" without `n`, the method, and a check of the matching papers.
- **Mechanism over topic.** If a cluster's description would fit a session title, it is not finished.
- **No fabrication.** Numbers, awards, affiliations and code links come from the source or they do not appear. Copy numbers exactly, with their table, figure or section.
- **Mind the context budget.** The script does the filtering and counting; read papers in batches of 40 and keep only cluster assignments in `triage.md`.
- **Be polite to the sites.** Listings are cached, arXiv is called at most once every 3 s, and nobody bulk-downloads PDFs of a whole venue.
- **Public terms only.** Filters and queries use generic technical terms; company names, products and `company-context.md` text never leave the workspace.
- Don't start experiments or write proposals here. Hand them off.
