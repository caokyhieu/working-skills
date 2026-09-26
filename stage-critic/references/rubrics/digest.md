# Rubric — digest

Inputs to read: the source itself (`sources/<id>/source.*` or the URL), the official code if linked, `sources/sources.md`.

1. **Read, not remembered.** Does the header state the version digested and the access date, and does *Source completeness* match what was actually available? Any protocol field filled where the stated completeness could not support it is a blocker.
2. **Numbers copied with locations.** Sample 5 numbers in *Reported results*; open the source and check value and location. One wrong number is a blocker.
3. **Claims and support.** Does each intro claim have an experiment named, and is the support grade defensible (single dataset + no variance ≠ `strong`)?
4. **Canonical formulation and purpose–mechanism [TM-2, TM-5].** Is §2b filled with inputs / outputs / objective / constraints / regime in generic terms, and does the mechanism line say *how*, not *that*? A formulation that just restates the title is a major.
5. **Assumptions.** Are implicit assumptions listed (data static? single tenant? labels available? hardware?) and marked `[inference]`?
6. **Weak spots vs limitations.** Are "our critique" items actually new, or restatements of the authors' limitations?
7. **Protocol gaps complete.** For each row of §7 marked unknown, is there a §9 row with where it might be found?
8. **Text vs code.** If code exists, was at least the evaluation script compared to the paper text?
9. **Extension hooks.** Is each hook tied to a numbered weak spot or assumption? Are any of them company-specific (they shouldn't be; that belongs to alignment)?
