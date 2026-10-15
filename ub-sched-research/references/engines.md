# Engine ontologies: YARN, Spark, Flink

Each engine keeps **its own ontology**: its own classes, relations and scheduling levels, in its own words. The UB ontology ([ontology.md](ontology.md)) doesn't replace them. It is the shared layer they are compared on. The **crosswalk** (§5) links the two, one row per engine concept, with a fidelity label. Research questions come from the rows where the mapping is lossy or missing.

`ub_sched.py init` copies this file to `ub-sched/engines.md`, where it is kept up to date. `ub_sched.py check` reads the engine terms from the first column (in backticks) of the §1–§3 class tables. Cards list them under `engine_terms`, written as `Engine:Term` (e.g. `Spark:TaskSetManager`).

**Version discipline.** The descriptions below are the stable architecture, written from general knowledge of the projects. Before a card, design or claim relies on a specific class, config key, JIRA or FLIP, confirm it in the source of the version in use and cite `[code: repo/path@commit]` or `[doc: url, version]`. Items marked `(verify)` changed across releases, or may have. Record the versions the team targets in `ub-sched/facts.md` (§ Engines).

Fidelity labels used in the crosswalk:

| Label | Meaning |
|---|---|
| `exact` | same meaning in both ontologies |
| `degenerate` | the engine concept is the single-server special case of the UB concept (e.g. a composition whose members all sit on one MatrixServer) |
| `lossy` | the engine concept exists but cannot express part of the UB concept (paths, pools, cross-server members) |
| `none` | the engine has no concept for it; a design must add one or work around it |

## 1. YARN ontology

### Classes

| Term | Meaning in YARN | Level |
|---|---|---|
| `ResourceManager` | Cluster-wide master; hosts the Scheduler, ApplicationsManager and ResourceTrackerService | cluster |
| `Scheduler` | Pluggable allocator inside the RM (`yarn.resourcemanager.scheduler.class`): CapacityScheduler, FairScheduler | cluster |
| `Queue` | Hierarchical capacity / share unit for tenants | cluster |
| `NodeManager` | Per-host agent; reports capacity by heartbeat, launches and isolates containers (cgroups) | host |
| `SchedulerNode` | RM-side view of one NodeManager: total, allocated and unallocated Resource | cluster |
| `Resource` | Vector of resource types: memory-mb, vcores, plus custom types from resource-types.xml (GPU, FPGA, …) | — |
| `Container` | An allocation of a Resource on **one** NodeManager, with a launch context | cluster |
| `ApplicationMaster` | Per-application process that negotiates containers and runs the application's own scheduling | application |
| `ResourceRequest` | AM ask: priority, resourceName (host / rack / `*`), capability, count, relaxLocality | application → cluster |
| `SchedulingRequest` | Newer ask with allocation tags and placement constraints (Hadoop 3.1+, YARN-6592) (verify) | application → cluster |
| `PlacementConstraint` | Affinity, anti-affinity, cardinality over allocation tags within a scope (node, rack) | cluster |
| `NodeLabel` | Partition of nodes (exclusive / non-exclusive) | cluster |
| `NodeAttribute` | Key–value attribute on a node usable in constraints (verify) | cluster |
| `OpportunisticContainer` | Container that can be queued at the NM and preempted (verify) | host |
| `ResourcePlugin` | NM-side device plugin framework (GPU, FPGA, pluggable device plugins) (verify) | host |
| `MultiNodeLookupPolicy` | CapacityScheduler policy that sorts candidate nodes when scheduling across many nodes (verify) | cluster |

### Relations and levels

- `ApplicationMaster` sends `ResourceRequest` / `SchedulingRequest` → `Scheduler` grants `Container` on `SchedulerNode` ↔ `NodeManager` → AM launches its own work in the container.
- YARN is the **cluster level** only. It never sees Spark tasks or Flink operators; it sees containers of a fixed Resource vector.
- Locality is expressed by **host and rack names** in `resourceName`, with `relaxLocality` as the fallback switch.

### Node-local assumptions (where UB breaks the model)

- A `Container` lives on exactly one NodeManager; its Resource is accounted against exactly one `SchedulerNode`.
- Custom resource types are **per-node counts**; there is no cluster-level resource that is not owned by some node.
- Isolation and enforcement happen in the NM on that host (cgroups, device plugins).
- The locality hierarchy is node → rack → any; there is no notion of a path cost between nodes.

