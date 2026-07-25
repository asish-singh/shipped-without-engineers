# Task 01, fix brief, idle detection

Written by the engineering lead after the PM rejected task 01 at acceptance. The developer works only from this brief. See acceptance.md for the rejection and the evidence.

## The objection

Idle detection has never worked in production. Across 9,922 real samples spanning 83 hours, `idle_seconds` was exactly 0.0 every single time and no sample was ever marked idle.

`read_idle_seconds()` runs `ioreg -c IOHIDSystem -d 1`. On the target machine the `-d 1` depth limit truncates the output before HIDIdleTime appears, so the regex in `idle_seconds_from_ioreg()` finds nothing and the function returns 0.0. A dead sensor is indistinguishable from a user who never pauses.

Confirmed on the target machine. `ioreg -c IOHIDSystem -d 1 | grep HIDIdleTime` returns nothing. Both `ioreg -c IOHIDSystem` and `ioreg -r -c IOHIDSystem -d 1` return the property correctly.

## Build

Three changes to `product/watcher/`. Keep the existing architecture, the footprint budget under 100 KB, zero dependencies, and no network calls. Do not restructure anything that is not named here.

1. **Repair the reading.** Use an `ioreg` invocation that actually returns HIDIdleTime on macOS 15 and later. Verify it by running it, not by reasoning about it.

2. **Make an unavailable sensor loud instead of silent.** This is the more important half of the fix. `idle_seconds_from_ioreg()` currently returns 0.0 when the property is missing, which is a lie that reads as valid data. Change the contract so a missing or unparseable reading is distinguishable from a genuine zero. Return `None` from the parser on no match, and in the written record set `idle_seconds` to `null` and `idle` to `false`, so any future analysis can tell "the user was active" apart from "we do not know". Sampling must never crash or skip because the sensor is unavailable, it degrades to null and carries on.

3. **Report the live reading in the status command.** `./watcher.py status` must print the current real idle seconds, read from the machine at that moment, or a plain language line saying the idle sensor is unavailable. This gives a human a five second way to confirm the sensor is alive, which is what nobody could do before. Do not print window titles or hosts, that restriction from the original brief stands.

## Definition of done, each item must be demonstrably yes

The original definition of done for this subsystem was satisfiable entirely by mocks, which is how the defect shipped. These criteria are written so that a mock cannot pass them.

- [ ] A test calls the real `read_idle_seconds()` against the actual machine, with no injected reader, and asserts the result is a number greater than zero. It may skip on non macOS platforms, it must not skip on macOS.
- [ ] A test proves the real reading changes. Take a live reading, sleep at least two seconds without simulating input, take another, and assert the second is greater than the first. This proves the sensor tracks reality rather than returning a constant.
- [ ] A test proves an unavailable sensor produces `null`, not `0.0`, in the written record, and that `idle` is `false` in that case.
- [ ] A test proves a genuine zero reading and an unavailable reading produce different written records.
- [ ] Existing idle marking behaviour is preserved. Over 180 seconds is idle, exactly 180 is not.
- [ ] `./watcher.py status` prints the live idle seconds on the real machine. Paste the real output in your report.
- [ ] All previously passing tests still pass. State the total count before and after.
- [ ] Footprint still under 100 KB, still zero dependencies, still no network imports.
- [ ] The README explains in plain language that a null idle reading means unknown rather than active.

## Also fix, secondary and low risk

The README and the original review both imply window titles are usually captured. In production they appeared on 108 of 9,922 samples, about 1 percent, because macOS only exposes titles for apps in the visible desktop space. Correct the README to state plainly that window titles are rarely available and nothing should depend on them. Do not change the title collection code.

## Explicitly out of scope

- Do not alter, migrate, backfill, or delete any existing data in `~/.shift-tracker/log/`. The 83 hours of zeros are evidence and they stay exactly as they are.
- Do not change the shift window, storage layout, sampling interval, or install scripts.
- Do not add a dependency, a network call, or a config file.

## Notes

- Code comments and README prose must not use em dashes, en dashes, hyphens, or colons as punctuation. File names and code syntax are exempt.
- Report only what you verified by running it. The previous pass on this task included a fabricated claim about a side effect that did not exist, it was caught, and it is now published in the case study. Every claim in your report will be independently re run by the reviewer.
