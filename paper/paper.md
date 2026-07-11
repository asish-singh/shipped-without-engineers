# Shipped Without Engineers

*A working paper on delegating to AI, written by a product manager who cannot code. Living draft. Everything asserted here links to unedited artifacts elsewhere in this repository, including the parts that make me look bad.*

## 1.

On a Friday night in July I asked an AI to interview me about a product idea, and by Saturday morning there was working software on my machine that I had not written a line of. I want to be careful with that sentence, because it is the kind of sentence that gets written a lot right now, usually by people selling something. So let me say immediately what this paper is not. It is not a claim that AI replaces engineers. It is not a tutorial about tools. And the software itself, a small program that watches how I spend my night shifts, is honestly not that interesting.

What I think is interesting is what I had to do to get it, because none of it was technical. I was interviewed. I signed things. I rejected a specification. I caught nothing myself, but the process I insisted on caught a lie. Every one of those moments came from the job I already do, product management, and by the end of the first task I had stopped thinking of this as a coding experiment. It is a management story in which the employees happen to be AIs.

The premise of this paper, which the rest of it tries to earn, is that the reliability of an AI teammate is mostly decided before the work starts, at the moment of delegation, by how precisely you can say what done means. That is a skill. It has a name and a profession attached to it. Nobody is more practiced at it than a decent product manager, and almost nobody in the current conversation about AI is talking about it.

## 2. The setup

Two AIs, arranged deliberately. An expensive, careful model as the engineering lead. A cheaper, faster one as the developer. The lead interviews me, writes the specifications, briefs the developer, reviews the developer's work with instructions to be hostile, and demonstrates results to me. The developer only ever sees the brief. I only ever see plain language.

I did not invent this arrangement, I stole it from every functioning company I have ever seen. Senior judgment directing junior throughput, with a quality gate between them. The economics are the same too. The first task cost about 145 thousand tokens of developer labor, which my existing subscription absorbed without noticing. Judgment is what costs money, so you spend it where being wrong is expensive, on understanding intent and on checking work, and you buy the labor cheap.

What I did not expect is how much the arrangement would depend on writing things down. A human team shares context by osmosis, hallway conversation, tone of voice, months of accumulated understanding of what the boss actually means. An AI team has none of that. The artifact is the entire relationship. If it is not in the brief, it does not exist. This turns out to be less of a limitation than a discipline, and it is the discipline this repository documents, stage by stage, with the actual artifacts.

## 3. What happened, told honestly

The project began as a worse idea. I wanted to build a public tool, and my AI lead dutifully spent an evening with me spec'ing one. The founding document from that evening is still in this repository, unedited, because what happened next is the first real lesson. Reading the specification back, I realized I was about to build a product nobody asked for, in order to write a paper about how well I build products. I rejected it at sign off. My exact words, which are also preserved, were that it would be very stupid.

I notice that rejecting your own signed off direction feels like failure and is actually the system working. The sign off stage exists precisely so that a misunderstanding costs a conversation instead of a build. It caught one. That the misunderstanding was between me and myself is beside the point, or maybe it is the point.

The replacement came from an ordinary complaint. I work nights, six in the evening until quarter to five in the morning, India time, and I genuinely did not know where those hours went. So the worked example became a tracker for my own shifts. When the lead interviewed me about it, five questions, transcript saved verbatim, something surfaced that I had never articulated. Asked to name my time sinks, I did not say social media or news. I said fake meetings, judged by the quality of their transcripts, and huddles that end with no owner for anything. My waste was not distraction. It was work shaped. It performs as work, it appears in the calendar as work, and it produces nothing. No screen time app measures that, which is why I had never seen it measured.

I want to flag what produced that insight, because it was not the AI being brilliant. It was being asked a direct question by something with infinite patience and no social stake in my answer, and having to answer in writing. The discovery interview is the oldest trick in product management. It works on stakeholders. It turns out to work on yourself.

