"""Phase 4: ASM/GSM surveillance-flag ingestion. Fixture data only, network-free -- reproduces the
real annexure/circular shapes found during source evaluation (T1_SURV66001/T2_SURV66016
reconciliation, the 2019 Annexure I-B IBC carve-out, the 2023 "Short - Term ASM Framework"
exclusion-title variant, real GSM PDF wording) as small, explicit fixtures rather than depending on
cached network data.
"""
from __future__ import annotations
import unittest

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import read_as_of
from src.ingestion.nse_market_data.asm import (
    ASM_LT, ASM_ST, ENTRY, EXIT, STAGE_CHANGE,
    ingest_asm_circular, is_periodic_asm_subject, mechanism_from_subject,
    parse_circular_workbook, parse_circular_zip_bytes, parse_sectioned_annexure, to_iso_date,
)
from src.ingestion.nse_market_data.gsm import (
    GSM, classify_gsm_subject, ingest_gsm_circular, is_gsm_subject, parse_gsm_pdf_text,
)
from datetime import date
from unittest.mock import MagicMock

# ---------- ASM: subject-line classification ----------

class IsPeriodicAsmSubjectTest(unittest.TestCase):
    def test_clean_lt_subject(self):
        self.assertTrue(is_periodic_asm_subject("Applicability of Additional Surveillance Measure (ASM)"))

    def test_clean_st_subject(self):
        self.assertTrue(is_periodic_asm_subject("Applicability of Short-Term Additional Surveillance Measure (ST-ASM)"))

    def test_real_typo_variants(self):
        # Real, observed titling typos across 7 years of circulars (phase4 doc).
        self.assertTrue(is_periodic_asm_subject("Applicabilty of Additional Surveillance Measure (ASM)"))
        self.assertTrue(is_periodic_asm_subject("Applicability of Aaddtional Surveillance Measure (ASM)"))
        self.assertTrue(is_periodic_asm_subject("Applicability of Additional Surveillanvce Measure (ASM)"))

    def test_surveillance_word_dropped_entirely_p4_012(self):
        """P4-012: real circulars (SURV49425, SURV60822, SURV63984, SURV69359 -- four real
        occurrences of the same shape, spread 2021-2025) drop the word "Surveillance" entirely
        rather than misspelling it -- "Applicability of Short-Term Additional Measure (ST-ASM)".
        This has to be recovered via the "(ASM)"/"(ST-ASM)" abbreviation, not the surve stem,
        since surve never appears in the text at all. SURV63984 specifically is where 63MOONS's
        real ASM exit lived; silently skipping it produced an apparent re-entry with no exit a
        month later in the store."""
        self.assertTrue(is_periodic_asm_subject("Applicability of Short-Term Additional Measure (ST-ASM)"))
        self.assertTrue(is_periodic_asm_subject("Applicability of Additional Measure (ASM)"))

    def test_denylist_never_matches_a_real_excluded_mechanism_subject(self):
        """P4-013: `is_periodic_asm_subject` is now a denylist (attempt everything unless a known
        category matches), not the allowlist P4-007/P4-012 patched. This asserts, with REAL
        subject strings pulled from the cached 7,936-circular index, that none of the excluded
        mechanisms are wrongly accepted -- a property that should stay asserted as the denylist
        evolves, not left a fact nobody checks again. (ICA has no standalone circular subject of
        its own -- it only appears as a section title inside an otherwise-real ASM circular,
        already covered by ParseSectionedAnnexureTest -- so it isn't represented here.)"""
        real_excluded_subjects = [
            "Applicability of Enhanced Surveillance Measure (ESM)",
            "List of Securities Moving to Stage II of Graded Surveillance Measure (GSM)",
            "Applicability of Additional Surveillance Measure under IBC",
            "Applicability of Surveillance Measure in respect of companies with high 'Encumbrance' as per Reg.28(3) of SEBI (SAST) Regulation 2011",
            "Applicability of Surveillance Measure in respect of companies with high promoter pledge",
            "Surveillance measures for Deep Out-of-The-Money (OTM) contracts",
            "Order Based Surveillance Measure - Persistent Noise Creators",
            "Trade for Trade",
            "Securities moving out Trade for Trade segment",
            "Applicability of Additional Surveillance Measure under ICA",
            "Applicability of Long-Term Additional Surveillance Measure (LT-ASM) Framework on Equity Derivatives",
            "Applicability of Long-Term Additional Surveillance Measure (LT-ASM) Framework on Public Sector Undertaking (PSU) Companies",
        ]
        for subject in real_excluded_subjects:
            self.assertFalse(is_periodic_asm_subject(subject), f"wrongly accepted: {subject!r}")

    def test_denylist_typo_tolerance_p4_013(self):
        """Real typo variants of denylist categories found while dry-running the new denylist
        against the full cached index -- each one would have leaked through as unwanted noise if
        left unfixed, the same class of gap (a specific misspelling not anticipated) as the
        allowlist's own P4-006/P4-007 typos, just lower-stakes on the deny side (noise, not lost
        data)."""
        self.assertFalse(is_periodic_asm_subject("Confimatory Order in matter of Capital Stroke Investment Services Pvt. Ltd."))
        self.assertFalse(is_periodic_asm_subject("Coriggendum in the matter India Infotech and Software Limited"))
        self.assertFalse(is_periodic_asm_subject("Cautionary Messages on Trading Terminal"))
        self.assertFalse(is_periodic_asm_subject("Applicability of Surveillance Measure in respect of companies with high 'Encumberance' as per Reg. 28(3) of SEBI (SAST) Regulation 2011"))
        self.assertFalse(is_periodic_asm_subject("Placing of Orders at Unrealistic Prices - Commodity Derivatives"))
        self.assertFalse(is_periodic_asm_subject("SAT orders in respect of Aspire Emerging Fund and Leman Diversified Fund"))
        self.assertFalse(is_periodic_asm_subject("Order in respect of Arth Stock broking Private Limited"))
        self.assertFalse(is_periodic_asm_subject("Revision of Order-to-Trade Ratio (OTR) framework"))
        self.assertFalse(is_periodic_asm_subject("Increase in margin for Non-F&O Stocks in Cash Market"))
        self.assertFalse(is_periodic_asm_subject("Framework on Material Price Movement (in Equity Cash Markets) with respect to Rumour Verification by Listed Entities"))
        self.assertFalse(is_periodic_asm_subject("Consolidated Penalty Structure for Surveillance"))
        self.assertFalse(is_periodic_asm_subject("Directions under Section 11(4)(b) and 11b of the Sceurities and Exchange Board of India Act, 1992 against Akar Laminators Limited and its Directors"))
        self.assertFalse(is_periodic_asm_subject("Extension of Surveillance Measures on Public Sector Undertaking (PSU) Companies"))
        self.assertFalse(is_periodic_asm_subject("Measures for Enhancing Trading Convenience and Strengthening Risk Monitoring in Equity Derivatives"))

    def test_denylist_accepts_real_typo_variants_the_old_allowlist_missed(self):
        """P4-013: real circulars the old allowlist wrongly rejected, confirmed by the pre-rebuild
        dry run against the full cached index -- must be accepted under the new denylist since
        nothing about them matches any exclusion category."""
        self.assertTrue(is_periodic_asm_subject("Applicability of Short- Term Additional Surveillance (ST-ASM)"))
        self.assertTrue(is_periodic_asm_subject("Applicability of Short-Term Additional Surveillance (ST-ASM)"))
        self.assertTrue(is_periodic_asm_subject("Application of Additional Surveillance Measure (ASM)"))
        self.assertTrue(is_periodic_asm_subject("Appllicability of Additional Surveillance Measure (ASM)"))

    def test_gsm_excluded(self):
        self.assertFalse(is_periodic_asm_subject("List of Securities Moving to Stage II of Graded Surveillance Measure (GSM)"))

    def test_ibc_excluded(self):
        self.assertFalse(is_periodic_asm_subject("Applicability of ASM for Companies relating to Insolvency and Bankruptcy Code (IBC)"))

    def test_promoter_pledge_excluded(self):
        self.assertFalse(is_periodic_asm_subject("Surveillance Measure - Promoter Pledge/Encumbrance"))

    def test_esm_excluded_including_the_real_enhnaced_typo(self):
        """P4-007: real circular SURV64061's subject was 'Applicability of Enhnaced Surveillance
        Measure (ESM)' -- 'Enhnaced' is a genuine typo of 'Enhanced' that the "enhanced" exclusion
        stem alone does not catch. Caught instead via the bare '(ESM)' abbreviation, which a typo
        is very unlikely to hit."""
        self.assertFalse(is_periodic_asm_subject("Applicability of Enhanced Surveillance Measure (ESM)"))
        self.assertFalse(is_periodic_asm_subject("Applicability of Enhnaced Surveillance Measure (ESM)"))

    def test_mechanism_from_subject(self):
        self.assertEqual(mechanism_from_subject("Applicability of Additional Surveillance Measure (ASM)"), ASM_LT)
        self.assertEqual(mechanism_from_subject("Applicability of Short-Term Additional Surveillance Measure (ST-ASM)"), ASM_ST)

