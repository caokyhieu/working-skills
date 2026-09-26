# Content and evidence

## Product connection

The deck must establish both product value and technical feasibility. Use these questions to connect individual slides to the investment argument:

- **Why does this matter to the product?** What product metric, user problem, operating cost, capability, or strategic need does it address?
- **Why is it technically feasible here?** Which existing systems, interfaces, datasets, runtimes, ML pipelines, databases, deployment processes, or engineering skills make this practical?

Avoid standalone academic explanation. Explain technical novelty only to the degree needed to establish why it is useful and implementable in the HQ product. Technical fit is supporting evidence for the value case, not a substitute for it.

## Value thesis before outline

For each proposed technology, write a concise argument linking the target use case, the current approach's limitation or unserved opportunity, the proposed advantage, its technical mechanism, and the expected product outcome. Explain what adoption enables and what opportunity remains without it. When the limitation is not observed internally, label it as a hypothesis instead of asserting a product defect.

Identify the strongest evidence supporting the advantage and the most consequential trade-off. Show why the proposal improves on a realistic baseline rather than merely adding another component. For multiple proposals, justify each separately before explaining their combined value; one technology's evidence does not prove another's benefit.

Put the decisive result or example visibly on the slide with source, metric, baseline, and scope. Keep fuller methodology in notes. Distinguish model-quality comparisons from index-efficiency comparisons, payload size from total system footprint, and external results from expected HQ impact. A worked example must be labeled illustrative; a quantitative model must expose its assumptions. Do not invent expected ROI or gains when evidence is absent.

Explain why the evidence warrants the requested commitment. Put the POC after this argument to resolve specific uncertainties. If the evidence does not support adoption, recommend a narrower investment or an alternative rather than manufacture enthusiasm.

Use an explicit mapping where possible:

```text
Technology capability → Product integration point → Product/engineering metric → Business or user outcome
```

Example:

```text
Group-relative policy optimization → Existing LLM training pipeline → Lower reward-model and sampling overhead → Faster iteration and reduced training cost for the chatbot product
```

## Narrative options

Select and adapt the following structure according to duration, audience, and user requirements. Do not include a slide merely because it appears in this list.

### 1. Title and Decision Thesis

- Technology name and the named HQ product
- A one-sentence value proposition
- Decision requested, if known

Example: `GRPO for Product X: reduce post-training iteration cost while improving response quality on the current training platform.`

### 2. Product Problem and Technical Root Cause

- Product pain: customer experience, performance, reliability, cost, delivery speed, or competitive gap
- Technical root cause: current system limitation that creates the product pain
- Use known product metrics; label unknown values as assumptions

### 3. Proposed Technology

- Explain the technology, algorithm, design pattern, or research finding at the appropriate technical level
- State the key mechanism and the difference from the current approach
- Include a simple algorithm or conceptual flow diagram when useful
- Include only the equations essential to decision-making; avoid proof-level mathematics unless explicitly requested

### 4. Evidence and Relevance

- Summarize 2-5 relevant papers, benchmark results, case studies, or internal experiments
- Prefer evidence matching the HQ use case: similar model size, workload, latency requirements, data regime, infrastructure, and evaluation metric
- Clearly separate observed evidence from projected HQ impact
- Cite sources in speaker notes and on a final references slide

### 5. Current-to-Proposed Integration Architecture

- Show the current product architecture or workflow
- Overlay the proposed technology at concrete integration points
- Identify data inputs/outputs, services, APIs, pipelines, stores, model lifecycle stages, and operational dependencies as relevant
- Highlight what remains unchanged, what is modified, and what is new

### 6. Product and Business Impact

- Connect technical improvements to product outcomes
- Use measurable metrics where available: accuracy, quality, latency, throughput, reliability, cost, developer productivity, time-to-market, retention, conversion, or revenue
- Provide conservative/base/optimistic ranges when estimates are uncertain
- State assumptions and sources

### 7. Technical Fit and Readiness

- Map the proposal to the current stack: infrastructure, programming languages, frameworks, data systems, ML tooling, observability, CI/CD, security, and deployment model
- Identify required changes, skill gaps, capacity needs, and dependencies
- Explicitly note incompatibilities, unknowns, and validation work

### 8. Alternatives and Trade-offs

- Compare the proposed approach against the current approach and 1-2 realistic alternatives
- Use 3-5 decision criteria, such as expected performance, engineering effort, time to value, operating cost, risk, and strategic fit
- Do not claim a winner without evidence; use a POC to resolve uncertainty where appropriate

### 9. Delivery Plan

- POC → pilot → production, adjusted for scope
- Include success metrics, timeline range, roles, effort estimate, and exit/rollback conditions
- Use T-shirt sizing (S/M/L/XL) when estimates are preliminary

### 10. Risks and Mitigations

- Technical risks: integration complexity, performance regression, reliability, data quality, model safety, operational burden, vendor dependency
- Product risks: delayed benefit, user disruption, adoption, business uncertainty
- Mitigations: staged rollout, offline evaluation, shadow mode, A/B testing, monitoring, feature flags, rollback plan

