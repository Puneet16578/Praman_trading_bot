# Phase 4 — ASM/GSM Sourcing (read-only investigation)

ASM/GSM placements are now a primary evaluation label source (per the SEBI feasibility finding,
`docs/phase3b_sebi_label_feasibility.md`), not a secondary feature. This phase answers where the
data actually lives, before any ingestion is built.

## The 30-second check: server-rendered or API?

**API, definitively.** `/reports/asm` and `/reports/gsm` render only empty container `<div>`s in
the raw HTML (`id="asm-lt-table-container"`, `id="gsm-table-container"`) — no stock data anywhere
in the server response. A dedicated JS bundle per page (`asm.js`, `gsm.js`) populates them after
load. Read directly from the JS source (equivalent information to a browser's network tab, no
browser needed):

- ASM: `GET /api/reportASM` → `{longterm: {data: [...]}, shortterm: {data: [...]}}`
- GSM: `GET /api/reportGSM` → `[...]`

## What the live snapshot API carries

Fetched and inspected both for real. Sample ASM row: `{"asmSurvIndicator": "Stage I", "asmTime":
"11-Sep-2026", "companyName": "A2Z Infra Engineering Limited", "isin": "INE619I01012", "series":
null, "survCode": "LTASM - I (13)", "survDesc": "Long Term Additional Surveillance Measure (LTASM)
- Stage I", "symbol": "A2ZINFRA", "srno": 1}`. Sample GSM row: `{"companyName": "AGS Transact
Technologies Limited", "gsmStage": "LXII", "gsmTime": "11-Sep-2026 08:13:02", "isin":
"INE583L01014", "survCode": "IBC - Receipt & GSM 0 (62)", "survDesc": "Insolvency and Bankruptcy
Code (IBC) - Receipt of Disclosure or Recommenced scrip and GSM stage 0", "symbol": "AGSTRA",
"srno": 1}`.

- **Stage**: present (see caveat on `gsmStage` below).
- **Entry/exit dates**: absent. One `asmTime`/`gsmTime` timestamp shared by the *entire* response
  (a single "as on" snapshot moment), not per-stock.
- **History**: absent from the live endpoint (no date parameters in either JS bundle) and
  effectively absent from the Wayback Machine — checked via CDX: 9 archived snapshots of
  `/api/reportASM`, 6 of `/api/reportGSM`, one from January 2024 and the rest clustered in the
  last two weeks (Aug 27 – Sep 11, 2026). A ~2.5-year gap with a single data point is not usable
  history.

## Where the history actually is: dated circulars

`GET /api/circulars?dept=SURV&fromDate=DD-MM-YYYY&toDate=DD-MM-YYYY` is a real, working, dated
listing. Confirmed at the 2019-10-01 floor: circular `SURV42545`, *"Applicability of Additional
Surveillance Measure (ASM)"*, published **October 31, 2019**.

Downloaded and opened `SURV42545.zip` in full: a PDF cover letter plus `Annexure_LT.xlsx`. The
Excel contains **explicit, separate, headed lists** — new Stage-I entries, Stage-I→Stage-II moves,
exclusions — each headed *"...w.e.f. November 01, 2019."* This is the exact bitemporal shape the
project needs, already present in the source: circular publication date (Oct 31, 2019) =
knowledge_date; the "w.e.f." date (Nov 1, 2019) = event_date. Also present: a "Consolidated - ASM"
sheet with full current membership and a `Stage` column.

Counted real volume across the full range (year-by-year sweep of `dept=SURV`, filtered by
"ASM"/"GSM"/"SURVEILLANCE MEASURE" in the subject line):

| Year | Total SURV circulars | ASM/GSM-subject |
|---|---|---|
| 2019 (Oct-Dec) | 198 | 142 |
| 2020 | 1,070 | 769 |
| 2021 | 1,133 | 839 |
| 2022 | 1,091 | 747 |
| 2023 | 1,251 | 880 |
| 2024 | 1,267 | 998 |
| 2025 | 1,135 | 902 |
| 2026 (through Sep) | 794 | 632 |
| **Total** | | **5,909** |

