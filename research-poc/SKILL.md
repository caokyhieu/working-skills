---
name: research-poc
description: Set up and orchestrate a paper-to-POC research workflow — reading a top-tier ML, AI, or database paper, aligning it with the company, proposing a novel extension, reproducing the benchmark, plotting results, and building the deck — as a stateful stage graph that can go back to any step and re-run only what that change affects. Use to start an idea, resume or continue the workflow, check status, or revise an earlier step.
---

# Research POC

Turn a published idea into a company proposal backed by evidence. Each idea moves through fixed stages. Each stage writes a file with a fixed format, and the next stage reads that file instead of relying on chat history. Every stage output is critiqued by **stage-critic** in a separate context before it is completed or shown at a gate. The user decides which ideas go forward; the agent never skips a gate or a critique to make progress look faster.

The reasoning rules the stages follow (structure mapping, purpose–mechanism matching, Toulmin arguments, grounded critique, …) are condensed in [references/thinking-models.md](references/thinking-models.md); skills cite them as `[TM-n]`.

## Workspace

Read [references/workspace-contract.md](references/workspace-contract.md) before creating or changing any workspace file. It defines the folder layout, the required contents of every handoff file and the gate for each stage. Other research skills follow the same contract, so do not rename files or change their formats.

Start a new idea with `python <skill-dir>/scripts/poc_state.py poc/<idea-id> init`. It creates the folder layout, `STATUS.md` and the `.poc/` state. Use a short kebab-case `idea-id` that names the source's idea, not the company product.

If the user has no source yet ("what should we work on?"), route to **source-scout**, which scans papers, open-source projects and technical blog posts against `company-context.md` and keeps a shortlist in `scouting/`. When the user picks a scouted candidate that has been digested, create the idea with `poc_state.py poc/<idea-id> promote --from scouting --source <source-id> --by <user>`: it copies the digest (and `scouting/alignment.md` if present) and records those stages as done, so the workflow starts at alignment approval or the proposal.

`company-context.md` sits at the workspace root and all ideas share it. If it is missing, copy [templates/company-context.md](templates/company-context.md) and ask the user to fill it in. Do not fill it with guessed product facts. Business alignment cannot pass its gate while the sections it relies on are empty or marked unknown.

`research-map.md` sits beside it: the translation of each priority into a research problem (canonical formulation, purpose and mechanism, sub-problems, bridging concepts, anchors, near-misses). If it is missing or has unconfirmed blocks, route to **research-map** before scouting or alignment; matching without it falls back to vocabulary overlap, which is the failure mode the map exists to prevent. `scouting/calibration.md` holds the rules learned from the user's overrules; scout, alignment and critic read it when it exists.

## Stages and workflow

Read [references/workflow.md](references/workflow.md) before running, resuming or revising any stage. The stage graph is in [pipeline.json](pipeline.json):

| Stage | Owner skill | Depends on | Writes | Gate |
|---|---|---|---|---|
| digest | source-digest | paper, repo or post sources | `sources/<source-id>/digest.md` | — |
| aligned | idea-alignment | digest, `company-context.md`, `research-map.md`, `scouting/calibration.md` | `ideas/alignment.md` | user picks match(es) |
| proposed | idea-extension | digest, aligned, `research-map.md` | `ideas/proposal.md` | user approves hypothesis and plan |
| reproduced | bench-setup | digest, proposed | `experiments/plan.md`, `reported_targets.json`, `reproduction.md` | user accepts verdict |
| extended | bench-setup | proposed, reproduced | `experiments/extension.md` (+ runs) | — |
| plotted | result-plots | proposed, extended, `results/runs.jsonl` | `results/summary.md`, `figures/` | — |
| deck | insight-ppt | aligned, proposed, plotted, `research-map.md` | `deck/*.pptx` | user approves deck |

Every stage has `critic: true`: after the owner skill returns, stage-critic reviews the output against its rubric and the stage's inputs, writes `reviews/<stage>-<run>.md`, and records `pass`, `revise` or `block`. `revise` sends the owner back in update mode (max two rounds); `block` stops for the user. `complete` is refused on `block`; `approve` is refused without a review. Gate prompts show the review's blockers and majors next to the gate question.

All state goes through `scripts/poc_state.py`. Never track progress only in chat or by editing `.poc/` by hand. Each completed stage records fingerprints of what it read and wrote, so status is recomputed from the files:

- A changed upstream output, a hand edit, or a new `company-context.md` marks exactly the affected stages `stale`.
- An approval stops counting when the approved file changes.
- A re-run that leaves its output unchanged does not trigger downstream work.

**Continue / resume:** run the orchestrator loop in workflow.md: `next` → gate, failure or compute check → `start` → delegate to the owner skill with the brief → **stage-critic** → (revise round if needed) → verify outputs → `complete`, then repeat. Stop at every gate, failure and expensive stage until the user answers.

**Go back:** map the request to the earliest stage whose output must change and run `reopen <stage> --reason "<user's words>"`, then continue the loop. Downstream stages are re-checked automatically and re-run in update mode only if their inputs changed. If a later result invalidates an earlier stage (for example, the reproduction shows the paper's claim doesn't hold), reopen that earlier stage instead of working around it.

**Status:** `status` prints the table and next actions and refreshes the generated block in `STATUS.md`. Record user decisions and reasons in `STATUS.md` → Decisions, next to the event log.

If an owner skill is not installed, do that stage by following the workspace contract directly and say that the skill was unavailable. If stage-critic is not installed, do the critique yourself in a fresh subagent from `stage-critic/references/rubrics/<stage>.md` if that folder exists; otherwise record the review as `pass` with the note "no critic available" so the omission is visible in `events.jsonl`.

## Standing rules

- Keep what the paper reports, what we measured, and what we project for the company separate in every file. Never present a paper's numbers as company results.
- Label claims as `[reported]`, `[measured: run ids]`, `[company-context]` or `[inference]`.
- Negative results are results. Record them in the stage file and in `STATUS.md`; do not drop an idea's history quietly.
- Do not send `company-context.md` content or internal data to public search tools, public LLM endpoints or external services.
- Ask before spending significant compute. Report the estimated GPU-hours before any full sweep.
