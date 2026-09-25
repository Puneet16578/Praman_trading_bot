"""Praman demo -- entry point. Local-only (see .streamlit/config.toml), read-only against
data/demo/praman_demo.sqlite ONLY (never production), truncated at DEMO_DATA_CUTOFF."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from demo.lib.cutoff import DEMO_DATA_CUTOFF
from demo.lib.store import DEMO_DB_PATH, DemoStoreMissingError, get_demo_connection, patch_reference_data_paths

st.set_page_config(page_title="Praman (demo)", page_icon="\U0001F50D", layout="wide")

if "anonymise" not in st.session_state:
    st.session_state["anonymise"] = False
if "reference_paths_patched" not in st.session_state:
    patch_reference_data_paths()
    st.session_state["reference_paths_patched"] = True

st.title("Praman -- forensic classifier for unusual NSE price moves (private demo)")

st.warning(
    f"**Local, read-only demo.** Opens only `data/demo/praman_demo.sqlite` (never the production "
    f"store), truncated so no event, price, label, or record dated after **{DEMO_DATA_CUTOFF}** is "
    f"ever visible here -- that is this project's own pre-registered forward evaluation window, "
    f"and no interim look at it is taken by this demo or anything else.",
    icon="\U0001F512",
)

try:
    conn = get_demo_connection()
    conn.close()
    st.success(f"Demo store found: `{DEMO_DB_PATH.relative_to(Path(__file__).resolve().parents[1])}`")
except DemoStoreMissingError as exc:
    st.error(str(exc))

st.session_state["anonymise"] = st.toggle(
    "Anonymise symbols (STOCK_A, STOCK_B, ...) -- for recorded video",
    value=st.session_state["anonymise"],
)

st.markdown(
    """
Use the sidebar to navigate:

1. **Event Browser** -- pick a real catalogued event (or search a symbol/date range) and see its
   full evidence report.
2. **As-of Guard** -- see what this project's bitemporal store could see at two different query
   dates, using a real corporate action (BAJFINANCE's 2025 bonus + split).
3. **Verifier** -- every claim behind a report, its verification tier and result, and a live
   "tamper with a claim" demonstration of the Adversary catching it.
4. **Findings** -- the project's aggregate, already-committed results: the headline retraction, the
   final clean-label feature AUCs, and the frozen forward pre-registration.

See `demo/DEMO.md` for a 5-minute walkthrough script.
"""
)
