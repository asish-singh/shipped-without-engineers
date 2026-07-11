# Project: shipped-without-engineers

A public case study and paper showing how a non technical product manager shipped a real product using Claude as engineering lead and Codex as the developer.

## Status

- Started: 2026-07-12
- Current state: just created, delivery cycle not yet started

## Goal

One public link that proves Asish can ship working software purely through product judgment. It holds three things. The shipped product (a Definition of Done tool, turn a plain language ask into checkable "this is done when" statements before delegating work to an AI, with a live demo URL). The full evidence trail for every task (discovery interview, signed PRD, engineering brief, cross model code review, acceptance verdict). And the paper, an educational analysis of the PM to Claude to Codex funnel written for non technical readers, framed as product management and AI methodology discovery, never as engineering.

The audience is anyone delegating work to AI, not engineers. The thesis is that defining done is the PM craft that makes AI delegation reliable, cheap, and properly quality checked. The self referential hook is that the tool being built generates definitions of done, and the process building it uses definitions of done at every quality gate.

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
- The product (the Definition of Done tool) is dogfooded. Once it minimally works, it generates the definition of done for every subsequent engineering brief in this repo, so the live demo shows its real output in use.
- The paper is written for product managers and anyone delegating to AI, never for engineers. Technical machinery appears only as one diagram, then the writing returns to management lessons.
- No em dashes, en dashes, hyphens, or colons as punctuation in any prose written for this repo, including the paper and artifacts authored by Claude. Technical strings are exempt.
- Commit working checkpoints as you go.
- Keep this file updated as the project evolves (goal, status, how to run).
