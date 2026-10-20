# ISIN freshness and HTTP 404: 21 October 2026

Read-only audit. No downloader, URL, store or metadata changes. No market-data
download attempted. No S1 evaluation performed.

## Failed request and history

`weekly_ingest.log` reports the **20 October current-day CM/UDiFF ISIN snapshot**
failed with HTTP 404 at the 22:00 retry; the ISIN step finished WARN at 22:06:15.
The current failure starts on that date. The previous actual run, 19 October,
refreshed successfully. 15/16 October were skipped on battery. An earlier
current-day 404 on 3 October is a separate episode, not proof of a continuing
outage. Historical snapshot warnings elsewhere in the log are different requests.

Call path: `scripts/weekly_ingest.py:step_isin_map` ->
`scripts/build_isin_map.py:main` -> `fetch_isin_snapshot(today)` -> installed
`jugaad_data.nse.bhavcopy_save`. This is the ISIN-bearing CM file, not the
`sec_bhavdata_full` file used by price ingestion.

Local package source shows this sequence for modern dates:

1. UDiFF archive, for 20 October:
   `https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20261020_F_0000.csv.zip`.
2. Daily-reports fallback, report code `CM-UDIFF-BHAVCOPY-CSV` for the same date.
3. Legacy `CM - Bhavcopy(csv)` fallback via
   `https://www.nseindia.com/api/reports`, with date `20-Oct-2026`, category
   `capital-market`, section/type `equities`, mode `single`.

These data URLs are **source-code descriptions only; not requested in this audit**.
The package suppresses intermediate request/ZIP errors before its final fallback.
The nightly warning retains only the final HTTP 404, not the failing response URL
or the intermediate causes. Thus the precise intermediate failure is NOT VERIFIED;
the final propagated HTTP error comes from the legacy fallback in this code path.
The holiday explains why a dated 20 October file would not be expected, but the
warning alone does not prove that every preceding request failed for that reason.

## Newest accepted snapshot and remaining freshness

Verified the map checksum against `data/raw/nse_symbol_isin_current.meta.json`.
Latest recorded snapshot: **19 October 2026**. Build timestamp:
`2026-10-19T18:07:44.939805+05:30`. Build source is `refresh`, not inferred mtime.
The 20 October 404 preserved this map and timestamp as designed.

`shared/isin_map_metadata.py:trading_days_since_build` counts distinct stored
bhavcopy event dates after the build date, through the assessment date, known by
that date. `desk/gates/checks.py` rejects only when `age > 5`.
Read-only query as of 21 October before market open returns **age 0**; the latest
stored session is 19 October. This passes the ISIN-freshness component of G1,
not necessarily every other G1 condition for every symbol.

If no refresh succeeds, **five more stored trading sessions remain acceptable**
(ages 1 through 5); rejection starts on the **sixth** (age 6). An un-ingested date
does not advance this counter, though other G1 checks can fail for absent data.
No future trading-calendar dates are assumed or asserted here.

## Documentation-only requests, in order

Each URL was requested separately; no data-file link or report API was fetched.

1. [NSE All Reports](https://www.nseindia.com/all-reports) — accessible.
   Lists CM-UDiFF Common Bhavcopy Final (zip) and explains that the old CM CSV
   formats were discontinued from 8 July 2024 (circular 62424, 12 June 2024).
   This is the already-handled format transition, not evidence of a new move.
2. `https://www.nseindia.com/market-data/bhavcopy` — browsing tool reported the
   page inaccessible. Its contents and HTTP status were not verified.
3. `https://www.nseindia.com/products-services/initial-public-offerings-udiff` —
   browsing tool reported the page inaccessible. Its contents and HTTP status
   were not verified.

No same-file, same-format move to a new official URL was established. **Downloader
unchanged.** Proposal: let the next ordinary trading-session nightly try its
existing source. If that fails, inspect the resulting log and seek approval for
a narrow diagnostic that records each fallback's status without downloading
additional research history. Do not replace the source based on a holiday 404.
