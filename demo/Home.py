"""Praman demo -- entry point. Local-only (see .streamlit/config.toml), read-only against
data/demo/praman_demo.sqlite ONLY (never production), truncated at DEMO_DATA_CUTOFF."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from demo import ui
from demo.lib import findings
from demo.lib.cutoff import DEMO_DATA_CUTOFF
from demo.lib.store import DEMO_DB_PATH, DemoStoreMissingError, get_demo_connection, patch_reference_data_paths

st.set_page_config(page_title="Praman (demo)", page_icon="\U0001F50D", layout="wide")
ui.inject_theme()

if "anonymise" not in st.session_state:
    st.session_state["anonymise"] = False
if "reference_paths_patched" not in st.session_state:
    patch_reference_data_paths()
    st.session_state["reference_paths_patched"] = True

ui.hero(
    "Praman",
    "A forensic classifier for unusual NSE price moves — measures whether a sharp move has an "
    "informational basis (a disclosure that plausibly explains it) or lacks one, and tries to "
    "prove that classification against outcomes and exchange surveillance history rather than "
    "merely asserting it. Reports measured signals and their values only — never a verdict.",
)

st.warning(
    f"**Local, read-only demo.** Opens only `data/demo/praman_demo.sqlite` (never the production "
    f"store), truncated so no event, price, label, or record dated after **{DEMO_DATA_CUTOFF}** is "
    f"ever visible here — that is this project's own pre-registered forward evaluation window, "
    f"and no interim look at it is taken by this demo or anything else.",
    icon="\U0001F512",
)

try:
    conn = get_demo_connection()
    conn.close()
    store_ok = True
except DemoStoreMissingError as exc:
    store_ok = False
    st.error(str(exc))

if store_ok:
    ui.stat_card_grid([
        ("Claims independently verified", f"{findings.LAYER1_VERIFICATION['claims_verified_pct']}%",
         f"{findings.LAYER1_VERIFICATION['claims_verified']:,} claims, {findings.LAYER1_VERIFICATION['claims_withheld']} correctly withheld — {findings.RETRACTION['source']}"),
        ("Defects logged and traced", str(findings.count_defects()),
         "Every one with root cause, fix, and re-verification evidence — docs/DEFECT_REGISTER.md, counted live from that file"),
        ("Pre-registration amendments", str(findings.count_preregistration_amendments()),
         "Each a dated, git-committed correction — never a silent edit — before the frozen state"),
        ("LLM calls in this codebase", "0",
         "Confirmed by grep across all of src/, not merely a design intention — P8-003, docs/DEFECT_REGISTER.md"),
    ])

st.markdown("")
st.session_state["anonymise"] = st.toggle(
    "Anonymise symbols (STOCK_A, STOCK_B, ...) — for recorded video",
    value=st.session_state["anonymise"],
)

ui.section_divider()
st.markdown("### Explore")

cards = [
    ("1_Event_Browser", "\U0001F4C2", "Event Browser",
     "Pick a real catalogued event (or search a symbol/date range) — see its full, live-generated evidence report."),
    ("2_As_Of_Guard", "\U0001F551", "As-of Guard",
     "What could this project's bitemporal store see at two different query dates? BAJFINANCE's real 2025 bonus + split."),
    ("3_Verifier", "✅", "Verifier",
     "Every claim behind a report, its verification tier and result — plus a live tamper-and-catch demonstration."),
    ("4_Findings", "\U0001F4CA", "Findings",
     "The headline retraction, the final clean-label feature AUCs, and the frozen forward pre-registration."),
]

cols = st.columns(len(cards))
for col, (page_file, icon, title, blurb) in zip(cols, cards):
    with col:
        st.markdown(
            f'<div class="praman-card"><h4>{icon} {title}</h4><p>{blurb}</p></div>',
            unsafe_allow_html=True,
        )
        st.page_link(f"pages/{page_file}.py", label=f"Open {title}", icon=icon)

ui.section_divider()
st.page_link("pages/0_About_This_Project.py", label="New here? Read the full project overview first", icon="\U0001F4D6")
st.caption("See `demo/DEMO.md` for a scripted 5-minute walkthrough.")
