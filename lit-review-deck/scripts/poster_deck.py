#!/usr/bin/env python3
"""Build a poster-style literature-review deck from blocks.json, in the team theme.

Usage:
    poster_deck.py reviews/<review-id>/blocks.json --out deck/<review-id>-v1.pptx
                   [--team-deck <insight-ppt>/scripts/team_deck.py] [--quiet]

Default: one paper per slide, laid out as that paper's conference poster — a title banner
(paper title, authors, venue, date, evidence tags, the headline number), then 3 columns of
boxed sections with coloured header bars (problem, general idea, how it works,
contributions, headline results, why it is strong, limits, why it matters for us). Figures
captured from the original sit inside the section they illustrate; tall ones beside the
text, wide ones below it. A takeaway strip and the source line close the slide. The builder
balances the columns and picks the largest body size (9 pt down to the 7.5 pt floor) and
figure scale that fit.

Set "per_slide" (or "columns") on a theme to get the older compact grid of 2-4 short
blocks per slide instead. Slides: title, contents, optional legend, the paper slides,
optional "also worth reading", "what we do next" and sources slides.

Schema: see ../templates/blocks.example.json. Paths inside blocks.json are relative to
the file itself. Requires python-pptx and insight-ppt/scripts/team_deck.py.
"""

import argparse
import json
import itertools
import math
import os
import struct
import sys

# ------------------------------------------------------------------ geometry
MARGIN_X, CONTENT_W = 0.78, 11.78
BLOCK_TOP, BLOCK_BOTTOM = 1.32, 6.10      # takeaway() sits at 6.30 with a rule at 6.16
COL_GUTTER, ROW_GUTTER = 0.24, 0.18
PAD = 0.18
MIN_FIG_H = 0.9

FIELDS = [("problem", "Problem"), ("does", "Does"), ("result", "Result"), ("for_us", "For us")]
TAGS = ("PEER-REVIEWED", "CODE", "SELF-REPORTED", "PREPRINT", "WATCH")

# -- poster slide (one paper per slide), laid out like a conference poster --
# A coloured title banner across the top, then 2-3 columns of boxed sections, each with a
# coloured header bar; figures sit inside the section they illustrate; a takeaway strip and
# the source line across the bottom. The master's logo zone (x >= 10.7, y >= 6.8) stays clear.
SLIDE_W = 13.333
PS_X, PS_W = 0.20, 12.93                  # body spans the slide with a thin outer margin
BANNER_H = 1.00
PS_TOP, PS_BOTTOM = 1.10, 6.74
FOOT_Y = 6.82
COL_GAP, BOX_GAP = 0.12, 0.10
HEAD_H, HEAD_SIZE = 0.23, 8.5             # section header bar
BOX_PAD, FIG_GAP = 0.07, 0.08
FIG_MAX_H, FIG_MIN_H = 2.7, 1.0           # figure height at full scale / below which it is unreadable
FIG_GROW = 1.35                           # leftover column height may grow figures this far
CAP_SIZE = 7.5
BODY_MAX, BODY_MIN, BODY_STEP = 9.0, 7.5, 0.25
LINE = 1.22
POSTER_CHAR_W = 0.58                      # average glyph width / size, a little wider than lint's 0.55
POSTER_COLORS = {"banner": "0070C0", "header": "0070C0", "accent": "red", "accent_fill": "pale_red"}

# key, section label; for_us is drawn in the accent colour
SECTIONS = [
    ("problem", "Problem"),
    ("idea", "General idea"),
    ("method", "How it works"),
    ("contributions", "Contributions"),
    ("results", "Headline results"),
    ("strengths", "Why it is strong"),
    ("limitations", "Limits and open questions"),
    ("for_us", "Why it matters for us"),
]
ACCENT_SECTIONS = ("for_us",)
FIGURE_HOMES = ("method", "results", "idea", "contributions")   # default home of figure 1, 2, ...


def load_team_deck(explicit=None):
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [explicit] if explicit else []
    candidates += [os.path.join(here, "..", "..", "insight-ppt", "scripts", "team_deck.py"),
                   os.path.join(here, "..", "..", "..", "insight-ppt", "scripts", "team_deck.py")]
    for path in candidates:
        if path and os.path.exists(path):
            sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
            import team_deck
            return team_deck
    sys.exit("team_deck.py not found. Install insight-ppt beside this skill, or pass --team-deck <path>.")


