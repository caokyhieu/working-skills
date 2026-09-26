# Paper-slide layout

**One paper, one slide.** Each slide is laid out like that paper's conference poster: a coloured title banner, three columns of boxed sections with coloured header bars, the paper's figures inside the sections they illustrate, and a takeaway strip across the bottom. A reader who sees only that slide should be able to say what the paper does, what it showed, and why we care. Slides are built with [insight-ppt/scripts/team_deck.py](../../insight-ppt/scripts/team_deck.py) in the team fonts and palette — see [team-theme.md](../../insight-ppt/references/team-theme.md) for colour meanings. Poster slides use the full slide width and skip the standard title/kicker header; the master's logo zone (bottom right) stays clear.

## Slide anatomy

```text
┌─ banner (blue, full width, 1.0 in) ────────────────────────────────────────────────────┐
│ Literature Review: Query Optimization · Cardinality estimation (kicker · theme)        │
│ Feedback-Driven Cardinality Estimation for Join Queries   (20 pt, down to 15)  ┌──────┐│
│ Leis et al. (TUM) · SIGMOD 2026 · 2026-06            [PEER-REVIEWED] [CODE]    │2.1x  ││ headline
└────────────────────────────────────────────────────────────────────────────────└──────┘┘
┌ PROBLEM ─────────────┐ ┌ CONTRIBUTIONS ───────┐ ┌ WHY IT IS STRONG ────┐  header bars 8.5 pt
│ Independence …       │ │ • Signature keying … │ │ • Baselines tuned …  │  body 7.5–9 pt
├ GENERAL IDEA ────────┤ ├ HEADLINE RESULTS ────┤ ├ LIMITS AND OPEN Q. ──┤
│ Treat the optimizer… │ │ • 2.1x lower p99 …   │ │ • No update-heavy …  │
├ HOW IT WORKS ────────┤ │ ┌──────────────────┐ │ │ • [inference] …      │
│ • Logs actual rows … │ │ │ Fig. 5 results   │ │ ├ WHY IT MATTERS (red)─┤
│ ┌──────────────────┐ │ │ └──────────────────┘ │ │ Optimizer latency    │
│ │ Fig. 2 mechanism │ │ │ Fig. 5 — Leis et al. │ │ (P1): replaces …     │
│ └──────────────────┘ │ │                      │ │                      │
└──────────────────────┘ └──────────────────────┘ └──────────────────────┘
▌Closest thing to a drop-in win in this review. One interface, public patch …   (takeaway)
 Source: Leis et al., SIGMOD 2026 · https://… Figures reproduced from the original, with attribution.
```

The builder lays the slide out itself: the section boxes keep their reading order and are split into columns so the tallest column is as short as possible; it then picks the largest body size (9 pt down to the **7.5 pt floor**) and figure scale (full down to half) at which everything fits. A column with spare height grows its figures into it, and then all boxes in the column share what is left, so columns end level as on a printed poster. When even the floor with half-size figures does not fit it warns instead of shrinking further — the fix is editorial, never a smaller font.

## The sections

In this order, all optional — omit what the paper does not support rather than padding it:

| Key | Label on the slide | What goes in it |
|---|---|---|
| `problem` | Problem | what was broken or missing before this paper, in one or two lines |
| `idea` | General idea | the paper's **own framing** of its approach — the sentence the authors would use |
| `method` | How it works | the mechanism, 3–5 bullets, in our words |
| `contributions` | Contributions | what the authors claim as new; `[lead, rest]` pairs read best |
| `results` | Headline results | numbers, each with its baseline, benchmark and location (`Table 4`, `Fig. 5`) |
| `strengths` | Why it is strong | what holds up under scrutiny: tuned baselines, ablations, released code, honest scope |
| `limitations` | Limits and open questions | the authors' caveats first, then ours marked `[inference]` |
| `for_us` | Why it matters for us | the direction from `company-context.md` plus the mechanism that touches it |

Plus `headline` (`[value, detail]`) for the one number, shown in a white box at the right of the banner, `tags` for the evidence tags (in the banner), and `takeaway` for the strip across the bottom. `for_us` is drawn with a red header on a pale-red box so the audience finds it without looking.

Rename a label with `section_labels`, reorder or drop with `sections`, and force where columns start with `column_breaks` (`["contributions", "strengths"]` starts column 2 at Contributions and column 3 at Why it is strong). `poster_columns` (paper, theme or deck) sets 2 or 3 columns; 3 is the default and suits a full card. Content the slide cannot hold goes into `notes` — speaker notes are part of the deliverable, not a dumping ground.

