---
name: system-diagram
description: Draw system and architecture diagrams as editable Excalidraw files (.excalidraw + PNG/SVG) in a clean hatched-container style — hosts, servers and components nested inside each other, request/response wires with purple protocol pills (SQL / Arrow Stream, HTTP / JSON), fan-out to partitions, annotations. Works from a codebase (scans entry points, servers, clients, compose/k8s files and imports, then checks every box and arrow against the code with path::symbol evidence) or from an idea described in words. Fifteen templates — containment architecture, layered, request flow, sequence, data pipeline, deployment, module dependency, event-driven, C4 context, architecture delta (before/after), state machine, ER model, hexagonal internals, control/data plane, swimlane. A JSON spec is compiled by a script that does layout, orthogonal routing, port fanning, arrow binding and lint, then the diagram is rendered with Excalidraw's own exporter and inspected visually until clean. Use when asked to draw, sketch, diagram or visualise a system, architecture, service, pipeline, deployment, data flow, request path, module structure or "how this codebase works", or to turn an idea into an Excalidraw diagram.
---

# system-diagram

Draws the system the way an engineer would on a whiteboard, but precise: containers
that nest (host ⊃ process ⊃ server ⊃ component), wires that say what travels on them,
and nothing that is not true. Output is a real `.excalidraw` file people keep editing,
plus a PNG/SVG for docs and slides. `design.JPG` at the repo root is the reference look.

You never hand-write Excalidraw JSON. You write a short **spec** (what exists, how it
nests, what connects); `scripts/sysdiag.py` compiles it (layout, routing, bindings, lint)
and `scripts/render.py` renders it with Excalidraw itself so you can look at it.

Five rules:

- **True before pretty.** In codebase mode every node and edge comes from code you read,
  carrying `ev: "path::symbol"`. Anything inferred is `assumed: true`; anything not built
  is role `planned`. Never draw a component because "systems like this usually have one".
- **The wire carries the meaning.** Label edges with what travels (SQL, Arrow Stream,
  gRPC, Parquet, `OrderPlaced`), not with verbs like "calls" or "uses". Request/response
  is a `back` pair.
- **Nesting is the architecture.** Containment shows deployment and ownership: a
  component sits inside the server process that hosts it, inside the host that runs it.
  If two things share a box they share a process.
- **Delete until it hurts.** One diagram answers one question. Over ~20 leaf nodes or
  ~25 edges, split into an overview plus detail diagrams. Focus colour on ≤ 2 nodes.
- **Look at it.** Lint clean is necessary, not sufficient. Render, open the PNG, fix,
  repeat (`references/layout-rules.md` §Review loop).

## Files

| Path | What |
|---|---|
| `scripts/sysdiag.py` | `build`, `lint`, `scan`, `templates`, `new` (standard library only) |
| `scripts/render.py` | `.excalidraw` → PNG (+ `--svg`) via Playwright and pinned Excalidraw |
| `assets/theme.json` | Every colour, font and spacing — the only place style lives |
| `templates/*.spec.json` | Fifteen worked specs, one per diagram type |
| `templates/previews/*.png` | What each template renders to — look before choosing |
| `references/templates.md` | Which template answers which question, and its layout grammar |
| `references/spec-format.md` | Every spec key |
| `references/style.md` | Roles (what each colour means), the design.JPG look, re-skinning |
| `references/codebase-reading.md` | Building a system model from code, with evidence |
| `references/layout-rules.md` | Layout and wiring rules, review loop, checklist |

Below, `sysdiag` = `python3 <skill dir>/scripts/sysdiag.py` and
`render` = `uv run --with playwright python <skill dir>/scripts/render.py`.
First render on a new machine: `uv run --with playwright playwright install chromium`.
Rendering needs network access to esm.sh (Excalidraw is loaded from there).

## Workflow

### 0. Pin the question and the reader

