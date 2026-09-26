# Architecture diagrams with clear hierarchy

Use this reference when a diagram must explain several subsystems, nested responsibilities, shared services, or deployment boundaries. The aim is the structural richness of `samples/block-diagram.jpg`, expressed in the deck's consistent style. The sample is optional: this guide is self-contained in an installed skill.

## Model the system before drawing

Build a small semantic inventory from the supplied architecture and evidence:

- **Containers:** named systems, subsystems, ownership or deployment boundaries. Record a stable ID, parent ID and boundary meaning. A logical responsibility group is not automatically a deployed service.
- **Components:** name, parent container, short responsibility, and status (existing, modified, new, or unknown). Keep product-specific names when known; do not add plausible services simply to fill space.
- **Connections:** source and target IDs, direction, interface or payload label, and relationship type (request, data movement, dependency, etc.). Record whether each is confirmed, proposed or unknown.
- **Slide purpose:** the particular integration change, bottleneck or trade-off the audience should understand. Decide which path needs visual emphasis and which detail belongs in a drill-down.

Do not treat all arrows as execution order. Containment explains where a component belongs; connections explain how components interact. Keep these meanings separate. If the slide is only a responsibility map, label it as such rather than implying a verified deployment topology.

## Choose a composition that fits the system

| System structure | Useful composition |
|---|---|
| Applications above several processing subsystems, shared supporting services | Top application band, broad nested processing region, narrow side column for supporting systems |
| Distinct presentation, service and data layers | Horizontal layer bands with components arranged within each layer |
| Control plane and data plane | Two named regions, with lifecycle/control links separated from the primary data path |
| Multiple independently deployed services or zones | Columns or grouped regions for the actual deployment boundaries |
| A change to an established system | One map highlighting additions/modifications; before/after only when the structural difference warrants it |

For a complex architecture slide, make the diagram the dominant content region—often roughly two-thirds to four-fifths of usable slide area. Place a short benefit/trade-off callout beside or below it. A large comparison table should not force the architecture into a tiny three-box strip. These proportions are starting points, not fixed quotas; use the audience, slide count and known detail to decide.

### Sample-inspired wireframe

This is a layout pattern, not a real product architecture. Replace the groups and components with supported facts and draw only supported or explicitly proposed interfaces.

```text
┌─ Supporting systems ─┐  ┌─ Applications / entry points ───────────────┐
│ Component A         │  │ Client A       Client B       API entry    │
│ Component B         │  └────────────────────────────────────────────┘
│ Component C         │  ┌─ Main processing system ───────────────────┐
└─────────────────────┘  │ ┌─ Subsystem 1 ─────┐ ┌─ Subsystem 2 ────┐ │
┌─ Data management ───┐  │ │ Component D      │ │ Component E      │ │
│ Store / catalog     │  │ └──────────────────┘ └──────────────────┘ │
│ Lifecycle service   │  │ ┌─ Shared processing layer ──────────────┐ │
└─────────────────────┘  │ │ Component F   Component G   Component H│ │
                         │ └────────────────────────────────────────┘ │
                         └────────────────────────────────────────────┘
```

The sample's useful qualities are its named regions, aligned component rows, nested subsystems and clear space between regions. Preserve those qualities without reproducing its many colors, placeholder content or unrelated topology.

## Lay out containers, components and connections

1. **Reserve the canvas.** Mark the title, diagram bounds, takeaway and source caption. Use the remaining region for architecture, not decorative empty boxes.
2. **Size from the content.** Estimate node sizes from the resolved font, label length and padding. Reserve a separate header band for every container. Compute the required child layout before fixing the parent size; then position the top-level regions. Prefer one- or two-line component names with a short responsibility only where needed.
3. **Arrange by relationship.** Align peers in rows or columns. Put heavily connected components close together; keep the main reading direction consistent. Usually two or three visible containment levels are enough. Use a drill-down when a deeper level is needed to explain the decision.
4. **Reserve routes.** Leave gutters between regions and between component rows. On a widescreen slide, approximately 0.15–0.25 inch inner padding and 0.25–0.4 inch inter-region gaps are useful starting points; enlarge them for edge labels and larger fonts. Do not hardcode these dimensions regardless of density.
5. **Route edges after placement.** Prefer horizontal/vertical segments with few bends. Enter and leave at deliberate points on node boundaries. Route around nodes, labels and container headers. Reorder nodes before accepting a tangle of crossing lines.
6. **Refine the emphasis.** Highlight the proposed change or decision-relevant path, leaving supporting structure quieter. Keep named subsystems and the main path readable at presentation size.

