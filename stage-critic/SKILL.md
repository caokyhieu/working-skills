---
name: stage-critic
description: Independent, located critique of one research-poc stage output (digest, alignment, proposal, reproduction, extension, plots, deck) or a scouting shortlist against a per-stage rubric, checked against the stage's inputs rather than the output alone. Returns pass / revise / block with blocker-graded objections. Use after an owner skill finishes and before the stage is completed or shown to the user, or when the user asks for a critical review of any stage file.
---

# Stage Critic

Find what is wrong with a stage output before the user sees it. The critic never edits the output; it writes a review and a verdict. It reads the stage's **inputs** as well as its output, because an output cannot be judged from itself [TM-10 in research-poc/references/thinking-models.md]. It runs in a fresh context, separate from the writer [TM-11].

Read [research-poc/references/thinking-models.md](../research-poc/references/thinking-models.md) once. Read the rubric for the stage in [references/rubrics/](references/rubrics/). Write `poc/<idea-id>/reviews/<stage>-<run>.md` from [templates/review.md](templates/review.md) (for scouting: `scouting/reviews/<date>-shortlist.md`).

## Inputs

The orchestrator (or the user) gives: the idea path, the stage, the run number, and the review round (1 or 2). Read:

1. The stage output(s) named in `.poc/pipeline.json` for that stage.
2. The stage's inputs: dependency outputs plus declared files (`poc_state.py start` prints them in the brief as `reads`). For `digest`, also the source itself when it is on disk (`sources/<id>/source.*`) or reachable by URL.
3. `research-map.md` and `company-context.md` for `aligned`, `proposed` and `deck`.
4. `scouting/calibration.md` when it exists: rules from the user's past overrules apply to every stage.
5. Previous reviews of the same stage, to check that earlier blockers were addressed and not merely deleted.

## Procedure

1. Answer the rubric's questions **in order**, each with `ok`, or an objection. Do not skip a question; if it doesn't apply, say why.
2. Add objections outside the rubric under *Other*, marked as such [TM-12].
3. Every objection is located and actionable [TM-13]:

   `[<file> §<section> / line <n>] — what is wrong — what would fix it — blocker | major | minor`

   - **blocker**: the output would mislead the next stage or the user (fabricated number, match with no shared structure, hypothesis with no falsifier, novelty asserted without search, threshold below seed variance, claim without run ids).
   - **major**: a real gap the user should know about before approving.
   - **minor**: precision or clarity.
4. Delete generic objections before returning. "Could be more rigorous" or "consider adding detail" is not an objection.
5. Write the **rebuttal** for the stage's central claim [TM-6]: the concrete company condition or measurement under which it fails. For `aligned` and `proposed` this is required; for other stages, write it when the output makes a claim.
6. Verdict:
   - `pass` — no blockers, ≤ 2 majors. Means "nothing found that must change", not "good" [TM-17].
   - `revise` — at least one blocker, or > 2 majors, and round < max rounds. The review becomes the writer's `why` list.
   - `block` — blockers remain after the last round, or the objection needs a user decision (e.g. a company fact the output needs is `UNKNOWN`).
7. End with a **meta-review**: two or three lines on the recurring cause (e.g. "matches rely on vocabulary overlap; the formulation step was skipped"). source-scout copies useful meta-reviews into `scouting/calibration.md`.

Record the verdict with `python <research-poc-dir>/scripts/poc_state.py poc/<idea-id> review <stage> --verdict pass|revise|block --by stage-critic --path reviews/<stage>-<run>.md --summary "<one line>"`. The script refuses `complete` while the last review of the current output is `block`, and refuses `approve` while no review exists for the current output when the stage is marked `critic: true`.

## What the critic is not

- Not a copy-editor. Style objections are `minor` and rarely worth writing.
- Not the user's gate. It cannot approve.
- Not the writer. If a fix is obvious, say what it is; don't apply it.
- Not a fan. A review with zero objections must list what was checked against which input, so the user can see it was actually read.

## Round limits

Default two rounds per stage per run. After round 2, the verdict is `pass` or `block`, never `revise`. The orchestrator surfaces `block` to the user with the review attached.