Before anything else, one sentence: *"This diagram shows <reader> how <question>."*
("…shows a new backend engineer how a StarRocks query reaches Druid segments.")
It decides the template, the zoom level and what to leave out. If the user gave no
reader or question and you cannot infer it, ask once; otherwise state your assumption.

### 1a. From a codebase

Follow `references/codebase-reading.md`. In short:

1. `sysdiag scan <repo> [--exclude 'vendored/*'] > <out>/scan.md` — languages, manifests, compose/k8s services,
   Dockerfiles, entry points, integration hints (servers, clients, drivers, brokers,
   engines, JNI/FFI), endpoint literals, env names, module import graph. The scan
   **finds places to read**; it proves nothing.
2. Read the entry points and the wiring code they reach (server setup, client
   construction, config loading). Build the **system model** in `<out>/model.md`:
   runtime units (processes/hosts), components inside each, connections with protocol
   and direction, data at rest, external systems — each row with `path::symbol`.
3. Choose the view(s): usually one overview (containment or C4 context) and one or two
   details (sequence for the hot path, hexagonal for the core service, module
   dependency for code structure).
4. For module structure, start from `sysdiag scan <repo> --spec-out <out>/deps.spec.json`
   and edit (merge, rename, cut ubiquitous utilities).

### 1b. From an idea

1. Restate the idea as a system model: runtime units, components, connections (what
   travels, which direction), data at rest, externals. Ask only for what changes the
   picture (e.g. "does the agent run on the same host as the broker?").
2. Mark everything `assumed: true`; components still to be built use role `planned`
   (dashed). If the idea is a change to an existing system, use `architecture-delta`.

### 2. Pick a template

Read `references/templates.md`, pick the template whose question matches, then
`sysdiag new <template> <out>/<name>.spec.json` and rewrite it. State the plan in one
line before building: template, the question, what you are leaving out.

### 3. Write the spec

`references/spec-format.md` has every key. Choose roles by what a thing **is**
(`references/style.md`): `zone` host, `service` server process (hatched), `client`
caller, `compute` engine/worker, `control` auth/pool/scheduler, `catalog` metadata,
`store`/`data` data at rest, `external` someone else's system, `brand` a product shown as
a wordmark. Put `ev` on every node and edge in codebase mode.

### 4. Build, render, look, fix

```bash
sysdiag build <out>/<name>.spec.json -o <out>/<name>.excalidraw [--require-evidence]
render <out>/<name>.excalidraw --svg
```

Fix every `WARN` (overlap, edge through a box, label collision, shared run, budget), then
**Read the PNG** and run the review loop in `references/layout-rules.md`: does it answer
the question; is the eye path left→right (or top→down); any crossing that a reorder
removes; labels next to the wire they name; nothing clipped. Usually 2–4 rounds. Change
the spec, never the `.excalidraw`, until the picture is right — hand edits in Excalidraw
are lost on rebuild (tell the user this if they plan to edit by hand: edit last).

### 5. Deliver

Default location `docs/diagrams/` in the target repo (or where the user says):
`<name>.spec.json`, `<name>.excalidraw`, `<name>.png`, `<name>.svg`, and
`<name>.evidence.md` in codebase mode. Report: the question it answers, what was left
out, every `assumed` element, and how to edit (excalidraw.com → Open, or the VS Code
Excalidraw extension). If a lint warning remains on purpose, say which and why.

## Updating a diagram after code changes

Re-run the scan, diff against `model.md`, edit the spec (never regenerate from scratch —
the layout decisions in it are work), rebuild, re-render, re-check the evidence rows
whose files changed (`git diff --name-only <old>..HEAD` against `evidence.md`).

## Do not

- Hand-write or hand-patch `.excalidraw` JSON — change the spec and rebuild.
- Draw boxes for libraries, utilities or config files unless they are the point.
- Label edges "uses", "calls", "talks to".
- Use more than two `focus` nodes, or colour to decorate — roles are semantic.
- Put a whole codebase in one picture.
- Publish a codebase diagram with `**missing**` evidence rows without saying so.
