# Project: shipped-without-engineers

A methodology whitepaper on delegating work to AI, written by a non technical product manager and proven on one real worked example, with Claude as engineering lead and Codex as the developer.

## Status

- Started: 2026-07-12
- Current state: framing settled on 2026-07-12, the paper is the deliverable, the build is evidence only. Worked example not yet chosen (it will be a real small need of Asish's). First product idea (a public Definition of Done tool) was rejected at PRD sign off, SPEC.md kept unedited as evidence.

## Goal

Publish a paper that names and teaches a method for delegating work to AI, for an audience of product managers and anyone who delegates to AI, never engineers. The method is proven by one small real build done end to end through it, with every artifact saved unedited and a scoreboard of costs and quality catches. Nothing here is a product for the world. The build is a prop, it needs no public URL, no users, no polish beyond honest working software.

The thesis is that defining done is the PM craft that makes AI delegation reliable, cheap, and properly quality checked. AI delegation needs product managers.

## The delivery cycle (the method this repo demonstrates)

Asish is the product manager. Claude is the engineering lead. Codex (via `codex exec`) is the developer. Asish never writes specs, prompts for Codex, or code. Every task follows five stages, and every stage produces a saved artifact in `tasks/<nn>-<slug>/`:

1. Discovery, Claude interviews Asish, one question at a time. Transcript saved verbatim.
2. PRD sign off, Claude writes back what it believes is wanted, including assumptions and out of scope items. Asish approves or corrects. All versions saved.
3. Engineering brief, Claude writes the ticket for Codex with a checkable definition of done. Asish does not see this being written, only the filed artifact.
4. Cross model review, Codex's work cannot merge until the other model has formally tried to fault it against the definition of done. Findings classified as blocking, cosmetic, or false alarm. Blocked work returns to Codex with the objection attached.
5. Acceptance, Claude demonstrates the working result and proof of each done criterion. Asish accepts or rejects in a sentence.

A scoreboard tracks per task: interview questions asked, whether the first PRD was right, blocking versus cosmetic versus false alarm review findings, first pass acceptance, and cost.

## Notes for Claude

- Asish is non technical: explain in plain language, choose sensible defaults, confirm before anything destructive.
- The integrity of the case study depends on the artifacts being real and unedited. Never polish or backfill an artifact after the fact. Failures and corrections stay in, they are the most convincing material.
- Asish must not be asked to write technical documents. If a stage needs technical input, turn it into plain language interview questions instead.
- Codex is invoked non interactively with `codex exec`. Codex works only from the engineering brief, never from the raw conversation.
- The paper is written for product managers and anyone delegating to AI, never for engineers. Technical machinery appears only as one diagram, then the writing returns to management lessons.
- The worked example must be a real need of Asish's, not an invented demo. Its value is credibility, not the software itself.
- No em dashes, en dashes, hyphens, or colons as punctuation in any prose written for this repo, including the paper and artifacts authored by Claude. Technical strings are exempt.
- Commit working checkpoints as you go.
- Keep this file updated as the project evolves (goal, status, how to run).
