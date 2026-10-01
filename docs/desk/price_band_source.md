# Phase A — circuit-band source verification

Verified 2026-10-01 before implementation. Source: NSE All Reports,
`https://www.nseindia.com/all-reports`, whose
`https://www.nseindia.com/api/daily-reports?key=CM` metadata names
`CM-PRICEBAND-COMPLETE-LIST`, displayed as **CM - Price Band complete list**.

- Dated URL: `https://nsearchives.nseindia.com/content/equities/sec_list_DDMMYYYY.csv`.
- Rolling URL: `https://nsearchives.nseindia.com/content/equities/sec_list.csv`.
- Columns: `Symbol,Series,Security Name,Band,Remarks`.
- Observed bands: 2, 5, 10, 20, **40**, and `No Band`. Do not silently discard 40.
- Real examples on the 30 September 2026 snapshot: A2ZINFRA/EQ = 5;
  RELIANCE/EQ = No Band. NSE's daily-price-band page explains that derivative
  securities have a dynamic operating range which may flex, not a fixed band.

## History and publication

The dated files for 2020-01-02, 2025-01-02, 2025-09-30, 2026-09-29, and
2026-09-30 returned HTTP 200 with the expected CSV header and different historical
content. 2019-10-01 returned 404. This establishes some historical availability,
not complete coverage. Missing/unverified dates remain UNKNOWN, with no backward
fill or use of today's list for past events.

Observed Last-Modified values: 2020-01-02 17:10:05 IST; 2025-01-02 17:40:37 IST;
2026-09-30 17:58:10 IST. No guaranteed daily publication time was found. The rolling
30 September file was modified one second after its dated counterpart.

## Effective session — important distinction

The complete list dated D is the snapshot published after D's close **for the next
trading session**. Direct cross-check: the 15 band changes between the 29 and
30 September complete lists exactly match `eq_band_changes_01102026.csv`'s changes
for 1 October. That change notice was published 30 September at 17:58:08 IST.
For example AASTHA changes 10 to 5; the September 30 list already contains 5.

Desk assessments and scans run after close and plan entry at the next open. Their
band lookup uses the same dated report D, known by the as-of day D. The source
record's `event_date` is the **dated snapshot**, not a claim that its band applied
during that day's trading. Output explicitly labels it next-session. Historical
intraday/circuit-hit evaluation must use the preceding trading session's snapshot.
An absent exact dated snapshot is UNKNOWN; do not carry an older snapshot forward
across a missing report. Publication after the requested knowledge cutoff is invisible.

Source metadata and raw probe responses are preserved under
`data/raw/price_bands_source_probe/` (gitignored). A committed small CSV fixture
preserves unchanged source rows with their full-file hash and provenance.

## Implementation proof

Ten dated reports (2026-09-17 through 2026-09-30) inserted 35,427 rows into the
Desk store. Independent grouped SQLite counts sum to the same total. September
30 contains 3,551 rows. A2ZINFRA EQ is FIXED 5%; RELIANCE EQ is DYNAMIC (No Band).
No missing report is filled with a current or earlier report.

Real-source fixture tests compute the two-day locked loss from the CSV's 5% band,
verify dynamic labelling, knowledge cutoffs, replay watermarks and append-only
enforcement. Full suite: `Ran 561 tests in 165.944s`, `OK`, Python exit code 0.
The scheduled ingestion sequence now downloads bands before making backups.
