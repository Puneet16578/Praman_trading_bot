# Knowledge-date audits, 18 October 2026

Read-only. No stored row was changed.

## 1. P8-083: band rows known before we had them

Question: before 3d7423e (committed 2026-10-14 16:07:32 IST), was any stored price-band row's
knowledge date earlier than the date we fetched it, and did any paper decision read one?

**Answer: none, so no paper decision read one.** The Desk store holds 32,118 band rows: nine lists
dated 1 Oct to 14 Oct. The 24,978 rows recorded before 3d7423e (lists dated 1 to 12 Oct) were each
fetched the same evening NSE published them, so their knowledge date equals the IST date of the
fetch. The only late list, 13 Oct's, was fetched on 14 Oct at 19:42 IST, after 3d7423e, and is
stored as known from 14 Oct.

| List dated | NSE Last-Modified (IST) | Fetched (IST) | Knowledge date | Rows |
| --- | --- | --- | --- | --- |
| 1 Oct | 1 Oct 19:39 | 1 Oct 21:25 | 1 Oct | 3,574 |
| 5 Oct | 5 Oct 17:58 | 5 Oct 18:08 | 5 Oct | 3,559 |
| 6 Oct | 6 Oct 17:55 | 6 Oct 21:12 | 6 Oct | 3,562 |
| 7 Oct | 7 Oct 19:24 | 7 Oct 20:56 | 7 Oct | 3,565 |
| 8 Oct | 8 Oct 18:01 | 8 Oct 19:01 | 8 Oct | 3,563 |
| 9 Oct | 9 Oct 19:16 | 9 Oct 19:57 | 9 Oct | 3,585 |
| 12 Oct | 12 Oct 18:23 | 12 Oct 21:19 | 12 Oct | 3,570 |
| 13 Oct | 13 Oct 19:00 | 14 Oct 19:42 | 14 Oct | 3,570 |
| 14 Oct | 14 Oct 18:22 | 14 Oct 19:42 | 14 Oct | 3,570 |

Within a day: knowledge is stored as a date, so a list fetched at 21:25 is "known" on that whole
day. No paper decision dated that day ran before the fetch: in the nightly, circuit_bands runs
before desk_scan and auto_paper, and a live decision can only read rows already in the store.
Audit replays filter on recorded_at (desk/replay.py), so they see what the decision saw.

Not in the store: the September lists that docs/desk/price_band_source.md says were inserted on
1 Oct (35,427 rows). They were lost when the Desk store was reset on 1 Oct, before the nightly began
(P8-025, "durable Desk store cleared during a proof": "the present 3,574 rows do not substantiate that
historical coverage. Missing historical bands remain unknown, never zero"). So there is nothing to
correct and no new defect.

## 2. Other nightly data dated by the source (report only; nothing fixed)

Who can read a row fetched late, under a decision dated before the fetch:
- **A live nightly decision: no.** It runs after that night's fetches and can only read rows already
  stored; a row fetched on a later night does not exist yet. Strategy 0 decides only the latest
  session, and only before 09:00 IST on the next weekday; otherwise the session is a burn-in gap.
- **An audit replay: no.** desk/replay.py reads both stores through recorded_at watermarks
  (desk/lib/store.py `get_replay_connection`, `get_desk_replay_connection`).
- **Anything that computes a decision for an earlier date later, through a live connection: yes**,
  for every dataset in the table except the last two. In the code: `desk assess --as-of <past
  date>` (desk/cli.py, live connections), `run_scan_range` over past dates (used only by
  scripts/desk_scan_proof.py, on a copy), and research that reads knowledge dates by design (the
  shadow analysis, the T1 build). Such a reader sees a file fetched on night N as known from its
  source date, before N.

| Dataset (nightly step) | Knowledge date comes from | How a file arrives late | Late file visible to a decision dated before the fetch? |
| --- | --- | --- | --- |
| Bhavcopy, Praman `bhavcopy` (bhavcopy, bhavcopy_today) | IST date of NSE's Last-Modified (src/ingestion/nse_market_data/bhavcopy.py) | catch-up after skipped nights: Monday's run fetches 15 and 16 Oct | yes, through a live recomputation |
| Announcements, `corporate_announcements` (announcements, announcements_recent) | the filing's own publication date (`sort_date`); a changed-content vintage of an already stored filing gets the fetch date (announcements_bulk.py `ingest_bulk`) | the bulk refresh re-reads from its last complete day: 13 Oct's filings were stored on 14 Oct | yes, through a live recomputation; for the disclosure check, the COMPLETE receipt it also needs is capped at its recorded date (P8-049), but a live recomputation sees later receipts too |
| Equity identities, `security_identities` (announcements_recent) | the trading day of NSE's archive file (announcements_bulk.py, `knowledge_date=day`) | the archive for a day can be fetched on any later night | yes, through a live recomputation |
| Corporate actions (corporate_actions) | the matching announcement's date for bonuses and splits; the ex-date for demergers, capital reductions and actions with no announcement path (corporate_actions.py) | each night fetches a recent window, so an action can be stored days or weeks after its announcement or ex-date | yes, through a live recomputation |
| ASM and GSM lists (asm_gsm) | the circular's own date: `cirDate` for ASM, the "Date:" in the circular for GSM | each night fetches a date range, so a missed circular is stored later | yes, through a live recomputation |
| Tick sizes, `tick_sizes` (tick_sizes) | IST date of the master's Last-Modified (desk/tick_sizes.py) | only the current master can be downloaded; "late" means after midnight but before the 08:00 regeneration, when the file is still the previous day's | yes in that narrow case, through a live recomputation |
| Price bands, `circuit_bands` (circuit_bands) | since 3d7423e, the later of Last-Modified and the fetch date (P8-083) | catch-up of missed lists (P8-082) | no |
| Announcement receipts, `source_freshness` | what a receipt certifies is capped by the date it was recorded (P8-049) | — | no |

Not in the table: the Desk's own records (scan, executions, Strategy 0 events, runs, monitor,
annotations) are written when the decision is made and carry its watermarks; the ISIN map is a file
rebuilt nightly from dated snapshots, with no knowledge date per row, and was not assessed here.

One P8-083 consequence for live decisions: if a run before 09:00 on D+1 decides session D, a band
list dated D fetched that morning is known from D+1 and invisible to that decision, so its band is
UNKNOWN (stricter). Bhavcopy and announcements fetched that morning stay visible (source-dated).
Backfilling old lists for research would need its own labelled rule, decided at that point (user,
2026-10-18).
