# PowerPoint construction and quality

## Implementation

Inspect available presentation tooling and dependencies. Use `python-pptx` or an equivalent library that produces editable objects and speaker notes. This skill supplies instructions and style configurations; it does not include an installed rendering engine or automatic research service. Install needed dependencies in an isolated environment when permitted. If unavailable, explain the limitation and retain the outline and sources without claiming PowerPoint generation succeeded.

Create a task-local generation script and structured content data. Separate intake/brief, evidence, product mapping, outline, diagrams, building, review, and revision concerns as the task warrants. Research and judgment belong to the agent; a helper must not fabricate them. Retain script and diagram source with the delivered deck for later edits.

## Resolve style

Read the chosen JSON under `templates/` for narrative, density and arrangement guidance. Visual styling for every built-in layout comes from the team theme: `templates/defaults.json` holds the tokens and [team-theme.md](team-theme.md) explains the components and slide patterns. Apply explicit user overrides last; null means retain the resolved value. Do not apply the team theme over a supplied corporate template or an explicitly requested alternate style.

Build built-in decks from `assets/team-template.pptx` with `scripts/team_deck.py`. The template's branded master draws the lab header, logo, confidentiality line, page number, footer bar and title-slide artwork, so never recreate or duplicate them on slides. Use the library's components instead of ad-hoc shapes so every slide shares the same header geometry, fills, borders, text roles and spacing. If a slide needs a shape the library lacks, build it from `Canvas.rect`, `Canvas.text` and the `C` colour tokens, and follow the same variant meanings.

Keep Microsoft YaHei as the deck font for Latin and East Asian text. If it is unavailable locally, keep the font name in the file and disclose that previews used a substitute. Substitutes are usually wider, so a title that clips in a preview may still fit in PowerPoint; do not respond by shrinking fonts. Rewrite the title shorter instead. Body text is 10–12 pt, dense diagram slides use 8.5–9.5 pt, and the floor is 7.5 pt for tags and small labels. When content does not fit, split the slide.

For existing-hq, resolve null styling fields from the supplied PowerPoint masters, layouts, and theme, record the source path in the task's resolved configuration, and apply explicit overrides. Null fields deliberately indicate inheritance. Preserve theme behavior and source slides; use a new output file. If the chosen library cannot preserve an existing chart, animation, or other object, use a more suitable tool or report the specific limitation before making a lossy revision.

## Editable content

Read [visual-design.md](visual-design.md) for visual selection, sample-derived compositions, and construction rules for architecture diagrams, sequence diagrams, decision flowcharts, tables, and charts. Plan these in the outline before placing objects. Reuse a shared set of visual helpers and resolved style values across the deck.

Build text boxes, tables, charts, and diagrams as native PowerPoint objects. Keep semantic diagram data (nodes, edges, labels, boundaries, and roles) or Mermaid/Graphviz source alongside native shapes to make diagrams reproducible. Include data behind charts. An imported SVG may be reproducible without being editable as individual PowerPoint shapes; disclose that distinction if used.

Architecture diagrams label current, modified, and new components, inputs/outputs, interfaces, and deployment boundaries. Use labels and line styles as well as color. Algorithm diagrams expose the decision-relevant mechanism; value flows connect it to a product metric. Roadmaps need success gates and rollback or exit criteria. Mark unconfirmed connections visibly rather than inventing topology.

Add speaker notes to every slide with the intended spoken explanation, source titles/URLs, assumptions, and technical caveats. Keep references in sources.md and a final references slide. Distinguish timed slides from appendix/reference slides in the outline.

Use one conclusion-led message per slide and typically 3–5 concise bullets at most. Reserve tables for comparisons, decision criteria, and compact evidence. Maintain consistent margins, alignment, typography, and diagram styling.

## Validation

Review the investment argument before layout checks. Read only the titles and visible evidence: can a reviewer name the product gain, its advantage over the baseline, supporting evidence, key trade-off, and reason to commit resources? Check that architecture diagrams explain how a benefit is realized and that the decision ask follows from the opportunity. If the deck mainly describes implementation or experiments, revise its content before polishing visuals. Preserve evidence limits when strengthening the argument.

Resolve every warning printed by `deck.save()`: long titles, likely overflow, text in the logo zone and fonts below the floor. Reopen the saved file with the chosen library. Check slide count and size, order, speaker notes, valid media/relationships, text and object boundaries, chart data, and expected editable objects. Confirm numerical claims have sources or explicit estimate labels. Check that the outline, notes, sources, and assumptions match the final deck.

Render using an available PowerPoint-compatible renderer (for example LibreOffice headless to PDF, then page images) and inspect every slide for clipping, overlap, unreadable labels, contrast, and diagram flow. Also check theme conformance against team-theme.md: branded header and footer visible and not covered, kicker and one-line title on content slides, and no duplicated footer or logo. Structural checks cannot establish visual correctness. Correct observed defects and render affected slides again. If no renderer is available, perform structural checks and explicitly report that visual rendering remains unverified.

Use versioned output paths, avoiding overwriting the supplied deck. Deliver artifact links, the decision narrative, unresolved evidence gaps, and verification limitations.
