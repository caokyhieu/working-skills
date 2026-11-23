#!/usr/bin/env python3
"""sysdiag — system diagrams as editable Excalidraw files.

Compiles a small JSON *spec* (groups, nodes, edges, notes) into an .excalidraw file:
layout (row / column / grid / ranks / free), orthogonal edge routing with fanned
ports, request/response pairs, protocol pills, bound text, arrow bindings, and a
lint pass (overlaps, edges through boxes, label collisions, budget). Standard
library only.

Commands
  build <spec.json> [-o OUT.excalidraw] [--theme FILE] [--strict] [--require-evidence]
  lint  <spec.json> [--theme FILE] [--require-evidence]   build in memory, print warnings only
  scan  <repo> [--depth N] [--json] [--spec-out FILE]     inventory a codebase for a system model
  templates                                               list bundled template specs
  new   <template> <out.spec.json>                        copy a template spec to start from

Spec format: references/spec-format.md. Theme: assets/theme.json.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
THEME_PATH = SKILL_DIR / "assets" / "theme.json"
TEMPLATE_DIR = SKILL_DIR / "templates"

SIDES = ("left", "right", "top", "bottom")
HORIZ = ("left", "right")


# ----------------------------------------------------------------------------- utils
def deep_merge(a, b):
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def snap(v, g=4):
    return int(-(-v // g) * g)  # ceil to grid


def seed_of(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16) % 2_000_000_000 + 1


def load_theme(path=None, override=None):
    theme = json.loads(Path(path or THEME_PATH).read_text())
    if override:
        theme = deep_merge(theme, override)
    return theme


class Diag:
    def __init__(self):
        self.warnings = []
        self.errors = []

    def warn(self, msg):
        self.warnings.append(msg)

    def err(self, msg):
        self.errors.append(msg)


# ----------------------------------------------------------------------------- text metrics
NARROW = set("il.,:;|!'`1()[]{}ftIjr ")
WIDE = set("mwMW@%&")


def text_w(s, size, fam, theme):
    base = theme["font"]["char_width"].get(str(fam), 0.58) / 0.56
    if fam == 3:  # monospace: every glyph the same advance
        return len(s) * size * theme["font"]["char_width"]["3"]
    w = 0.0
    for ch in s:
        if ch in NARROW:
            f = 0.32
        elif ch in WIDE:
            f = 0.86
        elif ch.isupper() or ch.isdigit():
            f = 0.66
        elif ord(ch) > 0x2E80:  # CJK
            f = 1.0
        else:
            f = 0.54
        w += f
    return w * size * base


def wrap(text, max_w, size, fam, theme):
    lines = []
    for para in str(text).split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            cand = word if not cur else cur + " " + word
            if text_w(cand, size, fam, theme) <= max_w or not cur:
                cur = cand
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def block_size(lines, size, fam, theme):
    lh = theme["font"]["line_height"]
    w = max((text_w(l, size, fam, theme) for l in lines), default=0)
    return w, len(lines) * size * lh


# ----------------------------------------------------------------------------- model
class Box:
    def __init__(self, spec, kind, parent=None):
        self.spec = spec
        self.kind = kind  # node | group | spacer | note
        self.id = spec.get("id") or ""
        self.parent = parent
        self.children = []
        self.x = self.y = 0.0
        self.w = self.h = 0.0
        self.role = spec.get("role", "default" if kind == "node" else "zone")

    @property
    def rect(self):
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def ancestors(self):
        p, out = self.parent, []
        while p is not None:
            out.append(p)
            p = p.parent
        return out

    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()


def role_style(theme, role, spec=None, diag=None):
    roles = theme["roles"]
    if role not in roles:
        if diag:
            diag.warn(f"unknown role '{role}' — using 'default' (roles: {', '.join(sorted(roles))})")
        role = "default"
    st = dict(roles["default"])
    st.update(roles[role])
    if spec:
        for k in ("bg", "stroke", "fill", "width", "style", "round", "text", "shape", "font", "align"):
            if k in spec:
                st[k] = spec[k]
    return st


def fam_of(theme, name):
    if name is None:
        return theme["font"]["family"]
    if isinstance(name, int):
        return name
    return theme["font"]["families"].get(name, theme["font"]["family"])


# ----------------------------------------------------------------------------- parse
def parse_tree(spec_item, parent, diag, ids):
    if "spacer" in spec_item:
        b = Box({"id": ""}, "spacer", parent)
        b.size = float(spec_item["spacer"])
        return b
    is_group = "children" in spec_item
    b = Box(spec_item, "group" if is_group else "node", parent)
    if not b.id:
        diag.err(f"element without id: {json.dumps(spec_item)[:80]}")
    elif b.id in ids:
        diag.err(f"duplicate id '{b.id}'")
    else:
        ids[b.id] = b
    if is_group:
        for c in spec_item["children"]:
            b.children.append(parse_tree(c, b, diag, ids))
    return b


# ----------------------------------------------------------------------------- measure
def measure_node(b, theme, diag):
    sp, S = b.spec, theme["spacing"]
    st = role_style(theme, b.role, sp, diag)
    b.style = st
    fam = fam_of(theme, st.get("font"))
    size = sp.get("size", st.get("size", theme["font"]["size"]["node"]))
    sub_size = theme["font"]["size"]["sub"]
    field_size = theme["font"]["size"]["field"]
    max_tw = sp.get("max_w", S["node_max_text_w"])
    if "w" in sp:
        max_tw = max(40, sp["w"] - 2 * S["node_pad_x"])
    label = sp.get("label", b.id)
    b.lines = wrap(label, max_tw, size, fam, theme) if st.get("align") != "left" else str(label).split("\n")
    b.fam, b.size = fam, size
    lw, lh = block_size(b.lines, size, fam, theme)
    b.sub_lines = wrap(sp["sub"], max_tw, sub_size, 3, theme) if sp.get("sub") else []
    sw, sh = block_size(b.sub_lines, sub_size, 3, theme) if b.sub_lines else (0, 0)
    b.field_lines = [str(f) for f in sp.get("fields", [])]
    fw, fh = block_size(b.field_lines, field_size, 3, theme) if b.field_lines else (0, 0)
    gap = 4 if b.sub_lines else 0
    fgap = 14 if b.field_lines else 0
    tw = max(lw, sw, fw)
    th = lh + gap + sh + fgap + fh
    shape = st.get("shape", "rect")
    b.shape = sp.get("shape", shape)
    padx, pady = S["node_pad_x"], S["node_pad_y"]
    if b.role == "brand":
        w, h = tw + 8, th + 8
    else:
        w = max(S["node_min_w"], tw + 2 * padx)
        h = max(S["node_min_h"], th + 2 * pady)
        if b.shape == "ellipse":
            w, h = w * 1.25, h * 1.2
        elif b.shape == "diamond":
            w, h = max(w * 1.5, h * 2.2), max(h * 1.6, 64)
        elif b.shape == "db":
            h += 22
    b.w = snap(sp.get("w", w))
    b.h = snap(sp.get("h", h))
    if "w" in sp and any(text_w(word, size, fam, theme) > sp["w"] - 8 for word in str(label).split()):
        diag.warn(f"node '{b.id}': a word in the label is wider than w={sp['w']}; widen it")
    if "h" in sp and th + 8 > sp["h"]:
        diag.warn(f"node '{b.id}': text needs ~{int(th + 2 * pady)}px height but h={sp['h']}")


def title_height(b, theme):
    if not b.spec.get("title"):
        return 0
    size = b.spec.get("title_size", theme["font"]["size"]["group"])
    lines = str(b.spec["title"]).split("\n")
    b.title_lines, b.title_size = lines, size
    return len(lines) * size * theme["font"]["line_height"] + theme["spacing"]["group_title_gap"]


def measure(b, theme, diag, ctx):
    if b.kind == "spacer":
        b.w = b.h = 0
        return
    if b.kind == "node":
        measure_node(b, theme, diag)
        return
    S = theme["spacing"]
    sp = b.spec
    b.style = role_style(theme, b.role, sp, diag)
    for c in b.children:
        measure(c, theme, diag, ctx)
    b.layout = sp.get("layout", "column")
    b.gap = sp.get("gap", S["gap"])
    b.pad = sp.get("pad", S["group_pad"])
    b.title_h = title_height(b, theme)
    kids = b.children
    if b.layout in ("row", "column"):
        main_is_x = b.layout == "row"
        mains, cross = [], []
        for c in kids:
            if c.kind == "spacer":
                mains.append(c.size)
                cross.append(0)
            else:
                mains.append(c.w if main_is_x else c.h)
                cross.append(c.h if main_is_x else c.w)
        inner_main = sum(mains) + b.gap * max(0, len(kids) - 1)
        inner_cross = max(cross, default=0)
        iw, ih = (inner_main, inner_cross) if main_is_x else (inner_cross, inner_main)
    elif b.layout == "grid":
        cols = sp.get("cols", 2)
        rows = [kids[i:i + cols] for i in range(0, len(kids), cols)]
        b.col_w = [max((r[i].w for r in rows if i < len(r)), default=0) for i in range(cols)]
        b.row_h = [max(c.h for c in r) for r in rows]
        gx = sp.get("gap_x", b.gap)
        gy = sp.get("gap_y", b.gap)
        b.gx, b.gy = gx, gy
        iw = sum(b.col_w) + gx * max(0, cols - 1)
        ih = sum(b.row_h) + gy * max(0, len(rows) - 1)
    elif b.layout == "ranks":
        iw, ih = measure_ranks(b, theme, ctx)
    elif b.layout == "free":
        xs = [c.spec.get("at", [0, 0]) for c in kids]
        iw = max((p[0] + c.w for p, c in zip(xs, kids)), default=0)
        ih = max((p[1] + c.h for p, c in zip(xs, kids)), default=0)
    else:
        diag.err(f"group '{b.id}': unknown layout '{b.layout}'")
        iw = ih = 0
    b.inner_w, b.inner_h = iw, ih
    tw = 0
    if b.spec.get("title"):
        tw = max(text_w(l, b.title_size, theme["font"]["family"], theme) for l in b.title_lines) + 16
    b.w = snap(max(iw + 2 * b.pad, tw + 2 * b.pad, sp.get("w", 0)))
    b.h = snap(max(ih + 2 * b.pad + b.title_h, sp.get("h", 0)))


def child_of(group, box):
    """direct child of group that contains box (or None)."""
    cur = box
    while cur is not None and cur.parent is not group:
        cur = cur.parent
    return cur


def measure_ranks(b, theme, ctx):
    S = theme["spacing"]
    kids = [c for c in b.children if c.kind != "spacer"]
    idx = {id(c): i for i, c in enumerate(kids)}
    succ = {i: set() for i in range(len(kids))}
    for e in ctx["edges"]:
        a, z = ctx["ids"].get(e.get("from")), ctx["ids"].get(e.get("to"))
        if not a or not z:
            continue
        ca, cz = child_of(b, a), child_of(b, z)
        if ca is None or cz is None or ca is cz:
            continue
        if e.get("rank_ignore"):
            continue
        succ[idx[id(ca)]].add(idx[id(cz)])
    # break cycles by DFS order
    state, order, back = {}, [], set()

    def dfs(u):
        state[u] = 1
        for v in sorted(succ[u]):
            if state.get(v) == 1:
                back.add((u, v))
            elif v not in state:
                dfs(v)
        state[u] = 2
        order.append(u)

    for u in range(len(kids)):
        if u not in state:
            dfs(u)
    rank = {}
    for u in reversed(order):  # topological
        rank.setdefault(u, 0)
        for v in succ[u]:
            if (u, v) in back:
                continue
            rank[v] = max(rank.get(v, 0), rank[u] + 1)
    for i, c in enumerate(kids):
        if "rank" in c.spec:
            rank[i] = c.spec["rank"]
    nr = max(rank.values(), default=0) + 1
    layers = [[i for i in range(len(kids)) if rank[i] == r] for r in range(nr)]
    pred = {i: [u for u in succ for v in succ[u] if v == i] for i in range(len(kids))}
    # barycenter sweeps
    def bary(layer, neighbours, ref):
        pos = {u: k for k, u in enumerate(ref)}
        cur = {v: k for k, v in enumerate(layer)}

        def key(v):
            ps = [pos[u] for u in neighbours[v] if u in pos]
            return sum(ps) / len(ps) if ps else cur[v]
        layer.sort(key=key)

    for _ in range(4):
        for r in range(1, nr):
            bary(layers[r], pred, layers[r - 1])
        for r in range(nr - 2, -1, -1):
            bary(layers[r], succ, layers[r + 1])
    b.rank_layers = [[kids[i] for i in L] for L in layers]
    b.dir = b.spec.get("dir", ctx["direction"])
    rg = b.spec.get("rank_gap", S["rank_gap"])
    b.rank_gap = rg
    if b.dir == "LR":
        widths = [max((c.w for c in L), default=0) for L in b.rank_layers]
        heights = [sum(c.h for c in L) + b.gap * max(0, len(L) - 1) for L in b.rank_layers]
        b.rank_sizes = widths
        return sum(widths) + rg * max(0, nr - 1), max(heights, default=0)
    heights = [max((c.h for c in L), default=0) for L in b.rank_layers]
    widths = [sum(c.w for c in L) + b.gap * max(0, len(L) - 1) for L in b.rank_layers]
    b.rank_sizes = heights
    return max(widths, default=0), sum(heights) + rg * max(0, nr - 1)


# ----------------------------------------------------------------------------- place
def justify_offsets(free, n, mode, gap):
    if n == 0:
        return 0, gap
    if mode == "center":
        return free / 2, gap
    if mode == "end":
        return free, gap
    if mode == "space-between" and n > 1:
        return 0, gap + free / (n - 1)
    if mode == "space-around":
        return free / (2 * n), gap + free / n
    if mode == "space-evenly":
        return free / (n + 1), gap + free / (n + 1)
    return 0, gap


def cross_pos(start, avail, size, align):
    if align == "center":
        return start + (avail - size) / 2
    if align == "end":
        return start + avail - size
    return start


def set_size(c, w=None, h=None):
    if c.kind == "spacer":
        return
    if w is not None:
        c.w = snap(w)
    if h is not None:
        c.h = snap(h)


def place(b, x, y, theme):
    b.x, b.y = x, y
    if b.kind != "group":
        return
    sp = b.spec
    cx, cy = x + b.pad, y + b.pad + b.title_h
    aw, ah = b.w - 2 * b.pad, b.h - 2 * b.pad - b.title_h
    align = sp.get("align", "center" if b.layout in ("row", "column") else "start")
    justify = sp.get("justify", "start")
    kids = b.children
    if b.layout in ("row", "column"):
        rowm = b.layout == "row"
        if align == "stretch":
            for c in kids:
                if c.kind != "spacer" and not c.spec.get("align_self"):
                    set_size(c, h=ah) if rowm else set_size(c, w=aw)
        sizes = [(c.size if c.kind == "spacer" else (c.w if rowm else c.h)) for c in kids]
        used = sum(sizes) + b.gap * max(0, len(kids) - 1)
        start, gap = justify_offsets((aw if rowm else ah) - used, len(kids), justify, b.gap)
        cur = (cx if rowm else cy) + start
        for c, s in zip(kids, sizes):
            al = c.spec.get("align_self", "start" if align == "stretch" else align)
            if rowm:
                place(c, cur, cross_pos(cy, ah, c.h, al), theme)
            else:
                place(c, cross_pos(cx, aw, c.w, al), cur, theme)
            cur += s + gap
    elif b.layout == "grid":
        cols = sp.get("cols", 2)
        yy = cy
        for r, rh in enumerate(b.row_h):
            xx = cx
            for ci in range(cols):
                k = r * cols + ci
                if k >= len(kids):
                    break
                c = kids[k]
                if align == "stretch":
                    set_size(c, w=b.col_w[ci], h=rh)
                place(c, cross_pos(xx, b.col_w[ci], c.w, "center" if align == "center" else "start"),
                      cross_pos(yy, rh, c.h, "center" if align == "center" else "start"), theme)
                xx += b.col_w[ci] + b.gx
            yy += rh + b.gy
    elif b.layout == "ranks":
        lr = b.dir == "LR"
        cur = cx if lr else cy
        for L, rs in zip(b.rank_layers, b.rank_sizes):
            total = sum((c.h if lr else c.w) for c in L) + b.gap * max(0, len(L) - 1)
            avail = ah if lr else aw
            off = cur
            s = (cy if lr else cx) + (avail - total) / 2
            for c in L:
                if lr:
                    place(c, off + (rs - c.w) / 2, s, theme)
                    s += c.h + b.gap
                else:
                    place(c, s, off + (rs - c.h) / 2, theme)
                    s += c.w + b.gap
            cur += rs + b.rank_gap
    elif b.layout == "free":
        for c in kids:
            at = c.spec.get("at", [0, 0])
            place(c, cx + at[0], cy + at[1], theme)


# ----------------------------------------------------------------------------- geometry helpers
def inter(r1, r2, pad=0):
    return not (r1[2] <= r2[0] + pad or r2[2] <= r1[0] + pad or r1[3] <= r2[1] + pad or r2[3] <= r1[1] + pad)


def seg_hits_rect(p, q, r, shrink=2):
    x1, y1, x2, y2 = r[0] + shrink, r[1] + shrink, r[2] - shrink, r[3] - shrink
    if x1 >= x2 or y1 >= y2:
        return False
    if abs(p[1] - q[1]) < 0.5:  # horizontal
        y = p[1]
        lo, hi = sorted((p[0], q[0]))
        return y1 < y < y2 and lo < x2 and hi > x1
    if abs(p[0] - q[0]) < 0.5:  # vertical
        x = p[0]
        lo, hi = sorted((p[1], q[1]))
        return x1 < x < x2 and lo < y2 and hi > y1
    # diagonal: sample
    for t in [i / 20 for i in range(1, 20)]:
        xx, yy = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        if x1 < xx < x2 and y1 < yy < y2:
            return True
    return False


def side_point(r, side, c):
    if side == "left":
        return (r[0], c)
    if side == "right":
        return (r[2], c)
    if side == "top":
        return (c, r[1])
    return (c, r[3])


def outward(side):
    return {"left": (-1, 0), "right": (1, 0), "top": (0, -1), "bottom": (0, 1)}[side]


def auto_sides(A, B, direction="LR"):
    ax1, ay1, ax2, ay2 = A
    bx1, by1, bx2, by2 = B
    if bx1 <= ax1 and bx2 >= ax2 and by1 <= ay1 and by2 >= ay2:  # B contains A
        return ("top", "top")
    if ax1 <= bx1 and ax2 >= bx2 and ay1 <= by1 and ay2 >= by2:
        return ("top", "top")
    dx = bx1 - ax2 if bx1 >= ax2 else (ax1 - bx2 if ax1 >= bx2 else -1)
    dy = by1 - ay2 if by1 >= ay2 else (ay1 - by2 if ay1 >= by2 else -1)
    if direction == "LR":
        horiz = dx >= 0 and (dy < 0 or dx >= 24 or dx * 1.2 >= dy)
    else:
        horiz = dx >= 0 and (dy < 24 and (dy < 0 or dx * 1.2 >= dy))
    if horiz:
        return ("right", "left") if bx1 >= ax2 else ("left", "right")
    if dy >= 0:
        return ("bottom", "top") if by1 >= ay2 else ("top", "bottom")
    # overlapping: use centers
    acx, acy = (ax1 + ax2) / 2, (ay1 + ay2) / 2
    bcx, bcy = (bx1 + bx2) / 2, (by1 + by2) / 2
    if abs(bcx - acx) >= abs(bcy - acy):
        return ("right", "left") if bcx > acx else ("left", "right")
    return ("bottom", "top") if bcy > acy else ("top", "bottom")


def simplify(pts):
    out = []
    for p in pts:
        p = (round(p[0], 1), round(p[1], 1))
        if out and abs(out[-1][0] - p[0]) < 0.5 and abs(out[-1][1] - p[1]) < 0.5:
            continue
        out.append(p)
    # drop collinear middles
    i = 1
    while i < len(out) - 1:
        a, b, c = out[i - 1], out[i], out[i + 1]
        if (abs(a[0] - b[0]) < 0.5 and abs(b[0] - c[0]) < 0.5) or (abs(a[1] - b[1]) < 0.5 and abs(b[1] - c[1]) < 0.5):
            out.pop(i)
        else:
            i += 1
    return out


def offset_polyline(pts, d):
    """offset an orthogonal polyline by d to the LEFT of travel (screen coords)."""
    if len(pts) < 2 or d == 0:
        return list(pts)
    segs = []
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = (dx * dx + dy * dy) ** 0.5 or 1
        nx, ny = dy / L, -dx / L
        segs.append(((a[0] + nx * d, a[1] + ny * d), (b[0] + nx * d, b[1] + ny * d), abs(dx) > abs(dy)))
    out = [segs[0][0]]
    for s1, s2 in zip(segs, segs[1:]):
        if s1[2] and not s2[2]:
            out.append((s2[0][0], s1[0][1]))
        elif not s1[2] and s2[2]:
            out.append((s1[0][0], s2[0][1]))
        else:
            out.append(s1[1])
    out.append(segs[-1][1])
    return out


# ----------------------------------------------------------------------------- routing
class Router:
    def __init__(self, obstacles, theme):
        self.obstacles = obstacles  # list of (box, rect)
        self.used_v = []
        self.used_h = []
        self.theme = theme

    def cost(self, pts, skip):
        c = 0.0
        for p, q in zip(pts, pts[1:]):
            for bx, r in self.obstacles:
                if bx in skip:
                    continue
                if seg_hits_rect(p, q, r):
                    c += 100
            if abs(p[0] - q[0]) < 0.5:
                lo, hi = sorted((p[1], q[1]))
                for x, a, b in self.used_v:
                    if abs(x - p[0]) < 10 and lo < b and hi > a:
                        c += 15
            elif abs(p[1] - q[1]) < 0.5:
                lo, hi = sorted((p[0], q[0]))
                for y, a, b in self.used_h:
                    if abs(y - p[1]) < 10 and lo < b and hi > a:
                        c += 15
        c += 0.5 * (len(pts) - 2)
        return c

    def commit(self, pts):
        for p, q in zip(pts, pts[1:]):
            if abs(p[0] - q[0]) < 0.5:
                self.used_v.append((p[0], *sorted((p[1], q[1]))))
            elif abs(p[1] - q[1]) < 0.5:
                self.used_h.append((p[1], *sorted((p[0], q[0]))))

    def route(self, p1, s1, p2, s2, skip, mode="auto", via=None, stub=24):
        if via:
            pts = [p1]
            for v in via:
                v = tuple(v)
                last = pts[-1]
                if abs(last[0] - v[0]) > 0.5 and abs(last[1] - v[1]) > 0.5:
                    pts.append((v[0], last[1]) if pts[-1] is p1 and s1 in HORIZ else (last[0], v[1]))
                pts.append(v)
            last = pts[-1]
            if abs(last[0] - p2[0]) > 0.5 and abs(last[1] - p2[1]) > 0.5:
                pts.append((p2[0], last[1]) if s2 not in HORIZ else (last[0], p2[1]))
            pts.append(p2)
            return simplify(pts)
        if mode == "straight":
            return [p1, p2]
        cands = []
        o1, o2 = outward(s1), outward(s2)
        h1, h2 = s1 in HORIZ, s2 in HORIZ
        if h1 and h2:
            if abs(p1[1] - p2[1]) < 0.5 and (p2[0] - p1[0]) * o1[0] > 0 and (p1[0] - p2[0]) * o2[0] > 0:
                cands.append([p1, p2])
            lo, hi = sorted((p1[0] + o1[0] * 12, p2[0] + o2[0] * 12))
            if (p2[0] - p1[0]) * o1[0] > 24 and (p1[0] - p2[0]) * o2[0] > 24:
                for m in self._range(lo, hi):
                    cands.append([p1, (m, p1[1]), (m, p2[1]), p2])
            else:  # U / wrap-around
                for k in (1, 2, 3, 5):
                    if o1[0] == o2[0]:
                        m = (max(p1[0], p2[0]) if o1[0] > 0 else min(p1[0], p2[0])) + o1[0] * stub * k
                        cands.append([p1, (m, p1[1]), (m, p2[1]), p2])
                    else:
                        a = (p1[0] + o1[0] * stub, p1[1])
                        bq = (p2[0] + o2[0] * stub, p2[1])
                        for ym in self._yspan(p1[1], p2[1], k):
                            cands.append([p1, a, (a[0], ym), (bq[0], ym), bq, p2])
        elif not h1 and not h2:
            if abs(p1[0] - p2[0]) < 0.5 and (p2[1] - p1[1]) * o1[1] > 0 and (p1[1] - p2[1]) * o2[1] > 0:
                cands.append([p1, p2])
            lo, hi = sorted((p1[1] + o1[1] * 12, p2[1] + o2[1] * 12))
            if (p2[1] - p1[1]) * o1[1] > 24 and (p1[1] - p2[1]) * o2[1] > 24:
                for m in self._range(lo, hi):
                    cands.append([p1, (p1[0], m), (p2[0], m), p2])
            else:
                for k in (1, 2, 3, 5):
                    if o1[1] == o2[1]:
                        m = (max(p1[1], p2[1]) if o1[1] > 0 else min(p1[1], p2[1])) + o1[1] * stub * k
                        cands.append([p1, (p1[0], m), (p2[0], m), p2])
                    else:
                        a = (p1[0], p1[1] + o1[1] * stub)
                        bq = (p2[0], p2[1] + o2[1] * stub)
                        for xm in self._yspan(p1[0], p2[0], k):
                            cands.append([p1, a, (xm, a[1]), (xm, bq[1]), bq, p2])
        else:
            if h1:  # horizontal then vertical
                corner = (p2[0], p1[1])
                ok = (corner[0] - p1[0]) * o1[0] > 0 and (corner[1] - p2[1]) * o2[1] > 0
                if ok:
                    cands.append([p1, corner, p2])
                a = (p1[0] + o1[0] * stub, p1[1])
                bq = (p2[0], p2[1] + o2[1] * stub)
                cands.append([p1, a, (a[0], bq[1]), bq, p2])
                for m in self._range(*sorted((p1[0], p2[0]))):
                    if (m - p1[0]) * o1[0] > 8:
                        cands.append([p1, (m, p1[1]), (m, bq[1]), bq, p2])
            else:
                corner = (p1[0], p2[1])
                ok = (corner[1] - p1[1]) * o1[1] > 0 and (corner[0] - p2[0]) * o2[0] > 0
                if ok:
                    cands.append([p1, corner, p2])
                a = (p1[0], p1[1] + o1[1] * stub)
                bq = (p2[0] + o2[0] * stub, p2[1])
                cands.append([p1, a, (bq[0], a[1]), bq, p2])
                for m in self._range(*sorted((p1[1], p2[1]))):
                    if (m - p1[1]) * o1[1] > 8:
                        cands.append([p1, (p1[0], m), (bq[0], m), bq, p2])
        if not cands:
            cands = [[p1, p2]]
        best = None
        for c in cands:
            c = simplify(c)
            mid_bias = 0
            if len(c) == 4:
                if abs(c[1][0] - c[2][0]) < 0.5:  # vertical middle
                    mid = (p1[0] + p2[0]) / 2
                    mid_bias = abs(c[1][0] - mid) / 400
                else:
                    mid = (p1[1] + p2[1]) / 2
                    mid_bias = abs(c[1][1] - mid) / 400
            score = self.cost(c, skip) + mid_bias
            if best is None or score < best[0]:
                best = (score, c)
        return best[1]

    @staticmethod
    def _range(lo, hi):
        if hi - lo < 8:
            return [(lo + hi) / 2]
        mid = (lo + hi) / 2
        out = [mid]
        step = 8
        k = 1
        while mid - k * step >= lo or mid + k * step <= hi:
            if mid - k * step >= lo:
                out.append(mid - k * step)
            if mid + k * step <= hi:
                out.append(mid + k * step)
            k += 1
        return out

    @staticmethod
    def _yspan(a, b, k):
        mid = (a + b) / 2
        return [mid, mid + 40 * k, mid - 40 * k]


# ----------------------------------------------------------------------------- element builders
class Emitter:
    def __init__(self, theme, sketch=False):
        self.theme = theme
        self.els = []
        self.by_id = {}
        self.rough = 1 if sketch else 0
        self.n = 0

    def uid(self, base):
        self.n += 1
        return f"{base}__{self.n}" if base else f"el{self.n}"

    def base(self, eid, typ, x, y, w, h, stroke="#1e1e1e", bg="transparent", fill="solid", width=1,
             style="solid", round_=False, groups=None, custom=None):
        el = {
            "id": eid, "type": typ, "x": round(x, 2), "y": round(y, 2), "width": round(w, 2), "height": round(h, 2),
            "angle": 0, "strokeColor": stroke, "backgroundColor": bg, "fillStyle": fill, "strokeWidth": width,
            "strokeStyle": style, "roughness": self.rough, "opacity": 100, "groupIds": list(groups or []),
            "frameId": None, "roundness": ({"type": 3} if round_ else None), "seed": seed_of(eid),
            "version": 1, "versionNonce": seed_of(eid + "#"), "isDeleted": False, "boundElements": [],
            "updated": 1, "link": None, "locked": False,
        }
        if custom:
            el["customData"] = custom
        self.els.append(el)
        self.by_id[eid] = el
        return el

    def text(self, eid, x, y, lines, size, fam, color="#1e1e1e", align="center", valign="middle",
             container=None, groups=None, w=None):
        txt = "\n".join(lines)
        tw = w if w is not None else max((text_w(l, size, fam, self.theme) for l in lines), default=0)
        th = len(lines) * size * self.theme["font"]["line_height"]
        el = self.base(eid, "text", x, y, tw, th, stroke=color, groups=groups)
        el.update({"text": txt, "fontSize": size, "fontFamily": fam, "textAlign": align, "verticalAlign": valign,
                   "containerId": container, "originalText": txt, "autoResize": True,
                   "lineHeight": self.theme["font"]["line_height"]})
        if container:
            self.by_id[container]["boundElements"].append({"type": "text", "id": eid})
        return el

    def arrow(self, eid, pts, stroke, width, style, start=None, end=None, head="arrow", tail=None, groups=None,
              custom=None, kind="arrow"):
        x0, y0 = pts[0]
        rel = [[round(p[0] - x0, 2), round(p[1] - y0, 2)] for p in pts]
        xs = [p[0] for p in rel]
        ys = [p[1] for p in rel]
        el = self.base(eid, kind, x0, y0, max(xs) - min(xs), max(ys) - min(ys), stroke=stroke, width=width,
                       style=style, groups=groups, custom=custom)
        el.update({"points": rel, "lastCommittedPoint": None,
                   "startBinding": ({"elementId": start, "focus": 0, "gap": 1} if start else None),
                   "endBinding": ({"elementId": end, "focus": 0, "gap": 1} if end else None),
                   "startArrowhead": tail, "endArrowhead": head})
        if kind == "arrow":
            el["elbowed"] = False
        for b in (start, end):
            if b and b in self.by_id:
                self.by_id[b]["boundElements"].append({"type": "arrow", "id": eid})
        return el


# ----------------------------------------------------------------------------- build
def build(spec, theme, diag, require_evidence=False):
    if spec.get("kind") == "sequence":
        return build_sequence(spec, theme, diag)
    ids = {}
    ctx = {"edges": spec.get("edges", []), "ids": ids, "direction": spec.get("direction", "LR")}
    root_spec = spec.get("root")
    if root_spec is None:
        root_spec = {"id": "__root", "layout": "row" if ctx["direction"] == "LR" else "column",
                     "children": spec.get("children", []), "role": "none", "pad": 0}
    root_spec = dict(root_spec)
    root_spec.setdefault("id", "__root")
    root_spec.setdefault("pad", 0)
    root_spec.setdefault("gap", spec.get("gap", 80))
    root_spec.setdefault("role", "none")
    theme["roles"].setdefault("none", {"bg": "transparent", "stroke": "transparent"})
    root = parse_tree(root_spec, None, diag, ids)
    if diag.errors:
        return None
    measure(root, theme, diag, ctx)
    place(root, 0, 0, theme)

    em = Emitter(theme, sketch=spec.get("style") == "sketch")
    leaves = [b for b in root.walk() if b.kind == "node"]
    groups = [b for b in root.walk() if b.kind == "group" and b is not root]

    # notes (positioned after layout; may be edge endpoints)
    notes = []
    for i, n in enumerate(spec.get("notes", [])):
        nb = Box(n, "note")
        nb.id = n.get("id") or f"note{i + 1}"
        size = n.get("size", theme["font"]["size"]["note"])
        fam = fam_of(theme, n.get("font"))
        nb.lines = wrap(n["text"], n.get("w", 260), size, fam, theme)
        nb.size, nb.fam = size, fam
        nb.w, nb.h = block_size(nb.lines, size, fam, theme)
        if "at" in n:
            nb.x, nb.y = n["at"]
        elif n.get("near") in ids:
            r = ids[n["near"]].rect
            pos = n.get("pos", "below")
            g = n.get("gap", 8)
            cxm, cym = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            nb.x = {"left": r[0] - g - nb.w, "right": r[2] + g}.get(pos.split("-")[-1] if "-" in pos else pos, cxm - nb.w / 2)
            if pos in ("above", "below"):
                nb.x = cxm - nb.w / 2
            if pos.endswith("left") and pos != "left":
                nb.x = r[0]
            if pos.endswith("right") and pos != "right":
                nb.x = r[2] - nb.w
            nb.y = {"above": r[1] - g - nb.h, "below": r[3] + g}.get(pos.split("-")[0], cym - nb.h / 2)
            if pos in ("inside-top",):
                nb.x, nb.y = cxm - nb.w / 2, r[1] + g
            nb.x += n.get("dx", 0)
            nb.y += n.get("dy", 0)
        else:
            diag.warn(f"note '{nb.id}' has neither 'at' nor a valid 'near'")
        notes.append(nb)
        ids.setdefault(nb.id, nb)

    # 1. groups (outer first)
    for g in groups:
        st = g.style
        if st.get("bg") == "transparent" and st.get("stroke") == "transparent" and not g.spec.get("title"):
            continue
        em.base(g.id, "rectangle", g.x, g.y, g.w, g.h, stroke=st["stroke"], bg=st["bg"], fill=st["fill"],
                width=st["width"], style=st["style"], round_=st.get("round", False),
                custom={"ev": g.spec["ev"]} if g.spec.get("ev") else None)
        if g.spec.get("title"):
            fam = theme["font"]["family"]
            tpos = g.spec.get("title_pos", "top")
            tw = max(text_w(l, g.title_size, fam, theme) for l in g.title_lines)
            tx = g.x + (g.w - tw) / 2 if tpos == "top" else g.x + 12
            em.text(g.id + "__title", tx, g.y + 10, g.title_lines, g.title_size, fam, color=st["text"],
                    align="center" if tpos == "top" else "left", valign="top")

    # 2. collect edges and ports
    edges = []
    for i, e in enumerate(spec.get("edges", [])):
        a, z = ids.get(e.get("from")), ids.get(e.get("to"))
        if a is None or z is None:
            diag.err(f"edge {i}: unknown endpoint {e.get('from')!r} -> {e.get('to')!r}")
            continue
        s1, s2 = auto_sides(a.rect, z.rect, ctx["direction"])
        s1 = e.get("from_side", s1)
        s2 = e.get("to_side", s2)
        edges.append({"spec": e, "a": a, "z": z, "s1": s1, "s2": s2, "i": i,
                      "pair": bool(e.get("back")), "id": e.get("id", f"e{i + 1}_{a.id}_{z.id}")})
    if diag.errors:
        return None
    S = theme["spacing"]
    slots = {}
    for ed in edges:
        slots.setdefault((id(ed["a"]), ed["s1"]), []).append((ed, "a"))
        slots.setdefault((id(ed["z"]), ed["s2"]), []).append((ed, "z"))

    def other_center(ed, end):
        o = ed["z"] if end == "a" else ed["a"]
        r = o.rect
        return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)

    for (bid, side), lst in slots.items():
        box = lst[0][0][lst[0][1]]
        r = box.rect
        horiz = side in HORIZ
        lo, hi = (r[1], r[3]) if horiz else (r[0], r[2])
        lst.sort(key=lambda t: (other_center(*t)[1] if horiz else other_center(*t)[0], t[0]["i"]))
        n = len(lst)
        for k, (ed, end) in enumerate(lst):
            c = lo + (hi - lo) * (k + 1) / (n + 1)
            ed["c" + end] = c
            ed["n" + end] = n
    # straighten single-slot edges with overlap
    for ed in edges:
        ra, rz = ed["a"].rect, ed["z"].rect
        horiz = ed["s1"] in HORIZ and ed["s2"] in HORIZ
        vert = ed["s1"] not in HORIZ and ed["s2"] not in HORIZ
        need = (S["pair_sep"] if ed["pair"] else 0) + 2 * S["port_margin"]
        if (horiz or vert) and ed["na"] == 1 and ed["nz"] == 1:
            lo = max(ra[1], rz[1]) if horiz else max(ra[0], rz[0])
            hi = min(ra[3], rz[3]) if horiz else min(ra[2], rz[2])
            if hi - lo >= need:
                ed["ca"] = ed["cz"] = (lo + hi) / 2
        for end, key in (("a", "from_port"), ("z", "to_port")):  # explicit fraction 0..1
            if key in ed["spec"]:
                bx = ed[end]
                r = bx.rect
                side = ed["s1"] if end == "a" else ed["s2"]
                f = ed["spec"][key]
                ed["c" + end] = (r[1] + (r[3] - r[1]) * f) if side in HORIZ else (r[0] + (r[2] - r[0]) * f)
        if ed["ca"] is not None and ed["cz"] is not None and (horiz or vert) and not ed["pair"]:
            m = S["port_margin"]
            for end, oth, key in (("z", "a", "to_port"), ("a", "z", "from_port")):
                r = ed[end].rect
                lo, hi = (r[1], r[3]) if horiz else (r[0], r[2])
                if ed["n" + end] == 1 and key not in ed["spec"] and lo + m <= ed["c" + oth] <= hi - m:
                    ed["c" + end] = ed["c" + oth]
                    break
    # 3. route
    obstacles = [(b, b.rect) for b in leaves]
    router = Router(obstacles, theme)
    label_boxes = []
    pending_labels = []
    order = sorted(edges, key=lambda ed: (len(ed["spec"].get("via", [])) == 0, ed["i"]))
    for ed in order:
        e = ed["spec"]
        a, z = ed["a"], ed["z"]
        p1 = side_point(a.rect, ed["s1"], ed["ca"])
        p2 = side_point(z.rect, ed["s2"], ed["cz"])
        skip = {a, z} | set(a.ancestors()) | set(z.ancestors())
        center = router.route(p1, ed["s1"], p2, ed["s2"], skip, e.get("route", "auto"), e.get("via"))
        kind = e.get("kind", "back_pair" if False else ("default"))
        est = dict(theme["edges"].get(e.get("type", "default"), theme["edges"]["default"]))
        for k in ("stroke", "width", "style"):
            if k in e:
                est[k] = e[k]
        head = e.get("head", "arrow")
        head = None if head == "none" else head
        tail = e.get("tail")
        tail = None if tail in (None, "none") else tail
        if e.get("both"):
            tail = head or "arrow"
        ev = e.get("ev")
        custom = {"ev": ev} if ev else None
        if ed["pair"]:
            d = S["pair_sep"] / 2
            fwd = simplify(offset_polyline(center, d))
            bwd = simplify(list(reversed(offset_polyline(center, -d))))
            # keep endpoints on box borders
            em.arrow(ed["id"], fwd, est["stroke"], est["width"], est["style"], start=a.id if a.kind != "note" else None,
                     end=z.id if z.kind != "note" else None, head=head, custom=custom)
            bst = dict(theme["edges"].get(e.get("back_type", "return"), theme["edges"]["return"]))
            em.arrow(ed["id"] + "__back", bwd, bst["stroke"], bst["width"], bst["style"],
                     start=z.id if z.kind != "note" else None, end=a.id if a.kind != "note" else None, head="arrow",
                     custom=custom)
            router.commit(fwd)
            router.commit(bwd)
            if e.get("label"):
                pending_labels.append((ed["id"] + "__lbl", e["label"], fwd, "left", e))
            pending_labels.append((ed["id"] + "__backlbl", e["back"], bwd, "left", e))
            ed["paths"] = [fwd, bwd]
        else:
            em.arrow(ed["id"], center, est["stroke"], est["width"], est["style"],
                     start=a.id if a.kind != "note" else None, end=z.id if z.kind != "note" else None,
                     head=head, tail=tail, custom=custom,
                     kind="line" if (head is None and tail is None and e.get("line")) else "arrow")
            router.commit(center)
            if e.get("label"):
                pending_labels.append((ed["id"] + "__lbl", e["label"], center, e.get("label_side", "auto"), e))
            ed["paths"] = [center]

    # 4. nodes (on top of arrows)
    for b in leaves:
        emit_node(em, b, theme)

    # 5. notes
    for nb in notes:
        n = nb.spec
        em.text(nb.id, nb.x, nb.y, nb.lines, nb.size, nb.fam, color=n.get("color", "#1e1e1e"),
                align=n.get("align", "left"), valign="top")

    # 6. labels
    blockers = [b.rect for b in leaves] + [(nb.x, nb.y, nb.x + nb.w, nb.y + nb.h) for nb in notes]
    for g in groups:
        if g.spec.get("title"):
            tw = max(text_w(l, g.title_size, theme["font"]["family"], theme) for l in g.title_lines)
            tx = g.x + (g.w - tw) / 2 if g.spec.get("title_pos", "top") == "top" else g.x + 12
            blockers.append((tx, g.y + 8, tx + tw, g.y + 10 + g.title_h - 8))
    all_paths = [p for ed in edges for p in ed["paths"]]
    for lid, text, pts, side, e in pending_labels:
        place_label(em, lid, text, pts, side, e, theme, blockers, label_boxes, all_paths, diag,
                    [g.rect for g in groups if g.style.get('stroke') != 'transparent'])

    # 7. title + legend
    els = [x for x in em.els]
    minx, miny, maxx, maxy = bbox(els)
    if spec.get("title"):
        size = theme["font"]["size"]["title"]
        fam = theme["font"]["family"]
        lines = [spec["title"]]
        ty = miny - size * 1.25 - (34 if spec.get("subtitle") else 24)
        em.text("__title", minx, ty, lines, size, fam, align="left", valign="top")
        if spec.get("subtitle"):
            em.text("__subtitle", minx, ty + size * 1.3, [spec["subtitle"]], 14, fam, color="#495057",
                    align="left", valign="top")
    if spec.get("legend"):
        emit_legend(em, spec, theme, leaves, minx, maxy + 40)

    lint(diag, leaves, notes, edges, label_boxes, theme, spec, require_evidence)
    return em


def emit_node(em, b, theme):
    st = b.style
    sp = b.spec
    ev = sp.get("ev")
    custom = {"ev": ev} if ev else None
    x, y, w, h = b.x, b.y, b.w, b.h
    grp = []
    multi = bool(b.sub_lines or b.field_lines)
    shape = b.shape
    if shape == "db":
        gid = b.id + "__g"
        grp = [gid]
        eh = min(22, h * 0.3)
        em.base(b.id + "__bot", "ellipse", x, y + h - eh, w, eh, stroke=st["stroke"], bg=st["bg"], fill=st["fill"],
                width=st["width"], style=st["style"], groups=grp)
        em.base(b.id, "rectangle", x, y + eh / 2, w, h - eh, stroke="transparent", bg=st["bg"], fill=st["fill"],
                width=st["width"], groups=grp, custom=custom)
        em.base(b.id + "__l", "line", x, y + eh / 2, 0, h - eh, stroke=st["stroke"], width=st["width"],
                style=st["style"], groups=grp).update(
            {"points": [[0, 0], [0, h - eh]], "lastCommittedPoint": None, "startBinding": None,
             "endBinding": None, "startArrowhead": None, "endArrowhead": None})
        em.base(b.id + "__r", "line", x + w, y + eh / 2, 0, h - eh, stroke=st["stroke"], width=st["width"],
                style=st["style"], groups=grp).update(
            {"points": [[0, 0], [0, h - eh]], "lastCommittedPoint": None, "startBinding": None,
             "endBinding": None, "startArrowhead": None, "endArrowhead": None})
        em.base(b.id + "__top", "ellipse", x, y, w, eh, stroke=st["stroke"], bg=st["bg"], fill=st["fill"],
                width=st["width"], style=st["style"], groups=grp)
        ty0, th_avail = y + eh, h - eh * 1.5
        multi = True
    else:
        typ = {"ellipse": "ellipse", "diamond": "diamond"}.get(shape, "rectangle")
        if multi:
            grp = [b.id + "__g"]
        em.base(b.id, typ, x, y, w, h, stroke=st["stroke"], bg=st["bg"], fill=st["fill"], width=st["width"],
                style=st["style"], round_=st.get("round", False) and typ == "rectangle", groups=grp, custom=custom)
        ty0, th_avail = y, h
    lh = theme["font"]["line_height"]
    lab_h = len(b.lines) * b.size * lh
    sub_size = theme["font"]["size"]["sub"]
    field_size = theme["font"]["size"]["field"]
    sub_h = len(b.sub_lines) * sub_size * lh + (4 if b.sub_lines else 0)
    if b.field_lines:
        # header at top, fields left-aligned below a divider
        S = theme["spacing"]
        hy = y + S["node_pad_y"]
        lw = max(text_w(l, b.size, b.fam, theme) for l in b.lines)
        em.text(b.id + "__t", x + (w - lw) / 2, hy, b.lines, b.size, b.fam, color=st["text"], groups=grp,
                valign="top")
        yy = hy + lab_h
        if b.sub_lines:
            sw = max(text_w(l, sub_size, 3, theme) for l in b.sub_lines)
            em.text(b.id + "__s", x + (w - sw) / 2, yy + 4, b.sub_lines, sub_size, 3, color="#495057", groups=grp,
                    valign="top")
            yy += sub_h
        dy = yy + 6
        ln = em.base(b.id + "__div", "line", x, dy, w, 0, stroke=st["stroke"], width=1, groups=grp)
        ln.update({"points": [[0, 0], [w, 0]], "lastCommittedPoint": None, "startBinding": None, "endBinding": None,
                   "startArrowhead": None, "endArrowhead": None})
        em.text(b.id + "__f", x + S["node_pad_x"] / 1.5, dy + 8, b.field_lines, field_size, 3, color=st["text"],
                align="left", valign="top", groups=grp)
        return
    total = lab_h + sub_h
    top = ty0 + (th_avail - total) / 2
    align = st.get("align", "center")
    if not multi and shape != "db":
        lw = max(text_w(l, b.size, b.fam, theme) for l in b.lines)
        tx = x + (w - lw) / 2 if align != "left" else x + theme["spacing"]["node_pad_x"]
        em.text(b.id + "__t", tx, top, b.lines, b.size, b.fam, color=st["text"], container=b.id,
                align="left" if align == "left" else "center")
        return
    lw = max(text_w(l, b.size, b.fam, theme) for l in b.lines)
    em.text(b.id + "__t", x + (w - lw) / 2, top, b.lines, b.size, b.fam, color=st["text"], groups=grp,
            valign="top")
    if b.sub_lines:
        sw = max(text_w(l, sub_size, 3, theme) for l in b.sub_lines)
        em.text(b.id + "__s", x + (w - sw) / 2, top + lab_h + 4, b.sub_lines, sub_size, 3,
                color="#495057" if st["text"] == "#1e1e1e" else st["text"], groups=grp, valign="top")


def place_label(em, lid, text, pts, side, e, theme, blockers, placed, paths, diag, group_rects=()):
    style = e.get("label_style", "pill")
    L = theme["labels"].get(style, theme["labels"]["pill"])
    size = e.get("label_size", theme["font"]["size"]["label"])
    fam = theme["font"]["family"]
    lines = str(text).split("\n")
    tw, th = block_size(lines, size, fam, theme)
    w, h = snap(tw + 2 * L["pad_x"], 2), snap(th + 2 * L["pad_y"], 2)
    gap = theme["spacing"]["label_gap"]
    segs = []
    for p, q in zip(pts, pts[1:]):
        ln = abs(p[0] - q[0]) + abs(p[1] - q[1])
        segs.append((ln, p, q))
    def seg_pref(sg):
        ln, p, q = sg
        hz = abs(p[1] - q[1]) < 0.5
        fits = ln >= (w + 16 if hz else h + 16)
        return (not fits, not hz, -ln)
    segs.sort(key=seg_pref)
    want = e.get("label_at")
    cands = []
    for rank, (ln, p, q) in enumerate(segs[:3]):
        hz = abs(p[1] - q[1]) < 0.5
        dx, dy = q[0] - p[0], q[1] - p[1]
        # left-of-travel side
        left_is_above = dx > 0 if hz else None
        left_is_right = dy > 0 if not hz else None
        for t in ([want] if want is not None else [0.5, 0.35, 0.65, 0.2, 0.8]):
            mx, my = p[0] + dx * t, p[1] + dy * t
            if hz:
                pref = side
                above_first = True
                if pref == "left":
                    above_first = left_is_above
                elif pref in ("below", "right"):
                    above_first = False
                for above in ([above_first, not above_first] if pref in ("auto", "left") else [above_first]):
                    yy = my - gap - h if above else my + gap
                    cands.append((rank, (mx - w / 2, yy)))
                if pref == "on":
                    cands.insert(0, (rank, (mx - w / 2, my - h / 2)))
            else:
                right_first = True
                if side == "left":
                    right_first = left_is_right
                elif side in ("above", "left-side"):
                    right_first = False
                for right in [right_first, not right_first]:
                    xx = mx + gap if right else mx - gap - w
                    cands.append((rank, (xx, my - h / 2)))
                if side == "on":
                    cands.insert(0, (rank, (mx - w / 2, my - h / 2)))
    best = None
    for k, (rank, (x, y)) in enumerate(cands):
        r = (x, y, x + w, y + h)
        score = k * 0.01 + rank * 0.5
        for b in blockers:
            if inter(r, b, -1):
                score += 10
        for b in placed:
            if inter(r, b, -2):
                score += 10
        for g in group_rects:
            if inter(r, g) and not (r[0] >= g[0] and r[1] >= g[1] and r[2] <= g[2] and r[3] <= g[3]):
                score += 4  # straddles a container border
        for pth in paths:
            if pth is pts:
                continue
            for p, q in zip(pth, pth[1:]):
                if seg_hits_rect(p, q, r, shrink=0):
                    score += 3
        if best is None or score < best[0]:
            best = (score, r)
    if best is None:
        return
    x, y = best[1][0], best[1][1]
    if style == "text":
        em.text(lid, x + L["pad_x"], y + L["pad_y"], lines, size, fam, color=L["text"], align="center", valign="top")
    else:
        em.base(lid, "rectangle", x, y, w, h, stroke=L["stroke"], bg=L["bg"], fill="solid", width=1, round_=True)
        em.text(lid + "__t", x + (w - tw) / 2, y + (h - th) / 2, lines, size, fam, color=L["text"], container=lid)
    placed.append(best[1])
    if best[0] >= 10:
        longest = max((sg[0] for sg in segs), default=0)
        hint = f"; its longest segment is {int(longest)}px but the label needs ~{int(w + 24)}px — raise the gap" if longest < w + 24 else ""
        diag.warn(f"label '{text}' could not avoid a box or another label{hint} (or set label_at / label_side)")


def emit_legend(em, spec, theme, leaves, x, y):
    items = spec["legend"]
    if items is True:
        seen = []
        for b in leaves:
            if b.role not in seen and b.role not in ("brand", "default", "none"):
                seen.append(b.role)
        items = [{"role": r, "text": r} for r in seen]
    fam = theme["font"]["family"]
    xx = x
    for i, it in enumerate(items):
        st = role_style(theme, it.get("role", "default"))
        em.base(f"__lg{i}", "rectangle", xx, y, 28, 18, stroke=st["stroke"], bg=st["bg"], fill=st["fill"],
                width=1, style=st["style"], round_=st.get("round", False))
        t = em.text(f"__lg{i}t", xx + 36, y + 1, [it["text"]], 13, fam, align="left", valign="top")
        xx += 36 + t["width"] + 28


def bbox(els):
    xs, ys, xe, ye = [], [], [], []
    for el in els:
        if el["type"] in ("arrow", "line"):
            for px, py in el["points"]:
                xs.append(el["x"] + px)
                ys.append(el["y"] + py)
                xe.append(el["x"] + px)
                ye.append(el["y"] + py)
        else:
            xs.append(el["x"])
            ys.append(el["y"])
            xe.append(el["x"] + el["width"])
            ye.append(el["y"] + el["height"])
    if not xs:
        return 0, 0, 0, 0
    return min(xs), min(ys), max(xe), max(ye)


# ----------------------------------------------------------------------------- lint
def lint(diag, leaves, notes, edges, labels, theme, spec, require_evidence):
    for i, a in enumerate(leaves):
        for b in leaves[i + 1:]:
            if inter(a.rect, b.rect, 1):
                diag.warn(f"overlap: nodes '{a.id}' and '{b.id}'")
    for nb in notes:
        r = (nb.x, nb.y, nb.x + nb.w, nb.y + nb.h)
        for b in leaves:
            if inter(r, b.rect, 1):
                diag.warn(f"overlap: note '{nb.id}' covers node '{b.id}'")
    for nb in notes:
        r = (nb.x, nb.y, nb.x + nb.w, nb.y + nb.h)
        for ed in edges:
            if nb in (ed["a"], ed["z"]):
                continue
            if any(seg_hits_rect(p, q, r, shrink=0) for pts in ed["paths"] for p, q in zip(pts, pts[1:])):
                diag.warn(f"note '{nb.id}' is crossed by edge {ed['a'].id}->{ed['z'].id} — move the note (pos/dx/dy)")
                break
    for ed in edges:
        skip = {ed["a"], ed["z"]}
        for pts in ed["paths"]:
            for p, q in zip(pts, pts[1:]):
                if abs(p[0] - q[0]) > 0.5 and abs(p[1] - q[1]) > 0.5 and ed["spec"].get("route") != "straight":
                    diag.warn(f"edge {ed['a'].id}->{ed['z'].id}: diagonal segment")
                for b in leaves:
                    if b in skip:
                        continue
                    if seg_hits_rect(p, q, b.rect):
                        diag.warn(f"edge {ed['a'].id}->{ed['z'].id} passes through node '{b.id}' — "
                                  f"set from_side/to_side, via, or move nodes")
                        break
    segs = []
    for ed in edges:
        for pts in ed["paths"]:
            for p, q in zip(pts, pts[1:]):
                segs.append((ed, p, q))
    seen = set()
    for i, (e1, p, q) in enumerate(segs):
        for e2, r, s in segs[i + 1:]:
            if e1 is e2:
                continue
            if abs(p[0] - q[0]) < 0.5 and abs(r[0] - s[0]) < 0.5 and abs(p[0] - r[0]) < 3:
                lo1, hi1 = sorted((p[1], q[1]))
                lo2, hi2 = sorted((r[1], s[1]))
                if min(hi1, hi2) - max(lo1, lo2) > 4:
                    key = (e1["id"], e2["id"])
                    if key not in seen:
                        seen.add(key)
                        diag.warn(f"edges {e1['a'].id}->{e1['z'].id} and {e2['a'].id}->{e2['z'].id} share a vertical run")
            if abs(p[1] - q[1]) < 0.5 and abs(r[1] - s[1]) < 0.5 and abs(p[1] - r[1]) < 3:
                lo1, hi1 = sorted((p[0], q[0]))
                lo2, hi2 = sorted((r[0], s[0]))
                if min(hi1, hi2) - max(lo1, lo2) > 4:
                    key = (e1["id"], e2["id"])
                    if key not in seen:
                        seen.add(key)
                        diag.warn(f"edges {e1['a'].id}->{e1['z'].id} and {e2['a'].id}->{e2['z'].id} share a horizontal run")
    focus = [b.id for b in leaves if b.role == "focus"]
    if len(focus) > 2:
        diag.warn(f"{len(focus)} focus nodes ({', '.join(focus)}) — keep focus to 1–2")
    budget = spec.get("budget", 30)
    if len(leaves) > budget:
        diag.warn(f"{len(leaves)} nodes > budget {budget}: split into an overview plus detail diagrams")
    for ed in edges:
        for k in ("label", "back"):
            t = ed["spec"].get(k)
            if t and ed["spec"].get("label_style", "pill") in ("pill", "chip") and len(str(t)) > 18:
                diag.warn(f"pill '{t}' is long (>18 chars); use label_style 'text' or shorten")
    if require_evidence:
        for b in leaves:
            if b.role not in ("brand",) and not b.spec.get("ev") and not b.spec.get("assumed"):
                diag.warn(f"evidence: node '{b.id}' has no 'ev' (path::symbol) and is not marked 'assumed'")
        for ed in edges:
            if not ed["spec"].get("ev") and not ed["spec"].get("assumed"):
                diag.warn(f"evidence: edge {ed['a'].id}->{ed['z'].id} has no 'ev' and is not marked 'assumed'")


# ----------------------------------------------------------------------------- sequence
def build_sequence(spec, theme, diag):
    em = Emitter(theme, sketch=spec.get("style") == "sketch")
    fam = theme["font"]["family"]
    actors = spec.get("actors", [])
    msgs = spec.get("messages", [])
    idx = {a["id"]: i for i, a in enumerate(actors)}
    boxes = []
    S = theme["spacing"]
    for a in actors:
        b = Box(a, "node")
        b.role = a.get("role", "component")
        measure_node(b, theme, diag)
        boxes.append(b)
    # column spacing from message label widths
    min_gap = [0] * max(0, len(actors) - 1)
    for m in msgs:
        if "from" in m and "to" in m and m["from"] in idx and m["to"] in idx:
            i, j = sorted((idx[m["from"]], idx[m["to"]]))
            if i == j:
                continue
            need = text_w(str(m.get("label", "")), 13, fam, theme) + 40
            per = need / (j - i)
            for k in range(i, j):
                min_gap[k] = max(min_gap[k], per)
    x = 0
    centers = []
    for k, b in enumerate(boxes):
        if k:
            prev = boxes[k - 1]
            x = max(x + prev.w + 40, centers[-1] + max(min_gap[k - 1], 160) - b.w / 2)
        b.x, b.y = x, 0
        centers.append(b.x + b.w / 2)
    top = max(b.h for b in boxes) + 40
    step = spec.get("step", 52)
    y = top
    rows = []
    for m in msgs:
        rows.append((m, y))
        if "note" in m:
            y += 30 + 18 * (str(m["note"]).count("\n") + 1)
        elif "divider" in m:
            y += 44
        elif m.get("from") == m.get("to"):
            y += step + 20
        else:
            y += step
    bottom = y + 20
    for b in boxes:
        emit_node(em, b, theme)
    for k, b in enumerate(boxes):
        cx = centers[k]
        ln = em.base(f"__life{k}", "line", cx, b.y + b.h, 0, bottom - b.h, stroke="#868e96", width=1, style="dashed")
        ln.update({"points": [[0, 0], [0, bottom - b.h]], "lastCommittedPoint": None, "startBinding": None,
                   "endBinding": None, "startArrowhead": None, "endArrowhead": None})
    minx, maxx = boxes[0].x, boxes[-1].x + boxes[-1].w
    for n, (m, yy) in enumerate(rows):
        if "divider" in m:
            ln = em.base(f"__div{n}", "line", minx, yy + 10, maxx - minx, 0, stroke="#adb5bd", style="dotted")
            ln.update({"points": [[0, 0], [maxx - minx, 0]], "lastCommittedPoint": None, "startBinding": None,
                       "endBinding": None, "startArrowhead": None, "endArrowhead": None})
            t = str(m["divider"])
            tw = text_w(t, 13, fam, theme)
            em.base(f"__divbg{n}", "rectangle", (minx + maxx) / 2 - tw / 2 - 8, yy, tw + 16, 20, stroke="#adb5bd",
                    bg="#f8f9fa")
            em.text(f"__divt{n}", (minx + maxx) / 2 - tw / 2, yy + 2, [t], 13, fam, color="#495057")
            continue
        if "note" in m:
            over = [idx[o] for o in m.get("over", []) if o in idx] or [0]
            x1 = centers[min(over)] - 60
            x2 = centers[max(over)] + 60
            lines = str(m["note"]).split("\n")
            tw, th = block_size(lines, 13, fam, theme)
            x2 = max(x2, x1 + tw + 20)
            em.base(f"__note{n}", "rectangle", x1, yy, x2 - x1, th + 12, stroke="#1e1e1e", bg="#fff3bf")
            em.text(f"__note{n}t", x1 + 10, yy + 6, lines, 13, fam, align="left", valign="top")
            continue
        if m.get("from") not in idx or m.get("to") not in idx:
            diag.err(f"message {n}: unknown actor in {m}")
            continue
        i, j = idx[m["from"]], idx[m["to"]]
        est = theme["edges"].get(m.get("type", "default"), theme["edges"]["default"])
        style = "dashed" if m.get("type") in ("return", "async") else est["style"]
        label = str(m.get("label", ""))
        if m.get("step"):
            label = f"{m['step']}. {label}"
        if i == j:
            cx = centers[i]
            pts = [(cx, yy), (cx + 40, yy), (cx + 40, yy + 22), (cx + 2, yy + 22)]
            em.arrow(f"__m{n}", pts, est["stroke"], est["width"], style)
            if label:
                em.text(f"__m{n}t", cx + 48, yy + 2, [label], 13, fam, align="left", valign="top")
            continue
        x1, x2 = centers[i], centers[j]
        em.arrow(f"__m{n}", [(x1, yy), (x2, yy)], est["stroke"], est["width"], style)
        if label:
            pill = m.get("label_style") == "pill"
            tw = text_w(label, 13, fam, theme)
            lx = (x1 + x2) / 2 - tw / 2
            if pill:
                L = theme["labels"]["pill"]
                em.base(f"__m{n}p", "rectangle", lx - L["pad_x"], yy - 26, tw + 2 * L["pad_x"], 22,
                        stroke=L["stroke"], bg=L["bg"], round_=True)
                em.text(f"__m{n}t", lx, yy - 23, [label], 13, fam, color=L["text"], container=f"__m{n}p")
            else:
                em.text(f"__m{n}t", lx, yy - 20, [label], 13, fam, valign="top")
    els = em.els
    minx, miny, maxx, maxy = bbox(els)
    if spec.get("title"):
        size = theme["font"]["size"]["title"]
        em.text("__title", minx, miny - size * 1.25 - 24, [spec["title"]], size, fam, align="left", valign="top")
    return em


# ----------------------------------------------------------------------------- scan
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "env", "dist", "build", "target", "__pycache__", "vendor",
             ".tox", ".mypy_cache", ".pytest_cache", ".idea", ".vscode", ".next", "out", "coverage", ".gradle",
             "site-packages", ".cache", ".planning"}
LANG = {".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
        ".go": "Go", ".java": "Java", ".kt": "Kotlin", ".scala": "Scala", ".rs": "Rust", ".c": "C", ".h": "C/C++",
        ".cc": "C++", ".cpp": "C++", ".hpp": "C++", ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".sql": "SQL",
        ".proto": "Protobuf", ".thrift": "Thrift", ".sh": "Shell", ".swift": "Swift"}
MANIFESTS = {"package.json", "pyproject.toml", "setup.py", "requirements.txt", "go.mod", "Cargo.toml", "pom.xml",
             "build.gradle", "build.gradle.kts", "build.sbt", "CMakeLists.txt", "Makefile", "Gemfile",
             "composer.json", "environment.yml", "uv.lock", "poetry.lock"}
HINTS = [
    ("HTTP server", r"FastAPI\(|Flask\(|express\(\)|http\.ListenAndServe|@RestController|@app\.(get|post|route)|uvicorn\.run|gin\.Default\(|aiohttp\.web|HttpServer"),
    ("HTTP client", r"requests\.(get|post|put|delete)|httpx\.|fetch\(|axios\.|http\.Get\(|HttpClient|urllib\.request|aiohttp\.ClientSession|reqwest::"),
    ("gRPC", r"grpc\.server|grpc\.NewServer|grpc\.insecure_channel|grpc\.Dial|_pb2_grpc|ServerBuilder"),
    ("Arrow Flight", r"FlightServerBase|flight\.FlightClient|FlightClient|FlightSqlClient|arrow_flight|FlightDescriptor|FlightService"),
    ("ADBC/ODBC/JDBC", r"adbc_driver|adbc\.|jdbc:|DriverManager\.getConnection|pyodbc|odbc"),
    ("SQL database", r"psycopg|asyncpg|sqlalchemy|create_engine|mysql\.connector|pymysql|sqlite3\.connect|database/sql|gorm\.|sqlx::|diesel::|JdbcTemplate"),
    ("Kafka / streams", r"KafkaProducer|KafkaConsumer|confluent_kafka|kafka\.Writer|sarama\.|kafka::|aiokafka"),
    ("Queue / broker", r"pika\.|celery|amqp|rabbitmq|nats\.|sqs|pubsub|redis\.Queue|rq\."),
    ("Cache / KV", r"redis\.Redis|redis\.StrictRedis|ioredis|go-redis|memcache|rocksdb"),
    ("Object storage", r"boto3\.(client|resource)\(['\"]s3|s3fs|minio|google\.cloud\.storage|azure\.storage|object_store::"),
    ("Engines", r"SparkSession|pyspark|datafusion|SessionContext|duckdb|polars|ray\.init|dask\.|flink|trino|starrocks|druid|clickhouse"),
    ("Native bridge (JNI/FFI)", r"System\.loadLibrary|JNIEnv|jni::|ctypes\.CDLL|cffi|pybind11|extern \"C\"|#\[no_mangle\]"),
    ("Subprocess / exec", r"subprocess\.(run|Popen|call)|os\.system\(|exec\.Command\(|ProcessBuilder"),
    ("WebSocket / SSE", r"websocket|WebSocket|EventSource|socket\.io|sse_starlette"),
    ("LLM / AI API", r"anthropic\.|openai\.|ChatCompletion|messages\.create|langchain|llama_index|transformers\.|vllm"),
    ("Threads / async pool", r"ThreadPoolExecutor|ProcessPoolExecutor|asyncio\.gather|tokio::spawn|go func\(|ExecutorService|rayon::"),
]
ENTRY = [
    (r"if __name__ == ['\"]__main__['\"]", "python __main__"),
    (r"^func main\(\)", "go main"),
    (r"public static void main\(", "java main"),
    (r"^fn main\(\)", "rust main"),
    (r"^\s*ENTRYPOINT|^\s*CMD", "docker cmd"),
    (r"argparse\.ArgumentParser|click\.command|typer\.Typer|cobra\.Command", "CLI"),
]
URL_RE = re.compile(r"\b(?:https?|grpc|jdbc:[a-z]+|postgres(?:ql)?|mysql|redis|kafka|s3|mongodb)://[^\s'\"<>)]{3,80}")
HOSTPORT_RE = re.compile(r"\b(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\d{1,3}(?:\.\d{1,3}){3}):\d{2,5}\b")
ENV_RE = re.compile(r"\b[A-Z][A-Z0-9_]*(?:HOST|PORT|URL|URI|DSN|ENDPOINT|ADDR|BROKERS?)\b")


def iter_files(root, excludes=()):
    import fnmatch
    import subprocess

    def excluded(rel):
        return any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.rstrip("/") + "/*") for pat in excludes)
    try:  # git knows what is source: tracked + untracked-but-not-ignored
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, timeout=60)
        if out.returncode == 0 and out.stdout:
            for rel in out.stdout.decode(errors="replace").split("\0"):
                if not rel or excluded(rel) or any(part in SKIP_DIRS or part.startswith(".") for part in rel.split("/")[:-1]):
                    continue
                p = Path(root) / rel
                if p.is_file():
                    yield p
            return
    except (OSError, subprocess.SubprocessError):
        pass
    for dp, dns, fns in os.walk(root):
        rel_dp = os.path.relpath(dp, root)
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith(".")
                  and not excluded(os.path.normpath(os.path.join(rel_dp, d)))]
        for fn in fns:
            if not excluded(os.path.normpath(os.path.join(rel_dp, fn))):
                yield Path(dp) / fn


def read_small(p, limit=400_000):
    try:
        if p.stat().st_size > limit:
            return None
        return p.read_text(errors="replace")
    except OSError:
        return None


def mini_compose(text):
    """tiny YAML subset reader for docker-compose services."""
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text) or {}
        out = {}
        for name, s in (data.get("services") or {}).items():
            s = s or {}
            dep = s.get("depends_on") or []
            out[name] = {"image": s.get("image"), "build": bool(s.get("build")), "ports": s.get("ports") or [],
                         "depends_on": list(dep.keys()) if isinstance(dep, dict) else list(dep)}
        return out
    except Exception:
        pass
    out, cur, key, in_services, svc_indent = {}, None, None, False, None
    for raw in text.splitlines():
        raw = re.sub(r"\s+#.*$", "", raw)
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        ind = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if ind == 0:
            in_services = line.startswith("services:")
            cur = None
            continue
        if not in_services:
            continue
        if svc_indent is None:
            svc_indent = ind
        if ind == svc_indent and line.endswith(":"):
            cur = line[:-1].strip("'\"")
            out[cur] = {"image": None, "build": False, "ports": [], "depends_on": []}
            key = None
            continue
        if cur is None:
            continue
        m = re.match(r"([A-Za-z_]+):\s*(.*)", line)
        if m and ind == svc_indent + 2 or (m and key is None):
            k, v = m.group(1), m.group(2)
            key = k
            if k == "image":
                out[cur]["image"] = v.strip("'\"")
            elif k == "build":
                out[cur]["build"] = True
            elif k in ("ports", "depends_on") and v.startswith("["):
                out[cur][k] = [x.strip(" '\"") for x in v.strip("[]").split(",") if x.strip()]
        elif line.startswith("- ") and key in ("ports", "depends_on"):
            out[cur][key].append(line[2:].strip(" '\""))
        elif key == "depends_on" and line.endswith(":"):
            out[cur]["depends_on"].append(line[:-1])
    return out


def module_of(rel, depth):
    parts = rel.parts[:-1]
    if not parts:
        return "(root)"
    return "/".join(parts[:depth])


def scan(root, depth=2, excludes=()):
    root = Path(root).resolve()
    langs, manifests, composes, dockerfiles, k8s, entries = {}, [], {}, [], [], []
    hints = {h: [] for h, _ in HINTS}
    urls, envs = {}, {}
    files = []
    py_mods = {}
    go_module = None
    java_pkgs = {}
    for p in iter_files(root, excludes):
        rel = p.relative_to(root)
        files.append(rel)
        ext = p.suffix.lower()
        if ext in LANG:
            langs[LANG[ext]] = langs.get(LANG[ext], 0) + 1
        if p.name in MANIFESTS:
            manifests.append(str(rel))
        if p.name.startswith("docker-compose") or p.name in ("compose.yml", "compose.yaml"):
            t = read_small(p)
            if t:
                composes[str(rel)] = mini_compose(t)
        if p.name == "Dockerfile" or p.name.startswith("Dockerfile."):
            t = read_small(p) or ""
            info = {"file": str(rel), "from": re.findall(r"^\s*FROM\s+(\S+)", t, re.M),
                    "expose": re.findall(r"^\s*EXPOSE\s+(.+)$", t, re.M),
                    "cmd": [l.strip() for l in re.findall(r"^\s*(?:CMD|ENTRYPOINT)\s+(.+)$", t, re.M)]}
            dockerfiles.append(info)
        if ext in (".yml", ".yaml"):
            t = read_small(p) or ""
            for kind, name in re.findall(r"^kind:\s*(\w+)[\s\S]*?^\s+name:\s*(\S+)", t, re.M)[:20]:
                k8s.append(f"{kind}/{name} ({rel})")
        if p.name == "go.mod":
            t = read_small(p) or ""
            m = re.search(r"^module\s+(\S+)", t, re.M)
            if m and (go_module is None or len(rel.parts) == 1):
                go_module = (m.group(1), rel.parent)
        if ext in (".sql", ".csv", ".tsv"):  # data-ish: count only
            continue
        if ext not in LANG and p.name not in ("Dockerfile",) and ext not in (".yml", ".yaml", ".toml", ".env", ".json", ".ini", ".cfg", ".conf", ".properties"):
            continue
        t = read_small(p)
        if t is None:
            continue
        for pat, label in ENTRY:
            m = re.search(pat, t, re.M)
            if m:
                ln = t[:m.start()].count("\n") + 1
                entries.append(f"{rel}:{ln} ({label})")
        if ext in LANG:
            for h, pat in HINTS:
                for m in re.finditer(pat, t):
                    ln = t[:m.start()].count("\n") + 1
                    if len(hints[h]) < 400:
                        hints[h].append((str(rel), ln, m.group(0)))
        for m in URL_RE.finditer(t):
            urls.setdefault(m.group(0), str(rel))
        for m in HOSTPORT_RE.finditer(t):
            urls.setdefault(m.group(0), str(rel))
        for m in ENV_RE.finditer(t):
            envs.setdefault(m.group(0), str(rel))
        if ext == ".py":
            py_mods[".".join(rel.with_suffix("").parts)] = rel
        if ext in (".java", ".kt", ".scala"):
            m = re.search(r"^\s*package\s+([\w.]+)", t, re.M)
            if m:
                java_pkgs.setdefault(m.group(1), set()).add(module_of(rel, depth))
    # import graph
    edges = {}
    sizes = {}
    pkg_roots = {}
    for mod, rel in py_mods.items():  # map importable names -> module dir
        parts = mod.split(".")
        for i in range(len(parts)):
            pkg_roots.setdefault(".".join(parts[i:]), rel)
    for rel in files:
        ext = rel.suffix.lower()
        if ext not in (".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".kt", ".scala"):
            continue
        src = module_of(rel, depth)
        sizes[src] = sizes.get(src, 0) + 1
        t = read_small(root / rel)
        if not t:
            continue
        targets = set()
        if ext == ".py":
            try:
                tree = ast.parse(t)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    if node.level:
                        base = list(rel.parent.parts)
                        if node.level > 1:
                            base = base[:-(node.level - 1)] if node.level - 1 <= len(base) else []
                        target = Path(*base, *(node.module.split(".") if node.module else []))
                        targets.add(module_of(target / "x.py", depth))
                        continue
                    names = [node.module] if node.module else []
                for nm in names:
                    parts = nm.split(".")
                    for i in range(len(parts), 0, -1):
                        hit = pkg_roots.get(".".join(parts[:i]))
                        if hit is None:
                            cand = ".".join(parts[:i])
                            hit = next((r for m2, r in py_mods.items() if m2.endswith(cand + ".__init__")), None)
                        if hit is not None:
                            targets.add(module_of(hit, depth))
                            break
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            for m in re.finditer(r"(?:import[^'\"]*from\s*|require\(\s*|import\(\s*)['\"](\.{1,2}/[^'\"]+)['\"]", t):
                target = (rel.parent / m.group(1))
                try:
                    norm = Path(os.path.normpath(str(target)))
                except ValueError:
                    continue
                targets.add(module_of(norm / "x", depth) if not norm.suffix else module_of(norm, depth))
        elif ext == ".go" and go_module:
            modpath, modroot = go_module
            for m in re.finditer(r"\"(" + re.escape(modpath) + r"/[^\"]+)\"", t):
                sub = m.group(1)[len(modpath) + 1:]
                targets.add(module_of(modroot / sub / "x.go", depth))
        elif ext in (".java", ".kt", ".scala"):
            for m in re.finditer(r"^\s*import\s+(?:static\s+)?([\w.]+)", t, re.M):
                name = m.group(1)
                while "." in name:
                    name = name.rsplit(".", 1)[0]
                    if name in java_pkgs:
                        targets.update(java_pkgs[name])
                        break
        for tg in targets:
            if tg != src:
                edges[(src, tg)] = edges.get((src, tg), 0) + 1
    return {"root": str(root), "files": len(files), "languages": dict(sorted(langs.items(), key=lambda kv: -kv[1])),
            "manifests": sorted(manifests), "compose": composes, "dockerfiles": dockerfiles, "k8s": k8s[:60],
            "entrypoints": entries[:80], "hints": {h: v for h, v in hints.items() if v},
            "endpoints": dict(list(urls.items())[:80]), "env": dict(list(envs.items())[:80]),
            "modules": dict(sorted(sizes.items(), key=lambda kv: -kv[1])),
            "imports": [{"from": a, "to": b, "count": c} for (a, b), c in sorted(edges.items(), key=lambda kv: -kv[1])]}


def scan_markdown(r):
    out = [f"# Scan: {r['root']}", "", f"{r['files']} files. Languages: " +
           ", ".join(f"{k} {v}" for k, v in r["languages"].items()), ""]
    out += ["## Manifests", *([f"- {m}" for m in r["manifests"]] or ["- none"]), ""]
    if r["compose"]:
        out.append("## docker-compose services")
        for f, svcs in r["compose"].items():
            out.append(f"- `{f}`")
            for n, s in svcs.items():
                out.append(f"  - **{n}** image={s['image'] or ('build' if s['build'] else '?')} ports={s['ports']} depends_on={s['depends_on']}")
        out.append("")
    if r["dockerfiles"]:
        out.append("## Dockerfiles")
        for d in r["dockerfiles"]:
            out.append(f"- `{d['file']}` FROM {', '.join(d['from'])}; EXPOSE {', '.join(d['expose']) or '-'}; {'; '.join(d['cmd'])}")
        out.append("")
    if r["k8s"]:
        out += ["## Kubernetes objects", *[f"- {k}" for k in r["k8s"]], ""]
    out += ["## Entry points", *([f"- {e}" for e in r["entrypoints"]] or ["- none found"]), ""]
    out.append("## Integration hints (regex — confirm by reading the code)")
    for h, occ in r["hints"].items():
        files = {}
        for f, ln, s in occ:
            files.setdefault(f, []).append(ln)
        refs = ", ".join(f"{f}:{lns[0]}" for f, lns in list(files.items())[:6])
        out.append(f"- **{h}** — {len(occ)} hits in {len(files)} files: {refs}")
    out.append("")
    if r["endpoints"]:
        out += ["## Endpoint literals", *[f"- `{u}` ({f})" for u, f in r["endpoints"].items()], ""]
    if r["env"]:
        out += ["## Config / env names", ", ".join(f"`{k}`" for k in r["env"]), ""]
    out.append("## Modules (files) and internal imports")
    out += [f"- {m} ({n})" for m, n in list(r["modules"].items())[:40]]
    out.append("")
    out += [f"- {e['from']} → {e['to']} ({e['count']})" for e in r["imports"][:80]] or ["- no internal imports resolved"]
    return "\n".join(out)


def deps_spec(r, max_nodes=18):
    mods = list(r["modules"].keys())[:max_nodes]
    keep = set(mods)
    edges = [e for e in r["imports"] if e["from"] in keep and e["to"] in keep]
    linked = {e["from"] for e in edges} | {e["to"] for e in edges}
    isolated = [m for m in mods if m not in linked]
    mods = [m for m in mods if m in linked] or mods
    count = {(e["from"], e["to"]): e["count"] for e in edges}
    nid = lambda m: re.sub(r"[^\w]", "_", m) or "root"
    out_edges = []
    for e in edges:
        rev = count.get((e["to"], e["from"]))
        weaker = rev is not None and (e["count"], e["from"]) < (rev, e["to"])
        ed = {"from": nid(e["from"]), "to": nid(e["to"]), "ev": f"{e['count']} imports"}
        if weaker:  # break the cycle on the weaker direction, and show it
            ed.update({"rank_ignore": True, "type": "async", "label": f"cycle ({e['count']})", "label_style": "text"})
        out_edges.append(ed)
    sub = "draft from import scan: rename, merge and cut before publishing"
    if isolated:
        sub += "; no internal imports: " + ", ".join(isolated[:8]) + (" …" if len(isolated) > 8 else "")
    return {
        "title": f"Module dependencies — {Path(r['root']).name}",
        "subtitle": sub,
        "direction": "LR",
        "root": {"id": "mods", "layout": "ranks", "role": "none", "gap": 48, "rank_gap": 160,
                 "children": [{"id": nid(m), "label": m, "sub": f"{r['modules'][m]} files",
                               "role": "component", "ev": m} for m in mods]},
        "edges": out_edges,
    }


# ----------------------------------------------------------------------------- CLI
def write_excalidraw(em, out, spec, theme):
    doc = {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": em.els,
           "appState": {"viewBackgroundColor": theme["canvas"]["background"], "gridSize": None}, "files": {}}
    Path(out).write_text(json.dumps(doc, indent=1))


def write_evidence(spec, out):
    rows = []
    def walk(n):
        if "children" in n:
            if n.get("ev"):
                rows.append(("group", n.get("id"), n.get("title", ""), n["ev"]))
            for c in n["children"]:
                walk(c)
        elif n.get("id"):
            rows.append(("node", n["id"], n.get("label", n["id"]).replace("\n", " "), n.get("ev") or ("assumed" if n.get("assumed") else "")))
    if spec.get("root"):
        walk(spec["root"])
    for c in spec.get("children", []):
        walk(c)
    for e in spec.get("edges", []):
        lab = " / ".join(x for x in (e.get("label"), e.get("back")) if x)
        rows.append(("edge", f"{e['from']} → {e['to']}", lab, e.get("ev") or ("assumed" if e.get("assumed") else "")))
    if not any(r[3] for r in rows):
        return None
    lines = [f"# Evidence — {spec.get('title', Path(out).stem)}", "", "| kind | id | label | evidence |", "|---|---|---|---|"]
    for k, i, l, ev in rows:
        ev = ", ".join(ev) if isinstance(ev, list) else ev
        lines.append(f"| {k} | `{i}` | {l} | {ev or '**missing**'} |")
    Path(out).write_text("\n".join(lines) + "\n")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("spec")
    b.add_argument("-o", "--out")
    b.add_argument("--theme")
    b.add_argument("--strict", action="store_true")
    b.add_argument("--require-evidence", action="store_true")
    l = sub.add_parser("lint")
    l.add_argument("spec")
    l.add_argument("--theme")
    l.add_argument("--require-evidence", action="store_true")
    s = sub.add_parser("scan")
    s.add_argument("repo")
    s.add_argument("--depth", type=int, default=2)
    s.add_argument("--json", action="store_true")
    s.add_argument("--spec-out")
    s.add_argument("--exclude", action="append", default=[], help="glob relative to repo, repeatable (e.g. 'deploy/stage/*')")
    sub.add_parser("templates")
    n = sub.add_parser("new")
    n.add_argument("template")
    n.add_argument("out")
    a = ap.parse_args(argv)

    if a.cmd == "templates":
        for p in sorted(TEMPLATE_DIR.glob("*.spec.json")):
            try:
                d = json.loads(p.read_text())
                print(f"{p.name[:-10]:<26} {d.get('_template', {}).get('use', '')}")
            except json.JSONDecodeError as ex:
                print(f"{p.name}: invalid JSON ({ex})")
        return 0
    if a.cmd == "new":
        src = TEMPLATE_DIR / f"{a.template}.spec.json"
        if not src.exists():
            print(f"no template '{a.template}'. Run: sysdiag.py templates", file=sys.stderr)
            return 2
        if Path(a.out).exists():
            print(f"{a.out} exists; not overwriting", file=sys.stderr)
            return 2
        shutil.copy(src, a.out)
        print(a.out)
        return 0
    if a.cmd == "scan":
        r = scan(a.repo, a.depth, a.exclude)
        print(json.dumps(r, indent=1) if a.json else scan_markdown(r))
        if a.spec_out:
            Path(a.spec_out).write_text(json.dumps(deps_spec(r), indent=1))
            print(f"\nwrote draft module-dependency spec: {a.spec_out}", file=sys.stderr)
        return 0

    spec = json.loads(Path(a.spec).read_text())
    theme = load_theme(a.theme, spec.get("theme"))
    diag = Diag()
    em = build(spec, theme, diag, require_evidence=a.require_evidence)
    for e in diag.errors:
        print(f"ERROR {e}", file=sys.stderr)
    if diag.errors or em is None:
        return 1
    if a.cmd == "build":
        out = a.out or re.sub(r"(\.spec)?\.json$", "", a.spec) + ".excalidraw"
        write_excalidraw(em, out, spec, theme)
        ev = write_evidence(spec, re.sub(r"\.excalidraw$", "", out) + ".evidence.md")
        x1, y1, x2, y2 = bbox(em.els)
        print(f"wrote {out}  ({len(em.els)} elements, {int(x2 - x1)}x{int(y2 - y1)} px)" + (f"; {ev}" if ev else ""))
    for w in diag.warnings:
        print(f"WARN  {w}")
    if not diag.warnings:
        print("lint: clean")
    return 1 if (getattr(a, "strict", False) and diag.warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
