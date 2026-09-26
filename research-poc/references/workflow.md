# Workflow engine

Each idea runs as a graph of stages, not a fixed line. Any stage can be reopened. Work after it is redone only when its inputs actually changed. The state is on disk, so any agent or session can pick up where the last one stopped.

`SCRIPT` below means `python <research-poc-skill-dir>/scripts/poc_state.py poc/<idea-id>`.

## State model

- `.poc/pipeline.json`: the stage graph (copied from the skill's `pipeline.json` at init; edit the copy to customise one idea). Each stage has an owner skill, `deps`, extra `inputs`, `outputs` (globs), and optional `gate` / `expensive` flags.
- `.poc/state.json`: per stage, the verdict, summary, run count, the **fingerprints of inputs and outputs recorded at completion**, the approval (bound to the output fingerprint), and the critic's reviews (each bound to the output fingerprint it reviewed). Written only by the script.
- `.poc/events.jsonl`: append-only history of start, review, complete, approve, reopen and abort events, with who and why.
- `STATUS.md`: the generated state table between markers, plus human-written decisions, open questions and notes.

Status is **recomputed from files on every call**:

| Status | Meaning | Next action |
|---|---|---|
| `pending` | never completed | run owner skill (create) |
| `in_progress` | an agent holds it | wait, or `abort` if abandoned |
| `stale` | an input changed since completion (upstream output, company context, hand edit upstream) | run owner skill in **update mode** |
| `reopened` | a person or agent explicitly went back to it | run owner skill in update mode, focused on the reopen reason |
| `edited` | its own outputs were changed by hand after completion | review the edit, then `complete` (and re-approve if gated) |
| `awaiting_approval` | gated stage completed, but this exact output is not approved | ask the user the gate question, then `approve` |
| `failed` | completed with verdict `failed` | decide with the user: reopen an upstream stage or re-run |
| `done` | inputs unchanged, outputs unchanged, approved if gated | nothing |

A stage is **blocked** while any dependency is not `done`. Downstream stages show "waiting on …" instead of running on inputs that aren't final.

**Early cutoff:** if an update re-run produces byte-identical outputs, downstream fingerprints still match, so those stages stay `done` and keep their approvals. Expensive experiments are only re-run when their inputs really changed.

## Orchestrator loop

Run this whenever the user asks to continue, resume, or "run the workflow":

1. `SCRIPT next`. If it prints "All stages done", report and stop.
2. Take the first action. Stages are listed in dependency order.
   - **`awaiting_approval`:** show the user the stage output summary and the gate question. `SCRIPT approve <stage> --by <user> --note "<decision>"` only on an explicit yes, then record the decision in `STATUS.md` → Decisions. Stop the loop until the user answers.
   - **`failed`:** present the verdict and the options (reopen which upstream stage, or re-run with what change). Stop until the user decides.
   - **`edited`:** read the diff against the previous version if available (git), summarise what changed and whether it breaks the stage's contract, then `complete` or reopen.
   - **`pending` / `stale` / `reopened`:** continue with step 3.
3. **Expensive stages** (`reproduced`, `extended`): before starting, state what will be re-run and the estimated compute, and get approval unless the user already authorised it for this change.
4. `SCRIPT start <stage> --by <agent-name>`. It prints a JSON **brief**: stage, owner skill, mode (`create`/`update`), `why` (changed inputs or reopen reason), `reads`, `writes`.
5. **Delegate.** Hand the brief to the owner skill. Use a subagent if the host supports it, with the brief, the idea path, and the instruction to follow that skill's *Update mode* section. Otherwise run the skill inline. One stage per agent. Don't let a delegate run other stages.
6. **Critique** (stages with `critic: true`, which is all of them by default). When the owner returns, run **stage-critic** in a fresh context (subagent, or a separate session — never the writer's context [TM-11]) with the idea path, the stage, the run and the round. It reads the output *and the inputs*, writes `reviews/<stage>-<run>.md` and records `SCRIPT review <stage> --verdict pass|revise|block --path reviews/<stage>-<run>.md --summary "..."`.
   - `pass` → step 7.
   - `revise` → `SCRIPT start <stage> --by <agent> --force`; the brief's `why` now carries the review path. Hand it to the owner skill in update mode, then critique again (round 2). After round 2 the critic returns `pass` or `block`, never `revise`.
   - `block` → stop. Show the user the review and the gate question together; `complete` is refused until the output changes and is re-reviewed, or the user decides and you pass `--force` with their decision in `--summary` and a line in `STATUS.md` → Critic objections overruled.
7. Check the outputs exist and meet the workspace contract, then `SCRIPT complete <stage> --verdict passed|accepted-with-caveats|failed --summary "<one line>"`. The script reports whether outputs changed. For gated stages, the gate prompt to the user must include the review's verdict and its blocker/major list; `approve` is refused while the current output has no review.
8. If the delegate could not finish, `SCRIPT abort <stage> --reason "..."` and report.
9. Repeat from step 1. Stop at every gate, every failure, before expensive work, or when the user interrupts.

Parallelism: stages may run in parallel only if neither depends on the other, directly or indirectly. In the default graph that never happens, so run one at a time. Several ideas (`poc/<idea-a>`, `poc/<idea-b>`) can run in parallel.

## Starting from scouting

`SCRIPT promote --from scouting --source <source-id> --by <user>` initialises the idea, copies `scouting/sources/<source-id>/` into `sources/`, marks `digest` complete, and, if `scouting/alignment.md` exists, copies it to `ideas/alignment.md` and marks `aligned` complete (still needing the user's gate approval). Then run the loop as usual. Record the promotion in source-scout's log (`scout_log.py scouting promote`), so the candidate leaves the shortlist.

## Going back

Map the user's request to the earliest stage whose **output** must change, and reopen only that stage:

| User says | Reopen | Why that stage |
|---|---|---|
| "Company priorities changed" | nothing; edit `company-context.md`, then run research-map to update `research-map.md` | `aligned` becomes stale automatically (both files are its inputs) |
| "The agent keeps matching on the wrong thing" | nothing; add a rule to `scouting/calibration.md` (`scout_log.py override`) and, if it generalises, to the research map | `aligned` becomes stale; the critic reads the rule on the next round |
| "Pick match M2 instead" | `aligned` | selection lives in alignment.md |
| "Raise the threshold to 15%" / "add an ablation" / "different baseline" | `proposed` | hypothesis and experiments live in proposal.md |
| "The paper's protocol was misread" | `digest` | the protocol lives in digest.md |
| "Reproduction harness had a bug" | `reproduced` | runs get superseded, reproduction re-verified |
| "Plot latency p99 instead of mean" | `plotted` | figures only; experiments untouched |
| "Change the deck story" | `deck` | slides only |

`SCRIPT reopen <stage> --reason "<user's words>" --by <user>`, then run the loop. Everything downstream is re-checked automatically. Don't reopen downstream stages by hand, and don't edit a downstream output to "match" the change without going through its stage.

If the user edits a file directly (for example proposal.md), don't reopen anything. The stage shows `edited` and its dependents `stale`; the loop handles both.

## Update mode (contract for every owner skill)

When the brief says `mode: update`:

1. Read your previous output and the `why` list. Read only the changed inputs closely. If `why` names a critic review (`review revise: reviews/<stage>-<n>.md`), read it and address every blocker and major at the location it cites; if you dispute one, say so in the change log with the reason rather than ignoring it. Never edit the review file.
2. Decide the smallest correct change. Keep content the change doesn't affect byte-identical, so early cutoff can work: don't reformat, re-date or reorder untouched sections.
3. Apply the change. Record it in the output's change log (or `STATUS.md` → Notes if the format has none): date, trigger, what changed, what was checked and left as is.
4. If nothing needs to change, leave the file untouched and say so. The orchestrator completes the stage and downstream stays `done`.
5. Respect gates: a change to a hypothesis, threshold, falsification criterion or match selection needs the user's approval again, and the script enforces this.
6. For experiments: never delete runs. Supersede them (see results-schema.md), and re-run only the configurations affected by the change.

## Guardrails

- Only the script writes `.poc/`. Never edit `state.json` or `events.jsonl` by hand.
- Don't use `--force` to skip a gate or a blocked dependency without the user's explicit instruction for that specific case. Record the reason in `STATUS.md` → Decisions.
- A delegate's report is not proof. Check that output files exist and follow the contract before `complete`.
- Fingerprints cover the files declared in the pipeline. If a change the pipeline can't see affects results (for example harness code changed after reproduction), reopen the affected stage explicitly.
