# Trading research registry

Registered 19 October 2026. DOCUMENTS ONLY.

Approved by the user in their message of 19 October 2026.

Registration commit: `d176f414eb6371ddb6eccddff778ca19f41f9218` (19 October 2026), introducing this registry and the S1 protocol. This hash was recorded after the registration commit was created.

Original draft from checkout 2d83e28c5d1d094fd1ee0be65b77a36f2355cb2e; revised against 0cd41bc4cf3ef5d3f26e841b5c6288b8ca854bfd using the user's 19 October decisions. Entries describe existing records; they do not authorise any action.

**Scope:** a research ledger separate from the frozen forensic experiment and from the operational strategy registry already implemented in [desk/automation/registry.py](D:/Agentic_ai_project/praman/desk/automation/registry.py). The blueprint's T2 “Not started” row is dated 4 October; it does not mean that S0 lacks an operational registry.

**Discipline:** retain every tested version, failure, inconclusive result, superseded attempt and abandoned idea. New versions append entries. Never overwrite locked reports or promote a descriptive analysis to a registered success.

All paths below link to repository documents. No new performance numbers were calculated.

## Registered context test

| ID / test | Status | Documents |
|---|---|---|
| T1 V0 | Evaluated baseline, not a separately passed trading strategy. | [Protocol](D:/Agentic_ai_project/praman/docs/desk/t1_market_context_prereg.md), [locked development](D:/Agentic_ai_project/praman/docs/desk/t1_development_results_20261018.md), [locked 2025](D:/Agentic_ai_project/praman/docs/desk/t1_holdout_results_2025.md). |
| T1 V1 | Development FAIL; 2025 INCONCLUSIVE. | Same locked reports. |
| T1 V2 | Development FAIL; 2025 INCONCLUSIVE. | Same locked reports. |
| T1 V3 | Development FAIL; 2025 replication not met. | Same locked reports. |

T1 is a context/adverse-move association test, not a demonstrated return strategy. Its three contrasts remain visible independently. Calendar 2025 is PARTIALLY EXPOSED. Random-label rehearsals were implementation checks, not additional successful strategy tests.

## Operational paper strategies

| ID / version | Status | Record |
|---|---|---|
| S0 v1 | SUPERSEDED_NEVER_RUN. | [Versioned definition](D:/Agentic_ai_project/praman/desk/automation/registry.py), [design changelog](D:/Agentic_ai_project/praman/docs/desk/DESIGN.md). |
| S0 v2 | Superseded after one run, 5 October 2026; existing positions retain their version in the shared S0 book. | Same definition and changelog. |
| S0 v3 | PAPER_BURN_IN; sealed. Operational exercise, not evidence of an edge. | Same definition and changelog. |
| Manual paper book | Separate discretionary operational book, not a registered systematic research hypothesis. No results inspected for this draft. | [Registry definition](D:/Agentic_ai_project/praman/desk/automation/registry.py), [paper guide](D:/Agentic_ai_project/praman/docs/desk/HOW_TO_PAPER_TRADE.md). |

The S0 seal, Windows task, live gates and cost configuration are unchanged. No sealed results are included.

## Registered and unregistered ideas

| Idea / ID | Description | Status and record |
|---|---|---|
| B / S1 v1 | Rebounds over the next one to three sessions after an unexplained catalogue drop; LONG-only delivery research. | Development recorded 21 October 2026: FAIL at h=1 and h=3 because (a) and (c) failed; LABEL SHOWN at both. Sensitivities, full report and 2025 pending; 2025 needs separate user approval. [Primary lock note](s1_development_results_20261021_primary.md). C1–C6 and the former section 11's definitions resolved by the user's decisions. [S1 protocol](s1_unexplained_drop_prereg.md). Sourcing: [A/B/C](D:/Agentic_ai_project/praman/docs/desk/abc_sourcing_check.md), [corrected funnel](D:/Agentic_ai_project/praman/docs/desk/abc_followup_check.md). |
| S1 h=5 and h=10 | Longer horizons in the blueprint's T2 programme. | NOT ATTEMPTED for S1; outside its three-session scheduled holding limit. No result or failure implied. |
| A | Follow catalogue events explained by material company announcements. | NOT REGISTERED. Input sourcing/counts only; same A/B/C reports. |
| C | Follow a strong first reaction to quarterly results. | NOT REGISTERED. Input sourcing/counts only; same A/B/C reports. |
| D | What happens after large opening gaps. | NOT REGISTERED. Intraday research only; execution excluded by blueprint amendment 1; needs intraday data from R1's forward collection. Definition supplied by the user on 19 October 2026. |
| E | Opening-range breakout. | NOT REGISTERED. Intraday research only; execution excluded by amendment 1; needs intraday data from R1's forward collection. User definition, 19 October 2026. |
| F | Reversion to VWAP. | NOT REGISTERED. Intraday research only; execution excluded by amendment 1; needs intraday data from R1's forward collection. User definition, 19 October 2026. |
| R2 | Results-drift sourcing investigation. | DATA CHECK ONLY, not a registered return strategy. [Sourcing check](D:/Agentic_ai_project/praman/docs/desk/r2_sourcing_check.md). Do not silently equate it with C or D–F. |

