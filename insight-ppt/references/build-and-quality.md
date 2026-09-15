# PowerPoint construction and quality

## Implementation

Inspect available presentation tooling and dependencies. Use `python-pptx` or an equivalent library that produces editable objects and speaker notes. This skill supplies instructions and style configurations; it does not include an installed rendering engine or automatic research service. Install needed dependencies in an isolated environment when permitted. If unavailable, explain the limitation and retain the outline and sources without claiming PowerPoint generation succeeded.

Create a task-local generation script and structured content data. Separate intake/brief, evidence, product mapping, outline, diagrams, building, review, and revision concerns as the task warrants. Research and judgment belong to the agent; a helper must not fabricate them. Retain script and diagram source with the delivered deck for later edits.

## Resolve style

Read the chosen JSON under `templates/`. For a built-in layout, recursively overlay the typography, palette, shades, component styles and surface fields from `templates/defaults.json`, keeping the chosen layout's narrative and arrangement guidance. Apply explicit user overrides last; null means retain the resolved value, and false for icons means disable icons. Do not apply personal defaults over a supplied corporate template or an explicitly requested alternate style. Colors are six-digit RGB strings; these are personal design choices, not a claim of official Huawei brand specifications.

Resolve `slide_background` separately from object fills. Keep the slide canvas white by default. Tables, text boxes and diagram groups may use the `surfaces` colors: pale red emphasis, light grey panels or alternating row fills, with thin neutral borders. Use charcoal or muted red text on these light fills. Table headers use charcoal fills and white text, matching V4. Solid muted-red emphasis nodes also use white text. Supporting text uses muted grey; do not force every object to use the same text color. Avoid filling every container just because a color is available.

Apply fonts, title/body sizes, diagram rules, and layout margins. The shared defaults match V4’s rendered hierarchy: Arial throughout, 29 pt main titles, 18 pt explanatory body, 17 pt subtitles, 13 pt section headings, and 10 pt captions. Use the separate table, chart and diagram styles for compact figures: tables and diagram labels default to 14 pt; small figure labels may use 10–17 pt when necessary. The body minimum applies to explanatory prose, not captions or figure labels. Keep the hierarchy visible; enlarge or split crowded visuals instead of reducing all text to 10–11 pt. V4’s actual slide typography takes precedence over its older nominal 30/20 pt template values. Set the native Office theme and text properties consistently, including East Asian body-font mappings. Retain the requested font names in the deck if unavailable locally, and disclose any substitute used only for previews; do not silently replace the requested deck fonts. Logo paths are supplied per task. Built-in defaults use widescreen slides; a provided corporate deck retains its own size.

For existing-hq, resolve null styling fields from the supplied PowerPoint masters, layouts, and theme, record the source path in the task's resolved configuration, and apply explicit overrides. Null fields deliberately indicate inheritance. Preserve theme behavior and source slides; use a new output file. If the chosen library cannot preserve an existing chart, animation, or other object, use a more suitable tool or report the specific limitation before making a lossy revision.

## Editable content

Read [visual-design.md](visual-design.md) for visual selection, sample-derived compositions, and construction rules for architecture diagrams, sequence diagrams, decision flowcharts, tables, and charts. Plan these in the outline before placing objects. Reuse a shared set of visual helpers and resolved style values across the deck.

Build text boxes, tables, charts, and diagrams as native PowerPoint objects. Keep semantic diagram data (nodes, edges, labels, boundaries, and roles) or Mermaid/Graphviz source alongside native shapes to make diagrams reproducible. Include data behind charts. An imported SVG may be reproducible without being editable as individual PowerPoint shapes; disclose that distinction if used.

Architecture diagrams label current, modified, and new components, inputs/outputs, interfaces, and deployment boundaries. Use labels and line styles as well as color. Algorithm diagrams expose the decision-relevant mechanism; value flows connect it to a product metric. Roadmaps need success gates and rollback or exit criteria. Mark unconfirmed connections visibly rather than inventing topology.

Add speaker notes to every slide with the intended spoken explanation, source titles/URLs, assumptions, and technical caveats. Keep references in sources.md and a final references slide. Distinguish timed slides from appendix/reference slides in the outline.

Use one conclusion-led message per slide and typically 3–5 concise bullets at most. Reserve tables for comparisons, decision criteria, and compact evidence. Maintain consistent margins, alignment, typography, and diagram styling.

## Validation

Review the investment argument before layout checks. Read only the titles and visible evidence: can a reviewer name the product gain, its advantage over the baseline, supporting evidence, key trade-off, and reason to commit resources? Check that architecture diagrams explain how a benefit is realized and that the decision ask follows from the opportunity. If the deck mainly describes implementation or experiments, revise its content before polishing visuals. Preserve evidence limits when strengthening the argument.

Reopen the saved file with the chosen library. Check slide count and size, order, speaker notes, valid media/relationships, text and object boundaries, chart data, and expected editable objects. Confirm numerical claims have sources or explicit estimate labels. Check that the outline, notes, sources, and assumptions match the final deck.

Render using an available PowerPoint-compatible renderer and inspect every slide for clipping, overlap, unreadable labels, contrast, and diagram flow. Structural checks cannot establish visual correctness. Correct observed defects and render affected slides again. If no renderer is available, perform structural checks and explicitly report that visual rendering remains unverified.

Use versioned output paths, avoiding overwriting the supplied deck. Deliver artifact links, the decision narrative, unresolved evidence gaps, and verification limitations.
