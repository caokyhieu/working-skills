# Spec format

A spec is one JSON file. `sysdiag.py build` turns it into an `.excalidraw` file: it
measures text, lays out boxes, routes orthogonal arrows, fans ports, places protocol
pills, binds arrows to shapes and lints the result. You describe **what** is in the
system and **how it nests**; you set coordinates only when you need to.

## Top level

| Key | Type | Meaning |
|---|---|---|
| `title`, `subtitle` | string | Drawn top-left above the diagram |
| `direction` | `LR` \| `TB` | Default reading direction; also the default for `ranks` groups |
| `root` | group | The outermost group (usually `layout: row` for LR) |
| `edges` | list | Connections (below) |
| `notes` | list | Free-floating annotations (below) |
| `legend` | `true` \| list | `true` = one swatch per role used; or `[{"role": "compute", "text": "execution engine"}]` |
| `style` | `"sketch"` | Hand-drawn strokes (roughness 1); default is clean |
| `theme` | object | Partial override of `assets/theme.json`, e.g. `{"font": {"family": 5}}` for Excalifont |
| `budget` | int | Max leaf nodes before lint says "split" (default 30) |
| `kind` | `"sequence"` | Switch to the sequence layout (see end) |

## Groups (containers)

Anything with `children` is a group: a host, a process, a server, a lane, a layer.

```json
{"id": "hn1", "title": "Druid # Historical Node 1 - 0.0.0.0", "role": "zone",
 "layout": "column", "gap": 22, "pad": 24, "align": "center", "children": [ ... ]}
```

| Key | Default | Meaning |
|---|---|---|
| `id` | required | Unique across the whole spec |
| `title` | — | Label at the top of the box; `\n` for two lines |
| `title_pos` | `top` | `top` (centred) or `top-left` |
| `role` | `zone` | Visual role (see `style.md`). `none` = invisible layout-only group |
| `layout` | `column` | `row`, `column`, `grid` (+`cols`), `ranks` (auto layers from edges), `free` (children use `at`) |
| `gap`, `pad` | 32, 24 | Space between children / inside the border |
| `align` | `center` | Cross-axis: `start`, `center`, `end`, `stretch` (children fill the cross axis — tall lanes) |
| `justify` | `start` | Main-axis: `start`, `center`, `end`, `space-between`, `space-around`, `space-evenly` |
| `w`, `h` | — | Minimum size (useful to make sibling zones equal) |
| `dir`, `rank_gap` | spec `direction`, 120 | For `ranks`: layer direction and distance between layers |
| `ev` | — | Evidence (see below) |

A child may set `align_self` (`start`/`center`/`end`) or, inside `ranks`, a fixed `rank`.
`{"spacer": 40}` inserts empty space in a row/column. A group with `"children": []` is a
plain box you can connect to (e.g. a union lane).

## Nodes (leaves)

```json
{"id": "df1", "label": "Datafusion 36", "sub": "SessionContext", "role": "compute",
 "ev": "engine/src/exec.rs::build_context"}
```

| Key | Meaning |
|---|---|
| `id`, `label` | `label` defaults to the id; wraps at ~200px or at `w` |
| `sub` | Second line in mono, smaller: a class, port, version, file |
| `role` | Visual role (`style.md`). Picks fill, stroke, hatch, shape |
| `shape` | Override: `rect`, `ellipse`, `diamond`, `db` (cylinder) |
| `fields` | List of strings → ER/table box with a header and field rows |
| `w`, `h` | Fixed size (lint warns if text will not fit) |
| `bg`, `stroke`, `fill`, `style`, `width`, `round`, `size`, `font` | One-off style overrides — prefer a role |
| `ev` | Evidence: `"path/file.py::Symbol"` or a list. Stored in the element's `customData` and written to `<name>.evidence.md` |
| `assumed` | `true` when not verified in code (idea mode, or inferred) — pair with role `planned` if it does not exist yet |