# ------------------------------------------------------------------ images
def image_size(path):
    """(width, height) in pixels, from the file header; Pillow only as a fallback."""
    with open(path, "rb") as fh:
        head = fh.read(32)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            return struct.unpack(">II", head[16:24])
        if head[:2] == b"\xff\xd8":                      # JPEG: walk the markers
            fh.seek(2)
            while True:
                b = fh.read(1)
                while b and b != b"\xff":
                    b = fh.read(1)
                marker = fh.read(1)
                while marker == b"\xff":
                    marker = fh.read(1)
                if not marker:
                    break
                if marker[0] in range(0xC0, 0xCF) and marker[0] not in (0xC4, 0xC8, 0xCC):
                    fh.read(3)
                    h, w = struct.unpack(">HH", fh.read(4))
                    return w, h
                (seg,) = struct.unpack(">H", fh.read(2))
                fh.seek(seg - 2, 1)
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def fit(path, box_x, box_y, box_w, box_h):
    """Rect (x, y, w, h) for the image inside the box, aspect preserved, centered."""
    size = image_size(path)
    if not size:
        return box_x, box_y, box_w, box_h
    iw, ih = size
    scale = min(box_w / iw, box_h / ih)
    w, h = iw * scale, ih * scale
    return box_x + (box_w - w) / 2, box_y + (box_h - h) / 2, w, h


# ------------------------------------------------------------------ text sizing
def est_height(paragraphs, w, size, line=1.35, char_w=0.55):
    """Mirror team_deck's lint estimate, so blocks are laid out to pass it."""
    total = 0.0
    for p in paragraphs:
        chars = sum(len(t) for t, _ in p) if isinstance(p, list) else len(p)
        per_line = max(1, (w * 72) / (size * char_w))
        total += max(1, math.ceil(chars / per_line)) * size * line / 72
    return total


def tag_width(label):
    return max(0.5, 0.075 * len(label) + 0.25)


def meta_line(paper):
    bits = [paper.get("authors"), paper.get("venue"), paper.get("date")]
    return paper.get("meta") or " · ".join(b for b in bits if b)


# ------------------------------------------------------------------ one block
def block(cv, paper, x, y, w, h, base, layout="stacked", warn=None):
    variant = paper.get("variant", "neutral")
    fill, border, bpt, dashed, title_color, body_color = base.VARIANTS[variant]
    cv.rect(x, y, w, h, fill, border, bpt, dashed)
    dark = variant in ("dark", "accent")
    meta_color = "on_dark_sub" if dark else "muted"

    inner_w = w - 2 * PAD
    cy = y + 0.13

    tw = 0.0
    tag = paper.get("tag")
    if tag:
        tw = tag_width(tag)
        cv.tag(x + w - PAD - tw, cy, tag, "accent" if dark else "outline")

    title_size = 10.5 if layout == "stacked" else 9.5
    title_w = inner_w - (tw + 0.1 if tag else 0)
    title_h = est_height([paper["title"]], title_w, title_size, 1.25) + 0.04
    cv.text(x + PAD, cy, title_w, title_h, paper["title"], size=title_size,
            color=title_color, bold=True, line=1.25)
    cy += max(title_h, 0.24 if tag else 0) + 0.05

    meta = meta_line(paper)
    if meta:
        cv.text(x + PAD, cy, inner_w, 0.19, meta, size=8, color=meta_color, wrap=False, line=1.2)
        cy += 0.22

    fields = [[(label + "  ", {"bold": True, "color": "white" if dark else "title", "size": 8.5}),
               (str(paper[key]), {"color": body_color})]
              for key, label in FIELDS if paper.get(key)]

    if layout == "side":                       # figure left, text right (dense 2x2 grids)
        fig_w = w * 0.42
        text_x, text_w = x + fig_w + 0.06, w - fig_w - PAD - 0.06
        fields_h = y + h - cy - PAD * 0.6
        cv.text(text_x, cy, text_w, fields_h, fields, size=8.5, color=body_color, line=1.3)
        _figure(cv, paper, x + PAD, cy, fig_w - PAD, fields_h, meta_color, warn)
        return

    field_size = 9 if layout == "stacked" else 8.5
    fields_h = est_height(fields, inner_w, field_size, 1.35) + 0.08
    credit = paper.get("figure_caption") or paper.get("cite")
    credit_h = 0.18 if (paper.get("figure") and credit) else 0.0
    if paper.get("figure"):
        # the figure is the point of a poster block: give it a floor, then warn if the
        # text no longer fits, rather than squeezing the figure to nothing.
        free = y + h - PAD * 0.7 - cy - credit_h - 0.10
        floor = min(MIN_FIG_H, free * 0.35)
        fig_h = max(floor, min(free - fields_h, free * 0.72))
        if free - fig_h < fields_h - 0.02 and warn is not None:
            over = fields_h - (free - fig_h)
            warn.append(f"block '{paper.get('id', paper['title'][:30])}': field lines need ~{over:.2f} in "
                        f"more than the block has once the figure fits; shorten them, drop 'Problem', "
                        f"or put fewer papers on this slide")
        _figure(cv, paper, x + PAD, cy, inner_w, fig_h, meta_color, warn)
        cy += fig_h + 0.04
        if credit:
            cv.text(x + PAD, cy, inner_w, 0.18, credit, size=7.5, color=meta_color, wrap=False, line=1.2)
            cy += credit_h
        cy += 0.06
    cv.text(x + PAD, cy, inner_w, max(0.2, y + h - cy - PAD * 0.6), fields,
            size=field_size, color=body_color, line=1.35)


