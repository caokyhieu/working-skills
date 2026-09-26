# Thinking models behind the workflow

Each rule in the research skills is borrowed from a published model of how people (or agents) find analogies, judge arguments, and correct themselves. This file condenses each model into the rule the skills apply, so a skill can cite the model instead of restating it. Read the paper when a rule seems wrong for a case; the rule is the compressed form, not the source of truth.

Rules are tagged `TM-n` and cited from the skills as `[TM-n]`.

## A. Finding the ground point between a paper and a company problem

### TM-1 Structure mapping — match relations, not vocabulary

Gentner (1983), *Structure-Mapping: A Theoretical Framework for Analogy*, Cognitive Science 7(2). doi:10.1207/s15516709cog0702_3

An analogy is a mapping of **relations** between two domains (objective, constraint, what-limits-what), not a match on attributes (same words, same field, same model family). Surface similarity predicts *retrieval*; structural similarity predicts *usefulness*.

**Rule.** A match between a paper and a company problem is valid only when it names the shared relational structure: the same objective under the same kind of constraint, with the same thing being the bottleneck. Shared vocabulary ("both use transformers", "both are about search") is not a match. The relevance chain in idea-alignment and screening exists to force this.

### TM-2 Purpose–mechanism decomposition

Hope, Chan, Kittur, Shahaf (KDD 2017), *Accelerating Innovation Through Analogy Mining*. arXiv:1706.05585
Chan, Chang, Hope, Shahaf, Kittur (CSCW 2018), *SOLVENT: A Mixed Initiative System for Finding Analogies between Research Papers*. doi:10.1145/3274300

Represent every item as **purpose** (what it is for) and **mechanism** (how it does it). Useful analogies come from same-purpose / different-mechanism (a new way to solve our problem) and same-mechanism / different-purpose (our tool applied elsewhere). SOLVENT annotates papers with *background / purpose / mechanism / findings* and shows that purpose–mechanism matching finds cross-domain analogies keyword search misses.

**Rule.** Digests carry a purpose–mechanism block. The research map carries a purpose–mechanism block per company problem. Matching compares purpose to purpose and mechanism to mechanism, and labels each match `same-purpose` or `same-mechanism`.

### TM-3 Intermediate abstraction is the sweet spot

Kang, Qian, Hope, Shahaf, Chan, Kittur (TOCHI 2022), *Augmenting Scientific Creativity with an Analogical Search Engine*. arXiv:2205.15476

An end-to-end analogical search engine over papers. The key empirical result: ideation success was mediated by an **intermediate** level of match on the problem abstraction. Exact matches yielded nothing new; very distant matches were unusable; partial matches on the abstracted problem were the productive band.

**Rule.** Do not filter for "same topic". Score transfer distance (`direct`, `adjacent-field`, `analogy`) and keep the middle. A `direct` match is a reproduction candidate, not a research direction; an `analogy` match needs a stated bridging concept [TM-4] or it is dropped.

### TM-4 Literature-based discovery — search for the bridge

Swanson (1986), *Undiscovered Public Knowledge*, Library Quarterly 56(2); Swanson (1986), *Fish Oil, Raynaud's Syndrome, and Undiscovered Public Knowledge*, Perspectives in Biology and Medicine 30(1).

Two literatures, A and C, may never cite each other yet be connected through a concept B that appears in both. The discovery is finding B.

**Rule.** When a paper is not directly about a company problem, look for the bridging concept: a quantity, structure, or constraint both share (e.g. "cardinality estimation" ↔ *density estimation* ↔ "learned sketches"; "KV-cache eviction" ↔ *buffer replacement* ↔ "page cache policies"). Record B explicitly; the ground-point statement must name it.

### TM-5 Abstract first, then reason

Zheng et al. (2023), *Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models*. arXiv:2310.06117
Yasunaga et al. (2023), *Large Language Models as Analogical Reasoners*. arXiv:2310.01714
Pólya (1945), *How to Solve It*; Altshuller, TRIZ (specific problem → abstract problem → abstract solution → specific solution).

Reasoning improves when the model first restates the problem at the level of principle, then maps back.

**Rule.** Every source and every company problem gets a **canonical formulation** — given *inputs*, produce *outputs*, optimising *objective*, subject to *constraints*, in *regime* (scale, dynamics) — before any matching is attempted. The formulation is what gets compared, not the abstract or the pain-point text.

## B. Judging whether a match or a proposal holds

### TM-6 Toulmin argument structure

Toulmin (1958), *The Uses of Argument*.

An argument is claim, grounds (the evidence), warrant (why the grounds support the claim), backing (why the warrant is acceptable), qualifier (how strong), and rebuttal (the conditions under which it fails).

**Rule.** A ground-point statement and a hypothesis are written in Toulmin form. The critic attacks the *warrant* first (is the shared structure real?) and must supply a *rebuttal* (under what company condition does the transfer fail?). A claim without a warrant is not a match.

### TM-7 Heilmeier Catechism

DARPA, George Heilmeier (1970s). https://www.darpa.mil/about/heilmeier-catechism

Eight questions for any proposal: What are you trying to do (no jargon)? How is it done today and what are the limits? What is new and why will it succeed? Who cares, and what difference will it make? What are the risks? How much will it cost? How long will it take? What are the mid-term and final "exams"?

**Rule.** `proposal.md` answers all eight. The `proposed` critic checks that "what is new" is supported by the novelty search, that "who cares" cites the research map, and that the mid-term exam is the early kill test.

### TM-8 Technology readiness

NASA Technology Readiness Levels (TRL 1–9).