Density targets for a full slide: `problem` and `idea` 1–2 lines each, `method` 3–5 bullets, `contributions` 2–4, `results` 2–4, `strengths` 2–3, `limitations` 2–3, `for_us` one sentence. That lands around 9 pt. More than that and the build warns.

## Figures

A figure lives **inside the section it illustrates**, the way a poster puts the architecture diagram in the method box and the results plot in the results box.

- **One to three figures per paper.** Two is the usual pair: the mechanism (architecture / method) and the headline result (the plot or table the abstract's number comes from).
- `section` names the box: `"method"`, `"results"`, `"idea"`, … Without it, figure 1 goes to How it works, figure 2 to Headline results, then General idea, Contributions. A figure with no box to go to gets a box of its own (`label`, default "Figure").
- `place`: `"below"` draws it the full column width under the text (about 4.2 in); `"beside"` puts it next to the text at under half that width. The default (`"auto"`) puts tall or square figures (aspect < 1) beside and wide ones below.
- A figure is drawn at most 2.7 in tall at full scale and never below 1.0 in; the builder trades body size against figure scale (down to half) to fit, and grows figures into a column's spare height.
- Every figure is credited under it (`Fig. N — Authors, Venue Year`) and keeps its `<name>.json` provenance from `figure_grab.py`. See [figure-capture.md](figure-capture.md).

## Theme dividers

A theme with more than one paper gets a divider slide before its papers: the conclusion-led theme title, the papers in it with a half-line each (`one_line`), and an optional `intro_takeaway`. Set `"intro": false` to skip it. Theme titles state the conclusion, not the topic — "Three groups converged on feedback-driven estimation" beats "Cardinality estimation papers" — and stay under ~52 characters, as do `slide_title` values.

## Slide sequence

1. **Title** — review title, window, presenter, team.
2. **Contents** — the themes, numbered.
3. **How to read a paper slide** — the anatomy legend and what the tags mean. Worth keeping for any audience beyond the immediate team.
4. **Per theme**: a divider slide, then one poster slide per paper.
5. **Also worth reading** — one line each for the near-misses, with why they were cut.
6. **What we do next** — read / try / watch, each tied to a direction and an owner if the user has one. Not a summary.
7. **Sources** — every paper with its citation and figure credits (also written to `deck/sources.md`).

## Tags and variants

Tags mark evidence, never quality: `PEER-REVIEWED`, `CODE`, `SELF-REPORTED`, `PREPRINT`, `WATCH`. Several per paper is normal (`["PEER-REVIEWED", "CODE"]`). Colour never carries the status alone.

## Compact grid (the exception)

When the user explicitly wants a summary wall — a back-page recap, or a set of papers that only deserve a line each — set `per_slide` (or `columns`, plus `rows`) on the theme and the old block grid is used instead, with the four short fields `problem` / `does` / `result` / `for_us`:

| Papers per slide | Spec | Block (w × h) | Fields that fit |
|---|---|---|---|
| 2 (1 × 2) | `"columns": 2` | 5.77 × 4.78 in | all four, one line each |
| 3 (1 × 3) | `"columns": 3` | 3.77 × 4.78 in | does + result + a short for_us |
| 4 (2 × 2) | `"columns": 2, "rows": 2` | 5.77 × 2.30 in | does + result, figure beside the text |

Anything past four blocks on a slide stops being readable at the back of a room.

## blocks.json

Full example: [templates/blocks.example.json](../templates/blocks.example.json). Figure paths are relative to `blocks.json`.

**Deck**: `title`, `subtitle`, `kicker` (repeated on every slide, in the poster banner), `poster_columns`, `poster_colors` (`banner`, `header`, `accent`, `accent_fill`; theme-level too), `window`, `presenters`, `team`, `themes`, the optional `contents` / `legend` / `sources` switches (all default on), `also_worth_reading`, `next_steps`.

**Theme**: `name` (contents entry), `title` (conclusion-led, ≤ 52 chars), `tagline`, `intro`, `intro_takeaway`, `papers`, and — only for the compact grid — `per_slide`, `columns`, `rows`, `layout`, `takeaway`.

**Paper**: `id`, `title`, `slide_title`, `one_line` (for the divider), `authors`, `venue`, `date` (or one prepared `meta` line), `url`, `tags`, `headline`, `figures` (each `path`, `caption`, optional `section` / `place` / `label`), `cite`, the section keys above, `sections` / `section_labels` / `column_breaks` / `poster_columns`, `takeaway` and `notes`.

The build also writes `deck/sources.md` beside the `.pptx` from the same data, so the citation list cannot drift from the slides.
