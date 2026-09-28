# Your first paper trade

Run these PowerShell commands from the `praman` folder. `python -m desk.cli`
is the runnable form of `desk`. Prices, dates and IDs below are examples to replace.

## Each trading evening, in order

1. Confirm the scheduled ingestion **finished today**. Check the latest run time,
   result and log summary, including gaps and the `bhavcopy_today` step:

   ```powershell
   Get-ScheduledTask -TaskName "PramanDailyIngest" | Get-ScheduledTaskInfo
   Get-Content logs/weekly_ingest.log -Tail 80
   ```

   If the task is missing, use the registration instructions in
   [OPERATIONS.md](../OPERATIONS.md#daily-ingestion-2026-09-28--operational-change-not-a-pre-registration-amendment).
   If ingestion is still running, wait. If it failed, inspect the log and resolve
   the reported problem; then run `python scripts/weekly_ingest.py`.
2. Run the daily review. It requires today's bhavcopy, completes pending entries,
   checks stops, and reports changes and exits:

   ```powershell
   python -m desk.cli evening
   ```

3. For a **new idea**, copy the template to a new filename, edit every example
   using evidence you have reviewed, then assess:

   ```powershell
   Copy-Item theses/_template.yaml theses/AXISBANK-2026-09-28.yaml
   notepad theses/AXISBANK-2026-09-28.yaml
   python -m desk.cli assess AXISBANK --thesis theses/AXISBANK-2026-09-28.yaml
   ```

   Read every gate result. Only if the result is **ELIGIBLE**, use the printed
   `decision_id` (here, `12`) to open **the SAME evening**:

   ```powershell
   python -m desk.cli paper open 12
   ```

   `PENDING` is normal: the next session's data has not arrived. The next evening's
   monitor completes that approved entry at the first available session open after
   the original request date (UTC). Let the monitor resume it; a fresh manual open
   request resets the date boundary. Waiting until tomorrow to first request an
   open moves the earliest fill forward. Use current assessments without `--as-of`.

## Decision states

| State | Meaning and next action |
| --- | --- |
| INSUFFICIENT | Data quality or required evidence failed. Resolve the listed gaps, ingest and reassess. |
| RESEARCH_REQUIRED | Structural integrity needs investigation. Resolve the flagged issue with evidence, then reassess. |
| WATCH | Thesis is incomplete. Fill the missing thesis fields and reassess. |
| ELIGIBLE | Gates permit a paper entry. Review the approved size and open that evening if proceeding. |
| VETO | Surveillance, liquidity, risk or behavioural rules block entry. Do not open; reassess only when the stated cause is resolved. |
| EXPIRED | The unused thesis is past its horizon. Retire it or write a fresh, evidence-backed idea and reassess. |

## Exits and review

The five thesis triggers are **price** (stop/target), **time** (horizon), **evidence**
(invalidation), **risk** (budget breach), and **portfolio** (allocation change).
**Current limitation:** `desk monitor`, also called by `desk evening`, automatically
fills **stop exits only**: at the session open if it gaps below the stop, otherwise
at the stop if touched. It does not automatically execute targets or the other four
triggers. Review those yourself; for non-price exits use the next session's actual
open once available. Manual close records the date and price you supply; it does
not calculate or validate a fill for you.

```powershell
python -m desk.cli monitor
python -m desk.cli status
python -m desk.cli journal show "AXISBANK:7"
python -m desk.cli paper close "AXISBANK:7" --event-date 2026-10-02 --price 1010 --reason "evidence: margin hypothesis invalidated; next-session open"
```

`status` shows open risk, open trade IDs and ingestion health. Use its exact trade
ID (`symbol:thesis_id`, not the decision ID) for `journal show` and `paper close`.
The journal shows that trade's events. Check it before and after a manual close.

## Three common refusal cases

1. **Today's data is missing:** wait for ingestion or fix and rerun it, then run
   `evening` again. Weekends/holidays also refuse because no session exists; resume
   on the next trading evening. Status's health line alone does not prove today's
   data is present.
2. **Decision is not ELIGIBLE / has no persisted thesis or size:** follow its gate
   reasons and the state table, supply the complete thesis, and reassess. Open only
   the new eligible decision ID.
3. **Historical or stale decision:** assess again against the latest ingested data
   without a historical `--as-of`, then open that same evening. The initial open
   refuses an as-of date more than one calendar day old, including across weekends.