A/B/C counting conventions and their sensitivities remain the pre-registration counting record, not the revised S1 population. At implementation, S1 needs a new frozen funnel version with dated ISIN eligibility for the event stock and market/peers, no GSM selection filter in any period, and its separately specified weekday execution/bootstrap calendar. The funnel's input calculations keep their frozen calendar. Existing counts are not recomputed by this document. Their 2025 input exposure remains disclosed.

S1 uses S0's next-session limit entry and current sizing, a frozen decision-close-minus-two-ATR stop monitored after fill, open exits at h=1/h=3, and no target. The barrier path is descriptive. The four interval tests, (a)/(b) at each horizon, use 98.75% two-sided intervals; (a) and (c) determine the per-horizon verdict, while (b) reports label evidence separately. Descriptive measures never decide the verdict. S1's full protocol is in [the registered document](s1_unexplained_drop_prereg.md); this summary grants no implementation authority.

D–F's intraday data dependency is [R1's forward collection design](D:/Agentic_ai_project/praman/docs/desk/R1_market_hours_watcher_design.md). This is a design/dependency reference, not evidence that sufficient data has been collected. Definitions and thresholds for those unregistered ideas still require their own protocols.

Forward results are closed until the firewall permits access: no earlier than 2027-06-01 (blueprint amendment 3) and no earlier than the binding evaluation (CLAUDE.md D7), whichever is later. This registration grants no release permission.

## Completed shadow and execution research, including unsuccessful approaches

Primary period was 2019–2025; 2026 through 15 September was separately descriptive. These are exposed periods, not untouched tests for a new strategy.

| Attempt | Status / limitation preserved | Documents |
|---|---|---|
| Original screening shadow replay | Completed observational replay. Pre-G6 artifacts retained; later correction does not erase the earlier attempt. Not a profitability verdict. | [Protocol](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_prereg.md), [pre-G6 report](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_results_pre_g6.md), [corrected report](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_results.md). |
| G6 correction and replay comparison | Completed correctness repair; original sizing did not enforce the intended cost-inclusive risk cap. | [Comparison](D:/Agentic_ai_project/praman/docs/desk/g6_correction_comparison.md). |
| Follow-up 1: volatility control | Completed descriptive association check, not a registered return edge. | [Protocol](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_followup_prereg.md), [pre-G6 results](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_followup_results_pre_g6.md), [corrected results](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_followup_results.md), [review](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_followup_review.md). |
| Follow-up 1: fixed 90% headroom | Completed; did not eliminate fill-time cap breaches. Retain this unsuccessful risk-control approach. | Same follow-up 1 protocol, results and review. |
| Follow-up 2: next-open versus 0.5 ATR limit | Completed; entry-selection conditions supported the limit convention, but limit entry alone did not solve fill-time risk breaches. | [Protocol](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_followup2_prereg.md), [results](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_followup2_results.md), [review](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_followup2_review.md). |
| Follow-up 3: sizing at the limit | Registered execution-risk test PASS; not a strategy-profitability pass. Informed S0 v2. | [Protocol](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_followup3_prereg.md), [results](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_followup3_results.md), [review](D:/Agentic_ai_project/praman/docs/desk/shadow_replay_followup3_review.md). |

