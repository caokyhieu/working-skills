# Visual planning and consistent design

## Choose the visual before building

For each substantive slide, record in the outline: conclusion, visual type, entities or data to show, evidence status, and any supporting explanation. Use the representation that makes the claim inspectable:

| What the reader needs to understand | Preferred visual |
|---|---|
| Components, layers, ownership, integration boundaries | Grouped block architecture |
| Messages exchanged between participants over time | Sequence diagram with participant columns |
| Steps, conditions, branches, retries, outcomes | Decision flowchart; swimlanes if ownership matters |
| Exact values, alternatives, criteria, mixed units | Native table or decision matrix |
| Trend over time | Native line chart |
| Magnitudes across categories | Native bar or column chart |
| Relationship between two numeric variables | Scatter plot |
| Several related metrics and their interpretation | Evidence dashboard combining table, chart, and commentary |
| Algorithm mechanism | Intermediate representations and operations; see content-and-evidence.md |

Use meaningful visuals where content calls for them, without imposing a quota or forcing every type into every deck. Missing quantitative data is a reason to use a qualitative comparison or mark an unknown, not to invent a chart. A title or decision-ask slide can remain text-led.

## One visual system per deck

Resolve style once using build-and-quality.md and keep the resolved configuration beside the generation source. Reuse helpers for panel headings, nodes, connectors, tables, charts, and captions so slides do not acquire independent styles. Inherit the same typography, accent, neutral surfaces, alignment grid, and emphasis rules across every visual type.

- Built-in defaults use the V4 design: white canvas, Arial, charcoal (`363338`) main text, muted red (`983C45`) emphasis, muted grey (`686368`) supporting text, and pale red (`F2E5E6`)/grey (`EFEEEE`) fills. Use charcoal table headers with white text. Titles are 29 pt, explanatory body 18 pt, and compact tables/diagram labels typically 14 pt; captions and small figure labels can use 10 pt. Use the selected corporate or explicit alternate style when applicable.
- Use a common title position, content boundaries, panel-heading treatment, caption position, and spacing unit. Equal-level nodes share padding, shape, border width, and label size. Align table and chart panels to the same grid.
- Map semantic roles consistently: neutral for baseline or unchanged elements, accent for the proposed component or focal series, and pale accent for supporting emphasis. Add explicit labels such as “New” and “Modified”; color alone must not carry status. Keep each entity's series color and line treatment stable across charts.
- Distinguish component status on node borders from edge meanings. Define connector styles per diagram and show a legend when ambiguous; do not use one dashed line to mean both “uncertain” and “response” in the same diagram.
- Use neutral tints, line patterns, markers, and direct labels for additional series rather than introducing a new palette. Avoid gradients, shadows, or decorative icons absent from the resolved style.
- Preserve the resolved font-size floor for each text role (body, table, diagram, chart or caption). If labels do not fit, shorten them, enlarge the visual, or split the material into overview and detail slides. Do not solve density by shrinking text or stretching a screenshot.

## Sample-derived composition recipes

The repository's `samples/` images come from different decks. The descriptions below make these recipes usable when only the skill folder is installed. If the images are available, inspect them as composition references. They are not deck templates or evidence: do not copy their company names, metrics, placeholder text, logos, footers, colors, or fonts into a proposal.

### Grouped block architecture — `block-diagram.jpg`

The useful pattern is a narrow supporting-systems column beside a wide main-system region, with applications across the top and processing subsystems nested below. It conveys hierarchy through containment and connections through arrows.

For complex architecture, read [architecture-diagrams.md](architecture-diagrams.md) before construction. It expands this recipe into semantic modeling, nested layout, connector routing and visual review. Preserve meaningful detail rather than automatically simplifying an architecture into a pipeline.

