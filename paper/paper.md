# Shipped Without Engineers

*A working paper on delegating to AI, written by a product manager who cannot code. Living draft. Every claim links to an unedited artifact in this repository, including the ones that make me look bad.*

## 1. What happened, in one paragraph

On a Friday night in July 2026 I set up two AI models as a two person engineering team. Claude, running in Claude Code, acted as the engineering lead. Codex, invoked from the command line with `codex exec`, acted as the developer. I acted as the product manager, which is my actual job, and I never wrote a line of code, a spec, or a prompt for the developer. By Saturday morning the team had shipped working software through a five stage delivery process, the developer's build passed review with zero blocking defects, and the developer's own completion report contained one flat fabrication that the process caught in minutes. This paper documents the method, the numbers, and what a product manager should take from it.

## 2. The team and how the work is distributed

The arrangement is deliberate and copied from every functioning company I have seen. Senior judgment directs junior throughput, with a quality gate between them.

**The product manager (me).** I speak only plain language. I answer interview questions, sign or reject documents, and accept or reject the final result. I never see code and I am never asked to evaluate anything technical.

**The engineering lead (Claude).** The expensive, careful model. It interviews me, writes the product requirements, translates my signed intent into an engineering brief with a checkable definition of done, reviews the developer's work with instructions to be hostile, and demonstrates the result to me in plain language.

**The developer (Codex).** The labor. It is invoked non interactively with `codex exec` and it works only from the engineering brief. It never sees my raw conversation, my reasoning, or my corrections. If something matters, it must be in the brief.

The economics follow the org chart. Judgment is what costs money, so it is spent where being wrong is expensive, on understanding intent and on checking work. Labor is bought cheap. The first build consumed 145,581 Codex tokens, which my existing subscription absorbed without noticing.

One property of this setup surprised me. A human team shares context by osmosis, hallway talk, tone, months of accumulated understanding. An AI team has none of that. The artifact is the entire relationship. If it is not written in the brief, it does not exist. That sounds like a limitation and works like a discipline.

## 3. The method, five stages, each leaving an artifact

Every task moves through the same five stages, and every stage files a saved, unedited document in `tasks/`.

1. **Discovery.** Claude interviews me, one question at a time, answers in writing. Transcript saved verbatim.
2. **PRD sign off.** Claude writes back what it believes I want, including its assumptions and what it considers out of scope. I approve or correct in plain language. Every version is saved.
3. **Engineering brief.** Claude writes the ticket for Codex, ending in a definition of done, a list of statements checkable as yes or no. I do not watch this being written. I only see the filed artifact.
4. **Cross model review.** Codex's work cannot merge until Claude has formally tried to fault it against the definition of done, rerunning every check itself rather than trusting the developer's report. Findings are classified as blocking, cosmetic, or false alarm. Blocked work goes back to Codex with the objection attached.
5. **Acceptance.** Claude demonstrates the working result and the proof for each done criterion. I accept or reject in a sentence.

The load bearing stage is the definition of done. "Handle my schedule properly" is a wish. "At 4.46 on Saturday morning it records nothing" is a contract. If you cannot produce such lines for a piece of work, you are not ready to delegate it, and the AI is not the bottleneck.

## 4. How the method was discovered, by failing

The project began as a worse idea. I wanted to build a public tool, and Claude dutifully spent an evening spec'ing one with me. The founding document, `SPEC.md`, is still in this repository unedited, because what happened next is the first real lesson. Reading the specification back at sign off, I realized I was about to build a product nobody asked for, in order to write a paper about how well I build products. I rejected it. My exact recorded words were that it would be very stupid.

Rejecting your own signed direction feels like failure and is actually the system working. The sign off stage exists so that a misunderstanding costs a conversation instead of a build. It caught one. That the misunderstanding was between me and myself is beside the point, or perhaps it is the point. The paper became the deliverable and the software became the evidence.

