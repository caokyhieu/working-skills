# Reading a codebase into a system model

The diagram is only as true as the model behind it. Build the model from code, write it
down with evidence, then draw. Never draw from a README, a commit message, a design doc
or memory alone — those describe intent; the code describes behaviour. Where they
disagree, draw the code and note the gap.

## 1. Scan (find where to read)

```bash
sysdiag scan <repo> --depth 2 > <out>/scan.md          # markdown inventory
sysdiag scan <repo> --json > <out>/scan.json            # same, machine-readable
sysdiag scan <repo> --spec-out <out>/deps.spec.json     # + draft module-dependency spec
```

What it lists and what each is good for:

| Section | Tells you |
|---|---|
| Manifests | Languages, frameworks, drivers in use (pyproject, package.json, go.mod, pom.xml, Cargo.toml) |
| docker-compose services, Dockerfiles, Kubernetes objects | Runtime units, images, ports, `depends_on` — the first draft of the boxes |
| Entry points | Where processes start (`__main__`, `func main`, CLI parsers, `CMD`) — read these first |
| Integration hints | Regex hits for servers, clients, drivers, brokers, engines, JNI/FFI, subprocesses, thread pools — the first draft of the wires |
| Endpoint literals, env names | Hosts/ports/URLs and config keys — what connects to what at runtime |
| Modules and imports | Code structure; draft for `module-dependency` |

Hints are regex matches: some are tests, examples or dead code. Each one is a place to
read, not a fact.

## 2. Read, in this order

1. **Entry points** — what process starts, what it constructs, what it listens on.
2. **Server setup** — the class or function that binds a port / registers handlers
   (`FlightServerBase` subclass, `FastAPI()` + routers, `grpc.server`, `http.ListenAndServe`).
3. **Client construction** — every place a connection to another process is made
   (driver connect, HTTP/gRPC/Flight client, producer/consumer, JNI load). The
   protocol is in the constructor or URL scheme.
4. **Config** — how addresses are wired (env, YAML, CLI flags). This tells you which
   process talks to which, and whether a link is one-to-one or fan-out (a list of nodes).
5. **The hot path** — follow one real request from entry to data and back. This is
   usually what the user wants to understand; it is also your sequence/request-flow view.
6. **Data at rest** — what is read/written where (paths, buckets, tables, caches).

Stop reading a branch once you know which box it belongs to and what crosses the
boundary. Inner logic that does not cross a box boundary does not appear in the diagram.

## 3. Write the model (`<out>/model.md`)

```markdown
# System model — <repo> @ <commit>
Question: shows <reader> how <question>.

## Runtime units (become zones / service containers)
| id | what | runs as | evidence |
|---|---|---|---|
| agent | Query Serving Agent | python process, port 8815 | agent/main.py::main |

## Components (become nodes inside a unit)
| id | in unit | role | what it does | evidence |
|---|---|---|---|---|
| union | agent | compute | unions partition streams | agent/exec.py::UnionExec |

## Connections (become edges)
| from | to | protocol / payload | direction | sync? | evidence |
|---|---|---|---|---|---|
| c1 | fss1 | Flight SQL: SQL → Arrow stream | request/response | sync | agent/flight.py::FlightReader.do_get |

## Data at rest / external systems
| id | what | evidence |

## Left out (and why)
- metrics exporter — not part of the question

## Assumptions / unverified
- broker runs on its own host (deploy files absent) — assumed
```

Granularity: a **runtime unit** is anything with its own process or host; a
**component** is a class/module that a reader would name when explaining the flow; an
**edge** exists only when something crosses a component boundary (call, message, file,
socket). Merge components that always change together. Name things as the code names
them (`FlightReaderExec`, not "Reader Component").

## 4. Map the model to a spec

| Model | Spec |
|---|---|
| host / VM / pod / node | group, role `zone`, title "<name> - <address>" |
| server process inside a host | group, role `service` (hatched), title = server kind |
| orchestrator process with internal stages | group, role `agent`, inner `lane`/`service` columns |
| component | node; role by what it is (`style.md`) |
| request/response connection | edge with `label` + `back` |
| one-way / async connection | edge, `type: async` if not awaited |
| control / config / metadata link | edge, `type: control` |
| data at rest | node `store` (cylinder) or `data` (box), in the unit that owns it |
| external system | node `external`, or `brand` for a well-known product wordmark |
| evidence | `ev` on the node/edge (`path::symbol`, list allowed) |
| inferred / not verified | `assumed: true` |
| not built yet | role `planned` + `assumed: true` |

Build with `--require-evidence`: every node/edge without `ev` or `assumed` is a warning,
and `<name>.evidence.md` lists the evidence table that goes with the picture.

## 5. Check before delivering

- Pick three edges at random and re-open their evidence: does the code really make that
  call, over that protocol, in that direction?
- Every runtime unit in compose/k8s/entry points is either drawn or listed under "Left out".
- Every `assumed` element is reported to the user.
- Labels use names a reader can grep for.