### 11. Recommendation and Decision Ask

- State the recommendation in one sentence
- Specify exactly what approval is needed: research time, POC budget, access to data, team allocation, pilot customer, or roadmap slot
- State the near-term next step and success threshold

### 12. References / Appendix

- Include 3-5 high-value sources, papers, product docs, benchmark reports, or internal evidence
- Move detailed technical material, equations, extra benchmarks, and implementation specifics to appendix slides when the main deck is executive-facing

## Duration

### Five-minute deck

Use: Title, product problem, proposed technology and integration, expected impact, recommendation/POC ask, optional one-slide appendix.

### Ten-minute deck

Use: Title, problem/root cause, technology overview, evidence, integration map, impact, fit, POC plan, decision ask, references.

When the user requests a compact five-slide proposal, a useful starting point is: (1) product opportunity and investment thesis, (2) capability gain with mechanism and evidence, (3) efficiency or second-proposal gain with evidence and trade-offs, (4) integration path showing how the benefits are realized, (5) expected value and a bounded decision ask. Adapt this to the number of proposals; do not impose five slides universally. Allocate most visible content to the value argument, with validation supporting the closing ask.

### Fifteen- to twenty-minute deck

Use the standard structure, including alternatives, trade-offs, risks, and a more detailed implementation path.

### Thirty-minute deck

Include the full standard structure plus technical appendix slides, deeper architecture, evaluation design, and detailed evidence.

## Diagram design

All diagrams must be editable or reproducible from source. Do not use decorative diagrams that do not communicate a decision-relevant relationship.

### Algorithm Concept Diagram

- Show input, core mechanism, feedback/evaluation loop if relevant, and output
- Label each component in product-relevant language
- Use mathematical notation only if it clarifies a key difference
- Compose it as a method figure or an explainer ([diagram-styles.md](diagram-styles.md)), whichever fits.
- For a technical proposal whose value depends on an algorithm, show the decision-relevant mechanism visibly. A box labeled with the algorithm name or an integration pipeline does not explain the algorithm. Show the intermediate representation and operations that produce the result, and connect them to the claimed quality or efficiency benefit.
- Distinguish offline preparation from query-time work when it explains cost or latency. Use a small worked example, similarity matrix, partition sketch, or pruning sequence where it makes the mechanism easier to understand. Label synthetic values as illustrative; preserve benchmark evidence and its scope alongside the diagram.

Example:

```text
Training prompts + candidate responses → group evaluation → relative reward computation → policy update → improved product model
```

### Integration Architecture Diagram

- Use a before/after or current/proposed overlay
- Show product components, interfaces, data flow, and deployment boundary
- Mark additions in the selected template accent color
- Include a short callout for each integration point explaining the expected technical benefit

### Value Flow Diagram

- Show: product input → technical capability → engineering metric → customer/business outcome

### Decision Matrix

- Compare current, proposed, and alternative approaches
- Limit to 3-5 criteria and avoid false precision

### Roadmap Diagram

- Show POC, pilot, production stages
- Include duration ranges, success gates, and decision points

## Evidence

- Search for recent, authoritative, and directly relevant papers, documentation, benchmarks, and case studies.
- Prefer primary sources: research papers, vendor documentation, official engineering blogs, reproducible benchmark reports, and internal materials.
- Cite claims, numerical benchmarks, and factual assertions.
- Never fabricate a benchmark, product metric, competitor adoption, paper citation, or cost estimate.
- Clearly mark any estimated impact as an estimate and list its assumptions.
- If evidence is weak or does not match HQ’s context, say so and recommend a POC rather than overstating confidence.
- Keep references concise in the main deck; place detailed citations in speaker notes and the final reference slide.

## Mapping

For each proposal, create a structured mapping before building slides:

| Field | Required content |
|---|---|
| Research problem | `research-map.md` R<n>.<x>: formulation, binding constraint, win definition (when the deck comes from a research-poc idea) |
| Ground point | From `ideas/alignment.md`: shared structure, transfer distance, bridging concept, what transfers and what changes; the rebuttal condition, stated as a risk |
| HQ product | Product name, users, and main purpose |
| Current capability | Current workflow or architecture relevant to the problem |
| Product pain | User, business, or operational limitation |
| Technical bottleneck | Root technical cause or suspected cause |
| Proposed technology | Algorithm, platform capability, system design, or research method |
| Integration point | Specific service, pipeline, model, database, API, or process affected |
| Expected engineering metric | Accuracy, latency, throughput, cost, reliability, developer time, etc. |
| Expected business outcome | User experience, retention, conversion, revenue, risk reduction, etc. |
| Validation method | Offline evaluation, load test, A/B test, shadow deployment, pilot, etc. |
| Key risk | Main technical and product risk |

Use this mapping to ensure the presentation tells a connected story rather than presenting disconnected business and technical sections.
