# Rubric — proposal

Inputs to read: `ideas/alignment.md` (selected match), `sources/*/digest.md` (§7 protocol, §8 results, variance), `research-map.md` (win definition), `company-context.md §6`.

1. **Heilmeier answered [TM-7].** All eight questions present in §0 without jargon. Missing "how is it done today" or "who cares" is a major.
2. **Directions before choice [TM-14, TM-16].** ≥ 4 directions listed, from ≥ 3 different extension patterns, with a screen result each. A single direction is a blocker.
3. **Novelty searched, not asserted [TM-15].** Queries, sources, dates and ≥ 3 closest works with concrete differences are recorded. Verdict `novel` with < 3 source kinds searched, or with no citation-graph search, is a blocker. `unverified` presented as anything else is a blocker.
4. **Difference is more than a swap.** For each closest work, is the stated difference a mechanism change, or a hyperparameter / dataset swap dressed up? If a reviewer could say "X applied to Y", is that acknowledged as `incremental`?
5. **Hypothesis fully specified.** X, M, Z, B, C, Y all present; M is the digest's metric definition; Z is the paper's strongest baseline, not a weak one.
6. **Threshold above noise.** Y ≥ the seed variance reported in the digest (or 2× std if reported), and tied to `company-context §6` "minimum improvement that would change a decision". Y below noise is a blocker.
7. **Falsifier would actually reject.** Is there a concrete result that the authors would accept as refuting the hypothesis? "If it doesn't improve" is not concrete. Missing or vague: blocker.
8. **Mechanism ablation.** Does at least one ablation remove the proposed mechanism's key ingredient so that a null result would show *why* it works or doesn't?
9. **Compute and kill test.** Estimated compute range given; the cheapest early test named and cheap (< 10 % of the budget).
10. **Company relevance cites the map.** Which outcome changes which decision, citing `research-map.md` R*n* and `company-context §6`.
11. **Rebuttal [TM-6].** Write it: the company condition (data, scale, constraint) under which the extension's advantage disappears. If the proposal already covers it in risks, say so.
