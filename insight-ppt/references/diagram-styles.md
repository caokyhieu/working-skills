# Diagram styles: method figures and explainers

Two drawing styles recur in good ML material. Use them for the diagrams you draw yourself. They set **how the diagram is composed**; the colours, font and components stay those of the team theme ([team-theme.md](team-theme.md)). Never bring in the pastel blue/green/orange/purple of the originals, rounded "app" boxes, emoji icons, or a second font.

| Style | Looks like | Use it when the slide must show |
|---|---|---|
| **A. Method figure** | The "Figure 1" of a NeurIPS/ICML paper: numbered panels, nested modules, tensors as grids, zoom-in callouts, inline math | How a model or algorithm is **composed**: which parts are frozen or trained, the intermediate representations, where the new operator sits |
| **B. Explainer** | A step-by-step technical infographic: numbered steps, rows of token boxes, brackets and dimension arrows, one worked example | How a runtime process **unfolds** on concrete data: tokens, requests, cache entries, time |

Pick one style per diagram. A deck can use both, but on different slides. Both styles are built with `scripts/team_deck.py`: the existing components plus the diagram helpers `panel`, `grid`, `zoom`, `op`, `route`, `badge`, `pills`, `bracket`, `dimension`, `mark`, `span` and `legend`. Everything stays native and editable.

If the repository's `templates/diagrams/` folder is available, `model-architect/` holds a style A example and `prefill-decode/` holds style B examples. They are composition references only. Don't copy their content, colours or watermarks.

## Colour mapping (both styles)

The originals give each state its own hue. On a team-theme slide, states map onto the existing variants, and every diagram with more than one state gets a `legend()` or caption. Colour never carries status alone.

| Meaning in the diagram | Team variant / fill | Pair with |
|---|---|---|
| Existing, frozen, context, reused, "free" | `neutral` (F5F5F5) or `white` | tag `FROZEN` / legend "reused" |
| The part the proposal adds, trains or changes | `outline` (red border); `accent` for **one** decisive element only | tag `NEW` / `TRAINED` |
| Work done, cost incurred (computed, prefill) | `pale` (FDF0EF) or `span(fill="pink")` | legend "computed" |
| Final or chosen result | `dark` (1D1D1A), at most 1–2 per slide | tag `FINAL` / caption |
| Inferred, future, speculative | `dashed` red; keep that single meaning | legend "inferred" |
| Rejected, discarded | `white` with a `mark(ok=False)` ✗ and the word "rejected" | text label |
| Highlighted cells in a matrix/tensor | `pink` (the part that matters), `pale_red` (secondary), `surface` (second stream, e.g. imaginary part) | caption |
| Operators (FFT, ReLU, ⊕) | `white` node or `op()` circle, grey border | — |
| Flow | grey (`muted`) connectors; red only for the decisive path | — |

With more than three states in one diagram, use a table or split the slide.

## Style A — method figure

**Anatomy.** Grey `panel()`s, one for each part of the method, labelled the way the paper's sections are ("§3.2 Fourier-projected adaptation") or as numbered stages when the method isn't ours to section. Inside each panel: sub-module groups (`white` panels), component `node()`s, tensors drawn with `grid()`, operators with `op()`, and `route()`d orthogonal edges. A `zoom()` callout links a small region to its enlarged detail panel.

Composition rules:

1. **Panels follow the method's decomposition.** Put the big picture (the whole architecture) in the widest panel and each mechanism detail in its own panel. A bottom band that runs full width suits a sequential sub-procedure (numbered `1 · … → 2 · … → 3 · …` sub-panels joined by grey block `arrow()`s).
2. **Show the representation, not just the box.** Draw the input/output as a column vector (`grid(rows, 1)`), a weight or attention matrix as a square grid with highlighted cells (`cells={(r, c): "pink"}`), and a batch or multi-head tensor as a grid with `stack=2`. This is what makes it a mechanism diagram rather than a pipeline (see the algorithm guidance in [content-and-evidence.md](content-and-evidence.md)).
3. **Trainable vs frozen is the headline distinction** in adaptation, continual-learning and fine-tuning figures. Mark it with the variant *and* a tag or sub-label ("frozen", "trained").
4. **Zoom callouts.** Put a dashed box on the source region and draw two thin lines to the detail panel. Place the detail panel next to the source so the lines stay short and don't cross unrelated shapes. One or two callouts per slide at most.
5. **Inline math.** Use Unicode in italic runs of the theme font (`[("W = M ⊙ cos Φ", {"italic": True})]`), e.g. `Ŷ`, `⊙`, `λ₁`, `Φ⁽ᵏ⁾`, `ℱ⁻¹`. Keep symbols next to the thing they name, not in a separate legend. No equation objects and no second font. A longer derivation goes in the notes.
6. **Density.** A method slide is dense by design: node labels 8.5–9.5 pt, math and edge labels 8–8.5 pt, never below 7.5 pt. If it doesn't fit, move one panel to its own slide. Don't shrink it.
7. **Provenance.** When the figure describes someone else's method, the tagline or a 9 pt caption says "Drawn by us after §3 of <cite>; sizes illustrative". Never present it as the authors' figure.

