You are an independent judge of a code card: a short reference document about one
part of a codebase, written by another agent. You did not write it. Assume it contains
errors, including deliberately planted ones. Your job is to find them by reading the code.

Repo root: {root}
Card to judge: {input}
  Judge THIS file. Cite its line numbers (L<n>).
Card rules: {skill}/references/card-format.md
Code to read:
{files}
Lines you must judge: {lines}
  Read the whole card for context, but give a verdict for every one of these lines.
{scope_note}

Rules:
- Read whole functions and classes, not grep hits. Follow calls into other files when a
  claim depends on what the callee does.
- Do not trust names, comments or docstrings: a function named `retry` may not retry.
  Judge what the code does.
- Do not edit any repo file. Write only your report. Do not open other files under
  {verify_dir}; they are not for you.
- Diagrams: every line inside a ```mermaid block is a claim. A node line claims the
  component exists under that name. An edge or message line claims that call or data
  flow exists in that direction. A label claims that protocol, payload or trigger. Judge
  each line. A real call or transition on the drawn path that the diagram omits is Missing.
- You may run read-only commands and small throwaway probes (python -c, a single test)
  to confirm behavior. Never modify the repo or its data.
{depth}

Write your report to {report} in exactly this format:

# Verify: {module} (shard {shard})
prep: {prep}
judge: subagent

## Claims
| Line | Section | Claim (short) | Verdict | Evidence |
|---|---|---|---|---|
| L<n> | <section> | <claim> | OK | <path>::<symbol> (read) |

- One row per claim; a line with two claims gets two rows; every listed line needs a row.
- Verdict is exactly one of:
  OK           the code confirms it. Evidence MUST name path::symbol or path:line, then (read) or (ran).
  WRONG        the code differs. Name the location and say what the code does.
  UNSUPPORTED  no evidence found. Say where you looked.
- An OK without a code location counts as UNSUPPORTED.

## Missing
- M1: <fact a developer changing this code needs and the card lacks> — <path::symbol>
Only: public entry points, failure paths, config reads, side effects, owned state,
concurrency, surprising behavior. Not private helpers. Write "None." if nothing.

## Probe
Write {probe_n} questions a developer about to change this code would ask (what happens
when X fails, who calls Y, what default Z has, what runs concurrently with W). Answer
each first from the card alone, then from the code.
| Q | Question | Card answer | Code answer | Verdict |
|---|---|---|---|---|
| P1 | <question> | <from the card> | <from the code> (<path>::<symbol>) | OK |
Verdict: OK (card answers correctly), MISLEADING (card's answer is wrong),
UNANSWERED (card is silent and the answer matters). If the number of questions is 0,
write "Skipped."

## Trace
{trace_rule}

## Precision
- L20: "<quote>" → <rewrite, or delete>     (or "None.")

VERDICT: <n> OK, <n> WRONG, <n> UNSUPPORTED, <n> missing, <n> probe failures

Reply with only the VERDICT line.
