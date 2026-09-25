"""Shared Streamlit-dependent presentation helpers -- deliberately NOT under demo/lib/, which must
stay importable without streamlit installed (tests/test_streamlit_optional.py only scans lib/).
Pure visual/formatting helpers only: nothing here computes a number, queries the store, or composes
narrative text about any event -- it only styles values the rest of the demo already produced.
"""
from __future__ import annotations

import streamlit as st

# Classification -> st.badge color. A visual encoding of an EXISTING value, not a new claim about
# it -- GROUNDED/UNEXPLAINED_ISOLATED are deliberately close in tone (both "outcome not yet clear
# either way" colors) because this project's own measurement found them statistically
# indistinguishable by outcome (docs/phase7b_classification_design.md) -- color choice should not
# imply a confidence gap the data doesn't show.
_CLASSIFICATION_COLORS = {
    "GROUNDED": "green",
    "PARTIALLY_GROUNDED": "blue",
    "UNEXPLAINED": "orange",
    "UNEXPLAINED_ISOLATED": "violet",
    "UNEXPLAINED_UNKNOWN_COVERAGE": "gray",
}

THEME_CSS = """
<style>
:root {
    --praman-accent: #2563eb;
}
.praman-hero {
    padding: 1.75rem 2rem;
    border-radius: 14px;
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 55%, #2563eb 130%);
    color: #f8fafc;
    margin-bottom: 1.25rem;
}
.praman-hero h1 {
    color: #ffffff;
    margin-bottom: 0.25rem;
    font-size: 2.1rem;
}
.praman-hero p {
    color: #dbeafe;
    font-size: 1.05rem;
    margin-bottom: 0;
}
.praman-card {
    border: 1px solid rgba(120, 120, 120, 0.25);
    border-radius: 12px;
    padding: 1rem 1.1rem;
    height: 100%;
    background: rgba(37, 99, 235, 0.04);
}
.praman-card h4 {
    margin-top: 0;
    margin-bottom: 0.35rem;
}
.praman-card p {
    font-size: 0.92rem;
    opacity: 0.85;
}
.praman-section-divider {
    margin: 1.75rem 0 1rem 0;
    border: none;
    border-top: 1px solid rgba(120, 120, 120, 0.25);
}
</style>
"""


def inject_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="praman-hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def page_header(icon: str, title: str, subtitle: str | None = None) -> None:
    st.markdown(f"## {icon} {title}")
    if subtitle:
        st.caption(subtitle)


def section_divider() -> None:
    st.markdown('<hr class="praman-section-divider" />', unsafe_allow_html=True)


def classification_badge(classification: str) -> None:
    color = _CLASSIFICATION_COLORS.get(classification, "gray")
    st.badge(classification, color=color)


def stat_card_grid(stats: list[tuple[str, str, str | None]]) -> None:
    """stats: list of (label, value, help_text_or_None). Renders as st.metric cards in columns."""
    cols = st.columns(len(stats))
    for col, (label, value, help_text) in zip(cols, stats):
        with col:
            st.metric(label, value, help=help_text)