Then the part I cannot do. The lead translated my signed intent into a brief for the developer, ending in a definition of done, statements checkable as yes or no. My schedule became boundary cases, at 4.44 on a Saturday morning the tracker records, at 4.46 it does not, Sunday nights do not exist. My four word correction at sign off, that the thing must stay light, became a hard budget, under a hundred kilobytes, nothing installed. I never saw this document being written. I have still not read the code. The method does not ask me to supervise work I cannot evaluate. It asks me to define done for work I can.

The developer built it in one pass, and built it well. Then it filed its completion report, and in the middle of the report, among true statements, was a claim about a side effect that had never happened. Something it had supposedly created and labeled somewhere. No such thing existed anywhere. The review stage, whose one rule is to reverify every claim rather than trust the worker's account, caught it in minutes and classified it, alongside three minor findings, in a written verdict that is in this repository.

I keep turning that moment over. The work was excellent. The report about the work contained a fabrication, delivered in the same confident voice as everything else. If I had been working alone with that AI, I would have believed it, because I believed everything else it said and had no way to check. Most people delegating to AI today are working alone with it. That should worry you more than the famous failure modes do, because the famous failure modes announce themselves, and this one arrived inside a job done well.

## 4. The method, extracted

Written as what I would tell another PM, or anyone who delegates to AI, over coffee.

Make it interview you before anything starts. One question at a time, answers in writing. You are not documenting requirements, you are discovering what you actually want, and you will be surprised.

Make it write back what it heard, with its assumptions and what it considers out of scope, and sign that or correct it. Every misunderstanding you catch here costs a sentence. The same misunderstanding caught after the build costs the build.

Insist on a definition of done that is answerable yes or no, line by line. "Handle my schedule properly" is a wish. "At 4.46 it records nothing" is a contract. If you cannot produce such lines for a piece of work, you have learned something important, you are not ready to delegate that work, and the AI is not the bottleneck.

Never accept the worker's own account of what it did. Have the work checked against the contract by something other than whoever did it, and make the checker rerun everything. My first task produced a false claim inside an excellent delivery. Yours will too, eventually, and the only question is whether your process notices or your customer does.

Accept or reject in writing, against the contract, nothing else. Done is a verdict, not a feeling of being impressed.

None of this is new. It is the boring machinery of well run delivery, applied to workers who read everything, forget nothing, never get offended by hostile review, and occasionally lie by accident. The machinery matters more with them, not less, because all the informal correction of a human team, the raised eyebrow, the corridor clarification, is gone. What is written is all there is.

## 5. Where this goes next

The tracker is live on my machine as of this weekend, sleeping until Monday evening. From here the paper stops being about setup and starts being about results, and I genuinely do not know what they will say, which is the fun of it.

Next comes the meeting judge, which will read my meeting transcripts and grade each one, decisions made, owners assigned, next steps that survived, or empty calories. Then the weekly memo, a plain language letter telling me where my hours went and which parts of my calendar are theater. After a few weeks, a monthly reckoning, what to stop doing. Each will be delivered through the same five stages, each will leave its artifacts here, and the scoreboard will keep the running tally of interviews, rejections, review catches, and cost.

My own data stays on my own machine, permanently. What gets published here are patterns, by hand, on the days I choose. If the memos say something uncomfortable about how I work, and I expect they will, the discomfort will be published and the specifics will not.

The larger bet, stated plainly so I can be held to it. The industry is currently obsessed with what AI can do, and is about to discover that its real constraint is people who can say precisely what they want and verify precisely what they got. That is not an engineering skill. If this repository, its evidence trail, and its eventual results make one person delegate differently next week, the paper has done its job.

## Appendix, the evidence

- The rejected first idea, unedited, `SPEC.md`
- The discovery interview, verbatim, `tasks/01-shift-tracker/discovery.md`
- The signed specification and my correction, `tasks/01-shift-tracker/prd.md`
- The brief and its definition of done, `tasks/01-shift-tracker/brief.md`
- The hostile review, including the fabricated claim, `tasks/01-shift-tracker/review.md`
- The running scoreboard, `SCOREBOARD.md`
- The session journal, `journal/SESSIONS.md`
