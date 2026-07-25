# Scoreboard

Per task metrics for the worked example. Costs are developer tokens for the build itself, the engineering lead's time is not metered here.

| Task | Discovery questions | First PRD accepted | Review findings (blocking / cosmetic / anomalies) | First pass acceptance | Developer tokens |
| --- | --- | --- | --- | --- | --- |
| 01 shift tracker watcher | 5 | Yes, with one correction (lightweightness) | 0 / 3 / 1 fabricated claim in the developer's self report | No, rejected at acceptance on one blocking defect found only by production data | 145,581 |
| 01a idle detection fix | 0, the defect was the requirement | Not applicable, fix brief | 0 / 0 / 0, and the self report was true this time | Yes, approved at review, install and one shift still pending | Not captured |
| 01b installer fix | 0, the defect was the requirement | Not applicable, fix brief | 0 / 0 / 0, self report true again | Yes, approved at review, agent verified alive on the real machine | Not captured |

## Notes

- Task 01 anomaly. The developer's closing report claimed a side effect (a collaboration log issue) that does not exist. Caught because the reviewer verifies every claim independently. See tasks/01-shift-tracker/review.md.
- Task 01 rejection. The review gate passed a subsystem that had never once run for real. Eight shifts and 9,922 production samples showed idle detection returning exactly zero every time. The definition of done said "idle over 180 seconds marks the sample idle", a claim about logic that a mock satisfies. It never required a real reading from the real machine. See tasks/01-shift-tracker/acceptance.md.
- Task 01a verification. The rewritten definition of done was tested by reintroducing the original bug in a scratch copy. The new tests failed, which proves they would catch a regression. A test that would also pass while broken proves nothing. See tasks/01-shift-tracker/review-fix.md.
- Task 01a token cost was not captured, because the run was logged with final message output only. Recorded as unknown rather than estimated.
- Three silent failures, one class, all surfaced on 25 July on one small tool. The idle sensor returned a plausible zero while blind. The launchd agent sat disabled for a day with nothing to say about it, costing Friday 24 July. And install.sh printed "Shift Tracker is installed and loaded" over an agent that was dying thirty times a minute, because it checked that launchd knew the service rather than that the process survived.
- Task 01b was found by running the installer on the real machine and reading one number, the launchd exit status column. Reading the code would not have found it. The tests passed, the plist linted, launchd knew the service, and an approving review of the previous fix had already been committed. See tasks/01-shift-tracker/review-fix-2.md.
- Cause of 01b. The source plist carried placeholder tokens and install.sh swapped them with plutil -replace on individual array positions, which inserts rather than overwrites on current macOS. The installed agent received five arguments where the watcher accepts one, so it exited 2 forever. The array is now written whole with plistlib.