### Plugin points for a UB design

| Seam | What a UB design could do there |
|---|---|
| Scheduler class (CapacityScheduler / FairScheduler / new) | Composition-aware allocation with path cost |
| `MultiNodeLookupPolicy` | Sort candidate nodes by UB distance to other members or data |
| Resource types | Expose UB-reachable memory or NPU capacity; must solve the per-node-ownership problem |
| `PlacementConstraint` / `NodeAttribute` | Encode UB distance classes or pool membership as attributes |
| NM `ResourcePlugin` | Attach remote memory / NPU into a container at launch through the UB OS component |
| AM protocol | Unchanged is cheapest; extending `SchedulingRequest` is the next step |

## 2. Spark ontology

### Classes

| Term | Meaning in Spark | Level |
|---|---|---|
| `SparkApplication` | A driver plus its executors | application |
| `Driver` | Process that runs the DAGScheduler and TaskScheduler | application |
| `Job` | Triggered by an action; a DAG of stages | application |
| `Stage` | Set of tasks bounded by shuffle dependencies (ShuffleMapStage, ResultStage) | application |
| `DAGScheduler` | Splits jobs into stages at shuffle boundaries, submits TaskSets, computes preferred locations | application |
| `TaskSet` | The tasks of one stage attempt | task |
| `TaskSchedulerImpl` | Matches TaskSets to executor resource offers | task |
| `TaskSetManager` | Per-TaskSet scheduling with locality levels and delay scheduling | task |
| `Task` | One partition's work (ShuffleMapTask, ResultTask) | task |
| `LocalityLevel` | PROCESS_LOCAL, NODE_LOCAL, NO_PREF, RACK_LOCAL, ANY; waits set by `spark.locality.wait*` | task |
| `TaskLocation` | Preferred location of a partition: host, executor cache, HDFS cache | task |
| `Executor` | JVM process on **one** host with cores, on-heap / off-heap memory, BlockManager | application |
| `SchedulerBackend` | Bridge to the cluster manager (CoarseGrainedSchedulerBackend; YARN, Kubernetes, standalone) | application → cluster |
| `ExternalClusterManager` | Plugin interface for a cluster manager (verify) | application → cluster |
| `ExecutorAllocationManager` | Dynamic allocation: grows and shrinks executors with the backlog | application |
| `ResourceProfile` | Executor and task resource requirements, per stage (stage-level scheduling, SPARK-27495, 3.1+) (verify) | application |
| `UnifiedMemoryManager` | Splits executor memory between execution and storage | host |
| `BlockManager` | Stores cached and shuffle blocks; serves remote fetches | host |
| `ShuffleManager` | Pluggable shuffle (sort-based by default); shuffle I/O plugin API (SPARK-25299) (verify) | host |
| `ExternalShuffleService` | Serves shuffle files independently of executors (needed for dynamic allocation on YARN) | host |
| `PushBasedShuffle` | Merges shuffle blocks at remote services (SPARK-30602, YARN) (verify) | host |
| `AdaptiveQueryExecution` | Re-plans at stage boundaries from runtime statistics (partition coalescing, skew join) | application |

### Relations and levels

- Two scheduling levels **inside** a YARN container grant: the application level (DAGScheduler, executors, dynamic allocation, ResourceProfile) and the task level (TaskSetManager over executor offers).
- On YARN, Spark's AM requests executor containers; YARN chooses the node, Spark chooses which task goes to which executor.
- Locality is a **host-level ladder** with time-based waits (delay scheduling).

### Node-local assumptions

- An executor's cores, memory and cache are all on one host; a cached block is local to one executor.
- Shuffle output is written to local disk and fetched over the network; the fetch cost doesn't depend on which host holds it, only on whether it is local.
- `LocalityLevel` has no rung between NODE_LOCAL and RACK_LOCAL, so "remote, one UB hop away" has nowhere to go.
- ResourceProfile describes a per-executor vector, not a cross-host composition.

### Plugin points for a UB design

