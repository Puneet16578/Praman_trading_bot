"""As-of Guard -- what could this project's bitemporal store see at two different query dates?
Two boundaries, shown side by side because they are genuinely different mechanisms:
  (a) knowledge_date -- when a fact (e.g. a corporate action) became visible at all.
  (b) event_date (ex-date) -- when a BONUS/SPLIT adjustment factor actually starts applying, once
      known -- knowing a split is coming does not retroactively adjust a price before it happens.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from demo import ui
from demo.lib.cutoff import DEMO_DATA_CUTOFF, cutoff_as_date, redact_post_cutoff
from demo.lib.store import get_demo_connection
from src.bitemporal.guard import read_as_of
from src.signals.price_adjustment import UnadjustableWindowError, adjusted_close, compute_adjustment_factor

st.set_page_config(page_title="As-of Guard -- Praman demo", layout="wide")
ui.inject_theme()
ui.page_header("\U0001F551", "As-of Guard", f"Both as-of dates are capped at this demo's own cutoff, {DEMO_DATA_CUTOFF}.")

symbol = st.text_input("Symbol", value="BAJFINANCE").strip().upper()
price_date = st.date_input("Price date (the historical close being queried)", value=None, max_value=cutoff_as_date())
col1, col2 = st.columns(2)
with col1:
    as_of_1 = st.date_input("as-of #1 (earlier)", value=None, max_value=cutoff_as_date(), key="as_of_1")
with col2:
    as_of_2 = st.date_input("as-of #2 (later)", value=None, max_value=cutoff_as_date(), key="as_of_2")

if symbol and price_date and as_of_1 and as_of_2:
    price_date_s, as_of_1_s, as_of_2_s = str(price_date), str(as_of_1), str(as_of_2)
    conn = get_demo_connection()
    try:
        st.divider()
        st.markdown("### (a) Is the corporate action itself visible? (crossing `knowledge_date`)")
        for label, as_of in (("as-of #1", as_of_1_s), ("as-of #2", as_of_2_s)):
            rows = read_as_of(conn, "corporate_actions", as_of, symbol=symbol)
            rows = [redact_post_cutoff(dict(r)) for r in rows]
            st.write(f"**{label} ({as_of}):** {len(rows)} corporate action row(s) visible")
            if rows:
                st.json(rows)

        st.markdown("### (b) Does the price adjustment apply yet? (crossing `event_date`, the ex-date)")
        for label, as_of in (("as-of #1", as_of_1_s), ("as-of #2", as_of_2_s)):
            try:
                factor = compute_adjustment_factor(conn, symbol, price_date_s, as_of)
                close = adjusted_close(conn, symbol, price_date_s, as_of)
                st.write(f"**{label} ({as_of}):** adjustment factor = **{factor:g}x**, adjusted close = **{close:.4f}**")
            except UnadjustableWindowError as exc:
                st.error(f"**{label} ({as_of}):** {exc}")
            except ValueError as exc:
                st.warning(f"**{label} ({as_of}):** {exc}")
    finally:
        conn.close()
else:
    st.info(
        "Try BAJFINANCE, price_date=2025-01-15, as-of #1=2025-04-01 (before the bonus/split was "
        "even announced), as-of #2=2025-07-01 (both announced AND effective) -- see demo/DEMO.md."
    )
