# Scanning for a review deck

The deck's promise is "this is what is new". That makes recency a filter, not a preference.

## Window rule

- Default window: **the last 12 months from today**. Take the publication or last-revision date, whichever the audience would call the paper's date: arXiv v-latest date, camera-ready date, release tag date, post date.
- A paper first posted 18 months ago whose v3 landed last month is **in**, and the slide says what v3 changed.
- A famous older paper is **out** as a slide of its own. It may appear as one line of context inside a newer paper's slide ("extends <older work> by …") or on a single framing slide before the poster slides.
- State the window on the title slide and in `brief.md` (`window: 2025-10-01 → 2026-09-17`), and say how many candidates were dropped for being outside it.

## Where to look

Use the venue, project and blog lists in [source-scout/references/sources.md](../../source-scout/references/sources.md). For a 12-month window the highest-yield entries are:

- **Papers**: the last edition of each top venue (NeurIPS, ICML, ICLR, KDD, ACL/EMNLP, CVPR, MLSys; SIGMOD, VLDB, ICDE, CIDR, EDBT; OSDI, SOSP, NSDI, ATC, EuroSys) plus arXiv listings for the relevant categories. Check industry tracks and best-paper lists separately: they carry deployment evidence, which reads well in a review.
- **Blogs and releases**: engineering blogs of the systems the company runs or competes with, release notes of the same, independent benchmark write-ups.
- **Forward links**: "cited by" and "related" from the sources already kept, restricted to the window.

## Query construction

Per theme, write 2–4 public queries: the problem phrasing, the technique phrasing, and a constraint phrasing (latency, memory, cost, privacy). Record the queries in `brief.md` so the next review can reuse them. Never put company, product or internal metric names in a query.

## Screening

Score with the rubric in [source-scout/references/screening.md](../../source-scout/references/screening.md). Its relevance chain (which problem, what shared structure, transfer distance) is what fills the block's "for us" line, so write it for every keep:

- **With `research-map.md`:** use the sub-problem id (`R1.b`), the map's formulation and its bridging concepts, exactly as the scout does.
- **Without a map:** use the theme id from `brief.md` as the problem, and write the shared structure in the theme's own terms (same objective or same binding constraint as the direction the theme serves). The chain is looser, but a paper that only shares vocabulary with a theme still doesn't get a block.

Then apply two filters specific to a review deck:

| Filter | Keep when | Drop when |
|---|---|---|
| **Block-able** | the contribution fits one sentence a non-specialist in the room can follow, and one number carries the result | it needs three slides of setup before the point lands, or its result is a table of 40 cells with no headline |
| **Figure-able** | the source has a figure that shows the mechanism or the result | the only figures are a system screenshot, a logo diagram, or nothing at all — see [figure-capture.md](figure-capture.md) before dropping; a results table can be redrawn as a native chart with attribution |

Both filters are about the deck, not the science. A paper that fails them can still be listed on the "also worth reading" slide with a one-line reason.

## Balance across the shortlist

Aim for a shortlist that is worth presenting, not just a ranked list:

- Cover every theme in `brief.md`; a theme with no recent work is itself a finding — say so on the slide.
- Mix evidence levels deliberately, and label them: peer-reviewed results, working code, self-reported vendor numbers. Two vendor blog posts in a row look like a sales deck.
- Prefer one strong paper per sub-topic over three variations of the same idea. If three groups converged on the same trick within the window, that convergence is the theme; give the strongest paper the slide and name the other two inside it.
- Include at most one or two "watch this" items with weak evidence, and tag them as such.

## Recording

If the workspace has a `scouting/` folder, record every screened source through `source-scout/scripts/scout_log.py` (`seen` before screening, `add` after) so reviews and scouting runs share one memory and the next review only sees new work. A `keep` needs `--problem`, `--distance` and `--structure` (and `--bridge` when the distance is not `direct`); pass the sub-problem id when a research map exists, otherwise the theme id (`--problem theme:vector-index`). Read `scouting/calibration.md` first (`scout_log.py scouting rules`): rules from earlier overrules apply to review screening too. Without a `scouting/` folder, keep the screening table, with the same chain columns, in `brief.md`.

Optionally run **stage-critic** on the shortlist with its `screened` rubric before presenting it; for a deck it mainly catches keeps that share only vocabulary with a theme and drops that were false negatives.