This subject-line count is a first pass, not yet broken down by circular *type* — see the
follow-up questions below, which found it substantially overcounts the periodic applicability
circulars specifically (many hits are per-stock intimations that merely mention ASM/GSM in
passing).

## Follow-up 1 — is 5,909 the real number of periodic circulars?

No. That count was every SURV circular whose subject merely *mentions* ASM/GSM/"surveillance
measure" — it includes framework-policy updates, promoter-pledge/encumbrance surveillance
(a different, unrelated mechanism), Deep-OTM contract surveillance, and one-off SEBI-order
notices, none of which are the periodic entry/exit/stage circulars this project needs.

Re-fetched and cached all 7,936 SURV circulars 2019-10 to 2026-09 to disk, then classified by
normalized (whitespace/typo-collapsed) subject text:

| Category | Count |
|---|---|
| Periodic ASM/ST-ASM applicability circulars | 3,773 |
| Periodic GSM stage-move/update circulars | 1,127 |
| **Total periodic (the number that matters)** | **~4,900** |
| Policy/framework/unrelated-mechanism circulars (real noise) | 108 |
| Still-unclassified residual | 903 |
| Non-ASM/GSM-mentioning at all | 2,029 |

The 903 residual is itself instructive, not just noise: manually inspecting it turned up (a) more
typo variants of the same periodic subject line my classifier still missed ("Applicabilty",
"Aaddtional", "Surveillanvce", "Sage II" for "Stage II" — real, observed spelling variants across
7 years of manual titling) and (b) genuinely different, adjacent surveillance mechanisms
(**ESM** — Enhanced Surveillance Measure — plus IBC-specific and "Persistent Noise Creator"
circulars) that are NOT ASM/GSM and were correctly excluded. **Best honest estimate: roughly
4,900–5,500 genuinely periodic ASM/GSM circulars**, not a single precise number — subject-line
typo variance is real and a production parser needs fuzzy matching, not exact-string matching,
against known title templates.

## Follow-up 2 — consolidated snapshot + deltas, or every circular?

Opened 5 real circulars in full, spread 2019/2021/2023/2025/2026 (`SURV42545`, `SURV48779`,
`SURV57402`, `SURV68952`, `SURV74211`): **the consolidated sheet is reliably present in all 5** —
viable to use as a periodic full-snapshot anchor. But its exact sheet name is not stable:
`"Consolidated - ASM"` (2019, 2021) vs. `"Consolidated - ST ASM"` (2023) vs. `"Consolidated ASM"`
— no hyphen (2025, 2026). A parser needs prefix/fuzzy sheet-name matching, not an exact name.

**Answer: yes, viable** — periodic consolidated snapshots plus the delta sheets between them is a
much smaller ingestion than every circular, since the consolidated sheet alone gives full
membership + stage at each anchor point, and deltas fill the gaps between anchors.

## Follow-up 3 — is the annexure format stable across 7 years?

Same 5 circulars. Column layout is the one thing that held perfectly: `Sr. No., Symbol, Security
Name, ISIN` (delta sheets) and `Sr. No., Symbol, Security Name, ISIN, Stage` (consolidated
sheets) across all 5, spanning 2019–2026. Everything else varies:
- **Sheet names**: `"Annexure I-A"/"I-B"/"II"` (2019, 2021 — includes IBC carve-out sheets) vs.
  the simpler `"Annexure I"/"II"` (2023, 2025, 2026 — no IBC split observed in the ST-ASM samples).
- **Row layout**: a blank row between the title and header row in 2019/2021/2023, but title
  directly followed by the header row with no blank in 2025/2026.
- **File naming**: `Annexure_LT.xlsx` (2019) vs. bare `Annexure.xlsx` (2021) vs. `Annexure_ST.xlsx`
  (2023/2025/2026).

**Conclusion: one parser per era, or one sufficiently fuzzy parser** (match sheets by prefix/
keyword, locate the header row by content rather than fixed offset, don't assume a fixed
filename) — not a single rigid template. This is a bigger real cost driver than the document
count.

