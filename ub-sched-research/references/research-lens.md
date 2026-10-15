# Research lens

Where to look, what to ask, and how to judge a claim for UB scheduling research. Everything here is a **seed**: confirm anchors and questions with the user before relying on them, and verify every citation before it goes into a card (title, venue, year, and that it says what the card claims).

## 1. Canonical formulation (draft for research-map.md)

> Given a DAG or dataflow of tasks and operators with multi-resource demands and communication demands, and a SuperPoD whose resources are split into server-local and UB-pooled resources and connected by a fabric with known topology and path costs, choose resource compositions and placements for the tasks. Optimise job completion time or throughput, plus utilisation, subject to capacity, fairness between queues, reliability and the YARN / Spark / Flink scheduling protocols, in a regime of many concurrent jobs, second-to-hour task durations and long-running streaming jobs.

**Binding constraint to check with the user:** is the limit today fragmentation (stranded memory or NPUs on some servers), shuffle or state I/O, or the engines' inability to express cross-server resources? The answer decides which questions in §4 come first.

## 2. Bridging fields [TM-4]

Fields that solve the same structure under other names:

| Field / term | Shared structure | What to borrow |
|---|---|---|
| Virtual network embedding (VNE), service function chain placement | map a demand graph (nodes + links) onto a substrate graph with node and link capacities | formulations and heuristics for placing compositions *with* their paths |
| Topology-aware process mapping (HPC: MPI rank mapping, graph partitioning) | place communicating processes to minimise traffic × distance | cost models, partitioners |
| Multi-resource / vector bin packing, DRF-style fairness | pack multi-dimensional demands, share fairly across resource types | packing heuristics; treating fabric links as one more resource |
| Memory disaggregation and remote memory (RDMA, far memory) | compute on one host, memory on another, behind an access-cost model | cost models, prefetch and eviction, failure handling |
| CXL memory pooling and tiering | pooled memory at a latency penalty, capacity decided per host or per VM | tier placement, page migration policies |
| NUMA-aware scheduling | distance inside a host; intra-server locality | distance matrices, first-touch, migration |
| Composable / rack-scale infrastructure | resources composed per workload from pools | composition APIs, lifecycles |
| Network-aware data-parallel scheduling | place tasks and data so that traffic stays on fast links | joint data + task placement |
| Stream operator placement and elastic scaling | long-running operator graph placement, rescaling under load | migration cost, state movement |
| Gang / co-scheduling | allocate groups of resources atomically | deadlock avoidance, all-or-nothing grants |
| Learning-based cluster scheduling | learn a placement policy from traces | state encoding of topology, sim-to-real gap |

## 3. Candidate anchors

Grouped by role, to confirm with the user and verify before use. Each should become a card.

**Engine designs (baselines):** YARN (Vavilapalli et al., SoCC 2013); Mesos (Hindman et al., NSDI 2011); Spark RDDs (Zaharia et al., NSDI 2012); Apache Flink (Carbone et al., IEEE Data Eng. Bull. 2015); Borg (Verma et al., EuroSys 2015). Plus the engine docs and code at the target versions, as `type: code` cards.

**Scheduling algorithms on node-local clusters:** Delay scheduling (Zaharia et al., EuroSys 2010); DRF (Ghodsi et al., NSDI 2011); Tetris multi-resource packing (Grandl et al., SIGCOMM 2014); Firmament flow-based scheduling (Gog et al., OSDI 2016); Medea for long-running containers with placement constraints (Garefalakis et al., EuroSys 2018); Decima learned DAG scheduling (Mao et al., SIGCOMM 2019); DS2 streaming autoscaling (Kalavri et al., OSDI 2018).

**Disaggregation and pooling:** LegoOS (Shan et al., OSDI 2018); Infiniswap (Gu et al., NSDI 2017); AIFM (Ruan et al., OSDI 2020); Pond CXL memory pooling (Li et al., ASPLOS 2023); TPP tiered memory (Maruf et al., ASPLOS 2023).

**UB / SuperPoD itself:** see `facts.md` for the public sources (openEuler UB Service Core white paper, UB OS Component docs, CloudMatrix384 and UB-Mesh papers). These define the hardware side and are the only sources for hardware numbers.

## 4. Seed research questions

Each gets a falsifiable hypothesis in `questions.md` [TM-6]. The *crosswalk row* is the lossy or missing mapping in [engines.md §5](engines.md) that the question is about.

| Id | Question | Crosswalk row | Level / pattern |
|---|---|---|---|
| Q1 | When does a cross-server composition beat the best single-server placement? Where is the break-even between UB path cost and the queueing / fragmentation it removes? | `YARN:Container` degenerate | cluster / A or C |
| Q2 | What should the allocation unit in YARN be on UB (container-as-composition, pool-level resource types, or something else) and what protocol change does the AM–RM interface need? | `YARN:Resource` lossy | cluster / C |
| Q3 | Should Spark's locality ladder be replaced by path-cost levels, and does delay scheduling still pay when "remote" is one UB hop? | `Spark:LocalityLevel` lossy | task / B |
| Q4 | How much does shuffle (Spark) or data exchange (Flink) through a UB memory pool change the best placement compared with local disk + TCP? | `Spark:ShuffleManager` none | application / B |
| Q5 | Should fabric links be scheduled as a resource (a DRF dimension) to avoid contention between compositions? | contention dimension; no engine row | cluster / C |
| Q6 | What is the reliability cost of spanning servers, and how should checkpointing (Flink) or recomputation (Spark) change with it? | `Flink:FailoverRegion` lossy | application / C |
| Q7 | For a long-running Flink job, is recomposition (moving memory or state over UB) cheaper than rescale-by-savepoint? | `Flink:StateBackend` lossy | application / B or C |
| Q8 | Can Spark ResourceProfile and Flink ResourceRequirements carry composition-aware demand without breaking existing applications? | `Spark:ResourceProfile`, `Flink:SlotManager` | application → cluster / C |

## 5. How to judge a claim

- **Baselines:** a UB scheduler is compared with a *tuned* node-local baseline on the same hardware (e.g. CapacityScheduler with sensible locality waits and container sizes), not with a strawman.
- **Workloads:** batch (TPC-DS, HiBench) and streaming (Nexmark) at least; a production-like trace when one exists. Report which ones exercise shuffle, state, or memory pressure.
- **Hardware honesty:** results on a simulator or emulated remote memory are labelled so; transfer to real UB hardware is a separate claim.
- **Cost vector:** every result reports the §5 dimensions of ontology.md that the design affects, including reliability and fragmentation, not only job time.
- **Engine fidelity:** a result obtained by bypassing YARN, Spark or Flink protocols says so, and says what the engine would need to change to reproduce it.
