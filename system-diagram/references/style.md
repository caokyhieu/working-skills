# Style

All values live in `assets/theme.json`; this page says what they **mean**. Choose a role
by what the thing is. The colour follows. Never pick a role for its colour.

## The look (design.JPG)

- White canvas, thin dark strokes, `roughness: 0` (clean lines, not hand-drawn), sans
  font (Excalidraw family 2, Helvetica). `"style": "sketch"` switches to hand-drawn.
- **Hosts** are light-grey boxes with the host name and address centred at the top.
- **Server processes** inside a host are **hatched blue** boxes (Excalidraw `hachure`
  fill) titled with the server kind ("Apache Flight SQL Server").
- **Components** inside a server are rounded pastel boxes: yellow for control concerns
  (Authentication, Concurrent Task Pool), teal for execution (Segment Reader, JNI Bridge,
  DataFusion), green for catalogs, white for plain parts and data.
- **Clients/adapters** are flat grey boxes (Flight SQL Client, Druid HTTP Client).
- **Wires** are thin black orthogonal arrows. Request/response is a parallel pair.
  What travels is a **purple pill** with white text (SQL, Arrow Stream, ADBC, HTTP,
  JSON Stream, UNION). Plain action words ("Discover table paths") are free text.
- **Annotations** are free text near what they explain (Partition 1, config strings,
  "Simplified", design remarks). No boxes around notes.
- Well-known products appear as a wordmark (`brand`), not a box.

## Roles

| Role | Looks | Use for |
|---|---|---|
| `zone` | light grey box | host, node, VM, pod, cluster, machine |
| `network` | dashed outline | VPC, region, environment, trust boundary |
| `agent` | grey box | orchestrator process with inner columns |
| `service` | hatched blue | server process / process boundary hosting components |
| `lane` | very light grey | inner column, stage, tier band, swimlane |
| `client` | flat grey | client, adapter, connector, SDK, driver |
| `component` | white rounded | plain module |
| `compute` | teal | engine, reader, worker, bridge, executor |
| `control` | yellow | auth, scheduler, pool, policy, config, gateway |
| `catalog` | green | catalog, metadata, registry, index, cache |
| `store` | white cylinder | database, object store |
| `data` | white rounded | files / data shown as a box |
| `queue` | orange | queue, topic, stream, bus |
| `external` | white, grey stroke | someone else's system |
| `actor` | blue ellipse | person or calling application |
| `brand` | big wordmark, no box | well-known product (StarRocks, Kafka) |
| `decision` | yellow diamond | branch |
| `state` | light blue | state in a state machine |
| `terminal` | black dot/ellipse | start/end |
| `entity` | white square box | ER entity with `fields` |
| `code` | dark box, mono green text | evidence artifact: real snippet / payload |
| `planned` | dashed grey | not built yet / assumption |
| `added` / `removed` | green / red dashed | architecture delta |
| `focus` | red | the 1–2 things the reader must notice |
| `none` | invisible | layout-only group |

Edge types: `default`/`data` (black), `control` (grey dashed), `async` (black dashed),
`hot` (red, thick), `link` (blue). Label styles: `pill` (purple protocol), `chip` (soft
lilac), `step` (black number), `text` (plain words).

## Re-skin

- Whole team: edit `assets/theme.json` (keep role names; change `bg`/`stroke`/`fill`).
  Use Excalidraw palette hexes so swatches match inside excalidraw.com.
- One diagram: a spec-level `"theme": {...}` is deep-merged over the file, e.g.
  `{"font": {"family": 5}}` (Excalifont) or `{"roles": {"service": {"bg": "#d0bfff"}}}`.
- Another theme file: `sysdiag build spec.json --theme my-theme.json`.

Fonts: 1 Virgil, 2 Helvetica (default), 3 Cascadia (mono, used for `sub` lines and fields),
5 Excalifont, 6 Nunito. Text widths are estimated per family (`font.char_width`); if
labels overflow in the render, raise that factor for the family you use.
