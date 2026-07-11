# Task 01, PRD, the Shift Tracker (working name)

Presented to the PM on 2026-07-12. Verdict below, verbatim.

## The need

Asish works nights, 6pm to 4.45am India time, Monday evening through Saturday 4.45am. He wants to know where he is most productive, and to reclaim time from work shaped waste, chiefly fake meetings and outcome free huddles.

## What we build, in three pieces

1. **The watcher.** A quiet background program on the Mac. During shift hours only, it notes which app and which website or window is active, and when the user is idle. It never takes screenshots, never records keystrokes, and stores everything in a private file on the Mac. Outside shift hours it sleeps. One macOS permission granted at first run, then invisible.
2. **The judge.** After each shift, it pulls Google Meet transcripts through Calendar and grades each meeting, did this produce decisions, owners, and next steps, or was it empty calories. Slack huddles are only visible as time blocks, so huddle time is reported as unjudged cost for now. Grading uses AI, a small per week cost on existing accounts.
3. **The review.** On demand, a page on the Mac with charts, plus a written memo in plain language, best hours, emptiest meetings, where the week leaked. Monthly, a sharper memo that says what to stop, including uncomfortable findings. People related findings never leave the Mac.

## Publishing

Nothing goes to GitHub automatically. The PM presses RUN to publish anonymized patterns only, never employer, names, apps, or sites.

## Assumptions

The Mac stays on during shifts. The Google account can read Calendar and transcripts. Anything about specific people is private forever, the public repo only ever shows patterns.

## Out of scope for task 01

The watcher ships first and collects a few real shifts before the judge (task 02) and the review plus RUN (task 03) are built, because the review is only as good as the data underneath. Out of scope entirely, tracking outside shift hours, screenshots, and anything the employer could read.

## Done means

The watcher survives a full real shift unattended, its log correctly shows shift start and end, active apps and sites, and idle gaps, and it wrote nothing outside shift hours. Per the PM's correction at sign off, it must also be genuinely lightweight, tiny on disk and barely noticeable while running.

## PM verdict, verbatim

> approved. but the mac app should not take much space, it should be very light

First PRD accepted with one correction (lightweightness), correction incorporated into the definition of done above.
