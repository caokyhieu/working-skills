---
source_id: <author-or-org><year>-<short-title>
title: 
type: paper            # paper | oss | code | doc | blog
evidence: peer-reviewed # peer-reviewed | working-code | self-reported | claim-only
version: 
engines: []            # YARN, Spark, Flink, or others added to engines.md; [] if engine-agnostic
engine_terms: []       # Engine:Term from engines.md, e.g. Spark:TaskSetManager
level: []              # cluster | application | task
pattern: n/a           # A (cluster only) | B (engine only) | C (co-designed) | n/a
layers: []             # L1 … L5 the source says something about
concepts: []           # UB ontology classes the source uses (ontology.md §2)
relations: []          # UB ontology relations the source uses (ontology.md §3)
locality_model: none   # none | node-local | hierarchical | numa-aware | network-aware | disaggregated | composable
separates: no          # does it keep placement / allocation / access apart? yes | partial | no
ub_transfer: unknown   # holds | partial | breaks | unknown
visibility: public     # public | internal (uses internal facts; never shared outside the team)
digest: 
---

# <title>

> One line: what the source does, in ontology terms.

## 1. Mapping to the UB ontology

| Source's term | Ontology class or relation | Engine term (if any) | Fidelity | Evidence |
|---|---|---|---|---|
| | | | exact / degenerate / lossy / none | [src §x] |

## 2. The three relations [O1]

- **Placement** (`physicallyLocatedOn`): what the source assumes about where resources sit.
- **Allocation** (`allocatedTo`): the allocation unit and whether it is exclusive or shared.
- **Access** (`canAccess via UBPath`): how remote access is modelled and costed, or "not modelled".
- **Separates:** yes / partial / no, with the sentence or code that shows it.

## 3. Engine landing [O7]

- **Engines and versions:** 
- **Scheduling level:** cluster / application / task
- **Pattern:** A / B / C / n/a, and why
- **Engine components touched:** `Engine:Term` → what changes (config, plugin, fork) `[code: path@commit]`
- **Protocol changes:** AM–RM, driver–executor, JobMaster–ResourceManager, or none
- **Faithful to the engine?** Does the mechanism keep the engine's semantics (stages, slots, locality, failover)? Where it bends them, say how.

## 4. Assumptions and UB transfer

| Assumption | Stated or found | Holds under UB? | Why (cite facts.md) |
|---|---|---|---|
| | | holds / partial / breaks / unknown | |

**Transfer verdict:** holds / partial / breaks / unknown, in one paragraph. Name what still matters with UB (topology, contention, failure domains) as well as what stops mattering.

## 5. Scheduling decision and cost vector [O5]

Describe one decision the algorithm makes, in ontology terms (Workload → ResourceComposition → UBPaths), and mark each dimension `measured`, `modelled` or `UNKNOWN`:

| latency | bandwidth | locality | contention | capacity | reliability | energy | fragmentation | data locality |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |

## 6. Evidence

- **Objective(s):** 
- **Benchmarks / workloads:** 
- **Baselines** (tuned?): 
- **Hardware** (real UB / other interconnect / simulated): 
- **Key results** (copied exactly with location): 

## 7. Seams (for `type: code` cards)

| Engine component | File / class @ commit | Role in scheduling | Node-local assumption in the code | Could carry a UB mechanism? |
|---|---|---|---|---|

## 8. Leads

- Questions touched (Q-ids in questions.md) and crosswalk rows it informs:
- New ontology terms needed (propose; do not add without the user):
- 1–3 extension leads, each tied to an assumption that breaks under UB:
