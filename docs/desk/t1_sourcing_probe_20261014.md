# T1 sourcing check, part 2: phase 1 probe results (14 October 2026)

Approved by the user on 2026-10-14: at most 64 requests, at least 10 seconds apart, outside the
nightly's hours, keeping each response's Date and Last-Modified headers, raw files hashed under
`data/raw/`. Sourcing only: no feature, outcome or store write. Used: 25 requests (00:41-00:46
IST, task Ready throughout), with `scripts/t1_source_probe.py`, which enforced the budget, the
spacing and the nightly-hours refusal. The other 39 were not needed and are not carried over.
Raw files and the request ledger are in `data/raw/t1_sources/` (outside the repository).

The only content checks were: each file's own date, the presence of the three index rows, and
whether the two publishers' closes for those rows are equal. No value is reported here.

## Every request

| # | Requested (IST) | URL | HTTP | Last-Modified (IST) | Date header (IST) | Bytes | SHA-256 (first 12) |
|---|---|---|---|---|---|---|---|
| 1 | 00:41:43 | https://liveindexsa.niftyindices.com/assets/js/historicalData.js | 200 | 2026-03-12 11:02 | 2026-10-14 00:41 | 502736 | 7da19ef9275e |
| 2 | 00:42:02 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_03092018.csv | 200 | 2018-09-04 01:10 | 2026-10-14 00:42 | 7398 | 1806666e72ea |
| 3 | 00:42:13 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_03122018.csv | 200 | 2018-12-03 23:20 | 2026-10-14 00:42 | 7385 | 25edf6976686 |
| 4 | 00:42:23 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_04022019.csv | 200 | 2019-02-04 23:30 | 2026-10-14 00:42 | 7527 | 7d6428f3efee |
| 5 | 00:42:34 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_01082019.csv | 200 | 2019-08-01 23:50 | 2026-10-14 00:42 | 7719 | cb5f8b3487eb |
| 6 | 00:42:44 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_03022020.csv | 200 | 2020-02-03 23:50 | 2026-10-14 00:42 | 7755 | 118d418ac13e |
| 7 | 00:42:55 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_03082020.csv | 200 | 2020-08-03 23:10 | 2026-10-14 00:42 | 7939 | 32933b84cd09 |
| 8 | 00:43:05 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_03022021.csv | 200 | 2021-02-03 23:20 | 2026-10-14 00:43 | 8486 | f577f222009b |
| 9 | 00:43:16 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_03082021.csv | 200 | 2021-08-03 23:20 | 2026-10-14 00:43 | 8575 | e8ada1a2c411 |
| 10 | 00:43:27 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_03022022.csv | 200 | 2022-02-03 23:20 | 2026-10-14 00:43 | 9613 | da89deab05ea |
| 11 | 00:43:37 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_03082022.csv | 200 | 2022-08-03 23:20 | 2026-10-14 00:43 | 9791 | 49325f89112d |
| 12 | 00:43:48 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_03022023.csv | 200 | 2023-02-03 23:20 | 2026-10-14 00:43 | 10276 | b63ae4e18e39 |
| 13 | 00:43:58 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_03082023.csv | 200 | 2023-08-03 23:20 | 2026-10-14 00:43 | 10683 | 1caa2fddd845 |
| 14 | 00:44:09 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_05022024.csv | 200 | 2024-02-05 23:20 | 2026-10-14 00:44 | 10840 | 7de1f9c6c213 |
| 15 | 00:44:19 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_05082024.csv | 200 | 2024-08-05 23:20 | 2026-10-14 00:44 | 12492 | b7c313e4bb91 |
| 16 | 00:44:30 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_04022025.csv | 200 | 2025-07-23 00:09 | 2026-10-14 00:44 | 14283 | 3a4e5d6476ff |
| 17 | 00:44:41 | https://www.niftyindices.com/Daily_Snapshot/ind_close_all_04082025.csv | 200 | 2025-08-04 23:30 | 2026-10-14 00:44 | 14794 | 5200705d0edd |
| 18 | 00:45:12 | https://nsearchives.nseindia.com/content/indices/ind_close_all_03092018.csv | 200 | 2019-01-17 17:14 | 2026-10-14 00:45 | 7398 | 1806666e72ea |
| 19 | 00:45:23 | https://nsearchives.nseindia.com/content/indices/ind_close_all_03122018.csv | 200 | 2019-01-17 17:14 | 2026-10-14 00:45 | 7464 | 6683cf9bcc21 |
| 20 | 00:45:34 | https://nsearchives.nseindia.com/content/indices/ind_close_all_04022019.csv | 200 | 2019-03-06 15:33 | 2026-10-14 00:45 | 7606 | aade63afa768 |
| 21 | 00:45:44 | https://nsearchives.nseindia.com/content/indices/ind_close_all_01082019.csv | 200 | 2019-08-23 11:19 | 2026-10-14 00:45 | 7799 | 67a278f1aaca |
| 22 | 00:45:55 | https://nsearchives.nseindia.com/content/indices/ind_close_all_03022020.csv | 200 | 2020-07-21 16:18 | 2026-10-14 00:45 | 7837 | 11bcd3be7785 |
| 23 | 00:46:05 | https://nsearchives.nseindia.com/content/indices/ind_close_all_03082020.csv | 200 | 2020-08-03 23:05 | 2026-10-14 00:46 | 7939 | 32933b84cd09 |
| 24 | 00:46:16 | https://nsearchives.nseindia.com/content/indices/ind_close_all_03022021.csv | 200 | 2021-02-03 23:20 | 2026-10-14 00:46 | 8486 | f577f222009b |
| 25 | 00:46:26 | https://nsearchives.nseindia.com/content/indices/ind_close_all_03082021.csv | 200 | 2021-08-03 23:20 | 2026-10-14 00:46 | 8575 | e8ada1a2c411 |