The replacement came from an ordinary complaint. I work nights, 18:00 to 04:45 India time, and I did not know where the hours went. So the worked example became a tracker for my own shifts. In the discovery interview, five questions, transcript in `tasks/01-shift-tracker/discovery.md`, something surfaced that I had never articulated. Asked to name my time sinks, I did not say social media. I said fake meetings, judged by the quality of their transcripts, and huddles that end with no owner for anything. My waste is not distraction, it is work shaped. It appears in the calendar as work and produces nothing, which is why no screen time app has ever measured it. That insight was not the AI being brilliant. It was being asked a direct question by something with infinite patience and no social stake in my answer, and having to answer in writing. The discovery interview is the oldest trick in product management. It works on yourself.

## 5. Task 01, the numbers

The first task was a local watcher that samples my activity only during shift hours, stores everything on my own machine, and touches no network.

- Discovery questions asked, 5.
- PRD accepted on the first version with one correction, the tool must stay very light. Claude turned those four words into a hard budget in the brief, under 100 KB, zero dependencies, nothing installed.
- My schedule became boundary cases in the definition of done. Monday 17:59 records nothing, Monday 18:00 records, Saturday 04:44 records, Saturday 04:46 does not, Sunday nights do not exist.
- Codex built it in one pass. 145,581 tokens.
- Claude's review reran everything independently. All 35 tests passed, the boundary cases behaved, the footprint came in at 52 KB, and an automated check confirmed no network modules are imported anywhere.
- Review verdict, 0 blocking findings, 3 cosmetic, 1 anomaly.

The anomaly is the most important line on the scoreboard. Codex's completion report, among true statements, claimed that "collaboration log issue 12 was created and labeled." No such issue, log, or side effect exists anywhere in the repository or on GitHub. The work was excellent. The report about the work contained a fabrication, delivered in the same confident voice as everything else. The review stage caught it in minutes because its one rule is to reverify every claim rather than trust the worker's account. The full record is in `tasks/01-shift-tracker/review.md`.

If I had been working alone with that AI, I would have believed the false claim, because I believed everything else it said and had no way to check. Most people delegating to AI today are working alone with it. That should worry you more than the famous failure modes do. The famous ones announce themselves. This one arrived inside a job done well.

## 6. What to copy, told over coffee

Make the AI interview you before anything starts, one question at a time, answers in writing. You are not documenting requirements, you are discovering what you actually want.

Make it write back what it heard, with assumptions and out of scope items, and sign or correct that. A misunderstanding caught here costs a sentence. The same one caught after the build costs the build.

Insist on a definition of done answerable yes or no, line by line, before any work begins.

Never accept the worker's own account of what it did. Have the work checked against the contract by a different model than the one that built it, and make the checker rerun everything itself. My first task produced a false claim inside an excellent delivery. Yours will too, eventually, and the only question is whether your process notices or your customer does.

Accept or reject in writing, against the contract, nothing else. Done is a verdict, not a feeling of being impressed.

None of this is new. It is the boring machinery of well run delivery, applied to workers who read everything, forget nothing, never resent hostile review, and occasionally lie by accident. The machinery matters more with them, not less, because all the informal correction of a human team is gone. What is written is all there is.

## 7. Where this goes next

The watcher is live on my machine, sleeping until Monday evening. Acceptance of task 01 waits on one real shift of data. Task 02 is the meeting judge, which will read my Google Meet transcripts and grade each meeting, decisions made, owners assigned, next steps that survived, or empty calories. Task 03 is the weekly memo, a plain language letter on where my hours went and which parts of my calendar are theater. Each will run through the same five stages, each will leave its artifacts here, and the scoreboard will keep the running tally.

My own data stays on my machine permanently. What gets published are patterns, by hand, on days I choose.

The larger bet, stated plainly so I can be held to it. The industry is obsessed with what AI can do and is about to discover that its real constraint is people who can say precisely what they want and verify precisely what they got. That is not an engineering skill. It is product management, and almost nobody in the current conversation about AI is talking about it.

## Appendix, the evidence

- The rejected first idea, unedited, `SPEC.md`
- The discovery interview, verbatim, `tasks/01-shift-tracker/discovery.md`
- The signed specification and my correction, `tasks/01-shift-tracker/prd.md`
- The brief and its definition of done, `tasks/01-shift-tracker/brief.md`
- The hostile review, including the fabricated claim, `tasks/01-shift-tracker/review.md`
- The running scoreboard, `SCOREBOARD.md`
- The session journal, `journal/SESSIONS.md`
