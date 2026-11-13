# UB scheduler ontology (seed, v0.1)

The shared vocabulary for research on scheduling YARN, Spark and Flink workloads on UnifiedBus (UB) SuperPoDs built from Matrix Servers. Every card, question and hypothesis in the workspace is written in these terms, so that a YARN paper, a memory-disaggregation paper and a Flink design doc can be compared on the same axes.

`ub_sched.py init` copies this file to `ub-sched/ontology.md`. The workspace copy is the living version: the user confirms it, and changes go through §7 with a change-log line. `ub_sched.py check` reads the class and relation names from the tables below (first column, in backticks), so keep that format when adding terms.

## 1. The central idea

UB weakens the server boundary but does not make physical topology irrelevant. Keep three things apart:

| Concept | Relation | Question it answers |
|---|---|---|
| Physical placement | `Resource physicallyLocatedOn MatrixServer` | Where does the hardware sit? Which failure domain, which links? |
| Logical ownership | `Resource allocatedTo Task` (reified as `Allocation`) | Who holds the resource right now, exclusively or shared? |
| Accessibility | `Task canAccess Resource via UBPath` | Can the task use it, and at what latency, bandwidth and contention cost? |

`MatrixServer` is the **physical and topological unit**. `Resource` and `ResourceComposition` are the **logical scheduling units**. Classic YARN / Spark / Flink scheduling is the degenerate case where every member of a composition sits on one server and `canAccess` is `local`.

## 2. Classes

### L1 Physical topology

| Class | Definition | Key attributes |
|---|---|---|
| `SuperPoD` | A set of Matrix Servers joined by one UB fabric into a single computing system | size, fabric, failure domains |
| `MatrixServer` | A physical server in a SuperPoD; the unit of physical placement, power and failure, not of allocation | devices, NUMA layout, UB ports |
| `NUMADomain` | A locality region inside a server (socket, die, memory controller) | devices, distance matrix |
| `Device` | Any physical processing or storage part; superclass of the rows below | type, capacity, backing server |
| `CPU` | General-purpose processor | cores, frequency, architecture |
| `NPU` | Neural processing unit (e.g. Ascend) | compute, HBM, UB ports |
| `GPU` | Graphics processor used as an accelerator | compute, HBM |
| `DPU` | Data processing unit offloading I/O, network or storage work | offload functions |
| `Memory` | Physical memory (DRAM, HBM) attached to a server or device | capacity, bandwidth, tier |
| `Storage` | Persistent storage device (SSD, NVMe, memory-semantic storage) | capacity, bandwidth, IOPS |
| `Switch` | A UB switching element between links | radix, ports |
| `Link` | A physical connection between two ports | bandwidth, latency, error rate |

### L2 UB fabric

| Class | Definition | Key attributes |
|---|---|---|
| `UnifiedBusFabric` | The UB interconnect of a SuperPoD: links, switches, routing, address space | topology, routing policy |
| `Topology` | The graph of servers, devices, switches and links (e.g. full mesh, nD-FullMesh, Clos) | shape, diameter, bisection bandwidth |
| `UBPath` | A route from a consumer to a resource over the fabric; `local` when no fabric hop is used | hop count, links traversed, bandwidth, latency, shared links |
| `FabricManager` | The control-plane component that configures the interconnect and enforces its SLAs | SLA targets, reconfiguration time |
| `GlobalAddressSpace` | The unified memory address space that lets a device address memory on another server | granularity, coherence model |
| `ResourcePool` | A set of same-kind resources that can be allocated independently of the server they sit on | kind, capacity, members |
| `ComputePool` | Pool of CPU or general compute | |
| `MemoryPool` | Pool of memory reachable over UB | tiering, access latency |
| `AcceleratorPool` | Pool of NPUs / GPUs | |
| `DPUPool` | Pool of DPUs | |
| `IOPool` | Pool of NICs, storage or other I/O | |

### L3 Logical resource

| Class | Definition | Key attributes |
|---|---|---|
| `Resource` | A schedulable quantity backed by one or more devices | kind, amount, backing devices, sharable |
| `ComputeResource` | Cores or compute slices | cores, share |
| `MemoryResource` | A memory region, local or pooled | size, tier, access path |
| `AcceleratorResource` | An NPU/GPU or slice of one | units, HBM |
| `IOResource` | Network, storage or DPU capacity | bandwidth, IOPS |
| `ResourceComposition` | A set of resources, possibly on different servers, bound together to serve one demand | members, paths between members, cost vector |
| `Allocation` | The reified `allocatedTo` relation: who holds what, from when, exclusive or shared | holder, resource, start, end, mode |

### L4 Workload and scheduler