**GSM specifically is a separate, harder problem discovered along the way**: ASM circulars are
ZIP+Excel throughout. GSM stage-move circulars are **plain PDFs**, and checked across
2019/2022/all of 2023 (Jan/Jul/Dec) they are **scanned images** (5 real characters, 60–85
embedded images per page, `extract_text()` returns nothing) — genuine OCR would be needed for
those years. Checked Dec 2024 and Sep 2026: **real, selectable text**, clean and directly
extractable. The transition happened somewhere in 2024 (bracketed between Dec-2023
image-only and Dec-2024 real-text; not narrowed further this session). GSM history before that
transition needs an OCR step ASM never will.

## Also confirmed — the GSM stage field is unreliable, exactly as suspected

Pulled 15 real live-API rows and compared `gsmStage` against the stage stated in `survDesc`
text. For **simple, non-overlapping GSM rows**, `gsmStage` happens to match
(`gsmStage='VI'` ↔ `survDesc='...Stage VI'`; `gsmStage='III'` ↔ `'...Stage III'`). But for
**composite rows** — a scrip simultaneously under GSM and IBC or ASM, which is common in the
sample — `gsmStage` diverges completely: `gsmStage='LXII'` while `survDesc` says *"GSM stage
0"* — because `gsmStage` is actually the Roman-numeral rendering of the parenthetical composite
surveillance-code number in `survCode` (`"IBC - Receipt & GSM 0 (62)"` → 62 → "LXII"), not a GSM
stage at all. It only coincidentally equals the true stage when the composite code number and
the GSM stage number happen to be the same integer, which is only true in the pure/simple case.
**Confirmed: `gsmStage` must never be stored as the stage. The real stage has to be parsed out of
`survDesc` text** (e.g. matching "GSM stage N" / "GSM - Stage N" / "Graded Surveillance Measure -
Stage N"). Storing `gsmStage` directly would have stored garbage for every composite-code row.

## Scope decision — GSM ingestion is 2025-01-01 onward only, not an oversight

GSM circulars before some point in 2024 are scanned images (checked directly across
2019/2022/Jan-Jul-Dec 2023: zero extractable text, 60-85 embedded images per page). GSM ingestion
is scoped to circulars published **2025-01-01 onward**, with no OCR step for the earlier period.
Reasoning (recorded verbatim per instruction, since this is a real scope tradeoff, not a
convenience):

1. **A silent OCR misread on a ticker symbol is a worse failure than a documented gap.** A wrong
   symbol produced by OCR is indistinguishable downstream from a right one — it would silently
   attach a real surveillance event to the wrong company. A missing date range is visible and
   honest: anyone querying pre-2025 GSM history gets nothing, not something wrong.
2. **GSM skews toward illiquidity/IBC-linked scrips — a different phenomenon from what this
   project measures.** This project's evaluation target is unusual price-move signatures with an
   informational-basis-vs-manipulation-consistent distinction; GSM's population is dominated by
   thinly-traded, insolvency-adjacent companies, a related but distinct concern from ASM's
   volume/price-based criteria. ASM is the richer signal for this project's actual question; GSM is
   a secondary one.
3. **The gap is a stated, scoped limitation, not a hidden one.** OCR over the 2019-2024 scanned
   PDF corpus remains a possible, explicitly named future follow-on if GSM history before 2025
   becomes load-bearing later — it is not being ruled out permanently, just not built now.

## Four excluded surveillance mechanisms

Real periodic ASM circulars routinely carry sections for related-but-distinct surveillance
mechanisms alongside their genuine ASM Stage I-IV sections — either as sections embedded inside an
otherwise-normal ASM circular's own Annexure, or as an entire circular devoted to the other
mechanism. All four are recognized by this build's parser (they match `TITLE_START_RE`, so they're
never silently skipped as a formatting failure) and all four are deliberately excluded from
ingestion — recorded here together, in one place, so a reader who notices any one of them doesn't
mistake it for an oversight or need to reconstruct the reasoning from four separate commit
messages. Section counts below are from the real, full 2019-10-01 to 2026-09 corpus (3,332
periodic ASM circulars):

