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

## Session 2, 2026-07-12

**What happened.** Asish reviewed the first paper draft and found it too vague, rambling, and silent on the concrete machinery. The paper was rewritten and pushed. It now names Claude as engineering lead and Codex as developer, presents the five stage cycle as an explicit numbered method, explains the role and cost distribution, tells the discovery story through the rejected SPEC.md pivot, and reports task 01 with real figures (5 questions, 145,581 tokens, 35 tests, 52 KB, 0 blocking, 3 cosmetic, 1 fabricated claim).

**Where things stand.** Watcher still sleeping until Monday 18:00 IST. Task 01 acceptance still pending one real shift of data.

**Next.** Unchanged from session 1, take the acceptance verdict, then task 02 the meeting judge.

## Session 3, 2026-07-25

**What happened.**

- Asish returned with eight shifts of real data and asked whether it was enough to proceed. It was, and checking it rather than assuming produced the paper's best finding so far.
- The data. Eight shifts captured, 14 to 23 July, 9,922 samples, about 82.7 hours, every night run end to end unattended. Applications captured on every sample, browser hosts on 65 percent, window titles on 1.1 percent.
- The defect. Idle detection had never worked. All 9,922 samples recorded idle_seconds as exactly 0.0. The cause was the `-d 1` depth flag on the ioreg call, which truncated the output before HIDIdleTime, combined with a parser that returned 0.0 on no match. A dead sensor was indistinguishable from a user who never pauses.
- Why the gate missed it. Every idle test injected a fake reader. The only test of the real path fed a hand written string to the parser. Thirty five passing tests, an independent cross model review, and a subsystem that had never once run for real. The definition of done shared the blame, "idle over 180 seconds marks the sample idle" is a claim about logic that a mock satisfies.
- Task 01 was rejected at acceptance on that one blocking defect, filed in acceptance.md. review.md was left untouched, because backfilling it would destroy the evidence.
- The fix went back to Codex with a definition of done written so no mock could pass it, requiring a live reading from the real machine and a second reading two seconds later that must be larger. Codex delivered, 39 tests now pass with none skipped, null is now distinct from zero, and the status command reports the live sensor.
- The review re ran everything, then did the check that mattered. The reviewer reintroduced the original bug in a scratch copy and confirmed both new tests fail. Approved with zero findings. The developer's self report was true this time, collaboration log issue 51 genuinely exists, which is worth noting against the fabrication on the first pass.
- Two findings surfaced from running the real system rather than reading the diff. The launchd agent is disabled in launchd's persistent override database, so it has not run since Friday morning and Friday 24 July produced no log. And the installed copy in Application Support is still the July 12 code, so the fix is not live. Both are the same defect class as the original bug, silent failure, because the plist sends stdout and stderr to /dev/null.

**Then the reinstall exposed a third silent failure.**

- Asish authorised the reinstall. install.sh printed "Shift Tracker is installed and loaded", and it was lying. The launchd exit status column read 2, the agent was dying instantly, and launchd was respawning it every thirty seconds. On Monday it would have collected nothing.
- The cause. The source plist carries placeholder tokens in ProgramArguments, and install.sh swapped them with `plutil -replace ProgramArguments.0` and `.1`. On current macOS those calls insert instead of overwrite, so the installed plist held five arguments with the placeholders still sitting in the middle. The watcher accepts one argument, got three, hit its usage branch, and returned 2. Reproduced directly on the command line.
- Why it was invisible. The plist sent stderr to `/dev/null`, and install.sh verified only that launchd knew the service, which is also true of a service that dies instantly.
- Worth recording honestly, the reviewer had already committed an approving review of the idle fix before finding this. The gate that caught it was not code reading, it was running the real thing and looking at one number.
- Task 01b went to Codex. The plist is now written whole with plistlib, stderr goes to `~/.shift-tracker/watcher.err.log`, and the installer waits five seconds and checks the real process state before it dares print success, exiting nonzero with plain language guidance when the agent is not healthy. The launchctl binary is injectable so tests never touch the real launchd domain.
- Review passed with zero findings. The reviewer reverted install.sh to the old plutil approach in a scratch copy and the new test failed with `AssertionError: 5 != 3`, which is the defect exactly. The broken install path was also proven to exit 1 with a readable message. Collaboration log issue 52 was checked and is real, two truthful self reports in a row now.

**Where things stand.**

- The watcher is installed, running, and finally pointed at the repaired code. Verified by the reviewer ten minutes after install, `state = running`, `runs = 1`, `pid = 15807`, `last exit code = (never exited)`, 0.0 percent CPU, about 10 MB resident. A crash looping agent climbs its run count, so a run count of one is the proof.
- All eight shifts of production data are intact and untouched throughout.
- Task 01 acceptance is still open by exactly one step, a shift collected with a live idle sensor. The next working shift is Monday 27 July at 18:00.

**Next.**

- On Tuesday 28 July, check the new log for idle values that are real numbers rather than zeros, then take Asish's acceptance verdict on task 01 and close it.
- Then task 02, the meeting judge.
- The paper needs a new section, and it now has a much better one than planned. Three silent failures in one day on one small tool, each of which passed every gate while the software's own account of itself was confident and wrong. The mock shaped definition of done is the headline, and the wider lesson is that a definition of done which can be satisfied without touching reality is not finished being written.