class ToIsoDateTest(unittest.TestCase):
    def test_single_space(self):
        self.assertEqual(to_iso_date("January 08, 2025"), "2025-01-08")

    def test_double_space_and_trailing_period(self):
        self.assertEqual(to_iso_date("November 01, 2019."), "2019-11-01")

    def test_no_space_after_prefix_stripped_already(self):
        self.assertEqual(to_iso_date("July 05, 2023"), "2023-07-05")

    def test_abbreviated_comma_less_month_p4_006(self):
        """P4-006: real circulars roughly SURV52458-58318 (mid-2022 to mid-2023) spell the w.e.f.
        date as 'Apr 03 2023' -- abbreviated month, no comma -- instead of 'April 03, 2023'.
        Confirmed against 232 distinct real failing date strings, all this one shape."""
        self.assertEqual(to_iso_date("Apr 03 2023"), "2023-04-03")
        self.assertEqual(to_iso_date("Dec 13 2022"), "2022-12-13")
        self.assertEqual(to_iso_date("Jan 02 2023"), "2023-01-02")

# ---------- ASM: section-aware annexure parsing ----------

def _row(*cells):
    return tuple(cells)

class ParseSectionedAnnexureTest(unittest.TestCase):
    def test_entry_transition_exclusion_and_footnotes(self):
        """Reproduces the real T2_SURV66016 Annexure I/II shape: two ENTRY rows (one with a
        per-symbol '*' footnote), one section-level '^'-footnoted STAGE_CHANGE, one plain
        STAGE_CHANGE, and Nil placeholders for every other stage-transition section."""
        rows = [
            _row("List of securities shortlisted in Long - Term ASM Framework Stage - I w.e.f. January 08, 2025"),
            _row(None, None, None, None),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row(1, "EPACK", "EPACK Durable Limited", "INE0G5901015"),
            _row(2, "ITI", "ITI Limited*", "INE248A01017"),
            _row("* Moved from STASM to LTASM framework"),
            _row(None, None, None, None),
            _row("List of securities shortlisted to move from Long - Term ASM Framework Stage - I to Stage - IV ^ w.e.f. January 08, 2025"),
            _row(None, None, None, None),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row(1, "SAGILITY", "Sagility India Limited", "INE0W2G01015"),
            _row("^ Scrips shortlisted as per Crtieria VII shall be shifted from Rolling Settlement to Trade for Trade"),
            _row(None, None, None, None),
            _row("List of securities shortlisted to move from Long - Term ASM Framework Stage - III to Stage - IV w.e.f. January 08, 2025"),
            _row(None, None, None, None),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row(1, "GVT&D", "GE Vernova T&D India Limited", "INE200A01026"),
            _row(None, None, None, None),
            _row("List of securities shortlisted to move from Long - Term ASM Framework Stage - II to Stage - III w.e.f. January 08, 2025"),
            _row(None, None, None, None),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row("", "", "Nil", ""),
        ]
        events, unparsed = parse_sectioned_annexure(rows, ASM_LT, "SURV66016", "2025-01-07")
        self.assertEqual(unparsed, [])

        by_symbol = {e["symbol"]: e for e in events}
        self.assertEqual(set(by_symbol), {"EPACK", "ITI", "SAGILITY", "GVT&D"})

        self.assertEqual(by_symbol["EPACK"]["action_type"], ENTRY)
        self.assertIsNone(by_symbol["EPACK"]["from_stage"])
        self.assertEqual(by_symbol["EPACK"]["to_stage"], "I")
        self.assertIsNone(by_symbol["EPACK"]["details"])
        self.assertEqual(by_symbol["EPACK"]["event_date"], "2025-01-08")

        self.assertEqual(by_symbol["ITI"]["details"], "Moved from STASM to LTASM framework")

        self.assertEqual(by_symbol["SAGILITY"]["action_type"], STAGE_CHANGE)
        self.assertEqual((by_symbol["SAGILITY"]["from_stage"], by_symbol["SAGILITY"]["to_stage"]), ("I", "IV"))
        self.assertIn("Crtieria VII", by_symbol["SAGILITY"]["details"])

        self.assertEqual((by_symbol["GVT&D"]["from_stage"], by_symbol["GVT&D"]["to_stage"]), ("III", "IV"))
        self.assertIsNone(by_symbol["GVT&D"]["details"])

    def test_nil_row_produces_no_event(self):
        rows = [
            _row("List of securities shortlisted in Long - Term ASM Framework Stage - II w.e.f. January 08, 2025"),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row("", "", "Nil", ""),
        ]
        events, unparsed = parse_sectioned_annexure(rows, ASM_LT, "SURV66016", "2025-01-07")
        self.assertEqual(events, [])
        self.assertEqual(unparsed, [])

    def test_2019_style_nil_row_in_sr_no_column(self):
        """2019/2021-era Nil rows put 'Nil' in the Sr. No. column, not the Security Name column."""
        rows = [
            _row("List of securities shortlisted to move from Long - Term ASM Framework Stage - II to Stage - III w.e.f.  November 01, 2019."),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN", "From Series", "To Series"),
            _row("Nil", None, None, None, None, None),
        ]
        events, unparsed = parse_sectioned_annexure(rows, ASM_LT, "SURV42545", "2019-10-31")
        self.assertEqual(events, [])
        self.assertEqual(unparsed, [])

    def test_ibc_section_reported_as_unparsed_not_dropped(self):
        rows = [
            _row("List of securities shortlisted in ASM for Companies relating to the Insolvency Resolution Process (IRP) as per Insolvency and Bankruptcy Code (IBC) w.e.f November 01, 2019"),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row(1, "ASSAMCO", "Assam Company India Limited", "INE442A01024"),
        ]
        events, unparsed = parse_sectioned_annexure(rows, ASM_LT, "SURV42545", "2019-10-31")
        self.assertEqual(events, [])  # IBC carve-out is out of scope, not silently ingested as a bare ASM entry
        self.assertEqual(len(unparsed), 1)
        self.assertIn("Insolvency", unparsed[0])

    def test_footnote_row_in_the_symbol_column_not_parsed_as_a_symbol(self):
        """P4-010: real circular SURV49783's Annexure I-A has the footnote-definition row's text in
        the SYMBOL column position, not column 0 -- (None, '* Moved from STASM to LTASM
        framework', None, None) -- because its Sr.No. cell is blank. A column-0-only footnote
        check missed this row entirely, and it was ingested as a bogus symbol literally named
        '* Moved from STASM to LTASM framework'."""
        rows = [
            _row("List of securities shortlisted in Long - Term ASM Framework Stage - I w.e.f. October 01, 2021."),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row(1, "MARATHON *", "Marathon Nextgen Realty Limited", "INE182D01020"),
            _row(None, "* Moved from STASM to LTASM framework", None, None),
        ]
        events, unparsed = parse_sectioned_annexure(rows, ASM_LT, "SURV49783", "2021-09-30")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["symbol"], "MARATHON")
        self.assertEqual(events[0]["details"], "Moved from STASM to LTASM framework")

    def test_marker_on_symbol_with_hash_character(self):
        """P4-011: real circular SURV49784 has 'IMAGICAA #' as the literal Symbol-column value,
        footnoted by a row reading '# As per BSE'. The marker must be stripped from the symbol
        (never stored as part of the business key) and used to look up the right footnote."""
        rows = [
            _row("List of securities shortlisted in Short - Term ASM Framework Stage - I w.e.f. October 01, 2021."),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row(1, "MAXVIL", "Max Ventures and Industries Limited", "INE154U01015"),
            _row(2, "IMAGICAA #", "Imagicaaworld Entertainment Limited", "INE172N01012"),
            _row(None, "# As per BSE", None, None),
        ]
        events, unparsed = parse_sectioned_annexure(rows, ASM_ST, "SURV49784", "2021-09-30")
        by_symbol = {e["symbol"]: e for e in events}
        self.assertEqual(set(by_symbol), {"MAXVIL", "IMAGICAA"})
        self.assertEqual(by_symbol["IMAGICAA"]["details"], "As per BSE")
        self.assertIsNone(by_symbol["MAXVIL"]["details"])

    def test_marked_symbol_matches_unmarked_symbol_across_circulars(self):
        """The whole point of stripping the marker: the same real company must resolve to the
        identical symbol whether or not a given circular happened to mark it, so lifecycle
        continuity (ENTRY...EXIT for the same symbol) isn't broken by marker presence alone."""
        marked = [
            _row("List of securities to be excluded from ASM Framework w.e.f. October 01, 2021."),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row(4, "MARATHON *", "Marathon Nextgen Realty Limited", "INE182D01020"),
            _row(None, "* Moved from STASM to LTASM framework", None, None),
        ]
        unmarked = [
            _row("List of securities shortlisted in Long - Term ASM Framework Stage - I w.e.f. October 01, 2021."),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row(1, "MARATHON", "Marathon Nextgen Realty Limited", "INE182D01020"),
        ]
        events1, _ = parse_sectioned_annexure(marked, ASM_ST, "SURV49784", "2021-09-30")
        events2, _ = parse_sectioned_annexure(unmarked, ASM_LT, "SURV49783", "2021-09-30")
        self.assertEqual(events1[0]["symbol"], events2[0]["symbol"])

    def test_short_term_exclusion_title_variant(self):
        """P4-001: the 2023-era ST-ASM annexure phrases exclusion as 'excluded from Short - Term
        ASM Framework', not the bare 'excluded from ASM Framework' seen in other eras."""
        rows = [
            _row("List of securities to be excluded from Short - Term ASM Framework w.e.f. July 05, 2023."),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row(1, "SOMECOMP", "Some Company Limited", "INE000000001"),
        ]
        events, unparsed = parse_sectioned_annexure(rows, ASM_ST, "SURV57402", "2023-07-04")
        self.assertEqual(unparsed, [])
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["action_type"], EXIT)
        self.assertEqual(events[0]["mechanism"], ASM_ST)

    def test_exclusion_without_term_wording_uses_subject_mechanism(self):
        rows = [
            _row("List of securities to be excluded from ASM Framework w.e.f. January 08, 2025"),
            _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
            _row(1, "SOMECOMP", "Some Company Limited", "INE000000001"),
        ]
        events, unparsed = parse_sectioned_annexure(rows, ASM_LT, "SURV66016", "2025-01-07")
        self.assertEqual(events[0]["mechanism"], ASM_LT)