def _figure(cv, paper, bx, by, bw, bh, meta_color, warn):
    path = paper.get("figure")
    if not path:
        return
    if not os.path.exists(path):
        if warn is not None:
            warn.append(f"figure missing: {path}")
        cv.rect(bx, by, bw, bh, "white", "red", 1.0, True)
        cv.text(bx, by, bw, bh, "figure not captured", size=8.5, color="title",
                align="ctr", anchor="ctr")
        return
    if not os.path.exists(os.path.splitext(path)[0] + ".json") and warn is not None:
        warn.append(f"no capture provenance beside {path}; re-run figure_grab.py")
    cv.rect(bx, by, bw, bh, "white", "border", 0.5)
    fx, fy, fw, fh = fit(path, bx + 0.03, by + 0.03, bw - 0.06, bh - 0.06)
    cv.image(path, fx, fy, fw, fh)


# ------------------------------------------------------------------ poster slide
def figures_of(paper):
    """Normalized figure list: [{path, caption, section, place}], newest schema or the old single one."""
    figs = paper.get("figures")
    if figs is None:
        figs = ([{"path": paper["figure"],
                  "caption": paper.get("figure_caption") or paper.get("cite")}]
                if paper.get("figure") else [])
    out = []
    for f in figs:
        f = {"path": f} if isinstance(f, str) else dict(f)
        out.append(f)
    return out


def paras_of(value, bullet=None):
    """A string, a list of lines, or [lead, rest] pairs -> paragraphs for cv.text()."""
    items = [value] if isinstance(value, str) else list(value)
    if bullet is None:
        bullet = len(items) > 1
    dot = "\u2022 " if bullet else ""
    out = []
    for it in items:
        if isinstance(it, (list, tuple)):
            lead = str(it[0])
            rest = str(it[1]) if len(it) > 1 else ""
            runs = [(dot + lead, {"bold": True, "color": "ink"})]
            if rest:
                runs.append((" " + rest, {}))
            out.append(runs)
        else:
            out.append([(dot + str(it), {})])
    return out


def sections_of(paper):
    """Poster boxes in reading order: [{key, label, paras, figs, accent}], figures attached.

    A figure goes into the section named by its "section" key; otherwise figure 1 goes to
    "How it works", figure 2 to "Headline results", then "General idea", "Contributions".
    A figure with no home gets a box of its own before "Why it matters for us".
    """
    order = paper.get("sections") or [k for k, _ in SECTIONS]
    labels = dict(SECTIONS)
    labels.update(paper.get("section_labels", {}))
    boxes = [{"key": k, "label": labels.get(k, k.replace("_", " ").title()),
              "paras": paras_of(paper[k]), "figs": [], "accent": k in ACCENT_SECTIONS}
             for k in order if paper.get(k)]
    by_key = {b["key"]: b for b in boxes}
    homes = [k for k in FIGURE_HOMES if k in by_key]
    for i, fig in enumerate(figures_of(paper)):
        fig["_aspect"] = aspect_of(fig.get("path"))
        home = fig.get("section") if fig.get("section") in by_key else \
            next((k for k in homes if not by_key[k]["figs"]), None)
        if home:
            by_key[home]["figs"].append(fig)
            continue
        at = next((j for j, b in enumerate(boxes) if b["accent"]), len(boxes))
        boxes.insert(at, {"key": f"figure{i + 1}", "label": fig.get("label", "Figure"),
                          "paras": [], "figs": [fig], "accent": False})
    return boxes


def aspect_of(path):
    size = image_size(path) if path and os.path.exists(path) else None
    return size[0] / size[1] if size and size[1] else 1.6


