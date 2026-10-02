# Rulebook v2 - 2026-10-02

The user-approved v2 replaces paper_to_live_criteria with operational_gate
(start live trading small) and edge_confidence_gate (scale later). V1 is unchanged.
All numeric requirements are in rulebook/desk_rulebook_v2.yaml and its changelog.

Operational status uses elapsed calendar days since the first recorded paper
entry, closed trades, the process audit and journal, historical recorded stress
exposure, recorded exit provenance and the defect register. Missing historical
stress evidence or an open defect without a severity is unverified and cannot
satisfy the gate. Historical ADJUST events lack a persisted updated stress loss,
so those histories need an auditable risk evaluation before qualification.

Edge status reports logged opportunities and explicitly recorded market regimes.
No regime is inferred from price moves or supplied by an LLM. Out-of-sample,
after-cost bootstrap expectancy, equal-weighted market comparison and neighbouring
parameter stability remain NOT_EVALUABLE until their registered evaluator exists.
The current shadow gate comparison is not that evaluation and cannot qualify
scaling. Passing the operational gate never implies passing the edge gate.

The current register still marks P8-007 critical/found-not-fixed; P8-021 is open
without a severity. These are surfaced as blockers, not silently reclassified.
The current Desk has no paper-trade history.

V2 schema and progress tests load the new file directly before activation because
the live versioned loader correctly refuses uncommitted configuration. The live
loader is verified again after committing the ACTIVE pointer.