Request 1 (the historical-data form's script) showed the form's interface code but not its data
endpoint, so the planned 16 Historical Data requests were not made: the daily files below answer
the probe's questions directly. The 8 planned India VIX requests were dropped because India VIX is
in the same daily file.

## What the files show

- **Coverage.** The NSE Indices Daily Snapshot file exists on all 16 sampled dates, two per year
  from September 2018 to August 2025. Each file's own `Index Date` equals the date requested (no
  wrong-day file, the P2-003 shape), and each holds rows for NIFTY 50, NIFTY 500 and INDIA VIX
  with open, high, low and close. Full daily coverage is not measured; that is phase 2.
- **Publication evidence (niftyindices.com).** `Last-Modified` falls on the trading day itself,
  between 23:10 and 23:50 IST, for 14 of the 16 files; for 3 September 2018 it is 01:10 IST the
  next day; for 4 February 2025 it is 23 July 2025, so that file was rewritten later and its header
  no longer shows when it first appeared. The times sit on 10-minute marks, which suggests an
  archive job: the header shows when the archive copy was written, which can be later than the
  close was first published, never earlier. Every observed time except the rewritten file is
  before the next session's 09:15 open.
- **NSE's copy (nsearchives.nseindia.com).** For all 8 compared dates the three rows' dates and
  closes are identical to niftyindices' (whole files byte-identical on 4). Its `Last-Modified` is
  weeks to months later up to February 2020 (re-uploads on 2019-01-17, 2019-03-06, 2019-08-23
  and 2020-07-21) and the same evening from August 2020. It corroborates the values, not the
  timing, for the early years.
- **The Date header** is the server's time of each response (14 October 2026). It is kept as
  asked but is not publication evidence.

## Coverage and provenance by input and year (sampled dates only)

NIFTY 50, NIFTY 500 and India VIX come from the same file, so each year's evidence is the same for
all three.

| Year | Sampled dates present | Last-Modified (niftyindices) | NSE copy |
|---|---|---|---|
| 2018 (Sep-Dec, warm-up) | 2 of 2 | same day 23:20; next day 01:10 | same values; re-uploaded 2019-01-17 |
| 2019 | 2 of 2 | same day 23:30, 23:50 | same values; re-uploaded 2019-03-06, 2019-08-23 |
| 2020 | 2 of 2 | same day 23:50, 23:10 | same values; re-uploaded 2020-07-21; then same evening |
| 2021 | 2 of 2 | same day 23:20, 23:20 | same values; same evening |
| 2022 | 2 of 2 | same day 23:20, 23:20 | not requested |
| 2023 | 2 of 2 | same day 23:20, 23:20 | not requested |
| 2024 | 2 of 2 | same day 23:20, 23:20 | not requested |
| 2025 | 2 of 2 | same day 23:30; one rewritten 2025-07-23 | not requested |

## What this means for the knowledge rule

The headers never prove when a close was first published; at best they bound when the archive
copy existed. They are consistent with every sampled close being public before the next session
opened, except the one rewritten file, whose header says nothing about its first appearance.
Under the pre-registration's strict rule (no proven publication date, no knowledge) the index
inputs would stay UNKNOWN; T1 addendum 2 therefore states an explicit ASSUMPTION that a close for
session D is known from session D+1, citing this evidence.

## Phase 2 (not approved; nothing fetched)

The full daily history from September 2018 is about 1,830 files from niftyindices, one request
each. At one request every 10 seconds that is about five hours, to be split across several
sessions outside the nightly's hours. Proposed separately when you want it.
