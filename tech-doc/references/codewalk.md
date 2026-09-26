# Code walk

The docs describe what someone meant to build. The code is what runs. This pass reads
the code for the mechanisms the docs skip, and writes them into `CODEMAP.md` so the
outline has a section for each.

Read in Phase 1c, and again before drafting any `Type: mechanism` section.

## How to read a class

Open the primary class(es) for an area and read the whole file, in this order:

1. Class-level Javadoc / module doc — the stated purpose and constraints.
2. Fields — what state the instance holds. A field typed as an enum or a status is a
   state machine; find the enum.
3. Constructor — what must be supplied, what it opens (connections, pools, threads),
   what it registers.
4. Public methods — the operations. For each, the thread it runs on and what it can
   throw.
5. `catch` blocks and `throw` sites — the failure modes and the fallback each triggers.
6. Static config reads — `config.get*("...")`, constants with defaults.

Do not grep for one term and stop. The mechanism is usually in a method the docs never
name.

## The six things to record per component

| Field | What to write |
|---|---|
| **Lifecycle / state** | The states a record or instance moves through, the trigger for each transition, and the enum/field that holds the state. A diagram in prose: `SHADOW --promoteThreshold misses--> WARMING`. |
| **Threading** | Which thread or pool runs this. What is single-writer or not thread-safe. Where a lock sits. |
| **Config surface** | Every config key read, its default, its effect. One row each. |
| **Failure modes** | Every exception thrown or caught, and the fallback (retry, degrade, propagate to client, log-and-continue). |
| **Transport / wire** | For anything dialing a backend: connection open, pooling, timeouts, driver/library resolution, catalog/metadata sync. Name the driver class or native lib. |
| **Surprises** | Anything the code does that a reader of the docs would not expect. These are the highest-value entries. |

## CODEMAP.md shape

```markdown
# Code map

## <Component> — `path/to/PrimaryClass.java`
- Lifecycle: <states + transitions, or "stateless">
- Threading: <thread/pool, non-thread-safe parts>
- Config: <key = default — effect>, one per line
- Failures: <exception -> fallback>, one per line
- Transport: <connection open / pool / timeout / driver resolution — or n/a>
- Surprises: <the non-obvious behavior>
- Feeds: §NN   <the outline section that will carry this>

## Deliberately dropped
- <mechanism> — <why it is out of scope for this doc>
```

## Depth bar

For every `Type: mechanism` section, ask: could this have been written from the source
docs alone, without opening the code? If yes, `CODEMAP.md` did not feed it. Go back and
read the class.

A mechanism section names classes and methods, gives config keys with their defaults,
states the failure mode and the thread it runs on. A section that has none of these is
an overview wearing a mechanism's title.
