# Round-2 completion check

Verified 2026-10-04 from repository source, Git history, stored evidence and the
full baseline suite: 610 tests in 227.455s, OK, Python exit 0. Existing SQLite
ResourceWarnings remain. Initial HEAD was `64ac2f1`, synced with origin/master.
The pre-existing risk-test trailing blank line and local scratch files were preserved.

| Item | Status and evidence | Commit |
|---|---|---|
| Desk-store incident and guard | Done. Incident documented without claiming lost band history was recovered. Filesystem guard protects durable paths; SQL authorizer blocks fact UPDATE/DELETE/DROP on normal connections. Temporary-store tests exercise both. Live Desk has 0 decisions/theses/trades, 580 opportunities, 545 executions, 3,574 bands. Guards are application-level, not Windows access controls. | `9b6179e` (P8-025); inventory refresh `67df697` |
| Firewall consolidation | Done. `desk/outcomes.py` is absent; callers use `desk/outcome_firewall.py` and the IST clock. Boundary and single-owner tests pass. | `07b916d` (P8-026) |
| Label comparison by value | Done. Five full current/pinned result dictionaries in `label_value_verification.json` compare exactly; the label-source diff against `afe3e2b` is empty. This is same-input code equivalence, not proof of the pinned data vintage. | `6849096`; five comparisons rerun and documented in `67df697` |
| pytz | Done as environment support, not a source change. Installed pytz 2026.4 and empyrical-reloaded 0.5.12 verified. No pytz references in `desk/` or `src/`. The empyrical drawdown cross-check passes in the full suite. | Finding recorded in `128d703`; no commit for the environment-only installation |
| Evaluator process definition | Done. Requires complete timely entry thesis/decision, no unlogged violations, no G7 override, and a matching recorded trigger or reasoned manual-close request before exit. A matching exit string alone is insufficient. Ten adversarial tests pass. | `128d703` (P8-028) |
| Line endings and encoding | Handoff is UTF-8 with no NUL bytes; Desk Markdown has an LF checkout rule. One missed mixed-encoding `.gitignore` fragment was repaired in this confirmation (P8-036); `git check-ignore` now recognizes scratch. Scratch files were neither deleted nor tracked. | `9b6179e` (handoff); `07b916d` (LF policy); P8-036 repair in this document's commit |
| Rulebook v2 | Done and active. Typed operational and edge-confidence gates, two-day circuit lock and 2xATR screening stop. V1 has no subsequent diff. Live read-only progress: operational NOT_MET, edge NOT_EVALUABLE. These are unmet evidence requirements, not an unfinished activation. | `2986e10`; later full suites verify committed activation |
| Research G2 sector applicability and diagnostics | Done. Research omits user sector applicability, without inventing sector evidence; normal assessments retain it. Final temporary-copy proof: 540 candidates, 403 pass / 137 fail, 505 execution records. Historical fixed sample: 158 pass / 42 fail. | `73f2ce4` (P8-027/P8-029); final proof `67df697` |
| Foreground runner, temporal queries and source provenance | Done. Sequential temporary-copy runner, registered global-session tails, one unchanged label function, and event-date-cluster uncertainty. G1 knowledge cutoffs and source-path handling repaired. | `bafd371` (P8-031/P8-032/P8-033) |
| Historical identities | Done. Preserve historical identities and give current observations precedence. Recorded recovery restored 32 missing identities and corrected 51 conflicts; full catalogue identity check passed. | `ec12bc4` (P8-034) |
| Denominators and sparse comparisons | Done. Every G1-G6 group is represented, including empty groups; warnings use each statistic's valid events/date clusters. | `67df697` (P8-035) |
| Full historical replay | Done. 70,362 events, all four cohort summaries, hashes and 640 statistic checks. No tuning followed results. | `64ac2f1` |

No requested round-2 item remains unfinished after the P8-036 repair. Existing
unrelated open defects P8-007 and P8-021 remain visible to readiness checks and
are not claimed fixed by this confirmation. Old handoff sections are historical;
their earlier pending status does not supersede later completion evidence.
