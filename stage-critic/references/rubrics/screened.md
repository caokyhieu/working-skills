# Rubric — scouting shortlist

Inputs to read: `research-map.md`, `scouting/calibration.md`, `scouting/runs/<date>.md`, `screened.jsonl` records for this run (`scout_log.py candidates`), and the abstract / README / post of each `keep`.

1. **Relevance chain present.** Does every `keep` name a sub-problem id (R*n*.x), the shared structure, and the transfer distance? A `keep` with a topic label only is a blocker.
2. **Structure, not vocabulary [TM-1].** For each `keep`, restate the source's canonical formulation from its abstract and compare it with the sub-problem's formulation in the research map. Does the objective or the binding constraint actually match? Name any that match only on words.
3. **Transfer distance honest [TM-3].** Is anything marked `direct` that is really `adjacent-field`, or `analogy` without a bridging concept?
4. **Near-miss check.** Does any `keep` match a near-miss pattern in the research map or a rule in `calibration.md`?
5. **Anchors used.** Did the run expand from the anchor sources (citation graph), or only from queries? A query-only run on a problem with anchors is a major.
6. **Evidence and TRL.** Is the evidence level consistent with the source type (a vendor post marked `peer-reviewed` is a blocker)? Is the TRL estimate within the problem's wanted band, and if not, is that stated?
7. **Drops.** Sample 5 drops. Is any a plausible `maybe` given the map's bridging concepts? (The critic looks for false negatives too.)
8. **Diversity [TM-16].** Are the keeps spread over sub-problems and mechanisms, or 8 variants of one idea?
9. **Pairwise ranking [TM-9].** If more than 5 keeps, was the final order settled by pairwise comparison with reasons, not by fit score alone?