**Rule.** The research map states the acceptable TRL band per problem (e.g. "TRL 3–5: validated in a lab benchmark, not deployed"). The scout records an estimated TRL per source, so "on-direction but ten years early" and "on-direction and ready to prototype" are distinguished instead of both scoring `fit 5`.

### TM-9 Pairwise ranking beats absolute scores

Gottweis et al. (2025), *Towards an AI co-scientist*. arXiv:2502.18864

Hypotheses are ranked by an Elo tournament of pairwise comparisons with written debate, then evolved; a meta-review agent synthesises the recurring objections. Pairwise judgements are more consistent than absolute rubric scores.

**Rule.** Rubric scores (1–5) screen; the final shortlist and the alignment ranking are settled by pairwise comparison of the top candidates, with the reason each pair was decided recorded. The critic's meta-review feeds the calibration file.

## C. Critique and self-correction

### TM-10 Self-critique needs external grounding

Huang et al. (ICLR 2024), *Large Language Models Cannot Self-Correct Reasoning Yet*. arXiv:2310.01798

Models asked to check their own reasoning without new information do not improve and often get worse. Improvements reported for self-correction come from external signals (tools, oracles, retrieved evidence).

**Rule.** The stage critic never judges an output in isolation. It reads the *inputs* (source text, digest, research map, company context) and checks the output against them. Every objection cites a location in an input or the output. "Reads well" is not a verdict.

### TM-11 Separate contexts, independent judgement

Du et al. (2023), *Improving Factuality and Reasoning in Language Models through Multiagent Debate*. arXiv:2305.14325
Madaan et al. (2023), *Self-Refine*. arXiv:2303.17651; Shinn et al. (2023), *Reflexion*. arXiv:2303.11366

Independent agents that critique each other beat one agent reflecting on itself; textual feedback stored between rounds lets the next attempt improve.

**Rule.** The critic runs in a fresh context (subagent, or a separate session), ideally a different model, with the rubric and the files but not the writer's chat. Its written review is the `why` list for the writer's update-mode re-run. Bounded rounds (default 2) to avoid loops.

### TM-12 Critique against a written constitution

Bai et al. (2022), *Constitutional AI: Harmlessness from AI Feedback*. arXiv:2212.08073

Critique and revision against an explicit list of principles is more consistent than free-form critique.

**Rule.** Each stage has a rubric file in `stage-critic/references/rubrics/`. The critic answers the rubric's questions in order; it may add objections outside the rubric but must mark them as such.

### TM-13 Specific, located feedback

Liang et al. (2023), *Can large language models provide useful feedback on research papers?* arXiv:2310.01783

LLM reviews overlap with human reviews about as much as human reviewers overlap with each other, but tend to be generic; specificity rises when the model is required to anchor comments to the text.

**Rule.** Every objection has the form `[file §/line] — what is wrong — what would fix it — blocker | major | minor`. Generic objections ("could be more rigorous") are deleted before the review is returned.

### TM-14 Branch, evaluate, prune

Yao et al. (2023), *Tree of Thoughts*. arXiv:2305.10601

Generate several candidates at each decision point, evaluate each with an explicit value judgement, keep the best, backtrack when none survive.

**Rule.** Alignment produces 3–8 candidate matches and extension produces 4–8 directions before any is refined. A stage that presents a single option without listing rejected alternatives is returned by the critic.

## D. Evidence from research-agent systems

### TM-15 Iterative novelty loop

Wang et al. (2023), *SciMON: Scientific Inspiration Machines Optimized for Novelty*. arXiv:2305.14259
Baek et al. (2024), *ResearchAgent*. arXiv:2404.07738

Generate an idea, retrieve its nearest neighbours in the literature, compare, and revise the idea until it is measurably distinct — rather than a single novelty check at the end.

**Rule.** idea-extension's novelty check runs as a loop: search → closest works → restate the difference → if the difference is only a hyperparameter or dataset swap, revise the direction and search again. Stop after 3 rounds or when the verdict is stable.

### TM-16 LLM ideas: novel, less feasible, low diversity

Si, Yang, Hashimoto (2024), *Can LLMs Generate Novel Research Ideas?* arXiv:2409.04109, and the 2025 follow-up on executing the ideas.

In a blind study with 100+ NLP researchers, LLM-generated ideas were rated more novel but less feasible than human ideas; generated idea sets had low diversity; when executed, the LLM ideas' advantage shrank.

**Rule.** Feasibility and effort carry at least equal weight to novelty in every ranking. Generation must be forced to diversify across extension patterns (no two directions from the same pattern unless justified). The human gate on alignment and proposal stays.

### TM-17 Automated reviewer as a stage gate

Lu et al. (2024), *The AI Scientist*. arXiv:2408.06292; Yamada et al. (2025), *The AI Scientist-v2*. arXiv:2504.08066

An automated reviewer scores each generated paper against a NeurIPS-style form; v2 adds tree search over experiment nodes and a vision model checking figures. The reviewer catches obvious failures but is optimistic, so its verdict is a floor, not a pass.

**Rule.** The critic's `pass` means "no blocker found", not "good". The user gate still decides.

## Where each model is applied

| Stage / skill | Models |
|---|---|
| research-map | TM-2, TM-5, TM-8 |
| source-scout (screening) | TM-1, TM-3, TM-4, TM-8, TM-9 |
| source-digest | TM-2, TM-5 |
| idea-alignment | TM-1 … TM-6, TM-9, TM-14 |
| idea-extension | TM-7, TM-14, TM-15, TM-16 |
| stage-critic | TM-6, TM-10 … TM-14, TM-17 |
| research-poc (orchestrator) | TM-11, TM-17 |
