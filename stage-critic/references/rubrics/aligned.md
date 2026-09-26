# Rubric — alignment

Inputs to read: all `sources/*/digest.md`, `research-map.md`, `company-context.md`, `scouting/calibration.md`.

1. **Relevance chain complete [TM-1].** For each match: paper formulation, sub-problem id, shared structure (objective / constraint / bottleneck), transfer distance, what transfers as-is, what must change. A missing *shared structure* is a blocker.
2. **Structure is real.** Restate the digest's §2b formulation and the map's formulation for the sub-problem. Do the objective **and** the binding constraint correspond? If only the topic corresponds, the match is vocabulary-only: blocker.
3. **Bridging concept named for non-direct matches [TM-4].** Every `adjacent-field` or `analogy` match names the concept B both share. Otherwise major.
4. **Assumption table honest.** For each `unknown` row, could `company-context.md` or `research-map.md` have answered it? If so, major. For each `breaks` row, is the consequence stated (reject or extension seed)?
5. **Ground point in Toulmin form [TM-6].** Claim, grounds (digest §), warrant (why the structure transfers), qualifier. Write the rebuttal yourself: under which company condition does the transfer fail? If the output has no defensible warrant, blocker.
6. **Scores cite sections.** Each score line cites `company-context.md` or `research-map.md`. Uncited scores are major.
7. **Arithmetic and ranking.** Recompute impact × feasibility. If > 3 matches, was the top order settled pairwise with reasons [TM-9]?
8. **Alternatives listed [TM-14].** Are there ≥ 3 candidate matches and a *Rejected* table with reasons? One match and no rejects is a major.
9. **Near-misses and past attempts.** Does any match hit a near-miss in the map, a `calibration.md` rule, a funded initiative, or a failed past attempt without saying why it differs?
10. **Direction synthesis.** If several digests were read, is there a *Direction synthesis* section (where the field is moving vs where the company sits)? Missing when ≥ 3 digests: major.
11. **Confidential terms.** Nothing in the file is destined for a public query.