```text
┌ §3.3 Stack (panel) ──┐ ┌ §3.2 Mechanism (panel) ─────────────────────────────┐
│ [backbone · frozen]  │ │ ▯ → [rFFT] → ▦▦ → ▦▦▦▦▦▦ (block-diag, pink) → ▦ → ▯ │
│ [layer 1 · TRAINED]──⊕→│     x          X̃        W (stack=2)       Ŷ          │
│ [layer 2 · frozen]   │ │       ┌dashed┐╲╲ zoom ┌ Polar form ┐               │
└──────────────────────┘ └──────────────────────┴─ W = M⊙cosΦ …┘──────────────┘
┌ §3.4 Consolidation (panel, full width) ──────────────────────────────────────┐
│ 1 · Snapshot  ➜  2 · Importance scoring  ➜  3 · Transfer                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Style B — explainer

**Anatomy.** The slide's title and tagline play the explainer's headline and one-line subtitle, so don't draw a second title. Below them come 2–4 steps, each opened by a `badge(n, "VERB", "what happens")` or a spaced-caps `section()` label, then a concrete worked example drawn as rows of `pills()`. Conclude with `strip()` or `takeaway()`.

Composition rules:

1. **One mechanism, one worked example.** Use real-looking tokens ("The quick" → "brown" → "fox") or request names, not abstract A/B/C, unless the point is positional (like "where reuse stops"). Label numbers illustrative unless they come from evidence.
2. **Steps read top to bottom:** badge row, then the example row. Aligned rows compare two cases (request 1 vs request 2, cached vs new, good order vs bad order). Keep the same column positions across rows so the eye compares straight down.
3. **Annotate on the drawing:**
   - `bracket()` under a group of pills, with a short label ("cache hit: no prefill"). Label it red only for the cost or the decisive group.
   - `dimension()`, a double-headed line with `extend_to` guide lines, for spans such as TTFT, ITL, end-to-end latency or a 1-second window.
   - `mark(ok=…)` above a token, next to a word ("accepted" / "rejected").
   - A dashed grey `connector()` for "same as above / reused from".
4. **Timelines and Gantt rows.** Use one `span()` per phase (queue on `track` with grey text, prefill on `pink`, decode on `surface` or as token pills). Draw one row per request for throughput views, with dashed vertical `connector()`s marking a measuring window. Add a `legend()`.
5. **Probability and score tables under tokens.** Use a `grid` of `white` boxes aligned under the pills, or a native `table()` when the values are the point. Put the worked arithmetic in one sentence below ("P(target) .32 < P(draft) .69 → kept with chance .46 → rejected").
6. **Definitions.** End with 1–3 lines in the takeaway form, bold ink term plus grey definition ("**TTFT:** time from prompt to first token"). Use no highlighter fills.
7. **Whitespace.** Explainers are sparser than method figures: body 9.5–11 pt, pills 0.35–0.45 in tall, at least 0.2 in between rows. If the example needs more than about 8 pills per row, shorten the example.

```text
SAME PREFIX, TWO REQUESTS                           ▭ computed  ▭ reused
Request 1  [System prompt][Tools][Examples][Question A]     (pale)
                             ┆ same tokens → same KV
Request 2  [System prompt][Tools][Examples][Question B]     (neutral … pale)
           └──── cache hit: no prefill ────┘└ prefill ~50 ┘
➊ PREFILL the whole prompt in one pass
[queue][ prefill ][tok 1]→[tok 2]→[tok 3]
|←──── TTFT ────→|       |← ITL →|
▌Stable content first. Anything after a changed token is recomputed.
```

## Build checklist

- Model the diagram before drawing it: panels and their members for A; steps, rows and the example data for B. Keep that source with the build script.
- Lay out from a grid (a column x per pill, a cell size per tensor) instead of scattering coordinates, so rows align.
- Every state has a legend or tag; each red element is justified; at most one `accent`.
- `deck.save()` prints no warnings. Render the slide and check that brackets sit under the right pills, dimension arrows start and end on the measured edges, zoom lines don't cross labels, and math runs are legible at presentation size.
