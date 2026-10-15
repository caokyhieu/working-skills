# How a field develops: changes, activity and influence

Read before writing the timeline (SKILL.md §6).

## 1. A timeline is not an explanation

Sorting papers by date gives a chronology. Explaining development means naming **what changed** and showing the evidence that one thing led to another.

> "B appeared after A" establishes sequence. "B developed from A" needs a citation in B that says it builds on A, or another explicit statement of influence.

In the atlas, influence is a `builds-on` or `contrasts-with` edge in a card, with the location of the sentence. Every timeline row says `influence: <card, location>` or **sequence only**.

## 2. Change types

Look for these; `atlas.py changes` proposes candidates for the first three from the graph and facets.

| Change | What to look for | Evidence that makes it a finding |
|---|---|---|
| **Assumption relaxed** | an `Assumption` concept that earlier methods `require` and a later method `relaxes` | the later paper states the relaxation and shows it matters (an experiment where the assumption fails) |
| **Method moves into a new domain** | a technique concept's first appearance in a new domain facet | the later paper cites the origin and says what had to change (adaptation) |
| **Failure motivates a new mechanism** | recurring `Limitation` / `challenges` rows on one mechanism, then papers with a different `Mechanism` for the same problem | the new papers cite the failure as motivation |
| **Evaluation becomes more realistic** | `Dataset` concepts moving from synthetic or toy settings to real or larger ones | the Dataset concept's definition in ontology.md says whether it is synthetic; results are not comparable across the move, so say so |
| **Same performance with less** | comparable results at lower compute, data or interaction cost | matched protocol and a stated budget in both papers |

`changes` writes `atlas/changes.md`. Treat its rows as leads: open both papers, confirm, and only then add the change to the timeline.

## 3. Topic activity

```text
topic share(t) = papers assigned the concept in period t / eligible papers with facets assigned in period t
```

- Eligible = venue-policy papers (`collected_via: policy`) dated in the period under the chosen date basis. Citation-followed papers are excluded: they have no known denominator.
- Facets overlap, so shares need not sum to 1.
- `atlas.py share --field F --dim problem --period year --date first_public` prints n per period, facet coverage, and the venue mix. Report all three with any share.

Things that create false trends:

- **The collection changed**, not the field: a venue added to the policy, a new track, a listing without abstracts in one year. `share` warns when the venue mix changes across periods.
- **Incomplete indexing**: the most recent period is missing papers whose proceedings are not out.
- **Renamed concepts**: the field changed its word for the same thing. Check ontology aliases before calling something new or dead.
- **Small n**: under 30 assigned papers per period, a change is a lead.
- **Mixed date bases**: arXiv v1 and proceedings dates can be a year apart. Use one basis per analysis and say which. First-public dates show when ideas appeared; proceedings dates show when a venue endorsed them.

## 4. Backtesting a trend claim

A trend method is trustworthy if it would have been right before the outcome was known. Pick a cutoff, use only papers public by then, and compare what the method said with what happened later:

```sh
atlas.py share --field F --dim technique --cutoff 2024-06-30
```

Record the result in `playbook.md` → Evaluation history (references/learning.md §2).

## 5. Writing the timeline

One row per change: when (period), the change in one line, its type, the before and after cards, the influence evidence or "sequence only", and confidence. Prefer five well-evidenced changes to twenty dated papers.