class ParseCircularWorkbookTest(unittest.TestCase):
    def test_skips_consolidated_sheets(self):
        class FakeSheet:
            def __init__(self, rows):
                self._rows = rows
            def iter_rows(self, values_only=True):
                return iter(self._rows)

        class FakeWorkbook:
            sheetnames = ["Annexure I", "Consolidated ASM"]
            def __getitem__(self, name):
                if name == "Annexure I":
                    return FakeSheet([
                        _row("List of securities shortlisted in Long - Term ASM Framework Stage - I w.e.f. January 08, 2025"),
                        _row("Sr. No.", "Symbol", "Security Name", "ISIN"),
                        _row(1, "ABC", "ABC Limited", "INE000000000"),
                    ])
                raise AssertionError("Consolidated sheet must never be parsed for events")

        events, unparsed = parse_circular_workbook(FakeWorkbook(), "Applicability of Additional Surveillance Measure (ASM)", "SURV1", "2025-01-01")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["symbol"], "ABC")

    def test_annexure_nested_inside_a_zip_subfolder_is_still_found(self):
        """P4-007: real circular SURV64061's zip contained 'SURV64061/Annexure.xlsx' -- nested in
        a subfolder, not at the zip root. A full-path 'startswith(\"annexure\")' check misses this
        entirely; matching must be on the basename."""
        import zipfile
        from io import BytesIO
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Annexure I"
        for row in [
            ("List of securities shortlisted in Long - Term ASM Framework Stage - I w.e.f. January 08, 2025",),
            ("Sr. No.", "Symbol", "Security Name", "ISIN"),
            (1, "ABC", "ABC Limited", "INE000000000"),
        ]:
            ws.append(row)
        xlsx_buf = BytesIO()
        wb.save(xlsx_buf)

        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("SURV64061/Annexure.xlsx", xlsx_buf.getvalue())
            zf.writestr("SURV64061/SURV64061.pdf", b"%PDF-1.4 fake cover letter")

        events, unparsed = parse_circular_zip_bytes(
            zip_buf.getvalue(), "Applicability of Additional Surveillance Measure (ASM)", "SURV64061", "2025-01-01")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["symbol"], "ABC")

