"""Symbol AND company-name masking for the "anonymise" toggle -- tickers are not the only
identifier in a report. Disclosure descriptions are free text and, per real NSE announcement data
checked directly against this project's own store, ~92% of them follow one of a few generated
templates that spell the full company name out ("Axis Bank Limited has informed the Exchange
regarding ..."). Masking only the ticker string leaves the company name sitting in plain text next
to it.

No attachment-URL masking is implemented: checked directly against this project's own design
(`src/agent/specialists.py`'s `attachment_url_unavailable` claim) -- this project's announcement
ingestion does not capture attachment URLs at all, and no field the live agent report renders
(`EventReport`, `EvidenceClaim`) is URL-shaped. `sebi_orders.pdf_url` exists in the schema but that
table is not read by any of the four demo pages. There is nothing to mask because the field this
project would need to leak through does not exist in what the demo shows.

Scope, stated honestly rather than implied complete: the leading-template regex below covers the
common case, measured directly (2,761/3,000 = 92.0% of a random sample of real, non-empty
announcement descriptions in this project's own store). The remaining ~8% use other real phrasings
("Significant movement in price has been observed in <Name>...", "The Exchange has sought
clarification from <Name>...") that this regex does not catch. This is a real, disclosed gap, not
assumed away -- exactly the same honesty this project's own banned-term lint applies to its own
measured catch rate.
"""
from __future__ import annotations
import re

STOCK_LABEL_PREFIX = "STOCK_"

# "<Name> has informed/submitted/filed/intimated/disclosed ..." -- the dominant real template.
_LEADING_COMPANY_NAME_RE = re.compile(
    r"^(.*?)\s+has\s+(?:informed|submitted|filed|intimated|disclosed)\b", re.IGNORECASE
)


def build_symbol_map(symbols: list[str]) -> dict[str, str]:
    """Stable STOCK_A, STOCK_B, ... assignment -- sorted order, so the same set of symbols always
    gets the same labels within one build (session-stable when the caller holds this dict in
    st.session_state for the session's lifetime, per demo/Home.py)."""
    ordered = sorted(set(symbols))
    labels = {}
    for i, sym in enumerate(ordered):
        labels[sym] = f"{STOCK_LABEL_PREFIX}{_label_suffix(i)}"
    return labels


def _label_suffix(i: int) -> str:
    """A, B, ..., Z, AA, AB, ... -- spreadsheet-column style, in case a demo session ever touches
    more than 26 symbols."""
    letters = []
    i += 1
    while i > 0:
        i, rem = divmod(i - 1, 26)
        letters.append(chr(ord("A") + rem))
    return "".join(reversed(letters))


def extract_company_name(description: str) -> str | None:
    """Best-effort extraction of the company name this ONE row's description names, from its own
    leading template -- not a lookup against any stored company-name field, because this project
    ingests none (symbol is the only identifier NSE data gives it). Returns None if the leading
    template does not match (see module docstring for the measured ~8% that don't)."""
    if not description:
        return None
    m = _LEADING_COMPANY_NAME_RE.match(description.strip())
    return m.group(1).strip() if m else None


def mask_text(text: str, symbol: str, replacement: str, company_names: list[str] | None = None) -> str:
    """Case-insensitive whole-occurrence replace of the symbol, and of every name in
    `company_names` if given (every occurrence in `text`, not only the leading one -- a name
    extracted from the lead often repeats later in the same sentence, e.g. "... OF AXIS BANK
    LIMITED (THE BANK)"). Multiple names are supported because one event's disclosure window can
    hold several announcements, each independently naming the company in its own lead phrase."""
    if not text:
        return text
    out = re.sub(re.escape(symbol), replacement, text, flags=re.IGNORECASE)
    for name in company_names or ():
        if name:
            out = re.sub(re.escape(name), replacement, out, flags=re.IGNORECASE)
    return out


def company_names_for_event(conn, symbol: str, event_date: str) -> list[str]:
    """Every company name extract_company_name() can pull from this event's own disclosure window
    -- one event can have several announcements, each independently naming the company in its own
    lead phrase. Uses the same get_disclosure_window() the live DisclosureAgent calls, so this sees
    exactly the rows the report itself is built from, nothing extra."""
    from src.mcp.tools import get_disclosure_window

    window = get_disclosure_window(conn, symbol, event_date)
    names = []
    for row in window["rows"]:
        name = extract_company_name(row.get("description") or "")
        if name and name not in names:
            names.append(name)
    return names


def mask_value(value, symbol: str, replacement: str, company_names: list[str] | None = None):
    """Recursively applies mask_text to every string in a dict/list/tuple structure -- for masking
    a whole report/claim dict at render time without hand-listing every field that might contain
    the symbol or company name."""
    if isinstance(value, dict):
        return {k: mask_value(v, symbol, replacement, company_names) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        seq = [mask_value(v, symbol, replacement, company_names) for v in value]
        return type(value)(seq) if not isinstance(value, list) else seq
    if isinstance(value, str):
        return mask_text(value, symbol, replacement, company_names)
    return value