def fig_dims(fig, w, scale):
    """(width, height) of a figure drawn at most w wide, at the given scale of its full size."""
    a = fig["_aspect"]
    natural = w / a
    h = min(natural, max(FIG_MIN_H, min(natural, FIG_MAX_H) * scale))
    return h * a, h


def caption_h(fig, w):
    return est_height([fig["caption"]], w, CAP_SIZE, 1.15, POSTER_CHAR_W) + 0.02 if fig.get("caption") else 0.0


def is_beside(box):
    """Tall or square figures sit beside the text, as on a real poster; wide ones go below."""
    figs = box["figs"]
    if len(figs) != 1 or not box["paras"]:
        return False
    place = figs[0].get("place", "auto")
    return place == "beside" or (place == "auto" and figs[0]["_aspect"] < 1.0)


def box_height(box, w, size, scale):
    inner = w - 2 * BOX_PAD
    if is_beside(box):
        fig_w = inner * 0.46
        text_h = est_height(box["paras"], inner - fig_w - 0.08, size, LINE, POSTER_CHAR_W)
        body = max(text_h, fig_dims(box["figs"][0], fig_w, scale)[1] + caption_h(box["figs"][0], fig_w))
    else:
        body = est_height(box["paras"], inner, size, LINE, POSTER_CHAR_W) if box["paras"] else 0.0
        for f in box["figs"]:
            body += FIG_GAP + fig_dims(f, inner, scale)[1] + caption_h(f, inner)
    return HEAD_H + BOX_PAD + body + BOX_PAD


def column_height(heights):
    return sum(heights) + BOX_GAP * max(0, len(heights) - 1)


def partition(heights, ncol, bounds=None):
    """Split boxes, in order, into ncol columns with the shortest tallest column."""
    n = len(heights)
    if bounds:
        return max(column_height(heights[a:b]) for a, b in zip(bounds, bounds[1:])), bounds
    best = None
    for cuts in itertools.combinations(range(1, n), max(0, min(ncol, n) - 1)):
        b = (0,) + cuts + (n,)
        tallest = max(column_height(heights[i:j]) for i, j in zip(b, b[1:]))
        if best is None or tallest < best[0] - 1e-9:
            best = (tallest, b)
    return best


def fixed_bounds(boxes, breaks):
    """Column bounds from "column_breaks": the section keys that start column 2, 3, ..."""
    if not breaks:
        return None
    keys = [b["key"] for b in boxes]
    starts = sorted({keys.index(k) for k in breaks if k in keys} - {0})
    return (0,) + tuple(starts) + (len(boxes),)


def fit_poster(boxes, ncol, room, bounds):
    """Largest body size and figure scale at which the boxes fit the columns."""
    ncol = len(bounds) - 1 if bounds else max(1, min(ncol, len(boxes)))
    col_w = (PS_W - COL_GAP * (ncol - 1)) / ncol
    steps = int(round((BODY_MAX - BODY_MIN) / BODY_STEP))
    sizes = [BODY_MAX - i * BODY_STEP for i in range(steps + 1)]
    scales = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
    score = lambda c: (c[0] - BODY_MIN) / (BODY_MAX - BODY_MIN) + (c[1] - 0.5) / 0.5
    last = None
    for size, scale in sorted(((s, f) for s in sizes for f in scales), key=score, reverse=True):
        tallest, b = partition([box_height(x, col_w, size, scale) for x in boxes], ncol, bounds)
        last = (size, scale, b, col_w, tallest - room)
        if tallest <= room:
            return size, scale, b, col_w, 0.0
    size, scale = BODY_MIN, scales[-1]
    tallest, b = partition([box_height(x, col_w, size, scale) for x in boxes], ncol, bounds)
    return size, scale, b, col_w, tallest - room


def place_figure(cv, fig, x, y, w, h, cap_w, cap_x, warn):
    path = fig.get("path")
    if not path or not os.path.exists(path):
        warn.append(f"figure missing: {path}")
        cv.rect(x, y, w, h, "white", "red", 1.0, True)
        cv.text(x, y, w, h, "figure not captured", size=8.5, color="title", align="ctr", anchor="ctr")
    else:
        if not os.path.exists(os.path.splitext(path)[0] + ".json"):
            warn.append(f"no capture provenance beside {path}; re-run figure_grab.py")
        cv.image(path, x, y, w, h)
    ch = caption_h(fig, cap_w)
    if ch:
        cv.text(cap_x, y + h + 0.01, cap_w, ch, fig["caption"], size=CAP_SIZE, color="muted", line=1.15)
    return h + ch