| Mechanism | Real section title (as observed) | Sections found | Why excluded |
|---|---|---|---|
| **IBC** (Insolvency and Bankruptcy Code) | *"...ASM for Companies relating to the Insolvency Resolution Process (IRP) as per Insolvency and Bankruptcy Code (IBC)..."* | 1,224 | A different placement trigger (insolvency proceedings) from the numbered Stage I-IV surveillance criteria; present since 2019 as its own `Annexure I-B`/`Consolidated-ASM(IBC)` sheets in the older circular format, and as embedded sections in the newer one. |
| **ICA** (Inter Creditor Agreement) | *"...ASM for Companies as per Inter Creditor Agreement (ICA)..."* | 84 | A debt-restructuring-triggered placement, the same structural category as IBC (not the ordinary volume/price Stage I-IV criteria) — discovered this session via the unparsed-titles-by-shape check, not previously documented. |
| **ESM** (Enhanced Surveillance Measure) | *"...Enhanced Surveillance Measure (ESM)..."*, or as an ASM `EXIT`'s footnote (e.g. `"Due to Shortlisted in ESM"`, `"Moved from STASM to ESM framework"`) | 2 standalone sections + present as the reason text in many real ASM `EXIT` events | An entirely separate NSE surveillance program from both ASM and GSM. When a symbol exits ASM specifically *because* it moved to ESM, that EXIT is a real, in-scope ASM event and is ingested normally — the footnote text explaining why is preserved verbatim in `details`, but no corresponding ESM entry event is created; ESM's own circulars/placements are not tracked. |
| **Encumbrance** (SEBI SAST Reg. 28(3)) | *"...companies with high 'Encumbrance' as per Reg. 28(3) of SEBI (SAST) Regulation 2011..."* | 2 | A promoter-shareholding-pledge-triggered surveillance category, unrelated to ASM's volume/price criteria — the same class of exclusion as IBC/ICA, just far rarer in the real corpus. |

None of the four is silently dropped: every section title that reaches `_classify_title` and
doesn't match one of the three real ASM section-type patterns (entry / stage-transition /
exclusion) is returned in `unparsed_titles`, which the ingestion report counts and groups by
normalized shape. A title appearing anywhere in that report that ISN'T one of these four
categories is the signal to stop and investigate before treating it as known-noise (this is
exactly how P4-012 was found — see the defect register).

## Reconciliation check — the ten-minute check that decided the ingestion shape

Before choosing between "ingest every daily delta circular" and "ingest periodic consolidated
snapshots + diff them," the two approaches were checked against each other directly, on two real,
genuinely consecutive ASM circulars: `SURV66001` (published **2025-01-06**, "T1") and `SURV66016`
(published **2025-01-07**, effective **"w.e.f. January 08, 2025"**, "T2") — the next periodic
ASM-applicability circular issued after T1, with no gap between them.

**Method.** `consolidated(T2)` (93 symbol/stage rows) diffed directly against `consolidated(T1)`
(91 rows) gives the ground-truth set of what actually changed: `added = {EPACK, ITI}`,
`removed = {}`, `stage_changed = {SAGILITY: I→IV, GVT&D: III→IV}`. Independently, T2's own
`Annexure I`/`Annexure II` delta sections were parsed (section-aware, not a flat-table read — see
below) and compared against that ground truth.

