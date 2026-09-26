---
name: idea-extension
description: Turn a selected paper-to-company match into a novel, testable research proposal — generate extension directions, run a documented prior-art and novelty check, and commit to a hypothesis that could be proven wrong, with a falsification criterion, ablations, and a compute estimate. Use when extending a paper's idea, checking whether an idea is novel, or writing a research proposal before experiments.
---

# Idea Extension

Produce one proposal that is new, matters to the company, and can be tested on the original paper's benchmark. Novelty must be shown with evidence, not claimed. A proposal that turns out to be `already done` is a useful result: report it and stop.

Follow the research-poc workspace contract. Read the digest(s), `ideas/alignment.md` (the selected match, its relevance chain, its assumption table and the direction synthesis), the matching problem block in `research-map.md`, and `company-context.md §6`. Write `poc/<idea-id>/ideas/proposal.md` using [templates/proposal.md](templates/proposal.md). The models behind these rules are in [research-poc/references/thinking-models.md](../research-poc/references/thinking-models.md).

## 1. Generate directions

Read [references/extension-patterns.md](references/extension-patterns.md). Generate 4–8 directions from: the alignment's *Must change* line and the assumptions marked `breaks` (the strongest seeds), the direction synthesis, the digest's weak spots and extension hooks. Use at least three different patterns; no two directions from the same pattern unless justified — generated idea sets collapse onto one idea otherwise [TM-16]. For each, write one paragraph: what changes, why it should help (the mechanism, not only the intuition), what it costs, and how it would show up on the benchmark.

Screen them on (a) plausibility of mechanism, (b) testability on the original benchmark plus any company-relevant variant, (c) company relevance via the research-map problem, (d) effort and feasibility — weighted at least as much as novelty [TM-16]. Keep the best 2–3 for the novelty check [TM-14].

## 2. Novelty check

Read [references/novelty-check.md](references/novelty-check.md) and follow it for each remaining direction. Use web or scholarly search tools if available. If they aren't, say the check could not be done and mark novelty `unverified`. Never assert novelty from memory alone.

Search only with public terms describing the method. Never include company names, product details, internal data or `company-context.md` content in queries.

Run it as a loop, not a single pass [TM-15]: search → list the closest works → restate the difference in one sentence → if the difference is only a hyperparameter, a dataset swap, or "X applied to Y", revise the direction so the mechanism actually differs, and search again. Stop after three rounds or when the verdict is stable. Record every round's queries, sources, dates and closest works with a concrete difference statement. Verdict: `novel` (no work combines these elements for this problem), `incremental` (close work exists; our difference is real but small) or `already done`. Drop `already done` directions. An `incremental` direction may go ahead if its company relevance is strong; say so honestly.

## 3. Commit to one proposal

Present the surviving directions with their verdicts and a recommendation, and let the user choose. Then write the proposal, starting with the **Heilmeier catechism** [TM-7] in plain language — what we are trying to do, how it is done today and its limits, what is new and why it will work, who cares (cite the research-map problem and `company-context §6`), risks, cost, time, and the mid-term and final exams (the early kill test and the falsification criterion). Then:

- **Hypothesis:** "X improves M by ≥ Y over Z on B under C." Choose Y from what would matter (the "what counts as a win" section in `company-context.md`) and from the seed variance reported in the paper. Don't pick Y to be easy to reach.
- **Falsification:** the concrete result that rejects the hypothesis, fixed before any experiment.
- **Mechanism check:** at least one ablation that shows *why* it works, not only *that* it works.
- **Experiments:** main comparison on the paper's benchmark (same datasets, metrics, baselines), ablations, sensitivity, optional company-relevant variant. Include seeds and an estimated compute range.
- **Risks:** what is most likely to make this fail, and the cheapest early experiment that would reveal it.
- **Company relevance:** which outcome changes which decision, citing `company-context.md`.

## Gate

The orchestrator runs stage-critic on the proposal (threshold above noise, falsifier concrete, novelty searched not asserted, ≥ 4 directions from ≥ 3 patterns) before asking the user. The user approves `proposal.md`; the research-poc orchestrator records the approval, which becomes void if the file changes. After approval, don't change the hypothesis, threshold or falsification criterion without the user agreeing and a dated note in the proposal. bench-setup uses these values as fixed.

## Update mode

When the research-poc workflow starts this stage with `mode: update` (a stale or reopened stage), follow the update-mode contract in research-poc's `references/workflow.md`:
- Read the previous output and the brief's `why` list. When `why` names a stage-critic review (`review revise: reviews/<stage>-<n>.md`), address every blocker and major at the location it cites, and record in the change log which were fixed and which are disputed, with the reason. Never edit the review file.
- Make the smallest correct change and leave unaffected content byte-identical.
- Add a Change log entry.
- If nothing needs to change, leave the file untouched and report that.

Report back to the orchestrator; don't mark the stage complete yourself.

For idea-extension in particular: a changed hypothesis, threshold, falsification criterion or experiment list needs fresh user approval. Refresh the novelty check if more than a few weeks have passed since its recorded search date.
