---
name: lit-review-deck
description: Build a literature-review slide deck where every paper gets its own slide, laid out like that paper's conference poster — figures screenshotted from the original, the general idea, contributions, headline numbers, strengths and limits, and why it matters for the company's direction, set dense in small type. Scans top-tier ML, AI and database venues, arXiv, engineering blogs and open-source releases from the last 12 months only. Use when the user asks for a paper review deck, a "what's new in <field>" presentation, a reading-group or research-radar deck, or a poster-style summary of recent work.
---

# Lit Review Deck

Answer one question for the audience: **what came out recently that changes what we should do?**

**One paper, one slide.** Each slide is laid out like that paper's conference poster: a title banner, then three columns of boxed sections with coloured headers — what problem it attacks, its general idea, how it works, what the authors contribute, the headline numbers, what makes it strong, what it does not cover, and the line that connects it to a company direction — with figures screenshotted from the original sitting inside the sections they illustrate. Dense and small-type is correct here — a reader stands in front of one slide and gets the whole paper. Content comes from the paper itself, never from the abstract alone where the full text is available. A paper a reader cannot connect to a direction does not belong in the deck.

This skill covers the whole path: scope → scan → select → read → capture figures → build slides → deck. It reuses `source-scout` for scanning conventions and `insight-ppt`'s team theme for the deck.

## Workspace

Reviews live at the workspace root, beside `scouting/` and `poc/`:

```text
company-context.md
reviews/<review-id>/
  brief.md                       # scope, themes, window, audience, approved by the user
  papers/<paper-id>/
    card.md                      # everything the paper's slide shows (templates/paper-card.md)
    source.pdf                   # local copy when the licence allows; otherwise the URL only
    figures/<name>.png           # captured figures, usually mechanism + result
    figures/<name>.json          # capture provenance (script-written)
  blocks.json                    # the deck spec built from the approved cards
  deck/<review-id>-v1.pptx, build_deck.py, sources.md
```

`review-id` is a short slug: `q3-2026-query-optimization`, `llm-serving-radar`. Keep one review per deck.

## 1. Scope the review (ask before scanning)

Read `company-context.md` for ranked priorities, products, data assets and constraints. Then agree with the user on:

| Question | Default if the user has no preference |
|---|---|
| Which company directions does this review serve? | the top 3 priorities in `company-context.md` |
| Recency window | last 12 months, hard limit — the point is what is new |
| Fields | ML/AI, databases, systems, as the directions require |
| How many papers | 6–10, one slide each (a slide takes 2–3 minutes to present) |
| Audience and duration | ask; it sets how many papers fit and how deep each slide goes |
| Presentation date and presenter | ask |

Write [templates/review-brief.md](templates/review-brief.md) to `reviews/<review-id>/brief.md` with the themes (2–4), the directions each theme serves, and the search topics per theme. **Confirm the brief before scanning.** Search topics use public, generic technical terms only: no company names, product names, internal metrics or `company-context.md` text goes into a query.

## 2. Scan

Read [references/scan-plan.md](references/scan-plan.md) for the window rule, venue and feed lists, query construction and what disqualifies a source. Venue and feed lists live in [source-scout/references/sources.md](../source-scout/references/sources.md); don't duplicate them here.

Cover papers, engineering blog posts and notable open-source releases for each theme. Anything published or last revised more than 12 months before today is out, whatever its merit — say so explicitly when dropping a well-known older paper the user may expect to see. If a `scouting/` folder exists, check `scout_log.py seen <url>` first and reuse the screened records instead of re-screening.

Screen with the rubric in [source-scout/references/screening.md](../source-scout/references/screening.md). Write the relevance chain (problem, shared structure, distance) for each keep so the deck's "for us" line says *why* the paper matters, not only what it does: with `research-map.md`, the sub-problem id and its bridging concepts; without one, the theme id from `brief.md` (`scan-plan.md` → Screening). Then apply the two review-specific filters in `scan-plan.md`: **it must be explainable in one slide**, and **it must have usable figures** — normally one showing the mechanism and one showing the headline result.

## 3. Select with the user

Present the shortlist grouped by theme: one line per candidate (title, venue, date, what it does, which direction it serves) and ask which go into the deck. Each pick costs a full slide, so say how many slides the selection adds up to. Show the ones you dropped for recency or fit with the reason. Don't build slides before the user picks.

## 4. Read each selected paper

