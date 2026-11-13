# Design sketch: <name>

> A scheduler design for one or more questions, written in the UB ontology and landed in the engines. Not a proposal yet: idea-extension turns a confirmed sketch into one.

**Questions:** Q<n>  **Pattern:** A / B / C  **Engines and versions:**   **Date:**

## 1. Decision

What is decided, at which level, how often, with what inputs:

```text
SchedulingDecision
├── Workload → <Stage / Operator / Task>
├── Compute → <ComputeResource> @ <MatrixServer or pool>
├── Accelerator → <AcceleratorResource> @ …
├── Memory → <MemoryResource> @ …
└── Communication → UBPath(<members>)
```

## 2. Model

- **Inputs** (and where the scheduler gets them: Fabric Manager, NM heartbeat, engine metrics):
- **Objective** and the cost vector dimensions it trades off (ontology.md §5):
- **Algorithm** (and the closest prior algorithm it adapts, with card id):
- **Assumptions** (each checked against facts.md):

## 3. Landing in the engines [O7]

| Level | Engine component | Today | Change (config / plugin / protocol / fork) | Compatible with unchanged apps? |
|---|---|---|---|---|
| cluster | `YARN:…` | | | |
| application | `Spark:…` / `Flink:…` | | | |
| task | `Spark:…` / `Flink:…` | | | |

What each level learns from the others, and what stays hidden:

## 4. Engine fidelity check

- Stage / slot / container semantics preserved? Where they bend:
- Failure and recovery (Spark recomputation, Flink checkpoints, YARN container loss) with cross-server compositions:
- Fairness and queues (YARN Queue semantics) preserved?
- Dynamic allocation / adaptive scheduling interplay:

## 5. Evaluation plan

- Hypothesis (from questions.md):
- Tuned baselines:
- Workloads:
- Hardware or emulation, and what does not transfer:
- Metrics per cost-vector dimension:
