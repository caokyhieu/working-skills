# Layout rules, review loop, checklist

## Composition

- **One reading direction.** LR for request paths and pipelines, TB for tiers and
  control-over-data. The entry point is top-left; data at rest sits at the far end.
- **Containment over arrows.** If A runs inside B, nest it; do not draw "A → B: runs on".
- **Fan-out reads as a fan.** Partitions/replicas stacked in a `space-between` column,
  wired from one point (`from_port: 0.5`).
- **Same things, same size.** Sibling clients/workers get the same `w`/`h`; sibling hosts
  the same `w`. Unequal sizes imply unequal importance.
- **Whitespace is structure.** Root `gap` 80–110 between major columns; 20–40 inside.
- **Show one, simplify the rest.** Draw one host in full, the rest reduced with a
  "Simplified" note.
- **Budget.** ≤ ~20 leaf nodes, ≤ ~25 edges, ≤ 2 `focus` nodes, ≤ 6 notes. Beyond that,
  split (overview + detail).

## Wiring

- Orthogonal only (the router does it). `route: straight` only for fan lines.
- Each edge leaves and enters perpendicular to a box side; several edges on one side get
  separate ports automatically, ordered to avoid crossings.
- Never through a box: lint reports it. Fix in this order: reorder children → change
  `from_side`/`to_side` → `from_port`/`to_port` → `via`.
- No shared runs: two edges on the same line look like one. Lint reports it.
- Request/response = `back` pair, not two independent edges.
- Labels: pills ≤ 18 characters (protocol or payload name). Longer explanations are
  `label_style: text` or a note.
- Edges may end on a group (the whole host/server) when the target component does not
  matter, exactly like design.JPG's HTTP pair into the broker.

## Review loop (after every build)

1. `sysdiag build …` → fix every `WARN` until `lint: clean` (or each remaining warning is
   deliberate and you can say why).
2. `render … --svg` → **Read the PNG**.
3. Check, in order:
   - **Question**: can the reader answer the question from step 0 in ten seconds?
   - **Eye path**: does the eye travel entry → … → data in the reading direction?
   - **Crossings**: any crossing a child reorder would remove? (Reorder; re-run.)
   - **Labels**: each pill next to the wire it names, not floating between two wires?
   - **Text**: nothing clipped or overflowing? (Widen with `w`, or raise
     `font.char_width` for the family.)
   - **Balance**: one region cramped while another is empty? (Adjust `gap`, `justify`, `w`.)
   - **Truth**: every node/edge still matches `model.md`?
4. Edit the spec, rebuild, re-render. Stop when nothing in step 3 fails.

## Pre-delivery checklist

- [ ] Question sentence written; template chosen for that question
- [ ] Codebase mode: `--require-evidence` clean or every `assumed` reported
- [ ] `lint: clean` (or deliberate warnings explained)
- [ ] PNG reviewed with the loop above, at least once after the last change
- [ ] Wires labelled with what travels; request/response as pairs
- [ ] ≤ 2 focus nodes; roles chosen by meaning
- [ ] Files saved: `.spec.json`, `.excalidraw`, `.png`, `.svg` (+ `.evidence.md`)
- [ ] Reported: question, left-out items, assumptions, how to edit