| Seam | What a UB design could do there |
|---|---|
| `ResourceProfile` | Request compositions per stage (e.g. compute here, memory from the pool) |
| `TaskLocation` / preferred locations | Add UB-distance-aware locations |
| `TaskSetManager` locality levels | Replace the fixed ladder with path-cost levels |
| `ShuffleManager` / shuffle I/O plugins | Shuffle through pooled memory over UB instead of local disk + network |
| `BlockManager` storage (OFF_HEAP) | Cache in a UB memory pool that other executors can reach |
| `ExternalClusterManager` / `SchedulerBackend` | Custom cluster manager that returns UB compositions |
| `SparkPlugin` (driver / executor plugins) | Collect UB telemetry, register remote resources (verify) |

## 3. Flink ontology

### Classes

| Term | Meaning in Flink | Level |
|---|---|---|
| `JobGraph` | Logical dataflow: JobVertices (chained operators) and edges | application |
| `JobVertex` | A chain of operators after operator chaining | application |
| `ExecutionGraph` | Parallel physical plan: ExecutionJobVertex → ExecutionVertex, IntermediateResultPartitions | application |
| `ExecutionVertex` | One parallel subtask of a JobVertex | task |
| `ResultPartitionType` | Pipelined, blocking or hybrid data exchange | application |
| `Dispatcher` | Accepts jobs and starts a JobMaster per job | cluster |
| `JobMaster` | Per-job master: scheduling, checkpoint coordination, failover | application |
| `SchedulerNG` | JobMaster scheduler: DefaultScheduler, AdaptiveScheduler (FLIP-160), AdaptiveBatchScheduler (verify) | application |
| `ResourceManager` | Flink's own RM; talks to YARN, Kubernetes or standalone; holds the SlotManager | cluster |
| `SlotManager` | Matches declared requirements to TaskManager slots (declarative, FLIP-138; fine-grained, FLIP-156) (verify) | cluster |
| `ResourceRequirements` | Declarative slot demand from JobMaster to ResourceManager (verify) | application → cluster |
| `TaskManager` | Worker JVM on **one** host; offers slots; holds network buffers and managed memory | host |
| `TaskSlot` | A slice of a TaskManager's resources; with fine-grained resource management, sized per SlotSharingGroup | host |
| `SlotSharingGroup` | Subtasks of different vertices that may share one slot; can carry a resource spec | application |
| `CoLocationGroup` | Forces subtasks onto the same slot (iterations) | application |
| `SlotSelectionStrategy` | Picks a slot for a request, using location preferences and previous allocations (verify) | task |
| `ManagedMemory` | Off-heap memory Flink manages for RocksDB, sorting, hashing | host |
| `NetworkBuffers` | Memory for the data exchange between subtasks, with credit-based flow control | host |
| `ShuffleService` | Pluggable shuffle (FLIP-31): Netty default, hybrid shuffle, remote shuffle services (verify) | host |
| `StateBackend` | HashMap (heap) or RocksDB; Flink 2.x adds disaggregated state (ForSt, FLIP-423) (verify) | host |
| `Checkpoint` | Consistent snapshot of state for recovery | application |
| `FailoverRegion` | Set of tasks restarted together after a failure | application |

### Relations and levels

- On YARN, Flink's ResourceManager asks YARN for TaskManager containers; the SlotManager hands slots to JobMasters; the JobMaster's scheduler assigns ExecutionVertices to slots.
- Streaming jobs are **long-running**: placement is made once and changes only on failover or rescaling (adaptive / reactive mode, savepoint-restart). Batch jobs schedule region by region.
- Locality is a preference (input location, previous allocation, local recovery), not a hierarchy.

### Node-local assumptions

- A slot is a slice of one TaskManager process on one host; managed memory and RocksDB state are local to it.
- Network buffers are per TaskManager; exchange between subtasks on different TMs goes over TCP (Netty).
- Local recovery assumes state copies on the local disk of the same host.
- Slot sizing is a per-TM vector; nothing lets a slot hold memory that sits on another host.

### Plugin points for a UB design

| Seam | What a UB design could do there |
|---|---|
| `SlotManager` / `ResourceRequirements` | Declare and satisfy compositions instead of per-TM slots |
| `SlotSharingGroup` resource spec | Attach pooled memory or NPU to a group |
| `SlotSelectionStrategy` | Score slots by UB path cost to upstream / downstream subtasks and state |
| `ShuffleService` | Exchange data over UB memory instead of Netty TCP |
| `StateBackend` / disaggregated state | Put keyed state in a UB memory pool; faster rescaling and recovery |
| `AdaptiveScheduler` | Recompose resources for a running job instead of restarting from a savepoint |

## 4. Two-level scheduling on YARN

