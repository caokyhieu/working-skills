# Reading a venue for ideas

## Cluster by mechanism

A cluster is a set of papers that use **the same trick for the same reason**. Name it by the trick.

| Topic label (too coarse) | Mechanism cluster (what the report needs) |
|---|---|
| LLM reasoning | RL on verifiable rewards where the model generates its own curriculum |
| Efficient inference | Drafting with a model's own early layers for speculative decoding |
| Diffusion models | Treating any-order autoregression as masked diffusion so AR training recipes carry over |
| Robustness | Certifying robustness by randomised smoothing in a learned latent space |

How to get there:

1. While reading a batch, write for each paper one line: *"uses <mechanism> to get <benefit> in <setting>"*. The mechanism slot is the part another paper could reuse.
2. Group papers whose mechanism slots match, even across different settings. Papers that share only the setting (same benchmark, same model family) do **not** share a cluster.
3. Split a cluster that has two mechanisms. Merge two clusters that turn out to be one mechanism described with different words, which happens often across communities: ML ↔ systems ↔ NLP ↔ vision.
4. Name the cluster in a way that someone who has not read any of its papers could say what the trick is.

Target: 5–15 clusters for a `standard` radar. Put more than that into *also seen*, one line each.

## Momentum and maturity

For each cluster, record:

| Field | How to fill it |
|---|---|
| Papers | count in the shortlist, with ids |
| Independent groups | count distinct first-author institutions or author sets. Three papers from one lab is one group. |
| Venue signal | how many are oral, spotlight or award |
| Maturity | `emerging` (1–2 groups, first appearance), `consolidating` (several groups, shared benchmarks, follow-ups citing each other), `saturated` (many small variants, gains shrinking, a survey has appeared) |
| Evidence quality | `strong` (ablations isolate the idea, tuned baselines, code), `mixed`, `weak` (one benchmark, untuned or old baselines, no code) |

**Convergence is the strongest signal on a radar.** Several groups arriving at the same trick independently, within one edition, is usually worth more than one oral.

## Hype cues

Put a cluster or paper in the hype check when two or more of these hold:

- the gain appears only on the authors' own benchmark or a benchmark built for the paper;
- the baselines are older than the previous edition of the venue, or plainly untuned;
- there is no ablation that removes the new component and keeps everything else;
- the claimed generality ("any model", "any task") is tested on one or two settings;
- the headline number is compute-unmatched: more samples, more tokens or a bigger model than the baseline;
- the mechanism can't be stated in a sentence, only the result can.

State the specific gap ("no compute-matched baseline in Table 2"), not a verdict about the field.

## Writing an idea card

- **The idea in the authors' framing.** Write the sentence they would use, then the mechanism in our words: why it should work, and what it exploits.
- **The delta.** Name the closest prior work the paper itself cites and say what is new relative to it. If the delta is small, say so. That is useful to know.
- **Evidence.** Give the headline numbers with baseline, benchmark and location (Table 3, §5.2). Say whether an ablation isolates the idea, and whether the baselines are compute-matched and tuned.
- **Transferable trick.** Say where else this would work, and what property a setting needs for it to transfer. This is the line that turns reading into ideas. Mark it `[inference]`.
- **Open questions.** List what the paper leaves unanswered: the authors' limitations first, then ours marked `[inference]`.

At `skim` depth, a card is four lines: idea, mechanism, headline claim, and `CLAIM-ONLY`.

## Seeds

A seed is an idea for new work that the radar makes visible. Generate seeds from these patterns (the full list is in [idea-extension/references/extension-patterns.md](../../idea-extension/references/extension-patterns.md)):

| Pattern | Where it comes from on a radar |
|---|---|
| **Shared blind spot** | A limitation that every paper in a cluster shares, such as all evaluating on short contexts or all assuming static data |
| **Cross-cluster combination** | One cluster's weakness is another cluster's strength |
| **Transfer** | A cluster's trick applied in a setting where its required property also holds, but no one has tried it yet |
| **Missing baseline** | A simple method no paper in the cluster compares against, which might be enough |
| **Contradiction** | Two papers reporting opposite effects of the same choice. Finding out why is a paper in itself. |
| **Change the constraint** | The cluster optimises accuracy; the same idea under a latency, memory or cost budget |

Each seed records: the observation (with card references), the gap, the **cheapest test** that would show whether the seed is worth more time (a dataset, a baseline, one metric, and roughly how much compute), and the cluster it came from. Seeds are `[inference]` by definition. Label them that way and don't overstate them.

## Budget

| Depth | Shortlist read (abstracts) | Cards (full text) | Seeds |
|---|---|---|---|
| skim | 80–300 | 0 (claim-only cards for must-reads) | 0–3 |
| standard | 80–300 | 8–15 | 3–6 |
| deep | 200–500 | 20–30 | 5–10 |

If the budget runs out, cut the number of cards and keep the clusters. The cluster map is the part that cannot be recovered later without re-reading everything.
