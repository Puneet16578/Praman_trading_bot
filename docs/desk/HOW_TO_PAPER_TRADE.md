# Your first paper trade

Run these PowerShell commands from the `praman` folder. `.\desk <command>` is the short form
(`desk.bat`, in this same folder); `python -m desk.cli <command>` is the long form and always
works as a fallback if the short form doesn't resolve for some reason (e.g. PowerShell's execution
policy blocking local scripts). Prices, dates and IDs below are examples to replace.

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
   .\desk evening
   ```

3. For a **new idea**, copy the template to a new filename, edit every example
   using evidence you have reviewed, then assess:

   ```powershell
   Copy-Item theses/_template.yaml theses/AXISBANK-2026-09-28.yaml
   notepad theses/AXISBANK-2026-09-28.yaml
   .\desk assess AXISBANK --thesis theses/AXISBANK-2026-09-28.yaml
   ```

   Read every gate result. Only if the result is **ELIGIBLE**, use the printed
   `decision_id` (here, `12`) to open **the SAME evening**:

   ```powershell
   .\desk paper open 12
   ```

   **Entry convention (since 2026-10-04): a day limit order.** The limit is your
   thesis `planned_entry` (the price the decision was sized at) plus 0.5 × ATR20 at
   the decision date. On the first session after your open request: if that
   session opens at or below the limit, the paper entry fills at the open;
   otherwise, if the session's low reaches the limit, it fills at the limit;
   otherwise it is **NO FILL** — the order is cancelled, never carried to a later
   session, and you reassess for a new decision. Quantity is the approved position
   size, unchanged. A demerger between the decision and the fill refuses the open.
   **Since 2026-10-04 (later the same day) `desk assess` sizes the position at that
   limit price**, not at `planned_entry`, so a limit fill can never push the planned
   loss past the per-trade budget (follow-up 3, `docs/desk/shadow_replay_followup3_review.md`;
   P8-043 closed). Positions are a little smaller: about 2% where the per-stock cap
   binds, about 20% where the per-trade budget binds. The assessment prints the
   price it sized at.

   `PENDING` is normal: the next session's data has not arrived. The next evening's
   monitor completes that approved entry at the first available session after the
   original request date, under the same limit rule (it can also end as NO FILL).
   Let the monitor resume it; a fresh manual open request resets the date boundary.
   Waiting until tomorrow to first request an open moves the earliest fill forward.
   Use current assessments without `--as-of`.

   Prices are kept on the decision's share basis: if a bonus or split goes ex after
   your decision, the store's adjustment factor converts later prices, so the stop,
   quantity and P&L stay consistent (P8-044).
   Closing a position later works the same way — see "Exits and review" below.

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
triggers — you judge those yourself, from `desk evening`'s "what changed" line (new
disclosures/surveillance for `evidence`), your thesis's own horizon date (`time`),
`desk status`'s open-risk line (`risk`), or your own judgment (`portfolio`).

When one of those four applies, close the position **manually — but there is no
`--price` or `--event-date` flag, on purpose**: exactly like `paper open`, a manual
close cannot record any exit price on any past date you choose. It fills at the
store's own real, raw price for the first session strictly after the moment you run
the command — the same treatment every fill gets, entry or exit, manual or automatic
(a stop). The real round-trip sell-side cost is computed separately and recorded in
its own field, never folded into the price itself, so two identical trades always
show identical realized P&L regardless of how they closed. You only ever supply the
`trade_id` and a mandatory `--reason`:

```powershell
.\desk monitor
.\desk status
.\desk journal show "AXISBANK:7"
.\desk paper close "AXISBANK:7" --reason "evidence: margin hypothesis invalidated"
```

`status` shows open risk, open trade IDs and ingestion health. Use its exact trade
ID (`symbol:thesis_id`, not the decision ID) for `journal show` and `paper close`.
The journal shows that trade's events. Check it before and after a manual close.
Just like a pending entry, if the next session's data isn't in the store yet this
prints `PENDING` and `desk monitor`/`desk evening` completes it automatically —
no need to re-run the close command yourself.

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
