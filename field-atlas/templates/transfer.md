---
id: H-<nnn>
title: <short name>
status: lead            # lead | proposed | prior-art-found | testing | supported | rejected | parked
source_field: <field-id>
target_field: <field-id or research-map R-id>
source_method: <concept>
target_problem: <concept>
lead: <L-number in bridges.md of DATE, or "user", or "card <paper-id>">
compatibility: <0-3>    # how much of the structural mapping holds (§3, §5)
evidence: <0-3>         # how well the technique is supported in its source domain (§2)
adaptation_cost: <low | medium | high>
prior_art: not-searched # not-searched | none-found | partial | known
rejection_criterion: <one line; required from `proposed` on>
created: <YYYY-MM-DD>
---

# H-<nnn>: <could <technique> solve <bottleneck> in <target>?>

> This is a hypothesis, not established knowledge. It lives in the hypothesis store and is never cited as a finding until `status: supported`, and then only with its experiment.

## 1. Transfer in one sentence

Could <source technique> address <target bottleneck>, because both <shared relational structure>?

## 2. Source technique

What is transferred (the method and, above all, its mechanism), the source cards, and how strong its evidence is in the source domain (independent groups, ablations, replications).

| Card | Evidence verdict | What it shows | Location |
|---|---|---|---|

## 3. Structural mapping

Map roles, not words [TM-1]. Use the problem concept's roles from ontology.md when it lists them.

| Structural role | Source: <field> | Target: <field> | Holds? |
|---|---|---|---|
| <state of knowledge> | | | yes / partly / no / unknown |
| <available action> | | | |
| <action cost> | | | |
| <desired benefit> | | | |
| <selection policy> | | | |
| <stopping condition> | | | |

## 4. Required assumptions

Every `requires` edge of the source method, plus assumptions found by reading.

| Assumption (concept) | Why the technique needs it | In the target: holds / fails / unknown | Evidence (card, location, or [inference]) |
|---|---|---|---|

## 5. Compatibility gaps

Where the mapping breaks (references/transfer.md §3 lists the usual breaks). Each gap is adaptation work or a reason to stop.

-

## 6. Adaptation

What must change for the technique to work in the target, and the cheapest version worth testing.

## 7. Prior-art check

Run the loop in references/transfer.md §4. Record every query; an empty search is a result only if the queries were good.

| Date | Query (public terms) | Where | Closest work | Difference in one sentence |
|---|---|---|---|---|

Verdict: `none-found` | `partial` | `known` (set `prior_art:` above). If `known`, set `status: prior-art-found`, say what the existing work found, and stop.

## 8. Experiment

| Item | Value |
|---|---|
| Baseline | <the strongest current approach in the target, tuned> |
| Intervention | <the adapted technique> |
| Outcome | <metric, and the threshold that would matter> |
| Setting | <dataset / environment / task set> |
| Budget | <compute, time, people> |
| Mechanism check | <an ablation showing *why* it helps, not only that it does> |

## 9. Rejection criterion

The result, fixed before running anything, that would count against the hypothesis. Copy it to `rejection_criterion:` above.

## 10. Outcome log

| Date | What happened | Status change | Lesson for playbook.md |
|---|---|---|---|