def draw_box(cv, box, x, y, w, h, size, scale, colors, warn):
    head = colors["accent"] if box["accent"] else colors["header"]
    cv.rect(x, y, w, h, colors["accent_fill"] if box["accent"] else "white", head, 0.75)
    cv.rect(x, y, w, HEAD_H, head, None)
    cv.text(x + BOX_PAD, y, w - 2 * BOX_PAD, HEAD_H, box["label"].upper(), size=HEAD_SIZE,
            color="white", bold=True, anchor="ctr", wrap=False, spacing=60, line=1.0)
    inner = w - 2 * BOX_PAD
    cx, cy = x + BOX_PAD, y + HEAD_H + BOX_PAD
    if is_beside(box):
        fig = box["figs"][0]
        fig_w = inner * 0.46
        tw = inner - fig_w - 0.08
        cv.text(cx, cy, tw, est_height(box["paras"], tw, size, LINE, POSTER_CHAR_W), box["paras"],
                size=size, color="ink", line=LINE)
        fx = cx + tw + 0.08
        fw, fh = fig_dims(fig, fig_w, scale)
        place_figure(cv, fig, fx + (fig_w - fw) / 2, cy, fw, fh, fig_w, fx, warn)
        return
    if box["paras"]:
        th = est_height(box["paras"], inner, size, LINE, POSTER_CHAR_W)
        cv.text(cx, cy, inner, th, box["paras"], size=size, color="ink", line=LINE)
        cy += th
    for f in box["figs"]:
        cy += FIG_GAP
        fw, fh = fig_dims(f, inner, scale)
        cy += place_figure(cv, f, cx + (inner - fw) / 2, cy, fw, fh, inner, cx, warn)


def poster_banner(cv, paper, theme, kicker, colors):
    cv.rect(0, 0, SLIDE_W, BANNER_H, colors["banner"], None)
    cv.rect(0, 0, 0.10, BANNER_H, colors["accent"], None)
    hl = paper.get("headline")
    right = SLIDE_W - PS_X - (3.35 if hl else 0.0)
    tx = 0.32
    tw = right - tx - 0.15
    kick = paper.get("kicker") or " · ".join(k for k in (kicker, theme.get("name")) if k)
    if kick:
        cv.text(tx, 0.06, tw, 0.20, kick, size=9, color="on_dark_sub", anchor="ctr", wrap=False, line=1.1)
    title, size = paper["title"], 20
    while size > 15 and len(title) * size * 0.55 / 72 > tw:
        size -= 1
    if len(title) * size * 0.55 / 72 > tw and paper.get("slide_title"):
        title, size = paper["slide_title"], 20
        while size > 15 and len(title) * size * 0.55 / 72 > tw:
            size -= 1
    cv.text(tx, 0.27, tw, 0.40, title, size=size, color="white", bold=True, anchor="ctr",
            wrap=False, line=1.1)
    tags = paper.get("tags") or ([paper["tag"]] if paper.get("tag") else [])
    tag_x = tx + tw - sum(tag_width(t) + 0.08 for t in tags)
    for t in tags:
        tag_x += cv.tag(tag_x, 0.71, t, "outline") + 0.08
    meta = meta_line(paper)
    if meta:
        cv.text(tx, 0.70, tw - sum(tag_width(t) + 0.08 for t in tags) - 0.1, 0.22, meta,
                size=10, color="white", anchor="ctr", wrap=False, line=1.1)
    if hl:
        lead, rest = (hl, "") if isinstance(hl, str) else (hl[0], hl[1] if len(hl) > 1 else "")
        hx, hw = SLIDE_W - PS_X - 3.2, 3.2
        cv.rect(hx, 0.12, hw, 0.76, "white", None)
        cv.rect(hx, 0.12, 0.05, 0.76, colors["accent"], None)
        cv.text(hx + 0.14, 0.14, hw - 0.22, 0.36, lead, size=16, color="title", bold=True,
                anchor="ctr", wrap=False, line=1.05)
        if rest:
            cv.text(hx + 0.14, 0.50, hw - 0.22, 0.36, rest, size=7.5, color="ink", line=1.15)


