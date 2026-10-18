# Retrying a battery-skipped nightly the same evening: a proposal (18 October 2026)

A proposal for the user's decision. Nothing is changed: not the scheduled task, not the script.

## Today

- One scheduled task, `PramanDailyIngest`, one weekly trigger: weekdays at 18:00 IST. Settings:
  start when available (a start missed while the laptop slept or was off runs when it is next
  available), wake to run, may start on battery, `IgnoreNew` for a second instance, 3-hour limit.
- The script (scripts/weekly_ingest.py `main`) checks power first: on battery below 30%
  (`MIN_BATTERY_PERCENT`), no step runs; it writes one WARN line to logs/weekly_ingest.log and a
  notice to that day's brief, and exits 0. Nothing tries again until the next weekday's 18:00.
- 15 Oct: started 18:00 on battery at 13%, skipped. 16 Oct: started 20:35 (the laptop was available
  late) on battery at 18%, skipped. Both sessions become Strategy 0 burn-in gaps, and their tick sizes
  stay UNKNOWN for good.

A same-evening retry that runs would have recorded that session's data, its tick sizes (Angel's master
for the day can be downloaded until it is regenerated at 08:00 the next morning), its band list known
the same day, and a Strategy 0 decision (Strategy 0 decides a session only before 09:00 IST on the
next weekday).

## What every option needs

1. **A "done today" check** at the start of the script: if a run that started on today's IST date
   has already finished (its `finished ... overall=` line is in the log), exit without running and
   without a skip notice. Your decision: does a run that finished with ERROR count as done (no retry)
   or not? Proposed: it counts; an ERROR is looked at, not retried blindly.
2. **One skip notice per evening in the brief**, listing the attempts ("skipped at 18:00 (13%),
   20:00 (16%), 22:00 (19%)"), while the log keeps one line per attempt.
3. Unchanged: the 30% rule on every attempt, the branch and working-tree guard (P8-059), one task,
   no overlap (`IgnoreNew`).

## Options

| | A. Two more time triggers | B. A power-source trigger | C. Restart on failure |
| --- | --- | --- | --- |
| Change | add weekday triggers at 20:00 and 22:00 IST to the same task; the script's done-today check | add an event trigger to the same task: System log, Kernel-Power event 105 (power source changed); done-today check plus an evening window | task setting "if the task fails, restart every 30 minutes, up to 8 times"; the battery skip exits non-zero instead of 0 |
| When it retries | at 20:00 and 22:00 only | within a minute of plugging in (or unplugging) | every 30 minutes for 4 hours |
| Plugged in at 20:30 | runs at 22:00 | runs at about 20:31 | runs at the next 30-minute retry |
| Evidence it works here | standard calendar triggers, like today's | event 105 is logged on this laptop (6 times on 17-18 Oct), on unplug as well as plug, sometimes twice | not verified: whether Task Scheduler's restart-on-failure fires on a non-zero exit code from the program must be tested on this machine |
| Risks | up to two hours' wait; plugged in after 22:00 means no run until the next weekday | fires at any hour, so the script must refuse outside an evening window (proposed 18:00 to 23:59 IST) to keep runs out of market hours and the day; fires on unplugging too (the battery check then skips again); hard to test end to end | Task Scheduler then shows every skip as a failed run; retries keep coming while still on battery below 30%, each one skipping again |
| Test | the done-today check and the dedupe are plain functions over the log and a clock (offline tests); the triggers are checked by reading the task XML | the same offline tests plus the window; the trigger itself only by plugging in for real | needs a real-machine test of the restart behaviour first |

**If you want one:** A is the simplest and most predictable, and keeps today's behaviour otherwise; B
is the fastest after plugging in but needs the evening window and is harder to test; C changes what a
skip looks like in Task Scheduler and rests on behaviour not yet verified here. A and B can also be
combined (B for speed, A as a fallback).

Not covered by any option: an evening spent entirely on battery below 30% is still skipped.
