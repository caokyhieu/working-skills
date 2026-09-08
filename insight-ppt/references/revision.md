# Revision and review

Support edits to existing decks without unnecessarily recreating the entire presentation.

When the user requests an edit:

1. Identify the deck version and target slides.
2. Restate the requested changes in a concise change plan.
3. Ask for clarification only when the requested change would alter product facts, claims, audience, or deck direction.
4. Preserve the selected template, deck structure, references, and content that is not being changed.
5. Create a new versioned output, such as `proposal-v2.pptx`.
6. Include a short changelog listing modified slides and the reason for each change.

Examples:

```text
/insight-ppt edit proposal-v1.pptx --changes "Make slide 5 show the Kafka integration path; add the fallback behavior."

/insight-ppt edit proposal-v2.pptx --changes "Keep the technical detail but simplify the message for product leadership."

/insight-ppt edit proposal-v2.pptx --changes "Replace external benchmark claims with conservative assumptions and add a POC validation slide."

/insight-ppt review proposal-v3.pptx --audience "HQ architecture committee" --goal "find weak technical-fit claims and missing risks"
```

For review-only requests, return prioritized findings with slide numbers, evidence gaps, technical-fit concerns, narrative issues, and concrete proposed changes. Do not generate a revised deck unless requested. Inspect any supplied sources before judging factual accuracy.

For targeted edits, treat the requested change as the task brief. Reuse context from the deck and prior conversation; ask only about consequential missing or ambiguous facts. A new approval gate is appropriate for a changed deck direction, not a routine edit already authorized by the user. Save a new version and keep the source outline, diagram sources, notes, citations, and assumptions synchronized.
