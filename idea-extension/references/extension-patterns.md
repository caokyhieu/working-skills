# Extension patterns

Use these as prompts, not a checklist. Every direction must still have a mechanism that explains why it helps.

| Pattern | Question | Example shape |
|---|---|---|
| **Break an assumption** | What happens where an assumption fails (skew, drift, updates, heavy tails, long context, multi-tenant)? | Static-data method → dynamic/updatable variant |
| **Fix a weak spot** | Which cost or failure mode did the authors avoid measuring? | Add a mechanism that bounds worst-case latency or memory |
| **Change the constraint** | What if the binding constraint is latency, memory, cost, privacy or edge hardware instead of accuracy? | Accuracy-optimal → Pareto-optimal under a budget |
| **Transfer across fields** | Does an ML technique solve a DB/systems problem, or the reverse? | Learned components in query processing; DB indexing ideas for retrieval/KV cache |
| **Combine two papers** | Do two recent insights complement each other, one's weakness being the other's strength? | Method A's representation + method B's search procedure |
| **Make it adaptive** | Replace a fixed heuristic or hyperparameter with something learned or workload-aware | Fixed threshold → per-query/per-partition policy |
| **Exploit structure the company has** | Does our data have structure (hierarchy, temporal, graph, schema) the generic method ignores? | Schema-aware or metadata-conditioned variant |
| **Theory → practice** | Is there a guarantee that can be made cheap, or a heuristic that can be given a guarantee? | Approximate method with error bounds |
| **Scale the regime** | Does it hold at 10–100× data, model size, or query rate? What breaks first? | Distributed/streaming variant |

## Filter out

- Pure hyperparameter changes or dataset swaps
- "Apply LLM to X" without a mechanism and a baseline that could win
- Directions that can't be evaluated on the original benchmark or a justified variant of it
- Directions whose value depends on company data we cannot access for the POC
