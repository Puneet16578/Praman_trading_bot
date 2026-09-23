"""NSE GSM (Graded Surveillance Measure) ingestion, from dated SURV circulars, restricted to
2025-01-01 onward -- deliberately, not an oversight. See `docs/phase4_asm_gsm_sourcing.md` for the
full scope decision; in short: GSM circulars before some point in 2024 are scanned images with no
extractable text (checked directly across 2019/2022/all of 2023), and this build declines to OCR
them because (1) a silent OCR misread on a ticker symbol is a worse failure than a documented gap
-- a wrong symbol is indistinguishable from a right one downstream, while a missing date range is
visible and honest; (2) GSM skews toward illiquidity/IBC-linked scrips, a different phenomenon
from the unusual-price-move signatures this project measures, so ASM is the richer signal and GSM
a secondary one; (3) the gap is a stated, scoped limitation with OCR as a possible future
follow-on, not a hidden one.

Unlike ASM, a GSM circular's own subject line states only the destination stage ("List of
Securities Moving to Stage II of Graded Surveillance Measure (GSM)") -- it never states the prior
stage the way ASM's "Stage - I to Stage - II" wording does. Every GSM stage-move circular is
therefore recorded as action_type=ENTRY (from_stage=None, to_stage=<parsed stage>) even though the
symbol may already have been under GSM at a different stage; this is a genuine limitation of the
source document, not a parsing shortcut, and must not be read as "this symbol was not under GSM
before." A separate subject template, "...moving out of Graded Surveillance Measure (GSM)...",
is a real, distinct EXIT event (verified against a real circular, SURV71691, this session) and is
recorded with from_stage=None, to_stage=None.

Also confirmed and NOT used here: the live `/api/reportGSM` endpoint's own `gsmStage` field is
unreliable for composite (GSM+IBC/ASM overlap) rows -- it is a Roman-numeral rendering of an
unrelated composite surveillance-code number, not the true GSM stage (see the phase doc). Stage is
always parsed from the dated circular's own subject/body text, never from that field.
"""
from __future__ import annotations
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable

import requests

from ...bitemporal.store import StoreValidationError, write_facts
from .asm import ENTRY, EXIT, to_iso_date  # shared action_type constants and date parser

GSM = "GSM"

GSM_MENTION_RE = re.compile(r"graded\s+surveillance|\bgsm\b", re.I)
MOVE_OUT_RE = re.compile(r"\bmoving\s+out\s+of\b", re.I)
MOVE_RE = re.compile(r"\bmov(?:e|ing)\b", re.I)
# "Sage" is a real, observed typo for "Stage" in NSE's own circular subject lines.
STAGE_RE = re.compile(r"\bs(?:t)?age\s*(III|II|IV|I)\b", re.I)

DATE_HEADER_RE = re.compile(r"Date:\s*([A-Za-z]+\s+\d{1,2},?\s*\d{4})")
# [\s\S] (not [^.]) between the anchor and the date phrase, deliberately -- real circular PDF text
# wraps mid-sentence ("...Stage II of GSM\nwith effect from December 23, 2024."), so the gap must
# be allowed to cross a line break (P4-002, docs/DEFECT_REGISTER.md). Every literal space inside
# "with effect from" is also `\s+`, not a literal " " -- real circulars wrap exactly there too
# ("...GSM with\neffect from December 23, 2025.", P4-003, docs/DEFECT_REGISTER.md).
EVENT_DATE_RE = re.compile(
    r"(?:framework|GSM)\b[\s\S]{0,80}?(?:with\s+effect\s+from|w\.e\.f\.?)\s*([A-Za-z]+\s+\d{1,2},?\s*\d{4})", re.I)
ROW_RE = re.compile(r"^\s*(\d+)\s+(\S+)\s+(.+?)\s+([A-Z]{2}[A-Z0-9]{9}[0-9])\b", re.M)
FOOTNOTE_LINE_RE = re.compile(r"^\s*\*\s*(\S.*)$", re.M)

