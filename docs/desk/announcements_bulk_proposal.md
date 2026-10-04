# Corporate-announcement bulk fetch: bounded investigation

2026-10-04. Exactly five user-approved HTTP requests, no retries or redirects,
for 2026-09-07 through 2026-09-13 only. No production ingestion or source change.
The existing per-symbol implementation was inspected before the probe.

Omitting `symbol` from NSE's existing `/api/corporate-announcements` endpoint,
keeping `index=equities`, `from_date=07-09-2026`, `to_date=13-09-2026`, returned
HTTP 200 and 3,132 rows for 1,357 symbols in 1.881 seconds. Including the cookie
request and three per-symbol calls, all requests returned 200. Timing/request
trace and raw-response hashes: announcements_bulk_probe.json. This establishes
bulk capability for THIS week, not a general pagination/completeness guarantee.

Live per-symbol parity, after the existing production row builder, compares
symbol, sequence ID, event/knowledge dates, category, description and publication
timestamp: RELIANCE 4/4, TCS 3/3, KOTAKBANK 4/4, all equal. The captured fixture
and tests/test_announcements_bulk_parity.py reproduce this offline and detect
both an omitted row and changed description. Three large-cap symbols are a sample;
this is not live all-symbol equivalence.

A read-only comparison with the existing per-symbol backfill for the same week
found 3,093 stored rows: 3,088 exact matches, 44 additional bulk keys and FIVE
stored keys missing from bulk (two HEG, three SANGINITA). No shared key changed
its persisted field values. Exact missing keys are in the JSON report. Backfill
and probe retrieval vintages differ; removals, upstream corrections, coverage or
endpoint differences cannot be distinguished with the approved request budget.
Neither response is assumed complete solely because it returned HTTP 200.

## Proposal, not an implemented switch

Propose bulk-first dated windows with the existing row builder, append-only
writes, exact identities, request counts and source-freshness semantics retained.
Do NOT approve blanket replacement yet: first reconcile the five missing stored
keys and prove date-window completeness/truncation behavior under a separately
approved probe. A fallback must fetch unresolved symbols and mark the refresh
PARTIAL if coverage cannot be established; HTTP success alone must not advance
the freshness watermark. Do not delete stored rows absent from a later response.

If approved after parity is resolved, one week could use one API request plus
session initialization instead of roughly 2,280 per-symbol calls. This is the
observed request-count opportunity, not a verified speedup for every nightly or
the first multi-week refresh. No production endpoint, cadence or refresh code was
changed. Further requests require user approval; the five-request budget is spent.

Reproduction: offline unit tests use the committed one-week sample fixture.
Running scripts/probe_announcements_bulk.py is NETWORK ACCESS and requires fresh
approval; it must not be run automatically by the test suite. Full captured
responses remain under data/processed/announcements_bulk_probe_20260907_13.

## 2026-10-05 reconciliation and revised proposal

The original week, **September 7-13, 2026**, was already before September 18.
The later announcement outage does not explain this week's discrepancies.
This addendum supersedes the unresolved-parity conclusion above while retaining
the original investigation record. No production fetcher or durable store changed.

Eight of ten newly approved requests were used: one cookie, one whole-week bulk,
two disjoint bulk windows (September 7-10 and 11-13), and four per-symbol calls
(HEG, SANGINITA, HMT, MELSTAR). All returned HTTP 200; no retries or redirects.
Two requests remain unused. Capture trace, response hashes and **all 49 individual
discrepancy classifications** are in [the reconciliation ledger](announcements_bulk_reconciliation.json).
Full responses remain in data/processed/announcements_bulk_reconcile_20261005.

### Every discrepancy, in both directions

| Direction / cause | Rows | Evidence |
|---|---:|---|
| Missing from bulk by the original symbol key: HEG -> HEGAM | 2 | IDs 106775414 and 106778188; matching ISIN INE545A01024, publication timestamp, date, category and description |
| Missing from bulk by the original symbol key: SANGINITA -> AGASTYAEN | 3 | IDs 106774556, 106776815 and 106779875; matching ISIN INE753W01010 and all non-symbol persisted fields |
| Missing from store by the bulk symbol key: AGASTYAEN -> stored SANGINITA | 3 | The same three announcements above, not three new disclosures |
| Missing from store: backfill universe exclusion | 41 | Twenty symbols with zero EQ price rows and zero announcement rows in the store; the backfill selects only symbols with an EQ price row. No matching sequence IDs under another stored symbol or date |
| Pagination / date boundary / timezone / revision / withdrawal | 0 attributed | No unresolved mismatch requires any of these explanations; checks and limits below |

