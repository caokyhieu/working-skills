# Working Skills

Agent skills that turn a technical idea into a company proposal backed by evidence: map the company's priorities to research problems, scout and read top-tier ML, AI or database papers, open-source projects and technical blog posts, align ideas with the business by problem structure rather than keywords, propose a novel extension, benchmark it, plot the results and present a proof of concept (POC) in the team's slide style. Every stage output is critiqued by an independent stage critic before you see it. A separate track turns the last twelve months of published work into a poster-style literature-review deck, and another catches you up on the new ideas at a conference edition.

The matching and critique rules are borrowed from published models of analogy, argument and self-correction (structure mapping, purpose–mechanism analogy search, Toulmin, the Heilmeier catechism, grounded critique); they are condensed in [research-poc/references/thinking-models.md](research-poc/references/thinking-models.md).

The skills are plain `SKILL.md` instructions plus references, templates and scripts. They work with **Claude Code** and **Codex** (CLI, app or IDE extension).

## Contents

- [The skills](#the-skills)
- [Requirements](#requirements)
- [Install](#install)
- [Quick start: run the research workflow](#quick-start-run-the-research-workflow)
- [How matching and critique work](#how-matching-and-critique-work)
- [No idea yet? Scout for sources](#no-idea-yet-scout-for-sources)
- [Go back and revise a step](#go-back-and-revise-a-step)
- [Use a skill on its own](#use-a-skill-on-its-own)
- [Review recent papers as a poster deck](#review-recent-papers-as-a-poster-deck)
- [Catch up on a conference](#catch-up-on-a-conference)
- [Build decks in the team theme](#build-decks-in-the-team-theme)
- [Workspace layout](#workspace-layout)
- [Script reference](#script-reference)
- [Share, update and keep confidential material private](#share-update-and-keep-confidential-material-private)
- [Troubleshooting](#troubleshooting)

## The skills

| Skill | Workflow stage | What it does | Main output |
|---|---|---|---|
| [research-map](research-map/SKILL.md) | once, before scouting | Translates each company priority into a research problem: canonical formulation, purpose and mechanism, sub-problems, bridging concepts to adjacent fields, anchor papers, near-misses, acceptable transfer distance | `research-map.md` |
| [source-scout](source-scout/SKILL.md) | before the workflow | Expands the citation graph from the map's anchors and queries by formulation; screens every hit with a relevance chain (sub-problem, shared structure, distance); learns from your overrules | `scouting/candidates.md`, `screened.jsonl`, `calibration.md` |
| [research-poc](research-poc/SKILL.md) | orchestrator | Creates the idea workspace, tracks state, runs stages in order, runs the critic after each, goes back when asked | `poc/<idea>/STATUS.md`, `.poc/` state |
| [source-digest](source-digest/SKILL.md) | `digest` | Reads a paper, repo or blog post; extracts purpose, mechanism and canonical formulation, key insight, weak spots, evidence level, exact benchmark protocol and reported results | `sources/<source-id>/digest.md` |
| [idea-alignment](idea-alignment/SKILL.md) | `aligned` | Matches sources to research-map problems by structure (relevance chain, bridging concept), writes each ground point as a rebuttable argument, scores, ranks pairwise and synthesises directions | `ideas/alignment.md` |
| [idea-extension](idea-extension/SKILL.md) | `proposed` | Proposes diversified extensions, runs an iterative novelty loop, answers the Heilmeier catechism, sets a hypothesis that could be proven wrong | `ideas/proposal.md` |
| [stage-critic](stage-critic/SKILL.md) | after every stage | Reviews a stage output against its rubric and its inputs in a fresh context; located, graded objections; `pass` / `revise` / `block` | `poc/<idea>/reviews/<stage>-<run>.md` |
| [bench-setup](bench-setup/SKILL.md) | `reproduced`, `extended` | Reproduces the source's baseline first, then runs the extension fairly across multiple seeds | `experiments/`, `results/runs.jsonl` |
| [result-plots](result-plots/SKILL.md) | `plotted` | Draws charts with confidence intervals and tests the hypothesis against its threshold | `figures/`, `results/summary.md` |
| [insight-ppt](insight-ppt/SKILL.md) | `deck` | Builds an editable proposal deck in the team theme | `deck/*.pptx` |
| [conference-radar](conference-radar/SKILL.md) | standalone | Fetches a venue edition's accepted papers (ICLR, ICML, NeurIPS, CVPR, ACL, EMNLP, …, or "accepted at" arXiv preprints), finds rising terms against the previous edition, clusters papers by shared mechanism, reads the representatives and proposes idea seeds | `radar/<id>/radar.md`, `cards/` |
| [lit-review-deck](lit-review-deck/SKILL.md) | standalone | Reviews the last 12 months of papers, blogs and releases and builds a poster-style deck: one block per paper, figure captured from the original | `reviews/<id>/deck/*.pptx` |

```text
research-map ─▶ source-scout ──▶ source-digest ─▶ idea-alignment ─▶ idea-extension ─▶ bench-setup ─▶ bench-setup ─▶ result-plots ─▶ insight-ppt
  (once)         (optional)         digest 🔍        aligned 🔍✋       proposed 🔍✋      reproduced 🔍✋   extended 🔍     plotted 🔍       deck 🔍✋
                                                                    ▲                                                                       │
                                                                    └──────────── reopen any stage; later stages re-run only if affected ───┘
🔍 = stage-critic reviews the output (revise up to twice, or block)   ✋ = waits for your approval, with the review attached
```

## Requirements

- Claude Code or Codex, Git, and Python 3.9+.
- Python packages, only for the scripts you use:

| Script | Needs |
|---|---|
| `research-poc/scripts/poc_state.py` | standard library only |
| `source-scout/scripts/scout_log.py` | standard library only |
| `source-scout/scripts/scholar_search.py` | standard library only (network access to api.semanticscholar.org) |
| `bench-setup/scripts/check_results.py` | standard library only |
| `result-plots/scripts/plot_results.py` | `matplotlib` |
| `insight-ppt/scripts/team_deck.py` | `python-pptx` |
| `conference-radar/scripts/radar.py` | standard library only (network access to the venue sites and arXiv; uses `curl` when present) |
| `lit-review-deck/scripts/poster_deck.py` | `python-pptx` |
| `lit-review-deck/scripts/figure_grab.py` | `pymupdf`, or poppler-utils + `Pillow` |
| `insight-ppt/scripts/make_team_template.py` | `python-pptx`, `Pillow` |

```sh
python -m venv .venv && . .venv/bin/activate
pip install matplotlib python-pptx Pillow pymupdf
```

- Optional: LibreOffice (`soffice`) to render decks to PDF or images for a visual check.
- The deck font is **Microsoft YaHei**. Previews on machines without it use a wider substitute font.

## Install

Skills are copied into the project where you work. Claude Code loads project skills from `.claude/skills/`; Codex loads them from `.agents/skills/`.

```sh
git clone https://github.com/caokyhieu/working-skills.git
cd working-skills
PROJECT_DIR="/absolute/path/to/your-project"
SKILLS="research-poc research-map stage-critic source-scout source-digest idea-alignment idea-extension bench-setup result-plots insight-ppt lit-review-deck conference-radar"
```

**Claude Code**

```sh
mkdir -p "$PROJECT_DIR/.claude/skills"
for s in $SKILLS; do cp -R "$s" "$PROJECT_DIR/.claude/skills/"; done
```

**Codex**

```sh
mkdir -p "$PROJECT_DIR/.agents/skills"
for s in $SKILLS; do cp -R "$s" "$PROJECT_DIR/.agents/skills/"; done
```

Notes:

- Copy **whole folders**. The instructions depend on each folder's `references/`, `templates/`, `scripts/` and `assets/`.
- Always install `research-poc` with any of the research skills; they follow its workspace contract. Install `research-map` and `stage-critic` with it: alignment and scouting refuse to run without a confirmed research map, and the orchestrator runs the critic after every stage. To use only the deck skill, install `insight-ppt` by itself. `lit-review-deck` needs `insight-ppt` beside it for the team theme, and uses `source-scout` when it is installed. `conference-radar` runs on its own.
- `agents/openai.yaml` is Codex metadata; Claude Code ignores it.
- Restart the agent after installing. In Claude Code, skills appear as `/research-poc`, `/research-map`, `/source-scout`, `/source-digest`, `/stage-critic`, and so on. In Codex, type `/skills` or mention `$research-poc`.

## Quick start: run the research workflow

The examples use Claude Code syntax (`/skill`). In Codex, write `$skill` instead.

### 1. Describe your company once

Copy the template to your project root and fill it in yourself. The agents read it but never invent its contents; mark unknown items `UNKNOWN`.

```sh
cp .claude/skills/research-poc/templates/company-context.md company-context.md   # Codex: .agents/skills/...
```

It covers strategic priorities, products and pain points, data assets, tech stack, constraints (latency, cost, privacy), what counts as a win, and past internal work. Keep it out of public tools; it is confidential.

### 1b. Build the research map with the agent

```text
/research-map Build research-map.md from company-context.md. Propose one research problem per priority and confirm each with me.
```

The map is what stops the agent matching on vocabulary. For each priority it holds a **canonical formulation** (inputs → outputs, objective, constraints, regime, in generic terms), the purpose and the mechanisms already tried, sub-problems, **bridging concepts** to adjacent fields, the acceptable transfer distance, 3–10 **anchor papers** that define "on-direction", and **near-misses** — things that sound related and are not, with the reason. Give it your anchors and your near-misses; those two tables do most of the work. Re-run it when priorities change; alignment becomes stale automatically.

### 2. Start an idea

From a source you already have (a paper, a GitHub repo or a blog post):

```text
/research-poc Start a new idea "learned-cardinality" from this paper:
https://arxiv.org/abs/XXXX.XXXXX (SIGMOD 2026). Our focus is the Spark optimizer.
```

The agent runs `poc_state.py poc/learned-cardinality init`, which creates the workspace, `STATUS.md` and the saved state, then starts the first stage. No source in mind? See [No idea yet? Scout for sources](#no-idea-yet-scout-for-sources).

### 3. Let it run, and answer at the approval points

```text
/research-poc Continue the workflow for learned-cardinality.
```

The orchestrator runs one stage at a time, hands each to its skill, then runs **stage-critic** on the output in a separate context. The critic reads the output *and* the stage's inputs, answers a per-stage rubric, and returns located objections graded blocker / major / minor with a verdict: `pass`, `revise` (the owner skill fixes and is reviewed again, at most twice) or `block` (stops for you). The orchestrator then records the result and, at a gate, shows you the review next to the question:

| Stage | Question you answer |
|---|---|
| `aligned` | Which company match(es) should go forward? |
| `proposed` | Approve the hypothesis, threshold, falsification criterion and experiment plan? |
| `reproduced` | Accept the reproduction verdict (and any caveats) before running the extension? |
| `deck` | Approve the deck? |

It also stops before expensive benchmark runs to confirm the compute estimate, whenever a stage fails, and whenever the critic blocks. Reply in plain language ("approve, go with M1", "use 5 seeds, not 3") and say "continue" to resume. Approvals are tied to the exact file content: if an approved file changes later, it needs approval again, and a gated stage cannot be approved without a critic review of its current output.

### 4. Check where things stand at any time

```text
/research-poc What's the status of learned-cardinality?
```

Or run the script yourself:

```sh
python .claude/skills/research-poc/scripts/poc_state.py poc/learned-cardinality status
```

```text
| Stage      | Owner          | Status            | Verdict | Review | Runs | Why / blocked by                              |
| digest     | source-digest  | done              | passed  | pass   | 1    |                                               |
| aligned    | idea-alignment | done              | passed  | pass   | 2    |                                               |
| proposed   | idea-extension | awaiting_approval | passed  | pass   | 2    |                                               |
| reproduced | bench-setup    | stale             | passed  |        | 1    | input changed ideas/proposal.md; waiting on proposed |
...
Next actions (in dependency order):
- proposed: ask the user: Approve the hypothesis, threshold, falsification criterion and experiment plan?
```

`STATUS.md` in the idea folder shows the same table, plus a Decisions section for the reasons behind your choices.

## How matching and critique work

The two failure modes this layout is built against are *finding unrelated papers* and *missing why a paper matters when it is not obviously about the company's domain*. Both come from matching on words. The fix is three layers, each borrowed from a published model (see [thinking-models.md](research-poc/references/thinking-models.md), cited as `[TM-n]` in the skills):

1. **Abstract both sides first** `[TM-5]`. Every digest carries a *canonical formulation* (inputs → outputs, objective, constraints, regime) and a purpose–mechanism line `[TM-2]`; the research map carries the same for every company problem. Matching compares formulations, never abstracts to pain-point prose.
2. **Require a relevance chain** `[TM-1, TM-3, TM-4]`. A source is kept, and a match is valid, only when the agent writes: which sub-problem, what *relational* structure is shared (same objective, same binding constraint, same bottleneck quantity), the transfer distance (`direct` / `adjacent-field` / `analogy`), and — for anything not direct — the *bridging concept* both share without naming each other. Vocabulary overlap is an explicit rejection reason. Intermediate distance is preferred: exact matches are reproductions, not research directions. The scouting script refuses a `keep` without the chain.
3. **Argue, then attack** `[TM-6, TM-10 … TM-13]`. Each match's ground point is written as claim → grounds → warrant → qualifier → rebuttal. The stage critic, in a fresh context with the inputs, attacks the warrant, writes the rebuttal, and returns located objections. Its `pass` means "no blocker found", not "good"; you still decide at the gate.

Your corrections feed back: overruling a verdict (`scout_log.py override … --rule "…"`) writes a rule to `scouting/calibration.md`, which the scout, the alignment and the critic read on every later run, and which is folded into the research map's near-misses when it generalises.

## No idea yet? Scout for sources

`source-scout` finds candidates when you have nothing to start from. It needs a confirmed `research-map.md`. It expands the citation graph from each problem's anchor papers (Semantic Scholar: citers, references, recommendations), then queries by formulation and by bridging concept across papers (conference proceedings, arXiv), open-source projects (repos, releases, design docs, benchmark leaderboards) and technical blog posts (engineering blogs, independent benchmarks, discussion threads). Each hit is screened in two passes: a cheap drop on title and abstract, then a relevance chain and scores for the survivors.

```text
/source-scout Build the watchlist from research-map.md, confirm it with me, then scan the last 90 days starting from the anchors.
```

You get `scouting/candidates.md`: a short list of `keep` and `maybe` items grouped by sub-problem, each with its chain (distance, shared structure, bridging concept, TRL) and a one-line reason. The stage critic reviews the shortlist before you see it (it re-derives formulations and samples the drops for false negatives). Everything screened, including drops, is recorded in `scouting/screened.jsonl`, so the next run only shows new items:

```text
/source-scout Scout again since the last run.
```

When you disagree with a verdict, say so and why; the agent records it as a calibration rule so the mistake is not repeated:

```sh
python .claude/skills/source-scout/scripts/scout_log.py scouting override --id leis2026-lc --verdict drop \
  --reason "static workload only" --rule "R1.a needs methods that handle hourly inserts; static-index papers are near-misses"
```

Pick the candidates you want to look at closely, then:

```text
/source-digest Digest candidates leis2026-lc and duckdb2026-agg into scouting/sources/.
/idea-alignment Rank the digests in scouting/sources/ against research-map.md and synthesise the directions.
/research-poc Promote leis2026-lc into a new idea "learned-cardinality".
```

The promotion copies the digest and alignment into `poc/learned-cardinality/` and records those stages as done, so the workflow continues from the alignment approval. Command form:

```sh
python .claude/skills/research-poc/scripts/poc_state.py poc/learned-cardinality promote --from scouting --source leis2026-lc --by you
python .claude/skills/source-scout/scripts/scout_log.py scouting promote --id leis2026-lc --idea learned-cardinality
```

Scouting rules: only public, generic terms go into searches (never company or product details); vendor claims count as self-reported until independently measured; the scout never starts ideas or experiments by itself.

## Go back and revise a step

The workflow is not a fixed line. Ask to go back to any stage, and the orchestrator reopens it with your reason. Everything after it is re-checked automatically.

```text
/research-poc For learned-cardinality, go back and raise the threshold from 10% to 15%;
the director wants a bigger margin.
```

What happens:

1. `proposed` is reopened and updated in place, with a change-log entry.
2. It needs your approval again.
3. `reproduced`, `extended`, `plotted` and `deck` become **stale** because their input changed. Each re-runs in **update mode**: it revises its previous output and re-runs only the affected parts.
4. If a re-run produces the same output, the stages after it stay done. Experiments are not repeated for a change that doesn't affect them.

Common requests and the stage they reopen:

| You say | Stage reopened |
|---|---|
| "Company priorities changed" | none: edit `company-context.md`, re-run `/research-map`; `aligned` becomes stale by itself |
| "It keeps matching on the wrong thing" | none: record an override (calibration rule); `aligned` becomes stale and the critic applies the rule |
| "The critic is wrong about M2" | none: tell the orchestrator; it completes with `--force` and your decision in the summary |
| "Take match M2 instead" | `aligned` |
| "Change the threshold / add an ablation / use a different baseline" | `proposed` |
| "The paper's protocol was misread" | `digest` |
| "The harness had a bug" | `reproduced` (old runs are marked superseded, never deleted) |
| "Plot p99 latency instead of the mean" | `plotted` |
| "Change the story of the deck" | `deck` |

Hand edits count too. If you edit `ideas/proposal.md` yourself, the stage shows `edited`, the stages after it show `stale`, and the next "continue" picks this up.

The full rules are in [research-poc/references/workflow.md](research-poc/references/workflow.md).

## Use a skill on its own

Each skill also works outside the workflow. Inside a `poc/<idea>/` workspace, it follows the workspace layout; elsewhere, it uses the same layout in the current directory.

**research-map**: translate priorities into research problems before scouting or aligning.

```text
/research-map Add a problem block for our new priority "cross-region replication cost" and propose anchors and near-misses.
```

**source-scout**: find candidates when you have no source yet (see [No idea yet?](#no-idea-yet-scout-for-sources)).

```text
/source-scout Scan the last 90 days for our watchlist topics across papers, open-source releases and engineering blogs.
```

**source-digest**: read and dissect a paper, an open-source project or a blog post.

```text
/source-digest Digest https://arxiv.org/abs/XXXX.XXXXX including the appendix and official repo.
/source-digest Digest the DuckDB 1.5 external aggregation design: release notes, design doc and benchmark scripts.
/source-digest Digest this engineering blog post and its discussion thread: <url>
```

Every digest records the source type and evidence level (`peer-reviewed`, `working-code`, `self-reported`, `claim-only`), the purpose, mechanism and canonical formulation with the adjacent fields that share it, the benchmark protocol table (datasets, metrics, baselines, hyperparameters, seeds, hardware), the reported results copied with their locations, protocol gaps, and extension hooks. For a batch it also writes `sources/INDEX.md`.

**idea-alignment**: find where a source's idea fits the business.

```text
/idea-alignment Map the digests in poc/learned-cardinality/sources to research-map.md; write the relevance chain and ground point for each match and rank them.
```

Every match carries a relevance chain (sub-problem, shared structure, transfer distance, bridging concept, what transfers and what must change), an assumption table checked against `company-context.md`, and a ground point written as an argument with its own rebuttal. Matches that share only vocabulary are listed under *Rejected*. With several digests, a *Direction synthesis* section says where the field is converging and which shared assumption breaks for the company — the seed for the extension.

**idea-extension**: turn a match into a novel, testable proposal.

```text
/idea-extension Extend match M1 into a proposal. Run the novelty check and give me 2–3 directions to choose from.
```

The proposal opens with the Heilmeier catechism (what, how today, what's new, who cares, risks, cost, time, exams). Directions come from at least three extension patterns. The novelty check runs as a loop — search, closest works, restate the difference, revise the direction if it is only "X applied to Y", search again — and records its queries, sources, dates and closest prior work per round. Novelty is marked `unverified` when search tools are unavailable, never assumed. Company details are kept out of search queries.

**stage-critic**: an independent review of any stage file.

```text
/stage-critic Review poc/learned-cardinality/ideas/alignment.md against its rubric and the digests; write the rebuttal for M1.
```

The rubrics are in [stage-critic/references/rubrics/](stage-critic/references/rubrics/), one per stage; add a question whenever a gate catches something the critic missed.

**bench-setup**: reproduce the paper, then benchmark the extension.

```text
/bench-setup Write the experiment plan and reproduce the paper's baseline on JOB before touching the extension.
```

It writes `experiments/plan.md` and `reported_targets.json` first, runs a quick smoke test, then reproduces. Check the run records:

```sh
python .claude/skills/bench-setup/scripts/check_results.py results/runs.jsonl --targets experiments/reported_targets.json
```

**result-plots**: charts and an honest summary.

```text
/result-plots Plot results against hnsw, include the recall-vs-QPS trade-off, and write the summary.
```

```sh
python .claude/skills/result-plots/scripts/plot_results.py results/runs.jsonl --baseline hnsw \
  --out figures --table results/improvements.md --tradeoff throughput_qps recall@10
```

**lit-review-deck**: a poster-style deck of recent work (see [the section above](#review-recent-papers-as-a-poster-deck)).

```text
/lit-review-deck Build a reading-group deck on the last 12 months of vector-index papers, 8 blocks.
```

**insight-ppt**: see the next section.

## Review recent papers as a poster deck

`lit-review-deck` answers "what came out recently that changes what we should do?". It scans papers, engineering blogs and open-source releases from **the last 12 months only**, screens them against `company-context.md`, and builds a deck laid out as a wall of posters: one block per paper, with a figure captured from the original PDF, the problem, the main contribution, one headline number and the line tying it to a company direction.

```text
/lit-review-deck Review the last year of work on query optimization and vector search for our
top 3 priorities. 20-minute deck for the engineering leads, about 10 papers.
```

It writes `reviews/<review-id>/brief.md` (scope, themes, window, search topics) and **asks you to approve it before scanning**, then presents a shortlist grouped by theme for you to pick from, including what it dropped for being outside the window. For each chosen paper it writes a card, captures the figure and records where the figure came from.

Three templates carry the review, and you can fill or edit any of them by hand:

| Template | Written to | Holds |
|---|---|---|
| [review-brief.md](lit-review-deck/templates/review-brief.md) | `reviews/<id>/brief.md` | audience, duration, window, the company directions served, the themes and their public search topics, the queries run, and what was dropped for being out of window |
| [paper-card.md](lit-review-deck/templates/paper-card.md) | `reviews/<id>/papers/<paper-id>/card.md` | one paper: the four block lines (problem, does, result, for us), evidence level, which figure and why, exact numbers with their locations, and the speaker notes |
| [blocks.example.json](lit-review-deck/templates/blocks.example.json) | `reviews/<id>/blocks.json` | the deck spec the build reads: themes, grid, per-paper blocks, takeaways, next steps |

Edit `brief.md` before approving it to change the scope, or edit `blocks.json` and rebuild to change the deck without re-running the scan.

Capture a figure from a source PDF:

```sh
python .claude/skills/lit-review-deck/scripts/figure_grab.py papers/leis2026-lc/source.pdf --probe --pages 1-8
python .claude/skills/lit-review-deck/scripts/figure_grab.py papers/leis2026-lc/source.pdf \
  --page 5 --rect 0.08,0.10,0.92,0.46 --units frac --dpi 220 \
  --out papers/leis2026-lc/figures/fig3.png --cite "Leis et al., SIGMOD 2026" --source-url <url>
```

Every capture writes a `.json` sidecar (page, crop, dpi, backend, citation). A figure without one does not go in the deck; every block shows its credit line and `deck/sources.md` lists them all.

Build the deck from the approved blocks:

```sh
python .claude/skills/lit-review-deck/scripts/poster_deck.py reviews/<review-id>/blocks.json \
  --out reviews/<review-id>/deck/<review-id>-v1.pptx
```

Two papers per slide by default, three or four on a dense slide; the script paginates a theme that does not fit, writes speaker notes and `sources.md`, and prints a layout warning per block that needs shorter lines. The deck uses the same team theme as `insight-ppt`. See [references/poster-layout.md](lit-review-deck/references/poster-layout.md) for the block anatomy and the `blocks.json` schema, and [references/figure-capture.md](lit-review-deck/references/figure-capture.md) for which figure to pick and the attribution rules.

Figures are reproduced from the originals with attribution, which is normal practice for an internal review. Before a deck leaves the company, check each figure's licence.

## Catch up on a conference

`conference-radar` answers "what new ideas came out of this venue, and which are worth my time?". It needs no company context or research map. It pulls the full accepted-paper list of a venue edition, looks at the whole venue before narrowing to your interests, and reports **ideas** rather than papers: each cluster is named by the mechanism its papers share, with a maturity label, an evidence verdict and the two or three papers that show it best.

```text
/conference-radar Catch me up on ICML 2026 and the NeurIPS 2026 papers already on arXiv:
efficient LLM inference and RL for reasoning. Standard depth, just for me.
```

It keeps a standing profile in `radar/interests.md`: your areas with their filter terms, what to ignore, and the ideas you already know, so later radars report only what changed. Each run writes `radar/<radar-id>/scope.md` and **asks you to confirm it before fetching**. At standard depth it also shows you the clusters and picks before reading full papers. The report `radar.md` has a TL;DR, the venue at a glance with rising and fading terms, the idea clusters, up to five must-reads, a hype check and idea seeds, each seed with the cheapest test that would show whether it is worth pursuing.

| Depth | Reads | Output |
|---|---|---|
| `skim` | abstracts only | venue at a glance, trends, clusters, must-reads |
| `standard` (default) | + 8–15 papers in full | + idea cards, seeds |
| `deep` | + 20–30 papers in full | + cross-cluster synthesis, closest-prior check on every card |

The script does the fetching and counting, so the agent never has to load thousands of abstracts:

```sh
S=.claude/skills/conference-radar/scripts/radar.py; R=radar/icml-2026
python $S fetch virtual --conf icml --year 2026 --out $R/papers.jsonl
python $S fetch virtual --conf icml --year 2025 --out $R/baseline.jsonl
python $S trends $R/papers.jsonl --baseline $R/baseline.jsonl --min-count 15
python $S filter $R/papers.jsonl --any "speculative decod|kv.?cache|quantiz" --titles-only --out $R/shortlist.jsonl
python $S enrich $R/shortlist.jsonl          # fill missing abstracts, find arXiv ids and PDFs
python $S show $R/shortlist.jsonl --limit 40
```

Supported listings: the virtual sites of ICLR, ICML, NeurIPS, CVPR, ICCV, ECCV and AISTATS; ACL Anthology volumes (ACL, EMNLP, NAACL, EACL, COLING, Findings); and arXiv, by "accepted at" comment, category or query. Other venues take a manual import in the same record format. The ICLR 2026 and ICML 2026 listings carry no abstracts, so the radar filters those on titles and enriches only the shortlist. OpenReview and DBLP block scripted access. See [references/venues.md](conference-radar/references/venues.md) for the per-venue details and [references/reading-ideas.md](conference-radar/references/reading-ideas.md) for how clusters, hype checks and seeds are built.

Hand-offs go only where you choose: a seed to `research-poc`, a cluster's queries to the `source-scout` watchlist, or the cards to `lit-review-deck` for a team deck.

## Build decks in the team theme

`insight-ppt` builds editable PowerPoint decks that look like the team's research decks. It starts from [`assets/team-template.pptx`](insight-ppt/assets/team-template.pptx), whose master slide supplies the lab header, logo, "Huawei Confidential" line, page number, footer bar and title-slide artwork. [`team_deck.py`](insight-ppt/scripts/team_deck.py) adds content as native, editable shapes: cyan corner triangle, blue topic kicker, one-line red conclusion titles, grey and dark cards, red-bar callout strips, takeaway lines, stat numbers, tables and native charts.

```text
/insight-ppt Create a 15-minute deck for engineering leadership from poc/learned-cardinality:
use ideas/proposal.md, results/summary.md and figures/. Kicker: "Research Insight: Learned Cardinality".
```

The skill asks for missing context (audience, duration, decision you want), proposes a brief and outline for your approval, then builds the deck, speaker notes and `sources.md`. It checks layout (title length, text overflow, footer area, minimum font size) and renders slides for visual inspection when a renderer is available.

Build slides directly in Python:

```python
import sys; sys.path.insert(0, ".claude/skills/insight-ppt/scripts")
from team_deck import TeamDeck

deck = TeamDeck(kicker="Research Insight: Learned Cardinality", corner="triangle")  # or corner="Technology Trends"
deck.title_slide("Learned Cardinality for Lakehouse Planning", "From SIGMOD'26 idea to a Spark POC",
                 presenters=["Your Name"], team="Intelligent Data Team")
s = deck.slide("Bad estimates, not slow operators, drive the tail", tagline="JOB benchmark, 113 queries")
s.section(0.78, 1.35, 5.5, "How estimation fails today")
s.card(0.78, 1.65, 5.4, 1.8, "1 · Independence assumption", ["errors compound across joins"], tag="Baseline")
s.card(7.0, 1.65, 5.55, 1.8, "2 · Learned joint model", ["learns correlations from samples"], variant="dark", tag="Proposed")
s.takeaway("Fix the estimate and the plan fixes itself.", "p99 drops 55% on JOB.")
s.notes("Sources: ...")
deck.save("deck/learned-cardinality-v1.pptx")   # prints layout warnings to fix
```

Card variants carry meaning: `neutral` = baseline or context, `dark` = chosen design, `accent`/`outline` = the proposed change, `dashed` = inferred or future. See [references/team-theme.md](insight-ppt/references/team-theme.md) for the slide anatomy, all components and the slide patterns taken from the example decks.

When the team's master template changes, rebuild the base template from a newer team deck. The script keeps the masters and removes all slide content, names, notes and document metadata:

```sh
python insight-ppt/scripts/make_team_template.py path/to/new-team-deck.pptx
```

## Workspace layout

```text
your-project/
├── company-context.md               # shared by all ideas; written by you
├── research-map.md                  # shared: problem formulations, anchors, near-misses (research-map, confirmed by you)
├── scouting/                        # optional, shared: source-scout
│   ├── watchlist.md                 #   sub-problems → queries, anchors, venues, projects, blogs
│   ├── calibration.md               #   rules from your overrules; read by scout, alignment and critic
│   ├── screened.jsonl               #   every source seen, with verdict, chain and scores (append-only)
│   ├── runs/<date>.md               #   one report per scouting run
│   ├── reviews/<date>-shortlist.md  #   critic review of the shortlist
│   ├── candidates.md                #   current shortlist
│   ├── sources/<source-id>/digest.md
│   └── alignment.md
├── radar/                           # optional, standalone: conference-radar
│   ├── interests.md                 #   your areas, filter terms, ignore list, ideas already known
│   └── <radar-id>/                  #   scope.md, papers.jsonl, baseline.jsonl, shortlist.jsonl,
│                                    #   triage.md, cards/<paper-id>.md, radar.md
├── reviews/<review-id>/             # optional, standalone: lit-review-deck
│   ├── brief.md                     #   scope, themes, window, search topics
│   ├── papers/<paper-id>/card.md, source.pdf, figures/*.png + *.json
│   ├── blocks.json                  #   the deck spec built from the approved cards
│   └── deck/                        #   .pptx, build script, sources.md
└── poc/<idea-id>/
    ├── .poc/                        # workflow state (only poc_state.py writes here)
    │   ├── pipeline.json            #   stage graph for this idea (editable copy)
    │   ├── state.json               #   verdicts, file fingerprints, approvals, reviews
    │   └── events.jsonl             #   history: start / review / complete / approve / reopen / abort
    ├── STATUS.md                    # generated state table + your decisions and notes
    ├── reviews/<stage>-<run>.md     # stage-critic reviews (never edited by the writer)
    ├── sources/<source-id>/digest.md
    ├── ideas/alignment.md, proposal.md
    ├── experiments/plan.md, reported_targets.json, reproduction.md, extension.md, code/, configs/
    ├── results/runs.jsonl, improvements.md, summary.md
    ├── figures/                     # .svg, .png, .csv, src/
    └── deck/                        # .pptx, outline, sources.md
```

File formats are defined in [research-poc/references/workspace-contract.md](research-poc/references/workspace-contract.md). Run records follow [bench-setup/references/results-schema.md](bench-setup/references/results-schema.md).

## Script reference

Paths below assume Claude Code (`.claude/skills/`). For Codex, use `.agents/skills/`.

**Workflow state**: `research-poc/scripts/poc_state.py <idea-dir> <command>`

| Command | Purpose |
|---|---|
| `init` | Create the workspace, `STATUS.md` and `.poc/` state |
| `promote --from scouting --source ID --by NAME` | Create the workspace from a scouted, digested candidate; `digest` (and `aligned`, if scouting has an alignment) start as done |
| `status [--json]` | Stage table and next actions; refreshes `STATUS.md` |
| `next [--json]` | Only the next actions, in dependency order |
| `start <stage> --by NAME` | Claim a stage; prints a brief (create or update mode, and why — including the last critic review when it was not a pass) |
| `review <stage> --verdict pass\|revise\|block --path reviews/<stage>-<run>.md --summary TEXT` | Record a stage-critic review, bound to the current output |
| `complete <stage> --verdict passed\|accepted-with-caveats\|failed --summary TEXT` | Record outputs and input fingerprints; refused while the current output's review is `block` (`--force` with the user's decision) |
| `approve <stage> --by NAME [--note TEXT]` | Approve a gated stage's current output; refused without a review of it (`--force` if the user waives) |
| `reopen <stage> --reason TEXT --by NAME` | Go back to a stage; later stages are re-checked |
| `abort <stage> --reason TEXT` | Release a stage an agent could not finish |
| `log [--stage S] [--limit N]` | Show the event history |

Statuses: `pending`, `in_progress`, `stale` (an input changed), `reopened`, `edited` (outputs changed by hand), `awaiting_approval`, `failed`, `done`. Transitions that aren't allowed (for example, starting a stage whose inputs aren't approved) exit with code 2 and an explanation.

**Scouting log**: `source-scout/scripts/scout_log.py scouting <command>`

| Command | Purpose |
|---|---|
| `init` | Create `scouting/` with the watchlist template |
| `add --id ID --type paper\|oss\|blog --url URL --title T --verdict keep\|maybe\|drop --reason R --problem R1.a --distance direct\|adjacent-field\|analogy --structure "…" [--bridge "…"] [--trl N] [--via ANCHOR] [scores…]` | Record a screened source with its relevance chain (a `keep` is refused without `--problem`, `--distance`, `--structure`, and `--bridge` at non-direct distance; duplicates refused unless `--version`) |
| `override --id ID --verdict V --reason R --rule "…"` | Record the user's overrule of an agent verdict and append the rule to `calibration.md` |
| `rules` | Print `calibration.md` |
| `seen <url-or-id>` | Exit 0 with the record if already screened, 1 if new |
| `candidates [--write]` | Shortlist of `keep`/`maybe` items not yet promoted; `--write` regenerates `candidates.md` |
| `promote --id ID --idea IDEA` | Mark a candidate as promoted to `poc/<idea>` |
| `last-run`, `stats` | Date of the last run report; counts by type and verdict |

**Scholar search**: `source-scout/scripts/scholar_search.py <command>` (Semantic Scholar API, standard library; `S2_API_KEY` optional)

| Command | Purpose |
|---|---|
| `anchors --map research-map.md --problem R1 [--edge citations\|references\|recommendations] [--since YEAR] [--limit N] [--md]` | Expand the citation graph from the arXiv/DOI anchors listed under a problem in the map |
| `expand --id arXiv:… \| DOI:… [--edge …]` | Citers, references or recommendations for one paper |
| `search --query "…" [--since YEAR] [--fields cs.DB]` | Keyword search (public terms only) |
| `paper --id …` | One paper with abstract |

**Benchmark checks**: `bench-setup/scripts/check_results.py runs.jsonl [--targets reported_targets.json] [--min-seeds 3] [--include-smoke]`
Validates run records, flags fairness problems (different budgets, dirty git trees, duplicates), aggregates mean ± std across seeds and suggests a reproduction verdict. Exit code 1 on schema errors.

**Plots**: `result-plots/scripts/plot_results.py runs.jsonl --baseline METHOD [--out figures] [--table PATH] [--roles ...] [--metrics ...] [--lower-is-better ...] [--higher-is-better ...] [--tradeoff X Y] [--min-seeds 3]`
Writes, per metric, bars with 95% CIs, a change-vs-baseline chart, a CSV, trade-off scatter plots and a Markdown improvement table with a verdict per comparison.

**Decks**: `insight-ppt/scripts/team_deck.py` (Python library, see above) and `insight-ppt/scripts/make_team_template.py <team-deck.pptx> [out.pptx]`.

**Conference radar**: `conference-radar/scripts/radar.py <command>` (standard library; `curl` used as a fallback for arXiv)

| Command | Purpose |
|---|---|
| `fetch virtual --conf iclr\|icml\|neurips\|cvpr\|iccv\|eccv\|aistats --year Y [--host H] --out F` | Accepted papers from a conference virtual site, with track (oral / spotlight / poster), topic and affiliations |
| `fetch acl --volume 2025.emnlp-main [--volume …] --out F` | ACL Anthology volumes, with abstracts |
| `fetch arxiv [--comment "NeurIPS 2026"] [--cat cs.LG] [--query Q] [--since Y] [--max N] --out F` | arXiv preprints by comment, category or query (3 s between calls) |
| `enrich F [--workers N] [--limit N]` | Fill missing abstracts and find arXiv ids and PDFs; rerun to retry failures |
| `stats F [--by topic\|track\|venue\|affiliation] [--coarse] [--top N]` | Counts and shares |
| `trends F --baseline B [--min-count K] [--ngram 1,2] [--titles-only]` | Rising and fading terms against another edition; titles only when abstract coverage differs |
| `filter F [--any RE] [--all RE] [--none RE] [--track …] [--topic RE] [--titles-only] [--skip F2] --out F3` | Shortlist by interest terms, track or topic; `--skip` hides papers an earlier radar covered |
| `show F [--offset N] [--limit 40] [--chars 500]` | Read a batch as compact Markdown |

`fetch` merges into its output and de-duplicates by title. Raw listings are cached in `.cache/` beside the output.

**Review decks**: `lit-review-deck/scripts/poster_deck.py <blocks.json> --out <deck.pptx> [--team-deck PATH]`
Builds the poster deck (title, contents, legend, theme slides, also-worth-reading, next steps, sources) and writes `sources.md` beside it.

`lit-review-deck/scripts/figure_grab.py <source.pdf> [--probe --pages 1-8] [--list-images] [--page N --rect x0,y0,x1,y1 --units frac|pt --dpi 220 --out fig.png --caption C --cite C --source-url U]`
Captures a figure region from a PDF and writes the provenance sidecar. Uses PyMuPDF, else `pdftoppm` with Pillow.

## Share, update and keep confidential material private

- **Share with your team:** commit `.claude/skills/` and/or `.agents/skills/` in your project. To keep skills local instead, list those folders in `.git/info/exclude`.
- **Update:** run `git pull --ff-only` in this checkout and copy the skill folders again (the install loop above). Back up project-specific edits first, and delete files that upstream removed.
- **Customise the workflow for one idea:** edit `poc/<idea>/.poc/pipeline.json` (stage inputs, outputs, gates). To change the default for all new ideas, edit `research-poc/pipeline.json`.
- **Confidential material:**
  - The example team decks in `templates/` are internal and are ignored by Git (`.gitignore`); never commit them.
  - `company-context.md` and internal data must not go to public search tools or external services; the skills are instructed not to send them.
  - The base deck template carries company branding and the confidentiality footer. Host this repository only where that is allowed.
- **Don't commit** `__pycache__/`, virtual environments or large benchmark data. Add them to `.gitignore`.

## Troubleshooting

| Problem | Fix |
|---|---|
| Scout finds unrelated papers | Check `research-map.md`: is the canonical formulation specific (objective + binding constraint), and are there near-misses? Overrule the bad keeps with `scout_log.py override … --rule` so the rule is learned; run from anchors (`scholar_search.py anchors`) rather than queries |
| Alignment says a paper is irrelevant when it isn't | Add the bridging concept to the problem's block in the map (the name the other field uses); re-run alignment; it becomes stale automatically |
| `refused: a keep needs --problem --distance --structure` | The scout must state the relevance chain; use `maybe` if it can't be stated from a skim |
| `refused: … has no stage-critic review` | Run stage-critic on the stage (or `approve --force` if you waive the review) |
| `refused: … last review of this output is 'block'` | Read `reviews/<stage>-<run>.md`, fix the blockers and re-review, or `complete --force` with your decision in the summary |
| Scout finds only papers | Ask it to cover open-source and blog sources too, or add projects and feeds to `scouting/watchlist.md` |
| Skill not listed | Restart the agent; check `.claude/skills/<skill>/SKILL.md` (or `.agents/skills/...`) exists and the whole folder was copied |
| `refused: no workflow state` | Run `poc_state.py poc/<idea> init` first, or check the idea path |
| `refused: ... blocked by upstream stages` | Finish or approve the listed stages first; `status` shows what's waiting |
| `refused: ... is done; use reopen` | Going back requires a reason: `reopen <stage> --reason "..."` |
| A stage is stuck `in_progress` | The agent stopped mid-stage: `abort <stage> --reason "..."`, then continue |
| `matplotlib is required` / `No module named pptx` | Install the packages from [Requirements](#requirements) in your environment |
| Deck titles look clipped in a preview | The preview font is wider than Microsoft YaHei; keep titles under ~52 characters and check in PowerPoint |
| Deck warnings on save | Fix each one (shorten the title, enlarge the box, split the slide); don't shrink text below 7.5 pt |
| `team_deck.py not found` | Install `insight-ppt` beside `lit-review-deck`, or pass `--team-deck <path>` |
| `no backend` from `figure_grab.py` | `pip install pymupdf`, or install poppler-utils (`pdftoppm`) and Pillow |
| "field lines need ~N in more than the block has" | Shorten the block's lines, drop `Problem`, or put fewer papers on the slide |
