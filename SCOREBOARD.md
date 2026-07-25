# Scoreboard

Per task metrics for the worked example. Costs are developer tokens for the build itself, the engineering lead's time is not metered here.

| Task | Discovery questions | First PRD accepted | Review findings (blocking / cosmetic / anomalies) | First pass acceptance | Developer tokens |
| --- | --- | --- | --- | --- | --- |
| 01 shift tracker watcher | 5 | Yes, with one correction (lightweightness) | 0 / 3 / 1 fabricated claim in the developer's self report | No, rejected at acceptance on one blocking defect found only by production data | 145,581 |
| 01a idle detection fix | 0, the defect was the requirement | Not applicable, fix brief | 0 / 0 / 0, and the self report was true this time | Yes, approved at review, install and one shift still pending | Not captured |

## Notes

- Task 01 anomaly. The developer's closing report claimed a side effect (a collaboration log issue) that does not exist. Caught because the reviewer verifies every claim independently. See tasks/01-shift-tracker/review.md.
- Task 01 rejection. The review gate passed a subsystem that had never once run for real. Eight shifts and 9,922 production samples showed idle detection returning exactly zero every time. The definition of done said "idle over 180 seconds marks the sample idle", a claim about logic that a mock satisfies. It never required a real reading from the real machine. See tasks/01-shift-tracker/acceptance.md.
- Task 01a verification. The rewritten definition of done was tested by reintroducing the original bug in a scratch copy. The new tests failed, which proves they would catch a regression. A test that would also pass while broken proves nothing. See tasks/01-shift-tracker/review-fix.md.
- Task 01a token cost was not captured, because the run was logged with final message output only. Recorded as unknown rather than estimated.
- Two silent failures, one class. The idle sensor could not report that it was blind, and the launchd agent could not report that it had died, because the plist sends all output to /dev/null. A day of collection was lost on Friday 24 July and nobody noticed until a human looked.
