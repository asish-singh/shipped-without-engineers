# Task 01, engineering brief for the developer

Written by the engineering lead. The developer works only from this brief.

## Build

A lightweight background activity watcher for macOS, living in `product/watcher/` of this repository. No GUI. It samples the user's foreground activity during defined shift hours and appends events to a local log. It must be extremely light, no Electron, no bundled runtime, no daemon frameworks. Use a single Python 3 script (macOS system python3 is acceptable) or a single shell plus osascript design, plus a launchd LaunchAgent plist and an install script.

## Behavior

1. **Shift window.** Active only Monday 18:00 through Saturday 04:45 local time (Asia/Kolkata is the machine timezone), meaning each weekday evening 18:00 to 23:59 and the following morning 00:00 to 04:45. Saturday 04:45 to Monday 18:00 it must record nothing. The window logic must be a pure function of the current timestamp so it is unit testable.
2. **Sampling.** Every 30 seconds while in the shift window, record a JSON line with ISO 8601 local timestamp, frontmost application name, window title of the frontmost window (best effort, empty string if unavailable), and idle seconds (from IOKit HIDIdleTime via `ioreg`). For browsers (Safari, Chrome, Arc, Brave, Edge), additionally capture the active tab's URL host only (not the full URL) via osascript, empty string if scripting permission is missing.
3. **Idle.** If idle seconds exceed 180, the sample is marked `"idle": true`.
4. **Storage.** Append to `~/.shift-tracker/log/YYYY-MM-DD.jsonl` where the date is the shift start date (samples after midnight belong to the previous evening's file). Directory created on first run with permissions 700. No data ever written anywhere else, no network calls at all.
5. **Scheduling.** A launchd LaunchAgent runs the sampler. Either launchd StartCalendarInterval wakeups or a persistent lightweight loop that sleeps outside the window, developer's choice, but justify it in a comment and keep memory under roughly 30 MB and CPU effectively idle.
6. **Install and uninstall.** `install.sh` copies the LaunchAgent plist to `~/Library/LaunchAgents/`, loads it, and prints in plain language what permission dialogs the user should expect (Accessibility and or Automation) and how to grant them. `uninstall.sh` unloads and removes everything except the data directory.
7. **Status command.** `./watcher.py status` (or equivalent) prints whether the agent is loaded, whether we are currently inside the shift window, the path of today's log, and the last recorded sample time.

## Definition of done, each item must be demonstrably yes

- [ ] A unit testable function decides in window or out of window for any timestamp, with tests covering Monday 17:59 (out), Monday 18:00 (in), Saturday 04:44 (in), Saturday 04:46 (out), Sunday 22:00 (out), Monday 00:30 (out, because Sunday evening is not worked).
- [ ] Running the sampler once inside the window appends exactly one valid JSON line with the fields named above.
- [ ] Running the sampler outside the window writes nothing and exits 0.
- [ ] Samples taken after midnight land in the previous evening's dated file.
- [ ] Idle over 180 seconds marks the sample idle.
- [ ] The watcher makes zero network calls (verifiable by reading the code, no network libraries imported or invoked).
- [ ] Total footprint on disk under 100 KB of code, no dependencies installed, nothing bundled.
- [ ] install.sh and uninstall.sh work and print plain language guidance.
- [ ] A README.md in product/watcher/ explains in non technical language what is collected, where it lives, and that it never leaves the machine.
- [ ] All tests pass via a single command stated in the README.

## Notes

- Window titles and URL hosts are sensitive. They stay in the local log only. Do not print them in status output.
- Code comments and README must not use em dashes, en dashes, hyphens, or colons as punctuation in prose. File names and code syntax are exempt.