# ---------- ASM: store write-through ----------

class IngestAsmCircularTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_writes_through_the_store_and_is_readable_as_of(self):
        import zipfile
        from io import BytesIO
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Annexure I"
        for row in [
            ("List of securities shortlisted in Long - Term ASM Framework Stage - I w.e.f. January 08, 2025",),
            ("Sr. No.", "Symbol", "Security Name", "ISIN"),
            (1, "ABC", "ABC Limited", "INE000000000"),
        ]:
            ws.append(row)
        xlsx_buf = BytesIO()
        wb.save(xlsx_buf)

        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("Annexure.xlsx", xlsx_buf.getvalue())

        from src.ingestion.nse_market_data.asm import AsmIngestionReport
        report = AsmIngestionReport()
        ingest_asm_circular(self.conn, "Applicability of Additional Surveillance Measure (ASM)",
                             "SURV1", "2025-01-01", zip_buf.getvalue(), report)

        self.assertEqual(report.circulars_processed, 1)
        self.assertEqual(report.event_counts, {"ASM_LT:ENTRY": 1})

        rows = read_as_of(self.conn, "surveillance_flags", as_of="2025-06-01")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "ABC")
        self.assertEqual(rows[0]["to_stage"], "I")

    def test_reingesting_the_same_circular_is_idempotent(self):
        """The retry pass re-fetches and re-ingests failed circulars against the SAME store a
        successful earlier attempt may have partially populated (a different circular in the same
        sweep, not this one -- but the retry script re-runs the whole sweep's failure list without
        tracking which of those failures ever reached write_facts). Re-ingesting a circular whose
        events are already present must not raise and must not create duplicate rows -- this is
        what makes "just re-run the failures" safe rather than something that could double-count."""
        import zipfile
        from io import BytesIO
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Annexure I"
        for row in [
            ("List of securities shortlisted in Long - Term ASM Framework Stage - I w.e.f. January 08, 2025",),
            ("Sr. No.", "Symbol", "Security Name", "ISIN"),
            (1, "ABC", "ABC Limited", "INE000000000"),
            (2, "DEF", "DEF Limited", "INE000000001"),
        ]:
            ws.append(row)
        xlsx_buf = BytesIO()
        wb.save(xlsx_buf)
        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("Annexure.xlsx", xlsx_buf.getvalue())
        zip_bytes = zip_buf.getvalue()

        from src.ingestion.nse_market_data.asm import AsmIngestionReport
        report1 = AsmIngestionReport()
        ingest_asm_circular(self.conn, "Applicability of Additional Surveillance Measure (ASM)",
                             "SURV1", "2025-01-01", zip_bytes, report1)
        count_after_first = self.conn.execute("SELECT COUNT(*) FROM surveillance_flags").fetchone()[0]
        self.assertEqual(count_after_first, 2)

        report2 = AsmIngestionReport()
        ingest_asm_circular(self.conn, "Applicability of Additional Surveillance Measure (ASM)",
                             "SURV1", "2025-01-01", zip_bytes, report2)  # identical re-ingest, must not raise
        count_after_second = self.conn.execute("SELECT COUNT(*) FROM surveillance_flags").fetchone()[0]
        self.assertEqual(count_after_second, 2, "re-ingesting the same circular must not create duplicate rows")
        self.assertEqual(report2.circulars_processed, 1, "a duplicate-only write still counts as a processed circular")
        self.assertEqual(report2.duplicate_events_skipped, 2, "both of the re-ingested circular's events must be reported as duplicate-skipped")

    def test_two_same_day_circulars_naming_the_same_symbol_is_tracked_as_a_duplicate_not_lost(self):
        """P4-009: real circulars SURV68086/SURV68088 (both ASM_LT, published the same day) both
        listed ICDSLTD -- a genuine same-day corrective/reissue circular pair, the same pattern
        already documented for corporate actions (KITEX). `write_facts` correctly stores only one
        row; `event_counts` alone (summed across both circulars' PARSED events) would overcount by
        one relative to the store -- `duplicate_events_skipped` is what makes the two numbers
        reconcile instead of silently disagreeing (the exact invariant P4-004/P4-005 established)."""
        import zipfile
        from io import BytesIO
        import openpyxl

        def make_zip(symbol: str) -> bytes:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Annexure I"
            for row in [
                ("List of securities shortlisted in Long - Term ASM Framework Stage - I w.e.f. May 21, 2025",),
                ("Sr. No.", "Symbol", "Security Name", "ISIN"),
                (1, symbol, f"{symbol} Limited", "INE000000000"),
            ]:
                ws.append(row)
            buf = BytesIO()
            wb.save(buf)
            zbuf = BytesIO()
            with zipfile.ZipFile(zbuf, "w") as zf:
                zf.writestr("Annexure.xlsx", buf.getvalue())
            return zbuf.getvalue()

        from src.ingestion.nse_market_data.asm import AsmIngestionReport
        report = AsmIngestionReport()
        ingest_asm_circular(self.conn, "Applicability of Additional Surveillance Measure (ASM)",
                             "SURV68086", "2025-05-20", make_zip("ICDSLTD"), report)
        ingest_asm_circular(self.conn, "Applicability of Additional Surveillance Measure (ASM)",
                             "SURV68088", "2025-05-20", make_zip("ICDSLTD"), report)  # same-day reissue

        store_count = self.conn.execute("SELECT COUNT(*) FROM surveillance_flags").fetchone()[0]
        self.assertEqual(store_count, 1)
        self.assertEqual(sum(report.event_counts.values()), 2)  # both circulars' events were parsed
        self.assertEqual(report.duplicate_events_skipped, 1)
        self.assertEqual(sum(report.event_counts.values()) - report.duplicate_events_skipped, store_count)

    def test_malformed_zip_is_counted_as_a_circular_failure_not_raised(self):
        from src.ingestion.nse_market_data.asm import AsmIngestionReport
        report = AsmIngestionReport()
        with self.assertRaises(Exception):
            # A caller-level sweep loop (fetch_and_ingest_asm_range) catches this; calling
            # ingest_asm_circular directly with garbage bytes still raises, by design --
            # only the network sweep loop is responsible for catching-and-logging.
            ingest_asm_circular(self.conn, "Applicability of Additional Surveillance Measure (ASM)",
                                 "SURVBAD", "2025-01-01", b"not a zip", report)

    def test_failed_write_is_never_counted_as_processed(self):
        """P4-005: a real DB whose surveillance_flags table predates the mechanism/action_type
        columns (a stale table, not a code bug) makes `write_facts` raise a plain sqlite3 error --
        this must propagate (not be swallowed here) and must NOT have already incremented
        circulars_processed, or a caller sweep loop's "processed" count silently overstates how
        much data actually reached the store."""
        import zipfile
        from io import BytesIO
        import openpyxl

        stale_conn = get_connection(":memory:")
        stale_conn.execute("""
            CREATE TABLE surveillance_flags (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL, stage TEXT NOT NULL,
                event_date TEXT NOT NULL, knowledge_date TEXT NOT NULL, source_file TEXT NOT NULL,
                recorded_at TEXT NOT NULL, UNIQUE (symbol, stage, event_date, knowledge_date)
            )
        """)  # the pre-Phase-4 placeholder shape, missing mechanism/action_type/etc.

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Annexure I"
        for row in [
            ("List of securities shortlisted in Long - Term ASM Framework Stage - I w.e.f. January 08, 2025",),
            ("Sr. No.", "Symbol", "Security Name", "ISIN"),
            (1, "ABC", "ABC Limited", "INE000000000"),
        ]:
            ws.append(row)
        xlsx_buf = BytesIO()
        wb.save(xlsx_buf)
        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("Annexure.xlsx", xlsx_buf.getvalue())

        from src.ingestion.nse_market_data.asm import AsmIngestionReport
        report = AsmIngestionReport()
        with self.assertRaises(Exception):
            ingest_asm_circular(stale_conn, "Applicability of Additional Surveillance Measure (ASM)",
                                 "SURV1", "2025-01-01", zip_buf.getvalue(), report)
        self.assertEqual(report.circulars_processed, 0)
        stale_conn.close()

