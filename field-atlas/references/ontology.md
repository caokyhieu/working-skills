# Field atlas ontology

version: 1
status: draft (confirm with the user at setup; then write `confirmed YYYY-MM-DD` here)

This file is the **shared schema** for every field in the atlas. It is what makes two fields comparable: a card from robotics and a card from research agents can only be lined up if both use the same entity types, relations and concept names. `atlas.py` parses the tables in §2–§5; rows whose first cell is not in backticks are ignored, so explanations can sit beside them.

- The **ontology** (this file) defines the kinds of things and relations, and the controlled concept names.
- The **knowledge graph** (`graph.jsonl`, compiled from cards) holds the instances: this paper's problem, this paper's claim at Table 2.

Keep the schema small. Extend it only through §6.

## 1. How the parts fit

```text
            addresses            uses
 Method ─────────────▶ Problem    Method ─────▶ Mechanism        (why it should help)
   │ requires / relaxes ─▶ Assumption          Problem ─constrained-by─▶ Constraint
   │ has-limitation ─▶ Limitation              Method ─builds-on─▶ paper:<id>   (influence, with location)
   ▼
 Experiment ─evaluates─▶ Method;  ─uses─▶ Dataset;  ─measured-by─▶ Metric;  ─produces─▶ Evidence
 Evidence ─supports / challenges─▶ Claim ─about─▶ Method | Problem | Mechanism
```

A **Problem** concept should be written at the level where the structure is visible and the field's nouns are gone [TM-5]: "choose costly observations to reduce decision-relevant uncertainty under a budget", not "active learning for robot grasping". That level is what lets the bridge search in `atlas.py bridges` find the same problem in two domains [TM-1, TM-3].

## 2. Entity types

