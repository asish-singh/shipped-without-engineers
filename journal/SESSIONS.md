# Session journal

One entry per working session between the PM and Claude. This file is the continuity record, any future session must read it first and append an entry before ending. Full raw transcripts live in journal/raw/, which stays out of git because raw chats contain private details.

## Session 1, 2026-07-12

**What happened.**

- The project found its identity through two pivots, both preserved as evidence. It began as a public Definition of Done tool, Asish rejected that at PRD sign off ("that would be very stupid"), and it settled as a methodology whitepaper for people who delegate work to AI, proven by one real worked example. The paper is the deliverable, the build is the evidence.
- The worked example was chosen, a Shift Tracker for Asish's own night shifts (18:00 to 04:45 IST, Monday evening through Saturday 04:45, Sunday night not worked). His discovery interview (five questions, verbatim in tasks/01-shift-tracker/discovery.md) surfaced the headline insight, his time waste is not entertainment, it is work shaped waste, fake meetings judged by transcript quality and Slack huddles with no owned next steps. Meetings live in Google Meet, transcripts reachable via Google Calendar.
- Task 01, the local watcher, went through the full delivery cycle in this one session. Discovery, PRD signed with one correction (must be very light), engineering brief, built by Codex (codex exec, 145,581 tokens, covered by existing subscription), cross model review passed with zero blocking findings, three cosmetic ones, and one anomaly, Codex fabricated a claim in its self report about a nonexistent "collaboration log issue 12". The catch is recorded in review.md and on the scoreboard as the paper's first proof point.
- The watcher was installed on Asish's Mac and verified with a supervised sample (then deleted). Agent loaded, app and idle detection confirmed, Chrome active tab site confirmed readable (calendar.google.com). Window titles are best effort, macOS only exposes titles for apps in the visible desktop space.

**Where things stand.**

- The watcher sleeps until Monday 2026-07-13 at 18:00 IST, when real data collection begins. First run may trigger one or two macOS permission pop ups naming Python or osascript, Asish should click Allow.
- Task 01 acceptance is pending one real shift of data. On Tuesday, run `./watcher.py status` inside product/watcher, a sample from shift hours means the definition of done is met and Asish accepts or rejects in a sentence.

**Later the same session.**

- The repo went public at https://github.com/asish-singh/shipped-without-engineers after a sweep confirmed no personal identifiers in committed files. Raw transcripts and activity data stay local only, Asish decided against a private backup repo.
- The first full draft of the paper was written to paper/paper.md and pushed. Asish's direction, write like a sophisticated human, story first, honest about failures, for PMs and people who delegate to AI, never for engineers. Sections 5 onward will be rewritten by real data.

**Next.**

- Take Asish's acceptance verdict on task 01, file it, update the scoreboard.
- Task 02 is the judge, pulling Google Meet transcripts via Calendar and grading meetings for decisions, owners, and next steps. Task 03 is the weekly review page plus memo and the manual RUN publish step, which pushes anonymized patterns only, never names, employers, apps, or sites.
- The paper can start drafting any time, chapter one is the discovery interview and the pivot story.