# ---------- GSM: subject-line classification ----------

class ClassifyGsmSubjectTest(unittest.TestCase):
    def test_stage_move(self):
        self.assertTrue(is_gsm_subject("List of Securities Moving to Stage II of Graded Surveillance Measure (GSM)"))
        self.assertEqual(classify_gsm_subject("List of Securities Moving to Stage II of Graded Surveillance Measure (GSM)"), (ENTRY, "II"))

    def test_sage_typo_tolerated(self):
        self.assertEqual(classify_gsm_subject("List of Securities moving to Sage II of Graded Surveillance Measure(GSM)"), (ENTRY, "II"))

    def test_moving_out(self):
        self.assertEqual(classify_gsm_subject("List of securities moving out of Graded Surveillance Measure (GSM) - Update"), (EXIT, None))

    def test_periodic_relaxation_not_a_transition(self):
        self.assertIsNone(classify_gsm_subject("Graded Surveillance Measure (GSM) - Periodic relaxation of surveillance action"))

    def test_framework_update_not_a_transition(self):
        self.assertIsNone(classify_gsm_subject("Graded Surveillance Measure Framework - Update"))

# ---------- GSM: PDF-text parsing ----------

STAGE_MOVE_TEXT = """National Stock Exchange of India
Circular
Department: SURVEILLANCE
Download Ref No: NSE/SURV/65707 Date: December 20, 2024
Sub: List of Securities Moving to Stage II of Graded Surveillance Measure (GSM)
members are hereby requested to note that the following securities shall be moved to Stage II of GSM
with effect from December 23, 2024.
Sr. No. Symbol Security Name ISIN
1 GAYAPROJ GAYATRI PROJECTS LIMITED INE336H01023
Trading in the above-mentioned securities shall be available in Trade for Trade.
"""