def poster_slide(deck, base, paper, theme, warn, spec=None):
    """One paper, one slide, laid out like the paper's conference poster."""
    spec = spec or {}
    colors = dict(POSTER_COLORS)
    colors.update(spec.get("poster_colors", {}))
    colors.update(theme.get("poster_colors", {}))
    slide = deck.prs.slides.add_slide(deck._blank)
    cv = base.Canvas(deck, slide, paper.get("slide_title") or paper["title"])
    deck.canvases.append(cv)
    poster_banner(cv, paper, theme, spec.get("kicker", ""), colors)

    boxes = sections_of(paper)
    ncol = int(paper.get("poster_columns") or theme.get("poster_columns") or spec.get("poster_columns") or 3)
    room = PS_BOTTOM - PS_TOP
    size, scale, bounds, col_w, over = fit_poster(boxes, ncol, room,
                                                  fixed_bounds(boxes, paper.get("column_breaks")))
    pid = paper.get("id", paper["title"][:30])
    if over > 0.02:
        warn.append(f"paper '{pid}': the boxes need ~{over:.2f} in more than a column holds at the "
                    f"{BODY_MIN} pt floor with figures at half size; cut a section, shorten the "
                    f"bullets, or move detail into the speaker notes")
    for c, (a, b) in enumerate(zip(bounds, bounds[1:])):
        col = boxes[a:b]
        # a short column grows its figures into the free space, then its boxes share the rest
        col_scale = scale
        if any(x["figs"] for x in col):
            s = scale
            while s + 0.05 <= FIG_GROW + 1e-9:
                if column_height([box_height(x, col_w, size, s + 0.05) for x in col]) > room:
                    break
                s += 0.05
            col_scale = s
        heights = [box_height(x, col_w, size, col_scale) for x in col]
        spare = max(0.0, room - column_height(heights)) / len(heights)
        heights = [h + spare for h in heights]      # columns end level, as on a printed poster
        x, y = PS_X + c * (col_w + COL_GAP), PS_TOP
        for box, h in zip(col, heights):
            draw_box(cv, box, x, y, col_w, h, size, col_scale, colors, warn)
            y += h + BOX_GAP

    take = paper.get("takeaway") or theme.get("takeaway")
    foot_w = 10.35
    y = FOOT_Y
    if take:
        lead, rest = (take, "") if isinstance(take, str) else (take[0], take[1] if len(take) > 1 else "")
        cv.strip(PS_X, y, foot_w, 0.36, lead, rest, size=9)
        y += 0.40
    src = " · ".join(s for s in (paper.get("cite") or meta_line(paper), paper.get("url")) if s)
    cv.text(PS_X, y, foot_w, 0.18, f"Source: {src}. Figures reproduced from the original, with attribution.",
            size=7.5, color="muted", wrap=False, line=1.1)

    notes = [paper["title"], meta_line(paper)]
    if paper.get("url"):
        notes.append(paper["url"])
    if paper.get("notes"):
        notes.append("")
        n = paper["notes"]
        notes.append(n if isinstance(n, str) else "\n".join("- " + str(i) for i in n))
    cv.notes("\n".join(notes).strip())
    return cv


# ------------------------------------------------------------------ slides
def grid(n, columns):
    cols = min(columns, n)
    rows = math.ceil(n / cols)
    w = (CONTENT_W - COL_GUTTER * (cols - 1)) / cols
    h = (BLOCK_BOTTOM - BLOCK_TOP - ROW_GUTTER * (rows - 1)) / rows
    cells = []
    for i in range(n):
        r, c = divmod(i, cols)
        cells.append((MARGIN_X + c * (w + COL_GUTTER), BLOCK_TOP + r * (h + ROW_GUTTER), w, h))
    return cells, rows


def theme_slides(deck, base, theme, warn, spec=None):
    papers = theme.get("papers", [])
    per_slide = int(theme.get("per_slide") or theme.get("columns") or 1)
    if theme.get("rows"):
        per_slide *= int(theme["rows"])
    if per_slide == 1:                       # default: a poster slide per paper
        if theme.get("intro", True) is not False and theme.get("title") and len(papers) > 1:
            theme_intro_slide(deck, theme)
        for paper in papers:
            poster_slide(deck, base, paper, theme, warn, spec)
        return
    pages = [papers[i:i + per_slide] for i in range(0, len(papers), per_slide)] or [[]]
    for page_no, page in enumerate(pages, 1):
        title = theme.get("title") or theme.get("name", "")
        if len(pages) > 1:
            title = f"{title} ({page_no}/{len(pages)})"
        cv = deck.slide(title, tagline=theme.get("tagline"))
        cells, rows = grid(len(page), int(theme.get("columns") or 2))
        layout = theme.get("layout") or ("side" if rows > 1 else "stacked")
        for paper, (x, y, w, h) in zip(page, cells):
            block(cv, paper, x, y, w, h, base, layout, warn)
        take = theme.get("takeaway")
        if take:
            lead, rest = (take, "") if isinstance(take, str) else (take[0], take[1] if len(take) > 1 else "")
            cv.takeaway(lead, rest)
        notes = "\n\n".join(f"{p['title']}\n{meta_line(p)}\n{p.get('notes', '')}".strip() for p in page)
        if notes:
            cv.notes(notes)


