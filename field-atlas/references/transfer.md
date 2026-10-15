# Cross-domain transfer: from lead to testable hypothesis

Read before proposing any transfer (SKILL.md §7). Models: structure mapping [TM-1], purpose–mechanism [TM-2], intermediate abstraction [TM-3], literature-based discovery [TM-4], Toulmin [TM-6], novelty loop [TM-15], in `research-poc/references/thinking-models.md`.

## 1. The principle

Topic labels cannot tell you whether a technique transfers. Two things can: the **structure of the problem** (what is chosen, under what cost, to improve what) and the **assumptions of the technique** (what must hold for it to work). "Both use transformers" is not a basis; "both choose informative actions under a limited budget" is.

That is why cards record `Problem` and `Assumption` rows with ontology concepts, and why Problem concepts are written without domain nouns.

## 2. Finding leads

`atlas.py graph` then `atlas.py bridges` lists, for each problem concept, methods recorded on it in one domain and not in another (card level), and optionally technique–problem co-assignments from facets (facet level, weaker). Each lead shows the method's recorded assumptions and whether target-domain cards mention them.

Other sources of leads:

- a card's *Transfer notes*;
- a problem shared across domains (`bridges.md` → Problems shared across domains) where one domain has a mature mechanism and the other has a recurring limitation;
- the user's own target problem (a research-map problem, or a bottleneck they name), searched against every problem concept with the same roles.

**An absent link is a search lead, not a discovery.** The collection may just not contain the paper that did it. The prior-art loop (§4) comes before any claim of novelty.

## 3. Structural mapping and where it breaks

Write the role-by-role mapping (template §3). Roles come from the problem concept's definition. A mapping holds when the same **relations** hold between corresponding roles, not when the roles have similar names.

Then look for the breaks. The usual ones:

| Break | Question to ask |
|---|---|
| **Answer reliability** | Does an action return a clear, stable answer in the target as it does in the source (a label vs. conflicting findings)? |
| **Uncertainty estimate** | Does the target have the uncertainty or value estimate the technique scores actions with? |
| **Independence** | Do observations in the target repeat the same underlying evidence (several papers on one dataset; one result reported many times)? |
| **Fixed target** | Does acting change what we are trying to learn (reading reveals a new question rather than resolving an old one)? |
| **Cost structure** | Are costs known in advance, comparable across actions, and on the same scale as in the source? |
| **Feedback timing** | Does the outcome arrive soon enough for the technique's update loop? |
| **Scale and regime** | Are the sizes, horizons and noise levels within the range the source evidence covers? |
| **Evaluation** | Can the target measure the outcome the source optimised, or only a proxy? |

Each break is either adaptation work (§6 of the template) or a reason to stop. Score `compatibility` 0–3 from how much of the mapping holds after the breaks.

## 4. Prior-art loop

Before a hypothesis moves from `lead` to `proposed`:

1. Search with the method and problem names **and every alias** in ontology.md for both concepts, in both communities' words. Use scholar_search, web search, and the venues' own search.
2. List the closest works. For each, write the difference in one sentence.
3. If the difference is only "X applied to Y" and someone did apply X to Y, the verdict is `known`: record what they found, set `status: prior-art-found`, and stop. That is a useful result.
4. If close work exists but the mechanism or setting genuinely differs, the verdict is `partial`; sharpen the hypothesis so the difference is the thing tested, and search again (at most three rounds).
5. `none-found` only after good queries in both communities. Record the date; refresh if more than a few weeks pass.

Never assert novelty from memory. Queries use public, generic terms only.

## 5. The proposal

`templates/transfer.md` in `atlas/hypotheses/H-<nnn>-<slug>.md`. Required: source technique, target bottleneck, structural mapping, required assumptions, compatibility gaps, adaptation, prior-art check, experiment (baseline, intervention, outcome, budget, mechanism check), and the rejection criterion. `atlas.py check` refuses a `proposed` hypothesis without a prior-art search or a rejection criterion.

Hypotheses live in `atlas/hypotheses/`, apart from cards and the report's findings. They are cited as hypotheses until an experiment changes their status.

## 6. Worked example (illustrative, not a novelty claim)

Active learning ↔ a research agent choosing its next action.

| Structural role | Active learning | Research agent |
|---|---|---|
| State of knowledge | predictive model | current evidence and hypotheses |
| Available action | request a label | read a paper or run an experiment |
| Action cost | annotation effort | time, tokens, compute |
| Desired benefit | reduce relevant uncertainty | resolve the uncertainty that affects a conclusion |
| Selection policy | acquisition function | policy for the next research action |
| Stopping condition | further labels have low value | further investigation has low expected value |

Shared problem concept: `budgeted-information-acquisition`. Candidate transfer: choose the next reading or experiment by expected information value per unit cost (`expected-information-gain` + `heterogeneous-action-cost`).

Breaks found: answers are not reliable (findings conflict: `reliable-oracle` fails); a usable uncertainty estimate may not exist (`calibrated-uncertainty-available` unknown); papers repeat the same evidence (`independent-observations` fails); reading can change the question (`fixed-target-quantity` fails). These four are the adaptation work: a belief state over conflicting claims, an uncertainty proxy, de-duplication of evidence, and a value estimate that allows new questions.

The prior-art loop would search Bayesian experimental design, value of information, information-directed sampling, active search and agent tool selection before calling any of this new. A minimal experiment: on a set of research questions with known answers, compare a fixed reading order (baseline) with information-per-cost selection (intervention) on accuracy at a fixed token budget; reject if the intervention does not beat the baseline by more than seed variance at two budgets.
