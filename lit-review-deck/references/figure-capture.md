# Capturing figures from the original source

A paper slide is carried by its figures. They must come from the source, be legible at slide size, and be credited.

## Which figures to pick

**One to three per paper, usually two**: one that shows how the method works, one that shows what it achieved. A slide with two well-chosen figures explains more than a slide with five cramped ones.

In order of preference:

1. **The mechanism figure**: the one that shows how the method works (architecture, data flow, the key transformation). It explains the contribution without the body text.
2. **The headline result figure**: the plot the authors lead with, when the contribution is empirical.
3. **A qualitative example**: the before/after, sample output or failure case, when it is the argument the paper actually makes.
4. **A table redrawn as a native chart**: only when no usable figure exists. Build it with `team_deck`'s `chart()` or `bar()`, caption it "redrawn from Table N", and keep the numbers exact.

Each figure sits inside the section it illustrates (`"section": "method"` / `"results"` in `blocks.json`; that is also the default for figure 1 and 2).

Never combine parts of two figures into one image (capture them as two entries in `figures` instead), never crop away the axis labels, units or legend, and never crop away a caveat marked in the figure. If the figure only makes sense with its caption, the block's figure caption carries the needed half-sentence.

## Capture quality

- Render from the **PDF**, not from a browser screenshot of an HTML view: vector text stays sharp.
- 200–300 dpi. A figure is about 5.6 in wide on a 13.33 in slide, and less when two share a row; below ~180 dpi axis labels turn to mush at presentation size.
- Crop to the figure itself: drop the surrounding body text and the figure's own number line ("Figure 3: …") — that goes in the slide caption instead, where it can be styled.
- Keep the aspect ratio. `poster_deck.py` fits each image inside its box without distorting it; a poster column is about 4.2 in wide, so a wide figure is drawn full column width and a tall or square one (aspect < 1) goes beside the text at under half that width. Crop to the panel that carries the point.
- Check legibility at 100%: if the smallest text in the captured figure is unreadable on the rendered slide, crop tighter to one panel rather than showing the whole thing.

## Script

```sh
python <skill-dir>/scripts/figure_grab.py <source.pdf> --page N \
  --rect x0,y0,x1,y1 --units frac|pt --dpi 220 \
  --out papers/<paper-id>/figures/<name>.png \
  --caption "Fig. 3: ..." --source-url <url> [--cite "Leis et al., SIGMOD 2026"]
```

- `--units frac` takes fractions of the page (0,0 = top-left, 1,1 = bottom-right) — easiest when eyeballing a page image.
- `--page N` with no `--rect` captures the whole page; use `--probe` first to render pages at low dpi and pick the region, and `--list-images` to see the embedded raster images on a page.
- Backends: PyMuPDF (`pip install pymupdf`) if available, otherwise `pdftoppm` from poppler-utils, with Pillow for cropping. The script says which backend it used.

Every capture writes `<name>.json` beside the image: source file, source URL, citation, page, rectangle, units, dpi, backend, image size and capture date. Don't hand-edit it; re-run the capture instead. A figure with no sidecar file does not go in the deck.

## Attribution and licence

- Each figure shows a credit line under it: `Fig. 3 — Leis et al., SIGMOD 2026`. `poster_deck.py` draws it from each figure's `caption`; don't remove it.
- `deck/sources.md` lists every paper with authors, venue, date, URL and the figure used.
- arXiv and most conference PDFs allow figure reuse for internal, non-commercial discussion with attribution, but licences vary (arXiv postings carry per-paper licences; ACM/IEEE copyright differs from CC-BY). For an **internal** review deck, attributed excerpts are the normal practice. Before anything leaves the company — a public talk, a blog post, a customer deck — check each figure's licence and say clearly in your handover which figures have not been cleared.
- Never remove or obscure a watermark, a copyright line burned into a figure, or an author's name.
- Never present a source figure as our own measurement, and never edit values, axes or labels inside a captured figure. Annotation on top (an arrow, a highlight box drawn in PowerPoint) is fine if the caption says it was added by us.
