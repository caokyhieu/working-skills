# Team theme

Built-in decks follow the team's research-deck design, taken from the team's example presentations. Exact values are in `templates/defaults.json`. This guide explains how to use them.

## Build from the base template

1. Start from `assets/team-template.pptx`. Never recreate the branding by hand. The template's master supplies:
   - the lab header
   - the logo
   - the "Huawei Confidential" line
   - the page number
   - the bottom colour bar
   - the title-slide artwork
2. Use `scripts/team_deck.py`:

```python
import sys; sys.path.insert(0, "<skill-dir>/scripts")
from team_deck import TeamDeck
deck = TeamDeck(kicker="Research Insight: <topic>", corner="triangle")  # or corner="Technology Trends"
deck.title_slide("<Deck title>", "<one-line subtitle>", presenters=["<Name>"], team="<Team>")
s = deck.slide("<Conclusion-led title>", tagline="<optional one-line context>")
...
deck.save("deck/<name>-v1.pptx")   # prints layout warnings: fix them all
```

3. Keep the build script with the deck. Every shape it creates is native and editable.

Content slides use the **Blank** layout under the branded master, which the library selects. Don't add a footer, page number, logo or "Confidential" text on slides: the master already draws them. Two of the example slides duplicated them by mistake.

Ask which lab or header the deck needs only if the user belongs to a different lab. The header text lives in the master; edit the master text in the template instead of covering it with shapes.

## Slide anatomy

```text
┌▶ cyan corner   kicker (13 pt blue): deck topic, same on every slide        HUAWEI | LAB HEADER (master)
│  TITLE: ONE CONCLUSION-LED LINE (26 pt bold red)
│  tagline (10 pt grey, optional): scope, benchmark, or reading instruction
│
│  SECTION LABEL (10.5 pt grey caps, spaced)
│  ┌ panels / diagram / table / chart ───────────────────────────────┐
│  └─────────────────────────────────────────────────────────────────┘
│  ▌callout strip: bold sentence + grey detail
│  ───────────────────────────────────────────────────────────────── rule
│  Takeaway: bold lead. Grey supporting detail.
└  page no. (master)            – Huawei Confidential – (master)               logo (master)
```

- Content area: x 0.78–12.56 in, y 1.10 in (1.30 with tagline) to 6.85 in. Keep x ≥ 10.7 and y ≥ 6.8 clear for the logo.
- Title: one line, at most about 52 characters. Rewrite it shorter instead of shrinking the font or wrapping.
- The kicker is the deck topic (for example "Research Insight: Learned Cardinality Estimation"), not a per-slide subtitle. Leave it off the contents slide and section dividers.

## Components (library method → when to use)

| Component | Method | Use for |
|---|---|---|
| Section label | `section()` | Naming regions on a dense slide ("HOW IT WORKS", "WHERE THIS GOES NEXT") |
| Panel heading | `heading()` | Bold 11 pt heading above a column or chart |
| Card | `card(variant=…, tag=…)` | Before/after, option A/B, a mechanism step with 2–4 short lines |
| Node | `node()` | Architecture and flow boxes: bold label + small second line |
| Tag | `tag()` / `card(tag=…)` | Status on a card: `BASELINE`, `PROPOSED`, `REPLACED`, `FINAL`, `INFERRED` |
| Callout strip | `strip()` | The one sentence to remember from a section |
| Takeaway | `takeaway()` | Slide conclusion at the bottom (usually with a rule above) |
| Stat | `stat()` | 2–4 headline numbers with short labels |
| Mini bars | `bar()` | Hand-built bar rows with value labels, for 2–6 items with a clear focus |
| Table | `table(highlight=…)` | Comparisons: grey header, hairline row rules, no vertical lines |
| Chart | `chart(focus=…)` | Native bar/column chart: focus series red, others grey |
| Arrows / connectors | `arrow()`, `connector()` | Grey for neutral flow; red only for the decisive transition |
| Rules | `rule()` | Thin grey dividers between columns or above the takeaway |
| Diagram helpers | `panel()`, `grid()`, `zoom()`, `op()`, `route()` | Method figures: titled section panels, tensors/matrices as cell grids, zoom-in callouts, operator circles, orthogonal edges ([diagram-styles.md](diagram-styles.md)) |
| Explainer helpers | `badge()`, `pills()`, `bracket()`, `dimension()`, `mark()`, `span()`, `legend()` | Numbered steps, token/request rows, group brackets, latency/span measures, ✓/✗, timeline segments, inline legends |
| Contents | `deck.contents()` | Numbered agenda (red numbers, 18 pt items) |
| Section divider | `deck.section_divider()` | Optional chapter break in decks over ~12 slides |

