# Task 01, second fix brief, the installer writes an unrunnable agent

Written by the engineering lead on 2026-07-25, immediately after the idle fix was merged. Found while reinstalling the repaired watcher on the target machine. The developer works only from this brief.

## The objection

`install.sh` reports success while installing a launchd agent that cannot run. After a clean install the agent starts, exits with code 2, and launchd respawns it every thirty seconds forever. No data is collected.

The cause. The source plist carries placeholder tokens in ProgramArguments.

```
0 => "__PYTHON_PATH__"
1 => "__WATCHER_PATH__"
2 => "run"
```

`install.sh` then calls `plutil -replace ProgramArguments.0` and `plutil -replace ProgramArguments.1`. On this macOS version those calls insert new elements at those indexes instead of overwriting them, so the installed plist ends up with five arguments.

```
0 => "/opt/homebrew/bin/python3"
1 => "/Users/.../watcher.py"
2 => "__PYTHON_PATH__"
3 => "__WATCHER_PATH__"
4 => "run"
```

The watcher receives three arguments where it accepts one, `main()` hits its usage branch, and returns 2. Reproduced directly.

```
$ python3 watcher.py __PYTHON_PATH__ __WATCHER_PATH__ run
Usage  watcher.py once or run or status
exit code: 2
```

Note. The plist installed on 14 July had the correct three arguments, so either an earlier plutil behaved differently or that file was corrected by hand at some point. The cause of that difference is unknown and not worth chasing. Assume nothing about plutil's array semantics and stop depending on them.

Why nobody noticed. `StandardErrorPath` and `StandardOutPath` are both `/dev/null`, so the usage error was written nowhere. `install.sh` verifies only that launchd knows the service, which is true of a service that dies instantly, then prints "Shift Tracker is installed and loaded".

## Build

Changes in `product/watcher/`. Keep the footprint budget, zero dependencies, and no network calls.

1. **Write ProgramArguments deterministically.** Stop editing the array element by element. Replace the whole array in one operation so the result cannot depend on plutil's insert versus overwrite behaviour. Any approach is acceptable as long as the installed plist provably contains exactly three arguments, the interpreter path, the watcher path, and `run`.

2. **Make the installer prove the agent survives.** After bootstrapping, the installer must confirm the service is actually alive rather than merely known to launchd. Wait a few seconds, then check that the agent has not accumulated a nonzero last exit code and that it is running or legitimately scheduled with a clean exit history. If the agent is failing, print in plain language that the install did not work, say where to look, and exit nonzero. It must never print success over a crash looping agent.

3. **Stop discarding the agent's own error output.** Point `StandardErrorPath` at a real file under `~/.shift-tracker/`, for example `~/.shift-tracker/watcher.err.log`, so a future failure leaves a trace. Keep `StandardOutPath` at `/dev/null`. The error file must never contain window titles or browser hosts, only process level errors, which is already true of everything the script writes to stderr.

4. **Fail loudly on bad arguments.** `main()` currently returns 2 with a usage line for wrong arguments, which is correct behaviour that was made invisible. Leave the exit code, but also make the message identify itself, for example prefix it with `watcher.py` so it is recognisable in a log file that may contain other output.

## Definition of done, each item must be demonstrably yes

Written so that no mock and no reasoning about plutil can satisfy these. Run them on this machine.

- [ ] A test runs the real `install.sh` against a temporary HOME, then reads the resulting plist and asserts ProgramArguments has exactly three elements, that none of them contains the substring `__`, that element 0 is an existing executable file, that element 1 is an existing file, and that element 2 is `run`.
- [ ] That same test asserts the plist passes `plutil -lint`.
- [ ] A test asserts that running the watcher with the arguments the broken plist produced (`__PYTHON_PATH__ __WATCHER_PATH__ run`) exits nonzero, so the regression has a named guard.
- [ ] After a real install on the real machine, the agent is alive. Prove it by showing `launchctl print` output with a last exit code of 0 or absent, and a live PID or a clean scheduled state, several seconds after installing. Paste the real output.
- [ ] Prove the agent stays up. Wait at least sixty seconds after install, then show that the run count has not climbed and no nonzero exit code has appeared. A crash looping agent increments its run count, so this distinguishes healthy from looping.
- [ ] `install.sh` exits nonzero and prints a plain language failure when the agent does not survive. Prove it by deliberately breaking something, for example pointing the plist at a nonexistent script in a temporary HOME, and pasting the real failure output.
- [ ] The installed plist points `StandardErrorPath` at a real file, and that file exists after an install.
- [ ] All existing tests still pass. State the count before and after.
- [ ] Footprint still under 100 KB across shipped files, still zero dependencies, still no network imports.

## Explicitly out of scope

- Do not alter, migrate, or delete anything in `~/.shift-tracker/log/`. The eight shifts of existing data are evidence.
- Do not change the shift window, the sampling interval, the storage layout, or the idle logic repaired in the previous pass.
- Do not add a dependency, a network call, or a configuration file.
- Do not install onto the real machine as part of your work beyond what the definition of done requires, and never leave the real agent in a broken state. If you install for proof, leave it working.

## Notes

- Tests must use a temporary HOME. Never let a test write to the real `~/.shift-tracker/` or the real `~/Library/LaunchAgents/`, and never let a test bootstrap or bootout the real user agent.
- Code comments and README prose must not use em dashes, en dashes, hyphens, or colons as punctuation. File names and code syntax are exempt.
- Report only what you verified by running it. Every claim will be re run by the reviewer, including a deliberate attempt to reintroduce this bug.
