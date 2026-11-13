# Evidence store: collection, provenance and signals

Read before collecting (SKILL.md §2) and before ranking (§5).

## 1. Why provenance

Without it the agent counts one paper twice (arXiv and proceedings), dates it by the wrong version, or credits it with stars from someone else's repository. Every field in `papers.jsonl` therefore says where it came from, and anything not observed stays missing.

## 2. The paper record

`atlas.py ingest` writes one canonical record per paper and merges versions into it. Match keys, in order: arXiv id (without version), DOI, OpenReview forum id, ACL id, normalised title.

| Field | Content | Filled by |
|---|---|---|
| `id` | stable canonical id (first one seen; never renumbered) | ingest |
| `ids` | arxiv, doi, openreview, acl, s2 | ingest, reviews, cites |
| `versions[]` | every public version: kind, label, url | ingest |
| `appearances[]` | venue, year, track, status (`accepted`, `claimed`, `rejected`, `withdrawn`, `unknown`), source | ingest; one per venue-track, so a workshop paper later at the main conference keeps both |
| `collected_via` | `policy` (in the scope's venue policy), `citation`, `search`, `user` | ingest `--via` |
| `first_public` | date and source (arXiv v1 preferred) | `dates`, or `set` with a source |
| `proceedings_date` | date the proceedings appeared (conference start) | ingest `--proceedings-date`, or `set` |
| `reviews[]` | per venue: review group, score field, scale, raw scores, confidences, decision, retrieval date, source | `reviews` |
| `repo` | url, status (`official`, `claimed`, `unverified`, `none`), evidence (where the link was found) | `set` after verification |
| `repo_obs[]` | dated observations: stars, forks, created, pushed, shared_with | `repos` |
| `citations[]` | dated counts with source | `cites`, or ingest of scholar_search records |
| `fulltext` | PDF url or local path under `fulltext/` | ingest, `set` |
| `facets`, `facets_by`, `relevance` | overlapping facet values, who assigned them, 0–3 relevance to the question | `facets` |
| `notes[]` | dated free text | `set ... note=...` |

## 3. Collecting

**Venue policy first.** Fetch each venue edition into its own raw file so track identities survive, then ingest it:

```sh
RADAR=<conference-radar-dir>/scripts/radar.py
python $RADAR fetch virtual --conf iclr --year 2025 --out atlas/<field>/raw/iclr-2025.jsonl
python <skill-dir>/scripts/atlas.py ingest atlas/<field>/raw/iclr-2025.jsonl --field <field> --proceedings-date 2025-04-24
```

conference-radar's `references/venues.md` lists the backends, which listings lack abstracts, and the manual route for venues without one. Keep its rules: never bulk-download PDFs, keep arXiv calls 3 s apart. If conference-radar is not installed, write records in its JSON-lines schema by hand from the venue's accepted-paper page.

Workshops, findings and other tracks are ingested from their own listings; they keep their own `appearances` entry. The scope decides which tracks count.

**Then beyond the venues.** The venue list must not become the boundary of discovery. Use source-scout's `scholar_search.py` (Semantic Scholar):

```sh
SS=<source-scout-dir>/scripts/scholar_search.py
python $SS expand --id arXiv:<anchor> --edge references --limit 50 --abstract > atlas/<field>/raw/refs-<anchor>.jsonl
python <skill-dir>/scripts/atlas.py ingest atlas/<field>/raw/refs-<anchor>.jsonl --field <field> --via citation
python $SS search --query "<alias from ontology.md>" --since 2020 --abstract > atlas/<field>/raw/search-<slug>.jsonl
python <skill-dir>/scripts/atlas.py ingest atlas/<field>/raw/search-<slug>.jsonl --field <field> --via search
```

Log every search in `log.md` → Searches (query, route, hits, kept). Outside-policy papers are read and carded like any other, but they are not counted in topic shares, which need a known denominator.

**Dates.** `atlas.py dates --field F` fills `first_public` from arXiv v1. For papers with no arXiv version, the first public date is the OpenReview submission date (if public) or the proceedings date; set it with `set <id> first_public.date=... first_public.source="..."`. Never guess a date.

## 4. Reviews (OpenReview)

OpenReview exposes submissions, reviews, meta-reviews and decisions for many ML venues, but what is public differs by venue and year, and anonymous API clients are usually refused (HTTP 403). The script logs in with `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD` (or `OPENREVIEW_TOKEN`); a free account works for public records.

```sh
python <skill-dir>/scripts/atlas.py reviews --field F --venue-id ICLR.cc/2025/Conference \
  --review-group main --scale "1,3,5,6,8,10" --save atlas/F/raw/openreview-iclr-2025.json
```

- Venues from 2024 on use API v2 (default). Older venues use `--api https://api.openreview.net`; if the submission invitation is named differently, pass `--invitation` (e.g. `ICLR.cc/2023/Conference/-/Blind_Submission`).
- The score field differs by venue (`rating`, `recommendation`, `overall_assessment`, ...); the script tries the common names, or pass `--rating-field`.
- Look up the rubric scale in the venue's reviewer guide and pass `--scale`; record it in `scope.md` → Review rubrics. Without a scale, scores are kept but not normalised.
- If the API is unreachable, save the notes JSON another way (e.g. `openreview-py` in a logged-in session) and use `--from-file`.
- **Missing stays missing.** No public reviews means `scores: []`; never fill it from a forum thread, a tweet or a guess.
- `--save` keeps the raw response for provenance.

## 5. Repositories

A repository counts only after it is **verified**: linked from the paper itself, the OpenReview page, the proceedings page or the authors' project page. Record where:

```sh
python <skill-dir>/scripts/atlas.py set --field F <paper-id> repo.url=https://github.com/o/r repo.status=official repo.evidence="paper p.1 footnote"
python <skill-dir>/scripts/atlas.py repos --field F          # dated star observation for every official repo
```

Papers-with-code-style links and search results are `claimed` until checked. A repository shared by several papers (a lab's monorepo, a library) is flagged: its stars say nothing about any one paper. Run `repos` again later to get a second observation; growth needs two.

## 6. Signals: what each can and cannot say

| Signal | What it can indicate | Main limitation | Where it is used |
|---|---|---|---|
| Review scores | Reviewer assessment under one venue's process and rubric | Scales, standards and calibration differ across venues and years; reviewers disagree | reading priority (as a z-score within its review group) |
| Acceptance tier | The venue's decision | Not a verdict on every claim | reported, not scored |
| GitHub stars | Repository attention | Not correctness, not use; age-dependent; shared repos | attention, momentum |
| Citations | Scholarly attention | Older papers had more exposure; self-citation; citing to disagree | attention (per year since first public), momentum |
| Independent replications | Support under additional evaluations | Sparse | evidence verdict in cards |
| Comparable benchmark results | Progress on a specified evaluation | Protocols, compute and tuning differ | progress (report section 3), only with matched protocols |

## 7. Rankings

There is no single ranking. `atlas.py rank` produces four views; each prints its weights, uses percentiles within the field, and lists missing components rather than counting them as zero.

| View | Question | Default components and weights |
|---|---|---|
| `reading` | What should be read next for this question? | relevance 0.5 (assigned at triage), evidence 0.3 (card verdict), review 0.2 (z within review group) |
| `attention` | What is being looked at? | citations per year 0.6, stars per year (official repos) 0.4 |
| `momentum` | What is changing now? | star growth per 30 days 0.5, citation growth per 30 days 0.5 (both need two observations ≥ 7 days apart) |
| `transfer` | Which hypotheses are worth testing? | compatibility 0.4, evidence 0.3, adaptation cost 0.3; sorted by prior-art verdict first |

Change weights with `--weights` when the question calls for it, and copy the printed weights into the report. Topic-level momentum comes from `share` (change in share between periods), not from this command.

**Normalising review scores.** The group is the set of papers reviewed under one process and rubric: venue, year, review group (the main track; a separately reviewed datasets-and-benchmarks track or workshop is its own group), score field and scale. Do **not** normalise within acceptance tiers (oral, spotlight, poster): tiers are decided from the scores, so normalising within them removes the signal. `reviews` stores the group's mean and spread over **every scored submission** in the dump, accepted or not, so a paper is compared with its whole review pool rather than with the papers you happened to collect; when no stored statistics exist, the collection's own papers are used, and groups with fewer than 10 scored papers get no z-score. Always keep the raw scores and the spread (disagreement) next to any normalised value.