def theme_intro_slide(deck, theme):
    """Divider before a theme's poster slides: the conclusion, then the papers in it."""
    cv = deck.slide(theme["title"], tagline=theme.get("tagline"))
    papers = theme.get("papers", [])
    items = []
    for p in papers:
        items.append([p.get("slide_title") or p["title"],
                      (p.get("one_line") or p.get("does") or p.get("idea_line") or "")])
    cv.section(MARGIN_X, 1.42, CONTENT_W, theme.get("name", "In this theme"))
    paras = []
    for i, (t, why) in enumerate(items, 1):
        runs = [(f"{i:02d}  {t}", {"bold": True, "color": "ink"})]
        if why:
            runs.append(("   " + (why if isinstance(why, str) else str(why)), {"color": "body"}))
        paras.append(runs)
    cv.text(MARGIN_X, 1.78, CONTENT_W, BLOCK_BOTTOM - 1.78, paras, size=11, color="body", line=1.7)
    take = theme.get("intro_takeaway")
    if take:
        lead, rest = (take, "") if isinstance(take, str) else (take[0], take[1] if len(take) > 1 else "")
        cv.takeaway(lead, rest)
    return cv


def legend_slide(deck):
    cv = deck.slide("How to read a paper slide", tagline="Every paper gets one slide, in the same order")
    cv.section(MARGIN_X, 1.35, 5.6, "Slide anatomy")
    cv.card(MARGIN_X, 1.65, 5.6, 4.1, "A paper's slide is its poster",
            ["Banner: paper title, authors \u00b7 venue \u00b7 date, tags, the headline number",
             "Three columns of boxes, read top to bottom, left to right:",
             "Problem \u2014 what was broken or missing before",
             "General idea \u2014 the paper's own framing of its approach",
             "How it works \u2014 the mechanism, with the paper's own figure",
             "Contributions \u00b7 Headline results (with the result figure)",
             "Why it is strong \u2014 what holds up under scrutiny",
             "Limits \u2014 the authors' caveats, then ours, marked [inference]",
             "Red box: why it matters for us \u2014 direction plus mechanism"], tag="PEER-REVIEWED", size=9)
    cv.section(6.96, 1.35, 5.6, "Tags mark evidence, not quality")
    rows = [["Tag", "Means"],
            ["PEER-REVIEWED", "accepted at a reviewed venue; numbers reviewed"],
            ["CODE", "public code we could run"],
            ["SELF-REPORTED", "vendor or author numbers, not independently checked"],
            ["PREPRINT", "not reviewed yet"],
            ["WATCH", "early work; evidence too thin to act on"]]
    cv.table(6.96, 1.65, 5.6, rows, col_widths=[1.7, 3.9], row_h=0.44, size=9)
    cv.takeaway("Numbers on a slide are the authors' results on their benchmark.",
                "They are not a prediction for our systems.")


def list_slide(deck, title, items, tagline=None, section=None):
    cv = deck.slide(title, tagline=tagline)
    y = 1.40
    if section:
        cv.section(MARGIN_X, y, CONTENT_W, section)
        y += 0.32
    paras = []
    for it in items:
        if isinstance(it, str):
            paras.append([("· " + it, {})])
        else:
            paras.append([("· " + it.get("title", ""), {"bold": True, "color": "ink"}),
                          (("  " + it["cite"]) if it.get("cite") else "", {"color": "muted", "size": 9}),
                          (("  — " + it["why"]) if it.get("why") else "", {"color": "body"})])
    cv.text(MARGIN_X, y, CONTENT_W, BLOCK_BOTTOM - y, paras, size=10.5, color="body", line=1.5)
    return cv


def next_steps_slide(deck, steps):
    cv = deck.slide(steps.get("title", "What we do next"), tagline=steps.get("tagline"))
    cols = [("read", "Read", "neutral"), ("try", "Try", "dark"), ("watch", "Watch", "dashed")]
    cols = [c for c in cols if steps.get(c[0])]
    w = (CONTENT_W - COL_GUTTER * (len(cols) - 1)) / max(1, len(cols))
    for i, (key, label, variant) in enumerate(cols):
        cv.card(MARGIN_X + i * (w + COL_GUTTER), 1.45, w, 3.9, label,
                steps[key], variant=variant, size=10)
    if steps.get("takeaway"):
        t = steps["takeaway"]
        cv.takeaway(*(t if isinstance(t, list) else [t]))
    return cv


