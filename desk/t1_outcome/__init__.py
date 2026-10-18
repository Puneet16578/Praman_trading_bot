"""T1 outcome step (user decision 2026-10-18): adverse20 through the outcome firewall, the
standardised risk differences, the coverage, sample-size and spell checks, and the block bootstrap.

Kept apart from desk/t1/, whose features must never touch an outcome (tests/test_t1_features.py).
Built and tested on synthetic fixtures only. Nothing here has been run on real data, and there is
no entry point that loads the real store: the development-period run is a separate, later step.
The choices the pre-registration leaves open are required arguments with no default
(docs/desk/t1_outcome_step.md), so no run can pick one silently.
"""
