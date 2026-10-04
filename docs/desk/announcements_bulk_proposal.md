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
