---
name: source-scout
description: Find and screen candidate sources for the company when there is no starting paper — expanding the citation graph from the research map's anchor papers and querying top-tier ML, AI and database venues, arXiv, open-source projects and technical blog posts by problem formulation, then screening each hit with a relevance chain (which research problem, what shared structure, how far the transfer) rather than a topic label; keeps a watchlist, a calibration file of the user's overrules, and a record of everything screened so reruns surface only new items. Use when the user asks what to work on next, wants new ideas, asks to scout or scan for papers, repos or posts, or wants a recurring research radar.
---

# Source Scout

Produce a short, screened list of sources worth digesting, each tied to a research-map problem by structure, not by keywords. A candidate is worth keeping when its formulation shares an objective or binding constraint with a sub-problem in `research-map.md`, its evidence can be checked, and it could become an experiment on a known benchmark. The user chooses which candidates go forward; the scout never starts an idea on its own. The rules come from [research-poc/references/thinking-models.md](../research-poc/references/thinking-models.md), cited as `[TM-n]`.

Sources are papers, open-source projects (repos, releases, design docs) and technical blog posts. Treat them with the evidence hierarchy in source-digest: peer-reviewed > working code > self-reported > claim-only.

## Workspace

Scouting lives at the workspace root and is shared across ideas:

```text
company-context.md
research-map.md         # problem formulations, anchors, near-misses (research-map skill)
scouting/
  watchlist.md          # sub-problems → queries, venues, orgs, feeds; written with the user
  calibration.md        # rules from the user's overrules (scout_log.py override); read before every screen
  screened.jsonl        # append-only record of every source seen, with verdict and relevance chain (script-managed)
  runs/<YYYY-MM-DD>.md  # one report per scouting run
  reviews/<date>-shortlist.md   # stage-critic review of the shortlist
  candidates.md         # current shortlist awaiting the user's pick (regenerated each run)
  sources/<source-id>/digest.md   # digests of picked candidates (source-digest)
  alignment.md          # cross-candidate ranking and direction synthesis (idea-alignment)
```

Create the folder and copy [templates/watchlist.md](templates/watchlist.md) on first use (`scripts/scout_log.py scouting init`). Use `scout_log.py` for every read or write of `screened.jsonl` and `calibration.md`; don't edit them by hand.

## 0. Require the research map

Read `research-map.md`. If it is missing or the problems you would scout for are `[draft]`, stop and route to **research-map**. Scouting from `company-context.md` priorities alone produces keyword hits, which is the failure this skill exists to avoid. Read `scouting/calibration.md` (`scout_log.py scouting rules`) and keep its rules in view while screening.

## 1. Build or refresh the watchlist

One row per **sub-problem** (R*n*.x), not per priority: the sub-problem's public search terms from the map, 2–4 queries with synonyms from adjacent communities (the map's *same formulation appears in* line), the anchors, and the near-misses as exclusions. Never put company names, product names, internal metrics or `company-context.md` text into a query. Read [references/sources.md](references/sources.md) for default venues, indexes and feeds per field. Confirm the watchlist with the user the first time and whenever the map changes.

## 2. Scan — anchors first, then queries

For each sub-problem, in this order:

1. **Citation-graph expansion from anchors** [TM-4]: `scripts/scholar_search.py anchors --map research-map.md --problem R<n> --edge citations --since <year>` and again with `--edge recommendations`. Anchors define "on-direction"; their citers and neighbours are the densest source of relevant work and of cross-field bridges. Record `--via <anchor>` when screening these.
2. **Formulation queries**: `scholar_search.py search --query "<terms>" --since <year>` for each watchlist query, plus the web-search tool for open-source projects and blog posts. Cover all three source types every run; a run that returns only papers is incomplete unless the watchlist excludes the others.
3. **Bridging-concept queries**: one query per bridging concept in the map's problem block, aimed at fields that don't use our vocabulary. This is where `adjacent-field` hits come from; expect low precision and skim fast.

Window: last 90 days on a first run, otherwise since the previous run date (`scout_log.py scouting last-run`). Check each hit against `screened.jsonl` first (`scout_log.py scouting seen <url-or-id>`) and skip anything already recorded unless it has a materially new version.