- Adapt the grouping to the actual product: title each boundary and distinguish components from containers. Use light neutral group fills, white component nodes, and an accent on the decision-relevant change.
- Show directional, labeled interfaces between groups or components. Route connectors through gutters and attach endpoints to their intended nodes; an arrow into a container represents the whole group only when that is intended.
- Keep reading order consistent, usually left-to-right or top-to-bottom. Reduce nesting or move detail to another slide when boundaries become difficult to trace.
- Pair the architecture with a short benefit or trade-off callout. Do not reproduce unknown topology from the sample or assume its arrangement fits every system.

### Evidence dashboard — `table-number-chart.webp`

The useful pattern is aligned panels combining explanatory text, compact metric tables, and a trend chart. A shared header treatment makes the parts feel related.

- Use this layout only when the panels support one conclusion. A useful adaptation puts explanation and comparison on the left, key metrics and the decisive chart on the right; fewer panels are preferable when the evidence is simple.
- Build native tables with clear headers, units, consistent precision, right-aligned numeric cells, and left-aligned labels. Use light row striping or restrained rules and emphasize only the decisive row or cell. Mark unavailable values as “Unknown” or “—” with an explanation, never as zero.
- Build a native chart with editable series data. Show the measure, unit, period, baseline, and relevant source or estimate label. Align the chart's fonts and accent with the tables; remove unnecessary borders and gridlines.
- Use bars for category magnitudes and lines for time trends. Bar magnitude axes normally start at zero; disclose and justify any exception. Clearly label a restricted line-chart range. Keep comparable panels on consistent scales. Avoid 3-D effects and dual axes that obscure the comparison.
- Check denominators, totals, percentage versus percentage-point changes, missing periods, and currency/unit conversions. Do not infer values by tracing the example chart. Retain the source data and transformations with the output.

### Participant sequence — `flow-chart.jpg`

This sample is a sequence diagram: participants sit across the top and messages progress downward. Use it to explain API calls, handoffs, callbacks, or asynchronous work.

- Place participants in equal-width columns with a common header style and aligned lifelines. Draw each message on its own row, label the operation, and point the arrow toward the receiver.
- Show actual causal order. Differentiate requests, returns, and asynchronous messages only when relevant, with a small legend. Group repeated or optional exchanges into labeled regions.
- Include failure, timeout, retry, or fallback paths when they affect the decision and are known. Label proposed behavior; do not invent a protocol to complete the picture.
- Use the deck's neutral and accent roles rather than assigning unrelated blues to participants. Split a long exchange into phases instead of squeezing more message rows onto one slide.

### Decision flowchart — complementary to the sequence sample

Use a flowchart when branching logic matters more than messages between participants. Use process rectangles, decision diamonds, clear start/end nodes, and arrows. Label every decision exit with its condition, such as “Pass” / “Fail”; identify retry limits or exit paths when specified. Keep the main path visually continuous and route loops around its outside. Use swimlanes only when responsibility needs to be visible. Preserve the same node fonts, fills, line weights, and spacing as the architecture and sequence diagrams.

## Build and inspect

Use native editable shapes and connectors for diagrams, native tables for comparisons, and native charts with embedded data where supported. Store semantic diagram sources (node IDs, groups, roles, edges, and labels; ordered messages for sequence diagrams) and chart data with the build source. Reproducible SVG is a fallback when a needed visual cannot reasonably be built natively; disclose its editing limits. Never use the sample image as the finished slide visual.

Inspect both individual slides and a rendered deck overview. Check:

- Architecture containment matches the intended boundaries; connectors reach the correct nodes and labels do not collide.
- Sequence messages follow causal order; flowchart branches are labeled and paths terminate or visibly loop as intended.
- Chart values match retained data and visible claims; legends, units, baselines, and table headers are readable.
- The same semantic role has the same styling throughout the deck; titles, panel headings, borders, and spacing look like one design system.
- The visual communicates the slide's conclusion without relying on the speaker notes to explain its basic structure.

Apply the structural and rendering checks in build-and-quality.md. A successful file save does not establish visual quality.