For repeated or crowded layouts, calculate positions from a grid and container bounds in the generation script instead of maintaining dozens of unrelated coordinates. An available graph-layout tool can propose node positions, but inspect its result and recreate native PowerPoint shapes/connectors where practical. Automatic placement does not establish architectural correctness.

## Connector rules that prevent ambiguity

- Label important cross-boundary interfaces with a short operation or payload, such as “candidate IDs” or “token blocks.” Put labels in reserved clear space beside a segment, not over component text.
- Draw an arrow to the component that actually participates. Connect to a container only if it represents a group-level interface; label that interface explicitly.
- Shared trunks must mean a real shared flow or an explicitly labeled aggregation. Do not merge unrelated lines merely to make the picture look cleaner. Use a junction dot for an intentional branch; a crossing without a dot is not a connection.
- Distinguish parallel flows with separate routes. Use two directed arrows when request and response need different labels; otherwise one labeled relationship may suffice. Avoid unexplained bidirectional arrows.
- Use solid lines for the main confirmed/proposed path and a separately explained treatment for uncertainty or secondary dependencies. Keep edge semantics distinct from the existing/modified/new status on nodes.
- Save edge endpoints, labels, container membership and bend points in the semantic source. Attach native connector endpoints to shapes when the presentation tool supports it; otherwise preserve the geometry in reproducible source and recheck routes after moves.

## Team-theme styling for nested architecture

Resolve exact values from `templates/defaults.json` and build with `scripts/team_deck.py` (`card`, `node`, `arrow`, `connector`, `section`). The shared visual grammar:

- **Canvas:** white, under the branded master. **Outer group:** grey `F5F5F5` panel with a thin `DDDDDD` border and a bold 9.5–11 pt heading inside its top-left, or a spaced grey caps section label above it. **Nested components:** white nodes with `DDDDDD` borders inside the grey group, so each nesting level has a different fill.
- **Status:** ordinary components are `neutral`/`white`. The component the proposal adds or owns is `accent` (solid red, white text) or `outline` (red border). Inferred, future or in-progress parts are `dashed` red. The chosen or final subsystem can be `dark`. Add a legend or caption such as "solid is confirmed, dashed is inferred"; colour alone must not carry status.
- **Typography:** Microsoft YaHei; node labels 9.5 pt bold with an 8 pt grey second line; group headings visibly stronger. Do not shrink node text below 8 pt. Enlarge the diagram or split it instead.
- **Connections:** small grey (`898989`) block arrows or 1 pt connectors for flow; 8–9 pt grey edge labels beside the arrow; red only for the decisive path. Use consistent line weights and no shadows or gradients (the library strips theme effects).
- Leave a side column (about 2.5–3 in) for "What changed", "Guards" or "Still not public" notes when the architecture needs interpretation, as the team decks do.

## Review the architecture, not just the shape bounds

Check the semantic inventory against the final diagram: are important components present, in the right groups, and connected to the correct endpoints? Confirm there are no invented links, orphaned components without an explained role, hidden boundary crossings or status conveyed by color alone.

Render and inspect the slide at presentation size. Trace the main path from entry to result, then inspect secondary connections. Fix labels touching edges, arrows through nodes, ambiguous intersections, missing arrowheads, cramped nested headers and inconsistent padding. Inspect the slide within the deck as well as alone.

If it is still too dense, first remove duplication, shorten labels and reroute edges. Then move secondary interfaces to a linked detail view or appendix if the slide budget allows. With a fixed slide count, aggregate real subsystems and explicitly name the omitted detail in notes; do not silently erase the mechanisms that justify the proposal. Return to a simple pipeline only when the actual question is about a sequence rather than system structure.
