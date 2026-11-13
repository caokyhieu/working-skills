---
paper_id: <id exactly as in papers.jsonl>
field: <field-id>
read: full            # full | partial | abstract  (abstract → evidence: claim-only)
evidence: mixed       # strong | mixed | weak | claim-only  — the evidence verdict below
ontology_version: 1
domain: [<concept>]
problem: [<concept>]
technique: [<concept>]
setting: [<concept>]
constraint: [<concept>]
---

# <paper title>

**Appearances:** <ICML 2025 oral; NeurIPS 2024 workshop X>  **First public:** <date, source>
**Links:** paper · pdf · code (<official | claimed | none>, where the link was found)
**Read:** <sections read; appendix yes/no>

## 1. In one paragraph

Problem in canonical form (inputs → outputs, objective, constraints, regime), the method, and the mechanism: why it should help, in our words. No field nouns in the first sentence.

## 2. Entities

One row per thing. `concept` = an ontology concept name or blank (blank structural rows cannot join bridges; propose a concept in §4 if one is missing). `where` = §, Table, Fig., page or line; `[inference]` when it is ours. Claim and Evidence rows need `kind` (assertion | result). `conf` = how sure the row reflects the source.

| id | type | concept | text | where | kind | conf |
|---|---|---|---|---|---|---|
| E1 | Problem | | | §1 | | high |
| E2 | Method | | | §3 | | high |
| E3 | Mechanism | | | §3.2 | | medium |
| E4 | Assumption | | | §3 / [inference] | | medium |
| E5 | Experiment | | | §5.1 | | high |
| E6 | Claim | | | abstract | assertion | high |
| E7 | Evidence | | <number, baseline, benchmark, seeds> | Table 2 | result | high |
| E8 | Limitation | | | §7 | | high |

## 3. Relations

`to` may be `paper:<paper-id>` for `builds-on` / `contrasts-with`; then `where` must quote or locate the sentence that says so.

| from | relation | to | where |
|---|---|---|---|
| E2 | addresses | E1 | |
| E2 | uses | E3 | |
| E2 | requires | E4 | |
| E5 | evaluates | E2 | |
| E5 | produces | E7 | |
| E7 | supports | E6 | |
| E6 | about | E2 | |
| E2 | has-limitation | E8 | |

## 4. Ontology gaps

What this paper says that the ontology cannot express. Each line also goes to the field's `log.md` → Extraction failures.

-

## 5. Evidence verdict

- Ablation isolating the mechanism: yes (<where>) | no
- Baselines tuned and compute-matched: yes | partly | no (<what is off>)
- Seeds / variance reported: yes | no
- Independent replication known: <paper-id> | none known
- Verdict (`evidence:` above): <strong | mixed | weak | claim-only>, because <one line>

## 6. Transfer notes  `[inference]`

- The structure this method exploits, stated without the domain:
- Assumptions a new domain would have to satisfy:
- Domains where the same problem concept appears (from `bridges.md`):
