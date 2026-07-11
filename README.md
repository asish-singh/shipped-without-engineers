# shipped-without-engineers

A live case study in shipping software without writing any of it. A non technical product manager (Asish) directs Claude, who acts as engineering lead, who in turn manages Codex as the developer. Every handoff in that funnel produces a saved artifact, so the whole engagement can be audited by anyone.

The thesis of the case study is simple. Agents are only as good as the definition of done they are given, and writing a sharp definition of done is a product management skill. AI development needs product managers.

## What is in here

- `SPEC.md`, the founding spec, written as a discovery interview between the PM and Claude. Chapter one of the paper.
- `product/`, the thing that got shipped. A Definition of Done tool. You describe work you want to delegate to an AI in plain language, and it gives you back a clear, checkable list of "this is done when" statements to hand over with the work.
- `tasks/`, one folder per delivered task, containing the discovery interview, the signed PRD, the engineering brief, the cross model code review, and the acceptance verdict, exactly as they happened.
- `paper/`, the writeup. An educational analysis of the PM to Claude to Codex delivery cycle for non technical readers, with templates you can reuse.
- `SCOREBOARD.md`, per task metrics. Questions asked, first pass acceptance, defects caught in review, cost.

## The loop worth noticing

The tool that got built turns rough asks into definitions of done. The process that built it used definitions of done to quality check every piece of AI work. The product quality checked its own construction.

## How to use

Nothing to run yet. Once the product ships, the live demo URL and run instructions will appear here.