MOVE_OUT_TEXT = """National Stock Exchange of India Limited
Circular
Department: SURVEILLANCE
Download Ref No: NSE/SURV/71691 Date: December 08, 2025
Sub: List of securities moving out of Graded Surveillance Measure (GSM) - Update
This is in furtherance to Exchange circular no. NSE/SURV/71670 dated December 05, 2025 on GSM
whereby it was informed that, the securities part of Annexure III of the said circular shall be moved
out of GSM framework w.e.f. December 09, 2025.
Sr. Price
No. Symbol Security Name ISIN Series band
1 BALKRISHNA BALKRISHNA PAPER MILLS LIMITED INE875R01011 EQ 20
2 FSC FUTURE SUPPLY CHAIN SOLUTIONS LIMITED* INE935Q01015 BZ 5
*Suspended
"""

class ParseGsmPdfTextTest(unittest.TestCase):
    def test_stage_move_template(self):
        events, reason = parse_gsm_pdf_text(STAGE_MOVE_TEXT, ENTRY, "II", "SURV65707")
        self.assertIsNone(reason)
        self.assertEqual(len(events), 1)
        e = events[0]
        self.assertEqual(e["symbol"], "GAYAPROJ")
        self.assertEqual(e["mechanism"], GSM)
        self.assertEqual(e["action_type"], ENTRY)
        self.assertEqual(e["to_stage"], "II")
        self.assertEqual(e["knowledge_date"], "2024-12-20")
        self.assertEqual(e["event_date"], "2024-12-23")

    def test_move_out_template_with_trailing_columns_and_footnote(self):
        """Real templates carry extra trailing columns (Series, Price band) after the ISIN, and a
        document-level '*' footnote that applies only to marked rows -- both must not break
        extraction."""
        events, reason = parse_gsm_pdf_text(MOVE_OUT_TEXT, EXIT, None, "SURV71691")
        self.assertIsNone(reason)
        by_symbol = {e["symbol"]: e for e in events}
        self.assertEqual(set(by_symbol), {"BALKRISHNA", "FSC"})
        self.assertEqual(by_symbol["BALKRISHNA"]["event_date"], "2025-12-09")
        self.assertIsNone(by_symbol["BALKRISHNA"]["details"])
        self.assertEqual(by_symbol["FSC"]["details"], "Suspended")
        self.assertIsNone(by_symbol["FSC"]["to_stage"])  # EXIT never carries a to_stage

    def test_digits_split_by_a_stray_space_are_collapsed_p4_008(self):
        """P4-008: real circulars SURV72963/SURV72867 (Feb 2026) extract with spurious whitespace
        INSIDE digit runs -- "February 2 5, 2026" for the 25th, "NSE/SURV/ 72963" -- a pdfplumber
        rendering artifact of that era's PDF, not a real gap in the source."""
        text = ("Sub: List of Securities Moving to Stage I I of Graded Surveillance Measure (GSM)\n"
                "Download Ref No: NSE/SURV/ 72963 Date: February 24, 2026\n"
                "members are hereby requested to note that the following securities shall be moved to "
                "Stage II of GSM with effect from February 2 5, 2026.\n"
                "Sr. No Symbol Security Name ISIN\n"
                "1 GLFL GUJARAT LEASE FINANCING LIMITED INE540A01017\n")
        events, reason = parse_gsm_pdf_text(text, ENTRY, "II", "SURV72963")
        self.assertIsNone(reason)
        self.assertEqual(events[0]["knowledge_date"], "2026-02-24")
        self.assertEqual(events[0]["event_date"], "2026-02-25")
        self.assertEqual(events[0]["symbol"], "GLFL")

    def test_with_effect_from_wrapped_across_a_line_break(self):
        """P4-003: real circular SURV71944 wraps mid-phrase -- "...GSM with\\neffect from
        December 23, 2025." -- not just mid-sentence like P4-002's case."""
        text = ("Sub: List of Securities Moving to Stage I of Graded Surveillance Measure (GSM)\n"
                "Date: December 22, 2025\n"
                "members are hereby requested to note that the following securities shall be moved to Stage I of GSM with\n"
                "effect from December 23, 2025.\n"
                "Sr. No Symbol Security Name ISIN\n"
                "1 SADBHAV SADBHAV ENGINEERING LIMITED INE226H01026\n")
        events, reason = parse_gsm_pdf_text(text, ENTRY, "I", "SURV71944")
        self.assertIsNone(reason)
        self.assertEqual(events[0]["event_date"], "2025-12-23")

    def test_missing_date_reported_as_failure_not_silently_skipped(self):
        events, reason = parse_gsm_pdf_text("Sub: List of Securities Moving to Stage I\nNo date here.", ENTRY, "I", "SURVX")
        self.assertEqual(events, [])
        self.assertIsNotNone(reason)

