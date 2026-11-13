# Facts register

> The only place hardware and engine-version facts come from [O6]. One row per fact, with its source and status. `internal` facts come from the user or company documents: they never go into search queries, public cards or anything shared outside the team.

**Last updated:** YYYY-MM-DD

## UB / SuperPoD / Matrix Server

| Id | Fact | Value | Source | Access date | Status | Visibility |
|---|---|---|---|---|---|---|
| F1 | openEuler UB Service Core provides cluster-level services for UB SuperPoDs (engine, memory, communication, I/O, virtualisation) | — | https://www.openeuler.org/projects/ub-service-core/white-paper/UB-Service-Core-SW-Arch-RD-2.0-en.pdf | | to-read | public |
| F2 | UB OS Component: Linux kernel extensions for managing UB interconnect and UB processing units | — | https://www.unifiedbus.com/en/software/ub-os-component | | to-read | public |
| F3 | CloudMatrix384: 384 Ascend 910C NPUs and 192 Kunpeng CPUs connected by a UB network; resources pooled and accessed uniformly | — | arXiv:2506.12708 | | to-read | public |
| F4 | UB-Mesh: nD-FullMesh datacenter topology built on UB, with all-path routing | — | arXiv:2503.20377 | | to-read | public |
| F5 | What a "Matrix Server" is in our deployment: devices, NUMA layout, UB ports | UNKNOWN | ask user | | open | internal |
| F6 | UB path latency and bandwidth: local vs 1-hop vs n-hop, per resource kind | UNKNOWN | | | open | |
| F7 | Memory pool: size, granularity, how it is allocated and to whom (per server, per pool, per process) | UNKNOWN | | | open | |
| F8 | Fabric Manager: which SLAs it enforces, and whether a scheduler can query or reserve paths | UNKNOWN | | | open | |
| F9 | Failure semantics: what a task sees when a server that backs its remote memory fails | UNKNOWN | | | open | |

Status: `to-read` (source found, not yet checked), `verified` (checked in the source; cite page / section), `open` (not known), `disputed` (sources disagree; list both).

## Engines

| Id | Engine | Version targeted | Deployment (on YARN? K8s?) | Source | Status |
|---|---|---|---|---|---|
| E1 | YARN / Hadoop | | | | open |
| E2 | Spark | | | | open |
| E3 | Flink | | | | open |

## Change log
