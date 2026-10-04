# Shadow replay follow-up 3: size against the limit price

Research only (preregistration `b2df2a2`). The active rulebook, strategy registry and paper conventions are unchanged. Every corrected SCREEN_PASS plan is re-sized with the screening sizing function at L = decision price + 0.5 x ATR20 instead of the decision price; execution uses follow-up 2's frozen limit evidence. No outcome is computed.

**Verdict: PASS.** P1 zero per-trade breaches at the fill: PASS. P2 primary fill rate >= 60%: PASS. Size reduction is reported, not gated.

Intervals: 2,000 event-date-cluster draws, seed 20261001, percentile 95%. Full denominators, date counts and usable draws are in the JSON companion.

## Primary 2019-2025

Passes 45770; quantity reduced for 41170; abstentions (q_L = 0) 1; unknown execution inputs 7.

| Statistic | Estimate [95% CI] |
|---|---|
| Quantity ratio q_L / q, mean | 0.9066 [0.9036, 0.9095]; draws=2000 |
| Quantity ratio, median | 0.9432 [0.9332, 0.9524]; draws=2000 |
| Quantity ratio, p90 | 1.0000 [0.9920, 1.0000]; draws=2000 |
| Quantity ratio p10 / p25 / p50 / p75 / p90 (points) | 0.8014 / 0.8036 / 0.9432 / 0.9837 / 1.0000 |
| Share of passes reduced, % | 89.9497 [89.5191, 90.3373]; draws=2000 |
| Abstention rate, % | 0.0022 [0.0000, 0.0068]; draws=2000 |
| Fill rate, limit-sized, % | 97.0985 [96.7832, 97.3735]; draws=2000 |
| Fill rate, follow-up 2 (frozen size), % | 97.1007 [96.7853, 97.3754]; draws=2000 |
| Fill-rate difference, pp | -0.0022 [-0.0068, 0.0000]; draws=2000 |
| Per-trade breaches at the fill | 0 of 44442 fills |
| Planned loss at decision, % of cap, median (limit-sized / frozen) | 79.1570 [78.9542, 79.3218]; draws=2000 / 84.2080 [83.2294, 85.2994]; draws=2000 |
| Planned loss at fill, % of cap, median (limit-sized / frozen) | 78.6013 [78.0036, 79.1883]; draws=2000 / 86.1429 [85.1266, 87.1288]; draws=2000 |
| Planned loss at fill, % of cap, p90 (limit-sized / frozen) | 95.7533 [95.1536, 96.3279]; draws=2000 / 113.2480 [112.5297, 114.0801]; draws=2000 |

## Descriptive 2026

Passes 7142; quantity reduced for 6439; abstentions (q_L = 0) 0; unknown execution inputs 2.

| Statistic | Estimate [95% CI] |
|---|---|
| Quantity ratio q_L / q, mean | 0.9041 [0.8969, 0.9114]; draws=2000 |
| Quantity ratio, median | 0.9286 [0.9021, 0.9497]; draws=2000 |
| Quantity ratio, p90 | 0.9922 [0.9902, 1.0000]; draws=2000 |
| Quantity ratio p10 / p25 / p50 / p75 / p90 (points) | 0.8015 / 0.8040 / 0.9286 / 0.9831 / 0.9922 |
| Share of passes reduced, % | 90.1568 [89.1124, 91.1229]; draws=2000 |
| Abstention rate, % | 0.0000 [0.0000, 0.0000]; draws=2000 |
| Fill rate, limit-sized, % | 97.6197 [96.3165, 98.4938]; draws=2000 |
| Fill rate, follow-up 2 (frozen size), % | 97.6197 [96.3165, 98.4938]; draws=2000 |
| Fill-rate difference, pp | 0.0000 [0.0000, 0.0000]; draws=2000 |
| Per-trade breaches at the fill | 0 of 6972 fills |
| Planned loss at decision, % of cap, median (limit-sized / frozen) | 79.3917 [78.8770, 79.6281]; draws=2000 / 85.6992 [83.2051, 88.1368]; draws=2000 |
| Planned loss at fill, % of cap, median (limit-sized / frozen) | 77.0025 [75.4933, 78.3803]; draws=2000 / 84.7900 [82.8403, 86.8565]; draws=2000 |
| Planned loss at fill, % of cap, p90 (limit-sized / frozen) | 94.2638 [92.3121, 96.4261]; draws=2000 / 110.8207 [108.2088, 113.7412]; draws=2000 |

## Provenance

```json
{
  "code_commit": "bc46648851f6645238de7e1dae4ada75d69bed01",
  "preregistration_commit": "b2df2a26db997ab028c206741d4c5f6628febaa4",
  "run_date": "2026-10-04",
  "seed": 20261001,
  "bootstrap_replicates": 2000,
  "raw_sha256": "9a71fcf32912a42e69ae207ee3c8ef47d7e84f72f11e00e012198938d6d299a3",
  "execution_path": "data/processed/desk_shadow_followup2_execution.jsonl",
  "execution_sha256": "16b6d22865e9ab109e7a6f20543631644619ef3bbc908c42f254792c8aabbda2",
  "followup2_results_sha256": "61ae68603f5c468d17b00b93ca6a808d094c156761333db3faee160c58d46263",
  "base_results_sha256": "1db07387814bf2d83e1ed94e14fa03bcb160d125a5e8deaa82a6f9cb5e3d1c32",
  "source_hashes": {
    "docs/desk/shadow_replay_followup3_prereg.md": "895221ad576e34aa6d6271fc3ed8cc390fb8b5f8b2358e607fbb086d41c22c2e",
    "desk/shadow_followup3.py": "76491d95bb33ceb91003532c499c041e5b505a55d2fb4e4568fb798309b60189",
    "scripts/desk_shadow_followup3.py": "eed7563f042dc58bfa67b637cb5abc3c67756d9b6332e10e5dad15c06a71ed7e",
    "tests/test_shadow_followup3.py": "25f55023bbaed34875ee0f9765a8bcdd97a80adaabe7916fc8ec32c9ab74d23d",
    "desk/shadow_followup.py": "8a984defd9d95e51fd84e617bfb7be732c244d66cd5ccf18009bd7f16d9cdcad",
    "desk/shadow_followup2.py": "6641b7378d15f3357070a01831108b0163427113f7588100a4333502cfd17190",
    "desk/risk/officer.py": "b18d806e3d60f88adc371ce922127bbc61f5f59c63734616d335ff3a88d05d22"
  },
  "passes": 52912,
  "command": "python -u scripts/desk_shadow_followup3.py",
  "database_access": "None: frozen artifacts only."
}
```