class IngestGsmCircularTest(unittest.TestCase):
    def setUp(self):
        self.conn = get_connection(":memory:")
        init_db(self.conn)

    def test_writes_through_the_store(self):
        from src.ingestion.nse_market_data.gsm import GsmIngestionReport
        report = GsmIngestionReport()
        ok = ingest_gsm_circular(self.conn, ENTRY, "II", "SURV65707", STAGE_MOVE_TEXT, report)
        self.assertTrue(ok)
        self.assertEqual(report.event_counts, {"GSM:ENTRY": 1})
        rows = read_as_of(self.conn, "surveillance_flags", as_of="2025-01-01")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["mechanism"], "GSM")

    def test_failed_write_is_never_counted_as_processed(self):
        """P4-005, GSM side of the same fix."""
        stale_conn = get_connection(":memory:")
        stale_conn.execute("""
            CREATE TABLE surveillance_flags (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL, stage TEXT NOT NULL,
                event_date TEXT NOT NULL, knowledge_date TEXT NOT NULL, source_file TEXT NOT NULL,
                recorded_at TEXT NOT NULL, UNIQUE (symbol, stage, event_date, knowledge_date)
            )
        """)
        from src.ingestion.nse_market_data.gsm import GsmIngestionReport
        report = GsmIngestionReport()
        with self.assertRaises(Exception):
            ingest_gsm_circular(stale_conn, ENTRY, "II", "SURV65707", STAGE_MOVE_TEXT, report)
        self.assertEqual(report.circulars_processed, 0)
        stale_conn.close()

