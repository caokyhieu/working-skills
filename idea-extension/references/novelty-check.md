# Novelty check

## Decompose the idea

Write the direction as a set of elements: **problem** × **core technique** × **key modification** × **setting/constraint**. Prior art that matches all elements means `already done`. A match on three elements is close work that must be discussed.

## Queries

For each element pair, create queries using synonyms from both communities (for example "learned index" / "learned cardinality estimation" / "ML for query optimization"; "KV cache compression" / "attention sparsification"). Include:

- the paper's own terminology
- terminology from adjacent fields (ML ↔ DB ↔ IR ↔ systems)
- the modification described functionally, without jargon

## Sources (search at least 3 kinds)

1. **Scholarly indexes:** Semantic Scholar, Google Scholar, DBLP, OpenReview, ACL Anthology
2. **Preprints:** arXiv (last 24 months at least; sort by date)
3. **Citation graph:** papers citing the source paper (Semantic Scholar / Google Scholar "cited by"), plus the source paper's related work
4. **Venues:** recent proceedings of NeurIPS, ICML, ICLR, ACL/EMNLP, KDD, SIGMOD, VLDB, ICDE, CIDR, OSDI/SOSP, MLSys, as relevant
5. **Code and practice:** GitHub, major library changelogs and engineering blogs. An idea that ships in a popular open-source system is not novel even if unpublished.
6. **Patents** (when the proposal may lead to a patent): Google Patents

Read at least the abstract and method section of each close hit; don't judge from titles.

## Record

| Query | Source | Date | Hits reviewed |
|---|---|---|---|

| Closest work | Venue/year | Elements matched | Concrete difference | Threat level (high/med/low) |
|---|---|---|---|---|

Threat is **high** if a reviewer could reasonably say "this is X applied to Y". Explain why the difference still matters, or downgrade the verdict.

## Loop [TM-15]

Round 1: search all source kinds, list the closest works, write the one-sentence difference. If a reviewer could say "this is X applied to Y" or the difference is a hyperparameter / dataset / scale change, revise the direction so the *mechanism* differs (change what is learned, what is bounded, what is adapted — see extension-patterns) and run round 2 with the revised elements. Stop after round 3 or when two consecutive rounds give the same verdict. Record every round; a revised direction keeps its number with a suffix (D2 → D2').

## Verdict rules

- `already done`: any work matches all elements, or the difference is only a hyperparameter or a dataset swap.
- `incremental`: close work exists; the difference is a real technical change but a reviewer could see it as a combination of known pieces.
- `novel`: no close work covers the core modification in this setting after searching all required source types.
- `unverified`: the search could not be performed.

Novelty checks go out of date. Record the search date and repeat the arXiv and citation-graph searches before writing the deck or any external submission.