**First pass looked like a disagreement, and wasn't.** A naive flat-table read of `Annexure I`
produced a set that didn't match the consolidated diff (extra symbols, a stray "Symbol" header
artifact). Re-inspecting the raw sheet row-by-row (not assuming the mismatch meant the source was
unreliable) showed `Annexure I` is not one table: it is **ten separate titled sub-sections** — new
Stage-I entries, new Stage-IV entries, and each of the nine pairwise stage-transition types
(I→II, II→III, I→IV, II→IV, III→IV, IV→III, III→II, II→I) — each with its own header row and a
literal `Nil` placeholder row when empty. This is exactly the same lesson this project already
learned once before (a "disagreement" between two real sources should be checked for a parsing bug
before it's trusted as a real data problem): the mismatch was the parser being wrong, not the data.

**Result, with a correct section-aware parser: perfect reconciliation.**

| | Consolidated-sheet diff (ground truth) | Section-aware `Annexure I`/`II` parse |
|---|---|---|
| Added | `{EPACK, ITI}` | `{EPACK, ITI}` — both under the plain Stage-I new-entrants section, `ITI` footnoted *"Moved from STASM to LTASM framework"* |
| Removed | `{}` | `{}` — `Annexure II` correctly shows `Nil` |
| Stage-changed | `{SAGILITY: I→IV, GVT&D: III→IV}` | `{SAGILITY: I→IV, GVT&D: III→IV}` — each under its own correctly-matching transition-type section |

**Decision this determined: ingest from the daily delta circulars (Annexure I/II), not from
diffing periodic consolidated snapshots.** Both sources are trustworthy once parsed correctly, so
the choice came down to which is structurally safer at scale, not which is more accurate:
periodic ASM-applicability circulars are issued at high frequency — the real full-range count
found this session is **3,334 periodic circulars across 2019-10-01 through 2026-09-11**, close to
one per trading day, not the monthly cadence an earlier single-year sample suggested. Diffing only
sparse periodic consolidated snapshots would silently lose any transient intermediate stage
transition that occurred and reversed *between* two chosen snapshot dates (e.g. a symbol moved
Stage I→II and back to Stage I within a gap the snapshot schedule doesn't sample) — a real event
this project's bitemporal model exists to capture, not average over. Each daily circular's delta
sections are self-contained and authoritative for that one day regardless of any gap in prior
ingestion coverage; a snapshot-diff approach's correctness depends on never missing a snapshot.
Consolidated sheets are still useful as an independent audit/reconciliation tool (as demonstrated
here) but are not ingested as facts — see `src/ingestion/nse_market_data/asm.py`'s module
docstring for why ingesting both would double-record the same fact two different ways.

## Ingestion build

Built `src/ingestion/nse_market_data/asm.py` and `src/ingestion/nse_market_data/gsm.py`, writing to
the `surveillance_flags` fact table (extended, not forked, from its Phase-1 placeholder shape —
see `src/bitemporal/schema.py`) with columns `mechanism` (`ASM_LT`/`ASM_ST`/`GSM`), `action_type`
(`ENTRY`/`EXIT`/`STAGE_CHANGE`), `from_stage`/`to_stage` (nullable), `source_circular`, and a
nullable `details` (footnote text, e.g. *"Moved from STASM to LTASM framework"*,
*"Due to Inclusion in ESM"*, *"Suspended"*).

- `knowledge_date` = the circular's own publication date (`cirDate` from `/api/circulars`).
- `event_date` = the "w.e.f. DATE" parsed from each Annexure section title (ASM) or the "with
  effect from"/"w.e.f." phrase in the circular body (GSM) — a genuinely different date from
  knowledge_date, never collapsed into it.
- Stage is always parsed from the dated document's own text (section title for ASM, subject line
  for GSM), never from the live API's fields.
- ASM subject-line discovery (`is_periodic_asm_subject`) is typo-tolerant by design: it checks
  only the letter-stems that survive every real typo found in 7 years of circular titling
  ("Applicabilty", "Aaddtional", "Surveillanvce") rather than the words most often misspelled, and
  explicitly excludes GSM/ESM/IBC/promoter-pledge circulars that also mention "surveillance."
- GSM subject-line classification tolerates the real "Sage" typo for "Stage" and distinguishes
  stage-move ("...moving to Stage N...") from move-out ("...moving out of GSM...") subjects;
  non-transition GSM-department subjects (periodic relaxation notices, framework-update
  announcements) are recognized and correctly excluded, not counted as parse failures.
- Twelve defects (P4-001 through P4-012 — see `docs/DEFECT_REGISTER.md`) were found and fixed
  against real data, most of them only surfaced by running the actual full-range ingestion and
  then actively checking its output rather than trusting a green exit code: a 2023-era
  exclusion-title wording variant; two real PDF line-wrap positions inside the GSM event-date
  phrase; a stale real-DB table schema and a report-accounting bug that together let a run report
  "2,883 circulars processed" against an actual store row count of zero; an abbreviated-month date
  format used for roughly a year of real circulars; an ESM-subject typo that nearly mislabeled an
  excluded mechanism as in-scope, plus a nested-zip-path bug found investigating it; a GSM PDF
  rendering artifact that split digits across whitespace; a cross-circular duplicate-event
  accounting gap; and — the most serious pair — a footnote-row detector that only checked column 0
  (missing footnotes that land in the Symbol column instead) and a symbol-marker character that
  was never stripped before being used as the business-key symbol, silently splitting one real
  company's history across two different stored identities. See "Data integrity — wrong, not just
  incomplete" below for what that last pair actually cost.
- A thirteenth defect (P4-013) was not a single bug but a design flaw: after P4-012 fixed one
  subject-classification miss (a dropped word), tracing a second, independent incoherence case
  found a real circular dropping a *different* required word. Two independent misses of the same
  shape is what an allowlist cannot bound — it was inverted to a denylist (attempt every SURV
  circular unless it matches one of ~25 explicit excluded-mechanism/administrative categories
  built from a full survey of all 1,756 distinct real subjects in the cached corpus), dry-run
  verified against the full cached index before any network use.
- 156 tests pass (`tests/test_asm_gsm_ingestion.py`, network-free, fixture-based — reproducing
  every one of the thirteen defects' real-data shapes directly, so none of them can regress
  silently).

## Confirmed real source anomalies: knowledge_date > event_date (4 rows, found during Phase 5 pre-flight)

Building Phase 5's surveillance-state helper, a direct query found 4 real `surveillance_flags`
rows (out of 31,646) where `knowledge_date > event_date` — the circular publication date is AFTER
its own stated effective date. Investigated each directly against the real circular PDF text
before assuming a parser bug; both are genuine, verified NSE authoring inconsistencies, not
extraction errors — the parser reproduced exactly what each document prints:

- **`SURV72908`/BLUECHIP** (GSM): the PDF's own header prints `"Date: February 24, 2026"`, its own
  body prints `"with effect from February 23, 2026"` — the circular is dated one day AFTER the
  effective date it itself states. Also notable: the cached circular index's `cirDate` field for
  this same circular reads `2026-02-20` — neither the index metadata nor the "with effect from"
  date agrees with the PDF's own printed publication date. `knowledge_date` here is taken from the
  PDF's own "Date:" line (not the index), the more defensible per-document source of truth, but
  three different fields disagreeing on one circular is a real characteristic of this source, not
  a defect to "fix" by picking whichever one is convenient.
- **`SURV72720`/GAYAPROJ, GFSTEELS, UNIVAFOODS** (GSM): the PDF is dated `February 10, 2026` but
  states `"with effect from February 11, 2025"` — a full year off, almost certainly NSE's own
  typo for 2026 (every other real GSM circular's effective date is 0-2 days after its own
  publication date, never a year), but this project does not silently "correct" a source date to
  what it's probably supposed to say. Recorded as-is, verbatim from the real document, per the
  never-fabricate rule.

**Why this doesn't corrupt anything downstream.** `surveillance_flags`, unlike `corporate_actions`,
has no established knowledge_date<=event_date guarantee to lean on — confirmed by this exact
finding, not assumed clean. `current_surveillance_state()` (Phase 5) is deliberately written to
never rely on one: it gates on bitemporal visibility (`knowledge_date<=as_of`, via `read_as_of`)
*and* separately requires `event_date<=as_of` before treating a transition as having taken effect.
For these 4 rows, that means: invisible entirely until their own `knowledge_date`, and effective
immediately the moment they become visible (since `event_date < knowledge_date <= as_of` the
instant visibility starts) — a real oddity in the data, but never a look-ahead risk or a row that
silently flips to "not yet effective" after having already been shown as effective.

## Data integrity — wrong, not just incomplete

Two structurally different kinds of defect were found in this build, and they have different
consequences for anyone reading a row count from before this rebuild:

**P4-010/P4-011 (footnote-as-symbol, unstripped marker) were CORRECTNESS failures, not coverage
gaps.** A row for a real event was not dropped — it was stored under a fabricated or wrong symbol
identity. `"MARATHON *"` (the marker never stripped) was stored as a symbol *distinct* from
`"MARATHON"` — the same real company, split into two unrelated identities depending on which
circular happened to carry the marker. Three rows were stored under symbols that were not
securities at all (literal footnote text, e.g. `"* Moved from STASM to LTASM framework"`). A row
count over data like this can look completely fine — nothing was missing, the count was even
technically "more complete" than the corrected version in a naive sense — while being wrong in a
way no row count, date-coverage check, or completeness metric could ever reveal. Finding it
required checking the data's own internal logic (does this symbol's event sequence tell a
coherent story?), not just checking that ingestion ran without error. **Any row count, date range,
or event breakdown reported from before this session's final rebuild is retracted, not merely
superseded** — it was generated from a store containing fabricated and misattributed rows.