| Class | Definition | Key attributes |
|---|---|---|
| `Application` | A submitted program (YARN application, Spark app, Flink job cluster) | owner, queue, priority |
| `Job` | A unit of work within an application (Spark job, Flink job) | DAG |
| `Stage` | A set of tasks that run the same code over different partitions (Spark stage) | parallelism, shuffle boundaries |
| `Operator` | A long-running streaming operator or chain (Flink) | parallelism, state size, throughput |
| `Task` | The smallest scheduled unit of execution | demand, duration, state |
| `DataPartition` | A block, split, shuffle partition or state shard a task reads or writes | size, location |
| `CommunicationDemand` | Traffic between tasks or operators (shuffle, exchange, all-to-all) | volume, pattern, burstiness |
| `ResourceDemand` | What a task, stage or operator asks for, per resource kind | vector, elasticity |
| `Constraint` | A hard or soft rule on placement (affinity, anti-affinity, locality, SLA, isolation) | hard/soft, scope |
| `Placement` | An assignment of tasks to a resource composition | tasks, composition |
| `SchedulingDecision` | One decision by a scheduler: placements plus the evaluated cost vector | placements, cost vector, time |
| `SchedulingPolicy` | The rule a scheduler applies (fair, capacity, priority, cost-based) | objective, fairness notion |
| `Scheduler` | The component that makes decisions (YARN RM scheduler, Spark TaskScheduler, Flink SlotManager, a new UB scheduler) | level, scope, frequency |
| `SchedulingLevel` | Where in the stack a scheduler decides: `cluster` (YARN RM: containers to apps), `application` (Spark driver, Flink JobMaster: executors / slots to stages or operators), `task` (Spark TaskSetManager, Flink slot selection: tasks to slots) | inputs visible, decision frequency |
| `EngineComponent` | A named class, interface, protocol or config of YARN, Spark or Flink that a mechanism lives in or plugs into (see engines.md) | engine, version, path, plugin point? |

### L5 Research

| Class | Definition | Key attributes |
|---|---|---|
| `Source` | A paper, repository, doc or blog post mapped onto this ontology | evidence level, version |
| `Algorithm` | A scheduling or placement method | complexity, inputs, decision frequency |
| `Assumption` | A condition an algorithm relies on (e.g. node-local memory, uniform network) | holds under UB? |
| `Objective` | What is optimised (makespan, throughput, p99 latency, utilisation, fairness, energy) | direction, weight |
| `Hypothesis` | A falsifiable claim with a threshold | metric, threshold, conditions |
| `Experiment` | A run that tests a hypothesis | setup, workload, hardware |
| `Benchmark` | A workload or trace used in experiments (TPC-DS, HiBench, Nexmark, production traces) | scale, pattern |
| `Baseline` | What an algorithm is compared against | tuned? version |
| `Metric` | A measured quantity | unit, aggregation |
| `Result` | A reported or measured outcome | value, variance, location |
| `Limitation` | A stated or found weakness | stated-by-authors / found |

## 3. Relations

| Relation | Domain → Range | Notes |
|---|---|---|
| `contains` | SuperPoD → MatrixServer; MatrixServer → NUMADomain / Device; NUMADomain → Device | physical containment only |
| `attachedTo` | MatrixServer / Device → UnifiedBusFabric | |
| `connects` | Link → (Device / Switch, Device / Switch) | |
| `traverses` | UBPath → Link / Switch | lets two paths be checked for shared links |
| `manages` | FabricManager → UnifiedBusFabric | |
| `backedBy` | Resource → Device | a pooled resource may be backed by several devices |
| `physicallyLocatedOn` | Resource / Device → MatrixServer | **placement** — see §1 |
| `memberOf` | Resource → ResourcePool | |
| `composes` | ResourceComposition → Resource | |
| `allocatedTo` | Resource → Task / Operator / Application | **ownership** — reified as `Allocation` |
| `canAccess` | Task / ComputeResource → Resource | **accessibility** — always qualified by `via` |
| `via` | canAccess → UBPath | `local` is a UBPath with zero fabric hops |
| `partOf` | Task → Stage → Job → Application; Task → Operator | |
| `hasDemand` | Task / Stage / Operator → ResourceDemand | |
| `subjectTo` | Task / Stage / Operator → Constraint | |
| `satisfiedBy` | ResourceDemand → ResourceComposition | |
| `executesOn` | Task → ComputeResource | |
| `uses` | Task → MemoryResource / AcceleratorResource / IOResource | |
| `reads` | Task → DataPartition | |
| `writes` | Task → DataPartition | |
| `storedOn` | DataPartition → MemoryResource / Storage | |
| `communicatesWith` | Task / Operator → Task / Operator | carries a CommunicationDemand |
| `decides` | SchedulingDecision → Placement | |
| `assigns` | Placement → (Task, ResourceComposition) | |
| `madeBy` | SchedulingDecision → Scheduler | |
| `applies` | Scheduler → SchedulingPolicy | |
| `implements` | Scheduler → Algorithm | |
| `operatesAt` | Scheduler → SchedulingLevel | |
| `delegatesTo` | Scheduler → Scheduler | YARN RM grants containers, the Spark driver / Flink JobMaster places work inside them |
| `realisedBy` | Scheduler / Algorithm / Constraint / ResourceDemand → EngineComponent | ties an idea to the engine code that carries it |
| `mapsTo` | EngineComponent → ontology class | e.g. YARN `Container` mapsTo `ResourceComposition` (single-server) |
| `assumes` | Algorithm → Assumption | |
| `optimises` | Algorithm → Objective | |
| `evaluatedIn` | Algorithm → Experiment | |
| `tests` | Experiment → Hypothesis | |
| `runs` | Experiment → Benchmark | |
| `comparedAgainst` | Experiment → Baseline | |
| `measures` | Experiment → Metric | |
| `reports` | Experiment / Source → Result | |
| `supports` | Result → Hypothesis | |
| `refutes` | Result → Hypothesis | |
| `hasLimitation` | Algorithm / Experiment → Limitation | |