## Forensic research and prior-exposure cross-reference

These remain in their original experiment; this ledger records exposure, not new trading-test IDs or new interpretations. The detailed script/period/outcome inventory is [A/B/C sourcing, section 6](D:/Agentic_ai_project/praman/docs/desk/abc_sourcing_check.md#6-prior-outcome-exposure-inventory-of-work-already-seen).

| Attempt family | Recorded status / scope | Source |
|---|---|---|
| Phase 6 signal development, outcome labels and ensemble | Historical analyses completed; overlapping catalogue exposure includes 2019–2025 and available pre-firewall 2026. | [Phase 6](D:/Agentic_ai_project/praman/docs/phase6_signals.md). |
| Phase 7b classifier comparisons | Historical class/outcome comparisons completed. | [Phase 7b](D:/Agentic_ai_project/praman/docs/phase7b_classification_design.md). |
| Phase 8 layers 2/3, baselines and alternative rankings | Historical evaluation and ranking attempts completed; spent 2026 test period retained as exposed. | [Evaluation](D:/Agentic_ai_project/praman/docs/phase8_evaluation_results.md). |
| Phase 8 robustness and Phase 8b feature selection | Completed; P8-001 discloses contamination of model selection by the spent hold-out. Do not present that evaluation as clean. | [Robustness](D:/Agentic_ai_project/praman/docs/phase8_robustness_checks.md), [feature review](D:/Agentic_ai_project/praman/docs/phase8b_clean_label_features.md). |
| Phase 10 scoring and mechanism preparation | Completed historical preparation; not the protected forward evaluation. | [Amendments](D:/Agentic_ai_project/praman/docs/phase10_preregistration_amendments.md). |
| P8-007 contamination sensitivity | Completed historical sensitivity/repair investigation. | [Scoping](D:/Agentic_ai_project/praman/docs/phase10_p8007_scoping.md), [corrections](D:/Agentic_ai_project/praman/docs/phase10_p8007_corrections.md). |
| Amendment 4 diagnosis, boundary/decay checks and revised-label attempts | Historical repair sequence; superseded limitations remain documented. | [Amendment 4](D:/Agentic_ai_project/praman/docs/phase10_preregistration_amendment4.md), detailed attempt inventory in A/B/C section 6. |
| Amendment 5 bridge prototype and label checks | Historical repair completed; final frozen protocol supersedes earlier label assumptions without deleting them. | [Amendment 5](D:/Agentic_ai_project/praman/docs/phase10_preregistration_amendment5.md). |
| Pinned-label value verification | Historical verification completed; not a separate strategy hypothesis. | [Verification](D:/Agentic_ai_project/praman/docs/desk/label_value_verification.md). |
| Frozen forensic forward evaluation | Pending its binding evaluation; firewall remains active. No result inspected or computed here. | [Frozen registration](D:/Agentic_ai_project/praman/docs/phase10_preregistration.md), amendment 5 above. |

This inventory is based on committed records and the existing exposure register. It cannot certify the absence of undocumented/manual experiments. D–F now have user-supplied descriptions and the R1 dependency above; they remain unregistered ideas, not fully specified experiments.

## Fields to preserve for future registered attempts

For each version: hypothesis; registration/approval date; protocol link; periods and exposure disclosure; all variants and sensitivities; family correction; code commit and input/configuration hashes; rehearsal record; locked results; per-test verdict and failure/inconclusive reasons; supersession history; and any separately approved forward evaluation.

S1 v1 was registered on 19 October 2026. Development recorded 21 October 2026: FAIL at h=1 and h=3 because (a) and (c) failed; LABEL SHOWN at both. Sensitivities, full report and 2025 are pending; 2025 requires separate user approval. [Primary lock note](s1_development_results_20261021_primary.md). Do not remove failed attempts, rewrite locked results, or open S0's seal. Approval of this document alone would not authorise an evaluation.

S1 v1 addendum: **Addendum 1 (20 October 2026): blocked exits**, approved before any
S1 outcome was seen, clarifies that a triggered stop or time exit remains pending
through selling locks and retries at the next available S1-session open, subject
to missing bars and the period boundary. It changes no other rule; S0 is unchanged.
