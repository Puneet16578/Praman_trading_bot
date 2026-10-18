# Defect Register

Every defect this project finds in itself, with an ID, root cause, fix, and re-verification
evidence — including ones introduced by this project's own code, per CLAUDE.md's verification
honesty rule.

| ID | Found | Severity | What it was | Status |
|---|---|---|---|---|
| P8-038 | 2026-10-04 registered follow-up | High | Original decision sizing ignores costs in the per-trade risk bound, and G6 does not enforce that bound including costs. | Repair implemented; regression and full replay verification pending |
| P8-037 | 2026-10-04 follow-up synthetic tests | Low | New missing-value rendering test matched `nan` inside the word `provenance`. | Fixed: match the standalone NaN token; no analysis affected |
| P8-036 | 2026-10-04 round-2 confirmation | Low | UTF-16 fragment in `.gitignore` made the scratch exclusion ineffective. | Fixed: UTF-8/LF rule; verified with `git check-ignore` |
| P2-001 | Ph. 2 (NSE ingestion, pre-flight) | High | `jugaad_data.nse.full_bhavcopy_save()` reports success (no exception) even when NSE returns an HTTP error page instead of real bhavcopy data. | Fixed — mitigated at the store layer |
| P2-002 | Ph. 2 (NSE ingestion, pre-implementation) | High | `sqlite3` silently binds a `numpy.int64`/`numpy.float64` parameter as a raw BLOB instead of an integer/float — no exception, no warning, and the store's own `numbers.Integral`/`numbers.Real` type check does not catch it (numpy scalars correctly satisfy those ABCs). | Fixed — store coerces to native `int`/`float` before binding |
| P2-003 | Ph. 2 (NSE ingestion, real-data verification) | High | NSE's bhavcopy archive can return HTTP 200 with well-formed CSV content for a **different date** than the one requested, under the requested date's own URL. For weekends/holidays this is a sane 1-3 day fallback to the nearest prior trading day; for 2019-09-30 specifically, the returned content was for 2019-06-27 — a 95-day anomaly, not a holiday fallback. This also invalidated this project's own earlier "earliest available date: 2019-09-30" claim, which had only checked "is this real CSV," not "is this CSV actually dated 2019-09-30." | Fixed — corrected earliest date to 2019-10-01; ingestion now compares the response's own DATE1 to the requested date and rejects (as a gap) any mismatch beyond a small fallback window |
| P2-004 | Ph. 2 (NSE ingestion, real-data verification) | Medium | A real NSE bhavcopy file can have a genuinely blank `SERIES` for some rows (observed: 30 of 43,942 rows in the 2019-10-01 file, all bond/NCD-like instruments — DHFL, HUDCO, IBULHSGFIN, IRFC). The parser's `str(nan_value).strip()` silently turned this into the literal text `"nan"` — a valid-looking, non-null string that passed the store's type check and would have corrupted the business key `(symbol, event_date, series)`. | Fixed — rows missing SYMBOL or SERIES are skipped (not force-labeled) and counted in `rows_skipped_invalid`, never silently stored |
| P2-005 | Ph. 2 (NSE ingestion, reporting review) | Medium | Gap reporting conflated "weekend/holiday, not a trading day" with "genuine ingestion failure on a real trading day" — a Saturday (hard HTML error) reported as "GAP" and a Sunday (small fallback to Friday's data) reported as "ingested," purely because of which artifact NSE happened to serve, not because of anything meaningfully different about the two dates. | Fixed — outcomes reclassified against a trading calendar derived from the batch's own observed `actual_event_date` evidence; GAP now means a date some other outcome confirms is real, but whose own fetch failed |
| P3-001 | Ph. 3 (corporate actions, parser widening review) | Low | The "N (word) Equity Share...for every M (word) Equity Shares" prose form of a bonus ratio (no colon) is common in real announcements (VBL, COSMOFIRST, XPROINDIA, MANINFRA, NYKAA, SBCL, KRISHANA all use it) and is not parsed — these land as `MATCHED_UNCONFIRMED`, which is safe (ratio still comes from `subject`) but avoidably conservative. | Known-deferred — optional polish, not built this session per explicit instruction |
| P3-002 | Ph. 3 (corporate actions, parser widening review) | Low | Bonus announcement text can be internally self-contradictory (BEPL: headline "ratio of 2:1" contradicted by its own explanatory clause "1 Equity Share...for every 2" — a real NSE authoring error). No internal-consistency check exists for bonus text the way `INTERNAL_MISMATCH` already exists for splits; currently caught only indirectly, via disagreement with `subject`, landing safely in `QUARANTINE`. | Known-deferred — optional polish, not built this session per explicit instruction |
| P3-003 | Ph. 3 (corporate actions, real ingestion) | Low | AFFLE's split announcement produces `INTERNAL_MISMATCH count=50.000004 fv=5.0` — a floating-point artifact (an extraction or rounding edge case), not a genuine inconsistency; the true ratio is very likely a clean 10.0. Currently and safely classified `MATCHED_UNCONFIRMED` (ratio still from `subject`), not silently trusted with the wrong number. | Known-deferred — optional polish, not built this session per explicit instruction |
| P4-001 | Ph. 4 (ASM ingestion, multi-era fixture verification) | Medium | `EXCLUSION_TITLE_RE` only matched the bare `"excluded from ASM Framework"` wording seen in the 2019/2021/2025/2026 samples. The real 2023 ST-ASM annexure phrases the same section as `"excluded from Short - Term ASM Framework"` — the regex silently missed it, and the section was mis-routed to `unparsed_titles` (undercounted, not fabricated, but still a real coverage gap). | Fixed — regex now accepts an optional `(Long|Short) - Term` infix and uses it to set `mechanism` directly when present |
| P4-002 | Ph. 4 (GSM ingestion, real-PDF verification) | Medium | `EVENT_DATE_RE`'s gap between the `GSM`/`framework` anchor and the `with effect from`/`w.e.f.` phrase excluded newlines (`[^\n.]`), on the assumption a stray period elsewhere in the paragraph was the bigger risk. Real GSM circular PDF text wraps mid-sentence — the 2024 sample's actual text is `"...Stage II of GSM\nwith effect from December 23, 2024."` — so the gap must cross a line break; the regex failed to find the event date on this real, correctly-formatted circular. | Fixed — gap changed to `[\s\S]{0,80}?` (any char including newline, still length-bounded) |
| P4-003 | Ph. 4 (GSM ingestion, real-network smoke test before the full run) | Medium | Even after P4-002's fix, 2 of 5 freshly live-fetched GSM circulars (`SURV71944`, `SURV71726`) still failed event-date extraction. Real cause: the literal phrase `"with effect from"` inside `EVENT_DATE_RE` used literal spaces, but these two circulars wrap the line break *inside* that phrase itself — `"...moved to Stage I of GSM with\neffect from December 23, 2025."` — a newline between "with" and "effect", not just before the phrase. | Fixed — literal spaces inside the phrase changed to `\s+` (`with\s+effect\s+from`) |
| P4-004 | Ph. 4 (full real ingestion run, first attempt) | **Critical** | The real DB's `surveillance_flags` table was created (empty) during Phase 1, before this table's schema was extended for real ASM/GSM data. `init_db()` only creates a table if a table of that name doesn't already exist — it never migrates an existing table when the registry's DDL changes. Every real write this session's first full ingestion run attempted failed with `sqlite3.OperationalError: table surveillance_flags has no column named action_type`. Final state after that run: `total_rows=0` — nothing was actually persisted, despite the run completing (exit code 0) and reporting `circulars_processed: 2883`. | Fixed — stale table was empty (verified: `SELECT COUNT(*)=0` before drop), so `DROP TABLE surveillance_flags` + `init_db()` re-create was a safe, lossless migration. Full ingestion re-run after the fix. |
| P4-005 | Ph. 4 (same run, report-accuracy review) | High | `ingest_asm_circular`/`ingest_gsm_circular` incremented `report.circulars_processed` **before** calling `write_facts`. When P4-004 made every write raise, the calling sweep loop's `except Exception` correctly counted each circular as failed too — but `circulars_processed` had already been bumped, so a circular whose data never reached the store was still counted as "processed." This is what let the first run's summary (`circulars_processed: 2883`) look like a mostly-successful run right next to `total_rows=0` in the same report — the two numbers should never have been able to disagree that badly. | Fixed — `circulars_processed` now increments only after `write_facts` returns without raising, in both modules |
| P4-006 | Ph. 4 (2nd full run, pre-retry failure-cause grouping) | High | `to_iso_date` only tried `%B` (full month name). Real circulars roughly SURV52458-58318 (mid-2022 to mid-2023) spell the w.e.f. date as `"Apr 03 2023"` — abbreviated month, no comma. This was **91% of all 482 ASM failures** (439/482, 232 distinct real date strings, all one shape) — the burst-and-plateau failure pattern that looked like it could be rate-limiting was mostly this one date-format gap. | Fixed — tries `%B %d %Y` then falls back to `%b %d %Y` |
| P4-007 | Ph. 4 (same pre-retry review) | High | Real circular SURV64061's subject was `"Applicability of Enhnaced Surveillance Measure (ESM)"` — `"Enhnaced"`, a genuine typo of `"Enhanced"` — which the `"enhanced"` exclusion stem in `is_periodic_asm_subject` did not catch, so an ESM circular (a mechanism CLAUDE.md explicitly says this project does not ingest) was nearly treated as periodic ASM. Investigating it also surfaced a second, independent bug: its zip nests the workbook in a subfolder (`"SURV64061/Annexure.xlsx"`), which the zip-entry matching (`nm.lower().startswith("annexure")`, a full-path check) missed entirely. | Fixed — added the bare `"esm"` substring (the `(ESM)` abbreviation, effectively typo-proof) to the exclusion check; zip-entry matching changed to match on the basename, not the full path |
| P4-008 | Ph. 4 (post-fix GSM failure review) | Medium | Two real 2026 GSM circulars (SURV72963, SURV72867) extract with spurious whitespace INSIDE digit runs — `"with effect from February 2 5, 2026"` for the 25th — a `pdfplumber` rendering artifact of that PDF generation era, not a real character in the source. `EVENT_DATE_RE`'s `\d{1,2}` cannot match across the injected space, so the event date silently failed to extract. **First attempted fix was itself briefly wrong**: collapsing all `\s+` between two digits also matched the *newline* between one table row's trailing number and the next row's leading serial number (real `MOVE_OUT_TEXT`-shaped text: `"...INE875R01011 EQ 20\n2 FSC..."`), merging two different rows' digits and breaking `ROW_RE`'s per-line matching — caught immediately by the existing `test_move_out_template_with_trailing_columns_and_footnote` test failing, before this second bug ever touched real data. | Fixed — collapse only `[ \t]` (not `\n`) between two digits |
| P4-009 | Ph. 4 (post-retry invariant check, per explicit "sum(event_counts) == COUNT(*)" assertion added to the analysis) | High | `report.event_counts` counted every PARSED event, not every event `write_facts` actually inserted -- `write_facts`'s own `BulkWriteResult.skipped_duplicate` was discarded. Real duplicates do occur: circulars SURV68086/SURV68088 (both ASM_LT, published the same calendar day) both listed ICDSLTD's Stage-I entry with the same event_date -- a genuine same-day corrective/reissue circular pair, the same pattern already documented for corporate actions (KITEX). `write_facts` correctly stored one row and silently skipped the duplicate; the report's summed `event_counts` (31,552) did not match the store's actual `COUNT(*)` (31,550) by exactly 2. One instance was confirmed directly (ICDSLTD); the second was not individually re-traced (would require re-fetching and re-parsing the full ~3,331-circular corpus a second time for zero data-correctness benefit -- the store itself, protected by the UNIQUE constraint, cannot hold a wrong or duplicated row either way) but is the same benign class of event. | Fixed — both `ingest_asm_circular`/`ingest_gsm_circular` now accumulate `report.duplicate_events_skipped` from `write_facts`'s return value; `sum(event_counts) - duplicate_events_skipped == COUNT(*)` holds exactly for all future runs |
| P4-010 | Ph. 4 (post-ingestion lifecycle-coherence check) | **Critical** | Footnote-definition rows were only recognized when the marker text landed in column 0. Real circular SURV49783's Annexure I-A has one at `(None, '* Moved from STASM to LTASM framework', None, None)` -- the Sr.No. cell (column 0) is blank, so the footnote text sits in the SYMBOL column position instead. The column-0-only check missed it entirely, it fell through to being treated as an ordinary data row, and `'* Moved from STASM to LTASM framework'` was ingested as a literal symbol (twice -- once as an ASM_LT ENTRY from SURV49783, once as an ASM_ST EXIT from SURV49784's analogous row). Found via a systematic lifecycle-coherence check across all 4,312 real (symbol, mechanism) tracks in the store, which flagged 3 tracks with a symbol string starting with `*`/`#` as structurally impossible. | Fixed — `_footnote_in_row` now scans every cell in a row (not just column 0): a row with exactly one non-blank cell, and that cell starting with a marker character, is a footnote row regardless of which column it lands in |
| P4-011 | Ph. 4 (same lifecycle-coherence check) | **Critical** | Real circulars mark individual symbols directly in the Symbol column (`"MARATHON *"`, `"IMAGICAA #"`), not only via a trailing marker on the Security Name column (the only place this project's parser checked). The marker was never stripped from the symbol value before storing, so the same real company split into two different stored symbol identities depending on whether a given circular happened to mark it (`"MARATHON"` vs `"MARATHON *"`) -- silently breaking lifecycle continuity (an ENTRY under one spelling with no matching EXIT, and vice versa). This was the dominant cause behind the "double-ENTRY, no EXIT between" and "EXIT with no prior ENTRY" cases the coherence check found far from the 2019-10-01 data floor (where left-censoring is the expected, benign explanation instead). | Fixed — `_strip_marker` strips a trailing `*`/`^`/`#` from both the Symbol and Security Name cells before either is used (as the business-key symbol, or to look up footnote `details`); the marker set was also widened to include `#`, observed for the first time in this circular |
| P4-012 | Ph. 4 (lifecycle-coherence check, second pass after P4-010/011 fixed but the not-near-floor categories did not collapse) | **Critical** | `is_periodic_asm_subject` requires the `"surve"` stem. Real circulars SURV49425/SURV60822/SURV63984/SURV69359 (four occurrences, 2021-2025) drop the word "Surveillance" entirely from their subject -- `"Applicability of Short-Term Additional Measure (ST-ASM)"` -- not a misspelling this project's typo tolerance could catch, an outright omission. These circulars were silently classified as not-periodic and never even attempted (not logged as a failure -- indistinguishable from the thousands of genuinely irrelevant SURV circulars). SURV63984 specifically is where symbol 63MOONS's real ASM exit lived; skipping it silently produced an apparent re-entry with no prior exit a month later, the exact symptom that first exposed this defect. | Fixed — added a narrow fallback: when `"surve"` is absent but `"applicab"`+`"measure"` are both present, accept the subject if it ends with the literal `"(ASM)"`/`"(ST-ASM)"` abbreviation (normalized to a trailing `"asm"`) -- an abbreviation never observed on any excluded-mechanism subject. **Superseded by P4-013** — see below. |
| P4-013 | Ph. 4 (tracing a second post-P4-012 incoherence case, ARENTERP) | **Critical / design change** | Tracing a `stage_mismatch` case the same way as 63MOONS found a SECOND, independent subject-classification miss: SURV49492's subject drops the word `"Measure"` instead of `"Surveillance"` -- `"Applicability of Short- Term Additional Surveillance (ST-ASM)"`. Two distinct real circulars each silently missing a *different* required word, found only by hand-tracing individual symbols' lifecycles, is exactly the pattern that makes an allowlist the wrong design for this data: a false negative is silent and requires exhaustive tracing to find, while a false positive under a denylist fails loudly (a fetch/parse attempt that doesn't match any known Annexure shape) the moment it happens. | **Redesigned, not just fixed** — `is_periodic_asm_subject` inverted from an allowlist (require positive stems) to a denylist (attempt every SURV circular subject unless it matches one of ~25 known-irrelevant categories, built from a full survey of all 1,756 distinct real subjects in the cached corpus, not guessed). Dry-run verified against the full cached index before any network use: converges to the same 62 distinct accepted subjects as the old allowlist, plus exactly 4 real typo/omission variants the allowlist missed, minus exactly 4 subjects the allowlist had wrongly swept in (a standalone ICA circular, two policy/framework announcements, one typo'd Encumbrance circular) — zero unexplained deltas either direction. |
| P8-001 | Ph. 8 (robustness review, before RESULTS.md was finalized) | **Critical** | Phase 8's Layers 2/3 scored the classifier and every baseline against the RAW `collapsed_90d` label, even though Phase 6 (`docs/phase6_signals.md`, Check 1) had already found that exact raw label "was tracking market drift, not move authenticity" and built `collapsed_relative` specifically to correct it. Layer 3's headline ("full system beats disclosure tier alone") was never checked against the label Phase 6's own findings said was the trustworthy one. | Corrected, not silently fixed — headline retracted. See `docs/phase8_robustness_checks.md` Check 1 for the full re-score under three alternative labels and the resulting before/after impact — the headline does not survive a label anchored away from the `return_20d` coupling (Check 1(b)/(c)). |
| P8-002 | Ph. 8b (feature re-analysis script, caught while writing it) | Low | `scripts/phase8b_feature_reauc.py`'s first draft read `cap_band` from `event_catalogue_loose_zscore_only.csv`, which only carries Phase 5's original 3-way (Small/Mid/Large) turnover-tercile split — not the 5-way (Micro/Small/Mid/Large/Mega) quintile bands Phase 7b/8's classification pipeline uses. Failed loudly (Micro/Mega rows silently matched zero events, printed `n/a`) before any number was published. Checked whether any earlier phase's real, published stratified analysis made the same mistake: no — `scripts/build_final_event_catalogue.py`'s 3-way `cap_band` was Phase 5's own deliberate, original design (used correctly by Phase 6's own 3-way stratification section); `scripts/fit_outcome_ensemble.py`, `scripts/build_event_classifications.py`, and `scripts/phase8_classify_holdout.py` each independently compute their own 5-way quintile bands and never read the catalogue's 3-way column. | Fixed before publishing — `phase8b_feature_reauc.py` now sources `cap_band` from `event_classifications.csv`/`phase8_2026_classifications.csv` instead. No retroactive correction needed elsewhere; logged per instruction to check, not because a real defect was found upstream. |
| P8-003 | Ph. 9 (adversarial lint pass + register-currency check) | **High / Critical (two parts)** | (1) `src/classification/event_classifier.py`'s `PROVENANCE_NOTE` and `DISCRIMINATIVE_POWER_NOTE`, rendered into every live report, stated "Phase 6 measured the combined signal ceiling at 0.611-0.70" — the exact figure `P8-001`'s correction withdrew. (2) `src/agent/banned_terms.py` missed 11 of 11 hand-written adversarial phrasings ("artificially inflated," "insider trading," "strong buy," bare "highly suspicious," "orchestrated," "circular trading," among others) — corroborating `tests/test_banned_terms_adversarial_evasion.py`'s own pre-existing, already-honestly-reported 0/5 finding (`docs/phase7c_agent_layer.md`) with a second, independently-authored phrasing set. | **Part (1) fixed** — both constants now cite `P8-001` and state the corrected finding (no top-tier lift, ~1.8% BSS); a stale test-file citation in `synthesis.py`'s docstring fixed alongside it; two test assertions that hardcoded the withdrawn "0.611" string updated to assert its ABSENCE instead. Full suite re-run: 326/326 pass. **Part (2) resolved architecturally, not by patching the lint** — confirmed zero LLM-provider-calling code exists anywhere in `src/`; `banned_terms.py` kept unchanged as a backstop (0/5 and 0/11 catch rates both recorded, not hidden); CLAUDE.md now states as standing policy that any future LLM-narrative capability must be local/dev-only and never reach shareable output — that is what enforces invariant 12's buy/sell/hold/target clause, not the lint. |
| P8-004 | Ph. 9 (writing `scripts/weekly_ingest.py`, first real end-to-end run) | **High** | `src/ingestion/nse_market_data/{asm,gsm}.py`'s `fetch_circular_index` returned `r.json()` directly, typed `-> list[dict]`. The REAL, live `nseindia.com/api/circulars` response is an envelope, `{"data": [...circulars...], "fromDate": ..., "toDate": ...}`, not a bare list. `for c in circulars` in `fetch_and_ingest_{asm,gsm}_range` therefore iterated the envelope dict's own keys (three strings) instead of its circulars, crashing on the very first real call: `AttributeError: 'str' object has no attribute 'get'`. Both functions' own docstrings already said "Not called by the fixture-based test suite" — this is why: neither had ever been run against real or realistically-shaped data in this project's history before this session's first attempt to automate weekly ingestion. | Fixed — both `fetch_circular_index` functions now return `r.json()["data"]`, confirmed against a real live call (26 real circulars returned for a real 2026-09 window, correct dict shape). Two regression tests added (`tests/test_asm_gsm_ingestion.py::FetchCircularIndexEnvelopeTest`), mocking the real envelope shape observed live — both pass. Full suite re-run after the fix; see re-verification below. |
| P8-005 | Ph. 9 (same first real run of `scripts/weekly_ingest.py`) | Medium | `weekly_ingest.py`'s own `_extract_gaps_and_mismatches` matched any line starting with `"GAP "` — but `ingest_bhavcopy_full_history.py` also prints an unconditional summary line, `"GAP (confirmed trading day, this request failed): 0"`, every run regardless of whether a real gap occurred. The bare-prefix match flagged that summary line as a real gap on every single run, including runs with zero real gaps — a false-positive that would have paged/alarmed on a clean week, every week. | Fixed — the match is now anchored on a trailing date (`^GAP \d{4}-\d{2}-\d{2}:`), matching only the real per-date gap lines. Re-verified live: a second end-to-end run (2026-09-22T17:17:03–17:42:13) reported a clean `GAPs: 0`, `overall=OK`. |
| P8-006 | Ph. 10 housekeeping (reproducibility gap flagged after `P8-004`) | **Critical** | Three scripts — `scripts/ingest_asm_gsm_sample.py`, `scripts/retry_asm_gsm_failures.py`, `scripts/ingest_corporate_actions_sample.py` — hardcoded paths into a PAST Claude session's own temp scratchpad directory (`C:\Users\...\Temp\claude\...\693aa27b-.../scratchpad\{sebi,cache}`) as their only source of historical circular/corporate-action/announcement data. Windows can delete that directory at any time; it does not exist on a fresh clone at all. A fresh clone therefore could not rebuild `surveillance_flags` or `corporate_actions` from scratch — directly contradicting this project's own README claim that its scripts do exactly that. `ingest_asm_gsm_sample.py` additionally duplicated `fetch_and_ingest_{asm,gsm}_range`'s own sweep logic in a second, parallel `run_asm`/`run_gsm` implementation (CLAUDE.md invariant 1). | Fixed, all three, by delegating to the live-network functions each domain already has (`fetch_and_ingest_{asm,gsm}_range`, `P8-004`-fixed; `fetch_all` for corporate actions) instead of any cache. `git grep` for the literal temp-directory path prefix across all of `scripts/` now returns zero matches. Full comparison and verification scope: `docs/phase10_housekeeping2.md`. |
| P8-007 | Ph. 10 housekeeping (Amendment 3's pre-specified split/bonus scan, run as a mechanism check against historical data) | **Critical, found not fixed** | This project's `corporate_actions` ingestion never captures ETF unit splits. A pre-specified scan for one-day returns shaped like a common unadjusted split/bonus ratio, run against the EXISTING historical catalogue as a mechanism check, found 96 hits, **zero** explained by an existing `BONUS`/`SPLIT` record — a large cluster are ETFs (`HDFCNIFETF`, `HDFCSENSEX`, `ICICI500`, `KOTAKGOLD`, etc.) sharing near-identical dates and near-exact ratios. Traced directly, not inferred from the shape alone: `HDFCNIFETF`'s raw bhavcopy close fell from 1628.18 (2021-02-16) to 162.44 (2021-02-17) — a real 10:1 unit split, `series='EQ'` (the same series equities use, so not a series-filtering gap), absent from `corporate_actions` entirely. This is the exact false-positive shape CLAUDE.md's own "Hard blocker" section already warns adjusted-return code about, occurring for real, for a whole instrument class this project's ingestion has never covered. | **Scoped precisely (`docs/phase10_p8007_scoping.md`), still found not fixed.** Full breakdown of the 96, using NSE's own live ETF list and a live per-symbol corporate-actions query (not our own store): 32 ETF-confirmed, 3 confirmed missed equity actions (each a distinct root cause — a regex gap, an unhandled action type, and an unresolved downstream drop later explained by `P8-008`), 61 with no corresponding live NSE record at all (price-move candidates). Root cause for ETFs confirmed directly (3 traced cases, 2 fund houses): NSE's corporate-actions endpoint does not carry ETF unit splits at all — a source-coverage gap, not a bug in our fetch/parse/tier logic. **ETF share: 3.91% TRAIN, 10.30% HOLD-OUT (growing); 43.90% of every `UNKNOWN_COVERAGE` event is ETF vs. 0.00% of every other disclosure tier** — the model's largest-magnitude coefficient substantially encodes instrument type, confirmed. **Contamination quantified and found immaterial**: 342 events (~0.4-0.46%), Phase 8b's feature AUC table re-run excluding them shifts every number under 0.003 — no conclusion changes. Still not fixed: identifying/ingesting a real ETF-split data source, and the equity-side gaps this scoping pass found (see `P8-008`). **Corrections pass (`docs/phase10_p8007_corrections.md`) supersedes the ETF-share numbers with a more complete ISIN-based method: `UNKNOWN_COVERAGE` fund-unit share revised to 61.22% (from the 43.90% live-list-only lower bound); shape-scan re-run on the equity-only population + corrected actions drops 96 hits to 55 (41 fund-unit-excluded, 3 explained by corrected actions, 52 persist unexplained). **Amendment 4 prep (`docs/phase10_amendment4_prep.md`): the equity-only rule is now APPLIED, not just measured** (excludes INF-prefix and unresolved ISINs; 3414 EQ symbols -> 2827 kept, catalogue 75,300 -> 70,638 events) and the refit CONFIRMS the hypothesis directly: `disclosure_UNKNOWN_COVERAGE`'s coefficient shrinks from -0.396295 to -0.159399 (less than half) once the fund-unit confound is removed — the largest-magnitude coefficient substantially WAS instrument type, not disclosure behavior, now measured post-correction rather than only inferred. Still not built: a real ETF-split ingestion source (out of scope -- ETFs are now excluded from the catalogue entirely, not adjusted for, per the applied rule). **CLOSED 2026-10-04 (user decision): mitigated by the equity-only rule, verified on current data by `scripts/desk_p8007_verification.py`; residual risks in the P8-007 section.** |
| P8-008 | Ph. 10, `P8-007` scoping (tracing why `UNIVASTU`'s real, parseable `"Bonus 2:1"` action was still missing) | **Critical, found — now code-fixed, live-swept, and PROMOTED to production** | `corporate_actions` has 702 total rows; **699 (99.6%) trace to the OLD, pre-`P8-006` scratchpad-cache file** (`source_file='nse_corporate_actions_2019_2026_cached.json'`), and only 3 come from real live ingestion (this week's `weekly_ingest.py` run). **The real, live, full historical sweep (`fetch_all(2019, 2026)`) — the function `P8-006` pointed `ingest_corporate_actions_sample.py` at — has never actually been executed.** This project's historical corporate-actions completeness has never been verified at scale; it is whatever an old, likely-partial "sample" cache happened to contain. Two additional, distinct equity-side gaps found while investigating (`docs/phase10_p8007_scoping.md` §1): `parse_subject_ratio`'s regex requires `\s+` immediately after `"Bonus"` and misses the real, hyphen-attached NSE phrasing `"Bonus- 1:2"` (confirmed: `AJANTPHARM`, 2022-06-22); the same function never attempts to parse Rights issues at all (confirmed: `M&MFIN`, `"Rights 1:1 @ Premium Rs 48/-"`, 2020-07-22) — a distinct, unhandled action type, not a parsing bug in an existing one. | **Corrections pass (`docs/phase10_p8007_corrections.md`): the full live sweep has now actually run** (18,190 raw actions/8yr, 578 announcement fetches — crashed once at #330 on a real NSE connection reset, resumed cleanly from cache with zero re-fetch, confirming the resumable design was necessary) **into a SEPARATE staging DB, diffed against production: 700/702 exact matches.** The regex and Rights gaps are fixed in code and tested (338/338 suite passes) — `QUARANTINE` and `RIGHTS` now write structural-break exclusion markers (`RATIO_CONFLICT_EXCLUSION`/`RIGHTS_EXCLUSION`) instead of being dropped/miscounted; `UNIVASTU` confirmed `QUARANTINE`-classified by current logic (garbled announcement ratio, same failure mode as `AURIGROW`), now correctly surfaced rather than silently missing. **Amendment 4 prep (`docs/phase10_amendment4_prep.md`): now promoted to production**, ISIN-resolved (`P8-010` fixed first) -- production `corporate_actions` 702 -> 974 rows (272 inserted, 679 true duplicates skipped), backed up before the write (`data/processed/praman_pre_p8007_promotion_backup_*.db`). `UNIVASTU`/`AJANTPHARM`/`HEG`'s split all confirmed correctly present post-promotion. Two rows (`PFC` `BONUS`, `HEG` `SPLIT`) now hold two coexisting vintages each (identical ratio, different knowledge_date/tier) -- append-only means neither is overwritten; `latest_as_of`'s max-knowledge_date tie-break resolution for both is verified and reported explicitly, not left to accident. |
| P8-009 | Ph. 10, `P8-007` corrections (caught while verifying item 2's own fix, before commit) | Medium, found and fixed same session | `event_catalogue.py` documents `STRUCTURAL_BREAK_ACTION_TYPES` as a deliberate, hand-mirrored copy of `price_adjustment.py`'s `UNADJUSTABLE_ACTION_TYPES` (a fast vectorized catalogue-build path vs. a slower, per-pair-verified path) — item 2's fix updated the former to add `RIGHTS`/`RATIO_CONFLICT` but missed the latter. Effect: `compute_adjustment_factor`/`adjusted_close` would silently treat a `RIGHTS`/`RATIO_CONFLICT` window as adjustment-neutral (factor unchanged, no exception) instead of raising `UnadjustableWindowError` — not a wrong factor, but a silent skip of the fail-closed exclusion item 2 exists to guarantee, on this module's slow path specifically. | **Fixed same session**, before affecting any real computation (no such row exists in production; nothing calls `compute_adjustment_factor` against the new staging data yet). `UNADJUSTABLE_ACTION_TYPES` now includes both new types, with a comment warning the two lists must be kept in sync by hand. Tests added (`RightsAndRatioConflictUnadjustableTest` in `test_price_adjustment.py`; two new window-exclusion tests in `test_event_catalogue.py`, which had no `RIGHTS`/`RATIO_CONFLICT` coverage at all before this). Full suite: 338/338 pass. Committed separately (`59d1dbf`). |
| P8-014 | Ph. 10, Amendment 5 prep (measuring the `P8-013` label's OWN missingness against model inputs, rather than assuming the redefinition alone had fixed it) | **Critical, found and fixed** | `P8-012`'s `extend_with_series` only appended an extension series' (`BE`/`BZ`) rows STRICTLY AFTER the primary series' own LAST-EVER date -- correct for a PERMANENT migration, blind to a TEMPORARY `EQ -> BE -> EQ` trade-for-trade stint (the common real shape for a surveillance-affected micro-cap, exactly the stock this project's classifier most wants to keep). A target date landing inside such a stint saw a stale pre-stint close and was wrongly marked missing. Confirmed directly, not assumed: 92.37% of TRAIN events missing under the `P8-013` label due to its staleness cap had a `BE`/`BZ` close in the exact window the old logic never looked at, and the resulting missingness was WORSE than before `P8-013` on the dimension it was meant to fix -- TRAIN missing rate 6.838% (4.3x the pre-`P8-013` rate) with a Micro-minus-Mega gap of 14.1pp (vs. 0.9pp before `P8-013`). `P8-013`'s own committed claim that the new label's missingness "isn't correlated with the model's own inputs" was asserted, not measured, and was wrong. | **Fixed, Amendment 5 (`docs/phase10_amendment5_prep.md`).** `build_symbol_history`'s `extend_with_series` now bridges per-date across the WHOLE calendar (any date the primary series lacks a row, from any extension series, primary series always wins on a shared date), not just the tail after the primary series' last date. Prototyped read-only first, then implemented with tests (temporary-stint bridging, same-date-conflict). Real effect: TRAIN missing rate 6.838% -> **1.310%**, Micro-minus-Mega gap 14.1pp -> **0.214pp**, TRAIN/HOLD-OUT gap 0.176pp -> 0.413pp (both comfortably within the 2.0pp commit bar). |
| P8-013 | Ph. 10, Amendment 4 prep round 4 (diagnosing round 3's own failed plateau measurement) | **Critical, found and fixed (see `P8-014` for a correction to this entry's own original claim)** | The pre-registration's own outcome definition (`relative_t0_primary`, Amendment 1 §1) required the SYMBOL'S OWN 90th real EQ trading session after `event_date` -- a thinly-traded stock needs disproportionately more CALENDAR time to reach that, so which events even HAVE a computable outcome is correlated with trading density, which is itself correlated with cap_band, volume_ratio, and other model inputs. Confirmed directly, not assumed: TRAIN missing-outcome rate by cap_band (buffer>=30 sessions) is a clean monotonic gradient, Micro 2.09% down to Mega 1.20% (`scripts/phase10_amendment4_selection_problem.py`); 5 spot-checked "missing" events in the worst band all had real gains of +31% to +59% once the artificial censoring was lifted -- not missing at random. Round 3's own attempt to fix this with a measured timing buffer failed to converge (no plateau within 120 sessions, `docs/phase10_amendment4_prep3.md`) because a buffer cannot fix an unbounded, feature-correlated tail; it can only be outrun by redefining the horizon itself. | **Fixed, Amendment 4 prep round 4 (`docs/phase10_amendment4_prep4.md`) -- but this entry's own original claim of near-total agreement/uncorrelated missingness compared only OLD-vs-NEW label AGREEMENT, not the new label's OWN missingness against model inputs, and `P8-014` found that quantity was badly correlated until fixed.** `relative_t0_primary` is redefined at a GLOBAL 90-session horizon (the market's own calendar, not the symbol's), using the symbol's last available close on or before that global date (with `P8-012`/`P8-014`'s EQ/BE/BZ bridge) and a 10-session staleness cap beyond which the outcome is genuinely MISSING rather than extrapolated. Old-vs-new label agreement 98.73% overall, a clean monotonic gradient by cap_band (Micro 96.60% -> Mega 99.79%) -- this part was correctly measured and stands. The new definition's FINAL (post-`P8-014`) missing-outcome rate is 1.310% (TRAIN) vs. 0.897% (HOLD-OUT) -- a 0.413pp gap, down from the own-session definition's 1.67% vs. 10.80% gap -- confirming the original elevated 2026 rate was almost entirely an artifact of the own-session definition, not genuine 2026-specific attrition. |
| P8-012 | Ph. 10, Amendment 4 prep round 2 (diagnosing HOLD-OUT's elevated missing-outcome rate) | **High, found and fixed for labels** | `build_symbol_history`'s EQ-only default means a stock moved to trade-for-trade settlement (`BE`/`BZ` series) -- a routine surveillance mechanism, disproportionately applied to exactly the kind of stock this project's own classifier flags -- silently looks "delisted": its EQ `trading_days` list stops abruptly at the series change, even though the security keeps trading under `BE`/`BZ`. Confirmed directly: 31.93% of HOLD-OUT's fully-elapsed-missing events (round 2 measurement) have `BE`/`BZ` rows after their own last EQ date; the series-move SHARE of TRAIN's own historical lacking events (28.64%) is nearly identical, confirming this is a constant background gap this project's ingestion has silently had since Phase 2, only surfaced by this diagnosis, not a 2026-specific problem. | **Fixed for label computation.** `build_symbol_history` (`src/signals/event_catalogue.py`) gains an optional `extend_with_series` parameter (default `()`, identical to before) -- appends rows from additional series STRICTLY AFTER the primary series' own last date, for label/outcome continuity only; the event catalogue itself (`build_final_event_catalogue.py`) stays EQ-only, unchanged, per instruction. Wired into `compute_outcome_labels.py` and `phase8_robustness_relabel_t0.py` with `("BE","BZ")`. Real, verified effect: HOLD-OUT's `possible_delisting_or_suspension` count dropped 709 -> 495 after this fix alone, and further to 368 once `P8-013`'s global-horizon redefinition was also applied. Tests: `ExtendWithSeriesTest` (4 cases, including deliberately NOT merging an overlapping-period row from the extension series). |
| P8-011 | Ph. 10, Amendment 4 prep (spot-checking the production promotion, `HEG` `SPLIT` row) | Low, found not fixed | The announcement-window cross-check fetch (`_fetch_announcements_for_actions`) queries NSE's corporate-ANNOUNCEMENTS endpoint using the action's raw, as-reported symbol (`HEGAM`) -- the same current-symbol-only reporting problem `P8-010` fixed for the corporate-ACTIONS endpoint and the final row write, but NOT for this earlier cross-check step. Observed real consequence: `HEG`'s real 2024-10-18 split now correctly resolves to `symbol=HEG` on write, but the announcement search (run as `HEGAM`) apparently failed to find the real announcement text the OLD pre-rename search once found, so this newly-added vintage is tagged `EX_DATE_FALLBACK` instead of the old cache's `MATCHED_UNCONFIRMED` -- a real, if narrow, tier-quality regression for this one row. Ratio (`10.0:2.0`) is identical in both vintages -- zero adjustment-factor impact, confirmed directly. | **Found, not fixed.** Low severity: 1 row observed affected across the entire 974-row post-promotion table; the correct ratio still reaches the store either way. Extending ISIN-aware resolution to the announcement-fetch step too (so the cross-check searches under the historically-correct symbol) is a real follow-up, deferred -- not built this session. |
| P8-010 | Ph. 10, `P8-007` corrections item 1 (tracing the full-sweep diff's 2 "present in ours, absent live" rows) | High, found and fixed | `HEG` (production) and `HEGAM` (live sweep) are the SAME security under two different symbol strings — confirmed via identical ISIN (`INE545A01024`), `HEG`'s own raw price showing the exact split (5.18x, 2024-10-18) and demerger (~62.6% drop, 2026-09-07) signatures, and `HEGAM` first appearing in this project's own bhavcopy the very next trading day (2026-09-22) after `HEG`'s last one. Real cause: `HEG` renamed its ticker to `HEGAM` around its 2026-09-07 demerger; NSE's live corporate-actions endpoint reports the security's ENTIRE history under its current symbol, retroactively, while this project's bhavcopy ingestion correctly preserves the ticker as traded on each historical date. This project's `corporate_actions`↔`bhavcopy` join is symbol-string-based throughout — a real structural gap for any security that changes ticker. | **Fixed, Amendment 4 prep (`docs/phase10_amendment4_prep.md`).** `src/ingestion/nse_market_data/isin_mapping.py` (new module) plus `resolve_isin_symbol`/`build_isin_candidates_for_actions` in `corporate_actions.py` resolve a raw action's reported symbol to whichever same-ISIN symbol was actually trading on its ex_date, using the action's own `isin` field. Applied during the real production promotion: `HEG`'s SPLIT is now correctly filed under `HEG`, not `HEGAM`. Found not to be the whole story: the ISIN map itself revealed **195 ISINs mapping to >1 symbol** (not just this one case), of which 19 have at least one action whose ex-date falls inside a sibling symbol's own trading window (26 orphaned actions total) -- 4 of these directly explain 4 of the P8-007 corrections' 52 persisting "unexplained" shape-scan hits once checked against the sibling's own action history. Also stitched price/label HISTORY across a rename (`build_symbol_history`'s new `symbol_group` parameter), since fixing action identity alone does not stitch bhavcopy itself -- measured necessary at ~0.52-0.54% of fully-elapsed catalogued events (just over the 0.5% bar set for doing this). See `P8-011` for a related, smaller gap found while verifying this fix. |

## P2-001 — `full_bhavcopy_save` silent failure on HTTP error

**Root cause.** `jugaad_data.nse.archives.NSEArchives.full_bhavcopy_raw()` calls
`self.get(...)` and returns `r.text` unconditionally — it never checks `r.status_code` or
validates that the response body is actually CSV. When NSE's server returns an HTML error page
(observed for every date before 2019-09-30 during this project's own history-depth probe), the
library writes that HTML to disk with a `.csv` extension and returns normally. A caller checking
only "did an exception get raised" gets a false positive.

**How it was found.** While empirically verifying the earliest retrievable bhavcopy date (a
pre-flight check requested before ingestion code was written), a sweep of dates from 2010 through
2019 all reported success. The returned files were suspiciously identical in size (3,651 bytes)
across totally unrelated dates spanning nine years. Reading one file's content directly showed
`<!DOCTYPE html>` — an NSE error page, not data. Binary-searching the real boundary by reading
file content (not trusting the library's return status) found the true cutover: 2019-09-27
(error page) vs. 2019-09-30 (real CSV, correct columns) — NSE introduced this combined
price+delivery file format starting 2019-09-30, seven business days later than the library's own
documented ("2019 and prior") claim would suggest, and precisely, not fuzzily.

**Fix / mitigation.** Per direction, content validation is NOT left as an ingestion-module nicety
that the next data source or a manual backfill could bypass. It lives in the store's write path
(`src/bitemporal/store.py`), which independently rejects any row/batch that doesn't match the
target table's declared shape before anything reaches SQLite:
- every declared column present (no silent partial row),
- every value's type checked against the table's declared `column_types` (numeric columns
  reject `bool` even though `bool` is an `int` subclass in Python),
- every non-nullable column rejected if `None`,
- the batch itself rejected if empty.

This does not make the store parse HTML — an HTML error page fed into ingestion's CSV parser
will fail to produce the expected columns at all and never reach the store as a row in the first
place. The store's independent check is the second, structural line of defense: it guarantees
that *no* future ingestion path (a different data source, a manual CSV backfill, a bug in a
parser) can smuggle a malformed row past validation just because it happened to not raise an
exception upstream.

**Re-verification.** See `tests/test_bitemporal_core.py`'s `StoreShapeValidationTest` class
(dtype rejection, null rejection, empty-batch rejection) and
`tests/test_nse_ingestion.py`'s content-validation test (an HTML fixture is rejected before
reaching the store). Both pasted with the Phase 2 test run.

## P2-002 — numpy scalar types silently mis-stored as BLOBs by sqlite3

**Root cause.** Python's `sqlite3` module binds query parameters by type-dispatch on the exact
Python type of the value. `numpy.int64`/`numpy.float64` (what every column of a pandas-parsed
CSV actually contains) are not recognized by `sqlite3`'s default adapters as `int`/`float` --
`sqlite3` falls back to treating them as a buffer-protocol object and silently writes the raw
memory bytes as a BLOB. No exception, no warning: `SELECT typeof(a)` on the written column would
report `blob`, not `integer`, and the stored bytes are not the decimal value at all.

This is NOT caught by `store.py`'s own dtype validation: `isinstance(numpy.int64(5),
numbers.Integral)` is `True` (numpy scalar types are registered with Python's numeric ABCs), so
the *shape* check that P2-001 added correctly says "this value is a valid integer" right before
`sqlite3` mis-serializes it anyway. Validating a value's logical type is not the same guarantee
as validating what the DB driver will actually persist for it.

**How it was found.** While building the bhavcopy ingestion module (which reads NSE's CSV via
pandas, whose numeric columns are numpy-typed by default), a deliberate pre-implementation check
of "does `sqlite3` actually bind numpy scalars correctly" was run before wiring pandas output
into the store at all. `conn.execute(..., (np.int64(5), np.float64(2.5)))` bound without error;
reading the row back showed column `a` as a Python `bytes` object containing raw memory, not the
integer 5.

**Fix.** `store.py`'s `_normalized_values()` now coerces every non-null value to the table's
declared native type (`int(...)` for `INTEGER`-marked columns, `float(...)` for `REAL`-marked
columns) immediately after shape validation and before it is ever bound to a SQL parameter --
this runs for every write path (`write_fact` and `write_facts`), so no future ingestion source
can reintroduce this by supplying numpy- or pandas-native numeric types.

**Re-verification.** `tests/test_bitemporal_core.py::NumericCoercionTest` inserts numpy-typed
values through both `write_fact` and `write_facts` and asserts `typeof(...)` on the stored column
is `integer`/`real`, not `blob`, and that the retrieved value round-trips to the correct number.
Pasted with the Phase 2 test run.

## P2-003 — NSE archive silently serves a different date's file than requested

**Root cause.** NSE's bhavcopy archive URL is keyed by requested date, but the file actually
returned is not always for that date. Observed behavior, confirmed by comparing the requested
date against the response CSV's own `DATE1` column across a systematic sweep:

| Requested | Actual DATE1 | Explanation |
|---|---|---|
| 2019-10-02 (holiday) | 2019-10-01 | Sane: falls back to nearest prior trading day |
| 2022-03-01 (holiday) | 2022-02-28 | Sane: same pattern |
| 2026-08-30 (Sunday) | 2026-08-28 | Sane: same pattern |
| 2026-09-06 (Sunday) | 2026-09-04 | Sane: same pattern |
| **2019-09-30** | **2019-06-27** | **Not a fallback — 95 days off, not 1-3** |

The first four are an undocumented but sensible archive convention (serve the last real trading
day's file under a closed-market date's URL). 2019-09-30 is different in kind: it is this
project's own previously-claimed "earliest available date," and it is a genuinely corrupted/
mislabeled archive entry on NSE's side, unrelated to the format-introduction boundary. This
directly invalidated CLAUDE.md's prior claim (checked only "is this real CSV, not an HTML error
page" — true for 2019-09-30, but the real CSV it returned was for the wrong date entirely).

**How it was found.** After the first real-data ingestion run, a sanity query for
`event_date='2019-09-30'` (one of the run's own reference dates) returned zero rows. Rather than
assume the ingestion silently dropped it, the raw response was re-fetched and inspected directly:
its `DATE1` column read `27-Jun-2019`. A systematic sweep of several other requested/actual date
pairs (table above) established the general fallback pattern and confirmed 2019-09-30 is the
outlier, not the rule.

**Fix.** Earliest usable date corrected in CLAUDE.md from 2019-09-30 to **2019-10-01** (verified:
requested date equals the response's own DATE1, exactly, with no fallback involved).
`ingest_bhavcopy_date` now compares the parsed rows' own event_date to the requested trade_date:
a small gap (≤7 calendar days -- covers holiday clusters) is accepted as the documented fallback
behavior and reported with `actual_event_date` distinct from the requested date; a larger gap is
rejected as a gap outcome with an explicit mismatch reason, never silently stored under an
assumption that the requested date was actually served.

**Re-verification.** `tests/test_nse_ingestion.py::DateMismatchTest` — a small (holiday-fallback)
mismatch is accepted and correctly labeled; a large (anomalous) mismatch is rejected as a gap, not
written to the store. Pasted with the Phase 2 test run. The real-data ingestion sample was re-run
with 2019-10-01 as the earliest reference date.

## P2-004 — blank SERIES silently stringified to the literal text "nan"

**Root cause.** `parse_bhavcopy_rows` built each row's `series` field as
`str(record["SERIES"]).strip()`. When pandas parses a genuinely blank CSV cell, the value is
`float('nan')`, and `str(float('nan'))` is the three-character string `"nan"` — a value that
passes every type/non-null check `store.py` runs (it IS a non-null `str`), while being
semantically meaningless and, worse, silently colliding across every affected row for the same
symbol+date under one fake shared "series."

**How it was found.** After the real ingestion sample, a query for symbol+event_date combinations
with more than one `series` value (checking the "multiple series, same date" case requested for
real-data guard re-testing) turned up `'nan'` in the set of distinct series values across the
dataset. Investigating which rows carried it traced to 30 rows, all in the 2019-10-01 file, all
NCD/bond-like instruments with unusually high per-unit prices (e.g. IRFC at 1240, IDFCFIRSTB at
9275) — consistent with debt instruments NSE's own file left the SERIES column blank for that day.

**Fix.** `parse_bhavcopy_rows` now checks `pd.isna()` on both SYMBOL and SERIES before building a
row; either being blank skips that row entirely (it cannot form a valid business key) and
increments a `skipped_invalid` counter returned alongside the valid rows, surfaced through
`DateIngestionOutcome.rows_skipped_invalid` — visible in ingestion reporting, never silently lost.

**Re-verification.** `tests/test_nse_ingestion.py::ParseBhavcopyRowsTest::test_row_with_missing_series_is_skipped_not_labeled_literal_nan`.
Pasted with the Phase 2 test run.

## P2-005 — gap reporting conflated "not a trading day" with "genuine ingestion failure"

**Root cause.** The first real ingestion run reported 2026-08-29 (a Saturday) as a "GAP" and
2026-08-30 (a Sunday) as "ingested," even though neither date is a real trading day. The
difference was purely an artifact of NSE's own serving behavior: a weekend sometimes returns a
flat HTML error (→ `BhavcopyFetchError` → status "gap"), and sometimes returns a small fallback to
the nearest prior trading day's file (→ status "ingested," with a mismatched `actual_event_date`
nobody was checking against the label). Neither label was actually correct: "gap" implies
something needs investigating; "ingested" implies the requested date itself had real data. A
weekend has neither problem — it's simply not a trading day.

**How it was found.** Pointed out directly: "Same situation, different outcome — the behaviour
depends on what NSE happens to serve, not on anything we control." Confirmed by inspecting the
per-date report from the first real run: 2026-08-29/2026-09-05 (Saturdays) labeled "GAP",
2026-08-30/2026-09-06 (Sundays) and 2022-03-01 (Holi, a real holiday) labeled "ingested" — despite
all five being equally non-trading-days.

**Fix.** `classify_against_observed_trading_calendar()` (`src/ingestion/nse_market_data/bhavcopy.py`)
derives which requested dates are genuine trading days purely from the batch's own evidence — the
set of `actual_event_date` values observed across every outcome (whether obtained directly or via
a neighbor's fallback) — with no new network calls and no external holiday calendar dependency.
Three outcomes, not two: `INGESTED` (a date's own direct fetch matched itself — real data for that
date), `NOT_A_TRADING_DAY` (nothing in the batch confirms the date was ever a real trading day —
the ordinary case for weekends and holidays alike), and `GAP` (some OTHER outcome confirms the
date is real, but this date's own fetch failed to retrieve it — a genuine anomaly). Coverage
reporting is now expressed against the derived trading calendar, not the raw calendar sweep.

**Re-verification.** `tests/test_nse_ingestion.py::TradingCalendarClassificationTest` — five cases,
including a synthetic true-gap (a neighbor's fallback confirms a date that its own fetch failed to
retrieve) and a reproduction of the exact real Aug29-Sep7 2026 pattern this project observed,
asserting zero genuine anomalies and the correct three not-a-trading-day dates. Re-run against the
real sample: 12 confirmed trading days, all 12 ingested, 0 gaps, 5 correctly excluded as
not-a-trading-day (`2022-03-01`, both Saturdays, both Sundays). Pasted with the Phase 2 test run.

## P4-001 — ASM exclusion-title regex missed the 2023-era "Short - Term" wording

**Root cause.** `EXCLUSION_TITLE_RE` was written against the T1/T2 (2025) and 2019/2021 samples,
all of which title the exclusion section the bare `"List of securities to be excluded from ASM
Framework w.e.f. ..."`. The 2023 ST-ASM circular (`SURV57402`) instead titles it `"...excluded from
Short - Term ASM Framework w.e.f. July 05, 2023."` — a real wording difference across eras that the
initial regex, matching only the literal phrase `"excluded from ASM Framework"`, did not
anticipate.

**How it was found.** After building the module against the T1/T2 reconciliation fixtures, a
broader verification pass ran the real parser (not an ad hoc script) against all five era-spanning
sample circulars used earlier for the format-stability check (2019/2021/2023/2025/2026). The 2023
case alone reported an unparsed title where none was expected; re-inspecting the raw section title
text directly showed the extra "Short - Term" wording the regex didn't tolerate.

**Fix.** `EXCLUSION_TITLE_RE` now matches an optional `(Long|Short)\s*-\s*Term\s+` infix before
`ASM Framework`; when present, that captured term sets `mechanism` directly (more specific than
falling back to the circular's own subject line), matching how `ENTRY_TITLE_RE`/
`TRANSITION_TITLE_RE` already derive mechanism from their own title text.

**Re-verification.** `tests/test_asm_gsm_ingestion.py::ParseSectionedAnnexureTest::test_short_term_exclusion_title_variant`
reproduces the exact 2023 title text and asserts it now parses to one `EXIT` event with
`mechanism="ASM_ST"`. Re-run against the real 2023 fixture directly: 0 unparsed titles (was 1),
5 events (was 3). Pasted with the Phase 4 test run.

## P4-002 — GSM event-date regex couldn't cross a real mid-sentence PDF line wrap

**Root cause.** `EVENT_DATE_RE` anchored on `(?:framework|GSM)\b[^\n.]{0,80}?(?:with effect
from|w\.e\.f\.?)...`, deliberately excluding both `.` and `\n` from the gap on the assumption that
a stray sentence-ending period elsewhere in the paragraph was the main risk of over-matching.
Real GSM circular PDF text (extracted via `pdfplumber`) wraps mid-sentence: the actual 2024 sample
reads `"...shall be moved to Stage II of GSM\nwith effect from December 23, 2024."` — the newline
between `"GSM"` and `"with effect from"` made the gap impossible to match, and the regex reported
"event date not found" on a real, correctly-formatted, non-degenerate circular.

**How it was found.** Verifying the GSM parser against three real circulars (2024 stage-move,
2026 stage-move, and a freshly-downloaded real 2025 "moving out of GSM" circular, `SURV71691`,
fetched specifically to check the EXIT template before writing its parsing logic) — the 2024 case
alone failed with `reason: event date not found`, despite the 2026 case (same subject template)
succeeding. Diffing the two extracted texts directly showed the only structural difference was the
line-wrap position relative to the anchor phrase.

**Fix.** Gap character class changed from `[^\n.]{0,80}?` to `[\s\S]{0,80}?` — any character,
including newlines, still bounded to 80 characters so it cannot run away across an unrelated
paragraph.

**Re-verification.** `tests/test_asm_gsm_ingestion.py::ParseGsmPdfTextTest::test_stage_move_template`
reproduces the real 2024 wrapped text and asserts `event_date == "2024-12-23"`. Re-run against the
real 2024/2026/SURV71691 PDF text directly: all three now resolve both dates correctly. Pasted with
the Phase 4 test run.

## P4-003 — "with effect from" itself wraps across a line break in some real circulars

**Root cause.** P4-002 fixed the gap *before* the `"with effect from"` anchor phrase to cross line
breaks, but the anchor phrase was still matched as a literal string with ordinary space characters
between its words. Two real, freshly live-fetched circulars (not present in the small sample set
used to build and initially verify the parser) wrap the line break *inside* the phrase itself:
`"...shall be moved to Stage I of GSM with\neffect from December 23, 2025."` — a newline exactly
between "with" and "effect". The literal-space match failed silently (no exception, just an
absent match), and the circular was correctly logged as a failure rather than mis-ingested with a
wrong or missing date — but it was still a real, avoidable gap.

**How it was found.** Before committing to the full real ASM/GSM ingestion run, a deliberate
network smoke test (10 real ASM + 5 real GSM circulars, freshly fetched live, not from the
scratchpad cache used to build the parser) was run first, specifically to catch exactly this kind
of format variance the small hand-picked sample set might have missed. 2 of 5 GSM circulars failed
with "event date not found"; fetching and reading those two circulars' PDF text directly showed the
line wrap fell inside the anchor phrase.

**Fix.** Every literal space inside `"with effect from"` changed to `\s+`
(`with\s+effect\s+from`), matching the same reasoning already applied to the surrounding gap in
P4-002.

**Re-verification.** `tests/test_asm_gsm_ingestion.py::ParseGsmPdfTextTest::test_with_effect_from_wrapped_across_a_line_break`
reproduces the exact real `SURV71944` wrapped text and asserts `event_date == "2025-12-23"`.
Re-run the same 5-circular live smoke test: 5/5 now succeed (was 3/5). Pasted with the Phase 4
test run.

## P4-004 — real DB's surveillance_flags table predated the Phase 4 schema and was never migrated

**Root cause.** `src/bitemporal/connection.py::init_db()` checks `sqlite_master` for a table of
each registered name and creates it only if absent — this is correct for a brand-new database, but
it means a table created under an OLDER version of `schema.py` (Phase 1's placeholder
`surveillance_flags`, with only `symbol/stage/event_date/knowledge_date` columns) is never altered
when the registry's DDL later changes. The real project DB (`data/processed/praman.db`) had
exactly this: an empty `surveillance_flags` table created during Phase 1, still in its original
shape, when this session's schema extension (adding `mechanism`, `action_type`, `from_stage`,
`to_stage`, `source_circular`, `details`) was made. Nothing in `init_db()`, `store.py`, or the
ingestion modules checks that an existing table's actual columns match the registry's current
declaration.

**How it was found.** The first full real ingestion run (`scripts/ingest_asm_gsm_sample.py`, 3,334
ASM + 131 GSM circulars) completed with exit code 0 and reported `circulars_processed: 2883`, which
read as a mostly-successful run. But `circulars_failed: 3298` (more failures than circulars even
attempted, a red flag on its own — see P4-005) all shared one literal reason string:
`"table surveillance_flags has no column named action_type"`. The run's own final summary line,
`min_event_date=None max_event_date=None total_rows=0`, made the real severity unambiguous: not
"mostly ingested with a to be reasonable failure rate", but zero rows actually persisted. Checked
directly: `SELECT sql FROM sqlite_master WHERE name='surveillance_flags'` on the real DB showed the
Phase 1 six-column shape, not the current registry's twelve-column shape.

**Fix.** Confirmed the stale table held zero rows (`SELECT COUNT(*)`) before touching it — this was
a schema migration of empty structure, not a data mutation, and would have been refused otherwise.
`DROP TABLE surveillance_flags` followed by `init_db()` (which then created it fresh from the
current registry DDL) brought the real DB in line with `schema.py`. This project has no general
schema-migration mechanism; a future DDL change to an already-populated table would need an
explicit, reviewed migration path (ALTER TABLE / rebuild-and-copy), not this drop-and-recreate
shortcut, which is safe here specifically because the table was empty.

**Re-verification.** `SELECT sql FROM sqlite_master ...` re-checked and matches `schema.py`'s
current `SURVEILLANCE_FLAGS.ddl` exactly. Full ingestion re-run after this fix (see
`docs/phase4_asm_gsm_sourcing.md` for the resulting row counts) actually persisted rows this time,
confirmed by a non-zero `total_rows` and non-`None` min/max `event_date` in the re-run's summary.

## P4-005 — a circular whose write failed could still be counted as "processed"

**Root cause.** `ingest_asm_circular`/`ingest_gsm_circular` incremented `report.circulars_processed`
immediately after parsing succeeded, then called `write_facts` afterward. If `write_facts` raised
(as every call did during the P4-004 incident), the exception propagated up to the caller's sweep
loop, which correctly appended the circular to `circulars_failed` — but `circulars_processed` had
already been incremented and was never rolled back. A circular could therefore be counted in both
`circulars_processed` and `circulars_failed` simultaneously, inflating the "processed" figure to
look far healthier than the actual state of the store.

**How it was found.** Investigating the P4-004 incident's numbers: `circulars_processed: 2883` and
`circulars_failed: 3298` sum to more than the 3,334 ASM circulars actually attempted, which is only
possible if some circulars were double-counted. Tracing `ingest_asm_circular`'s code directly
showed `report.circulars_processed += 1` sits before the `write_facts(...)` call it depends on for
correctness, not after.

**Fix.** Reordered both functions so `circulars_processed` (and, for ASM, the recording of
`unparsed_section_titles`) increments only after `write_facts` returns without raising. A circular
whose write fails is now counted exactly once, as failed, never additionally as processed.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::IngestAsmCircularTest::test_failed_write_is_never_counted_as_processed`
and the GSM-side equivalent in `IngestGsmCircularTest` each construct a connection with the stale
(pre-Phase-4) table shape, assert the write raises, and assert `report.circulars_processed == 0`
afterward. Pasted with the Phase 4 test run.

## P4-006 — abbreviated, comma-less month names not recognized in w.e.f. dates

**Root cause.** `to_iso_date` parsed the extracted month/day/year text with a single format,
`"%B %d %Y"` (full month name required). Real ASM circulars roughly SURV52458 through SURV58318
(a contiguous run corresponding to mid-2022 through mid-2023) title their sections with the w.e.f.
date spelled `"Apr 03 2023"` — an abbreviated three-letter month with no comma — rather than the
`"April 03, 2023"` form used in every other sampled era. `strptime` with `%B` rejects an
abbreviated month outright.

**How it was found.** Per direction, the 482 ASM failures from the second full ingestion run were
grouped by normalized cause *before* any retry was attempted (see the run's failure-cause
breakdown). 439 of 482 (91%) shared the exact same error shape, `"time data '<X>' does not match
format '%B %d %Y'"`; extracting the 439 raw date strings found 232 distinct values, every one of
them the three-letter-month, no-comma shape. This directly falsified the initial hypothesis that
the run's bursty failure pattern (clean recovery between failure clusters) was NSE-side rate
limiting — it was a real, single-cause format gap concentrated in one calendar era, not a
transient network problem, and no amount of retrying with backoff would ever have fixed it.

**Fix.** `to_iso_date` now tries `"%B %d %Y"` first (the common case), then falls back to
`"%b %d %Y"` (abbreviated month) before raising.

**Re-verification.** `tests/test_asm_gsm_ingestion.py::ToIsoDateTest::test_abbreviated_comma_less_month_p4_006`
asserts `to_iso_date("Apr 03 2023") == "2023-04-03"` and two more real observed strings. This fix
also resolved GSM's one date-format failure (SURV74620, `"Jun 10 2026"`) for free, since GSM's
date parsing shares this same function.

## P4-007 — ESM typo bypassed the exclusion filter; and a nested zip path

**Root cause (two independent bugs found investigating one failure).** Real circular SURV64061's
subject line was `"Applicability of Enhnaced Surveillance Measure (ESM)"` — `"Enhnaced"`, a
letter-transposition typo of `"Enhanced"` in NSE's own manually-typed title. `is_periodic_asm_subject`'s
exclusion check looked for the substring `"enhanced"` in the normalized subject; `"enhnaced"` does
not contain that substring, so this ESM circular (a mechanism CLAUDE.md explicitly records as
deliberately not ingested) would have been treated as a periodic ASM circular and ingested under
the wrong mechanism. Investigating why its ingestion attempt failed (rather than silently
succeeding under the wrong label) surfaced a second, unrelated bug: its zip nests the workbook one
level down (`"SURV64061/Annexure.xlsx"`), and `parse_circular_zip_bytes`'s
`nm.lower().startswith("annexure")` check matches against the full zip-entry path, which never
starts with `"annexure"` when the entry is inside a subfolder.

**How it was found.** Investigating the non-date, non-network ASM failures from the second run
(4 remaining after date-format and connection-error causes were set aside) turned up SURV64061's
`"No Annexure*.xlsx found in zip"` error. Checking the cached circular index directly for this
circular's actual subject revealed the ESM/"Enhnaced" title before the zip-structure issue was
even examined — the exclusion-filter gap is the more serious of the two, since it would have
silently mis-labeled real data rather than merely failing to parse it.

**Fix.** Added the bare `"esm"` substring to `is_periodic_asm_subject`'s exclusion check — every
real ESM subject carries the literal `"(ESM)"` abbreviation, three capital letters a typo is very
unlikely to hit, unlike the full word "Enhanced." Independently, `parse_circular_zip_bytes` now
matches the Annexure workbook by the zip entry's basename (last `/`-separated segment), not the
full path.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::IsPeriodicAsmSubjectTest::test_esm_excluded_including_the_real_enhnaced_typo`
asserts both the correctly-spelled and the real "Enhnaced" subject are excluded.
`ParseCircularWorkbookTest::test_annexure_nested_inside_a_zip_subfolder_is_still_found` reproduces
the exact real `"SURV64061/Annexure.xlsx"` zip layout and asserts the workbook is still found and
parsed. Pasted with the Phase 4 test run.

## P4-008 — stray whitespace inside digit runs in some real 2026 GSM PDFs

**Root cause.** Two real GSM circulars (SURV72963, SURV72867, both February 2026) extract via
`pdfplumber` with spurious single-space characters inserted inside otherwise-contiguous digit
sequences — `"with effect from February 2 5, 2026"` for what is genuinely the 25th, similarly
`"NSE/SURV/ 72963"` and `"Stage I I"` for "Stage II." This is a rendering artifact of whatever PDF
generation tool produced circulars from that period, not a real character in the source document.
`EVENT_DATE_RE`'s `\d{1,2}` cannot match across the injected space, so `parse_gsm_pdf_text` could
not find the event date at all.

**How it was found.** After the date-format (P4-006) and connection-error causes were set aside,
inspecting the real PDF text of the two remaining unexplained ASM-adjacent... (GSM) failures
directly showed the character-level spacing artifact.

**First fix attempt was itself wrong, caught immediately.** The first version collapsed all
whitespace (`\s+`, which matches `\n`) between two digits. Running the full test suite immediately
after showed `test_move_out_template_with_trailing_columns_and_footnote` failing: real move-out-
template text has one row's trailing number directly followed by a newline and the next row's
leading serial number (`"...INE875R01011 EQ 20\n2 FSC..."`), and the `\s+` version merged the
`"20"` and `"2"` across that newline, corrupting `ROW_RE`'s per-line row matching and silently
dropping the FSC row.

**Fix.** Restricted the collapse to horizontal whitespace only (`[ \t]`, explicitly not `\n`) —
`re.sub(r"(?<=\d)[ \t]+(?=\d)", "", text)`. This still merges the same-line digit splits
(`"2 5"` → `"25"`, `"NSE/SURV/ 72963"` unaffected since a space after `/` isn't between two
digits) without ever crossing a line boundary.

**Re-verification.** `tests/test_asm_gsm_ingestion.py::ParseGsmPdfTextTest::test_digits_split_by_a_stray_space_are_collapsed_p4_008`
reproduces the real SURV72963 text shape and asserts both dates resolve correctly. The full suite
(148 tests, including the move-out-template test the first attempt broke) passes. Re-verified
against both real live circulars directly: SURV72963 → GLFL, ENTRY, Stage II, event_date
2026-02-25; SURV72867 → ARSHIYA, ENTRY, Stage I, event_date 2026-02-19.

## P4-009 — event_counts double-counted a genuine cross-circular duplicate

**Root cause.** `ingest_asm_circular`/`ingest_gsm_circular` called `write_facts(...)` and
discarded its return value, then unconditionally incremented `event_counts` for every event the
parser produced. `write_facts` silently and correctly skips a row whose exact business key
(symbol, mechanism, event_date, knowledge_date) already exists — the intended, tested idempotency
behavior — but nothing in the calling code distinguished "this event was newly inserted" from
"this event was already present and correctly skipped." A report built purely from parsed-event
counts therefore overstates the store's actual row count whenever two different circulars
legitimately describe the identical fact.

**How it was found.** The invariant assertion added to the post-ingestion analysis script per
explicit instruction (`sum(event_counts) == COUNT(*) FROM surveillance_flags`) failed on the real,
full post-retry dataset: reported 31,552, stored 31,550, diff=2. Rather than treat a diff of 2 out
of 31,552 as noise, the 27 real same-day/same-mechanism ASM circular pairs found in the cached
circular index were re-fetched and re-parsed directly to check for overlapping events; one pair,
SURV68086/SURV68088 (both ASM_LT, both dated 2025-05-20), both produced an identical
(ICDSLTD, ASM_LT, 2025-05-21) event. The second unit of the diff=2 was not individually
re-traced — doing so would require re-parsing the full successfully-processed corpus a second
time, and the store itself cannot contain a wrong or duplicated row regardless (the UNIQUE
constraint already guarantees that); only the *report's* count was ever inaccurate.

**Fix.** Both ingestion functions now capture `write_facts`'s returned `BulkWriteResult` and
accumulate its `skipped_duplicate` count into a new `report.duplicate_events_skipped` field.
`event_counts` still reflects parsed events (useful for describing what a circular's own Annexure
said); `sum(event_counts) - duplicate_events_skipped` is what should be compared against the
store's `COUNT(*)`, and does so exactly.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::IngestAsmCircularTest::test_two_same_day_circulars_naming_the_same_symbol_is_tracked_as_a_duplicate_not_lost`
reproduces the exact real SURV68086/SURV68088/ICDSLTD shape (two circulars, same day, same
symbol/mechanism/event_date) and asserts `sum(event_counts) - duplicate_events_skipped ==
COUNT(*)` holds. `test_reingesting_the_same_circular_is_idempotent` was extended to also assert
`duplicate_events_skipped == 2` on a full re-ingest. Pasted with the Phase 4 test run.

## P4-010 — footnote-definition rows outside column 0 were ingested as bogus symbols

**Root cause.** The footnote-row check looked only at `_cell(row, 0)` for a string starting with
`*`/`^`. Real circular SURV49783's Annexure I-A sheet has a footnote row shaped
`(None, '* Moved from STASM to LTASM framework', None, None)` — its Sr.No. column is blank (this
footnote doesn't number a symbol row, it clarifies the one directly above), so the marker text
lands in the Symbol column position, not column 0. The check missed it, the row fell through to
ordinary data-row handling, and `_valid_symbol()` correctly saw a non-empty, non-"Nil" string and
accepted it — because nothing about that check knows a footnote from a symbol by content alone.

**How it was found.** A systematic coherence check was run across every one of the 4,312 real
(symbol, mechanism) tracks in the store (ENTRY → STAGE_CHANGE* → EXIT should never show two
ENTRYs with no EXIT between, or an EXIT with no prior ENTRY, except near the 2019-10-01 data floor
where left-censoring is expected). Three tracks had a "symbol" starting with `*` or `#` —
structurally impossible for a real NSE ticker — which is what triggered fetching the real source
circular directly rather than assuming the store was simply incomplete.

**Fix.** `_footnote_in_row` now scans every cell in the row: a row counts as a footnote definition
if exactly one cell is non-blank and that cell's text starts with a marker character, regardless
of which column position it occupies.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::ParseSectionedAnnexureTest::test_footnote_row_in_the_symbol_column_not_parsed_as_a_symbol`
reproduces the exact real SURV49783 row shape and asserts exactly one real event (MARATHON) is
produced, not two. Re-verified against the real SURV49783/SURV49784 circulars directly: no bogus
symbols in either circular's output. Pasted with the Phase 4 test run.

## P4-011 — marker attached directly to the Symbol cell was never stripped

**Root cause.** The parser checked for a footnote marker only on the Security Name cell
(`name.strip()[-1:] in ("*", "^")`), using it to attach `details` but never to clean the symbol
itself. Real circulars mark individual securities directly on the Symbol cell instead
(`"MARATHON *"`, `"IMAGICAA #"` — the latter using `#`, a marker character not previously seen).
Since the marker was never stripped, the stored `symbol` value carried it verbatim, and the exact
same real company would be stored under two different symbol strings across different circulars
depending on whether that particular circular happened to mark it — silently fragmenting one
company's ASM history into two unrelated (symbol, mechanism) tracks.

**How it was found.** Same lifecycle-coherence check as P4-010. After excluding cases explained by
the 2019-10-01 data floor (left-censoring), 117 "EXIT with no prior ENTRY" and 90 "double-ENTRY, no
EXIT between" tracks remained unexplained. Inspecting SURV49783/SURV49784 directly (already being
fetched for P4-010) showed the real cause for at least this pair: `"MARATHON *"` (marked, in
SURV49784's exclusion list) versus `"MARATHON"` (unmarked, in SURV49783's entry list) would have
been stored as two different symbols for what is obviously the same real company (same ISIN,
`INE182D01020`, in both rows).

**Fix.** `_strip_marker` strips a trailing marker character (now `*`, `^`, or `#`) from a cell
value, returning the clean value and the marker separately. Applied to both the Symbol and
Security Name cells before either is used — the clean, marker-free symbol is what becomes the
business-key `symbol`; whichever cell actually carried a marker is used to look up the matching
footnote text for `details`.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::ParseSectionedAnnexureTest::test_marker_on_symbol_with_hash_character`
reproduces the real SURV49784 `"IMAGICAA #"` row and asserts the stored symbol is `"IMAGICAA"` with
`details="As per BSE"`. `test_marked_symbol_matches_unmarked_symbol_across_circulars` asserts a
marked and an unmarked appearance of the same real symbol (`"MARATHON *"` vs `"MARATHON"`) resolve
to the identical stored value. The full ingestion was re-run after this fix (see
`docs/phase4_asm_gsm_sourcing.md` for the before/after lifecycle-coherence numbers). Pasted with
the Phase 4 test run.

## P4-012 — "Surveillance" dropped entirely from four real circular subjects

**Root cause.** `is_periodic_asm_subject` requires the `"surve"` stem to appear anywhere in the
normalized subject -- deliberately typo-tolerant (P4-006's era already showed "Surveillanvce" and
similar misspellings), but a typo-tolerance check only helps when some form of the word is
present. Four real circulars (SURV49425 in 2021, SURV60822 and SURV63984 in 2024, SURV69359 in
2025) title themselves `"Applicability of Short-Term Additional Measure (ST-ASM)"` -- the word
"Surveillance" is not misspelled, it simply is not there. `"surve"` never appears, and the primary
check correctly (given its own rule) rejected the subject.

**How it was found.** After P4-010/P4-011 were fixed and the full ingestion re-run, the
categorized lifecycle-coherence check (run before any retry, specifically to isolate whether the
marker fix was the *whole* explanation) showed the not-near-floor incoherence categories had NOT
collapsed toward zero as expected (`double_entry` 90→93 even went up slightly; `stage_mismatch`
17→20). Per instruction, this was treated as evidence of a second real defect rather than accepted
as a smaller, "good enough" number. One concrete case was traced to ground truth directly: symbol
63MOONS showed ENTRY on 2024-09-10 and ENTRY again on 2024-10-16 with no EXIT between. Its presence
was checked circular-by-circular across every real ST-ASM circular in that window via its
Consolidated-sheet snapshot, which pinpointed the disappearance to somewhere between SURV63967
(2024-09-16, present) and SURV64008 (2024-09-18, absent) -- but 63MOONS appeared in neither
circular's Annexure II. Listing every SURV circular of any subject in that exact date range
surfaced SURV63984 (2024-09-17), whose subject the classifier had rejected; fetching it directly
confirmed 63MOONS's real EXIT (`"* Due to Shortlisting in ESM"`) sitting in its Annexure II, exactly
where it should be if the circular had been included.

**Fix.** Added a narrow, evidence-based fallback to `is_periodic_asm_subject`: when `"surve"` is
absent but `"applicab"` and `"measure"` are both still present, accept the subject anyway if it
ends with the normalized `"asm"` suffix -- the literal `"(ASM)"`/`"(ST-ASM)"` abbreviation every
real periodic subject carries as its last token, and which does not appear as a subject-ending
abbreviation on any of the excluded mechanisms (GSM/ESM/IBC/pledge all end differently, and are
excluded earlier in the same function regardless). Checked directly against the full cached
circular index: exactly 4 circulars are recovered by this fallback, all four the identical real
shape, and re-checking every already-passing real subject in the corpus confirms nothing new is
wrongly included.

**Re-verification.**
`tests/test_asm_gsm_ingestion.py::IsPeriodicAsmSubjectTest::test_surveillance_word_dropped_entirely_p4_012`
asserts both the real SURV63984 subject and its LT equivalent are now accepted. The full ingestion
was rebuilt a third time after this fix; see `docs/phase4_asm_gsm_sourcing.md` for the resulting
lifecycle-coherence numbers, which is what confirms whether this was the full remaining
explanation.

## P4-013 — allowlist inverted to a denylist after a second, independent subject-classification miss

**Root cause.** Not a single bug but a design flaw: `is_periodic_asm_subject` required specific
positive stems to be present (`"applicab"`, `"measure"`, and either `"surve"` or the `"(ASM)"`
abbreviation after P4-012). This structurally cannot distinguish "a genuine periodic circular with
an unanticipated typo/omission" from "a genuinely irrelevant circular" — it can only ever react to
variants already seen. After P4-012 (the "Surveillance" omission) was fixed and the full ingestion
rebuilt, the categorized lifecycle-coherence check's not-near-floor categories dropped but did not
collapse to zero. Tracing a second case (`ARENTERP`, `stage_mismatch` on 2021-09-13) the same way
63MOONS had been traced found `SURV49492`, subject `"Applicability of Short- Term Additional
Surveillance (ST-ASM)"` — this time the word `"Measure"` is missing, a distinct omission from
P4-012's. Two independent real circulars, each dropping a *different* required word, is the
pattern that makes an allowlist fundamentally the wrong shape for manually-typed, 7-years-of-typos
real data: nothing bounds how many more such variants exist, and each one is silent until someone
manually traces the exact symbol and date range it affected.

**How it was found.** Per explicit instruction, the categorized coherence check was re-run after
every fix rather than accepted on a shrinking-number basis, specifically to catch exactly this
kind of "improved but didn't fully collapse" result. `ALOKTEXT` was traced first and resolved to
an already-known, unfixable cause (`SURV42671`'s missing Annexure). `ARENTERP` was traced second
and found the new, second cause above. At two independent misses of the same general shape, the
call was made to stop patching individual variants and change the underlying design.

**Fix.** `is_periodic_asm_subject` inverted from an allowlist to a denylist: attempt every SURV
circular subject by default, reject only if it matches one of roughly 25 explicit categories
(GSM/ESM/IBC/ICA/Encumbrance/pledge/Deep-OTM/Trade-for-Trade/Persistent-Noise/policy-framework
updates/individual SEBI-SAT-NCLT order & directions circulars/price-band changes/algo-trading
notices/order-to-trade-ratio/surveillance-administrative circulars/standardization & SOP
notices/USDINR conversion/withholding-payout/trade-cancellation-mechanism/position-limit
notices/ETF notices/broker-confidence measures/caution & advisory notices/vendor-tech-admin
circulars/client-due-diligence/member-dashboard/derivatives-contract-specific notices/illiquid
securities/misc risk-control notices). These categories were built from a full survey of all 1,756
distinct real subjects in the cached 2019-2026 index (`survey_output.txt`, this session's
scratchpad), not guessed, and iterated three times against real typo variants found the same way
as the positive-side ones (`"Confimatory"` for Confirmatory, `"Coriggendum"` for Corrigendum,
`"Cautionary"` not matching a bare `"caution"` word-boundary check, `"Encumberance"` typo, "Placing
**of** Orders at..." breaking an adjacency-only regex, `"SAT orders"` plural not matching a
singular-only pattern).

**Verified before any network use.** A dry run compared the new denylist against the old allowlist
over all 7,936 cached circulars with zero fetches: identical 62 distinct subjects accepted in
common; exactly 4 distinct subjects (5 circulars) newly accepted, all confirmed genuine periodic
circulars with a real typo/omission (`"Application"` for "Applicability", `"Appllicability"`
typo, and two more instances of the "Measure"-dropped shape); exactly 4 distinct subjects newly
rejected, all confirmed correct exclusions (a standalone ICA circular the old allowlist had wrongly
sub-classified as generic ASM, two LT-ASM policy/scope-announcement circulars that are not periodic
entry/exit lists, and the "Encumberance" typo variant of the Encumbrance category). Zero
unexplained deltas either direction.

**Re-verification.** All 154 existing tests continue to pass unchanged (the denylist reduces to
the same accept/reject decisions for every case they cover). The full ingestion was rebuilt a
fourth time after this change; see `docs/phase4_asm_gsm_sourcing.md` for the resulting
lifecycle-coherence numbers.

## P8-001 — Phase 8 Layers 2/3 scored against the raw label Phase 6 had already shown was contaminated

**Root cause.** `docs/phase6_signals.md`'s Check 1 measured the raw `collapsed_90d` label swinging
50.6%-74.1% by year and concluded plainly: "the raw label was tracking market conditions, not move
authenticity, exactly as suspected." Phase 6 then built `collapsed_relative` (equal-weighted
EQ-index-adjusted) specifically as the corrected label and used it for every subsequent Phase 6
measurement (AUC stratification, the ensemble ceiling). Phase 8's Layer 2/3 scripts
(`scripts/phase8_layer2_metrics.py`, `scripts/phase8_layer3_baselines.py`) were written afresh
against `collapsed_90d` — the same raw label Phase 6 had already flagged — without carrying that
correction forward. Nothing enforced consistency between the two phases; the label choice was
never revisited when Phase 8 started.

**A second, independent problem compounded the first, only found by the robustness review that
caught this one:** `collapsed_90d`'s own pre-move base (`close(event_date − 20)`) is the *identical*
anchor `return_20d_context_only` is computed from. A stock with a small `|return_20d|` sits close to
that base by construction and crosses back over it on almost any subsequent move, real signal or
none — a mechanical coupling between the label and the classifier's own `momentum_high` input,
independent of the market-drift problem above.

**How it was found.** A pre-registered robustness review (`docs/phase8_robustness_checks.md`, Check
1), requested before RESULTS.md was finalized, explicitly because the 2026 base rate reported in
Layer 2 (74.1%) is the exact top of the range Phase 6's own Check 1 had already named as
market-drift-contaminated.

**Fix / resolution.** Not a code fix — a measurement correction. `docs/phase8_robustness_checks.md`
Check 1 re-derives TRAIN-only score tables and re-scores baseline 3 vs. baseline 4 under three
alternative labels (`collapsed_relative`, and a new pre-registered label anchored at the event-day
close instead of `event_date − 20`). The decomposition isolates which of the two problems drove the
headline, measured as LIFT over each label's own base rate (raw Brier/precision are not comparable
across labels with different base rates — an earlier draft of this decomposition made exactly that
invalid comparison and was corrected before publishing): correcting market drift alone
(`collapsed_90d` → `collapsed_relative`, same t−20 anchor) barely moves the classifier's own lift
(+16.4pp → +15.9pp); only removing the shared anchor (`collapsed_relative` → the new t0-anchored
label) collapses it (to −22.5pp / +6.7pp). The mechanical coupling, not market drift, is the
operative defect. A follow-up (`docs/phase8b_clean_label_features.md`) re-ran Phase 6's own
feature analysis under the clean label and found the classifier's core momentum input
(`return_20d_context_only`) reverses sign on real 2026 hold-out data.

**Re-verification.** All numbers reproducible from `scripts/phase8_robustness_relabel_t0.py`,
`scripts/phase8_robustness_check1_rescoring.py`, `scripts/phase8_robustness_check1_skillscore.py`,
`scripts/phase8_robustness_check1_direction.py`, `scripts/phase8b_feature_reauc.py`, and
`scripts/phase8b_momentum_flagrate_check.py` — real output pasted in `docs/phase8_robustness_checks.md`
and `docs/phase8b_clean_label_features.md`, not re-typed from memory. RESULTS.md updated to lead
with this finding rather than the original Layer 3 headline.

## P8-003 — production report text and the manipulation-lint both fell behind, found by Phase 9's audit

**Root cause, two independent parts.**

**(1) Stale ceiling figure in live report output.** `src/classification/event_classifier.py`'s
`PROVENANCE_NOTE` (module-level, rendered into every report's narrative) and
`DISCRIMINATIVE_POWER_NOTE` (rendered standalone next to every classification) both hardcode "Phase
6 measured the combined signal ceiling at 0.611-0.70 held out on 2025-2026 data." `P8-001`'s
correction withdrew that exact figure — its two dominant features (`return_20d_context_only`,
`close_to_close_60d`) reverse sign on real 2026 hold-out data once scored against a decoupled label
(`docs/phase8b_clean_label_features.md` item 3). These constants were never updated when the
correction was made, so every report this system generates continues to cite a number this
project's own documentation no longer stands behind.

**(2) `banned_terms.py` (CLAUDE.md invariant 12's mechanical enforcement) has real, evidenced
coverage gaps.** An adversarial pass (`docs/phase9_hygiene_review.md` §1) ran 11 hand-written,
LLM-plausible phrasings through `lint_text()` directly and found **11 of 11 missed**: manipulation-
adjacent vocabulary outside the fixed `DIRECT_TERMS` list ("insider trading," "circular trading,"
"artificially inflated," "orchestrated," "coordinated operation," "synthetic [volume]"), bare
"suspicious" with no score/rank word nearby to trigger `RANKING_PATTERNS`, and invariant 12's entire
buy/sell/hold/target-price clause, which has no detector family assigned to it at all. **This is not
a new discovery in isolation** — `tests/test_banned_terms_adversarial_evasion.py`, already in this
project's suite since Phase 7c, independently measured a 0/5 catch rate on a differently-authored
set of deliberate evasions and reported it honestly ("a low number here is the honest finding, not a
bug to paper over," `docs/phase7c_agent_layer.md`). This pass's 11/11 (a set of mundane,
LLM-plausible phrasings, not deliberately engineered to evade the regex the way the Phase 7c set
was) corroborates that finding from a second, independent angle rather than duplicating it.

**How it was found.** Phase 9's adversarial lint pass and register-currency check, run as their own
exercise rather than incidentally — the module's own docstring already stated it expects false
negatives and does not assume 100% coverage; this is that check, actually run, with real output.

**Fix.**

**(1) Applied.** `PROVENANCE_NOTE` and `DISCRIMINATIVE_POWER_NOTE` now cite `P8-001` and state the
corrected finding (no top-tier precision lift over base rate; aggregate Brier Skill Score ~1.8% vs.
a constant baseline) instead of the withdrawn ceiling. A stale citation in `synthesis.py`'s
docstring (a `tests/test_orchestrator_determinism.py` file that does not exist — the real test is
`OrchestratorDeterminismTest` in `tests/test_orchestrator.py`) was corrected alongside it, found
while re-verifying this fix. Two tests that hardcoded the withdrawn `"0.611"` string
(`tests/test_synthesis.py`, `tests/test_orchestrator.py`) were updated to assert its ABSENCE and
the presence of the `"P8-001"` citation instead, so a future accidental revert is caught rather than
silently passing.

**(2) Resolved architecturally, per explicit decision — NOT by patching `banned_terms.py` toward
more coverage.** A vocabulary list losing to paraphrase twice, independently, is exactly the pattern
this project's own register (P4-012/P4-013) has previously treated as "the detection shape itself
is wrong, not merely incomplete." Rather than add more patterns, confirmed directly (grep across
all of `src/`) that **zero LLM-provider-calling code exists anywhere in this codebase** — every
`EvidenceClaim.text` is a deterministic template (`src/agent/specialists.py`), and `synthesis.py`
never calls a provider. `CLAUDE.md` now states this as standing policy (invariant 2's "LLM
narrative scope" note): any future LLM-narrative capability must be local/dev-only and must never
reach shareable output — that is what enforces invariant 12's buy/sell/hold/target clause, not
`banned_terms.py`. The lint itself is UNCHANGED — kept as a backstop, both its 0/5 (Phase 7c) and
0/11 (Phase 9) catch rates recorded plainly beside it, neither hidden nor treated as the primary
control.

**Re-verification.** Full suite re-run after both fixes: `python -m unittest discover -s tests`,
**326/326 tests pass**, including the two updated assertions
(`test_discriminative_power_note_is_attached_unconditionally`,
`test_discriminative_power_note_present_on_every_report`) and the pre-existing
`AdversarialEvasionCatchRateTest`/`test_report_is_banned_term_clean` suites, unchanged and still
passing. Full real test output: `docs/phase9_hygiene_review.md`.

(An earlier draft of this entry's re-verification paragraph said "pending the fix" and described
re-running the 11 phrasings against a patched lint — stale as soon as (2) above was resolved
architecturally instead of by patching, since no patch to `banned_terms.py` was ever going to be
applied. Removed rather than left contradicting the paragraph directly above it — caught while
adding `P8-004`/`P8-005` below, itself a small instance of exactly the register-consistency check
this phase exists to run.)

## P8-004 — `fetch_circular_index` never unwrapped the real API's envelope, crashed on its first live call

**Root cause.** `src/ingestion/nse_market_data/asm.py` and `.../gsm.py` each define their own
`fetch_circular_index(session, from_date, to_date) -> list[dict]`, both calling
`session.get("https://www.nseindia.com/api/circulars", ...)` and returning `r.json()` directly.
The real, live response from this endpoint is an envelope — `{"data": [...circulars...],
"fromDate": "...", "toDate": "..."}` — not a bare list. `fetch_and_ingest_asm_range`/
`fetch_and_ingest_gsm_range` both do `for c in circulars: subject = c.get("sub", "") or ""`;
iterating the un-unwrapped envelope dict yields its own three keys (`"data"`, `"fromDate"`,
`"toDate"`, each a plain string) instead of circular dicts, so the very first iteration crashed:
`AttributeError: 'str' object has no attribute 'get'`.

**How it was found.** Writing `scripts/weekly_ingest.py` (this phase's item 2) and actually running
it end to end, rather than only reading the code. Both functions' own docstrings already said "Not
called by the fixture-based test suite" — confirmed directly (`grep fetch_circular_index tests/`
returns nothing before this fix) that neither function had ever been exercised against real, or
even realistically-shaped, data anywhere in this project's history. `scripts/ingest_asm_gsm_sample.py`
(the only prior caller of the underlying parse/ingest functions) sourced its circular list from a
pre-fetched, already-unwrapped cache file, not from `fetch_circular_index` itself, so it never
exercised this code path either.

**Fix.** Both `fetch_circular_index` functions now return `r.json()["data"]`. Verified directly
against the real, live endpoint (not assumed from the traceback alone): a real call for a real
10-day window in 2026-09 returned 26 real circulars, correct dict shape, `sub`/`circNumber`/
`cirDate`/`circFilelink` all present as expected by the calling code.

**Re-verification.** Two new regression tests (`tests/test_asm_gsm_ingestion.py::FetchCircularIndexEnvelopeTest`),
mocking a session whose `.json()` returns the real observed envelope shape (trimmed to 2 of the 26
real circulars) — both `test_asm_fetch_circular_index_unwraps_data_key` and
`test_gsm_fetch_circular_index_unwraps_data_key` pass. Full suite re-run after the fix: **328/328
pass** (326 + these 2 new tests). A second real, live end-to-end run of `scripts/weekly_ingest.py`
after the fix completed with `asm_gsm=OK` (previously `ERROR`) — real confirmation, not inference
from the traceback alone.

## P8-005 — `weekly_ingest.py`'s own GAP detection matched an unconditional summary line

**Root cause.** `scripts/weekly_ingest.py`'s `_extract_gaps_and_mismatches` matched any captured
output line whose stripped text started with `"GAP "`. `scripts/ingest_bhavcopy_full_history.py`
prints TWO different lines beginning with that exact prefix: a per-date line only printed when a
real gap occurred (`"GAP 2026-09-16: <reason>"`), and an unconditional summary line printed on
EVERY run regardless of outcome (`"GAP (confirmed trading day, this request failed): 0"`). The
bare-prefix match could not tell them apart, so the summary line was counted as a real gap on every
single run — a script meant to surface real problems in an unattended weekly log would have logged
a false "GAP" every week, including clean weeks with zero real gaps, which is exactly the kind of
false-positive that trains a human to stop reading the log.

**How it was found.** The very first real end-to-end run of `scripts/weekly_ingest.py`
(alongside `P8-004`, in the same run) reported `GAPs: 1` — investigated directly rather than
accepted, since 1 unexplained gap on a run expected to be clean (recent, already-mostly-ingested
dates) was itself suspicious; the "gap" turned out to be the summary line, count zero, not a real
failure.

**Fix.** The match is now anchored on a trailing date (`^GAP \d{4}-\d{2}-\d{2}:`,
`_GAP_LINE_RE`), matching only real per-date gap lines and never the unconditional summary line.

**Re-verification.** A second real, live end-to-end run of `scripts/weekly_ingest.py` after both
this fix and `P8-004`'s reported `GAPs: 0` (started 2026-09-22T17:17:03, finished 17:42:13,
`overall=OK`) — the false positive is gone on a real run with no real gaps, not merely reasoned
about.

## P8-006 — three historical ingestion scripts could not survive a fresh clone

**Root cause.** `scripts/ingest_asm_gsm_sample.py`, `scripts/retry_asm_gsm_failures.py`, and
`scripts/ingest_corporate_actions_sample.py` each hardcoded a `Path(r"C:\Users\VICTUS\AppData\
Local\Temp\claude\d--Agentic-ai-project\693aa27b-1dbb-463f-b783-329123a86aff\scratchpad\...")` as
their sole source of the data they ingest — a SURV circular index (7,936 rows), a prior run's
failure-list report, and cached corporate-actions/announcements JSON, respectively. This directory
belongs to a Claude session that ended before this one started. It happened to still exist on disk
when checked (Windows had not yet cleaned it up), but nothing about that is guaranteed, and it does
not exist at all on a fresh clone of this repository — directly contradicting `README.md`'s own
"Setup" section, which says "running the ingestion scripts under `scripts/` builds it from scratch"
with no caveat that three of them silently cannot. `ingest_asm_gsm_sample.py` additionally
duplicated `fetch_and_ingest_{asm,gsm}_range`'s sweep logic in its own `run_asm`/`run_gsm`
functions — a second, independent implementation of the same thing (CLAUDE.md invariant 1: "never
create a parallel implementation").

**How it was found.** Flagged directly after `P8-004` (this same session): fixing
`fetch_circular_index`'s envelope bug for `weekly_ingest.py` prompted the question of whether the
ORIGINAL historical ingestion path had the same shape of fragility. It did, in a different form —
not a live-call crash, but a call that was never live at all.

**Fix.** All three scripts now delegate to the live-network function each domain already has,
removing the scratchpad dependency and (for the ASM/GSM sample script) the duplicated sweep logic
in the same change:
- `ingest_asm_gsm_sample.py` → `fetch_and_ingest_asm_range`/`fetch_and_ingest_gsm_range` directly
  (the same functions `P8-004` fixed and `weekly_ingest.py` already uses live), for the full
  2019-10-01 (ASM) / 2025-01-01 (GSM) historical range through today. Its own output report now
  writes to `data/raw/asm_gsm_ingestion_report.json` (gitignored, stable across sessions), not the
  scratchpad.
- `retry_asm_gsm_failures.py` → the same live `fetch_circular_index` for its lookup index, and
  reads/writes its failure-list reports from/to the same `data/raw/` location instead of the
  scratchpad. Its own backoff/transient-retry logic (real, not duplicated elsewhere) is unchanged.
- `ingest_corporate_actions_sample.py` → `fetch_all(year_from, year_to)` directly, which already
  returns `announcements_by_key` in the exact shape `ingest_corporate_actions()` needs — the old
  `rekey_announcements()` bridging function is no longer needed and was removed, not merely
  bypassed.

`git grep` for the literal temp-directory path prefix (`C:\\Users\\VICTUS\\AppData\\Local\\Temp`)
across all of `scripts/` now returns zero matches — confirmed directly, not assumed from having
fixed the three files known about going in.

**Re-verification, stated precisely by what was and was not actually run:**
- **Circular-index full-range fetch: live-verified.** A real call to `fetch_circular_index` for
  the full 2019-10-01..2026-09-15 range returned 7,945 circulars in 0.8 seconds — no pagination
  gap, no chunking needed. Compared directly against the old (still-present) scratchpad cache
  (7,936 rows): every one of the old cache's circular numbers is present in the live fetch (0
  missing); the live fetch has exactly 9 more, 6 explained by circulars published after the old
  cache was captured and 3 unexplained by recency alone (not investigated further — noted, not
  glossed over). The live fetch is a strict superset of the old cache. Full numbers:
  `docs/phase10_housekeeping2.md`.
- **`fetch_and_ingest_{asm,gsm}_range` (what `ingest_asm_gsm_sample.py` now calls): already
  live-verified this session**, via `weekly_ingest.py`'s own successful second run (`P8-004`'s
  re-verification) — the identical functions, a shorter date range. Not re-run at full 7-year
  historical scale in this pass: the store already holds that history from the original ingestion,
  so a full re-run would mostly re-discover duplicates already known to be handled correctly
  (`write_facts`'s own duplicate-business-key skip, exercised directly by
  `tests/test_asm_gsm_ingestion.py::IngestAsmCircularTest::test_reingesting_the_same_circular_is_idempotent`),
  at the cost of thousands of redundant network calls for no new information.
- **`fetch_corporate_actions_year`: spot-checked live** (2026, 1,819 real rows, correct bare-list
  shape — no envelope problem the way the SURV circulars endpoint had). **The full `fetch_all()`
  sweep — 7 years plus one announcement-window fetch per distinct (symbol, ex_date) pair,
  potentially thousands of calls — was NOT run end to end.** Stated in the script's own docstring:
  DOCUMENTED, NOT VERIFIED at full historical scale.
- **`retry_asm_gsm_failures.py`: syntax/import-verified only.** Not run live — there is currently
  no failure-list report at `data/raw/asm_gsm_ingestion_report.json` to retry against, because
  nothing has failed. Nothing to falsely claim was tested.
- All three scripts: `python -m py_compile` and a real `importlib` load (not just a syntax check)
  confirm each still defines and can execute `main()`.

## P8-007 — ETF unit splits are entirely uncaptured by corporate-actions ingestion

**Root cause.** `src/ingestion/nse_market_data/corporate_actions.py`'s live fetch
(`fetch_corporate_actions_year`/`fetch_recent`, both hitting `nseindia.com/api/corporates-
corporateActions`) and its subject-ratio parser were built and validated against equity BONUS/SPLIT
actions. Real ETF unit splits — a routine AMC practice to keep an ETF's per-unit NAV in a
retail-friendly range — either are not returned by this endpoint at all, or are returned in a shape
`parse_subject_ratio` does not recognize; either way, zero rows for this action type exist anywhere
in `corporate_actions`.

**How it was found.** `docs/phase10_preregistration_amendment3.md`'s pre-specified split/bonus
shape scan (`scripts/phase10_scan_split_bonus_shapes.py`), run as a mechanism check against the
EXISTING historical catalogue (not the still-nonexistent forward window, and inspecting prices, not
outcomes) rather than assumed to be forward-only. 96 events matched a common split/bonus shape
within 2 percentage points; **zero** had a corresponding `corporate_actions` row. Traced one
directly to raw `bhavcopy`, not left at the statistical shape alone: `HDFCNIFETF`, `series='EQ'`
(so not a series-scoping gap), close 1628.18 -> 162.44 from 2021-02-16 to 2021-02-17 — exactly a
10:1 ratio. A large share of the 96 hits are ETFs clustering on shared dates near-exact ratios
(`HDFCLOWVOL`/`HDFCMID150`/`HDFCMOMENT`/`HDFCNEXT50`/`HDFCNIF100`/`HDFCNIFBAN`/`HDFCNIFETF`/
`HDFCNIFIT`/`HDFCPVTBAN`/`HDFCSENETF`/`HDFCSENSEX` all near -90% on 2023-10-20 or 2024-02-02 alone)
— a pattern far too coordinated to be coincidental genuine price moves.

**Why this matters beyond the forward window this amendment is actually about:** this is the exact
false-positive shape `CLAUDE.md`'s own "Hard blocker — adjusted price series does not exist yet"
section already warns about in the abstract ("a 1-for-1 bonus looks like a ~50% overnight crash on
unadjusted closes... precisely the shape of false positive this project exists to distinguish from
a genuine manipulation-consistent signature") — happening for real, today, in the ALREADY-BUILT
historical event catalogue, for an entire instrument class (ETFs) nobody had previously checked for
this specific gap.

**Fix.** **Not applied.** Determining how many of the 96 (or of the wider ~75,300-event catalogue)
are ETF splits vs. genuine equity actions this project's parser still misses vs. real large moves
requires per-hit investigation this pass did not do at scale (one was traced fully; 95 were not).
Building real ETF corporate-action ingestion requires first identifying what NSE/AMC disclosure
path actually carries this information, since the standard equity endpoint apparently doesn't (or
doesn't in a recognized shape) — genuine new development, not a config or parser tweak, and out of
scope for this pass. A scoping question this raises but does not answer: whether ETFs belong in
this project's catalogue at all, given the project's actual purpose (equity manipulation forensics)
— filtering them out may be more appropriate than adjusting for their splits, but that is a decision
for the project owner, not assumed here.

**Re-verification.** N/A — nothing was fixed. The scan script and its full, real 96-event output
are the evidence trail: `scripts/phase10_scan_split_bonus_shapes.py`,
`docs/phase10_housekeeping3.md`.

**Closure, 2026-10-04 (user decision: verify the mitigation, then close with a residual-risk note).**
**Status.** Closed — mitigated, not fixed at source.
Verification is computed, read-only (both stores opened `mode=ro`), by
`scripts/desk_p8007_verification.py` with its decision rule fixed in the script before the first
run; output `docs/desk/p8007_verification.json` (catalogue SHA-256 `ab6dbe70…`, ISIN map
`2b33925b…`). As of 2026-10-04: the final catalogue's 70,638 events cover 2,549 symbols, all
equity (zero fund-unit, zero unresolved); the Desk opportunity log's 456 symbols are all equity;
on the latest session (2026-10-01) 349 of 2,662 EQ-series symbols are fund units and every one is
excluded; the pre-specified shape scan (7 ratios, 2 pp, ±10 days) finds zero fund-unit hits.
Mechanisms: the equity-only rule in `scripts/build_final_event_catalogue.py`, the identity
exclusions in `desk/scan.py`, and the replay's abort on any fund or unresolved symbol. An ETF unit
split therefore cannot reach a catalogued event, a Desk screen, a replay or a paper trade.

Residual risks: (1) ETF unit splits are still not ingested; any future use of fund units
reopens this. (2) `build_final_event_catalogue.py` skips the equity-only filter when the ISIN map
file is missing (fail-open; the pinned build was verified above to contain no fund units, and the
Desk scan and replay fail closed). (3) 43 equity one-day moves within 2 pp of a split/bonus ratio
have no corporate action in the store as of today (2020: 8, 2021: 5, 2022: 6, 2023: 4, 2024: 9,
2025: 8, 2026: 3; listed in the JSON). Several are known genuine crashes (e.g. IDEA 2020-03-18,
ZEEL 2024-01-23), but some deep drops (GODHA 2022-06-21 −88.8%, KARDA 2021-09-13 −90.9%, RNBDENIMS
2026-05-19 −82.2%) could be equity actions NSE's endpoint never carried. That is equity
corporate-action coverage (P8-008 territory), not ETF splits: an unrecorded split would read as a
crash in research labels and as a false stop in paper trading.

## P8-009 — `price_adjustment.py`'s `UNADJUSTABLE_ACTION_TYPES` missed `RIGHTS`/`RATIO_CONFLICT`

**Root cause.** `src/signals/event_catalogue.py`'s module docstring documents
`STRUCTURAL_BREAK_ACTION_TYPES` as a deliberate, hand-mirrored copy of
`src/signals/price_adjustment.py`'s `UNADJUSTABLE_ACTION_TYPES` — the former drives a fast,
vectorized catalogue-build path; the latter drives a slower, per-`(price_date, as_of)`-pair,
`latest_as_of`-verified path used directly by `compute_adjustment_factor`/`adjusted_close`. The
two are genuinely separate Python tuples in separate modules, kept in sync by hand, not by a
shared import. `P8-007` corrections' item 2 (write `RIGHTS`/`RATIO_CONFLICT` as structural-break
exclusion markers instead of dropping/miscounting them) updated `STRUCTURAL_BREAK_ACTION_TYPES`
but not `UNADJUSTABLE_ACTION_TYPES`.

**Effect of the gap.** A `RIGHTS` or `RATIO_CONFLICT` row falling inside a
`compute_adjustment_factor` window would silently fall through both the `UNADJUSTABLE_ACTION_TYPES`
check and the `(BONUS, SPLIT)` factor-multiplication check, leaving the cumulative factor
unchanged and raising nothing — not a wrong multiplicative factor, but a silent skip of the exact
fail-closed exclusion item 2 exists to guarantee, specific to this module's slower path. Currently
inert against real data: no `RIGHTS`/`RATIO_CONFLICT` row exists in production, and nothing calls
`compute_adjustment_factor` against the new staging sweep this session.

**How it was found.** Caught while independently verifying item 2's own fix before committing it
— re-reading every consumer of the old `(DEMERGER, CAPITAL_REDUCTION)` pairing to confirm the fix
was complete, rather than assuming `event_catalogue.py`'s update was sufficient on its own.

**Fix.** `UNADJUSTABLE_ACTION_TYPES` now includes `RIGHTS` and `RATIO_CONFLICT`, with a comment
explaining why the duplication exists and warning that the two lists must be kept in sync by hand.

**Re-verification.** Tests added: `RightsAndRatioConflictUnadjustableTest`
(`tests/test_price_adjustment.py`, mirroring the existing `DemergerUnadjustableTest` pattern —
in-range raises `UnadjustableWindowError` for both new types, out-of-range does not raise) and two
new tests in `tests/test_event_catalogue.py`
(`test_rights_window_excluded_same_as_demerger`, `test_ratio_conflict_window_excluded_same_as_demerger`,
mirroring `test_capital_reduction_window_excluded_same_as_demerger` — this file had zero
`RIGHTS`/`RATIO_CONFLICT` coverage before this change). Full suite re-run: **338/338 pass.**
Committed separately from the original item 2/3 fix, as its own commit (`59d1dbf`).

## P8-010 — a live corporate-actions feed reports a security's CURRENT symbol, not the symbol in effect on each historical date

**Root cause.** `HEG` and `HEGAM` are the same security (ISIN `INE545A01024`) under two different
ticker strings. `HEG` renamed its own ticker to `HEGAM`, confirmed directly:
- `HEG`'s own raw bhavcopy close falls 2570.40 (2024-10-17) → 496.35 (2024-10-18), a 5.18x drop —
  matching the 10:2 (5x) split ratio recorded, under `HEG`, in production's `corporate_actions`.
- `HEG`'s own raw bhavcopy close falls 728.25 (2026-09-04) → 272.20 (2026-09-07), a real ~62.6%
  drop consistent with the demerger recorded, under `HEG`, in production's `corporate_actions`.
- `HEG` has 1,726 bhavcopy rows, 2019-10-01 through 2026-09-21 (its last day under that ticker).
  `HEGAM` has exactly one bhavcopy row, dated 2026-09-22 — the very next trading day.

NSE's live `corporates-corporateActions` endpoint, queried today (2026-09-23, after the rename),
returns this ISIN's ENTIRE disclosure history — back to a 2019 buyback — under the CURRENT symbol
string `HEGAM`, regardless of what ticker was actually in effect on each historical date. This
project's own bhavcopy ingestion, by contrast, correctly preserves the ticker as traded on that
specific date, so `HEG`'s 1,726 rows of real price history remain filed under `HEG`. This
project's `corporate_actions`↔`bhavcopy` join (`compute_adjustment_factor`, `build_symbol_history`)
is symbol-string-based throughout — it has no ISIN-based identity-resolution step anywhere.

**How it was found.** `P8-007` corrections item 1's full-sweep-vs-production diff
(`scripts/phase10_p8007_sweep_diff.py`) flagged `HEG`'s `SPLIT`/`DEMERGER` rows as "present in
ours, absent live" — a 2-row bucket the diff script's automatic cause-classification does not
attempt to explain further (it only classifies the "present live, absent from ours" side). Traced
by hand rather than left as an unexplained stale-cache guess, since the user's instruction was to
report every difference "grouped by cause," not merely counted.

**Why this matters beyond these 2 rows.** A future correction that naively "fixes" these 2 rows by
trusting the live feed's current-symbol field (writing them as `HEGAM` instead of `HEG`, or simply
deleting the `HEG`-labeled rows in favor of promoting the live sweep's `HEGAM`-labeled ones) would
silently orphan `HEG`'s real split/demerger from all 1,726 days of correctly-`HEG`-labeled price
history — the 60-session exclusion window and the adjustment factor would simply stop applying to
the series they exist to protect. The OLD stale cache happened to get this one case right, purely
because it was fetched before the rename took effect. This is a real, general structural gap
(nothing about `corporate_actions`/`bhavcopy` ties a row to a security by ISIN — only by whatever
symbol string a given source happened to report it under at fetch time), not specific to `HEG`.

**Fix (Amendment 4 prep, `docs/phase10_amendment4_prep.md`).** Not applied in the P8-007
corrections session (explicitly out of scope there: "no change to the production
`corporate_actions` table or any derived table") -- applied here instead. `src/ingestion/
nse_market_data/isin_mapping.py` (new module: `fetch_isin_snapshot`, `merge_isin_snapshots`,
`build_symbol_groups`, `load_isin_map`) plus `resolve_isin_symbol`/
`build_isin_candidates_for_actions` in `corporate_actions.py` resolve a raw action's reported
symbol to whichever same-ISIN symbol was actually trading on its ex_date, using the action's own
`isin` field (present in NSE's raw response) and this project's own bhavcopy date ranges.
`ingest_corporate_actions` gains an optional `isin_map` parameter (default `None` -- fully
backward compatible). `weekly_ingest.py`'s corporate-actions step now loads the map when present.

Fixing action IDENTITY does not by itself stitch PRICE history across a rename, so a second,
related fix: `build_symbol_history` (`src/signals/event_catalogue.py`) gains an optional
`symbol_group` parameter that merges every same-ISIN symbol's bhavcopy rows and corporate actions
into one continuous history -- wired into the full catalogue/label rebuild pipeline (`build_final_
event_catalogue.py`, `compute_clustering.py`, `build_event_classifications.py`, `compute_outcome_
labels.py`, `phase8_robustness_relabel_t0.py`). Measured necessary, not assumed: renames were
found to cause a missing 90-session outcome for ~0.52-0.54% of fully-elapsed catalogued events
(`docs/phase10_amendment4_prep.md` item 3) -- just over the 0.5% bar set in advance for doing this.

Applying this ALSO revealed the true scope was never just `HEG`/`HEGAM`: inverting the ISIN map
found **195 ISINs mapping to more than one symbol** across this project's full universe. 19 of
those have at least one corporate action whose ex-date falls inside a sibling symbol's own trading
window (26 such "orphaned" actions total) -- 4 of them (`COSMOFILMS`/`COSMOFIRST`,
`INFIBEAM`/`CCAVENUE`, `MINDAIND`/`UNOMINDA`, `NXTDIGITAL`/`NDLVENTURE`) directly explain 4 of the
P8-007 corrections' 52 persisting "unexplained" split/bonus shape-scan hits once checked against
the sibling symbol's own action history, not just the event's own catalogued symbol.

**Re-verification.** Promoted into production for real (`scripts/phase10_amendment4_promote_
corporate_actions.py`, backed up first): `corporate_actions` 702 -> 974 rows. Confirmed directly:
`HEG`'s real 2024-10-18 split is now correctly filed under `HEG` (previously would have written
`HEGAM`, orphaning it from `HEG`'s own 1,726-row price history, exactly the risk this entry
originally warned about). Full suite re-run after all Amendment 4 prep code changes: 362/362 pass.
A related, smaller gap found while spot-checking this promotion is logged separately as `P8-011`
(the announcement cross-check fetch itself is not yet ISIN-aware, unlike the row-write path).

## P8-011 — the announcement cross-check fetch is not ISIN-aware, unlike the row-write path

**Root cause.** `P8-010`'s fix resolves a raw action's SYMBOL correctly at the point of writing a
row (`resolve_isin_symbol`), but an EARLIER pipeline step -- `_fetch_announcements_for_actions`,
which queries NSE's corporate-ANNOUNCEMENTS endpoint to cross-check a bonus/split's ratio and find
a real announcement date -- still queries using the action's raw, as-reported symbol (`HEGAM` for
a pre-rename `HEG` action). The announcements endpoint is a DIFFERENT NSE endpoint from
corporate-actions and may not carry the same historical record under a post-rename symbol.

**How it was found.** Spot-checking the real production promotion (`P8-010`'s fix applied for
real): `HEG`'s 2024-10-18 split's ratio (`10.0:2.0`) is written correctly (`resolve_isin_symbol`
worked), but its confidence_tier downgraded to `EX_DATE_FALLBACK` in the newly-added vintage,
versus the OLD pre-rename cache's `MATCHED_UNCONFIRMED` -- meaning the announcement search, run
under `HEGAM`, did not find the same real announcement text a pre-rename-era search (under `HEG`)
once did.

**Impact, measured precisely, not assumed.** The ratio is identical in both vintages
(`10.0:2.0`) -- `compute_adjustment_factor`'s output is unaffected either way, confirmed directly.
Only the confidence_tier metadata for this ONE row (of 974 in the post-promotion table) is less
precise than it could be. `latest_as_of` currently resolves to the NEWER, EX_DATE_FALLBACK vintage
for any `as_of` on or after 2024-10-18 (the opposite direction from the `PFC` case, where the
OLDER row wins) -- reported alongside `PFC`'s case in `docs/phase10_amendment4_prep.md` as the
same underlying "two coexisting vintages, append-only" phenomenon.

**Fix.** **Not applied.** Low severity, single row observed affected, zero adjustment-factor
impact. Extending `resolve_isin_symbol`-style resolution to `_fetch_announcements_for_actions`
(so the announcement search itself uses the historically-correct symbol, not just the final
written row) is a real, scoped follow-up, deferred to a future session.

**Re-verification.** N/A — nothing was fixed. Evidence trail: `docs/phase10_amendment4_prep.md`,
`scripts/phase10_amendment4_promote_corporate_actions.py`'s own spot-check output.

## P8-012 — `build_symbol_history`'s EQ-only default silently treats a trade-for-trade move as delisting

**Root cause.** `build_symbol_history` (`src/signals/event_catalogue.py`) reads bhavcopy filtered
to `series="EQ"` by default. A stock placed under trade-for-trade settlement (`BE`/`BZ` series) --
a routine NSE surveillance mechanism, and disproportionately applied to exactly the volatile,
flagged stocks this project's classifier analyzes -- leaves the EQ series entirely while
continuing to trade. Its EQ `trading_days` list therefore stops abruptly at the series-change
date, indistinguishable from a genuine delisting to any forward-looking label computation.

**How it was found.** Diagnosing HOLD-OUT's elevated missing-outcome rate (Amendment 4 prep round
2, `docs/phase10_amendment4_prep2.md`): after confirming a boundary-proximity artifact explained
part of the gap, checked directly whether affected symbols continued trading under a different
series. 31.93% of HOLD-OUT's fully-elapsed-missing events had `BE`/`BZ` rows dated after their own
last EQ row. Cross-checked against TRAIN's own historical population for the same measurement:
28.64% -- nearly identical, confirming this is a constant, previously-unnoticed background rate
this project's ingestion has had since its earliest bhavcopy work (Phase 2), not a 2026 anomaly.

**Fix.** `build_symbol_history` gains an optional `extend_with_series: tuple[str, ...] = ()`
parameter (default identical to before -- fully backward compatible). Given a non-empty tuple,
rows from those additional series, STRICTLY AFTER the primary series' own last date, are appended
for continuity. Deliberately narrow: rows inside any OVERLAP period between EQ and the extension
series (observed in real data -- a BE-designated lot can trade concurrently with EQ for the same
company) are never merged, avoiding an ambiguous, potentially-wrong price splice. Wired into
`compute_outcome_labels.py` and `phase8_robustness_relabel_t0.py` with `("BE", "BZ")` -- labels
only; `build_final_event_catalogue.py` (the event catalogue itself) stays EQ-only, unchanged, per
explicit instruction ("the catalogue stays EQ-based").

**Re-verification.** Tests: `ExtendWithSeriesTest` (`tests/test_event_catalogue.py`, 4 cases --
no-op default, real continuation through BE, the overlap-period exclusion, and a bonus-during-
extension adjustment check). Real-data effect, measured by rebuilding both label artifacts:
HOLD-OUT's `possible_delisting_or_suspension` count dropped from 709 to 495 (214 events recovered,
matching the measured ~30% series-move share almost exactly) -- and to 368 once `P8-013`'s
global-horizon redefinition was layered on top. Full suite: 366/366 pass after this change.

## P8-013 — the outcome label's own-session horizon creates feature-correlated missingness

**Root cause.** The pre-registered `relative_t0_primary` label (Amendment 1 §1) required the
security's own 90th REAL EQ trading session after `event_date` to exist before an outcome could be
computed. A thinly-traded security needs more CALENDAR time than a heavily-traded one to
accumulate 90 real sessions -- meaning WHICH events have a computable outcome at all is correlated
with trading density, and trading density is itself correlated with `cap_band`, `volume_ratio`,
and other of this project's own model inputs. This is a textbook non-random-missingness problem:
excluding these events as "no outcome" silently biases any evaluation toward the subset of events
that happened to occur in liquid names, or with enough elapsed calendar time to catch up.

**How it was found.** `P8-011`/`P8-012`'s diagnosis of HOLD-OUT's elevated missing-outcome rate
found two mechanisms (boundary proximity, series moves) but left a residual gap between TRAIN and
HOLD-OUT unexplained. Amendment 4 prep round 3 attempted to fix the boundary-proximity mechanism
with a MEASURED timing buffer (a plateau in the missing-rate-by-buffer curve) and found no plateau
within 120 sessions (`docs/phase10_amendment4_prep3.md`) -- because a buffer cannot bound an
unbounded tail: `scripts/phase10_amendment4_selection_problem.py` then confirmed directly that the
missing-outcome rate under the OLD definition is a clean monotonic function of `cap_band` (TRAIN,
buffer>=30 sessions: Micro 2.09%, Small 1.84%, Mid 1.46%, Large 1.36%, Mega 1.20%), and that 5
spot-checked "missing" events in the worst-affected band all had large real gains (+31% to +59%)
once the artificial censoring was lifted -- proving these are not missing at random, and that no
amount of buffer-tuning was ever going to fix a problem rooted in the label's own definition.

**Fix.** `relative_t0_primary`'s horizon is redefined at a GLOBAL 90-session point (the market's
own calendar, `market_index.csv`, not the security's own trading days) -- the outcome uses the
security's LAST AVAILABLE close (EQ, extended through `BE`/`BZ` per `P8-012`) on or before that
global date, with the market index evaluated at that SAME observed date (never a later index level
the security had no chance to keep pace with -- verified against a synthetic case where using the
wrong index date would have produced 0.0 instead of the correct 1.0). A 10-session STALENESS CAP:
if the last available close is more than 10 global sessions stale relative to the target date, the
outcome is genuinely MISSING, not extrapolated across the gap. `scripts/phase8_robustness_
relabel_t0.py`'s `compute_t0_relative` implements this; the own-session definition is recorded as
superseded, not silently replaced.

**Re-verification.** Verified against hand-constructed synthetic cases before trusting it against
real data (no staleness, exact-zero-staleness boundary, beyond-cap missing, within-cap with the
index-date check). Real-data effect: old-vs-new label agreement is 98.73% overall, with a clean
monotonic gradient by cap_band (Micro 96.60% -> Small 98.28% -> Mid 99.09% -> Large 99.59% -> Mega
99.79%) -- confirming the redefinition changes exactly the population it should (thin names where
the two definitions can disagree), not everything indiscriminately. The refit and Phase 8b re-run
under the new label both show no conclusion changes from the pre-registration's own feature
inclusion/exclusion decisions. Full suite: 366/366 pass.

**Correction, added post-commit (Amendment 5, `docs/phase10_amendment5_prep.md`), per this
register's own practice of appending a correction rather than silently editing a settled entry:**
the "6.838% (TRAIN) vs. 6.661% (HOLD-OUT), a 0.176pp gap" figure originally reported here compared
this label's TRAIN and HOLD-OUT rates to EACH OTHER and correctly found them close -- but that
comparison alone does not establish the label's missingness is uncorrelated with model inputs, and
no such check was actually run before this entry asserted one. `P8-014` ran it and found the new
label's OWN missing-outcome rate was, in fact, a clean monotonic function of `cap_band` (a 14.1pp
Micro-minus-Mega gap) until `P8-012`'s own extension logic was corrected for a temporary
trade-for-trade stint. See `P8-014` for the root cause and fix; the FINAL, post-`P8-014` rate
(1.310% TRAIN / 0.897% HOLD-OUT, 0.413pp gap) is the one that should be cited going forward, not
the figure originally reported in this entry.

## P8-014 — `P8-012`'s series-extension fix was itself blind to a temporary trade-for-trade stint

**Root cause.** `build_symbol_history`'s original `extend_with_series` (`P8-012`) appended an
extension series' (`BE`/`BZ`) rows only STRICTLY AFTER the primary series' own LAST-EVER date --
correct for a PERMANENT series migration (a stock leaves EQ for BE/BZ and never returns), but blind
to a TEMPORARY stint (`EQ -> BE -> EQ`, the security resumes normal trading afterward). During such
a stint, the merged calendar had a GAP with no rows at all; a forward-looking target date landing
inside that gap resolved to a STALE pre-stint EQ close, and the 10-session staleness cap (`P8-013`)
correctly, but wrongly, flagged the outcome as missing -- the security had not gone dark, it was
trading under `BE`, just not visible to the code.

**How it was found.** `P8-013`'s own committed entry (above) claimed the redefined label's
missingness was resolved by the definition change alone -- a claim about OLD-vs-NEW label
agreement, not about whether the NEW label's own missingness correlates with model inputs, which
was never actually checked. Amendment 5 prep measured it directly
(`scripts/phase10_amendment5_measure.py`): TRAIN's missing-outcome rate under `P8-013` was 6.838%
(4.3x the rate before `P8-013`), and its `cap_band` gradient (Micro 16.0% down to Mega 1.9%, a
14.1pp spread) was WORSE than the own-session definition's own gradient (0.9pp) -- the fix that was
supposed to solve exactly this problem had, on this specific dimension, made it worse. Checked
directly, not guessed at: 92.37% of the TRAIN events missing due to the staleness cap had a real
`BE`/`BZ` close within the exact 10-session window the extension logic never looked at.

**Fix.** `extend_with_series` now bridges per date across the WHOLE calendar: a `covered_dates` set
tracks which dates the primary series (then each extension series, in the order given) already
fills, so a later series only contributes dates still missing -- regardless of whether those dates
fall before, during, or after the primary series' own range. The primary series always wins on any
date more than one series has a row for. Prototyped read-only first
(`scripts/phase10_amendment5_bridge_prototype.py`, no pipeline change) against the exact decision
rule Amendment 5 set in advance (TRAIN missing rate must fall by >=1.0pp AND the Micro-minus-Mega
gap must narrow) before implementing it for real.

**Re-verification.** Tests: `ExtendWithSeriesTest` gained `test_temporary_stint_bridged_not_just_
the_tail` (an EQ -> BE-only-stint -> EQ fixture, confirming all dates are bridged and a target date
landing inside the stint resolves to the real bridged close, not a stale pre-stint one) and
`test_same_date_conflict_primary_series_wins` (renamed from the equivalent pre-existing test,
same assertion, still passes under the new per-date-merge logic). Real-data effect, measured by
rebuilding the label: TRAIN missing rate 6.838% -> **1.310%**; Micro-minus-Mega gap 14.1pp ->
**0.214pp**; TRAIN/HOLD-OUT gap (the `P8-013` commit-rule check) 0.176pp -> 0.413pp, still
comfortably within the 2.0pp bar. Full suite: 367/367 pass. Full numbers:
`docs/phase10_amendment5_prep.md`.

## P8-015 — daily bhavcopy retry crashed before its first wait

**Root cause.** `scripts/weekly_ingest.py` called `time.sleep` when today's bhavcopy
was unavailable, but never imported `time`. A delayed publication therefore raised
`NameError` after the first fetch instead of using the configured retry budget.

**Fix.** Import `time`. Keep the existing attempt count and delay unchanged.

**Re-verification.** `tests/test_weekly_ingest_retry.py` exercises publication on
attempt three and exhaustion of all six attempts. Both patch `time.sleep`, check
the exact fetch and sleep calls, and verify the connection closes without an
exception. Targeted run: 2 tests passed. Full suite: `Ran 512 tests in 381.032s`,
`OK`. Pyflakes was not installed; no package was installed for this check.

## P8-016 — demo binding depended on launch directory; netstat false alarm

**Root cause.** The documented command relied on Streamlit discovering the repo's
`.streamlit/config.toml` from the current directory. The previous session also
misread Windows netstat's remote-address column (`0.0.0.0` on a listening socket)
as the local bind address, reporting network reachability despite the local
address being `127.0.0.1`. This incident description comes from the user's session
message; the earlier socket was not re-observed in this session.

**Fix.** `demo/run_demo.ps1` supplies `--server.address localhost` explicitly and
resolves the application path from `$PSScriptRoot`. `demo/DEMO.md` uses it.
Interpret listening scope from netstat's local-address column.

**Re-verification.** The launcher test executes PowerShell from a temporary folder
with a fake Python command and asserts the application path and localhost flag.
No server is launched by the test. The initial test failed with `PSSecurityException`
because this machine disables scripts. The test and documented command now use a
process-only execution-policy override, leaving machine policy unchanged.
Full suite: `Ran 513 tests in 240.705s`, `OK` (Python exit code 0).

## P8-017 — unavailable current ISIN snapshot aborted refresh; freshness was unrecorded

**Root cause.** Today's snapshot fetch was outside the historical-snapshot error
handling. A normal HTTP 404 aborted the step. The map had no build provenance,
so neither Desk status nor G1 could distinguish an old retained map from a refresh.
The script's docstring also incorrectly claimed it was not called by weekly ingest.

**Fix.** Today's 404 retains the existing map and companion with WARN; missing-map
and other HTTP failures remain ERROR. Ingestion reports OK/WARN/ERROR. Successful
builds write an offset-bearing build timestamp, SHA-256, and used snapshot dates.
The existing map has a one-time companion labelled as inferred from file mtime,
with unknown historical dates explicitly marked. Status shows trading-day age;
G1 fails above five days using the timestamp stored on the decision. Replay uses
only that stored value. Explicit ALTER migration checks row counts before/after;
the real database remained at 0 rows. See docs/OPERATIONS.md's operational note.

**Re-verification.** 12 operational tests passed, including 404 retention, other
HTTP failures, checksum integrity, used dates, health levels, five/six-day boundary,
duplicate-session handling, and a populated-table migration with unchanged rows.
The existing replay test now forbids current metadata reads during replay.
During implementation, the new keyword was initially placed before the positional
connection in four test calls, causing Python import errors. This agent-introduced
argument-order error was corrected before committing; it was not a sandbox failure.

**Handoff review (Claude Code, resuming the interrupted Codex session).** The uncommitted diff was
read in full against the approved plan rather than trusted. All changed files compiled; the four
calls were already valid keyword arguments when the session resumed. Verified directly: bhavcopy
`knowledge_date` is a plain date, so the age query's `knowledge_date <= as_of` comparison is
correct; the real Desk `decisions` table carries the column with 0 rows; the existing companion's
SHA-256 matches the map's bytes; jugaad requests the current UDiFF report first and falls back to
the legacy report only on failure, so today's 404 is "not yet published", not a permanently dead
endpoint. One change made: the five-day limit was duplicated in G1 and the status line; both now
read `shared.isin_map_metadata.MAX_AGE_TRADING_DAYS`. Known, accepted: an ISIN-age failure
returns before G1's other checks, so it can mask a coexisting data-gap reason.

Targeted tests: `Ran 30 tests`, `OK`. Full suite: `Ran 525 tests in 111.076s`, `OK` (Python
exit code 0).

## P8-028 - evaluator treated a matching exit reason as good process

**Root cause.** The evaluator classified process using only an exit-reason prefix.
It did not inspect the original entry thesis, overrides or rule violations.
**Fix.** Audit the linked thesis and decision as recorded before entry, detect
unlogged violations (including unlogged stop widening), reject any G7 override,
and require a prior recorded exit trigger or reasoned manual-close request.
Manual close and monitor now append explicit provenance before recording exits.
The evaluator checks the outcome firewall before fetching exit prices and closes
its database connection on every return. Existing journal rows are untouched.
**Verification.** Ten targeted tests pass, including incomplete/late thesis,
reason-only and late trigger failures, G7 decision/journal overrides, unlogged
violation and stop-widening detection, valid trigger and reasoned manual close.

## P8-030 - readiness test imported a discoverable TestCase as a fixture

See also P8-031/P8-032 below for the subsequent replay review.

**Root cause.** The initial readiness test imported ProcessQualityTest directly,
causing unittest to rediscover its ten methods and inflate the targeted count.
**Fix.** Import its module under a fixture alias instead; no duplicate TestCase
class is exposed to discovery in the readiness module.
**Verification.** Targeted readiness run now reports seven distinct tests, OK.
No production behavior or research result was affected.

## P8-031 - draft shadow replay did not implement the registered analysis

**Root cause.** The inherited runner used a process pool, security-session tails,
incorrect action-factor direction, incomplete stop-gap/locked-circuit logic and
no registered bootstrap comparisons. The earlier P8-026 edit in this review also
left its header syntactically invalid; a text-based test did not import it.
No full replay from that code was run in this review.
**Fix.** Replace it with a sequential runner on read-only temporary copies, the
unchanged Amendment 5 function, global-session adjusted tails, explicit missing
denominators, overlapping reason groups, and paired event-date bootstraps.
Add a runner import/parse test and adversarial path/uncertainty tests. Exact
SELECT caching and single-date statistic evaluation avoid unnecessary work;
neither changes the pinned calculation or as-of parameters.
**Verification.** Thirteen targeted replay tests pass (11.948s), including real
split/bonus and demerger statistic equivalence. Full-suite and full-run evidence
will be recorded in the handoff and results.

## P8-032 - G1 availability queries could see late-known rows

**Root cause.** Four direct bhavcopy availability queries bounded event dates
without bounding knowledge dates, contrary to the as-of contract.
**Fix.** Add the assessment-date knowledge cutoff to all four queries. Register
the repair in the dated shadow-replay addendum before full replay outcomes.
**Verification.** A late-known security row cannot satisfy G1 in the historical
assessment; included in the thirteen passing replay tests. Thresholds unchanged.

## P8-033 - profiler invocation exposed a relative runner source path

**Root cause.** The new runner assumed `__file__` was absolute when recording
source hashes. Python's cProfile entry point supplied a relative path; the
input-only profile stopped before any screening or outcome calculation.
**Fix.** Resolve the source path before taking its repository-relative name.
**Verification.** The cProfile input-only run completed 30 events. Subsequent
full suite: 609 tests in 282.945s, OK, including runner import and fourteen
replay checks. No outcome or stored fact was affected.

## P8-034 - ISIN refresh discarded historical identities and reversed precedence

**Root cause.** Refresh rebuilt solely from successful downloads, losing symbols
when a historical download failed. Today's snapshot was first in a last-wins
merge, so historical ISINs could overwrite current observations. A fresh build
timestamp did not imply complete or correctly ordered coverage. The pre-replay
audit found 57 catalogue events across ten unresolved symbols.
**Fix.** Retain the existing map as fallback, merge dated historical observations
in order and today's snapshot last. Recover missing identities using real NSE
snapshots; preserve the previous map and companion in scratch. Commit a recovery
audit and dated preregistration addendum. Replay refuses unresolved/fund events.
**Verification.** All 70,638 existing catalogue rows resolve as equity after
recovery; no catalogue event was removed. A regression test combines a missing
historical snapshot, retained delisted identity and reused-symbol conflict.

## P8-038 - passed decisions can already exceed per-trade risk including costs

**Root cause.** `compute_position_size` divides the per-trade budget by the
entry-stop distance without transaction costs. The subsequent `g6_risk` checks
stress against the open-risk budget and stock/sector capital, but does not check
planned loss including costs against the per-trade budget. The fill observer
does check that additional limit, so its breaches are not all caused by an
overnight price change.
**Evidence.** In the frozen replay, 12,693 of 45,700 filled primary PASS candidates
and 1,958 of 7,131 descriptive-2026 PASS candidates already breach the per-trade
cap at their decision price. No other decision cap is breached in those filled
PASS cohorts. Independent affine sizing bounds and direct measurements confirm
these counts. A synthetic reproduction with active v2/costs: entry 100, stop 90,
quantity 500, cap Rs 5,000; planned loss including costs Rs 5,121.39357, yet G6 PASS.
**Status at discovery (2026-10-04).** Open. No active sizing or gate was changed after inspecting outcomes.
The pre-registered research variant correctly includes costs and fits each cap
at 90%; its improvement therefore combines proper cost-aware decision sizing
with the registered headroom, not headroom alone. A production repair is a
separate task and must preserve the original result artifacts.
**Verification.** Frozen baseline fill flags match the original checks exactly.
All 52,831 original filled PASS quantities in the two periods were checked for
variant maximality and agreement with independent affine constraints. Full
counts and conditional excess distributions are in the follow-up results.

**Resolution, 2026-10-04.** Fixed in `7801550` after preregistration addenda
`cb89f96`: whole-share sizing uses the same cost-inclusive `planned_loss_inr`
as the gate, and G6 independently rejects any cost-inclusive per-trade excess.
Verified by the complete corrected replay (`ed81160`, 70,362 events, decision
cap assertion on every pass) and the old/new audit (`15024e9`): corrected
decision-time breaches are zero for all six caps in both periods (old: 12,695
primary / 1,958 descriptive per-trade); labels and adverse20 unchanged for
every event; quantities only decreased. Net +72 passes, all FAIL->PASS (71 G5
order-ADV, 1 G6 open-risk stress), because smaller quantities clear other
caps. **Status.** Fixed and verified 2026-10-04. At-fill breaches remain; see P8-043.

## P8-037 - rendering test confused provenance with a NaN value

**Root cause.** The new empty-group report test searched for the substring `nan`
anywhere in the text; it matched `provenance`, producing a false failure even
though every missing numeric result rendered as unavailable.
**Fix.** Check for the standalone case-insensitive NaN token instead.
**Verification.** The full suite, including the empty-group renderer and all
sixteen follow-up tests: 626 tests in 109.457s, OK, Python exit 0. No real follow-up was run before this
repair; statistics, data and the registered protocol were unchanged.

## P8-036 - mixed encoding made the scratch ignore rule ineffective

**Root cause.** Commit `7df208c` appended `scratch/` as a UTF-16 fragment to an
otherwise UTF-8 `.gitignore`, leaving ten NUL bytes. Git did not recognize the
rule, despite the old handoff claiming scratch was ignored. Round-2 repaired the
handoff encoding and Markdown line-ending policy but missed this file.
**Fix.** Replace only the malformed fragment with UTF-8 `scratch/` and LF.
All local scratch artifacts remain untouched; nothing is added to tracking.
**Verification.** Before the repair `git check-ignore scratch/proof_scan.py`
returned no match. Afterward it identifies `.gitignore:8:scratch/`; the file has
zero NUL bytes. Baseline suite: 610 tests, OK, exit 0. No research result changed.

## P8-035 - replay warnings needed statistic-specific denominators

**Root cause.** Pre-run report review found small-sample warnings used the whole
group count, which could conceal sparse valid observations for a particular
metric. Gates with zero rejected candidates were omitted from the tables.
**Fix.** Record valid-event and date-cluster counts and warnings per statistic;
include every G1-G6 group even when empty, with unavailable comparisons. Group
missing ATR-plan reasons consistently. No outcome definition or threshold changed.
**Verification.** The paired-cluster test asserts per-statistic sample warnings
and an explicit empty G3 group. This repair precedes the full replay.

## P8-029 - diagnostic sampler assumed every year had 29 catalogue events

**Root cause.** The first draft of this review's sampler requested 29 events from
2019, where the final catalogue contains none, and failed before evaluating data.
**Fix.** Take all available events from undersized strata and fill the remaining
sample without replacement with the fixed seed. No outcomes informed selection.
**Verification.** Exactly 200 historical events completed; identifiers and all
input-only gate results are committed in gate_diagnostics_round2.json.

## P8-027 - research screening rejected every candidate for absent user sector

**Root cause.** G2 required sector while mechanical screening always supplied None.
ATR-based entry/stop inputs already existed, so missing user thesis fields were
not a universal G6 blocker. Current ISIN metadata verifies at age zero.
**Fix.** Exclude only sector from research-mode G2; keep it Unknown in the bundle.
User assessments still require it. Invalid ATR, surveillance, liquidity and risk
failures remain failures. Nightly scans now pass verified map metadata and retain
previous frozen records. Range proofs share the nightly path and temporary copies.
**Verification.** 11 screening tests pass. Complete ten-session proof: 538 events,
403 passes / 135 failures, 503 execution rows, no durable writes. Historical
200-event baseline: G2 fails all 200; one G1, seven G4, 36 G5 and one G6 also fail.
Exact first/every-gate tables and reasons: docs/desk/gate_diagnostics_round2.md.
Dated pre-registration addendum prepared before this review computes any outcomes.

## P8-025 — durable Desk store cleared during a proof

**Root cause.** The prior handoff explicitly reports clearing the production Desk
store around a proof. The scratch proof opened the production connection. This
violates append-only storage; an empty journal never authorizes a reset.

**Impact and recovery, 2026-10-01.** Read-only temporary copies of both local Desk
backups contain zero rows in every table; the Praman backup has no Desk journal
tables. No backed-up thesis, decision, or paper trade needs a restoration decision.
The current store contains 567 scan rows, 545 execution rows and 3,574 circuit-band
rows, with zero thesis/decision/trade rows. All rows and all backups were preserved.
The normal additive initializer ran and row counts remained identical. Earlier
handoff reports 35,427 band rows; the present 3,574 rows do not substantiate that
historical coverage. Missing historical bands remain unknown, never zero.

**Fix.** Explicit durable-store non-negotiable in CLAUDE.md; filesystem audit guard
and SQL authorizer on normal durable connections; safety tests run before the suite.
The scratch proof now uses a temporary copy. These are Python/application guards,
not a claim that Windows permissions prevent an external shell from deleting a file.
Full timestamps and per-table counts: `docs/desk/store_inventory_round2.md`.

**Verification.** Two targeted guard tests pass, covering removal, replacement,
truncation, parent removal, SQL DELETE/UPDATE/DROP refusal, and permitted appends.
Initial baseline: 574 tests, two unrelated existing failures (clock and raw close).

## P8-026 — duplicated outcome boundary and raw replay reference

**Root cause.** A second outcome firewall used the machine clock, and the draft
replay used a raw previous-close field for the circuit calculation.
**Fix.** All Desk outcome callers use `desk/outcome_firewall.py` and its IST clock.
The duplicate module is removed. The replay derives the prior close on the session's
corporate-action-adjusted basis. No outcomes were computed during this repair.
**Verification.** Existing date-boundary tests cover May 31 / June 1 and the event
cutoff; a grep-style test rejects a second hard-coded Desk boundary.

## P8-024 — overnight-gap stress loss used the wrong current price scale

**Root cause.** `desk/risk/officer.py` multiplied the decision-date raw close by
the cumulative corporate-action factor before applying an adverse percentage gap.
That normalized series is useful for return ratios, but is not the current rupee
price. Direct store check: BAJFINANCE on 2025-06-18 closed at 919, with cumulative
factor 10; the old risk calculation used 9,190. This is a code defect, not a
sandbox/network/temp-folder failure.

**Fix.** Apply the gap percentage to the unscaled decision-date close. Historical
gap comparisons still adjust both prices onto the same as-of basis. A regression
test independently computes the worst gap from real adjusted OHLC rows across
BAJFINANCE's split/bonus and checks its current-rupee loss. Full-suite verification
is recorded in HANDOFF with the implementation checkpoint.

## P8-022 — new circuit-band table omitted from shared append-only test fixture

**Root cause.** Agent-introduced during Phase A Step 2: adding `circuit_bands` to
`DESK_TABLES` without adding its sample INSERT to the registry-wide append-only
test caused two `KeyError: circuit_bands` errors. Targeted circuit-band trigger
tests already passed; the existing registry-wide test could not create its row.
This was not a sandbox or temporary-folder failure.

**Fix.** Add a populated circuit-band fixture to the registry-wide UPDATE/DELETE
checks. Re-verification is recorded with Step 2 in the handoff.

## P8-023 — desk assess crashed while printing a zero-share position

**Root cause.** The engine deliberately returns a zero size and no stress-loss
record when budget caps cannot admit one share. CLI printing checked only whether
size was non-NULL, then dereferenced `result.stress_loss.stress_loss_inr`.

**Fix.** Print size independently and print numeric losses only when their record
exists; otherwise show N/A with the absence of a sized plan. This also lets band
provenance be shown when there is no complete thesis. Re-verification is recorded
with Step 2 in the handoff.

## P8-021 — announcement backfill is not a daily refresh; partial failures can look OK (open)

**Root cause.** During Phase A's foreground ingestion review,
`scripts/ingest_announcements_full_history.py` was read directly: its remaining
universe excludes every symbol already represented by any announcement row. This
resumes a historical backfill but does not refresh newer disclosures for those
symbols. It also catches per-symbol errors and prints `FAILED` without raising;
the ingestion wrapper recognizes exceptions and `WARN`, so it can report OK for
that partially failed step. Its summary currently drops those captured FAILED lines.
The underlying `fetch_symbol_announcements` also returns an empty list for any
non-200 response, making that response indistinguishable from a genuinely empty
history to its caller. No claim that such a response occurred in this run is made.

**Status.** Open; no pipeline or ingestion-source changes made for this finding.
Do not interpret an OK announcements step as proof of current disclosure coverage.
The user-requested latest-trading-day check is a separate bhavcopy check. A fix
needs a bounded recent-announcement refresh and explicit partial-failure reporting,
with tests and source-scope review before changing research ingestion behavior.

**Evidence.** `already_fetched_symbols`, the `remaining` filter, and the per-symbol
exception handler in the script; `_run_capturing` in `scripts/weekly_ingest.py`.
No claim about how many symbols failed in the active run can be made from these
code paths alone. Re-verification remains pending a fix.

**Triage, 2026-10-04 (user decision: give a severity, then fix or close).**
**Severity.** High.
Measured, read-only, in the production store: the backfill wrote ~1.02 million rows on
2026-09-18/19, and every nightly run since added only a few hundred (881, 239, 187, 5 and 13
rows), because the step skips every symbol with any stored row. Announcements by event month:
2026-08 20,897 rows / 2,296 symbols; 2026-09 8,847 / 2,065; 2026-10 18 / 4. Disclosures after
about 2026-09-18 are therefore missing for ~2,280 symbols. Impact: (1) Amendment 2 §5 of the
frozen pre-registration commits to weekly announcement ingestion through 2027-01-15, explicitly
not a single backfill; the forward window began 2026-09-16 and `disclosure_tier` is a binding
input, so the commitment was silently not being met. (2) Every live Desk evidence bundle since
then reads "no recent disclosure" as a fact when it is missing data. Not Critical because nothing
stored is wrong and the gap is recoverable: `knowledge_date` is each announcement's own
publication date and re-fetched rows are skipped by UNIQUE (symbol, seq_id, knowledge_date), so a
late refresh restores point-in-time-correct rows.

**Fix (code, 2026-10-04).** (1) `fetch_symbol_announcements` raises `AnnouncementFetchError` on a
non-200 response or a non-list payload instead of returning `[]` (a deliberate `src/` change
under the user's instruction to fix this defect). (2) The backfill prints its per-symbol failures
and summary as `WARN ...` lines, so the nightly step reports WARN instead of OK. (3) New nightly
step `announcements_recent` (`scripts/ingest_announcements_recent.py`), after `isin_map`: a
weekly (Amendment 2 §5), bounded, overlapping re-read for active equities that already have
rows, through the same fetch/row/write path as the backfill; marked complete only when no symbol
failed, so failures are retried the next night. First live run expected to fetch ~2,280 symbols
from about 2026-09-10; runtime unmeasured (the full backfill took ~87 minutes for 2,958 full
histories). Tests: 8 new (mocked sessions and fixture stores; no network).
**Status.** Open — fixed in code; live re-verification pending the first nightly refresh
(expect 2026-09 and 2026-10 per-symbol announcement counts to return to the normal range and a
COMPLETE refresh state). Close with that evidence.

**Additions, 2026-10-04 (user decisions; the one-line src change above approved).** (1) Missing
data never reads as "no disclosure": the Desk's disclosure dimension is a FACT only when the
announcement source is known complete through the day before the decision (stated limit 0 days,
`desk/source_freshness.py`). Completeness comes from the 2026-09-17 backfill baseline or a
`source_freshness` row (new append-only Desk table, read as of the decision's Desk watermark so
replay is exact) that the nightly `announcements_recent` step writes after each COMPLETE or
PARTIAL refresh, excluding the failed symbols. Otherwise the dimension is UNKNOWN, G2 fails and
the assessment is INSUFFICIENT (a screen SCREEN_FAIL), never ELIGIBLE. Two further routes to a
false "none" are closed the same way: a symbol with no stored announcement at all, and a window
with fewer than 10 sessions of history. The refresh now runs nightly. (2) Every opportunity and
decision recorded from 2026-09-19 until the fix is annotated INCOMPLETE_DISCLOSURE_EVIDENCE in the
new append-only `record_annotations` table, never edited or invalidated; research filters through
the `opportunity_log_annotated` / `decisions_annotated` views. (3) `docs/OPERATIONS.md` records the
lapse of Amendment 2 §5's weekly announcement ingestion as an operational deviation, recoverable
by publication date before the June 2027 evaluation. Tests: `tests/test_disclosure_freshness.py`
(stale sources never yield a disclosure FACT, across a grid of lags on real AXISBANK sessions; the
assessment becomes INSUFFICIENT; coverage and history gaps; partial refreshes; replay; the nightly
step) and `tests/test_record_annotations.py`.

**Closure, 2026-10-05 (user conditions: September back in range and a current watermark).**
**Status.** Closed — fixed and verified live.
The approved bulk switch (`904c53f`) and its foreground backfill from 2026-09-10 to 2026-10-05
(`docs/desk/announcements_bulk_rollout_results.json`; 28 of 30 approved requests, all HTTP 200)
completed every window: 12,394 rows returned, 9,400 inserted, 2,994 already stored, store delta
exactly +9,400. September 2026 now holds 17,077 rows (17,067 unique announcements, 2,384 symbols;
identical equity-only), inside the normal 16,000-21,000 (it was 8,847). October through 2026-10-05
is a partial month: 1,188 rows. The market-wide watermark is COMPLETE through 2026-10-05 (Desk
`source_freshness` row 1), so a 2026-10-05 decision's disclosure window (needing 2026-10-04) is
a FACT again. Residual: 163 bulk rows have an ambiguous or absent dated identity; they are stored
and any window containing one reads as UNKNOWN, not "no disclosure".
Nightly confirmation, 2026-10-05: the first scheduled bulk refresh (18:07 IST; 5 requests, all
HTTP 200) was COMPLETE for 2026-09-28 to 2026-10-05: 4,834 rows returned, 270 inserted, 4,564
already stored (Desk `source_freshness` row 2). September is unchanged at 17,077 rows. The
receipt's through date overstates the run's own day; see P8-049.

## P8-020 — interrupted ingestion left no durable start or progress

**Root cause.** `weekly_ingest.main()` captured all steps in memory and wrote its
first log entry only after they finished. An interrupted or sleeping process could
leave no evidence of the run, so Desk status continued displaying an older summary.
The process held no Windows system-awake request. The existing scheduled task's
wake and missed-start settings were already correct; this was not a task-setting bug.

**Fix.** Append, flush, and fsync a start before work and a status after every step.
Match each finished summary to its microsecond-resolution start timestamp. Desk
status reports unmatched starts, even if a later run completed. Hold and restore
the Windows thread's execution state with a guarded context manager; non-Windows
platforms do not call the API. No ingestion data calculations or task credentials change.

**Re-verification.** Seven targeted tests pass, including interruption between
steps, progress visibility during the next step, ERROR completion, overlapping
unfinished/completed runs, Windows restoration after interruption, API failure,
and non-Windows behavior. Full suite: `Ran 542 tests in 197.270s`, `OK`, Python
exit code 0. Existing mocked-ingestion summary tests also exercised the real
Windows sleep API successfully.
Live status still reports the pre-change log's ERROR and latest trading date
2026-09-25. No live ingestion or network download was run. Old interruptions with
no start entry cannot be reconstructed by the new parser.

**Follow-up, 2026-09-30.** Once a real interrupted start existed, status was refined
to show the latest completed summary alongside unmatched starts. A later recovery
can now be assessed without erasing the earlier interruption. The regression test
requires both the old unmatched timestamp and the later OK result. Full suite:
`Ran 552 tests in 119.817s`, `OK`, exit code 0.

## P8-019 — date-dependent test regression introduced with P8-018

**Root cause.** P8-018 moved ingestion's calendar date to `market_today()`, but the
retry tests still patched `weekly_ingest.date.today()`. That patch no longer reached
the code. The 28 September pass depended on the machine date matching the fixture;
on 30 September the baseline ran 534 tests with one failure and one `StopIteration`
error. The fetch and database are mocked: this is a test regression, not a sandbox
network or temporary-folder failure.

**Fix.** Audit all tests for date/datetime clock patches. The shared retry helper
was the only obsolete patch; it now patches `weekly_ingest.market_today` and checks
that it is called. ISIN-refresh tests also use a fixed market date, and health-age
tests inject a fixed UTC instant into their actual timestamp reader. A grep-style
guard rejects `date.today()` and `datetime.today()` in `desk/` and `scripts/`;
UTC timestamp calls remain allowed. Production calculations are unchanged.

**Re-verification.** On 30 September: `Ran 535 tests in 133.823s`, `OK`, Python
exit code 0. Pre-existing SQLite connection ResourceWarnings remain visible.

## P8-018 — mixed clocks: IST log times read as UTC; UTC dates compared with NSE dates

**Found.** `desk status` printed `last run 2026-09-28T13:53:03 (-1d ago)` minutes after a run.

**Root cause.** `scripts/weekly_ingest.py` wrote naive local (IST) timestamps;
`desk/ingestion_health.py` labelled them UTC, placing a same-day run 5.5 hours in the future.
The audit of every timestamp created or compared in `desk/` and `scripts/` found three more
places where a UTC value met an NSE (IST) calendar date:

| Where | Before | Effect |
|---|---|---|
| `desk/paper/open.py` (`check_can_open`, `open_approved_decision`) | `now.date()` of a UTC `now` | Between 00:00 and 05:30 IST the UTC date is still the previous day: an open at 01:00 IST on D+1 filled at D+1, one at 06:00 IST filled at D+2. Not a look-ahead leak (D+1's session opens 09:15 IST, after the UTC date rolls over), but the chosen session depended on the hour, contradicting the module's own rule, and staleness read one day low in that window. |
| `desk/paper/close.py` (`close_approved_trade`) | same | same shape for exits |
| `desk/gates/engine.py` (`_g7_overrides_this_month`) | UTC `recorded_at LIKE 'YYYY-MM%'` vs IST `as_of_date` month | an override between 00:00 and 05:30 IST on the 1st counted toward the previous month |
| `desk/cli.py` (`evening`), `date.today()` in `weekly_ingest.py`, `build_isin_map.py`, `ingest_bhavcopy_full_history.py`, `ingest_announcements_full_history.py`, `ingest_asm_gsm_sample.py`, `retry_asm_gsm_failures.py` | machine-local date | correct only because this machine runs in IST |

Left unchanged, verified UTC-vs-UTC: store and journal `recorded_at` (`_now()`), replay
watermarks, `scripts/snapshot_store.py`; `time.time()` is used only for durations.

**Fix.** `shared/market_time.py`: `IST` (fixed +05:30, no DST), `market_today()`,
`market_date()` (refuses naive datetimes), `parse_logged_timestamp()` (legacy naive log entries
read as IST). The log now writes `+05:30`; every NSE-date use above goes through the module.

**Re-verification.** 8 new tests: legacy and offset same-day runs report `(0d ago)`; opens at
01:00 and 06:00 IST on D+1, passed as UTC instants exactly as production's default `now`, both
fill at D+2; an override at 00:30 IST on the 1st counts toward the new month; `market_date`
conversions. Run against the pre-fix code, 4 fail as expected. A first draft of the 01:00 test
passed an IST-labelled datetime, which hid the bug (`.date()` already returned the IST date); it
passed against the old code and was corrected to a UTC instant before commit. Full suite:
`Ran 533 tests in 213.729s`, `OK` (Python exit code 0).

### P8-038 correction work, 2026-10-04

Both-side costs are required by the rulebook and correctly used by the follow-up.
The sizing bound used gross stop distance and G6 lacked an independent per-trade
check. Cost-inclusive integer sizing and a G6 check now repair both omissions.
Unknown quantitative gates cannot derive ELIGIBLE. No rulebook or entry convention
was changed. Earlier results are preserved as *_pre_g6; preregistration addenda
and the next experiment were committed first at cb89f96. Real-data regression and
full replay verification are pending; do not treat this entry as completed evidence.

## P8-039 - regression quantity type and maintenance encoding errors

2026-10-04, Low, fixed. The new real-assessment regression passed the engine's
integral float quantity to cap_measurements, which requires an integer. Convert
the assertion input to int. A follow-on documentation command omitted UTF-8 and
first mangled existing punctuation and a subsequent read stopped on a decode
error. Restore existing text from Git and reapply only intended additions with
explicit UTF-8. Diff review confirmed the original punctuation is preserved.
No historical run or production measurement was affected.

## P8-040 - proposed limit runner confused market and knowledge cutoffs

2026-10-04, Medium, fixed before the first limit run. Static review found the new
runner queried next-session bars as of the replay's latest market-session date
rather than its run/knowledge date. That could omit a late-known correction.
Use the recorded run_date, matching execution_observation's original as_of cutoff.
The experiment also checks each baseline opening against its frozen replay fill;
any mismatch aborts. No real limit result was computed with the draft cutoff.

## P8-041 - unfinished volatility/limit work missed three review items

2026-10-04, Low, fixed before any real run of either module. Review of the
uncommitted Codex files found: (1) volatility context did not explicitly mark
a historical assessment as retrospective, which A2 requires; it now records and
displays `retrospective` when the decision predates the reference publication
date. (2) The limit runner checked the frozen baseline opening only one way; a
pass with no frozen fill but a usable opening would have produced a limit fill.
The guard is now two-sided and requires a positive frozen quantity (the replay's
cap assertion already rejects nonpositive pass quantities). (3) The
preregistration's required shared-date draw test was absent; added. No result,
store or registered protocol was affected.

## P8-042 - first volatility-context wiring could abort assess after recording

2026-10-04, Medium, fixed before commit. The first `desk assess` wiring caught
only ValueError/UnadjustableWindowError from the context lookup. Any other
exception (seen as TypeError in the existing zero-share CLI test, which mocks the
store connection) aborted the command after the decision row was already
appended, so the operator would see a crash for an information-only field. The
lookup now records UNKNOWN with the exception type and message; a test covers
it. No durable store was written by the faulty draft outside temporary tests.

## P8-043 - decision-price sizing still breaches the per-trade cap at the fill (open)

**Severity.** Medium. **Status.** Open.

2026-10-04, Medium, OPEN (risk-control gap, not a code defect). With P8-038
fixed, every pass satisfies the per-trade cap at its decision price, but the
fill is the next session's price while quantity and stop stay frozen. In the
corrected primary replay 30.38% of filled passes exceed the cost-inclusive
per-trade cap at the next open (median excess 11.5%, p90 40.7% of cap).
Follow-up 2's 0.5 x ATR20 limit reduces this to 27.47% (paired difference
-2.91 pp [-3.14, -2.70]; p90 excess 24.1%). Impact: any automatic or manual
paper entry that does not re-check the cap at the fill will routinely take
more than the budgeted per-trade risk. No rule, gate or convention changed.
Candidate mitigations, each needing its own preregistration before measurement:
size against the limit price (bounds planned loss for any fill at or below the
limit by construction), or re-check the cap at the fill and abstain.

**Closure, 2026-10-04 (user decision: close once Strategy 0 v2 is active).**
**Status.** Closed — fixed by sizing at the entry limit price in both books.
Follow-up 3 (prereg `b2df2a2`, implementation `bc46648`, results `72a0a97`) passed both
preregistered criteria: zero per-trade cap breaches at the fill in 51,414 limit fills across
both periods (frozen decision-price sizing: 27.47% of primary fills), fill rate unchanged at
97.10%, mean quantity ratio 0.907. Applied in `b13cc7e`: Strategy 0 v2 (registered PAPER_BURN_IN
in the production Desk store on 2026-10-04 at 20:50 IST; v1 kept as SUPERSEDED_NEVER_RUN, never
run) and manual `desk assess`, both sizing with the rulebook function at the day limit order's
price. For any fill at or below the limit, the planned loss cannot exceed the planned loss at
the limit, which the sizing keeps within the cap (costs are non-decreasing in price). Engine tests
assert zero at-fill breaches for limit-sized fills. Research screening and the frozen replays keep
decision-price sizing, as registered.

## P8-044 - paper fills used the history-wide split factor, not the decision share basis

**Severity.** High. **Status.** Fixed 2026-10-04, before any record was affected.

**Found.** While implementing the user-approved manual limit entry. `desk/paper/open.py`,
`desk/paper/close.py` and `desk/paper/execution.py` (`check_stop_on_session`, and the unused
`fill_entry`/`fill_non_price_exit`) multiplied raw session prices by `cum_factor_up_to(date)`,
the product of every bonus/split since the symbol's history began. That re-expresses a price in
the history's EARLIEST share basis, while the thesis stop and the decision quantity are on the
current raw basis. Verified on the real store, read-only: TATASTEEL (SPLIT 10:1, 2022-07-28) has
`cum_factor_up_to('2026-10-01') = 10`, so a manual paper entry at the real open of 184.37 would
have been recorded at 1,843.70, costs and P&L would have been scaled ten-fold, and the stop could
never trigger. Any symbol with a bonus or split since 2019 was affected. Separately, neither the
manual path nor Strategy 0 handled a bonus/split ex-date between the decision and the fill
(Strategy 0 compared a raw post-split open with a pre-split limit), and corporate actions during a
manual holding were never applied (`adjust_for_corporate_actions` had no caller).

**Impact.** None recorded: the Desk store holds zero manual paper trades, and Strategy 0 has never
run in production. Research code is unaffected; it only divides prices adjusted the same way.

**Fix.** One rule everywhere: every price of a paper position is kept on its DECISION date's share
basis. `desk/paper/execution.py:basis_factor` returns the store's point-in-time
`compute_adjustment_factor` over (decision date, session date] — exactly 1.0 without an
intervening bonus/split, so the common case records the raw price. Manual entry, close and the
monitor's stop check use it (the position's basis date is its opening decision's as_of_date);
Strategy 0 evaluates and records entries on that basis and re-expresses stop and quantity from the
decision date. An unadjustable action (demerger) refuses the manual open or close and leaves the
monitor's stop unchecked with an explicit report; for Strategy 0 it is a NO_FILL at entry and an
exit order while held. Never priced by guesswork.

**Re-verification.** `tests/test_paper_limit_entry.py` (10 tests) and a new Strategy 0 test,
including a regression fixture whose history-wide factor is 10 (the old code records 1,015.0
there; the fix records 101.5), a split between decision and fill, a split during a holding (no
false stop on the decision basis; the raw comparison would have stopped out), the decision-basis
exit price and P&L, and demergers. Existing paper, hindsight, monitor and risk tests pass unchanged.

**Structural guard, 2026-10-04 (user request).** Lineage: P8-044 is the second CONFIRMED
share-basis defect, after P8-024 (stress loss scaled by BAJFINANCE's history-wide factor 10: 9,190
instead of 919). The suspected P7-001 (`prev_close` in `close_to_close_60d`) was investigated twice
and refuted (`docs/RESULTS.md`; guarded by `tests/test_no_raw_prev_close_in_signals.py`), so it is
not counted. Follow-through in `b13cc7e`: Strategy 0 now records its stop, monitored prices and
exits on the decision basis too (it had kept exits at raw prices with a re-expressed quantity,
which was notionally consistent but not one basis). `tests/test_share_basis_structural.py` drives
one synthetic 10:1 split between decision and exit through every price path -- manual open, the
monitor and its stop, a pending manual close, Strategy 0 entry, monitoring and stop exit -- and
asserts that every recorded price stays on the decision basis, that costs equal the costs of the
real post-split share count at raw prices, and that P&L equals that economic oracle. Mutation
check: removing the decision basis from the manual close/monitor path, or forcing Strategy 0's
basis factor to 1, each makes it fail; the unmutated code passes.


## 2026-10-04 dated clarification: requested P7-001 recollection

This audit searched DEFECT_REGISTER.md, RESULTS.md, Phase 7 documentation and
available Git history for P7-001, close_to_close_pct, raw_prev_close_unadjusted,
and the recalled KOTAKBANK 2026-09-02 / 3.87% versus 0.33% example. No record
confirming that example or that field rename was found in the available history.
There is no confirmed defect ID to assign to the recalled case on this evidence.
P7-001 is referenced as a REFUTED suspicion about close_to_close_60d; there is no
P7-001 defect-table entry describing a different confirmed bug.

The guard test first appears at 7b3de51, already explicitly labelled preventive,
not a fix. RESULTS.md's correction was introduced at 1c3f655. The schema still
stores the original raw previous-close column for provenance; the signal path
uses the adjusted return function. The literal raw_prev_close_unadjusted appears
in later Desk material (b279ec9/a90db35), not as evidence of a schema rename or
of the recalled Phase 7 bug. Confirmed later price-basis defects P8-024 and P8-044
are separate cases and do not establish the recalled example. Historical entries
above are preserved. This is a clarification of the requested identification,
not a claim that an unlocated incident was fixed.

The Phase 7 derivation module independently recomputes volume_ratio and delivery
percentiles only. Its documented price-return checks remain transcription-only;
it does not implement the recalled independent close_to_close_pct check.

## P8-045 - historical interrupted ingestion shown as currently unfinished

**Status.** Closed.

2026-10-04, Low, fixed. ingestion_health_line retained unmatched starts even
after a later successful run, so the October 1 interruption still appeared
current after October 3 finished. Current warnings now include only unmatched
starts later than the latest completed OK/WARN run's start. WARN is the nightly
runner's successful completion with warnings (scheduler exit 0); ERROR does not
supersede an interruption. The log is never edited, so history remains intact.
Tests cover later OK/WARN recovery, ERROR non-recovery, a newer unmatched start,
and history preservation. Full-suite verification is in HANDOFF.

## P8-046 - obsolete announcement symbols can return a successful empty response

**Status.** Open. Medium. Found 2026-10-05 during the approved bulk parity probe.
**Severity.** Medium (stated above; added in this machine-readable form 2026-10-05).

NSE returned HTTP 200 with zero rows for HEG and SANGINITA over September 7-13,
while the bulk endpoint returned the same five stored announcements under HEGAM
and AGASTYAEN, with matching sequence IDs, ISINs, timestamps and contents. The
per-symbol row builder uses the requested symbol, and the refresh treats a valid
empty list as success; it does not distinguish an obsolete symbol from a real
absence. This can falsely establish freshness when an old symbol is in the plan.
The scope of missed post-rename disclosures has not been measured; these five
historical disclosures are already stored and are not claimed lost.

**Historical reach, 2026-10-05 (approved read-only audit; report only).** Plan fixed before any
request; 20 of 20 approved audit requests, all HTTP 200
(`docs/desk/announcement_rename_audit_results.md` / `.json`). Of 20 sampled securities from the
logged 195 rename groups (127 with 4,402 eligible events), 12 would have a different frozen
disclosure tier, all frozen `UNKNOWN_COVERAGE` while the bulk endpoint holds their announcements
under the later symbol (10 by missing disclosures, 2 coverage-only). Estimated affected events:
about 2,356 of 4,402 (Hajek ratio; Horvitz-Thompson about 2,407), about 1,816 through missing
disclosures; no precise CI (one event per security). No frozen artifact changed. Prospectively,
the nightly no longer queries by symbol (bulk mode), so obsolete-symbol empty responses can no
longer establish freshness; status stays Open for the historical effect, which only a separately
registered re-analysis could address.

**Frozen-data implications, 2026-10-06 (user direction).** Recorded in `docs/OPERATIONS.md` as a
known limitation for the June 2027 evaluation, not an amendment: about 2,400 catalogued events from
renamed securities (roughly 3% of the catalogue) probably had their disclosure tier misrecorded in
the training data, with the audit's estimates and sampling limits. The pinned forward pipeline
(`afe3e2b`) was verified to still read the restructured store
(`docs/desk/pinned_reader_verification.md`; `scripts/verify_pinned_announcement_reader.py`, read-only
copy, temporary worktree): 1,143 of 1,156 recent events identical to HEAD's reader in tier and
rows; 13 window-boundary differences in two renamed securities (HEAD the more conservative); the
pinned `init_db` changes nothing; no unexplained, misfiled, duplicate or read-after-event
difference. Not evaluation-blocking. The symbol-keyed blind spot continues forward: 9 sampled HEGAM
events cannot see 118 rows filed under HEG (all from the old per-symbol path, no tier changed), and
after a future rename an event's first 10 sessions will see only the post-rename announcements.

Evidence: docs/desk/announcements_bulk_reconciliation.json and its captured
responses; all five alias pairs reproduce offline. Tests reject same-ID matches
with changed content, date or ISIN. The proposed bulk switch must resolve dated
identities and fail closed on unresolved coverage. No production fix is made in
this investigation; source/freshness changes await the user's switch review.

## P8-047 - draft bulk audit compared UTF-8 captures with inconsistent decoding

**Status.** Closed. Low. Introduced and corrected 2026-10-05 before commit.

The first draft of the offline reconciliation script decoded the old JSON capture
with the Windows default encoding but the new capture explicitly as UTF-8. This
reported a false persisted-content difference for non-ASCII announcement text.
All JSON text reads in that script now specify UTF-8. Re-running on the real
captures confirms identical persisted fields across both days and split windows.
No durable store, source payload, or committed historical result was changed.

## P8-048 - bulk-switch draft broke schema setup and migrated production before review

**Severity.** Medium. **Status.** Fixed 2026-10-05, before the switch was committed.

Found while resuming the unfinished Codex bulk switch. (1) `CORPORATE_ANNOUNCEMENTS.triggers` was
written as `("""CREATE TRIGGER ...""")` with no trailing comma: a string, not a one-element tuple,
so `init_db` iterated its characters and failed with `near "C": syntax error`. Every test that
initialises a store errored (20 targeted tests); the full suite was otherwise unaffected. Fixed with
the trailing comma; 45 targeted tests and the full suite (752) then passed. (2) Process: before that
edit, an earlier uncommitted draft had already run `init_db` against the PRODUCTION Praman store
(data/processed/praman.db, modified 2026-10-05 11:58), adding five nullable columns to
`corporate_announcements` (isin, reported_symbol, identity_date, identity_status, raw_json), two
indexes and the `announcements_stable_id_insert` trigger. Verified read-only: no row added or
changed (1,022,965 rows, latest recorded_at 2026-10-03; no row has an isin), and `security_identities`
was not created. The change is additive and is the approved design, but it reached production
unreviewed. It is compatible with e09d608's code (the trigger only rejects an exact
(seq_id, knowledge_date) repeat, which that code already treats as a skipped duplicate).

Review fixes in the same change: the equity-only read filter required `INE` ISINs, silently
dropping the IN9 DVR class that the project's equity-only rule keeps; it now excludes fund units
(`INF`) only. Bulk ingestion now resolves publication-date identity from the append-only
`security_identities` fact table as of the run, not from the cache files that transported it.

## P8-049 - a same-day refresh receipt certifies the rest of that day

**Severity.** Medium. **Status.** Open. Found 2026-10-05 verifying the first nightly bulk
refresh; no record affected.

`step_announcements_recent` records `through_date` as the refresh's end date, which is the run's
own market date (`ingest_announcements_recent.main`: `end_date = market_today()`), and
`complete_through` returns it unchanged. A receipt recorded during day D therefore states the
source complete through all of D, although D's filings keep arriving after the run. Both receipts
so far do this: `source_freshness` row 1 (backfill, recorded 12:29 IST) and row 2 (nightly, 18:07
IST) each certify 2026-10-05. Measured read-only from the stored bulk rows' own publication
timestamps (`sort_date`): on each of the nine full trading days 2026-09-21 to 2026-10-01, 25.2% to
38.2% of that day's announcements were published after 18:07 IST (2026-09-30: 460 of 1,216).

Reach. A decision dated D+1 needs completeness through D. Normally the D+1 nightly re-reads D in
full (seven-day overlap) before that night's Strategy 0 run, so nothing is exposed; tonight's
decisions were dated 2026-10-05, needed 2026-10-04, and were fully covered. Exposed: (1) a night
whose refresh is not COMPLETE while the later steps still run: that night's Strategy 0 decisions
rest on the previous evening's receipt and read about a third of the previous day's filings as
absent, and so does a manual `desk assess` at its default as-of (the newest stored session) until
the next COMPLETE refresh; (2) a manual `desk assess --as-of` later than the latest receipt's run
date. While every nightly refresh completes, the default as-of is not exposed. (Corrected
2026-10-05 before the session ended: the first wording said the default as-of is never exposed.)
No decision or opportunity is affected:
production `decisions` has 0 rows, and the 37 Strategy 0 contracts and 45 screened events are
dated 2026-10-05. Medium, like P8-046 (a narrow condition can falsely establish freshness), not
High like P8-021 (every live bundle affected).

Proposed fix, not implemented (a Desk code change awaiting review): `complete_through` caps each
receipt at the last calendar day fully elapsed in IST when it was recorded (the IST date of
`recorded_at`, minus one day). Applied on read, it corrects the existing receipts without editing
them, stays deterministic under replay (the same rule over the same visible rows), and leaves
tonight's results unchanged (rows 1-2 would certify 2026-10-04, which those decisions needed).
Test to add: a receipt recorded at 18:07 IST on D leaves a D+1 decision's disclosure dimension
UNKNOWN until a receipt recorded on D+1 or later exists.

**Fix, 2026-10-06 (user approval: "approve the fix as proposed, at Medium severity").**
**Status.** Closed — fixed as proposed and verified against the production receipts (read-only).
`desk/source_freshness.py`: `certified_through` caps a receipt at the IST day before the day it was
recorded (a naive or unreadable `recorded_at` certifies nothing); `complete_through` and
`market_coverage_from` both use it. Receipts are unchanged. Tests
(`tests/test_disclosure_freshness.py::SameDayReceiptTest`): the cap at the IST day boundary
(23:59 IST still D; 00:01 IST is D+1), a receipt claiming less is kept, and a D+1 decision is UNKNOWN
under a receipt recorded on D, then a FACT after one recorded on D+1. That test fails with the cap
removed. Earlier tests now stamp receipts explicitly instead of using the wall clock. Production,
read-only: rows 1-2 now certify 2026-10-04, so the 2026-10-05 decisions (needing 2026-10-04) are
unchanged; a 2026-10-06 decision stays UNKNOWN until tonight's receipt certifies 2026-10-05.

## P8-052 - Strategy 0 v2 chose among budget-limited candidates in symbol order

**Severity.** Low. **Status.** Closed — superseded by Strategy 0 v3 (user approval 2026-10-06).

Raised by the user after the first run: v2's registered definition takes the day's SCREEN_PASS
candidates "ordered by symbol then opportunity_id" and accepts them greedily against the Rs 25,000
open-risk budget, so a symbol's spelling decided which candidates were traded when not all fit. On
2026-10-05, 37 passed: 5PAISA (first alphabetically) and AUBANK (third) were accepted; ATLANTAELE
(second) was rejected because its Rs 8,849.79 stress loss no longer fitted after 5PAISA's Rs
19,866.53; the other 34 were rejected on the budget as well. Low: Strategy 0 is a paper burn-in, not
expected to be profitable, its results are not evidence of an edge, and no evaluation uses its
selection; but its sealed record would over-weight early-alphabet and digit-led symbols.

Fix (v3, `desk/automation/registry.py`, `desk/automation/strategy0.py`): the same greedy budget rule
over a seeded random order, seed = sha256("S0-v3-candidate-order|<decision date>"), each candidate
ranked by sha256("<seed>|<symbol>"), ties by opportunity_id. The seed and order are recorded in each
run's operational record and shown in the brief. A hash rank rather than `random.shuffle` keeps the
order independent of Python's RNG implementation, and adding or removing one candidate never
reorders the others. v2 is marked SUPERSEDED_AFTER_ONE_RUN by the next run's registration. Found
while implementing it and fixed with it: the engine's book, its once-per-date check and its
fill-failure streak were all keyed by version, so a version change would have orphaned v2's two
pending positions (never settled, never monitored, outside the budget) and could re-decide
2026-10-05. Now one book spans versions (each position keeps its accepting version on every
event), a run date is processed once across versions, and the streak counts every version. Tests
(`tests/test_strategy0_engine.py`): the order matches an independent restatement of the rule and is
recorded; reproducibility from the date; v2's positions settle and are monitored under v3 with
version 2 and count against v3's budget; ALREADY_RUN across versions; a cross-version failure
streak trips the switch. The in-code v1 and v2 definitions hash exactly as the production rows
(`3e93f063...`, `1ff7fa71...`). Rehearsed on a temporary copy of the production desk store: v2
superseded after one run, v3 registered, 2026-10-05 ALREADY_RUN, 5PAISA and AUBANK in the book as
v2 PENDING_ENTRY (Rs 24,764.32 of the budget); the production store was unchanged.

## P8-060 - the nightly ISIN refresh re-downloads fixed historical snapshots, making WARN routine

**Severity.** Low. **Status.** Closed — fixed 2026-10-13 (user approval); found the same day (the
user asked why the ISIN WARN stopped).

`scripts/build_isin_map.py` fetches today's CM snapshot plus all ten fixed historical
`SNAPSHOT_DATES` (2019-11-15 to 2025-10-13) from NSE's archive every night, with no cache. Most nights
one or two of those downloads fail with an HTTP error, a different date each night (30 Sep:
2020-06-15, 2021-02-17; 6 Oct: 2020-06-15, 2021-06-15; 7 Oct: 2020-06-15, 2023-06-15; 8 Oct:
2021-02-17; 9 Oct: 2021-07-22; none on 5 and 12 Oct), and the step reports WARN. The same dates
succeed on other nights, so the failures are transient on NSE's side. Nothing changed: the last
change to the script or `isin_mapping.py` is ec12bc4 (P8-034), before all of these runs. 12 Oct was
simply a night when every download succeeded. Since P8-034 a failed historical snapshot loses no
identity (the existing map's identities are retained), so the WARN carries almost no information,
and a routine WARN hides a real one. The log keeps only the exception type, not the HTTP status.
Proposed fix: fetch each fixed historical snapshot once into a checksummed cache and re-use it, so
the nightly fetches only today's snapshot (ten fewer NSE requests a night), and record the HTTP
status of any failure; then an ISIN WARN means something real.

**Fix, 2026-10-13 (user approval).** `scripts/build_isin_map.py` reads each fixed historical
snapshot through `cached_bhavcopy_save`: the raw CSV lives in `data/raw/isin_snapshots/` (with the
project's other raw data, outside the repository) as `cm_<date>.csv` with a
`.sha256.json` sidecar (SHA-256, size, NSE file name, download time). Every use re-hashes the file;
a missing file, missing or unreadable sidecar, or a mismatch is a WARN naming the problem and the
snapshot is downloaded again into a fresh folder, checked to be a CM bhavcopy with an ISIN column
and at least one row (an error page is never cached), and replaced whole. Today's snapshot is never
cached and its handling is unchanged (a 404 is a WARN and keeps the existing map). A failure now
names the HTTP status ("HTTPError, HTTP 503: ..."). `src/` is unchanged (the cache wraps the
`bhavcopy_save` that `fetch_isin_snapshot` already takes), and so are the merge and identity
rules. Check (network, temporary cache; the production map and `data/raw` only read): each of the
ten snapshots parsed from the cache equals the same snapshot freshly downloaded (1,478 to 2,292
symbols each), all ten cache reads verified their hash with no download, and the merged historical
map is identical (2,819 symbols). Against the production map built 12 Oct: all 2,819 present; the 53
whose ISIN differs there are all explained by that build's own 12 Oct snapshot, which wins on
conflict by design. The real cache folder does not exist yet: tonight's nightly downloads the ten
snapshots once (as it does every night now) and caches them; from 14 Oct it fetches only today's.
Tests: `tests/test_isin_map_operations.py::HistoricalSnapshotCacheTest` (downloaded once then read
from the cache with the same map, today's never cached; a damaged file, a missing file, a missing
or unreadable sidecar each re-downloaded with a WARN and then read from the cache again; an HTTP
503 names the status; an error page is not cached and the next run caches both).

## P8-058 - manual open risk was entry-to-stop risk, not the stress loss the rulebook caps

**Severity.** Medium. **Status.** Closed — fixed 2026-10-13 (user approval); no record affected.

Raised by the user. `risk.max_open_risk_pct` caps aggregate STRESS-loss exposure (the rulebook's own
comment: "measured on stress loss ... not on planned loss alone"), and G6 adds each candidate at its
stress loss. But the open risk already used by manual trades (`desk.gates.engine._open_risk_used_inr`,
also the input to position sizing's open-risk room and the brief/`desk status` manual line) summed
|entry - stop| x quantity: no costs and no gap or locked-circuit stress. Its docstring claimed the
stress loss recorded on the opening decision and cited a "named gap" in `docs/desk/phase1.md` that
is not there; no rulebook, DESIGN.md or register text records a decision to use entry-to-stop. Open
manual trades therefore counted at a fraction of their stress, about a quarter for a 20%-band stock
with a stop 10% below entry (the locked-circuit scenario is band x 2 lock days = 40% of position),
so G6 could admit a trade beyond the cap and sizing saw too much room. Medium: a risk cap was
understated; production has had no manual trade and no manual decision, so nothing was affected and
no recorded decision replays differently.

Fix: each open manual trade counts at the stress loss recorded on the decision that opened it
(`decisions.stress_loss_inr`, persisted at assessment and sized at the limit price), as Strategy 0
counts the stress loss recorded at acceptance. A trade without one makes the open risk unknown
(`OpenRiskUnknown`): G5 and G6 become UNKNOWN with the reason, so the assessment cannot be
ELIGIBLE, and the brief and `desk status` show UNKNOWN, never an understated number. The display
label is now "Open risk by book (stress loss, the rulebook measure)". No rulebook change. Tests:
`tests/test_manual_open_risk.py` (the rulebook's stress loss for a fixed 20% band, Rs 2,000 against
Rs 500 entry-to-stop; G6 fails where the old measure passed; an unrecorded stress loss; closed
trades; a real-data assessment with an unrecorded open trade). All five fail with the old measure
restored.

## P8-059 - the nightly could run half-finished working-tree code

**Severity.** Medium. **Status.** Closed — guard added 2026-10-13 (user approval); never occurred.

The scheduled task runs `scripts/weekly_ingest.py` from the working tree and records `code_commit`
(HEAD) with every decision, and since P8-053 it usually starts the moment the laptop wakes. A
session interrupted by sleep would leave it uncommitted, possibly unfinished code, and its
decisions would cite a commit that is not the code that ran. Guard: before any step,
`git --no-optional-locks status --porcelain -z --untracked-files=all` (which never writes to the
repository: a test shows plain `git status` rewrites the index where this does not). If any file
the nightly runs or reads differs from HEAD, tracked or untracked (code and config under `src/`,
`desk/`, `scripts/`, `shared/`, `config/`, `rulebook/`, plus the three docs it reads at run time:
`docs/DEFECT_REGISTER.md` for the open-critical-defect switch and the two
`docs/desk/shadow_replay_followup*_results.json` files), or git cannot run, no step runs and the
skip is a WARN in the log and that day's brief naming the files, exactly like the low-battery skip.
Other docs and theses never trip it. git comes from PATH (the machine PATH holds `C:\Program
Files\Git\cmd`, which the scheduled task inherits) with that install path as a fallback. The normal
state was checked first: the porcelain status was empty. Tests: `tests/test_nightly_tree_guard.py`
(a real temporary repository: clean, tracked/untracked/renamed code and config, the read docs,
ignored docs and theses, no index write, git missing or failing; `main()` runs on a clean tree and
skips on a dirty one). The nightly harnesses in other tests now isolate the check, as they do the
battery (P8-055 lesson). Catch-up: the data steps catch up; the skipped date's scan, Strategy 0
decisions and brief do not (P8-056), nor do Strategy 0's stop checks for that session (P8-057).

**Follow-up, 2026-10-13 (user: "also skip when HEAD isn't master").** The guard had a hole: a clean
tree on another branch, or a detached HEAD, ran that code. Now, before the tree check,
`git --no-optional-locks rev-parse --abbrev-ref HEAD` (read-only) must print `master`; otherwise no
step runs and the WARN reads "HEAD is on branch <name>, not master; the nightly runs only on master"
(or "HEAD is detached, ..."). If git cannot read HEAD, it skips with "git could not read HEAD". The
burn-in gap record (P8-056) labels these NOT_ON_MASTER and GIT_UNAVAILABLE. Tests:
`tests/test_nightly_tree_guard.py::HeadBranchTest` (a real temporary repository: master, another
branch, detached HEAD, no index write, git missing or failing) and `NightlyGuardTest` (another
branch and detached HEAD skip with the WARN in the log and brief, the branch is checked before the
tree, an unreadable HEAD skips, the gap labels); the other nightly harnesses patch the branch too.

## P8-056 - a skipped night loses that date's scan, Strategy 0 decisions and brief

**Severity.** Medium. **Status.** Closed — fixed 2026-10-13 (user decision, option (b)); see the fix below.

After a skipped or missed night the next run catches up the data steps: bhavcopy fills missing
dates, announcements re-read a seven-day overlap, corporate actions 60 days, ASM/GSM 30 days, and
the manual monitor checks every session since entry (P8-054). But the circuit bands, the desk scan,
Strategy 0's run and the brief all work on the latest stored session only
(`ingest_price_bands.run()`, `run_scan(latest)`, `run_auto_paper()`, `write_brief()`), so the
skipped date gets no bands, no opportunity log, no Strategy 0 decisions and no brief of its own. A
Strategy 0 run for a past date would also trip DATA_STALE_OR_INCONSISTENT by design ("Run date ...
is not the latest stored session"), which blocks new entries. Nothing affected yet: every session
since Strategy 0 began (2026-10-05) had its own run. The P8-053 and P8-059 guards make skipped
nights more likely. Options: (a) on the next run, process each missed session in date order with
only the data known by that session (needs a stated exception to the stale-data switch for
catch-up dates, and a rule for an entry whose next session is already in the store); or (b) keep
recording the date as a burn-in gap and say so in the brief.

**Fix, 2026-10-13 (user decision: record the date as a gap, with no catch-up exception to the
stale-data switch; "paper must only do what live trading could have done ... An entry needs an
order placed before the next open; if that couldn't happen, there's no entry").** No new Strategy 0
version; the stale-data switch is unchanged.
- New append-only table `strategy_gaps` (one row per strategy and decision date). Each trading
  session after the last date Strategy 0 decided and before the run date with no Strategy 0 run is
  recorded by the next run, which then decides its own date normally; the missed date is never
  decided later. Reason: RUN_FAILED if a run for it crashed (the nightly's `S0_RUN_FAILED` journal
  event), else the skip the nightly logged for it (BATTERY_SKIP, UNCOMMITTED_CODE, NOT_ON_MASTER,
  GIT_UNAVAILABLE; `desk.ingestion_health.skips_by_decision_date` reads `logs/weekly_ingest.log`: a
  skip at or after 15:30 IST belongs to that day, an earlier one to the previous weekday), else
  NO_RUN. The skip lines and failures go in the gap's detail.
- Too late: `strategy0.entry_cutoff(D)` is 09:00 IST on the next weekday after D. A run whose
  decision time (the moment Strategy 0 decides, in the auto_paper step; the steps after it place
  nothing) is after the cut-off records D as DECIDED_TOO_LATE, with the decision time and cut-off,
  and makes no candidate decisions; pending entries, stops and exits (including late time exits) are
  still processed. No holiday calendar exists, so after a weekday holiday the cut-off is the
  holiday's morning: earlier than needed, never later, so it can only cost an entry, never allow
  one live could not have placed.
- Brief: "Burn-in gaps recorded by this run: <date> (<reason>); N in total" in the Strategy 0
  section, and on a too-late run "NO DECISIONS for <date>: ..." instead of "NO TRADE". `desk
  status`: "Strategy 0 burn-in gaps (dates with no decisions): N; latest <date> (<reason>)".
- What happens today, before this fix (user question): a run for D that decided after the next
  morning's open still accepted entries, and their limit orders were then filled against an open
  that had happened before the decision. It never happened: all six Strategy 0 runs (5-12 Oct)
  decided the same evening, between 18:40 and 21:52 IST, and every session had its own run, so the
  new code records no gap for the past (replay of all six runs with it on temporary copies:
  identical, no gaps).
- A run after midnight but before 09:00 decides D normally (tested). Reported, not changed: the
  `bhavcopy_today` step, which runs before Strategy 0, asks for the calendar day's file; after
  midnight that is the next session's, which cannot exist yet, so it spends its whole retry budget
  (6 attempts, 15 minutes apart, about 75 minutes of waiting) and reports WARN. A run starting
  after about 07:00 can therefore reach Strategy 0 after 09:00 and record a DECIDED_TOO_LATE gap
  that the decision itself did not need.
- Unchanged: the skipped date still gets no circuit bands, desk scan or brief of its own; the data
  steps catch up as before.
- Tests: `tests/test_strategy0_engine.py::BurnInGapTest` (a run after a skipped night decides its
  own date and records the gap once; NO_RUN; RUN_FAILED; too late: a gap, no decisions, entries and
  a stop still filled, brief lines; 08:59 after midnight decides; a Friday decided on Saturday is on
  time, the cut-off Monday 09:00), `tests/test_ingestion_progress.py::SkipsByDecisionDateTest`, the
  nightly passing the logged skips (`test_nightly_passes_the_logged_skip_reasons_to_strategy0`),
  `tests/test_desk_brief.py` (the `desk status` line) and `tests/test_desk_append_only.py`.

## P8-057 - Strategy 0 checks stops on the run date's session only

**Severity.** Medium. **Status.** Open — found 2026-10-13; the fix awaits the user's decision.

`strategy0.run` monitors each open position against `session_bar(..., run_date)` only. After a
skipped run date (P8-056), a stop touched on the skipped session is never seen if the next session
recovers, and a time-limit exit is ordered one session late (the session count itself is right).
The same defect class as P8-054 in the manual book. Nothing affected: every session since
2026-10-05 had its own run, so every Strategy 0 position was checked on every session. Proposed
fix: check every session since the fill in date order, as P8-054 does; it changes the registered
engine's implementation, not its rule ("monitoring starts the session after the fill").

**Fix, 2026-10-13 (user approval; "paper must only do what live trading could have done: a stop
would sit at the broker and fire whether or not the laptop ran").**
**Status.** Closed — fixed; no new Strategy 0 version (the code now follows the registered rule).
`strategy0.run` checks every session not yet monitored (after the fill and the last MONITORED
session), in date order, with the same rule and the same events (one MONITORED per session, the
EXIT_FILLED dated on the breach session). The stop rule itself now lives once, in
`desk.paper.execution.stop_rule`, used by both the manual monitor (`check_stop_on_session`) and
Strategy 0. The session loops stay separate: Strategy 0 records a MONITORED event per global session
from its registered EQ/BE/BZ bar, the manual monitor scans the symbol's EQ history. An exit ORDER
needs a run, so a 10-session time exit after a skipped night is ordered at the next run, as live
would, with `ordered_late_by_sessions` on the event and a "Time-limit exits ordered late" line in the
brief. Unchanged for a normal night: when today's bar is missing the time check waits, as before.
Tests (`tests/test_strategy0_engine.py::SkippedSessionMonitoringTest`): a stop touched or gapped on a
skipped day with the price recovering the next day, every session monitored once across a skipped
night, the late time exit; all four fail with the pre-fix engine. Replay of all six Strategy 0 runs
with the new code on temporary copies: position events (259) and decision contracts (248)
identical; operational records identical except that run 1's lacks the `candidate_order` key v3's
code adds (pre-existing since e36ac7c, not this fix). Manual monitor (P8-054), checked and unchanged:
stops catch up the same way; its time exit fills at the first open after the horizon even when the
run before that open was missed, which live trading could not do (reported to the user). Commit 72d2947.

## P8-054 - desk monitor checked a manual stop on the run date's session only

**Severity.** Medium. **Status.** Closed — fixed 2026-10-11 (user approval); no record affected.

Raised by the user: manual positions were monitored only when someone ran `desk monitor`, and
`run_monitor` checked each open trade's stop against one session, the run date's
(`check_stop_on_session(..., run_date, ...)`). After a forgotten evening, a stop hit on the missed
day was never found if the next session recovered above the stop, and was filled on the wrong day
at the wrong price if it did not. The time exit (horizon) was never automated at all. Medium: a risk
control could silently fail; no manual trade has existed yet (production `paper_trade_events` has 0
rows), so nothing was affected.

Fix: `desk.monitor.first_mechanical_exit` checks every session from the entry session through the
run date in date order, with the stop in force on each date, and returns the first mechanical exit:
the stop (gap at the open, else touch at the stop, the existing rule) or the time exit at the open
of the first session after both the thesis horizon and the entry session (only that open counts on
that session; an open through the stop is reported as a stop gap). A trade with no linked thesis
keeps its stop and has no time exit. The nightly gained a `manual_monitor` step (after
`auto_paper`, before `brief`) running `desk monitor` for the latest session; the brief shows its
report (exits, pending opens/closes, open positions, what changed). Targets and the evidence, risk
and portfolio exits stay the user's judgement. Tests: `tests/test_desk_monitor_catchup.py` (8 cases;
all 7 behavioural ones fail with the old one-session rule restored), `tests/test_desk_brief.py`
(nightly step order and call, brief section). `tests/test_share_basis_structural.py`'s fixture thesis
horizon moved from 2021-12-31 to 2026-12-31: that share-basis scenario is set in 2026 and the
stale fixture date now (correctly) triggers the time exit it does not exercise.

## P8-055 - nightly tests depended on the machine's real battery level

**Severity.** Low. **Status.** Closed — introduced by P8-053 (2026-10-07), fixed 2026-10-11.

P8-053's guard reads the live power status in `weekly_ingest.main()`. Three test harnesses that
call `main()` did not isolate it, so they passed while the laptop was on AC power and, on
2026-10-11 with it on battery at 21%, five tests failed (four in `test_ingestion_progress.py`, one
in `test_desk_brief.py`; the guard correctly skipped every step). Fixed by patching
`power_status` in those harnesses (`tests/test_ingestion_progress.py`, `tests/test_desk_brief.py`,
`tests/test_isin_map_operations.py`); the affected modules (95 tests) then passed with the laptop
still on battery at 21%. Found 2026-10-12: those failing tests' skip notices also reached the real
`logs/brief_2026-10-11.txt` (the default folder of `record_skipped_run`, which they did not patch),
six WARN notices dated a Sunday on which no run happened; their log lines went to the tests'
temporary log, so `logs/weekly_ingest.log` is clean. The isolation fix prevents a recurrence; the
file is left in place for the user to decide.

**Follow-up, 2026-10-12 (user direction).** The file was moved, not deleted, to
`logs/_quarantine/brief_2026-10-11.txt` with a one-line `NOTE.txt` citing P8-055. Tests now never
write into the real `logs/` folder, the same rule the databases follow: `shared/log_paths.py` is the
one place the folder is resolved (`weekly_ingest.LOG_PATH`, `desk.backups.EVENT_PATH`,
`desk.ingestion_health.LOG_PATH`, and the brief writers' default folder), and `tests/__init__.py`
points it at a fresh temporary directory before any test module imports a writer (discovery
imports `tests/test_000_logs_isolation.py` first). `tests/test_zzz_real_logs_untouched.py`, last in
discovery, fails if the real folder changed during the run, excluding only the file this process's
own output is redirected into. Checked: a probe file written into the real folder during a run makes
it fail; the P8-055 scenario (a low-battery skip with only the log path patched) now lands in the
temporary folder, and that regression test fails with the isolation switched off.

## P8-053 - the nightly run could be skipped silently on battery

**Severity.** Low. **Status.** Closed — fixed 2026-10-07 (user approval for both changes).

The 2026-10-06 18:00 run never started: the laptop was asleep (Modern Standby 15:41-19:26) and on
battery, and the scheduled task kept Windows' default "start only on AC power", which also blocked
missed-start recovery after the machine woke. Nothing recorded the miss (Task Scheduler's history
log is disabled; the script logs nothing before it starts); it was found only because the user asked.
Low: the data catch up on the next run, and a manual run that evening decided 2026-10-06 normally;
without one, that date would have had no desk scan, no Strategy 0 decisions and no brief.

Fix: the task may start on battery (`DisallowStartIfOnBatteries` true -> false, the only change in
the exported XML; wake-to-run and missed-start recovery unchanged). `scripts/weekly_ingest.py` skips
the run on battery below 30% (`MIN_BATTERY_PERCENT`, read with GetSystemPowerStatus), writing a WARN
to the log and to the day's brief (`desk.brief.record_skipped_run`, never replacing a brief); the
health line reports the skip without counting it as a run. Exactly 30%, AC power, or an unreadable
status all run. Tests: `tests/test_ingestion_progress.py::LowBatteryGuardTest` (skip, threshold
and unknown cases, health line, Windows structure parsing) and
`tests/test_desk_brief.py::SkippedRunBriefTest`. Follow-up the same day (user approval): "stop if
the computer switches to battery power" turned off too (`StopIfGoingOnBatteries` true -> false, the
only XML change), so a run started on AC power is no longer stopped when the charger is pulled.

## P8-050 - the nightly brief reports its own run as never finished

**Severity.** Low. **Status.** Open. Found 2026-10-05 in the first brief written by the nightly.

`step_brief` runs as step 11 of 12, before `weekly_ingest` writes the run's finish line, and the
brief's data-health section uses `ingestion_health_line`, which (by P8-045's rule) reports any
start later than the latest finished run as unfinished. Every nightly brief therefore describes the
run that is writing it as "never finished (no matching finish recorded; may still be running)" and
reports the previous run as the last one. `logs/brief_2026-10-05.txt`: "last run
2026-10-03T05:54:29... overall=WARN...; started 2026-10-05T18:00:01..., never finished", while that
run finished at 18:51:11 with overall=OK (`desk status` afterwards: "last run
2026-10-05T18:00:01... (0d ago), overall=OK"). Display only: no gate or kill switch reads this
line. Proposed fix: when the brief is written inside the nightly, label that run as in progress
with the step statuses logged so far; keep P8-045's rule for any other unmatched start.

**Fix, 2026-10-06 (user approval: "fix both").**
**Status.** Closed — fixed; first live brief with it is tonight's.
`weekly_ingest` holds the running run's start while its steps run and passes it to the brief
(`write_brief(current_run_start=...)`); `ingestion_health_line(current_run_start)` reports that run
as "this run (started ...) is in progress: N steps logged so far, all OK" (or the non-OK steps),
followed by the previous finished run, and never as unfinished. Called without it (`desk status`,
an outside observer) the line is unchanged, and any other unmatched start keeps P8-045's rule.
Tests: `tests/test_ingestion_progress.py` (own run in progress while the outside view still says
unfinished; an earlier interruption and a WARN step still reported; the log unchanged) and
`tests/test_desk_brief.py` (the nightly passes its own start to the brief).

## P8-051 - desk status shows only the manual book's open risk and positions

**Severity.** Low. **Status.** Open. Found 2026-10-05 after the first Strategy 0 run.

`cmd_status` prints `_open_risk_used_inr` (manual `paper_trade_events` only) as "Open risk used"
and the manual open trade IDs as "Open positions", without saying so; Strategy 0's book
(`strategy_paper_events`) is not shown. After tonight's run `desk status` printed "Open risk used:
0.00 / 25000.00" and "Open positions: []", while the brief shows Strategy 0 at Rs 24,764.32 of
Rs 25,000.00 with two pending entries (5PAISA, AUBANK). Display only: each book has its own budget
and Strategy 0 sized against its own running total (`budget_used_before_inr` in its
`strategy_paper_events`), so no gate is wrong. Proposed fix: label the existing lines as the
manual book and add a Strategy 0 line from the latest `strategy_runs` record, as the brief does.

**Fix, 2026-10-06 (user approval: "desk status should show Strategy 0's book alongside the manual
one, clearly labelled, with no P&L").**
**Status.** Closed — fixed and checked against the production store.
`desk.brief.open_risk_lines`, shared by the brief and `desk status`: "Open risk by book (Strategy 0:
stress loss; manual: entry-to-stop risk)", a Strategy 0 line as of its latest run (version, open
risk of its budget, each held position's symbol, state, accepting version and decision date; no
prices, no P&L), the manual line, and the seal line. Production `desk status` now prints
"Strategy 0 (after its 2026-10-05 run, version 2): Rs 24,764.32 of Rs 25,000.00; 2 positions open,
pending or exiting: 5PAISA PENDING_ENTRY (v2, decided 2026-10-05), AUBANK PENDING_ENTRY (v2, decided
2026-10-05)" above the manual line. Test: `tests/test_desk_brief.py` (both books labelled in `desk
status`; no limit price or P&L text; the old unlabelled lines gone).



## P8-061 - manual time exits were filled retroactively after a missed run

**Severity.** Medium. **Status.** Fixed 2026-10-13, Part A1.
`first_mechanical_exit` used the first session after the horizon even if no run had
placed an exit order. Unlike a standing stop, this order could not have existed.
The monitor now appends one TIME_EXIT_ORDERED journal event on the next run at or
after the horizon; only a later session can fill it. Missed-session stop checks
remain in date order. The brief shows the order date and delay in trading sessions.
Production manual paper_trade_events count was 0 (read-only check); no records changed.
Regression evidence: tests.test_desk_monitor_catchup and tests.test_desk_brief:
21 tests in 12.733s, OK. Full-suite evidence is in the session handoff.


## P8-062 - morning recovery waits for a bhavcopy that cannot yet exist

**Severity.** Medium. **Status.** Fixed 2026-10-13, Part A2.
The weekday-only same-day retry step could wait before today's market close,
including after midnight, delaying recovery past Strategy 0's 09:00 cutoff.
It now requires the run to have started on today's weekday at/after 15:30 IST.
Otherwise it logs why and returns before a request or sleep. Original run-start
is used even if earlier steps cross close or midnight. Forward holiday dates are
not available; the weekday limitation remains explicit in OPERATIONS.md.
Re-verification: 19 targeted tests in 2.861s, OK; full-suite result in HANDOFF.md.


## P8-063 - nightly health display tolerated a week of missed runs

**Severity.** Low. **Status.** Fixed 2026-10-13, Part A3.
The health line reused Strategy 0's registered seven-calendar-day stale threshold.
Brief/status now use a separate previous-weekday display threshold on the last
finished run's IST finish date; the registered constant stays 7, with no version
change. No forward holiday calendar exists; conservative holiday false positives
remain documented. Tests cover weekends, missed weekdays, in-progress runs and
UTC/IST finish dates: 35 targeted tests in 1.049s, OK. Full suite in HANDOFF.md.


## P8-064 - paper exits can fill on an all-day locked lower circuit

**Severity.** Medium. **Status.** Closed — fixed 2026-10-14 (user approval), both books; see the fix below.
The shared stop_rule(opening, low, stop) has no execution-availability input. Both
manual monitoring and Strategy 0 accept its fill without consulting bands/queues.
Verified synthetic example: previous close 100, band 5%, OHLC all 95, stop 98;
stop_rule(95, 95, 98) returns ('stop_gap', 95), even under the specified no-buyers
condition. Next-open exit paths likewise assume liquidity. This is paper execution
correctness; no live broker execution exists and production outcomes were not read.
Proposed fix, not implemented: detect a possibly locked raw bar against the exact
applicable preceding-session band and verified reference price/tick, defer the exit
append-only and retain risk until a later executable session. Daily volume alone
cannot prove buyers/queue priority; missing/dynamic bands and corporate-action
ambiguity stay UNKNOWN. Full proposal and tests: docs/desk/locked_circuit_review_20261013.md.
Re-verification: direct synthetic shared-rule call reproduced the fill; both callers
and pending-exit paths inspected. No engine change or outcome backfill authorized.
Buy side added 2026-10-13 (user request): the registered limit entry (`limit_fill`,
both books) also fills a paper buy at the open on an all-day upper lock whenever the
limit is at or above the locked price; synthetic calls with limit 102 filled at 102
and at 101 on flat bars. Proposed detection (POSSIBLY_LOCKED_UPPER, no fill, reason
LOCKED_UPPER; unverifiable band on a flat bar = LOCK_STATUS_UNKNOWN) in the same
review document. Document only; engine unchanged.

**Fix, 2026-10-14 (user approval: "approved for implementation, both books. No new Strategy 0
version").** `desk/paper/locks.py` holds the rule for both books. The band in force on session S
is the price-band report dated the session before S, the reference price is that session's raw
close of the same series, and the limits are reference x (1 -/+ band %). A bar is LOCKED_LOWER or
LOCKED_UPPER when all four raw prices sit within one tick of that limit; that needs a FIXED band,
the reference, S's tick size and no corporate action with ex-date S. When any of those is unknown
and the bar is exactly flat, it is FLAT_UNKNOWN and assumed locked (user rule: "no buy, and no sell
that session").
- Sells: a stop hit, a pending exit order (time limit, kill switch, unadjustable action) or a
  manual close on a session that blocks sells does not fill; the stop or order is tried again on
  the next session under the same rule. Strategy 0 records why on that session's MONITORED event
  (`stop_hit_not_filled`, or `exit_deferred` with the lock evidence) and in the brief; the manual
  monitor lists it in its report and the brief; a manual close appends PAPER_CLOSE_DEFERRED.
- Buys: no fill at an upper lock (or a flat bar with its limits unknown); a normal no-fill
  (`LOCKED_UPPER`/`POSSIBLY_LOCKED`), which the fill-failure switch counts as an attempt.
- The limit is capped at the next session's upper limit when that band was recorded before the
  decision (Strategy 0: `limit_cap` on the acceptance, only when it binds; sizing stays at the
  uncapped limit, so quantity is unchanged or smaller in effect). When the band was not known at
  decision time and the limit turns out above it, the order is rejected: a normal no-fill
  (`REJECTED`). The capped order follows the same day-limit rule (`limit_order_fill`).
- Tick sizes are recorded daily, point-in-time, from Angel One's public scrip master
  (`desk/tick_sizes.py`, table `tick_sizes`, nightly step `tick_sizes` after `circuit_bands`): the
  master's `tick_size` is in paise and it is generated each morning (Last-Modified 08:00 IST), so
  a copy is dated to that session. Plain HTTPS, no login, no SDK. Nothing before the first
  recording is known, so until then any flat bar is treated as possibly locked.
- Records change only when a rule binds: every new field is written only on a blocked, capped or
  rejected fill. Replay of all seven Strategy 0 runs on temporary copies, with the band reports
  each run could see: identical (the only difference is run 1's missing `candidate_order` key,
  pre-existing since v3).
- Tests: `tests/test_paper_locks.py` (14: tick master; lower, upper, touch-only and flat-elsewhere
  bars; unknown band, dynamic band, unknown tick, ex-date reset; the buy cap's decision-time rule;
  Strategy 0 stop at a lower lock then re-checked, flat-unknown sell, pending exit deferred then
  filled, upper-lock no-fill counted as an attempt, the cap, the rejection; manual monitor, close
  and open). The 13 behavioural tests fail with the lock and cap checks switched off.

## P8-065 - draft broker guard rejected an unrelated local variable

**Severity.** Low. **Status.** Fixed 2026-10-13, B2 before commit.
The first AST guard treated every name `position` as a forbidden SDK reference,
including local arithmetic variables. Restrict detection to function calls,
attributes, imports, dynamic attribute references and endpoint strings.
Re-verification: repository-wide AST scan and adversarial guard cases pass in
the 25-test offline Angel run (0.847s, OK). No runtime code was affected.

## P8-066 - draft broker session cleanup missed two failure paths

**Severity.** Medium. **Status.** Fixed 2026-10-13, B2 before commit.
Checking as-of before session expiry retained an expired token when yesterday's
as-of was supplied; login could also mint a token before its implicit profile
request failed. Check expiry and clear first; best-effort revoke a partial login
then always clear memory. Tests cover both paths, in the 25-test offline run
(0.847s, OK). No authenticated call or real credential was used.

## P8-067 - HTTP debug logging could expose broker authentication

**Severity.** Medium. **Status.** Fixed 2026-10-13, B2 before commit.
Muting SDK logging alone left externally configured HTTP debug logging enabled;
the SDK profile query contains the refresh token. The wrapper now temporarily
disables standard logging and HTTP connection debug output around authenticated
REST transport and restores settings in finally. Websocket trace is disabled.
Regression exercises noisy transport logging and restoration, in the 25-test
offline run (0.847s, OK). No actual secret exposure occurred.

## P8-068 - SDK isolation did not cover DNS, bytecode and feed debug logging

**Severity.** Medium. **Status.** Fixed 2026-10-13, user follow-up 1.
The draft import interceptor blocked ipify but left the SDK's hostname lookup
and hardware-address discovery active. Normal Python imports can write bytecode;
the WebSocket transport did not share REST's configured-log suppression.
SDK loading now disables bytecode writes temporarily and intercepts hostname and
hardware probes as well as public-IP HTTP. The SDK constructor remains bypassed.
Both IP headers are explicitly 127.0.0.1 and MAC is 00:00:00:00:00:00, replacing
the SDK's hardcoded public-IP fallback. Actual account/IP compatibility is unverified.
Streaming now uses the same logging/debug suppression, restored on exit.
The terminal script disables bytecode before importing project modules; use -B
for arbitrary wrapper imports too (a module cannot prevent its own prior import
cache write). No package install or authenticated/network call occurred.
Evidence: 28 offline Angel tests in 1.343s, OK; guarded fresh-process import,
mocked import probes and entire login/quote/candles/feed/logout flow. Seven
distinct synthetic secrets and request headers do not escape into logs/output;
file/folder access guards remain untriggered. The downloaded pinned SDK wheel's
actual import/construction also passed an audit-hook ban on network/filesystem
writes with optional logging/feed modules stubbed. Full suite in HANDOFF.md.

## P8-069 - a filing landing during the refresh voids the whole night's disclosure certification

**Severity.** Medium. **Status.** Closed — fixed 2026-10-14 (user approval); found 2026-10-13 from that night's WARN.
The 13 Oct nightly's `announcements_recent` step reported "WARN announcements bulk
2026-10-12..2026-10-13: AnnouncementFetchError". Not a timeout or an HTTP failure: the run's own
request trace (`data/raw/announcement_runs/20261013T123643127766/requests.json`) shows all 8
requests (cookie, identity, two whole windows, four split checks) returned HTTP 200 in 0.18-1.79 s.
Re-running the checks on the saved responses, without any request, shows the cause:
`fetch_checked_window` compares a whole window with the same dates fetched in halves. The whole
12-13 Oct response (requested 18:06:58 IST) held 965 announcements, the two single-day responses
576 + 388 = 964. The one difference is a 13 Oct filing published at 18:06:54, four seconds before
the whole request, missing from the 13 Oct response requested two seconds after it (whose latest
filing was 18:05:15). No row differed in content. The check raised "Whole/split announcement
windows differ", the window failed and the receipt was PARTIAL.

Effect: a decision for D needs the source complete through D-1 (`required_through`), and a receipt
recorded on D certifies at most D-1 (P8-049). The 12 Oct half matched exactly, so a COMPLETE
receipt would have certified 12 Oct; the PARTIAL one certified nothing. All 52 candidates of
13 Oct failed G2 ("disclosures is UNKNOWN"), Strategy 0 had nothing to decide, and the brief said
only "NO TRADE ... a normal outcome". It is not a burn-in gap: Strategy 0 ran and decided.
13 Oct's announcements were not stored (the failed window is not ingested).

Catch-up: the data, yes. The bulk state keeps `last_complete` at 2026-10-12, so the 14 Oct run
re-reads 5-14 Oct and stores 13 Oct's filings if its own checks pass. The decisions, no: 13 Oct is
decided once. The same race can recur on any night: the current IST day's filings keep arriving
during an evening run (P8-049 measured 25-38% after 18:07), and the single-day query evidently
lagged the whole-window query by several seconds. First occurrence in eight bulk refreshes.

New failure mode: the consistency check cannot tell a still-open day's late arrivals from a real
inconsistency, and one current-day difference fails earlier, completed days. Proposed fix (not
implemented): compare whole and split responses only for completed IST days (publication before
the current day), which is all a receipt recorded tonight can certify anyway; ingest the current
day's rows without certifying them; keep the check's failure for any difference on a completed
day. Optionally retry a failed comparison once after a pause. The brief should also say why no
candidate passed (G2 UNKNOWN from a PARTIAL receipt) instead of only "a normal outcome".
No request was made to test any of this.

**Fix, 2026-10-14 (user approval: "the whole/split comparison certifies only completed days,
through D-1, matching P8-049").** `fetch_checked_window(..., open_day=...)` compares only filings
published before the IST day in progress; that day's filings from both responses are stored (the
whole response plus any filing only the split saw), and the night's receipt, recorded that day,
certifies through D-1 at most (P8-049, unchanged). A difference on a completed day still fails the
window. The refresh passes `open_day=market_today()` and records `open_day` and `open_day_rows` on
the window that contains it. Re-run offline on the saved 13 Oct responses, the new rule passes that
night's window (965 filings stored). Tests: `tests/test_announcements_open_day.py` (a synthetic
filing arriving between the two requests, which still fails under the old rule; a split-only filing
stored; a completed-day difference still failing; the whole night COMPLETE with its receipt
certifying 12 Oct, not 13 Oct). Note appended, never an edit (user decision): the 52 opportunity
log rows of 13 Oct carry INCOMPLETE_DISCLOSURE_EVIDENCE citing P8-069, and Strategy 0's 13 Oct
run an `S0_RUN_ANNOTATED` journal entry (`scripts/desk_annotate_p8069.py`, idempotent, dry-run on
a temporary copy first); `desk status` and every brief show "Strategy 0 burn-in dates decided on
incomplete disclosure data". Nothing is re-decided. The brief's bare "NO TRADE ... a normal
outcome" on such a night is still not explained there (reported, not changed).

## P8-070 - Praman's store lacks five real trading sessions, so windows across them silently shorten

**Severity.** Medium. **Status.** Open — found 2026-10-14 while building T1 inputs; fix awaits the user.
The official NIFTY 50/NIFTY 500/India VIX histories (niftyindices, downloaded for T1 phase 2) list
sessions that the bhavcopy store has no rows for at all:
- 2022-08-08, a regular weekday session (8 Aug 2022; 9 Aug was the holiday). Not recorded as a
  gap in any log or document.
- Four weekend special sessions: 2020-02-01 and 2025-02-01 (Budget-day Saturdays, full sessions),
  2023-11-12 (Muhurat) and 2024-03-02 (special Saturday session). The daily ingestion skips weekends
  locally (OPERATIONS.md, "Daily ingestion"), so these were never requested. The store does hold four
  other weekend sessions (2019-10-27, 2020-11-14, 2024-01-20, 2024-05-18), so weekends are not
  excluded by design everywhere.
Effect: anything counting "global sessions" from the store (the forensic catalogue's windows and
labels, the Desk's ATR and lookbacks, T1) treats the day before and the day after as adjacent, so a
20-session window spans 21 real sessions. T1 treats 2022-08-08 as a session with every stock missing
(windows across it are UNKNOWN) and leaves the four weekend sessions out of its calendar; both are
in the T1 coverage report for review. Nothing is changed in the store. Possible fix (needs approval:
a Praman store write and NSE requests): fetch the five dated bhavcopy files, check each file's own
date (P2-003), ingest them append-only, and say how the frozen pipeline's pinned inputs are affected.
*Note 2026-10-18 (append-only):* evidence and options for T1 in
docs/desk/t1_coverage_decisions_20261018.md. 2022-08-08 was a session (index histories, 675
announcements, and the 10 Aug file's previous close differs from 5 Aug's for 1,774 of 1,811 symbols);
why the load missed it is still unknown. The four stored weekend sessions came from the following
weekday holiday's file. Still open; nothing changed in the store.

## P8-071 - the Angel connection test exited with code 1 and said nothing

**Severity.** Low. **Status.** Closed — fixed 2026-10-14 (user report: "exits silently with code 1").
`scripts/angel_connection_test.py` caught every failure and returned 1 without printing, so the
user's window (no `smartapi-python`, no `ANGEL_API_KEY`) gave no clue. Its own test asserted the
silence (`test_failure_still_logs_out_without_printing_exception` checked for empty output), so the
defect was encoded in a test. The wrapper's errors were already fixed, credential-free messages.
Fix: every run ends with one plain line. A setup check runs before any login (missing or wrong
library: "Stopped before login: ..."), each wrapper error maps to a plain reason ("ANGEL_API_KEY is
not set in this window: see setup step 2", "Angel library not installed ...: see setup step 1",
login failure with the unverified IP headers named), other errors give only their type, and success
ends "Connection test completed: ...". New `--check` mode: `desk.angel_market_data.check_setup()`
reports the Python, the pinned library and its two dependencies and loads the SDK offline, without
logging in and without reading `ANGEL_API_KEY` (a test fails if it touches the variable). Run on the
nightly's Python: "Setup ready for the connection test." Tests: `tests/test_angel_connection_test.py`
(8). The pinned library was installed the same day after a dry run showed only two new packages.


## P8-072 through P8-075 - Angel parsing, diagnosis and bounded smoke tests

Found/fixed 2026-10-14; offline verification only. Full evidence and limitations:
[Angel diagnosis](desk/angel_diagnosis_20261014.md).

- **P8-072 (Medium):** malformed master rows aborted all mapping; broad exception handlers
  erased transport/HTTP/JSON/API categories. Type-check records, reject ambiguous identities,
  and preserve only enumerated diagnostics. Reproduced with mocks before fixing.
- **P8-073 (Low):** hardcoded smoke-test candle date; replace with a recent completed SBIN EQ
  session evidenced by the knowledge-filtered local store. No weekday-only calendar assumption.
  *Reversed 2026-10-14 by user decision (P8-078): the fixed 2026-09-01 date is back, with an optional
  `--candle-date` limited to stored sessions before the forward window.*
- **P8-074 (Medium):** feed failures lost their category; recv() hid control-frame identity and
  delayed outer deadline checks on control-only traffic. Use recv_data(control_frame=True),
  distinguish closure/parsing/callback/interruption, and preserve automatic protocol PONG.
- **P8-075 (Low):** capacity evaluation lacked an explicit minimum-duration check. Pass required
  duration from the runner, retain safe error metadata, and provide an isolated --only-25 run.

Regression coverage: tests/test_angel_diagnostics.py plus the existing Angel suites.
The exact causes of the previously observed live master/candle/239-second feed failures remain
unresolved because the old errors discarded the evidence. Authenticated re-verification is pending
separate user-run tests; no claim of restored live reliability follows from mocked tests.


## P8-076 - historical HTTP 403 discarded available broker error classifications

**Severity:** Low (diagnostics). **Status:** Fixed offline; historical access itself unresolved.
The 2026-10-14 user test succeeded through quote retrieval, then candles returned HTTP 403.
The dispatcher rejected non-200 responses before inspecting SDK error envelopes: explicit
PermissionException, TokenException and InputException all became generic HTTP failures.
Reproduced offline before the change. Now only exact allowlisted indicators become fixed
categories; ambiguous 403 remains unclassified, status is retained, and no response text or
sensitive headers escape. Local candle dates are distinguished from broker date-format errors.
No retry, credential/header workaround, endpoint change, or policy bypass. Request comparison
with SDK 1.5.5 found no wire-format defect explaining the denial. App entitlement, registered
static IP and gateway restrictions require account-side verification. Details and evidence:
[historical 403 investigation](desk/angel_candle_403_20261014.md).

## P8-077 - the feed sent no protocol PING and kept no record of how it closed

**Severity.** Medium. **Status.** Closed — fixed 2026-10-14 (user request); the 239-second drop's cause is still unknown.
The wrapper sent only Angel's documented text heartbeat ("ping" every 10 seconds; the WebSocket 2.0
page says "The client must send a heartbeat message for each WebSocket connection every 30 sec to
keep the connection alive", request "ping", response "pong"). The SDK it wraps also sends a
protocol PING frame every 10 seconds (smartWebSocketV2.connect: run_forever(ping_interval=10)), and
the wrapper did not. When the feed ended it recorded only a category, so the 239-second drop on
2026-10-14 left no evidence of who closed it or how idle it was.
Fix: every 10 seconds the feed sends a protocol PING and the text "ping"; websocket-client 1.8.0
answers the server's PINGs itself (recv_data_frame), and its plain socket never closes the
connection on a late PONG (only WebSocketApp.run_forever with ping_timeout does). A text "pong"
(any case or spacing) is counted, never a tick or an error; any other text frame still stops the
feed (api_rejection) and is counted. Every exit records a close summary with numbers and fixed
words only: who closed (server, client, connection_lost), the close code, the reason's length (its
text is never kept), seconds connected, since the last message, since the last PING sent and PONG
received, since the last text ping and text pong, and frame counts. It rides on the error
(`error_details(...)['stream']`) and is returned on a normal finish; the connection test prints it
as one "Feed close:" line and the capacity probe stores it per tier.
The code does not explain the 239-second drop: that run was busy (7,252 ticks over 25 symbols,
longest silence 1.8 s), so an idle timeout is unlikely, and the text heartbeat already met Angel's
documented rule. One remaining possibility is a text frame other than "pong", which the old code
also treated as fatal; the new summary would show it. Tests: tests/test_angel_feed_keepalive.py (6:
a fake server that drops quiet clients keeps our feed for 10 fake minutes and drops a feed without
protocol PINGs at 30 s; server PINGs, text and protocol pongs never ticks; the close summary's fields
with a secret close reason withheld; the library's own PING answer and lack of a pong timeout).

## P8-078 - Angel's own throttling reply was reported as an unexplained 403, and the candle date moved

**Severity.** Low (diagnostics). **Status.** Closed — fixed 2026-10-14 (user decision); the 11:22 403's cause is still unknown.
At 11:22 on 2026-10-14 the candle call returned HTTP 403 and the test could not say whether the
reply was Angel's documented throttling phrase: 967729e turned every non-200 reply into an "http"
failure without looking at it, and Codex's later fix (P8-076) matched only one exact, case-sensitive,
non-JSON form. The same run also asked for a different date from the 08:10 run that worked
(2026-10-13 instead of 2026-09-01), because P8-073 had replaced the fixed date with the latest stored
session, so two things changed at once.
Fix: the wrapper recognises Angel's two phrases, "Access denied because of exceeding access rate"
(docs FAQ; forum topic 5595) and "Access denied because of exceeding rate limit" (docs RateLimit
page), whole and ignoring case, spacing and a final full stop, in the reply or its JSON "message",
and reports `RATE_LIMITED (Angel's "exceeding access rate" reply)`; the reply is never printed or
kept, and any other 403 stays unclassified. Angel's error-code page (docs/Exceptions, 61 codes) has
no rate-limit code, so none was added. **P8-073 is reversed by the user's decision:** the connection
test asks for the fixed 2026-09-01 again; `--candle-date YYYY-MM-DD` accepts only a stored SBIN EQ
session before the forward window's start. It prints one summary line instead of every bar, and a
candle failure says whether the market was open at that moment. Request unchanged; one request, no
retry. Tests: tests/test_angel_candle_403.py (phrases in body and JSON, a phrase plus anything else
is not throttling, the two failure lines with a fixed clock), tests/test_angel_connection_test.py
(date validation, the summary of the 08:10 pattern: 361 bars, 15:15-15:28 missing),
tests/test_angel_diagnostics.py. Evidence: docs/desk/angel_candle_403_20261014.md.

## P8-079 - a feed we stopped ourselves read as if Angel had closed it

**Severity.** Low (diagnostics). **Status.** Closed — fixed 2026-10-14 (user request).
When the wrapper stopped the feed itself (an unexpected text message, an unreadable tick, a tick
handler error, or the time being up), the close summary said only "closed by client", and the
capacity probe's tier line read "feed closed by client after N s (code none)", which looks like a
connection that ended on its own. The summary now carries `stopped_because`, a fixed label
(unexpected text message, unreadable tick, tick handler error, time up, interrupted), and
`stopped_message_bytes`, the length of the message that caused it, never its text. The tier line
says "feed stopped by us: unexpected text message (N bytes, text never shown) after S s"; a close by
the server keeps "feed closed by server after S s (code C)". The connection test's "Feed close:" line
says "(we stopped it: ...)". Tests: tests/test_angel_feed_keepalive.py,
tests/test_angel_stream_capacity_test.py (FeedCloseTextTest), tests/test_angel_connection_test.py.

## P8-080 - an unexplained 403 left no trace of what kind of reply it was

**Severity.** Low (diagnostics). **Status.** Closed — fixed 2026-10-14 (user request).
An HTTP 403 that matched no known indicator became "Access denied; cause unclassified" and nothing
else, so a later run could not say whether Angel had answered with JSON, an HTML gateway page or a
line of text. Such a 403 now carries its shape only: kind (JSON, HTML, plain text or empty), its
length in bytes, and an error code only when the JSON's error-code field is exactly two capital
letters and four digits (Angel's pattern, e.g. AB1004). Never any message text. It is in
`error_details(...)['reply']`; the connection test prints "Reply: <kind>, <n> bytes, error code
<code> | no Angel error code (text never shown)." before its stop line. Throttling replies and
classified denials carry no shape. Tests: tests/test_angel_candle_403.py.

## P8-081 - the capacity probe hid why it stopped when setup was incomplete

**Severity.** Low (usability). **Status.** Closed — fixed 2026-10-14 (user report).
On 2026-10-14 at 14:59 and 15:01 the user's probe runs stopped within a second, before any feed,
because ANGEL_API_KEY was not set; the summary and the last line said only "failed or interrupted
(no detail is printed)". The probe now gives the connection test's fixed reasons (one owner,
`stop_reason` in scripts/angel_connection_test.py) with the stage: for example "failed at login:
ANGEL_API_KEY is not set in this window: see setup step 2". A missing or wrong SDK is refused before
login with the connection test's words. The reasons are fixed text and hold no secrets; an unexpected
exception gives only its type. Tests: tests/test_angel_stream_capacity_test.py.

## P8-082 - a price-band list published after the 18:00 nightly was never fetched

**Severity.** Medium (a lock input left UNKNOWN for good). **Status.** Closed — fixed 2026-10-14 (user request; Part B3).
On 2026-10-13 the nightly started at 18:00 and its circuit_bands step asked for
`sec_list_13102026.csv` at 18:07:58; NSE answered 404, so the bands for 14 Oct stayed UNKNOWN (the
step WARNed, as designed). The URL and file name were right: NSE's report metadata names the same
file ("CM - Price Band complete list", content/equities/). The timing was the problem: NSE publishes
no time for the list (its "Daily review of Price Bands" and "price band changes" pages, read
2026-10-14, give none), and the lists' Last-Modified times in the Desk store were 17:55 to 19:39 IST
from 1 to 12 Oct (earlier probes: 17:10 to 17:58). The step then never asked for 13 Oct again: it
only ever requested the store's latest trading date, so one early night lost that list permanently.
Fix, inside the existing step: with no explicit range it now asks for the latest trading date plus
the store's sessions after the latest stored list (at most 5), so a list missed one night is
fetched the next. Each list keeps its own Last-Modified date as its knowledge date (fetch_report
already refuses any other), so an earlier run's view is never changed; recorded_at shows the late
arrival. A catch-up list NSE has since rewritten, or that no longer parses, stays UNKNOWN with a WARN
instead of stopping tonight's list. The brief's Data health gains a price-band line: "Price bands:
WARN, no NSE list dated D yet; the next session's bands are UNKNOWN, so a flat bar counts as possibly
locked" (FLAT_UNKNOWN, P8-064), or "OK, list dated D (N rows, published HH:MM IST)". Not changed: the
18:00 start; a same-evening wait for a late list would lengthen the nightly and is left to the user.
Tests: tests/test_price_band_catch_up.py.

## P8-083 - a price-band list fetched late was known from its publication date, not from when we had it

**Severity.** Medium (look-ahead risk). **Status.** Closed — fixed 2026-10-14 (user check of P8-082).
A list's knowledge date was its Last-Modified date. With P8-082's catch-up, a list for 13 Oct fetched
on the night of 14 Oct would have been stored as known on 13 Oct, so anything reading bands directly
by knowledge date (the gate engine, the lock rule, the shadow analysis; only the replay views filter
on recorded_at) could have seen it in a decision dated 13 Oct, although no 13 Oct run had it. Now the
knowledge date is the later of the Last-Modified date and the date we fetched the list, and fetching
the same file again adds nothing, so its first knowledge date stands. Same-evening fetches are
unchanged. Rows already stored are untouched (append-only); a future explicit backfill of old lists
will be known only from the day it runs. Tests: tests/test_circuit_bands.py,
tests/test_price_band_catch_up.py. P8-082's entry describes the earlier rule.

## P8-084 - a late-fetched source-dated row is visible to a later recomputation of an earlier decision

**Severity.** Medium (look-ahead in recomputations, not in live decisions). **Status.** Closed — found
2026-10-18 (user's knowledge-date audit); replay paths fixed the same day (user decision, below).
Bhavcopy, announcements, equity identities, corporate actions, ASM/GSM lists and tick sizes take their
knowledge date from the source (a Last-Modified date, a filing or circular date, an archive's trading
day, an ex-date), not from when Praman fetched the file. A file fetched late (for example the bhavcopy
for 15 and 16 Oct, which Monday's run will fetch after two battery skips) is therefore known, to any
reader that filters on knowledge date alone, from a date before Praman had it. Live nightly decisions
cannot see it (it is not yet stored when they run) and audit replays filter on recorded_at, but a later
live recomputation of an earlier-dated decision (`desk assess --as-of <past date>`, research such as the
shadow analysis and the T1 build) can. Price bands (P8-083) and announcement receipts (P8-049) are dated
by when Praman had them. Details: docs/desk/knowledge_date_audit_20261018.md. A rule for research
backfills is to be decided when one is needed (user, 2026-10-18).
*Fix 2026-10-18 (user decision: two clocks; status now Closed for the replay paths).* No stored date
was rewritten. Research reads keep the source's date. Replays of Praman's own decisions read only rows
stored by the decision time: `desk assess --as-of <past session>` and `desk scan --date <past
session>` now read through replay connections limited to the end of that session's IST day
(`desk.lib.store.decision_watermark`); records still go to the live Desk store, and scan's fill
observations still read live. The audit replay already used recorded watermarks; it now reads the
decision's own thesis by id. Tests: tests/test_decision_clock.py (a bhavcopy for 15 and 16 Oct stored
on 19 Oct is invisible to replays dated 15 and 16 Oct). The reader table is in the audit note.

## P8-085 - T1 treats date-only evidence as known the same session, and its ISIN snapshots carry no publication evidence

**Severity.** Medium (research inputs; no outcome has been computed). **Status.** Resolved 2026-10-18
under user-approved addendum 3; originally found while checking draft (d).
The pre-registration says: "When only a proven publication DATE exists, make the value available at
the next market session, not at an invented same-day time. If even the publication date cannot be
proven, knowledge begins at first observed retrieval and earlier historical values remain UNKNOWN."
The T1 build (desk/t1/panel.py, written by Claude on 2026-10-13) does otherwise in two places:
- **Stock bars.** The store keeps each bar's knowledge as a date (the IST date of the archive file's
  Last-Modified); the time of day was seen at download but not kept. The build makes a bar usable at
  the decision on its own session ("known the same day" in the coverage report), not at the next.
- **ISIN snapshots.** The sidecars record the requested date, the file name and the download time
  (October 2026), no Last-Modified. The build uses each snapshot from its own session, with neither
  publication evidence nor an ASSUMPTION label.
The draft addendum's (d) refers to "the evidence or ASSUMPTION labels the build already carries";
for these two inputs there are none, so it was not recorded. The rehearsal of 2026-10-18 ran the
build as it is. Options for the user: state labelled ASSUMPTIONS (same session, or next session) for
the bars and the snapshots, as addendum 2 did for index closes; or apply the strict rule (bars from
the next session; snapshots unknown until retrieved, which leaves no eligible stock-day).


**P8-085 resolution (18 October 2026).** Addendum 3 records same-session EQ-bar
availability as an ASSUMPTION, preserving current-close eligibility, ATR and
breadth definitions; stored later knowledge dates still block earlier inputs.
Index/VIX remain D-1. ISIN snapshots now start strictly after their file date,
with an explicit ASSUMPTION and no use of October download dates. Last known
identity continues forward. No durable data was changed. The audit lists every
same-session stock-bar use: `docs/desk/t1_timing_audit_20261018.md`.
Re-verification: 51 focused T1 tests pass, including snapshot-date exclusion,
next-session activation across non-sessions, carry-forward, default weekend
exclusion, purge/empty bootstrap dates, the 5% boundary, and the full-run seal.
Second random-label rehearsal: `docs/desk/t1_rehearsal2_20261018.md`; 34.1 seconds,
2,091,749,376 bytes peak; no real outcome read/computed. The stock-bar assumption
is not claimed to be verified publication evidence. Real development run remains
unwired; firewall and Strategy 0 seal unchanged.

## P8-086 - Nightly brief understates screening scope and omits screening rejection counts

**Severity.** Low (display only). **Status.** Resolved 2026-10-18.
The old "Passed evidence/data checks" label described only part of screening:
`desk/gates/engine.py` requires G1-G6 to pass. The brief now names all six gates
and adds rejection counts from each candidate's stored gate results. Fixed
category labels use `shadow_analysis.reason_key`; raw reason texts, percentages
and rupee amounts are never interpolated. Counts are deduplicated per candidate
and category; gate counts can overlap. The stressed-exit "of which" count is
the intersection with the turnover-cap group, not an assumed subset.
No decision, gate, Strategy 0 or persistence logic changed.
Verification: 16 brief tests pass, including five new cases for exact formatting,
deduplication/multiple gates, subset semantics, safe fallback labels and G7/G8
exclusion. Read-only rendering for 14 October matches the user's requested line
exactly; no brief file was written or overwritten.

## P8-087 - T1 development loaders read later dates before restricting the panel

**Severity.** Medium (research isolation). **Status.** Resolved 2026-10-18; found 2026-10-18
during preflight for the user's once-only development evaluation; evaluation not started.
At code `9dea1e8b785b4c4aeb0c044e8774478c3210ea7d`, `desk/t1/panel.py:56`
queries the next 40 event dates after `end`, even when `end` is 2024-12-31.
`desk/t1/inputs.py` loads all cached index histories/snapshots without a date bound,
and `panel.snapshot_identities` reads every cached ISIN snapshot, including later
files. Restricting the assembled panel to development dates does not prevent those
reads. The outcome reader checks the assembled panel, not these earlier source reads.
The second rehearsal did not compute real outcomes, but its loader was not isolated
from later source dates. Its reported development metrics do not prove read isolation.

The user's current requirement is stronger: no 2025 date read for inputs or outcomes.
Stopped before any real evaluation. Evidence is static source inspection; did not
execute the unrestricted loaders to reproduce the unwanted read. A repair must
bound source access before loading, omit post-development calendar queries, and
test the boundary before a separately authorised run. No repair or retry performed.

Repair authorised separately: all T1 file loaders now select date-bounded payloads
before opening them, skip wholly later files, and refuse mixed ranges. The shared
read guard refuses an end after 2024-12-31 before SQL or file reads. ISIN selection
precedes even sidecar access. The post-end session query is removed; stock/action
SQL is bounded by event and knowledge dates, and the ancillary late-session query
ends in 2024. Source ledgers are read only as file-selection metadata, not market
observations. Historical payloads are separate yearly files, so no mixed payload
had to be opened. Six boundary tests include later-file traps and a SQL trap that
fail on the original implementation; 57 focused tests pass. No outcome access.
Third rehearsal at fcf9711 established exact equality of every saved analytical
field with the second rehearsal (docs/desk/t1_rehearsal3_20261018.md). Additional
fixture testing proves a changed future tail cannot change any prior feature or
threshold. Final pre-evaluation validation: 61 focused tests; full suite 1,039
tests in 263.863 seconds, OK. P8-088 warnings recur and remain unfixed.

## P8-088 - Test suite emits unclosed SQLite connection ResourceWarnings

**Severity / priority.** Low. **Status.** Open, logged 2026-10-18 at the user's request.
The full suite at `dea07c7` passed 1,029 tests in 231.224 seconds (exit 0), but Python
3.13 emitted `ResourceWarning: unclosed database in <sqlite3.Connection ...>`.
Warnings surfaced during garbage collection in unittest.mock, bitemporal guards,
Desk schema/fixtures and other modules. Those locations do not establish where
each connection was opened; exact owners remain untraced. No failing assertion
or demonstrated durable-store damage. Investigate test-fixture connection cleanup
in a later task. No fix, warning suppression or rerun performed for this item.
