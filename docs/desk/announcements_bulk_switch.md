# Bulk announcement switch — 2026-10-05

User-approved replacement of the nightly ticker loop. No frozen classifier,
catalogue, label, pre-registration or research result is rebuilt.

## Identity and append-only migration

The business key is NSE `seq_id`, independent of ticker. When absent, a SHA-256
of publication timestamp, category, text and attachment URL supplies the key;
current ticker/name/ISIN are excluded from that hash. Repeated identical content
never appends a new announcement. A genuine revised content vintage retains the
ID and uses its later observation date as knowledge_date.

The existing table receives nullable identity/provenance columns. Dated bhavcopy
identity observations enter the registered append-only `security_identities`
fact table, included in Desk recorded-at replay views and store watermarks;
readers do not consult an unbounded current cache. Existing rows
are not rewritten or deleted. A nonunique ID index and an insert trigger enforce
global ID/vintage uniqueness on old stores despite their pre-existing alias
duplicates; new stores also have a global UNIQUE constraint. Reads deduplicate
legacy IDs. Counts distinguish physical rows from unique announcement IDs.

Publication-date symbol/ISIN resolution uses dated NSE CM bhavcopy snapshots,
never the merged current-symbol map. A snapshot dated after publication cannot
participate. On non-trading days use the latest preceding available snapshot.
The archive's own TradDt must match the requested date. Raw exchange ticker and
JSON are retained. Missing/ambiguous dated identity remains UNKNOWN, stored in
full and visible as a coverage limitation rather than guessed or discarded.

All returned types/series enter storage, including funds and securities excluded
by the old EQ-only backfill. Equity-only filtering happens in the disclosure read
path using dated identity. Legacy rows with no new metadata retain their historical
symbol interpretation. An unresolved new identity in the requested window yields
UNKNOWN coverage. This change does not relax the Desk's independent series gates.

## Fetching and freshness

`PRAMAN_ANNOUNCEMENTS_MODE=bulk` is the default. `per_symbol` explicitly enables
the retained old path; neither the fetch function nor the backfill is deleted.
The nightly's old backfill step reports that it is disabled in bulk mode.

Windows are at most seven calendar days, with a seven-day overlap on later runs.
Each window is fetched whole and as two disjoint smaller windows; all semantic
rows must match. HTTP errors, bad payloads, wrong dates, split mismatch or failed
ingestion produce WARN. PARTIAL never advances the market-wide watermark, even
if other windows succeeded. An interrupted/repeated run can safely re-ingest its
successful windows. Raw responses and request-attempt traces are retained.

The coverage origin is September 10. No refresh may skip a gap from the prior
complete date. Only a successful full run replaces the operational state pointer;
freshness receipts remain append-only in the Desk store. Per-symbol fallback
receipts cannot establish market-wide coverage. Historical complete receipts
remain visible for replay. A market-wide receipt can establish a true NONE tier
for a security with no previous announcements, only when it covers the whole
pre-event window. Otherwise absence remains UNKNOWN.

The current calendar day is fetched again on every invocation, including the
evening nightly after this morning's backfill. A successful intraday response
covers publications available at its retrieval time, not future disclosures.

## Approved run and historical audit

The foreground runner uses a hard limit of 30 backfill attempts and a separate
20-attempt audit budget, with no automatic retries or redirects. The planned
backfill is 12 announcement calls, 15 dated identity files and one cookie = 28.
The audit reuses that session; it does not write to the source store.

The audit's population/sample/estimator are fixed before fetches in
announcement_rename_audit_plan.json. It reconstructs the original **195** groups
from the historical rename log, rather than silently using the current 205.
127 groups have eligible catalogue events (4,402 total). Sample 20 securities
uniformly, then one eligible event per sampled security, seed 20261005. Each
request covers that event's exact ten-session pre-event window. The primary
event-count-weighted ratio estimate and raw Horvitz-Thompson estimate are reports,
not corrections to frozen classifications. Additional fully covered events are
descriptive observations, not extra independent samples. No precise population
confidence interval is claimed from one sampled event per security.

NSE can revise/remove historical records; current bulk contents are an audit
comparison, not proof of the exact response Phase 7 received. Audit windows do
not have spare requests for the backfill's split check; report this completeness
limit and suppress the estimate on any failed sampled request. No forward-window
outcome column is loaded, and no frozen artifact is changed.

September is compared with the stated 16,000-21,000 full-month range. October is
partial through October 5 and must be labelled accordingly. P8-021 can close only
if both of the user's count conditions and a current watermark actually hold.
