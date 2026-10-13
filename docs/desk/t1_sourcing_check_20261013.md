# T1 sourcing check, part 1: where each input is published (13 October 2026)

Sourcing only, under T1 addendum 1 (commit 86b2543). No data file was downloaded, no data
endpoint was called, and no T1 feature or outcome was computed. Only public documentation pages
were read (the user's rule of 2026-10-13: up to 20 pages per site, one at a time, with a pause),
after the 13 October nightly had finished. Coverage per input and year cannot be measured without
downloads, so the table below says where each input is published and what is still unproven;
the measured table follows the approved probe.

## Pages read (all public documentation; nothing downloaded from a data endpoint)

| Time (IST) | Page | Result |
|---|---|---|
| 23:41 | https://www.niftyindices.com/reports/historical-data (via the fetch tool) | timed out |
| 23:42 | https://www.nseindia.com/reports-indices-historical-index-data (via the fetch tool) | timed out |
| 23:43 | https://www.nseindia.com/static/products-services/indices-nifty500-index (via the fetch tool) | timed out |
| 23:45 | https://www.niftyindices.com/reports/historical-data | read |
| 23:46 | https://www.niftyindices.com/reports/daily-reports | read |
| 23:46 | https://www.niftyindices.com/resources/industry-classification | read |
| 23:47 | https://www.niftyindices.com/indices/equity/broad-based-indices/India-Vix | 404 page |
| 23:47 | https://www.nseindia.com/static/products-services/indices-indiavix-index | read |
| 23:48 | https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives | read |
| 23:48 | https://www.niftyindices.com/reports/?option1=Archives%20of%20Daily/%20Monthly%20Reports&option2=Daily%20Snapshot | redirect |
| 23:49 | https://www.niftyindices.com/reports?option1=Archives%20of%20Daily/%20Monthly%20Reports&option2=Daily%20Snapshot | read |
| 23:49 | https://www.niftyindices.com/media | read |
| 23:51 | https://www.niftyindices.com/Press_Release/ind_prs21032022_1.pdf | read (press release) |
| 23:51 | https://www.niftyindices.com/resources/index-methodology | read |
| 23:51 | https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf | read (methodology) |

Totals: niftyindices.com 11 of 20 (one timed out), nseindia.com 4 of 20 (two timed out). Two
web searches restricted to these two domains located the pages. Pages were read from this
machine with a browser user agent after the fetch tool timed out.

## What the pages establish

**Index closes (NIFTY 50, NIFTY 500).** NSE Indices publishes two forms:
- Historical Data (niftyindices.com/reports/historical-data): a form returning Date, Open, High,
  Low, Close for a chosen index and period, as CSV, through a POST endpoint
  (`/reports/historical-data/Index/`). This is today's final series: no vintages, no publication
  times.
- Daily Snapshot: one file per trading day, `/Daily_Snapshot/ind_close_all_DDMMYYYY.csv` (the
  page links 12 and 13 October 2026), with an archive whose download link for a chosen date comes
  from the same POST endpoint. The pages do not say how far back the archive goes.
- No page read states when a day's closes are published. The candidate evidence is each daily
  file's HTTP `Last-Modified`, the same evidence the project already uses for bhavcopy knowledge
  dates. Whether archived files keep their original timestamps, rather than the date of a later
  re-upload, is unknown and is the first thing the probe must establish.

**India VIX.** NSE computes it (the niftyindices VIX page is a 404). NSE's product page offers a
computation methodology PDF, a white paper and a "historical value" search, which loads from a
data endpoint. Nothing read states the publication time. Whether India VIX appears in the daily
`ind_close_all` file is unverified.

**Sector membership.** Three facts from the publisher:
- The common India Industry Classification (NSE Indices and BSE; 12 macro-economic sectors, 22
  sectors, 58 industries, 200 basic industries) took effect on 31 March 2022 (joint press
  release, 21 March 2022). Before that a different NSE scheme applied. The development period
  (2019-10 to 2024) therefore spans a change of classification scheme.
- Classification is reviewed annually after annual reports, and on major corporate events. The
  site publishes only the current guidelines and structure (2023-07 versions). No dated,
  per-company classification history was found on either site.
- Sectoral indices are small: 10 to 20 stocks each (methodology document, September 2026
  version). Their dated changes are in press releases: 913 between 2018 and 2025, named by date
  (`/Press_Release/ind_prsDDMMYYYY.pdf`), including the semi-annual Index Maintenance
  Sub-Committee decisions and replacements.

## Inputs: what is known now

Every year from September 2018 to December 2025 currently has the same status for each input,
because nothing has been downloaded. The phase 1 probe below samples two dates per year, so the
next version of this table is measured per year.

| Input | Official source located | Coverage, Sep 2018 to Dec 2025 | Publication evidence |
|---|---|---|---|
| NIFTY 50 close | NSE Indices: Daily Snapshot files and Historical Data | not measured; archive depth not stated | none stated; `Last-Modified` untested |
| NIFTY 500 close | same as NIFTY 50 | not measured | none stated; `Last-Modified` untested |
| India VIX close | NSE historical VIX page (data endpoint); possibly the Daily Snapshot | not measured | none stated |
| Point-in-time sector membership, whole population | no dated per-company source found | not available as found | n/a |
| Sectoral-index membership (option 2 below) | NSE Indices dated press releases, 2018-2025: 913 | releases located; composition not rebuilt | press release dates |

If publication can't be proven for an input, the pre-registration's rule applies: knowledge
begins at first retrieval and earlier history is UNKNOWN. For the index inputs that would block
V1 and the market-relative displays entirely. This is the main risk, not a reason to relax the rule.

## Options for V3's sector membership (the decision is yours, by a further dated addendum)

1. **Drop V3.** Nothing found proves dated sector membership for the whole population over
   2019-2025.
2. **Declared alternative: dated sectoral-index membership.** Rebuild each sectoral index's
   constituents from the dated press releases, starting from a dated full composition. This is
   provable, but it covers only the stocks inside those indices (roughly 10 to 20 each), and a
   sectoral index's peers are not "the publisher's sector". V3 would become a narrower test
   (constituents only), stated before any outcome.
3. **Dated snapshots of the constituent lists that carry an industry column** (for example the
   NIFTY 500 list), from third-party web archives whose capture time proves public availability.
   Coverage would be sparse and irregular, and the provenance is third-party. Evaluating this
   needs its own requests, to the archive rather than to NSE.

No present-day classification is backfilled under any option.

## Proposed request budget (awaiting approval; nothing fetched)

**Phase 1, a probe** (at most 64 requests, one every 10 seconds or slower, outside the nightly's
hours, stopping at the first HTTP 403 or 429):
- Daily Snapshot archive: 2 dates per year for 2018-2025 (16 dates), each 1 POST for the link and
  1 GET for the file: 32 requests. Record HTTP status, `Last-Modified`, size, SHA-256, and whether
  NIFTY 50, NIFTY 500 and India VIX rows are present.
- Historical Data endpoint (today's final series), NIFTY 50 and NIFTY 500, one request per index
  per year: 16 requests. Used only to cross-check the daily files' values and coverage.
- NSE India VIX history endpoint, one request per year: 8 requests (dropped if the daily file
  already carries India VIX).
- NSE's own mirror of the daily file, if it exists, for the same 8 earliest sampled dates:
  8 requests.
- Files go to `data/raw/t1_sources/` with their response headers and hashes; nothing enters the
  repository or the stores, and no feature or outcome is computed.

**Phase 2**, the full daily history (about 1,830 trading days from September 2018), is proposed
separately after you have seen phase 1's results, with its own count and pacing. Option 3 above
needs a separate, small budget only if you want it evaluated.
