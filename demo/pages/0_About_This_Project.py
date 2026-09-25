"""About This Project -- a single, self-contained page a first-time reader can go through top to
bottom and come away understanding what Praman is, how it's built, what it found, and what's
pending. Every number here is sourced the same way the Findings page sources its numbers (parsed
or hand-transcribed-with-a-test, demo/lib/findings.py) -- nothing on this page is invented for
presentation purposes."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from demo import ui
from demo.lib import findings

st.set_page_config(page_title="About -- Praman demo", layout="wide")
ui.inject_theme()
ui.page_header("\U0001F4D6", "About This Project", "Read this once, top to bottom, and the rest of the demo will make sense.")

st.markdown(
    """
## What Praman is

Praman is a **forensic classifier for unusual price moves on the NSE** (India's National Stock
Exchange). Given a stock that moved sharply on a given day, it measures whether the move has an
**informational basis** — a corporate disclosure in the preceding trading sessions that plausibly
explains it — or whether it moved with no such disclosure on record, and tries to *prove* that
classification against subsequent price behaviour and exchange surveillance history, rather than
merely asserting it.

**It never states a conclusion beyond that.** No verdicts, no "this looks suspicious," no
buy/sell/hold. A fact like *"delivery 11% on 14x average volume; no disclosure in the preceding 10
sessions"* is exactly the kind of thing Praman reports — the interpretation is left to the reader.
This isn't a stylistic choice; it's enforced architecturally (see "No verdicts, structurally"
below), not just by convention.
"""
)

ui.section_divider()
st.markdown("## Architecture, in five ideas")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        st.markdown("#### 1. Bitemporal or nothing")
        st.write(
            "Every fact carries an *event date* (when it happened) and a *knowledge date* (when it "
            "became publicly known). Every query is as-of a specific date — a function that reads "
            "data without an as-of parameter is treated as a bug, not a convenience. This is what "
            "the **As-of Guard** page demonstrates directly."
        )
    with st.container(border=True):
        st.markdown("#### 2. A fixed, deterministic pipeline")
        st.write(
            "A Supervisor dispatches three specialist agents (Market Microstructure, Disclosure, "
            "Surveillance), each recomputing its own signals *live* from the store — never from a "
            "cached artifact. Every specialist tool call passes through one authorization gate "
            "(role × tool × budget, fail-closed)."
        )
with col2:
    with st.container(border=True):
        st.markdown("#### 3. An adversarial verifier")
        st.write(
            "Before any claim reaches output, a deterministic Adversary independently re-derives "
            "it — for two claim types, via a second, separately-implemented code path — and runs a "
            "lint against stating a verdict. A claim that doesn't reproduce, or that reads as a "
            "conclusion, is dropped, not softened. The **Verifier** page shows this live, including "
            "a real tamper-and-catch demonstration."
        )
    with st.container(border=True):
        st.markdown("#### 4. No language model, anywhere")
        st.write(
            "Confirmed by grep across the entire codebase, not merely a design intention: zero "
            "LLM-provider-calling code exists. Every report is a deterministic Python template over "
            "data. This is *why* invariant 12 (see below) is enforceable at all — there is no "
            "free-text generation surface for a paraphrase to slip past a word-list filter."
        )

with st.container(border=True):
    st.markdown("#### 5. No verdicts, structurally")
    st.write(
        "The rule that Praman never states a conclusion is enforced by having no code path that "
        "renders free-text narrative into shareable output at all — not by a keyword filter as the "
        "primary control. That filter exists too, as a backstop, and this project reports its own "
        "measured catch rate honestly: 5/5 on phrasings written to test it directly, but 0/5 against "
        "sentences written specifically to *evade* it while still stating a verdict. That 0/5 is "
        "reported as the honest finding, not hidden — it's exactly why the architectural control, "
        "not the word list, is what's actually relied on."
    )

ui.section_divider()
st.markdown("## The headline result — and why it doesn't stand")

st.markdown(
    f"""
This is the part most worth reading closely, because it's the clearest demonstration of how this
project actually works: **a strong, clean-looking result was found, checked, and retracted by the
project's own review — before it shipped as a claim.**

The original finding: the full classification system's precision in its top-scored tier
(**{findings.RETRACTION['classifier_top_tier_precision_raw']}%**) cleared a disclosure-tier-only
baseline (**{findings.RETRACTION['disclosure_alone_precision_raw']}%**) with non-overlapping
confidence intervals — the kind of result that would normally be the headline.

