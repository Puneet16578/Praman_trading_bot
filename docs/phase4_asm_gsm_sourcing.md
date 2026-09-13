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
