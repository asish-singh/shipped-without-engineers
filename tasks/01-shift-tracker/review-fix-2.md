# Task 01, cross model review of the installer fix

Reviewer, Claude (engineering lead). Developer, Codex. Reviewed 2026-07-25 against fix-brief-2.md. Four files changed, 266 insertions, 27 deletions, all inside product/watcher/. Every claim in the developer's report was re run by the reviewer.

## What the developer changed

- The plist is now rewritten with `plistlib`, replacing the entire ProgramArguments array and the error log path in one operation. No more editing array positions and hoping plutil overwrites rather than inserts.
- `install.sh` creates `~/.shift-tracker/watcher.err.log` at mode 600 and installs it as `StandardErrorPath`, so the agent can no longer die into `/dev/null`.
- After bootstrapping, the installer sleeps five seconds and inspects the service's real state, pid, and exit history. If the agent is unhealthy it prints a plain language failure, boots the service out rather than leaving a corpse behind, and exits nonzero.
- The launchctl binary is now injectable through an environment variable, which is what lets the tests exercise the installer without going anywhere near the real launchd domain.
- The usage error from `main()` is prefixed with `watcher.py` so it is identifiable in a shared log file.

## Independently verified

- 41 tests pass, up from 39, run by the reviewer with the documented command. Zero skipped.
- The installed plist on the real machine has exactly three ProgramArguments, the interpreter, the watcher path, and `run`. No placeholder tokens survive.
- `StandardErrorPath` points at `/Users/asishsingh/.shift-tracker/watcher.err.log`, the file exists, it is mode 600, and it is empty, which is the correct state for an agent that has not errored.
- The installed copy of watcher.py now matches the repository checksum, so the idle repair from the previous pass is finally live on the machine.
- The real agent is healthy. Ten minutes after install, `state = running`, `runs = 1`, `pid = 15807`, `last exit code = (never exited)`. A crash looping agent increments its run count, so a run count still at one is the proof that matters.
- Resource use is within the original brief. 0.0 percent CPU and about 10 MB resident, against a budget of roughly 30 MB.
- The test suite does not touch the real system. It installs into a temporary HOME and injects a fake launchctl shell script, and the real agent's run count and pid were unchanged after the reviewer ran the full suite.
- Production data intact. All eight log files present and unmodified.
- The developer reported collaboration log issue 52. The reviewer checked GitHub. It exists, it is closed, and it is labelled. Two truthful self reports in a row now, after the fabrication on the first pass.

## The check that matters most

The reviewer copied the fixed watcher to a scratch directory, reverted `install.sh` to the original `plutil -replace ProgramArguments.0` approach, and ran the new installer test.

```
AssertionError: 5 != 3
```

Five arguments where three were required, which is precisely the defect, caught by the guard written for it. The test earns its place.

The failure path was also proven rather than assumed. With a deliberately broken watcher path in a temporary HOME, the installer exits 1 and prints "Shift Tracker installation did not work because the background agent did not stay healthy", naming the error log and the launchctl command to inspect. It no longer prints success over a dead agent.

## Findings

**Blocking.** None.

**Cosmetic.** None worth recording.

## How this defect was found, which is the point

This bug was not found by reading code. It was found because the reviewer ran the installer on the real machine and then looked at one number, the launchd exit status column, which read 2.

The install script had already printed "Shift Tracker is installed and loaded". Every earlier gate agreed with it. The tests passed, the plist linted, launchd knew the service, and the reviewer had already written and committed an approving review of the idle fix. The agent was dying thirty times a minute the whole time.

Three separate silent failures surfaced in one day on one small tool. The idle sensor that returned a plausible zero when blind. The launchd agent that had been disabled for a day with nothing to say about it. The installer that reported success over an agent that could not start. In every case the software's own account of itself was confident and wrong, and only an outside check against reality caught it.

## Verdict

Approved for merge.

Task 01 acceptance is still open by one step. The watcher is now installed, running, and pointed at working code, but it has not yet collected a shift with a live idle sensor. The next working shift begins Monday 27 July at 18:00. Acceptance should be decided on that data, not on this review.