**P4-012 (the dropped-"Surveillance" subject variant) is, by contrast, a genuine coverage gap.**
Four real circulars were never attempted at all — correctly classified as out of scope by the
letter of the (now-fixed) rule, incorrectly so in fact. Their events are simply absent from the
store, not present under a wrong identity. This is the ordinary, expected kind of gap this
project's failure reporting already exists to surface (a circular in `circulars_failed`, or in
this case, one that should have been there but wasn't attempted at all) — visibly missing, not
silently wrong.

The distinction matters beyond bookkeeping: a coverage gap fails loudly the moment someone asks
"did we get everything" and checks the failure list or the date coverage. A correctness failure
like P4-010/P4-011 fails silently — the row is *there*, the count looks *fine*, and only a
structural check of the data's own internal consistency (the lifecycle-coherence check that
actually found it) catches it. That asymmetry is why the coherence check was worth building and
running before trusting any of this table's numbers, and why it should be re-run after any future
change to the ASM/GSM parsers, not treated as a one-time verification.

## Final ingestion results (post P4-013 rebuild, fully retried)

Real full-range ingestion: ASM 2019-10-01 through 2026-09, GSM 2025-01-01 through 2026-09 only
(per the scope decision above). Five ground-up rebuilds were required as each lifecycle-coherence
pass found a real defect (P4-004 through P4-013) — every number below is from the fifth and final
one, after all thirteen defects were fixed and both real-data test-suite regressions and a
dry-run comparison confirmed clean.

