# Task 01, acceptance

Stage five of the delivery cycle. The engineering lead demonstrates the result against the signed definition of done, the PM accepts or rejects. Written 2026-07-25, after eight real shifts of production data.

The review in review.md approved the build for merge but recorded that true completion required real shift data. This is that step.

## Evidence, from production data only

The watcher ran unattended on the PM's machine from 2026-07-14 through 2026-07-24. No supervision, no restarts, no intervention.

- Eight shifts captured, 14, 15, 16, 17, 20, 21, 22 and 23 July.
- 9,922 samples at 30 second intervals, about 82.7 hours of observed shift time.
- Every night started at or within eleven minutes of 18:00 and ended between 04:15 and 04:44, so full shifts were survived end to end.
- Nothing was written on the two non working nights, and nothing was written outside shift hours on any night.
- Total data footprint, 1.5 MB for eight shifts.
- Frontmost application captured on 100 percent of samples.
- Browser host captured on 64.6 percent of samples, with 12 to 23 distinct hosts per night, which is consistent with the share of time spent in a browser.
- Window titles captured on 108 of 9,922 samples, 1.1 percent.

## Definition of done, checked against production data

| Criterion | Verdict |
| --- | --- |
| Survives a full real shift unattended | Yes, eight consecutive working shifts |
| Log correctly shows shift start and end | Yes |
| Log shows active apps | Yes, every sample |
| Log shows active sites | Yes, on browser samples |
| Log shows idle gaps | **No, see the blocking defect** |
| Wrote nothing outside shift hours | Yes |
| Genuinely lightweight, tiny on disk, barely noticeable | Yes, 52 KB of code, zero dependencies, no perceived impact across 83 hours |

## Blocking defect, idle detection never worked in production

Every one of the 9,922 samples recorded `idle_seconds` as exactly 0.0. Median zero, ninety ninth percentile zero, maximum zero. Not one sample across 83 hours was ever marked idle.

This is not a finding about the PM's habits. A human being cannot register zero idle time at every 30 second sample for 83 hours. It is a dead sensor reporting a plausible number.

The cause. `read_idle_seconds()` runs `ioreg -c IOHIDSystem -d 1` and parses HIDIdleTime out of the output. On this machine the `-d 1` depth limit truncates the output before the property is reached, so the regex never matches. `idle_seconds_from_ioreg()` then returns 0.0 on no match, exactly as its own test asserts it should. The failure is silent by design. Removing `-d 1` returns the value correctly, so the repair is one line.

Why the review gate missed it, which is the finding worth keeping. Every idle test in the suite injects a fake reader, for example `idle_reader=lambda: 181`, and proves that the marking logic is correct. The only test of the real code path feeds a hand written string to the parser. Nothing ever asked this Mac for its actual idle time. Thirty five passing tests, an independent cross model review, and a whole subsystem that had never once run for real.

The definition of done shares the blame. It said "idle over 180 seconds marks the sample idle", which is a statement about logic. It never said "the idle reading on the target machine is a real number that changes when the user stops typing", which is a statement about the world. A criterion that can be satisfied by a mock is not finished being written.

## Secondary observations, not blocking

1. Window title capture at 1.1 percent is far weaker than "best effort" suggests. The cause is known and documented, macOS only exposes titles for apps in the visible desktop space. It is not a defect against the brief, but the review and the README both overstate what this field delivers, and nothing downstream should depend on it.
2. Monday 13 July has no log file, although collection was expected to begin that evening. The most likely cause is the first run permission dialogs sitting unanswered. Unproven, and it cost one night.

## Verdict

Rejected on one blocking defect. Idle detection is returned to the developer with the objection attached. Every other criterion is met by production data.

The PM was shown the finding, the root cause, and this recommendation, and directed the lead to proceed with it. His instruction, verbatim, one word.

> proceed
