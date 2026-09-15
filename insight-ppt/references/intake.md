# Intake and brief

Before researching, drafting, or generating a deck, run an **intake interview**. Do not make up missing product context, stack details, target audience, metrics, or performance claims.

### Step 1: Identify the task

Ask the user whether they want to:

- Create a new proposal deck
- Edit an existing draft
- Review and improve a draft
- Produce a concise outline before generating PowerPoint

If the user provides an existing `.pptx`, source outline, product documentation, or prior deck, inspect it and preserve useful structure, visual style, and factual content unless the user requests a redesign.

### Step 2: Ask for required parameters

Ask the following questions in a compact, numbered form. Pre-fill values already supplied by the user and ask only for missing or ambiguous items.

```text
To create the proposal deck, please confirm:

1. Topic / proposed technology:
2. HQ product(s) affected:
3. Current product architecture and technology stack:
4. Product problem or opportunity to address:
5. Target audience: Executive / Product / Technical leadership / Mixed
6. Presentation duration: 5, 10, 15, 20, or 30 minutes?
7. Preferred output length: Auto, 6-8, 8-10, 10-12, 12-15, or custom slide count?
8. Presentation style/template: choose one from the available templates below.
9. Desired decision or call to action: Approve research, approve POC, approve pilot, approve production investment, or other?
10. Evidence available: papers, benchmarks, internal metrics, competitor examples, URLs, or documents?
11. Branding assets: HQ logo, brand colors, font, existing PPT template, or “use default”?
12. Constraints: deadline, team capacity, budget, deployment environment, compliance, latency, cost, or data restrictions?
```

### Step 3: Convert duration to slide count

Use the requested presentation duration as the primary constraint. Recommend a deck length, then ask for confirmation if needed.

| Presentation duration | Recommended slides | Intended use |
|---|---:|---|
| 5 minutes | 5-7 | Decision teaser or project pitch |
| 10 minutes | 8-10 | Concise technology insight proposal |
| 15 minutes | 10-12 | Standard proposal with technical and business fit |
| 20 minutes | 12-15 | Decision deck with stronger evidence and alternatives |
| 30 minutes | 15-20 | Technical review or architecture discussion |

Rules:

- If the user provides both duration and a slide count that conflict, flag the conflict and recommend a choice.
- Reserve 1-3 minutes for questions unless the user says otherwise.
- Prioritize a coherent narrative over filling a fixed slide count.
- If slide count is set to `Auto`, derive it from duration and audience.

### Step 4: Offer a template gallery

Present the layout options below and ask the user to select by number or name. Built-in layouts use the shared personal defaults in `templates/defaults.json`: the V4 muted red/grey design, with a white slide canvas, Arial throughout, 29 pt titles, 18 pt explanatory text, charcoal text, muted red emphasis, and pale red/grey object fills. Tables use charcoal headers with white text; compact tables and diagram labels are typically 14 pt. Layout choice changes organization and emphasis; an explicit palette/font choice overrides the defaults. Supplied corporate templates retain their own styling. If the user does not choose, recommend a layout based on audience:

```text
Choose a presentation template:

1. Executive Insight
   - Best for: VP, director, product leadership, decision meetings
   - Look: Clean whitespace, strong headline per slide, restrained diagrams, business metrics emphasized
   - Palette: Shared personal defaults; configurable
   - Detail level: Concise

2. Technical Architecture
   - Best for: Architects, engineering leadership, platform teams
   - Look: Structured layouts, architecture diagrams, component callouts, evidence tables
   - Palette: Shared personal defaults; configurable
   - Detail level: Medium to high

3. Product Strategy
   - Best for: Product, business, and technical mixed audience
   - Look: Product journey, value flow, roadmap, customer and KPI emphasis
   - Palette: Shared personal defaults; configurable
   - Detail level: Medium

4. Research-to-Product
   - Best for: AI/ML, data systems, research transfer proposals
   - Look: Paper-to-product storyline, algorithm concept diagram, benchmark evidence, integration path
   - Palette: Shared personal defaults; configurable
   - Detail level: Medium to high

5. Minimal Corporate
   - Best for: Formal HQ reviews and reusable internal decks
   - Look: Conservative, brand-friendly, low visual risk, compact tables and simple diagrams
   - Palette: Shared personal defaults; configurable
   - Detail level: Medium

6. Existing HQ Template
   - Best for: When the user uploads an approved corporate template or reference deck
   - Look: Match the supplied master slides, typography, colors, and layouts
   - Detail level: Configurable
```

Template system requirements:

- Implement each template as an editable style configuration, not as static images.
- Keep colors, fonts, title styles, body styles, diagram colors, and layout rules in separate template configuration files.
- Allow the user to override palette, font, logo, density, and use of icons.
- Use accessible contrast and readable font sizes.
- Use no more than 2 fonts and 3 primary colors in a generated deck unless the supplied corporate template requires otherwise.

### Step 5: Confirm a one-page deck brief

Before creating the `.pptx`, show the user a concise brief containing:

- Working title
- Target audience
- Duration and planned slide count
- Selected template
- HQ products and current stack
- Product problem
- Proposed technology
- Expected decision ask
- Evidence sources available or still required
- Value thesis for each proposal: use case, advantage over the current approach, supporting evidence, and expected product outcome
- Initial narrative / slide outline
- Visual plan per substantive slide: diagram/chart/table/flowchart or text, intended takeaway, required inputs, and evidence gaps; use visual-design.md for selection and sample-derived layouts

Ask: **“Approve this brief and outline, or tell me what to change?”**

Generate the deck only after the user approves the brief, unless the user explicitly asks for a fast first draft.

## Command-style requests

```text
/insight-ppt create
/insight-ppt edit <deck-file>
/insight-ppt review <deck-file>
/insight-ppt outline
```

Optional parameters after intake is complete:

```text
--topic "..."
--hq-products "..."
--current-stack "..."
--product-problem "..."
--audience "executive|product|technical|mixed"
--duration "5|10|15|20|30"
--slides "auto|6-8|8-10|10-12|12-15|custom"
--template "executive-insight|technical-architecture|product-strategy|research-to-product|minimal-corporate|existing-hq"
--decision-ask "research|poc|pilot|production|other"
--evidence "..."
--branding "..."
--constraints "..."
```
