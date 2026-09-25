"""Findings -- aggregate, already-committed results only. No live query. Every figure is loaded
from demo/lib/findings.py, which either parses it directly from a committed doc or, where that
would be unreliably fragile, hand-transcribes it with a source-equality test
(tests/test_demo_findings_figures.py) -- the source path is printed beside every figure below."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from demo import ui
from demo.lib import findings

st.set_page_config(page_title="Findings -- Praman demo", layout="wide")
ui.inject_theme()
ui.page_header("\U0001F4CA", "Findings", "Static. No live query on this page.")

st.markdown("## Layer 1 -- factual accuracy")
st.caption(f"Source: {findings.LAYER1_VERIFICATION['source']}")
l1 = findings.LAYER1_VERIFICATION
c1, c2, c3 = st.columns(3)
c1.metric("Claims verified", f"{l1['claims_verified_pct']}%", help=f"{l1['claims_verified']:,} claims checked, {l1['claims_withheld']} correctly withheld")
c2.metric("Independently re-derived sample", f"{l1['derivation_sample_pct']}%", help=f"{l1['derivation_sample_n']} of {l1['derivation_sample_of']:,} eligible claims, via a separate code path from raw data")
c3.metric("Defects logged project-wide", str(findings.count_defects()), help="Live count from docs/DEFECT_REGISTER.md")
st.caption("Unaffected by the retraction below -- Layer 1 tests transcription/derivation correctness, not classification performance.")

st.markdown("## The headline, and its retraction")
st.caption(f"Source: {findings.RETRACTION['source']}")
col1, col2 = st.columns(2)
with col1:
    st.metric("Classifier top-tier precision -- raw label", f"{findings.RETRACTION['classifier_top_tier_precision_raw']}%")
    st.metric(
        "Classifier top-tier precision -- clean label",
        f"{findings.RETRACTION['classifier_top_tier_precision_clean']}%",
        delta=f"n={findings.RETRACTION['classifier_top_tier_n_clean']}, below base rate",
    )
with col2:
    st.metric("Disclosure-tier-alone -- raw label", f"{findings.RETRACTION['disclosure_alone_precision_raw']}%")
    st.metric("Disclosure-tier-alone -- clean label", f"{findings.RETRACTION['disclosure_alone_precision_clean']}%", delta="= its own base rate, zero lift")

st.markdown("## Drift vs. coupling, decomposed")
st.caption(f"Source: {findings.DECOMPOSITION['source']}")
st.write(
    f"Correcting market drift alone barely moves the classifier's lift: "
    f"**+{findings.DECOMPOSITION['raw_lift_pp']}pp -> +{findings.DECOMPOSITION['drift_corrected_lift_pp']}pp** "
    f"(same anchor). Only removing the shared anchor collapses it: "
    f"**{findings.DECOMPOSITION['decoupled_lift_pp_primary']}pp / "
    f"+{findings.DECOMPOSITION['decoupled_lift_pp_secondary']}pp** under the two decoupled thresholds tested."
)

st.markdown("## Final, frozen clean-label feature AUCs")
st.caption("Source: docs/RESULTS.md (parsed directly from the committed table, not re-typed)")
st.dataframe(findings.parse_final_auc_table(), width="stretch")

st.markdown("## The frozen forward pre-registration")
st.caption(f"Source: {findings.FROZEN_PREREGISTRATION['source']}")
p = findings.FROZEN_PREREGISTRATION
st.write(f"- TRAIN missing rate: **{p['train_missing_rate_pct']}%** | HOLD-OUT: **{p['holdout_missing_rate_pct']}%** | gap: **{p['gap_pp']}pp**")
st.write(f"- Missing-data threshold: **{p['missing_data_threshold_pct']}%**")
st.write(f"- Evaluation window: **{p['evaluation_window']}** -- earliest possible run: **{p['earliest_run']}**")
st.write(f"- Pinned commit: `{p['pinned_commit']}`")
st.info("No forward outcome has existed at any point this pre-registration was written or amended. "
        "As of Amendment 5 it is FROZEN -- further amendments only for a defect that would make the "
        "evaluation impossible to run.")
