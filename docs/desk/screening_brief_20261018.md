# Screening brief wording (18 October 2026)

The passed-count label now reads:

Passed screening (G1–G6: data, evidence, structure, surveillance, liquidity, per-trade risk)

The stored SCREEN_PASS state means every G1-G6 result passed (`desk/gates/engine.py`).
The new rejection line reads stored gate results, counts each rejected candidate
once overall, and each non-passing gate/category once per candidate. Gate totals
may overlap. Only fixed category names are displayed; no raw reasons are rendered.
The "of which" stressed-exit count measures the actual overlap with turnover failures.

Rendered from the real Desk store read-only for 14 October, using only
`screening_rejection_line`; no brief file was written or overwritten:

```text
Rejected at screening: 10 (G5 liquidity 8: over 1% of average turnover 8, of which stressed exit over 3 sessions 4; G4 surveillance 2: ASM 2; G1 data 0, G2 evidence 0, G3 structure 0, G6 per-trade risk 0)
```

Validation: `python -B -m unittest tests.test_desk_brief` — 16 tests, OK.
No decision logic changed. P8-086 records the display defect and repair.