## 4. Invariants

- **O1 — three relations stay separate.** `physicallyLocatedOn`, `allocatedTo` and `canAccess` are never merged. A source that says "the task runs on node N" is making up to three claims; the card records which ones it actually makes.
- **O2 — MatrixServer is not the allocation unit.** Allocation is by `Resource` or `ResourceComposition`. A YARN container, Spark executor or Flink slot is a composition whose members are all `physicallyLocatedOn` one server.
- **O3 — access has a cost.** Every `canAccess` names its `UBPath` (or `local`) and that path's bandwidth, latency and shared links, or marks them `UNKNOWN`.
- **O4 — topology still matters.** A model that treats the fabric as uniform (every remote access costs the same) states that as an `Assumption`; it is not the default.
- **O5 — decisions are costed on every dimension.** A `SchedulingDecision` is evaluated on the §5 dimensions; each one is `measured`, `modelled` or `UNKNOWN`, never silently dropped.
- **O6 — hardware numbers come from the facts register.** Bandwidth, latency, pool sizes and SLAs cite `facts.md`; never from memory.
- **O7 — every mechanism lands in an engine.** A scheduler, algorithm, constraint or demand proposed for this research names its `SchedulingLevel` and the `EngineComponent`s that realise it in YARN, Spark and/or Flink, following [engines.md](engines.md). A mechanism with no landing point is a thought experiment and is labelled so.

## 5. Evaluation dimensions of a SchedulingDecision

| Dimension | What it captures | Typical metric |
|---|---|---|
| latency | cost of each `canAccess` path and of task communication | ns per access, p99 task time |
| bandwidth | throughput available on the paths used | GB/s per path, bisection share |
| locality | NUMA, server, pod distance between composition members and data | hop count, locality level |
| contention | links, pools or devices shared with other compositions | link utilisation, interference slowdown |
| capacity | whether demand fits | headroom per resource kind |
| reliability | failure domains spanned; a composition over three servers fails if any fails | servers spanned, expected loss per failure |
| energy | power drawn by devices and fabric | J per job |
| fragmentation | stranded capacity left by the decision | stranded cores / GB / NPUs |
| data locality | distance from tasks to their `DataPartition`s | bytes moved over UB |

## 6. Locality models (for classifying sources)

Each card sets `locality_model` to the strongest model the source's algorithm reasons with:

| Value | The algorithm assumes | Examples of where it shows up |
|---|---|---|
| `none` | resources are interchangeable; location is ignored | FIFO, simple fair share |
| `node-local` | resources are used on the host that holds them; anything else is a network copy | YARN containers, Spark executors, Flink slots |
| `hierarchical` | fixed levels (process / node / rack / any) with a wait or penalty per level | Spark delay scheduling, YARN rack awareness |
| `numa-aware` | distance inside a host matters | NUMA-aware placement |
| `network-aware` | link bandwidth or topology enters the cost | network-aware task placement, topology-aware HPC mapping |
| `disaggregated` | some resources (usually memory) are remote, behind a cost model | remote-memory and CXL-pooling systems |
| `composable` | the unit of allocation is a cross-server composition with a path-cost model | the target model for UB |

## 7. Changing the ontology

Propose the change with the reason (the card or question that needed it), show the diff, and apply it only after the user confirms. Add the term to the right table so `ub_sched.py check` picks it up, record it in the change log, then run `check` and list the cards that should be revisited. Rename instead of duplicating; retire a term with `[retired YYYY-MM-DD]` in its definition rather than deleting it.

## Change log

- v0.1 — seed from the user's five-layer ontology (physical topology, UB fabric, logical resource, workload and scheduler, research), plus `NUMADomain`, `Switch`, `GlobalAddressSpace`, `Operator`, `DataPartition`, `CommunicationDemand`, `Allocation` and the reliability dimension.