```text
YARN ResourceManager (cluster level)        grants Containers on NodeManagers
   └─ delegatesTo
      Spark driver / Flink ResourceManager+JobMaster (application level)
         └─ TaskSetManager / SlotSelectionStrategy (task level)
```

A UB mechanism has to say at which level it decides, and what the other levels learn about it:

| Design pattern | Changes | Engines see | Typical cost |
|---|---|---|---|
| **A. Cluster only** | YARN scheduler / NM plugin composes resources; the container "looks local" to the engine | nothing new | engines cannot exploit topology; path cost hidden from task placement |
| **B. Engine only** | shuffle, state, cache or locality inside Spark / Flink use UB; YARN unchanged | UB paths inside their plugins | YARN still packs by node; fragmentation remains |
| **C. Co-designed** | engines declare composition-aware demand (ResourceProfile, ResourceRequirements) and YARN returns compositions with path costs | a new demand / grant vocabulary | protocol changes on both sides; highest payoff |

Every design card names its pattern and lists the engine interfaces it touches. Prefer plugin points over forks; when a fork is unavoidable, say which class and why.

## 5. Crosswalk to the UB ontology

Starting rows; keep them in the workspace copy and add rows as cards reveal them.

| Engine concept | UB concept | Fidelity | What is lost / note |
|---|---|---|---|
| `YARN:NodeManager` | `MatrixServer` (+ its devices) | degenerate | NM sees only its own host; pooled resources have no owner NM |
| `YARN:Container` | `ResourceComposition` | degenerate | members restricted to one server; no path costs |
| `YARN:Resource` | `ResourceDemand` / `Resource` | lossy | per-node vector; no pool-level or remote resource |
| `YARN:ResourceRequest` | `ResourceDemand` + `Constraint` | lossy | locality only by host / rack name |
| `YARN:PlacementConstraint` | `Constraint` | lossy | scopes are node / rack; no UB-distance scope |
| `YARN:Scheduler` | `Scheduler` @ `cluster` | exact | |
| `YARN:Queue` | `SchedulingPolicy` (fairness / capacity) | exact | |
| `Spark:Executor` | `ResourceComposition` (single-server) + `ComputeResource` + `MemoryResource` | degenerate | memory, cache and cores tied to one host |
| `Spark:Stage` | `Stage` | exact | |
| `Spark:Task` | `Task` | exact | |
| `Spark:ResourceProfile` | `ResourceDemand` | lossy | per-executor vector; cannot ask for pooled memory or co-location distance |
| `Spark:LocalityLevel` | `UBPath` cost class | lossy | fixed host ladder; no hop or bandwidth notion |
| `Spark:TaskLocation` | `DataPartition storedOn` + `canAccess` | lossy | host-based only |
| `Spark:ShuffleManager` | `CommunicationDemand` realised over `UBPath` | none → plugin | shuffle cost not modelled in placement |
| `Spark:BlockManager` | `MemoryResource` + `DataPartition` | degenerate | cache private to one executor |
| `Flink:TaskManager` | `MatrixServer`-bound `ResourceComposition` | degenerate | |
| `Flink:TaskSlot` | `ResourceComposition` (single-server) | degenerate | |
| `Flink:SlotSharingGroup` | `Constraint` (co-location) + `ResourceDemand` | lossy | co-location means same slot, not "within N hops" |
| `Flink:ExecutionVertex` | `Task` (of an `Operator`) | exact | |
| `Flink:JobVertex` | `Operator` | exact | |
| `Flink:ResultPartitionType` | `CommunicationDemand` pattern | exact | |
| `Flink:StateBackend` | `MemoryResource` / `Storage` holding `DataPartition` (state) | lossy | local by default; disaggregated state is the bridge |
| `Flink:SlotManager` | `Scheduler` @ `cluster` (inside Flink) | exact | sits under YARN when deployed on YARN |
| `Flink:FailoverRegion` | reliability dimension | lossy | failure domain is the TM, not the composition |
| — | `UBPath`, `GlobalAddressSpace`, `MemoryPool` | none | no engine has these; every UB design introduces them somewhere |

## 6. Adding another engine

For Kubernetes, Ray, Presto/Trino or another engine, add a section with the same four parts (classes with levels, relations and levels, node-local assumptions, plugin points) and add its rows to §5. Use the engine's own names; don't rename its concepts into UB terms.
