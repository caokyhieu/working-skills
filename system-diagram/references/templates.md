# Templates

Pick by the **question** the reader has, not by what the system is. Every template is a
working spec in `templates/`; start from it with `sysdiag new <name> <out>.spec.json`. Each has a rendered preview in
`templates/previews/<name>.png` — open it before choosing.
If two fit, pick the one whose main axis matches the question (containment = "where does
it run", flow = "in what order", ranks = "what depends on what").

| Question the reader has | Template | Layout grammar |
|---|---|---|
| What runs where, and what talks to what over which protocol? | `containment-architecture` | caller → orchestrator → hosts; host ⊃ server ⊃ components; request/response pairs with pills |
| Which tier may call which? | `layered-architecture` | TB bands (lanes), nodes in rows, edges only downward |
| What happens, step by step, when X is requested? | `request-flow` | one numbered path (`step` labels) through nested services |
| In what order do messages go between processes? | `sequence` | actors across the top, lifelines, messages downward |
| How does data move and change form? | `data-pipeline` | LR stage lanes (sources → ingest → process → store → serve), format on each wire |
| Where is it deployed: network, hosts, replicas, ports? | `deployment` | network (dashed) ⊃ subnet/cluster ⊃ pod/process ⊃ container |
| How is the code organised; what imports what? | `module-dependency` | `ranks` layout from the import graph; callers left |
| Who produces and who consumes which events? | `event-driven` | producers → broker ⊃ topics → consumers (fan-in, fan-out) |
| What is the system and what is around it? | `c4-context` | one focus box, people left, external systems right |
| What changes between now and the proposal? | `architecture-delta` | two equal panels Before / After; `removed` / `added` roles; change list note |
| What states can it be in and what moves it? | `state-machine` | `ranks` of states; `event [guard]` text labels; loops with `rank_ignore` |
| What are the entities and their relations? | `er-model` | entity boxes with `fields`; cardinality labels |
| What is inside this one service? | `hexagonal` | inbound adapters → core → outbound adapters |
| What is the hot path vs the management path? | `control-data-plane` | control band on top (dashed grey edges), data band below (`hot` edges) |
| Who does which step, and where are the hand-offs? | `swimlane` | one lane per owner; spacers place steps in time columns |

## Notes per template

**containment-architecture** (design.JPG). Left: the caller (often a `brand`
wordmark) and what it also reaches (e.g. GaussDB via ODBC). Middle: the orchestrating
process as `agent`, with inner `service`/`lane` columns `align: stretch` so they run full
height, and the partition clients in a `space-between` column. Right: one `zone` per
host, a hatched `service` per server process inside, components in rows inside that.
Fan-out lines from a union lane use `route: straight`, `from_port: 0.5`, `head: none`.
Every client→server link is a `back` pair (`SQL` / `Arrow Stream`). Show one host in
full and the rest "Simplified" with a note — it says "same as above" without repetition.

**layered-architecture**. Bands are `lane` groups with `title_pos: top-left`, the
service band may be `service` (hatched) to mark the process boundary. If an edge skips a
band, it is either a real violation (draw it, `type: hot`) or the layering is wrong.

**request-flow**. Number edges `1..n` with `label_style: step`; the number can carry one
word (`4 HTTPS`). Side effects that do not block the response are `type: async`.

**sequence**. Keep ≤ 6 actors and ≤ 14 messages; returns are `type: return` (dashed).
Use `divider` for phases ("in parallel", "on retry") and `note` for what a step decides.

**data-pipeline**. One lane per stage, same height (`align: stretch`). The format on
each wire (CDC, Avro, Parquet, JSON) is the most useful label in the picture.

**deployment**. Only when placement is the point. Replica counts go in the pod title
(`api pod  x3`), versions and ports in `sub`.

**module-dependency**. Generate a draft: `sysdiag scan REPO --depth 2 --spec-out deps.spec.json`.
Then merge modules that always travel together, drop modules everyone imports (say so in
`subtitle`), cap at ~15 nodes. One `focus` = the module the reader is about to change.

**event-driven**. Edge labels are event names. Consumers subscribe with `type: async`.

**c4-context**. Exactly one `focus` box: the system. `chip` labels keep it calm.

**architecture-delta**. Same `w` on both panels; suffix ids `_b`/`_a`; changed nodes use
`removed` (red dashed) or `added` (green); unchanged nodes keep their normal role. List
the changes as a numbered note under the panels.

**state-machine**. `terminal` (filled dot) for start, `added`/`removed` roles for
success/failure terminals if useful. Back-edges (`retry`) get `rank_ignore: true` and
explicit `from_side`/`to_side: top` so they arc over.

**er-model**. `fields` like `"PK id  uuid"`, `"FK table_id  uuid"`. Edge `head: triangle`.

**hexagonal**. Only adapters touch the outside; the core never points at a vendor name.

**control-data-plane**. The visual difference (dashed grey vs thick red) is the message.

**swimlane**. Columns are time: align steps with `spacer`s so the step order reads
left→right across lanes. Cross-lane edges are the hand-offs worth discussing.

## Combining views

A codebase usually needs 2–3 diagrams, not one big one:

1. **Overview** — `containment-architecture` or `c4-context`.
2. **Hot path** — `sequence` or `request-flow` for the request that matters most.
3. **Inside the core** — `hexagonal` or `module-dependency` for the service being changed.

Keep ids and labels identical across the views so the reader can match them.
