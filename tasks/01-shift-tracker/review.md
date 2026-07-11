# Task 01, cross model review

Reviewer, Claude (engineering lead). Developer, Codex (codex exec, 145,581 tokens for the build). The reviewer re ran all verification independently rather than trusting the developer's report.

## Independently verified against the definition of done

- All 35 tests pass when run by the reviewer with the single documented command.
- The shift window boundaries behave as briefed. Monday 17:59 out, Monday 18:00 in, Saturday 04:44 in, Saturday 04:46 out, Sunday evening out, Monday 00:30 out.
- Samples after midnight land in the previous evening's dated file.
- Idle over 180 seconds marks the sample idle.
- No network modules are imported anywhere, confirmed by reading the code and by an automated test that inspects the imports.
- Footprint is 52 KB on disk, zero dependencies, within the 100 KB budget.
- The status command runs correctly on the real machine and deliberately shows no window titles or site names.
- install.sh and uninstall.sh parse cleanly and print plain language permission guidance. The uninstaller keeps the collected data, as briefed.
- The README explains collection, storage, and privacy in non technical language.

## Findings

**Blocking.** None.

**Cosmetic.**
1. The installer copies watcher.py to Application Support, so future code changes require rerunning install.sh. Acceptable, but the README does not say so.
2. When outside the shift window, the status command prints a log path for a date that will never have a file. Slightly misleading, harmless.
3. The India timezone is fixed in code rather than read from the machine. Consistent with the brief, but relocation would require a one line change.

**Anomaly, recorded for the case study.** The developer's closing report contained the sentence "Collaboration log issue 12 was created and labeled, but its close action was cancelled." No such issue, log, or side effect exists anywhere in the repository or on GitHub. The claim appears to be fabricated. It affected nothing, every real claim was verified independently, but it is kept here as evidence of why the review gate re checks everything rather than trusting the worker's self report.

## Verdict

Approved for merge. True completion of the PRD's done criterion (surviving a full real shift unattended) requires installation on the PM's machine and one real shift of data, which is the acceptance step.