## 3. Screen in two passes

Read [references/screening.md](references/screening.md).

**Pass 1 (cheap, wide):** from title and abstract, drop anything with no plausible formulation overlap or that matches a near-miss or calibration rule. Record drops with a one-line reason; they prevent re-screening.

**Pass 2 (narrow):** for the survivors, write the **relevance chain** — sub-problem id, shared structure (objective / binding constraint / bottleneck quantity), transfer distance, bridging concept when the distance is not `direct`, estimated TRL [TM-1, TM-3, TM-8]. Then score evidence, reproducibility, novelty potential and effort. `fit` is derived from the chain (screening.md), not guessed. A keep whose shared-structure line contains only topic words is a `maybe` at best.

```sh
python <skill-dir>/scripts/scout_log.py scouting add --id <source-id> --type paper|oss|blog --url <url> \
  --title "..." --venue "..." --date YYYY-MM-DD --topic <watchlist-row> --verdict keep|maybe|drop \
  --problem R1.a --distance direct|adjacent-field|analogy --structure "<shared objective / constraint>" \
  [--bridge "<concept B>"] [--trl N] [--via <anchor-id>] \
  --fit N --evidence N --repro N --novelty N --effort N --reason "..."
```

The script refuses a `keep` without `--problem`, `--distance` and `--structure`, and without `--bridge` at non-direct distance.

Aim for quality and spread [TM-16]: 5–10 keeps per run across several sub-problems and mechanisms is a good outcome; 8 variants of one idea or 40 unscreened links is not. When more than 5 keeps compete, settle the order by pairwise comparison with one line per decided pair [TM-9], recorded in the run report.

## 4. Critique, report and hand off

Run **stage-critic** on the shortlist with the `screened` rubric (it re-derives formulations for each keep, samples drops for false negatives, and checks near-misses). Address blockers before showing the user; keep its meta-review for `calibration.md` if it generalises.

Write `scouting/runs/<date>.md` from [templates/run-report.md](templates/run-report.md) and regenerate `scouting/candidates.md` (`scout_log.py scouting candidates --write`). Present the shortlist grouped by sub-problem, each with its relevance chain, and ask the user which candidates to digest.

**When the user disagrees with a verdict**, record it: `scout_log.py scouting override --id <id> --verdict <their verdict> --reason "<their words>" --rule "<the generalisable rule>"`. The rule lands in `calibration.md`, is read on every future screen, and is folded into the research map when it generalises. This is the loop that stops the same mistake recurring.

For picked candidates:

1. Run source-digest on each into `scouting/sources/<source-id>/`, plus `scouting/sources/INDEX.md`.
2. Run idea-alignment across those digests into `scouting/alignment.md` (includes the direction synthesis).
3. When the user selects a match, create the idea with the research-poc promotion command, which copies the digest and alignment into the new `poc/<idea-id>/` and records those stages as completed:

```sh
python <research-poc-dir>/scripts/poc_state.py poc/<idea-id> promote --from scouting --source <source-id> --by <user>
```

Then mark the candidate as promoted: `scout_log.py scouting promote --id <source-id> --idea <idea-id>`.

## Recurring use

"Scout again" or a scheduled run repeats steps 2–4 with the same watchlist and reports only new items. Keep run reports short: what was scanned, how many seen, kept and dropped, the shortlist with chains. Revisit `maybe` items when a newer version, code release or independent benchmark appears, or when a new calibration rule or bridging concept would change their chain.

## Rules

- Public queries only. No company context leaves the workspace; the research map's *public search terms* are the only phrases that go into a query.
- A keep names a sub-problem and a shared structure or it is not a keep.
- Prefer intermediate distance [TM-3]: a `direct` hit on an anchor's topic is often a reproduction candidate; say so. An `analogy` without a named bridging concept is a drop.
- Record drops with reasons so the same source is not re-screened next run.
- Don't rank on hype: stars, likes or vendor claims are weak evidence. Prefer working code and independent measurements.
- A `claim-only` source can be kept only if the claim is checkable with a feasible experiment; say what that experiment is.
- Don't start research-poc ideas, run experiments or write proposals from the scout. Hand off through the promotion command.
