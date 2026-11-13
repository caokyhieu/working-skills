# Judge

The writer of a card remembers what it meant and reads that instead of what it wrote.
So a card is not trusted until an independent judge, an agent with a fresh context
holding only the card and the code, has checked every claim and passed a test of its
own diligence. `cards.py stamp` refuses a card without a passing verdict for the
current card text and the current code.

Four layers, cheapest first:

| Layer | Who | Catches |
|---|---|---|
| 1. `cards.py check` | script | anchors that point nowhere, parameters the definition lacks, imports missing from `depends_on`, Uses / Used by disagreement, leftover `TBD`, length |
| 2. Claim judge | fresh agent(s) | every claim line judged OK / WRONG / UNSUPPORTED with a code location |
| 3. Probe | the same judge(s) | omissions and misleading text: questions a developer would ask, answered from the card, then from the code |
| 4. Canary | script | a judge that skims: one claim in the judge's copy is silently made wrong; a report that misses it is rejected |

The system card gets the same treatment, plus a cross-card check (flows and
cross-module rules against the module cards and the code).

## Run it

```bash
cards check <module>                # layer 1; fix every error first
cards judge <module>                # writes verify/<module>/s<k>.prompt.md, one per judge
# spawn one fresh agent per prompt file, in parallel (see Spawning)
cards verdict <module>              # grades the reports; PASS or FAIL with finding ids
```

`judge` decides the depth from the code itself:

| Tier | When (owned code) | Judges | Probe questions | Extra |
|---|---|---|---|---|
| small | ≤ 400 LOC, ≤ 60 branches, no concurrency | 1 | 3 | |
| medium | up to 1500 LOC or any concurrency marker | 1 | 5 | |
| complex | > 1500 LOC, ≥ 5 concurrency markers, > 250 branches, or > 15 files | 2–4, each its own lines and its own canary | 6 each | depth checklist, call-chain Trace required, each failure mode cited at raise site AND handler |

`--shards N` overrides the judge count (raise it for code you know is tricky);
`--full` re-judges every line.

## Spawning

- **Claude Code**: `Agent` tool, `subagent_type: general-purpose`. Prompt: "Read
  `<prompt file>` and follow its instructions exactly. It is your complete task."
  Several judges run in parallel; wait for all, then `verdict`. Not `Explore`: it reads
  excerpts, and judging needs whole files. If the harness lets you choose the judge's
  model, a different model from the writer's makes correlated mistakes less likely.
- **Codex / other harnesses**: any fresh-context agent with file read and shell.
- **No subagent available**: `cards judge <module> --self`. Re-read the card and code
  from disk, follow the prompt yourself, write the report. No canary is planted (you
  would know it), and the stamp records `judge: self`. Tell the user; it is weaker.

Never add your own explanation of the code to the judge's prompt. What you believe the
code does is the thing under test.

## What `verdict` enforces

A card passes only when all of these hold:

- Every assigned line has a verdict row (`L<n>`). Unjudged lines block; they cannot be waived.
- Each judge flagged its canary line WRONG. A judge that missed it is rejected: run
  `judge` again (new canary) and spawn a **fresh** agent, not the same one.
- The report carries the `prep:` id of this run: an old report cannot be reused.
- No open finding:

  | Finding id | Meaning | Fix |
  |---|---|---|
  | `s1:L14` WRONG | the code says otherwise | correct the line from the code |
  | `s1:L14` UNSUPPORTED | judge found no evidence | find the evidence and anchor it, or delete the claim |
  | `s1:L14` OK without a code location | judge did not show its work | re-judge |
  | `s1:L32` failure mode not traced (complex) | raise site without handler | re-judge, or deepen the card |
  | `s1:M2` MISSING | card lacks a fact a developer needs | add it, or waive with a reason |
  | `s1:P3` MISLEADING / UNANSWERED | card answers a real question wrongly or not at all | fix or add the fact |
  | `s1:trace` | complex module, no call chains | re-judge |

- The card and the code did not change between `judge` and `verdict`.

Waive a finding only with a reason: `cards verdict api --waive 's1:M2=private helper,
no behavior change'`. Waive a WRONG only when you dispute it with code evidence **and
the user agrees**. Waivers are stored in `verify/<module>/run.json` and shown at the
checkpoint.

## Rounds

After a FAIL, fix the card (or, with the user, the code), then `judge` again. Lines that
are unchanged and were judged OK carry over when the code is unchanged, so the next round
judges only the edited lines (and still plants a canary among them). If the code changed,
every line is judged again. Expect one or two rounds. If a third round still fails on
the same claim, stop and ask the user: writer and judge disagree about the code, and
the user decides.

A judge's precision notes (`## Precision`) do not block; apply the ones that cut words
without losing facts.

## Files

```
docs/cards/verify/<module>/run.json      the current run: tier, judges, canaries, findings, waivers, pass/fail
docs/cards/verify/<module>/s<k>.prompt.md judge k's full brief
docs/cards/verify/<module>/s<k>.input.md  judge k's copy of the card (with its canary)
docs/cards/verify/<module>/s<k>.report.md judge k's report
docs/cards/verify/<module>/judged.md      the card text at the last verdict (for carry-over)
```

`verify/` is the working area of the current round. When the card is stamped, its
reports and `run.json` are copied into the version folder
(`history/<module>/vNNN_<date>_<commit>/judge/`), so every version keeps the evidence
that passed it. The writer must not read `run.json` before the verdict: it holds the
canaries.

## At the checkpoint

Report to the user, per card: tier, number of judges, canary caught per judge, claim
counts, findings fixed, findings waived with reasons. For example:

```
ingest (complex, 3 judges): canaries 3/3 caught; 41 OK, 2 WRONG fixed (L18 timeout 30s→10s,
L44 retry count), 1 MISSING added (s2:M1 close() drains queue); waived s3:P4 (test-only path)
```