The 41 excluded rows break down as follows. The ledger records each ID, date,
text, and that symbol's price-series counts and date coverage, with knowledge
cutoff 2026-10-05. This is an additional observed cause, not a forced attribution
to one of the four candidate causes in the request.

| Symbols | Rows per symbol | Stored price series |
|---|---|---|
| MELSTAR | 9 | BE, BZ |
| HMT | 6 | BZ |
| NEUEON / XLENERGY | 3 / 3 | BE / BE and BZ |
| VHLTD / KALYANI / GAMMONIND / LEEL | 2 / 2 / 2 / 2 | BE / BE / none / BZ |
| SWANDEF / CLCIND / DSKULKARNI / ATNINTER | 1 each | BE |
| BLUEBLENDS / AIFL / CANDC / NITINFIRE / BGLOBAL | 1 each | BE and BZ / BZ / BZ / BZ / BE and BZ |
| ASIL / RUSHABEAR / ABHISHEK | 1 each | none |

There were already two HEGAM counterparts in the store, recorded September 23,
alongside the two HEG rows recorded September 18. Thus five missing old-symbol
keys correspond to only three new-symbol extras. Stored row count 3,093 represents
3,091 distinct announcement IDs for this week; the bulk's 3,132 IDs add exactly
41 disclosures outside the backfill universe. No historical rows were removed.

### Checks against alternative causes

- **Pagination/truncation:** the whole-week response has 3,132 rows. The split
  responses have 2,492 + 640 rows; their union is identical on every persisted
  field to the whole week. HMT 6/6 and MELSTAR 9/9 also match per-symbol fetches.
  Together with the earlier 11-row sample, 26 sampled rows match. This verifies
  this week; it does not establish an unlimited response-size guarantee.
- **Date boundary/timezone:** all rows fall inside September 7-13; both date
  endpoints are present. All 3,132 `an_dt` values parse to the same wall-clock
  timestamp as `sort_date`. Split boundaries lose no row; all five rename pairs
  retain identical timestamps. No timezone correction is needed to reconcile
  these records. An absolute timezone contract beyond this check is not inferred.
- **Renames:** exact sequence ID, identical non-symbol contents and matching ISIN
  explain all five stored-key absences. Current bulk company names and attachment
  filenames also retain the old/new-name connection. Both old-symbol live queries
  now return empty lists. Current identity evidence explains retrieval behavior;
  it must not be backdated as a historical membership or rename-effective date.
- **Revisions/withdrawals:** no shared key has changed persisted fields, and the
  October 4 and October 5 bulk captures have identical persisted contents. Every
  stored record is present exactly or under an explained alias. There is no need
  to hypothesize a withdrawal or revision, and none is established by this probe.

**Acceptance result: PASS for this week.** All 3,093 stored rows are represented:
3,088 exact symbol-key matches and five explained renames. All 44 bulk-only keys
are explained: three aliases and 41 universe exclusions. No unresolved discrepancy.

### Proposed switch, awaiting approval

Propose replacing the per-symbol nightly loop with bulk requests in dated windows
of at most one week, retaining the production row builder, append-only writes,
request accounting and source-freshness semantics. The one-week probe supports
one API request plus cookie initialization instead of roughly 2,280 API requests.
Keeping the demonstrated split-window check would use three API requests per
weekly window plus session initialization. This is the proposed initial guarded
request load; runtime and completeness for other windows remain to be verified.

Implementation must explicitly handle symbol aliases using dated identity evidence,
preserve original exchange symbols/IDs and historical records, and refuse to mark
an unresolved identity or coverage gap complete. An empty response for an obsolete
symbol cannot establish freshness (new defect P8-046). Reuse the existing equity
scope through dated identity resolution; admitting the 41 additional disclosures
or broadening the universe is a separate scope choice. Do not silently adopt a
current symbol as the identity at an older decision date or merge by sequence ID
alone. A per-symbol fallback cannot repair the old-symbol-empty case by itself.

Before rollout, replay the committed rename/content-mutation and per-symbol parity
fixtures and require the split-window completeness check on the refresh window;
mark unresolved coverage PARTIAL. A one-week sample is insufficient evidence to
discard coverage guards. This is a proposal only: no switch has been implemented.

Reproduce the analysis offline with `python scripts/reconcile_announcements_bulk.py`
against the saved responses and read-only store (the ledger includes comparison
and identity-map hashes). The capture script requires `--fetch`, refuses to overwrite
an existing capture directory, and is never called by tests. Any new capture uses
the remaining request budget only with an explicitly bounded request plan.