Card and node variants carry meaning. Use them the same way throughout the deck:

| Variant | Meaning |
|---|---|
| `neutral` (grey panel) | Baseline, existing system, context |
| `white` | Sub-components inside a panel |
| `dark` | The chosen/final design or key conclusion; 1–2 per slide at most |
| `accent` (solid red) | The single component the proposal adds or owns |
| `outline` (red border) | Emphasized or new step |
| `dashed` (red dashed) | Inferred, future or in progress; always state this in a caption or legend |
| `pale` | Soft highlight or warning note |

Colour never carries status alone. Pair it with a tag or caption such as "solid: today · dashed red: future phase" or "solid is confirmed, dashed is inferred".

## Typography

- Font: **Microsoft YaHei** for Latin and East Asian text (one family). If the machine building the deck lacks it, keep the font name in the file and say that previews used a substitute. Substitutes are usually wider, so a title that fits in PowerPoint may clip in the preview; the 52-character title limit leaves room for that.
- Body 10–12 pt. Dense mechanism/diagram slides use 8.5–9.5 pt body and 8 pt node sub-labels. Captions 9 pt grey; tags 7.5 pt. Nothing below 7.5 pt.
- The team decks are dense by design: one slide often holds a two-panel comparison, a callout and a takeaway. Keep that density, but split a slide when the lint reports overflow or when text would need to drop below the floor.

## Slide patterns from the team decks

- **Evolution / before → after:** grey card (tag `REPLACED` or `BASELINE`), grey arrow, dark card (tag `FINAL` or `PROPOSED`); callout strip below; then a second section showing what comes next.
- **Legacy vs current, side by side:** two column headings in spaced caps, a vertical rule between them, and each side as a top-down node stack with small grey arrows and edge labels. The focal layer is `accent` on the new side and `dark` for the failure mode on the old side.
- **Mechanism walkthrough:** a numbered step row (`1 · …` → `2 · …`) with the decisive step in `outline` and the outcome in `dark`, plus a text panel and a "Why …" panel below.
- **Evidence dashboard:** 2–3 columns, each with a panel heading, native chart, and 9.5 pt grey note on source/caveat; vertical rules between; a one-line bold verdict at the bottom.
- **Headline numbers:** a lead sentence, left column with red subheadings and grey paragraphs, vertical rule, and a 2×2 grid of stats plus a short timeline.
- **Confirmed vs inferred architecture:** solid nodes for documented components, dashed red for inferred ones, a legend at the bottom-left, and a side column "Still not public".
- **Prioritized table:** a legend line in red (`P0 = …  P1 = …`), a table with a pale-red highlighted priority column, and a bold "Not in scope" line below.
- **Summary:** a 16 pt bold verdict line, three numbered takeaways on the left, "What to watch next" bullets on the right.

## Quality checks specific to the theme

- `deck.save()` prints warnings for long titles, text overflow, text in the logo zone and fonts below the floor. Resolve every warning or state why it is a false positive.
- Render every slide and compare it with the anatomy above: the title is one line, the kicker is present on content slides, nothing covers the master header or footer, and no duplicate footer/logo appears.
- One dark card and one red accent per region at most. If everything is emphasized, nothing is.
- Charts: focus series red, all others grey, data labels on, legend only with more than one series.