## Edges

```json
{"from": "c1", "to": "fss1", "label": "SQL", "back": "Arrow Stream", "ev": "client/flight.py::FlightReader.read"}
```

| Key | Meaning |
|---|---|
| `from`, `to` | Ids of nodes, groups **or notes** |
| `label` | Text on the wire. Default style `pill` (purple protocol badge) |
| `back` | Makes a **request/response pair**: two parallel arrows, forward labelled `label`, return labelled `back` (SQL / Arrow Stream) |
| `label_style` | `pill` (protocol), `chip` (soft protocol), `step` (numbered step), `text` (plain words beside the line) |
| `label_side` | `auto`, `left` (left of travel), `above`, `below`, `right`, `on` |
| `label_at` | 0..1 position along the longest segment |
| `type` | Edge style from theme: `default`, `data`, `control` (grey dashed), `async` (dashed), `hot` (red, thick), `link` (blue) |
| `back_type` | Style of the return arrow (default `return`) |
| `head`, `tail` | `arrow` (default head), `triangle`, `dot`, `bar`, `none` |
| `both` | Arrowheads on both ends |
| `from_side`, `to_side` | Force `left`/`right`/`top`/`bottom` (auto picks by geometry) |
| `from_port`, `to_port` | 0..1 position along that side (all three `union` lines use 0.5 → fan from one point) |
| `route` | `auto` (orthogonal, avoids boxes), `straight` (diagonal allowed — only for fan lines) |
| `via` | `[[x, y], ...]` waypoints in absolute canvas coordinates |
| `rank_ignore` | Do not let this edge influence `ranks` layering (feedback loops) |
| `stroke`, `width`, `style` | One-off overrides |
| `ev`, `assumed` | As for nodes |

## Notes

Free text — annotations, partition names, config snippets. Notes can be edge endpoints.

```json
{"id": "flighttable", "text": "FlightTable(nodes=\"0.0.0.0:8000;0.0.0.1:8000\")",
 "near": "agent", "pos": "above", "gap": 40, "w": 420}
```

`pos`: `above`, `below`, `left`, `right`, `above-left`, `above-right`, `below-left`,
`below-right`, `inside-top`. Fine-tune with `dx`, `dy`. Or give `at: [x, y]` absolute.
`w` is the wrap width; `size`, `color`, `font` (`mono` for code) are optional.

## Sequence diagrams (`"kind": "sequence"`)

```json
{"kind": "sequence", "title": "Partitioned read",
 "actors": [{"id": "sr", "label": "StarRocks", "role": "client"}, {"id": "agent", "label": "Query Agent", "role": "service"}],
 "messages": [
   {"from": "sr", "to": "agent", "label": "ADBC execute(sql)", "step": 1},
   {"note": "plan splits into 3 partitions", "over": ["agent"]},
   {"divider": "per partition"},
   {"from": "agent", "to": "sr", "label": "Arrow batches", "type": "return"}]}
```

Message keys: `from`, `to` (same id = self-call), `label`, `step`, `type`
(`return`/`async` = dashed), `label_style: "pill"`. Rows: `note` + `over`, `divider`.

## Coordinates and units

Canvas pixels, origin top-left, y down. Sizes snap to a 4px grid. When a layout needs a
hand nudge, prefer (in order): `gap`/`pad`/`justify` → `w`/`h` → `from_side`/`to_side`
→ `from_port`/`to_port` → `via` → a `free` group with `at`.

## Output files

`build spec.json -o docs/diagrams/name.excalidraw` writes:

- `name.excalidraw` — open in excalidraw.com, the VS Code Excalidraw extension, or Obsidian; everything stays editable (arrows are bound to boxes, text is bound to shapes)
- `name.evidence.md` — when any `ev`/`assumed` exists: one row per node/edge with its evidence, `**missing**` where there is none

`render.py name.excalidraw --svg` then writes `name.png` (and `name.svg`).
