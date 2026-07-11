# Founding spec, the Definition of Done tool

This spec was produced through a discovery interview between Asish (product manager) and Claude on 2026-07-12. It is chapter one of the paper. The interview answers below are verbatim.

## The discovery interview

**Who is the first user?**

> anyone delegating work to ai

**What moment are we saving them from?**

> help them brainstorm and implement things in most efficient way with AI and reduce costs and delegate properly for best outcomes

**What does success look like, in their words?**

> reliability, correctness of means and ends, thoroughly qc'd output

## What the PM's answers tell us

The user is broad, not just tech company PMs. Anyone who hands work to an AI, a founder, a marketer, a student, a consultant. The pain is not "AI is bad," it is "I delegate badly, so I pay in retries, cost, and wrong outputs." Success is trust. The user wants to hand work over and believe what comes back.

The insight underneath all three answers is that reliability is created before the work starts, at the moment of delegation, by saying precisely what done means. That is the product.

## The product in one sentence

You describe the work you want an AI to do, in plain language, and the tool gives you back a definition of done, a short checkable list of "this is done when" statements you attach to the work, so the output can be judged instead of trusted.

## What version one does

1. The user pastes or types a rough ask, any kind of work, not just code.
2. The tool asks up to three clarifying questions, the kind a good manager would ask, only when the ask is genuinely ambiguous.
3. It returns a definition of done, five to ten statements, each one checkable by a yes or no answer, covering both the ends (the result) and the means (constraints like cost, tone, sources, format).
4. It flags anything the user has not decided yet as an open question rather than guessing.
5. The result can be copied out in one click to paste alongside the delegated task.

## Explicitly out of scope for version one

- Running the delegated work itself. The tool defines done, it does not do the work.
- Accounts, saved history, teams. One session, one ask, one definition.
- Grading finished work against the definition. A tempting version two.

## How we will know the product works

- A rough ask of one or two sentences produces a definition of done that a stranger could use to accept or reject the finished work without asking the requester anything.
- Every statement in the output is answerable yes or no. No vague statements like "the output is high quality."
- The tool's own definitions of done get used, unedited, as the quality gates for building the rest of this repo. If we keep having to rewrite them by hand, the product is not working.

## Open questions carried forward

- What the tool is called. Working name, Definition of Done tool.
- Whether version one is a public web page or starts as a simple local page. Leaning public web page, since the case study needs a live link.