def is_gsm_subject(subject: str) -> bool:
    return bool(GSM_MENTION_RE.search(subject or ""))

def classify_gsm_subject(subject: str) -> tuple[str, str | None] | None:
    """Returns (action_type, to_stage) for a stage-transition GSM circular, or None if `subject`
    is a real GSM-department circular that names no symbol-level transition (periodic relaxation
    notices, framework-update announcements) -- those are correctly out of scope, not failures."""
    if MOVE_OUT_RE.search(subject):
        return (EXIT, None)
    stage_m = STAGE_RE.search(subject)
    if MOVE_RE.search(subject) and stage_m:
        return (ENTRY, stage_m.group(1).upper())
    return None

def parse_gsm_pdf_text(text: str, action_type: str, to_stage: str | None,
                        source_circular: str) -> tuple[list[dict], str | None]:
    """Pure function: parses one already-extracted GSM circular PDF text body. Returns
    (events, failure_reason) -- failure_reason is set (and events empty) when the knowledge_date
    or event_date can't be found, since a row list with no reliable date is not safely ingestible.
    """
    # Real circulars from early 2026 (SURV72963, SURV72867) extract with spurious whitespace
    # INSIDE digit runs -- "with effect from February 2 5, 2026" for the 25th -- a pdfplumber
    # rendering artifact of that era's PDF generator, not a real space in the source document
    # (P4-008, docs/DEFECT_REGISTER.md). Collapsing ONLY horizontal whitespace (not \n) between two
    # digits is deliberate: a plain \s+ also matches the newline between one row's trailing number
    # and the next row's leading serial number ("...20\n2 FSC...", real MOVE_OUT_TEXT shape),
    # which would merge two different rows' digits and corrupt ROW_RE's per-line matching.
    text = re.sub(r"(?<=\d)[ \t]+(?=\d)", "", text)

    date_m = DATE_HEADER_RE.search(text)
    if not date_m:
        return [], "circular publication date ('Date: ...') not found in PDF header"
    knowledge_date = to_iso_date(date_m.group(1))

    event_m = EVENT_DATE_RE.search(text)
    if not event_m:
        return [], "event date ('with effect from'/'w.e.f.') not found in PDF body"
    event_date = to_iso_date(event_m.group(1))

    footnote_m = FOOTNOTE_LINE_RE.search(text)
    footnote_text = footnote_m.group(1).strip() if footnote_m else None

    events = []
    for row_m in ROW_RE.finditer(text):
        symbol, name = row_m.group(2), row_m.group(3)
        details = footnote_text if footnote_text and name.strip().endswith(("*", "^")) else None
        events.append({
            "symbol": symbol.strip(), "mechanism": GSM, "action_type": action_type,
            "from_stage": None, "to_stage": to_stage if action_type == ENTRY else None,
            "event_date": event_date, "knowledge_date": knowledge_date,
            "source_circular": source_circular, "details": details,
        })
    return events, None

# ---------- Bulk ingestion + reporting ----------

@dataclass
class GsmIngestionReport:
    event_counts: dict[str, int] = field(default_factory=dict)  # PARSED counts, see duplicate_events_skipped
    duplicate_events_skipped: int = 0
    circulars_processed: int = 0
    circulars_skipped_not_transition: int = 0
    circulars_failed: list[dict] = field(default_factory=list)  # {"circular", "reason"}

def ingest_gsm_circular(conn, action_type: str, to_stage: str | None, source_circular: str,
                         pdf_text: str, report: GsmIngestionReport) -> bool:
    """Returns True if the circular was ingested, False if its date fields could not be parsed
    (caller logs the reason). Raises on `StoreValidationError` -- our own contract violation, never
    swallowed as a source-format failure. `event_counts`/`duplicate_events_skipped`: see the ASM
    module's `ingest_asm_circular` docstring (P4-009, docs/DEFECT_REGISTER.md) -- same reasoning,
    same fix, applies equally here."""
    events, reason = parse_gsm_pdf_text(pdf_text, action_type, to_stage, source_circular)
    if reason is not None:
        report.circulars_failed.append({"circular": source_circular, "reason": reason})
        return False
    if events:
        # Must come BEFORE circulars_processed is incremented (P4-005, docs/DEFECT_REGISTER.md):
        # if this write raises, the caller's sweep loop counts the circular as failed, and it must
        # not ALSO be counted as processed just because parsing got that far.
        result = write_facts(conn, "surveillance_flags", [{**e, "source_file": source_circular} for e in events])
        report.duplicate_events_skipped += result.skipped_duplicate
    report.circulars_processed += 1
    for e in events:
        key = f'{e["mechanism"]}:{e["action_type"]}'
        report.event_counts[key] = report.event_counts.get(key, 0) + 1
    return True

