---
name: insight-ppt
description: Create, outline, review, or revise editable PowerPoint proposals for HQ technology initiatives, connecting a named product's business value to its current architecture and technical fit. Use for product-specific technology decision decks, not generic technology trend presentations.
---

# Insight PPT

Build an investment argument supported by technical evidence: explain what valuable capability HQ gains, why the current approach leaves an opportunity, and why the expected benefit merits the engineering effort. Connect technology capability → concrete product integration point → engineering metric → business or user outcome. HQ is the user's organization; do not infer its products or stack.

## Intake and scope

Read [references/intake.md](references/intake.md) before research or drafting. Identify create, edit, review, or outline mode from the request; ask if ambiguous. Treat `/insight-ppt` and its suggested flags as natural-language invocation conventions, not an installed executable.

Inspect supplied decks and documents first to prefill the interview. Ask only for missing or ambiguous context. Never invent product facts, architecture, audience, metrics, or performance claims. An explicit unknown can be recorded as an open question; it is not permission to assert an answer. A targeted edit or review reuses established context and needs only relevant missing information.

Use duration as the primary constraint, reserve 1–3 minutes for questions unless told otherwise, and resolve conflicts with requested slide count. Offer the six-template gallery from the intake reference. Recommend a style if none is chosen and include that choice in the brief.

Before building a new deck or substantially redirecting one, present the one-page brief and slide outline and ask: “Approve this brief and outline, or tell me what to change?” Generate only after approval unless the user explicitly requests a fast first draft or has already authorized proceeding. A fast draft still requires intake and must visibly identify unknowns. Outline mode ends with the Markdown outline and brief; review mode ends with findings unless revisions are requested.

## Research and narrative

Read [references/content-and-evidence.md](references/content-and-evidence.md) when developing or assessing content. Write the value thesis for each proposal and build the product-tech mapping before selecting slides. Establish the product opportunity and meaningful advantage over the current approach, then use technical detail to explain how that value can be realized. Architecture or test plans alone do not establish investment merit. Adapt the narrative to the audience and time; do not mechanically fill every section.

Put decisive evidence on the slides: a relevant research result, a concrete worked example, or a clearly labeled quantitative model, with baseline and applicability. Distinguish a measured product shortcoming from a proposed opportunity. Sparse internal data should lead to a conditional but substantive value argument grounded in public evidence, with targeted validation for the remaining gaps. A POC is the next step after establishing the opportunity; keep detailed test procedures in notes unless the user requests an evaluation-design presentation.

Search authoritative, recent primary sources and read the actual evidence. Keep measured results, projected HQ impact, assumptions, and unknowns distinct. Cite factual and numerical claims in speaker notes and references. Never transfer an external benchmark to HQ as an observed result. If tools or evidence are unavailable, disclose the gap and propose validation instead of fabricating sources. Do not send confidential internal material to public search tools.

## Templates and construction

Read [references/build-and-quality.md](references/build-and-quality.md) before generating PowerPoint. Load the shared [style defaults](templates/defaults.json) and the selected editable layout configuration:

1. [Executive Insight](templates/executive-insight.json)
2. [Technical Architecture](templates/technical-architecture.json)
3. [Product Strategy](templates/product-strategy.json)
4. [Research-to-Product](templates/research-to-product.json)
5. [Minimal Corporate](templates/minimal-corporate.json)
6. [Existing HQ Template](templates/existing-hq.json)

User overrides take precedence. Existing HQ mode requires a supplied template or reference deck; do not silently substitute invented corporate styling. Preserve its master slides, layouts, and typography. The other configurations are editable design tokens, not prebuilt PowerPoint masters.

For built-in layouts, use the shared personal defaults: the V4 muted red/grey design with a white slide background, Arial throughout, 29 pt charcoal titles, and 18 pt explanatory body text. Use muted red (`983C45`) for emphasis, charcoal (`363338`) for primary text, and muted grey for supporting text. Tables use charcoal headers with white text and pale red/grey rows; diagrams and callouts share those light fills. Compact table and diagram text is typically 14 pt; reserve 10 pt for captions and small figure labels. A white slide background does not require white objects: choose contrasting fills for table headers, alternating rows, callouts and diagram groups when they improve readability. Keep compact figures legible and use the surrounding space for useful explanation and comparisons. An explicitly selected alternate style or supplied corporate template takes precedence over these defaults.

Use native editable text, shapes, connectors, tables, and charts wherever possible. Retain source for generated diagrams; never flatten entire slides into screenshots. Keep at most two fonts and three primary colors unless the corporate template requires more. Use conclusion-led slide titles and readable content.

Read [references/visual-design.md](references/visual-design.md) when planning or building diagrams, charts, tables, or flowcharts. Select a visual per slide based on the relationship or evidence it must explain; do not default to bullet lists when structure, sequence, comparison, or numerical trends carry the message. Record the visual choice and required data in the outline. Use the sample-derived layout recipes in that reference and resolve one shared visual system for the whole deck. References from different decks supply composition ideas, not competing themes or factual content.

For architecture slides with multiple subsystems or boundaries, also read [references/architecture-diagrams.md](references/architecture-diagrams.md). Model containment and interfaces before placing shapes. Show a structured system map with nested groups, component rows and routed connections when the architecture calls for it; a row of three process boxes is not a substitute for those relationships. Give the diagram enough slide area to explain the system, while keeping the V4 default style.

When explaining an algorithm to technical reviewers, include a visible mechanism diagram at the level needed to justify its benefit. Show the key intermediate representation and operations, not only input/output boxes or the component's location in the product. Read the algorithm diagram guidance in the content reference; retain the value argument and evidence alongside the mechanism.

## Revisions and delivery

For existing-deck edits or reviews, read [references/revision.md](references/revision.md). Preserve unaffected content and styling, use a new versioned filename, and identify changed slides and reasons.

For deck creation or revision deliver the editable `.pptx`, Markdown source outline, speaker notes embedded on every slide, `sources.md`, reproducible diagram sources where feasible, and `assumptions-and-open-questions.md` when evidence or inputs are incomplete. Keep a deck-generation or revision script with the output when one is used. Deliver review findings or an outline without an unsolicited `.pptx` for those modes.

Before delivery, check whether a reviewer can explain why the proposal deserves investment from the titles and visible evidence alone. Revise a deck dominated by components, risks, or experiments if it does not demonstrate a meaningful product advantage and credible implementation path. Do not increase confidence beyond the evidence to make the argument persuasive; narrow or qualify the recommendation when needed.

Validate structure and visually inspect rendered slides before delivery when rendering is available. State any unverified visual or compatibility checks honestly. Do not claim a deck exists until the file has been generated and inspected.
