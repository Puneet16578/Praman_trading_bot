# Amendment 5 label verification - 2026-10-02

The pinned-input table in docs/phase10_preregistration_amendment5.md, section 9, states:

| Input | Pinned source |
|---|---|
| Label (`relative_t0_primary`) | `scripts/phase8_robustness_relabel_t0.py` (`P8-013` global-horizon definition, 10-session staleness cap, `P8-012`/`P8-014` full per-date EQ/BE/BZ bridge) |

The function is `compute_t0_relative`; its primary returned field is `collapsed_t0_primary`. The Desk replay imports and calls this function directly. `git diff afe3e2b HEAD -- scripts/phase8_robustness_relabel_t0.py` is empty. The label module is unchanged.

Definition: signed, event-close-anchored return relative to the equal-weighted EQ market index; target is 90 GLOBAL sessions after the event; use the last real close on/before that target with at most 10 global sessions of staleness, and the index on that same observed date. Histories bridge EQ/BE/BZ per date and stitch symbols sharing an ISIN. The input is the final equity-only catalogue; the label function itself assumes this caller-side universe filter. Missing labels remain missing.

## Five value comparisons

| Event | Signed return, current | Signed return, pinned | Primary / secondary |
|---|---:|---:|---|
| 63MOONS 2020-01-01 | -0.370037868452851 | -0.370037868452851 | True / True |
| A2ZINFRA 2021-01-01 | -0.3007412736660139 | -0.3007412736660139 | True / True |
| 3PLAND 2022-01-03 | -0.1421028252915506 | -0.1421028252915506 | True / True |
| AAREYDRUGS 2024-01-01 | -0.2742267340286104 | -0.2742267340286104 | True / True |
| 3IINFOLTD 2025-01-01 | -0.16897798403084896 | -0.16897798403084896 | True / True |

Selection was the first chronological/lexicographic event in each of 2020, 2021, 2022, 2024 and 2025, fixed before comparing values. There are no 2019 events in this catalogue. All five full result dictionaries match exactly. This verifies code equivalence using identical current inputs, not the historical data vintage at the pinned commit.

Reproduce: `python scripts/desk_verify_label.py`. The committed screening addendum is in 73f2ce4, preceding these computations.