A pre-registered follow-up check asked a sharper question first: did the outcome label and the
classifier's own core input secretly share the same anchor point? They did — both were built from
`close(event date − 20 sessions)`. Re-scored under a label that removes the shared anchor:
"""
)

c1, c2 = st.columns(2)
with c1:
    st.metric("Classifier, top tier — raw label", f"{findings.RETRACTION['classifier_top_tier_precision_raw']}%")
    st.metric(
        "Classifier, top tier — clean label",
        f"{findings.RETRACTION['classifier_top_tier_precision_clean']}%",
        delta=f"n={findings.RETRACTION['classifier_top_tier_n_clean']}, below base rate",
        delta_color="inverse",
    )
with c2:
    st.metric("Disclosure tier alone — raw label", f"{findings.RETRACTION['disclosure_alone_precision_raw']}%")
    st.metric("Disclosure tier alone — clean label", f"{findings.RETRACTION['disclosure_alone_precision_clean']}%", delta="= its own base rate, zero lift")

st.write(
    "Neither the classifier nor disclosure tier alone showed any lift over its own base rate once "
    "the coupling was removed. **The original result measured the coupling, not real signal.** "
    "This is logged, with root cause and re-verification evidence, as its own defect "
    "(`P8-001`) — see the **Findings** page for the full decomposition."
)

ui.section_divider()
st.markdown("## How defects get found — two real examples")

with st.expander("A fix for one selection bias silently created a second, worse one (`P8-013` → `P8-014`)"):
    st.write(
        "An outcome label was redefined to fix a bias where thinly-traded stocks took disproportionately "
        "longer to accumulate a computable outcome. The fix was applied, and a committed document "
        "asserted the new label's missingness \"isn't correlated with the model's own inputs\" — "
        "*without actually measuring that claim*. When it was measured directly, it was not just "
        "unmeasured but false: the new label's missing rate was 4.3x the old one, with a 14.1 "
        "percentage-point gap between the smallest and largest companies — worse than before the fix. "
        "Root cause: the underlying series-continuity logic only handled a *permanent* change in how "
        "a stock trades, not a *temporary* one — exactly the pattern for the surveillance-affected "
        "small companies this project most needs to keep. Found by re-measuring the fix's own effect "
        "rather than assuming it had worked; fixed at the root; the corrected rate dropped to 1.31%."
    )

with st.expander("A silent HTML-as-CSV download (`P2-001`)"):
    st.write(
        "An early data-source check found that a library used for fetching exchange price data "
        "reports success — no exception — even when the exchange returns an HTML error page instead "
        "of real data. Nine years of \"successfully fetched\" historical files turned out to be "
        "byte-identical error pages. Found by noticing the file sizes were suspiciously identical "
        "across unrelated dates spanning years; fixed at the storage layer with independent shape "
        "validation, so no future data source can make the same mistake silently."
    )

st.caption(
    f"These are two of **{findings.count_defects()}** defects logged against this project as a "
    "whole, each with root cause, fix, and re-verification evidence — `docs/DEFECT_REGISTER.md`."
)

ui.section_divider()
st.markdown("## Where things stand now")

p = findings.FROZEN_PREREGISTRATION
st.info(
    f"A redesigned scoring function is pre-registered and **frozen** as of "
    f"**{findings.count_preregistration_amendments()} rounds of amendment** — most of that work was "
    f"spent fixing the outcome *label*, not the model. It evaluates forward-only: missing-data "
    f"threshold **{p['missing_data_threshold_pct']}%**, evaluation window **{p['evaluation_window']}**, "
    f"pinned to a specific commit, and **no forward outcome has existed at any point this was "
    f"written or amended.** The earliest possible run is **{p['earliest_run']}**. Further amendments "
    f"are warranted only for a defect that would make the evaluation impossible to run — not for "
    f"further tuning.",
    icon="\U0001F9CA",
)

ui.section_divider()
st.markdown("## Where to go next")
st.write(
    "Use the sidebar to open **Event Browser** for a real evidence report, **As-of Guard** to see "
    "the bitemporal store in action, **Verifier** to watch the Adversary catch a tampered claim "
    "live, or **Findings** for the full, sourced numbers behind everything above."
)
