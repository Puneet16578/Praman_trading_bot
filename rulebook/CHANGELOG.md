# Rulebook changelog

## v2 (2026-10-02) - approved in the round 2 user request

Replace paper_to_live_criteria with separate operational and edge-confidence gates.
Starting small requires 90 elapsed calendar days, 30 closed paper trades, no
unlogged violations or open-risk budget breaches, recorded exits, and no open
high-severity defects. Scaling additionally requires 1,000 opportunities, two
regimes, out-of-sample evaluation, positive expectancy after costs with a bootstrap
95% lower bound above zero, equal-weighted market comparison, and stability across
neighbouring parameters. The analytical edge checks are defined but not yet evaluable.
Unknown risk history or unclassified open defects cannot satisfy the operational gate.
Explicitly record circuit_lock_days=2 and screening_stop_atr_multiple=2, matching
existing defaults. All other numeric risk/liquidity limits remain as in v1.
The v1 file remains unchanged for historical replay.

## v1 (2026-09-27) -- APPROVED, committed

Initial rulebook for Desk Phase 1. `capital_allocated_inr` is the user's own confirmed figure
(Rs 500,000). Every other limit was proposed by Claude with a one-line reason at STOP 2 and
approved by the user, including two schema additions made during STOP 2 review
(`risk.stress_loss_floor_pct_of_position`, `liquidity.participation_pct_of_stressed_volume`) and an
expanded, "ALL of" `paper_to_live_criteria` block. See `desk_rulebook_v1.yaml` for the values and
their reasons.