# ---------- P8-004: fetch_circular_index must unwrap the real API's envelope shape ----------

# The real, live https://www.nseindia.com/api/circulars response, confirmed directly against the
# API (docs/DEFECT_REGISTER.md, P8-004): an envelope, not a bare list. Reproduced verbatim in
# shape (trimmed to 2 of the real 26 circulars returned for a real 2026-09 window).
REAL_CIRCULARS_ENVELOPE_SHAPE = {
    "data": [
        {"cirDate": "20260922", "circNumber": "76481", "sub": "Empanelment as Algo Provider",
         "circFilelink": "https://nsearchives.nseindia.com/content/circulars/INVG76481.pdf"},
        {"cirDate": "20260921", "circNumber": "76451", "sub": "Applicability of Enhanced Surveillance Measure (ESM)",
         "circFilelink": "https://nsearchives.nseindia.com/content/circulars/SURV76451.zip"},
    ],
    "fromDate": "12-09-2026", "toDate": "22-09-2026",
}

def _mock_session_returning(payload) -> MagicMock:
    session = MagicMock()
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    session.get.return_value = response
    return session

class FetchCircularIndexEnvelopeTest(unittest.TestCase):
    """P8-004: `for c in circulars` previously iterated the envelope dict's own keys (each a
    string) when the real API returned {"data": [...], "fromDate": ..., "toDate": ...} instead of
    a bare list -- caught only by an actual live network call, since this function was never
    exercised against real or realistically-shaped data anywhere in this test suite before."""

    def test_asm_fetch_circular_index_unwraps_data_key(self):
        from src.ingestion.nse_market_data.asm import fetch_circular_index
        session = _mock_session_returning(REAL_CIRCULARS_ENVELOPE_SHAPE)
        result = fetch_circular_index(session, date(2026, 9, 12), date(2026, 9, 22))
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], dict)
        self.assertEqual(result[0]["circNumber"], "76481")
        # The real failure mode: iterating the un-unwrapped envelope yields strings, not dicts.
        for c in result:
            self.assertTrue(hasattr(c, "get"), "circular entries must be dicts, not envelope keys")

    def test_gsm_fetch_circular_index_unwraps_data_key(self):
        from src.ingestion.nse_market_data.gsm import fetch_circular_index
        session = _mock_session_returning(REAL_CIRCULARS_ENVELOPE_SHAPE)
        result = fetch_circular_index(session, date(2026, 9, 12), date(2026, 9, 22))
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], dict)

if __name__ == "__main__":
    unittest.main()