# ---------- Real network fetch (not used by the fixture-based test suite) ----------

def session_with_cookie(timeout: float = 20.0) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "application/json",
    })
    session.get("https://www.nseindia.com", timeout=timeout)
    return session

def fetch_circular_index(session: requests.Session, from_date: date, to_date: date, timeout: float = 30.0) -> list[dict]:
    """P8-004 (docs/DEFECT_REGISTER.md) -- same fix as src/ingestion/nse_market_data/asm.py's
    identical function: the real response is an envelope, {"data": [...], "fromDate": ...,
    "toDate": ...}, not a bare list. See that module's docstring for the full trace."""
    r = session.get("https://www.nseindia.com/api/circulars",
                     params={"dept": "SURV", "fromDate": from_date.strftime("%d-%m-%Y"), "toDate": to_date.strftime("%d-%m-%Y")},
                     timeout=timeout)
    r.raise_for_status()
    return r.json()["data"]

def fetch_circular_pdf_text(session: requests.Session, url: str, timeout: float = 30.0) -> str:
    import pdfplumber
    from io import BytesIO
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    text_parts = []
    with pdfplumber.open(BytesIO(r.content)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)

def fetch_circular_index_union(session: requests.Session, from_date: date, to_date: date,
                                timeout: float = 30.0) -> list[dict]:
    """P8-007 scoping finding, docs/phase10_p8007_scoping.md -- same fix as
    src/ingestion/nse_market_data/asm.py's identical function: a single live call was observed
    to return an incomplete result once; two calls unioned by `circNumber` is cheap insurance
    against this observed intermittency (the index call itself is fast, confirmed directly)."""
    first = fetch_circular_index(session, from_date, to_date)
    second = fetch_circular_index(session, from_date, to_date)
    by_number = {str(c["circNumber"]): c for c in first}
    for c in second:
        by_number.setdefault(str(c["circNumber"]), c)
    return list(by_number.values())

def fetch_and_ingest_gsm_range(conn, from_date: date, to_date: date, delay_seconds: float = 0.3,
                                session_factory: Callable[[], requests.Session] = session_with_cookie) -> GsmIngestionReport:
    """Real network sweep, 2025-01-01 floor enforced by the caller passing `from_date` -- this
    function itself does not hardcode the floor so tests can exercise it at any date range, but
    `scripts/ingest_asm_gsm_sample.py` never calls it with a date before 2025-01-01. Circular index
    unioned across two calls -- see `fetch_circular_index_union`. Not called by the fixture-based
    test suite."""
    session = session_factory()
    report = GsmIngestionReport()
    circulars = fetch_circular_index_union(session, from_date, to_date)
    for c in circulars:
        subject = c.get("sub", "") or ""
        if not is_gsm_subject(subject):
            continue
        classification = classify_gsm_subject(subject)
        source_circular = "SURV" + str(c["circNumber"])
        if classification is None:
            report.circulars_skipped_not_transition += 1
            continue
        action_type, to_stage = classification
        try:
            pdf_text = fetch_circular_pdf_text(session, c["circFilelink"])
            ingest_gsm_circular(conn, action_type, to_stage, source_circular, pdf_text, report)
        except StoreValidationError:
            raise
        except Exception as exc:
            report.circulars_failed.append({"circular": source_circular, "reason": str(exc)})
        time.sleep(delay_seconds)
    return report
