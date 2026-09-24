# Defect Register

Every defect this project finds in itself, with an ID, root cause, fix, and re-verification
evidence — including ones introduced by this project's own code, per CLAUDE.md's verification
honesty rule.

| ID | Found | Severity | What it was | Status |
|---|---|---|---|---|
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
| P8-007 | Ph. 10 housekeeping (Amendment 3's pre-specified split/bonus scan, run as a mechanism check against historical data) | **Critical, found not fixed** | This project's `corporate_actions` ingestion never captures ETF unit splits. A pre-specified scan for one-day returns shaped like a common unadjusted split/bonus ratio, run against the EXISTING historical catalogue as a mechanism check, found 96 hits, **zero** explained by an existing `BONUS`/`SPLIT` record — a large cluster are ETFs (`HDFCNIFETF`, `HDFCSENSEX`, `ICICI500`, `KOTAKGOLD`, etc.) sharing near-identical dates and near-exact ratios. Traced directly, not inferred from the shape alone: `HDFCNIFETF`'s raw bhavcopy close fell from 1628.18 (2021-02-16) to 162.44 (2021-02-17) — a real 10:1 unit split, `series='EQ'` (the same series equities use, so not a series-filtering gap), absent from `corporate_actions` entirely. This is the exact false-positive shape CLAUDE.md's own "Hard blocker" section already warns adjusted-return code about, occurring for real, for a whole instrument class this project's ingestion has never covered. | **Scoped precisely (`docs/phase10_p8007_scoping.md`), still found not fixed.** Full breakdown of the 96, using NSE's own live ETF list and a live per-symbol corporate-actions query (not our own store): 32 ETF-confirmed, 3 confirmed missed equity actions (each a distinct root cause — a regex gap, an unhandled action type, and an unresolved downstream drop later explained by `P8-008`), 61 with no corresponding live NSE record at all (price-move candidates). Root cause for ETFs confirmed directly (3 traced cases, 2 fund houses): NSE's corporate-actions endpoint does not carry ETF unit splits at all — a source-coverage gap, not a bug in our fetch/parse/tier logic. **ETF share: 3.91% TRAIN, 10.30% HOLD-OUT (growing); 43.90% of every `UNKNOWN_COVERAGE` event is ETF vs. 0.00% of every other disclosure tier** — the model's largest-magnitude coefficient substantially encodes instrument type, confirmed. **Contamination quantified and found immaterial**: 342 events (~0.4-0.46%), Phase 8b's feature AUC table re-run excluding them shifts every number under 0.003 — no conclusion changes. Still not fixed: identifying/ingesting a real ETF-split data source, and the equity-side gaps this scoping pass found (see `P8-008`). **Corrections pass (`docs/phase10_p8007_corrections.md`) supersedes the ETF-share numbers with a more complete ISIN-based method: `UNKNOWN_COVERAGE` fund-unit share revised to 61.22% (from the 43.90% live-list-only lower bound); shape-scan re-run on the equity-only population + corrected actions drops 96 hits to 55 (41 fund-unit-excluded, 3 explained by corrected actions, 52 persist unexplained). **Amendment 4 prep (`docs/phase10_amendment4_prep.md`): the equity-only rule is now APPLIED, not just measured** (excludes INF-prefix and unresolved ISINs; 3414 EQ symbols -> 2827 kept, catalogue 75,300 -> 70,638 events) and the refit CONFIRMS the hypothesis directly: `disclosure_UNKNOWN_COVERAGE`'s coefficient shrinks from -0.396295 to -0.159399 (less than half) once the fund-unit confound is removed — the largest-magnitude coefficient substantially WAS instrument type, not disclosure behavior, now measured post-correction rather than only inferred. Still not built: a real ETF-split ingestion source (out of scope -- ETFs are now excluded from the catalogue entirely, not adjusted for, per the applied rule). |
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
