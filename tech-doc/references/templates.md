# Templates

## state.json

```json
{
  "slug": "query-engine-readme",
  "target": "docs/query-engine.md",
  "companions": ["docs/query-engine/benchmarks.md"],
  "phase": "drafting",
  "updated": "2026-09-02",
  "sections": [
    {"id": "01-overview",  "title": "Overview",  "status": "approved", "file": "main"},
    {"id": "02-architecture", "title": "Architecture", "status": "verified", "file": "main",
     "verify_rounds": 2},
    {"id": "03-api", "title": "Query API", "status": "pending", "file": "main"},
    {"id": "11-benchmarks", "title": "Benchmark results", "status": "pending",
     "file": "benchmarks.md"}
  ],
  "sources": [
    {"path": "docs/RESULTS.md", "level": "measured", "verdict": "split",
     "feeds": ["10-adbc-connectors", "11-benchmarks"]},
    {"path": "docs/architecture.md", "level": "derived", "verdict": "supersede",
     "feeds": ["02-topology"], "note": "3 claims corrected at source"}
  ],
  "open_questions": ["Default Flight SQL port?"],
  "last_sweep": {"after_section": "09-connector-matrix", "found": 2},
  "resolved": ["architecture.md ShardingGate claim: corrected at source, user approved"]
}
```

`phase`: `scope` | `ingest` | `codewalk` | `outline` | `drafting` | `assembly` | `done`.
`status`: `pending` | `drafted` | `verified` | `approved` | `deferred`.
`file`: `main` | the companion file name.
`level`: `measured` | `authored` | `derived` | `external`.
`verdict`: `absorb` | `split` | `extract` | `supersede` | `drop`.

## SOURCES.md

```markdown
# Ingested sources

| Doc | Level | Verdict | Feeds | Last touched |
|---|---|---|---|---|
| `docs/RESULTS.md` | measured | split | §10, §11 (benchmarks.md) | 2026-08-14 |
| `docs/architecture.md` | derived | supersede | §2, §3 | 2026-07-02 |
| `docs/design-spec.md` | authored | absorb | §1 (rationale), §12 | 2026-06-20 |

## Per doc

### docs/RESULTS.md
- Covers: Druid ADBC vs Avatica JDBC throughput, 6 query shapes.
- Take: §10 gets the one summary table (ADBC vs JDBC per payload); §11 gets all six
  query-shape tables, re-typed into this doc's columns. Not the methodology prose.
- Conditions carried into the doc: row counts, query text, hardware, 300 s ceiling.
- Verified against: `connectors/druid-adbc/src/lib.rs`.

### docs/architecture.md
- Covers: component topology, planner passes.
- Conflicts: claims `ShardingGate` runs after `TopNPushdown`; no non-test caller exists.
- Take: nothing — code supplies §2, §3.
- Resolution: corrected at source (user approved 2026-09-02).
- Dropped: throughput figures superseded by RESULTS.md.

### docs/design-spec.md
- Take: the three design choices behind the proxy (why Flight SQL, why StarRocks
  coordinates, why no result cache in the proxy), stated as `Design choice:` lines.
- Dropped: background narration, the obsolete deployment diagram.
```

One `### ` block per source doc. "Take" and "Conflicts" are the two lines that matter —
the first says exactly which content is carried in and where (Phase 4 checks it is
there), the second stops the next session re-discovering the same drift.

The `Doc` column is what `metrics.py` reads for the `source_links` gate: keep each path
backticked in the first column.

## CODEMAP.md

```markdown
# Code map

## Connector layer — `engine/pushdown/src/main/java/com/pushdown/config/ConnectorRegistry.java`
- Lifecycle: stateless after `loadDefault()`; registry built once per JVM.
- Threading: read-only after construction; safe to share.
- Config: `connectors.conf` default-deny — a backend with no section declares no transports.
- Failures: missing section -> `IllegalStateException` at load, not at query time.
- Transport: ADBC native lib resolved as a literal filesystem path (`driver_url`), never
  a driver-manager name lookup; bare `adbc_driver_druid` fails at query time.
- Surprises: `DialectResolver` returns the StarRocks dialect for every backend.
- Feeds: §6

## Cache registry lifecycle — `cache/core/src/main/java/com/pushdown/cache/CacheStatus.java`
- Lifecycle: SHADOW -> WARMING -> READY -> BACKFILLING/DRAINING; all mutations via
  `CacheManager` on one thread.
- Config: `promoteThreshold`, `promoteWindowSeconds`, `shadowTtlSeconds`,
  `evictionGraceSeconds` (10s), eviction sweep every 5 min.
- Failures: WARMING load fails -> back to SHADOW; orphaned DRAINING recovered by sweep.
- Feeds: §7

## Deliberately dropped
- Flight gRPC event loop internals — out of scope; this doc is the query path, not the server.
```

One `## ` block per component. `Feeds:` must name a real section, or the entry moves to
`Deliberately dropped`.

## CONTEXT.md

```markdown
# Frozen context

## Components (exact spelling)
| Name | Is | Lives in |
|---|---|---|
| Flight SQL Proxy | ADBC-facing entry point | `proxy/` |

## Terms
- **pushdown** — predicate/aggregate evaluated in the source engine. Not "push-down".

## Example schema (reuse everywhere)
events(day DATE, user_id BIGINT, source VARCHAR(32), amount DECIMAL(12,2))  [Druid]
users(user_id BIGINT PRIMARY KEY, region VARCHAR(16))                       [GaussDB]

## Diagram legend
Solid arrow = data. Edge label = payload. `[(...)]` = external store.
```

## Section skeletons

**Overview** — what it is (1 sentence), what problem it solves (1), what it is not (1),
one topology diagram.

**Architecture** — component table (name / responsibility / module), one top-level
diagram, then one subsection per component with its own diagram if needed.

**API** — per endpoint: signature, one request example, one response example, error line.

**Mechanism** (`Type: mechanism`) — two or three sentences on what the component does
and its precondition, then, as bold-lead-in bullet groups: the lifecycle / state transitions
(with a `stateDiagram-v2` if more than three states), the thread it runs on, a config
table (`key | default | effect`), and the failure modes with their fallback. Name the
classes and methods. One worked example (SQL, wire trace, or state walk).

**Use cases** — per case: goal (1 sentence), schema, query, what the engine does.

**Operations** — config table (key / default / effect), start command, health check,
three most common failures with their fix.

**Companion file** — `# <Title>` then one line stating what it holds and which main
section it supports (`Reference for §10.`), then the sections in outline order. It
carries its own condition lines and schemas; it never assumes the reader has an
ingested doc.
