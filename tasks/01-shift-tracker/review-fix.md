# Task 01, cross model review of the idle fix

Reviewer, Claude (engineering lead). Developer, Codex. Reviewed 2026-07-25 against fix-brief.md. Every claim in the developer's report was re run by the reviewer rather than trusted. Three files changed, 89 insertions, 12 deletions, all inside product/watcher/.

## What the developer changed

- `read_idle_seconds()` now runs `ioreg -r -c IOHIDSystem -d 1`. The `-r` flag makes ioreg print the matched object's properties, which is what the missing depth was hiding.
- `idle_seconds_from_ioreg()` returns `None` instead of 0.0 when the property is absent, and its regex now anchors to a whole line so a partial match cannot be read as a valid number.
- `sample_once()` writes `idle_seconds` as null and `idle` as false when the reading is unavailable, and never crashes on it.
- `print_status()` takes a live reading and prints either the real idle seconds or a plain language line saying the sensor is unavailable.

## Independently verified

- 39 tests pass, up from 35, run by the reviewer with the documented command. Zero tests skipped, so the macOS only tests genuinely executed here.
- The live status command, run by the reviewer, printed `Current idle seconds  291.169632875`. The sensor is alive and the number is plausible for a machine sitting untouched during the review.
- The real ioreg line on this machine is `      "HIDIdleTime" = 291128217333`, and the new anchored regex matches it. Confirmed against actual output, not against a fixture.
- Null is distinguishable from zero in the written record. Verified by reading the tests and by the developer's probe output, `{"idle_seconds":null,"idle":false}` against `{"idle_seconds":0.0,"idle":false}`.
- Idle boundary behaviour preserved. Exactly 180 is not idle, 180.000001 is.
- Shipped footprint 44,676 bytes across six files, under the 100 KB budget, measured by the reviewer.
- No network imports. The module imports only json, os, re, stat, subprocess, sys, time, datetime and pathlib.
- Production data untouched. All eight log files carry their original timestamps and sizes.
- The developer reported creating collaboration log issue 51. The reviewer checked GitHub. It exists, it is closed, and it carries the collaboration-log label. Unlike the previous pass on this task, this self report claim is true.

## The check that matters most

A test that passes is worthless if it would also pass while broken. The reviewer copied the fixed code to a scratch directory, reintroduced the original `-d 1` invocation, and re ran the two live sensor tests. Both failed, with `AssertionError: None is not an instance of any of (<class 'int'>, <class 'float'>)`.

The new definition of done therefore does what the old one could not. It cannot be satisfied by a mock, and it fails in the presence of the exact bug that shipped.

## Findings

**Blocking against the fix brief.** None.

**Cosmetic.** None worth recording.

## Two findings about the product, discovered during review, outside the fix brief

Neither is a defect in the developer's work. Both were found because the reviewer ran the real system instead of only reading the diff.

1. **The watcher is not running, and has not been since Friday morning.** The launchd service is absent from `launchctl list`, and `launchctl print-disabled gui/501` reports `"com.shifttracker.watcher" => disabled`. Something unloaded the agent and launchd recorded that state persistently, so it will not return at login on its own. The consequence is that Friday 24 July produced no log at all. The plist is still in place and the interpreter it points at still works, so a re enable plus a reinstall restores collection. Nothing was lost beyond that one night, because Saturday and Sunday nights are not worked.

2. **The fix is not live on the machine.** install.sh copies watcher.py into Application Support, and that copy still has the July 12 code and a different checksum from the repository. Until install.sh is rerun, the machine keeps sampling with the broken sensor. This is cosmetic finding 1 from the original review turning into a real consequence, which is worth noting rather than burying.

Both findings share the defect class that caused the original bug. The plist sends stdout and stderr to `/dev/null`, so the watcher cannot report that it died, just as the idle sensor could not report that it was blind. A system that fails silently will be trusted while it is failing. The product has no heartbeat, and a day of loss went unnoticed until a human happened to look.

## Verdict

Approved for merge. The idle defect is repaired, the repair is proven against the live machine, and the new criteria would catch a regression.

Acceptance of task 01 remains open until the fix is installed and one real shift is collected with a working sensor. The next working shift begins Monday 27 July at 18:00.
