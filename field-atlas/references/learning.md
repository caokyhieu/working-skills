# Memory and learning from use

Read at the end of a run (SKILL.md §9) and whenever a rule is about to change.

## 1. Five memories, kept apart

| Memory | Holds | Where | Written by |
|---|---|---|---|
| **Evidence store** | papers, versions, dates, reviews, repository and citation observations, full text, located passages | `<field>/papers.jsonl`, `<field>/raw/`, `<field>/fulltext/`, card rows with `where` | script; cards |
| **Semantic memory** | concepts, relations, assumptions, supported claims | `ontology.md` (schema and concepts), `graph.jsonl` (compiled from cards) | user-confirmed ontology changes; cards |
| **Episodic memory** | searches run, extraction failures, investigations and outcomes | `<field>/log.md` | agent and script, append-only |
| **Procedural memory** | validated search strategies, extraction rules, analysis procedures | `playbook.md` | only through §3 |
| **Hypothesis store** | unverified connections, proposed experiments, their outcomes | `hypotheses/` | agent; status changes logged |

The hypothesis store never feeds back into the semantic memory as fact. A hypothesis becomes knowledge only through an experiment or a paper, and then as a card with evidence.

## 2. Evaluate each stage separately

One end-to-end impression hides where things fail. Check stages one at a time, on samples a person (or a separate agent context, as with stage-critic) has checked.

| Stage | Question | How | Record |
|---|---|---|---|
| Retrieval | Did it find the relevant papers? | The user lists 10–20 papers they know belong; measure how many are in `papers.jsonl` and how many were carded | recall on the expert list |
| Extraction | Are claims and relations supported by the cited passages? | `atlas.py audit --n 20`, checked by someone other than the card's author | supported / partly / unsupported / wrong-type rates |
| Organisation | Does the map keep useful connections across topics? | The user names pairs of papers that should be linked; check they share a concept in some facet or an edge | pairs connected / named |
| Trend analysis | Would it have been right at the time? | `share --cutoff <date>` and `changes` with only pre-cutoff papers; compare with what followed | hits / misses with reasons |
| Transfer proposals | Are they compatible, new, useful? | Expert verdict per hypothesis: `compatible`, `already known`, `useful experiment`, `rejected because …` | verdicts and reasons |

Log every evaluation in `playbook.md` → Evaluation history, with the failure patterns.

## 3. Changing a rule

When a failure pattern repeats (for example, experts keep rejecting transfers because an assumption was overlooked):

1. **Propose** the rule in `playbook.md` → Proposed: the rule, the stage, the cases that motivated it.
2. **Test** it on cases that did not motivate it: other hypotheses, other cards, another cutoff. A rule that only fixes the cases it was written from is not yet a rule.
3. **Adopt** it if it helps on the held-out cases without breaking others; otherwise move it to Rejected with the reason.
4. Rules that change the schema go through ontology.md §6 instead.

Examples of rules that come out of this: a new row in the break checklist (transfer.md §3), a new alias source for retrieval, a stricter extraction rule ("an Evidence row must name the baseline"), a minimum n for a trend claim.