Write `papers/<paper-id>/card.md` from [templates/paper-card.md](templates/paper-card.md). The card holds everything the slide shows, so read the actual source — introduction, method and evaluation sections at minimum — not the abstract alone. When only an abstract is available, say so on the card, tag the slide `CLAIM-ONLY` and say it in the tagline.

Two things are easy to get wrong here. **The general idea is the authors' framing**, the sentence they would use, not our summary of the summary. **The strengths are evidence, not enthusiasm**: tuned baselines, an ablation that isolates the contribution, released code, an honest scope statement. If nothing on that list is true, the strengths section says so, and the paper probably deserved a line in "also worth reading" instead of a slide.

A full `source-digest` is not needed for a review slide, but the same rules apply: copy numbers exactly with their location, tag your own reasoning `[inference]`, and separate the authors' claims from your reading. If the paper is already digested under `scouting/sources/` or `poc/*/sources/`, build the card from the digest and don't re-read.

## 5. Capture the figures

One to three per paper — usually two: the figure that shows the **mechanism** and the figure that shows the **headline result**. Read [references/figure-capture.md](references/figure-capture.md) before capturing anything: which figures to pick, resolution, cropping, and the attribution and licence rules. Capture with the script, which records provenance next to the image:

```sh
python <skill-dir>/scripts/figure_grab.py papers/<paper-id>/source.pdf \
  --page 5 --rect 0.08,0.10,0.92,0.46 --units frac --dpi 220 \
  --out papers/<paper-id>/figures/fig3.png \
  --caption "Fig. 3: end-to-end latency on JOB" --source-url <url>
```

Every figure keeps its `<name>.json` and is credited on the slide (`Fig. N, <short cite>`) and in `deck/sources.md`. Never redraw a source figure as if it were ours, and never present a source figure as our measurement.

## 6. Build the slides

Assemble `blocks.json` from the approved cards ([templates/blocks.example.json](templates/blocks.example.json)) — one entry per paper, one slide per entry — then build:

```sh
python <skill-dir>/scripts/poster_deck.py reviews/<review-id>/blocks.json \
  --out reviews/<review-id>/deck/<review-id>-v1.pptx
```

The script writes the deck in the team theme via `insight-ppt/scripts/team_deck.py` (title slide, contents, legend, a divider per theme, one poster slide per paper, then sources) and prints layout warnings. It balances the section boxes across three poster columns, places each figure in its section, and shrinks the body text from 9 pt to the 7.5 pt floor (and figures to half size) by itself; it warns only when even the floor is not enough. Fix every warning editorially — cut a section, shorten bullets, move detail into the speaker notes — never by shrinking below the floor.

Read [references/poster-layout.md](references/poster-layout.md) for the slide anatomy, the section list, figure placement and the compact-grid exception. Read [insight-ppt/references/team-theme.md](../insight-ppt/references/team-theme.md) for the theme itself; this deck uses the same components and colour meanings.

Keep `build_deck.py` (or the exact command) with the deck, write `deck/sources.md` with one row per paper (title, authors, venue, date, URL, figure credit), and put the per-paper detail the slide cannot hold into speaker notes.

## 7. Check before delivering

- Every slide: figures present and credited, the general idea in the authors' framing, contributions, at least one number with its baseline and benchmark, strengths that name evidence, limits, and a direction line.
- No paper older than the window. No direction line that is guesswork about company plans.
- Nothing on a slide that is not in the paper, except our `[inference]` lines — and those are marked.
- Themes read in an order that builds an argument, and each theme divider states a conclusion; the closing slide says what to read, try or watch next — not a generic summary.
- Render the slides and inspect them when a renderer (`soffice`) is available; otherwise state that the visual check was not run.

## Rules

- **Recency is a hard filter.** Older work appears only as one line of context inside a slide, never as its own slide.
- **No fabricated figures, numbers or affiliations.** A figure comes from the source or it is not shown.
- **Relevance is argued, not asserted.** The direction line names the priority and the mechanism by which the paper touches it. Mark speculation `[inference]` on the card and hedge it on the slide.
- **Public queries only.** Company context never leaves the workspace.
- **Measured vs projected.** A paper's number is the authors' result on their benchmark. Never restate it as our expected gain.
- **Dense is fine, illegible is not.** 7.5 pt is the floor; past it, cut content instead.
- Don't start experiments or write proposals here. Hand promising papers to `research-poc` (`promote`) or `idea-alignment`.
