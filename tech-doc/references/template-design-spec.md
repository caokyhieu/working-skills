# Template: feature design spec

The house format for a release feature design spec under `docs/`. Use it as the default
outline for design specs; adjust subsection names, keep the four-part spine.

Headings below are described in English. Write the actual headings in the target
document's language, matching sibling documents in `docs/`.

## Spine

```
# <Feature> Design Specification

## 1. Background          Why this work exists
### 1.x <scenario>        One subsection per driving business scenario
## 2. Solution Overview   Deployment view + runtime view
## 3. Feature Analysis    The bulk of the document
### 3.1 Detailed Design   Design principles + end-to-end flow
### 3.2..3.n <area>       One subsection per functional area
## 4. DFX Analysis        Non-functional analysis
### 4.1 Resources and Dependencies
### 4.2 Security
### 4.3 Performance
### 4.4 Test Cases
```

Numbering is `## 1.` / `### 1.1`. Keep it — reviewers cite section numbers.

## Section rules

**1. Background** — per scenario: the product or platform involved, a capability table
(`capability | description | target date`), and one bold value line stating what the
feature enables. Screenshots belong here, not in section 3. State the business need
in the doc itself; do not point to a wiki page or ingested doc for it.

**2. Solution Overview** — two views, nothing else:
- Deployment view: one `flowchart TD` — who declares what, which operator renders it,
  where connection info and models get registered. Number the steps on edges: `(1) ...`.
- Runtime view: the request path in production.
Both stay under ~9 nodes. Use `subgraph` for layers (core service / cluster / external
supporting systems).

**3.1 Detailed Design** — open with **design principles**: a numbered list, one line
each, stating who owns what ("the product declares the StarRocks CR"). Then the detailed
design with one `sequenceDiagram` covering the end-to-end flow across services. Use
`opt` blocks for conditional branches instead of a second diagram.

**3.2..3.n functional areas** — each follows the same shape:
1. One paragraph: what changes in this component, and its precondition
   (e.g. "applies to clusters with `label=hybrid|query`").
2. A numbered requirement list — each item is one deliverable.
3. A mapping table when the work lands on existing code:
   `reference implementation | method | type | sync mode`.
3b. For any area with runtime behavior — a lifecycle/state view (a `stateDiagram-v2`
   when more than three states), a one-line threading note (which thread or pool, what
   is not thread-safe), a config table (`key | default | effect`), and a failure-mode
   list (`condition -> fallback`). Tag the section `Type: mechanism` in `OUTLINE.md`.
4. Concrete API calls: `curl` + JSON body, with `//` comments on the fields that carry a
   decision. Give the endpoint path and one line on what it does.
5. Scenario decomposition when the flow is complex — this is how a big diagram gets
   split: **Scenario 1** (startup / init), **Scenario 2** (compensation / failure),
   **Scenario 3** (multi-cluster / scale). One diagram per scenario, never one diagram
   for all three. Decision logic gets its own `graph TD` with `{...}` branch nodes.

**4. DFX Analysis** — no prose, four fixed subsections:
- Resources and dependencies: table `service | memory | CPU`, one row per service, each
  qualified by its load assumption (`OneQueryService (10 concurrent, single node)`).
- Security: bullets — file permissions, credential handling, transport.
- Performance: bullets, each a number or an explicit "baseline unchanged" statement.
- Test cases: link to where the test cases live (test directory or test-management
  system). Do not inline them. This is the one outward link the spec keeps — it points
  at the tests, not at another document.

## Conventions

- Component names appear as `<local name>/<ServiceName>` on first use, then the short
  form. Freeze the pair in `CONTEXT.md`.
- Real values in examples — real IPs, ports, class names from the codebase. Redact
  passwords as `<redacted>`; never paste a live credential into a doc.
- Existing images are external URLs. Never invent an image link. Where a screenshot is
  expected but missing, leave `<!-- TODO(user): screenshot — <what it should show> -->`
  and ask the user for it.