| Type | What it captures | A card row must carry |
|---|---|---|
| `Problem` | What must be solved: inputs, outputs, objective, regime | text; concept when one fits |
| `Method` | The procedure the paper proposes or uses as a baseline | text; concept when one fits |
| `Mechanism` | Why the procedure is expected to help: the property it exploits | text; concept |
| `Assumption` | What must hold for the method to work, stated or found | text; where (or `[inference]`) |
| `Constraint` | What limits acceptable solutions (budget, latency, privacy, no interaction) | text |
| `Dataset` | Dataset, benchmark, simulator or environment used for evaluation | text; concept for shared benchmarks |
| `Metric` | How outcomes are measured | text |
| `Experiment` | One evaluation setup: method(s), data, metric, baselines | where |
| `Claim` | What the paper asserts | where; kind (`assertion` or `result`) |
| `Evidence` | What supports or challenges a claim: a number, an ablation, a failure case | where; kind; conf |
| `Limitation` | Where applicability or evidence is restricted | where (authors' or `[inference]`) |

`kind`: `assertion` = the authors say so; `result` = an experimental outcome you can point to (a table cell, a figure, an ablation). `conf` (`high` / `medium` / `low`) is the extraction confidence: how sure you are the row says what the source says, not how true the claim is.

## 3. Relations

Each row is a typed signature; the same name may appear with several signatures. `Paper` means a target written `paper:<paper-id>`.

| Relation | From | To | Meaning |
|---|---|---|---|
| `addresses` | Method | Problem | the method is proposed for this problem |
| `uses` | Method | Mechanism | the method relies on this mechanism |
| `requires` | Method | Assumption | the method needs this to hold |
| `relaxes` | Method | Assumption | the method removes an assumption earlier work needed |
| `respects` | Method | Constraint | the method works within this constraint |
| `constrained-by` | Problem | Constraint | the problem statement includes this limit |
| `has-limitation` | Method | Limitation | stated or found limit of the method |
| `evaluates` | Experiment | Method | the experiment tests the method |
| `compares-against` | Experiment | Method | baseline in the experiment |
| `uses` | Experiment | Dataset | the experiment runs on this data or environment |
| `measured-by` | Experiment | Metric | outcome measure |
| `produces` | Experiment | Evidence | the experiment yields this evidence |
| `supports` | Evidence | Claim | evidence for the claim |
| `challenges` | Evidence | Claim | evidence against, or a scope restriction |
| `about` | Claim | Method | the claim concerns the method |
| `about` | Claim | Problem | the claim concerns the problem |
| `about` | Claim | Mechanism | the claim concerns why something works |
| `builds-on` | Method | Paper | the paper says its method derives from that paper (cite the sentence) |
| `contrasts-with` | Method | Paper | the paper positions itself against that paper |

`builds-on` and `contrasts-with` are the only evidence of **influence** the atlas accepts. Without one, a later paper merely came after an earlier one.

## 4. Facet dimensions

Every paper can carry several values in each facet; facets overlap by design. Facet values must be concepts (§5) whose *Facets* column lists the dimension.

| Facet | Question it answers | Example value |
|---|---|---|
| `domain` | Where is it applied? | `robotics` |
| `problem` | What structural problem is solved? | `planning-under-uncertainty` |
| `technique` | What method family or mechanism? | `model-based-search` |
| `setting` | Under which learning or data regime? | `offline` |
| `constraint` | What limits the solution? | `limited-interaction-budget` |

## 5. Concepts

Controlled names. Lowercase, hyphenated, stable. *Type* is the entity type a card row must have to use the concept (`Facet` = facet value only). *Aliases* are other communities' words for the same thing; they drive prior-art searches, so collect them generously.

The seed rows come from the worked example in [transfer.md](transfer.md). Keep, rename or retire them at setup.

| Concept | Type | Facets | Definition | Aliases | Since |
|---|---|---|---|---|---|
| `budgeted-information-acquisition` | Problem | problem | choose which costly observations or actions to take next so as to reduce the uncertainty that matters for a decision, under a budget; roles: state of knowledge, available actions, action cost, benefit, selection policy, stopping rule | active learning; Bayesian experimental design; optimal experimental design; value of information; adaptive sampling; active search; information-directed sampling | v1 |
| `planning-under-uncertainty` | Problem | problem | choose a sequence of actions when outcomes or state are uncertain | POMDP planning; decision-making under uncertainty; belief-space planning | v1 |
| `acquisition-function` | Mechanism | technique | score candidate queries or actions by expected utility, pick the best | query strategy; selection criterion; acquisition rule; utility function | v1 |
| `expected-information-gain` | Mechanism | technique | utility = expected reduction in uncertainty about a target quantity | mutual-information acquisition; BALD; EIG; entropy search | v1 |
| `model-based-search` | Method | technique | plan by searching over a learned or given model of outcomes | MCTS with a learned model; model-predictive planning | v1 |
| `calibrated-uncertainty-available` | Assumption | — | the model's uncertainty is good enough to rank candidate actions | well-calibrated posterior; reliable epistemic uncertainty | v1 |
| `reliable-oracle` | Assumption | — | each query returns a correct, stable answer | noiseless labels; trusted annotator | v1 |
| `independent-observations` | Assumption | — | observations do not repeat the same underlying evidence | i.i.d. queries; non-redundant samples | v1 |
| `fixed-target-quantity` | Assumption | — | what we are uncertain about does not change as information arrives | fixed hypothesis space; stationary objective | v1 |
| `limited-interaction-budget` | Constraint | constraint | only a small number of costly queries, trials or interactions are allowed | low budget; few-shot interaction; expensive evaluations | v1 |
| `heterogeneous-action-cost` | Constraint | constraint | actions differ in cost and the cost matters | cost-sensitive acquisition; cost-aware selection | v1 |
| `offline` | Facet | setting | learn from a fixed dataset, no interaction during training | batch RL; offline RL | v1 |
| `online` | Facet | setting | learn while interacting | interactive learning | v1 |
| `robotics` | Facet | domain | physical or simulated robots | — | v1 |
| `nlp` | Facet | domain | natural-language processing | computational linguistics | v1 |
| `research-agents` | Facet | domain | agents that read, search, run experiments or use tools to answer research questions | AI scientist; deep-research agents; tool-using agents | v1 |

## 6. Extending the ontology

Extend when extraction fails, not in advance. The loop:

1. **Notice.** A card has something important that no type, relation or concept expresses: you are writing the same free-text phrase in several cards, or a concept is too coarse to separate papers that clearly differ. Record it in the card's *Ontology gaps* section and in the field's `log.md` under *Extraction failures*.
2. **Check coverage.** Can an existing concept express it, possibly with an alias? Is it a value (a concept) rather than a new type or relation? Prefer, in order: a new alias < a new concept < a new relation signature < a new entity type.
3. **Propose.** Write the proposal in §7 with: the name, the definition, two or more cards that need it, and the existing concept it is closest to and why that one is not enough.
4. **Decide with the user.** Accepted changes bump `version:` for new types or relations, or for any rename or split; new concepts and aliases do not bump it. Add the row with `Since` = the version.
5. **Migrate.** `atlas.py check` flags cards written under an older version. Re-check those cards for the changed part only. A split concept needs every card that used the old concept re-labelled; keep the old row with `retired → <new names>` in its definition rather than deleting it.

Never add a concept silently from inside a card.

## 7. Proposed changes

| Proposal | Kind | Cards that need it | Closest existing | Decision |
|---|---|---|---|---|

## 8. Change log

| Date | Version | Change | Reason |
|---|---|---|---|
| | 1 | initial schema | |
