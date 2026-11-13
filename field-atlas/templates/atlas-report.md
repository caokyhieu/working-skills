# <Field>: map, development and transfers

**Question:** <from scope.md>  **Scope:** <venues · years · tracks>, plus <n> outside-policy papers  **Date basis:** <first_public | proceedings>  **As of:** <YYYY-MM-DD>  **Ontology:** v<n>

## TL;DR

Five lines or fewer, each a finding with its evidence level, not a topic:

1. 
2. 
3. 

## 1. What the area contains

The map, one view per facet. Each view lists the concepts with paper counts and the representative cards. Concepts, not session titles.

### By problem

| Problem | Papers (n) | Main methods | Key assumptions | Representative cards |
|---|---|---|---|---|

### By technique

| Technique / mechanism | Papers (n) | Problems it is used on | Domains | Evidence level |
|---|---|---|---|---|

### By domain and constraint

| Domain | Constraints that bind | Problems | Datasets / environments |
|---|---|---|---|

### Findings that stand

Claims supported by `result` evidence in more than one independent group. Each with card ids and locations.

| Finding | Evidence | Cards | Limits |
|---|---|---|---|

### Contested or thin

Claims with challenging evidence, single-group support, or `claim-only` support.

## 2. How it developed

Changes, not a list of papers by date. Each row is a typed change with its evidence of influence.

| When | Change | Type | Before → after | Influence evidence | Confidence |
|---|---|---|---|---|---|
| | | assumption relaxed / domain move / failure-driven mechanism / evaluation realism / efficiency | <card> → <card> | cites at §x / **sequence only** | |

### Topic activity

`atlas.py share` output for the facets that matter, with n per period, facet coverage, and the venue mix. State the date basis. Rising concepts are leads until a sample of their papers was checked.

## 3. Attention and progress

Four views, never merged into one list. Each prints its weights.

- **Reading priority** (relevance × evidence strength): top 10.
- **Attention** (citations per year, stars per year of verified repositories):
- **Momentum** (recent change in stars and citations; topic-share change):
- **Progress** (comparable benchmark results under matched protocols):

### Attention without progress

Directions with high attention or momentum and thin or contested evidence, each with the specific gap.

## 4. Transfer shortlist

`atlas.py rank --view transfer`. For each hypothesis: the one-sentence transfer, the strongest gap, the prior-art verdict, the experiment and its rejection criterion. Link to `hypotheses/H-<n>.md`.

| Hypothesis | Source → target | Prior art | Biggest gap | Cheapest test | Rejection criterion |
|---|---|---|---|---|---|

## 5. Coverage and limits

- Collected: <n per venue-year-track>; outside policy: <n citation, n search>.
- Dated: <n first_public>; reviews: <n with public scores> of <n> in OpenReview venues; verified repositories: <n>.
- Facets assigned: <n> (<%>); cards: <n> (full <n>, partial <n>, abstract-only <n>).
- Extraction audit: <rate supported> on <n> rows (`eval/extraction-audit-<date>.md`), or "not yet run".
- Known gaps: venues not covered, listings without abstracts, renamed concepts, periods with n < 30.
