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

## Open item flagged, not yet resolved

`gsmStage` in the live API ("LXII", "LVIII") does not match the stated 0–6 GSM stage scale — it
looks like a running composite-surveillance-code sequence number, not a stage. `survCode`/`survDesc`
mentioning "GSM stage 0" separately suggests the real stage lives in `survDesc` text instead.
Confirmed at scale in the follow-up below.