def figure_credits(paper):
    creds = [f.get("caption") for f in figures_of(paper) if f.get("caption")]
    return "; ".join(creds) or paper.get("cite") or "\u2014"


def sources_slide(deck, spec):
    rows = [["Paper", "Venue · date", "Figure credit"]]
    for theme in spec.get("themes", []):
        for p in theme.get("papers", []):
            rows.append([p["title"], meta_line(p), figure_credits(p)])
    if len(rows) == 1:
        return
    per = 9
    pages = [rows[1:][i:i + per] for i in range(0, len(rows) - 1, per)]
    for n, page in enumerate(pages, 1):
        title = "Sources" + (f" ({n}/{len(pages)})" if len(pages) > 1 else "")
        cv = deck.slide(title, tagline="Figures are reproduced from the originals, with attribution")
        cv.table(MARGIN_X, 1.40, CONTENT_W, [rows[0]] + page,
                 col_widths=[5.4, 2.8, 3.58], row_h=0.44, size=8.5)


def write_sources_md(spec, path):
    lines = [f"# Sources — {spec.get('title', '')}", "",
             f"Window: {spec.get('window', 'not stated')}", "",
             "| # | Paper | Authors | Venue | Date | URL | Figure used |",
             "|---|---|---|---|---|---|---|"]
    i = 0
    for theme in spec.get("themes", []):
        for p in theme.get("papers", []):
            i += 1
            lines.append(f"| {i} | {p['title']} | {p.get('authors', '')} | {p.get('venue', '')} | "
                         f"{p.get('date', '')} | {p.get('url', '')} | "
                         f"{figure_credits(p)} |")
    lines += ["", "Figures are reproduced from the original publications for internal discussion, "
                  "with attribution. Check each figure's licence before any external use."]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ------------------------------------------------------------------ build
def build(spec, out, base, quiet=False):
    warn = []
    deck = base.TeamDeck(kicker=spec.get("kicker", ""), corner=spec.get("corner", "triangle"))
    subtitle = spec.get("subtitle") or (f"Recent work, {spec['window']}" if spec.get("window") else "")
    deck.title_slide(spec["title"], subtitle,
                     presenters=spec.get("presenters", []), team=spec.get("team", ""))
    themes = spec.get("themes", [])
    if spec.get("contents", True) and len(themes) > 1:
        deck.contents([t.get("name", t.get("title", "")) for t in themes])
    if spec.get("legend", True):
        legend_slide(deck)
    for theme in themes:
        theme_slides(deck, base, theme, warn, spec)
    if spec.get("also_worth_reading"):
        list_slide(deck, spec.get("also_title", "Also worth reading"), spec["also_worth_reading"],
                   tagline="Screened in the same window, cut from the blocks for the reason given")
    if spec.get("next_steps"):
        next_steps_slide(deck, spec["next_steps"])
    if spec.get("sources", True):
        sources_slide(deck, spec)
    warn += deck.save(out, quiet=True)
    md = os.path.join(os.path.dirname(os.path.abspath(out)), "sources.md")
    write_sources_md(spec, md)
    if not quiet:
        print(f"saved {out} ({len(deck.prs.slides)} slides) and {md}")
        for w in warn:
            print("WARN", w, file=sys.stderr)
    return warn


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("blocks", help="blocks.json")
    ap.add_argument("--out", required=True, help="output .pptx")
    ap.add_argument("--team-deck", help="path to insight-ppt/scripts/team_deck.py")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    base = load_team_deck(args.team_deck)
    with open(args.blocks, encoding="utf-8") as fh:
        spec = json.load(fh)
    root = os.path.dirname(os.path.abspath(args.blocks))
    for theme in spec.get("themes", []):
        for p in theme.get("papers", []):
            if p.get("figure") and not os.path.isabs(p["figure"]):
                p["figure"] = os.path.join(root, p["figure"])
            figs = p.get("figures")
            if figs:
                p["figures"] = [{"path": f} if isinstance(f, str) else dict(f) for f in figs]
                for f in p["figures"]:
                    if f.get("path") and not os.path.isabs(f["path"]):
                        f["path"] = os.path.join(root, f["path"])
    warn = build(spec, args.out, base, args.quiet)
    return 1 if any(w.startswith("figure missing") for w in warn) else 0


if __name__ == "__main__":
    sys.exit(main())