**Rows ingested, by mechanism × action_type:**

| Mechanism | ENTRY | EXIT | STAGE_CHANGE |
|---|---|---|---|
| ASM_LT | 4,785 | 4,735 | 2,882 |
| ASM_ST | 9,257 | 9,185 | 601 |
| GSM | 149 | 52 | — |
| **Total** | | | **31,646 rows** |

**Invariant check** (`sum(parsed event counts) - known duplicate-skips == COUNT(*) in the store`):
31,648 parsed − 2 confirmed duplicate-skips (the same same-day corrective-reissue-circular pattern
as the ICDSLTD case, P4-009) = 31,646. **Holds exactly.**

**Date coverage:** `event_date` spans 2019-10-03 to 2026-09-15. 1,718 distinct `knowledge_date`s
(circulars that contributed at least one row) across the range. **Zero gaps greater than 14 days**
between consecutive circular knowledge_dates — the delta stream has no multi-week hole anywhere in
seven years.

**Circular failures — fully enumerated, all explained, none patchable further:**

| Circular | Mechanism | Reason | Nature |
|---|---|---|---|
| SURV42671 | ASM | Zip contains only a PDF, no Annexure*.xlsx | Genuine source anomaly — this one circular has no machine-readable annexure at all |
| SURV67457 | ASM | `fileExt=None`, download link literally `null67457.null` | Genuine NSE circular-index corruption for this one entry |
| SURV70095, SURV69960, SURV69831, SURV67962, SURV67163 | GSM | Scanned-image PDF, zero/near-zero extractable text | Exactly the pre-2025 GSM pattern, confirmed occurring on 5 individual 2025 circulars too — consistent with, not a violation of, the GSM scope decision (no OCR) |

**Unparsed ASM section titles, grouped by normalized shape:** 1,219 distinct raw titles collapse
to **4 normalized shapes, all IBC** (the Insolvency and Bankruptcy Code carve-out — see "Four
excluded surveillance mechanisms" above). After the P4-013 denylist rebuild, ICA/ESM/Encumbrance
sections no longer appear here at all, because the circulars that used to leak them in (wrongly
accepted by the old allowlist, or embedded inside a circular that is now correctly excluded at
the subject level) are gone. **Nothing outside the four documented, deliberate exclusions
appears anywhere in this report.**

**Bitemporal guard, re-verified on real rows:** a real row (`BHAGERIA`, ASM_ST, `event_date`
2020-01-01, `knowledge_date` 2019-12-31, from `SURV43064`) is invisible at `as_of` one day before
its own knowledge_date and visible on/after it — the same pattern already proven for
`corporate_actions`, now confirmed for `surveillance_flags` against real ingested data, not a
fixture.

### Lifecycle-coherence: what the residual actually is

The categorized coherence check was re-run after every one of the thirteen defect fixes. Final
numbers, out of 4,271 real (symbol, mechanism) tracks and 31,445 ASM events:

| Category | Count | Status |
|---|---|---|
| `malformed_symbol` | 0 | Must be zero — is |
| `exit_no_entry`, near the 2019-10-01 floor (≤45 days) | 85 | Expected — left-censoring |
| `stage_change_no_entry`, near the floor | 16 | Expected — left-censoring |
| `exit_no_entry`, NOT near the floor | 56 | Residual — see below |
| `stage_change_no_entry`, NOT near the floor | 17 | Residual — see below |
| `double_entry` | 36 | Residual — see below |
| `stage_mismatch` | 12 | Residual — see below |

Two individual residual cases were traced end-to-end (fetch the real circulars, read the raw
Annexure/Consolidated sheets directly, find the exact date and circular responsible):

1. **`ALOKTEXT`** traces to `SURV42671` — the one ASM circular with no Annexure at all. Fully
   explained by a known, permanent, non-patchable source gap already in the failures table above.
2. **`ARENTERP`** does **not** trace to a missed circular. Every ST-ASM circular in the relevant
   window (2021-08-25 through 2021-09-13) was individually fetched and checked; `ARENTERP`'s stage
   changes from I to II somewhere between `SURV49455` (Aug 31, consolidated stage I) and
   `SURV49479` (Sep 2, consolidated stage II) — but `SURV49479`'s **own** `Annexure I` "Stage I to
   Stage II" delta section reads `Nil` for that date. The circular was fetched successfully and
   parsed correctly; its own two sheets (`Annexure I` and `Consolidated - ST ASM`) simply disagree
   with each other. This is a genuine inconsistency in NSE's own source document, not a defect in
   this project's code — a third, structurally different residual category from both P4-012 and
   P4-013 (a source-internal contradiction, not a missed or misclassified circular), and not one
   this project's ingestion can resolve by construction: there is no way to derive the correct
   transition date when the source's own delta and snapshot views disagree.

**Conclusion: the residual is bounded and explained, not further chaseable through this project's
code.** It decomposes into three known, distinct causes — left-censoring at the 2019-10-01 floor
(structural), one circular with no machine-readable annexure (`SURV42671`, a single permanent
source gap), and an apparent small population of real NSE circulars whose own consolidated and
delta sheets disagree with each other (a source data-quality property, not a parsing gap — ARENTERP
is a confirmed instance, and the residual counts above are consistent with more such cases existing
unenumerated, since finding each one requires the same full manual trace). No further subject-
classification defect is indicated: the denylist redesign (P4-013) already collapsed the
misclassification-driven categories sharply (`double_entry` 93→36, `stage_change_no_entry`
not-near-floor 20→17, `exit_no_entry` not-near-floor 88→56 across the two post-inversion rebuilds),
and the remaining residual traces to causes outside this project's control, not a fourth missed
circular pattern.
