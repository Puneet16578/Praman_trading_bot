# T1 2025 random-label rehearsal

No real outcomes read. The reader and firewall entry points raised throughout the rehearsal.
2025 PARTIALLY EXPOSED. Decisions and outcome windows within 2025; warm-up before 2025 permitted.
Read ceiling 2025-12-31; fixed development boundaries and weights; registered settings unchanged.

Runtime seconds: {'load': 25.8, 'features': 20.8, 'rehearsal': 0.4, 'total': 47.1}; peak working set bytes: 2657398784.
Decision sessions: 228 (2025-01-01 to 2025-12-02).
Eligible stock-days: 395621; identity exclusions: 21301.
Complete windows: 386055 (97.5820292654%).
Purged sessions: ['2025-12-03', '2025-12-04', '2025-12-05', '2025-12-08', '2025-12-09', '2025-12-10', '2025-12-11', '2025-12-12', '2025-12-15', '2025-12-16', '2025-12-17', '2025-12-18', '2025-12-19', '2025-12-22', '2025-12-23', '2025-12-24', '2025-12-26', '2025-12-29', '2025-12-30', '2025-12-31'].
Locked boundaries: [3.1605964603389842, 3.9592760180995112, 4.76384909369999, 5.857440286897999].
Locked weights: {1: 0.2, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.2}; used weights: {1: 0.2, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.2}; exact equality verified.

| Variant | Coverage | Smallest valid cell | Fewest dates | Spells | Usable draws | Unusable draws |
|---|---:|---:|---:|---:|---:|---:|
| V1 | 100.0000000000% | 12076 | 97 | 1 | 1718 | 282 |
| V2 | 100.0000000000% | 24214 | 83 | 2 | 1715 | 285 |
| V3 | 100.0000000000% | 19853 | 224 | None | 2000 | 0 |

## V1

| Cell | Candidates | Valid windows | Dates |
|---|---:|---:|---:|
| adverse q1 | 15792 | 15749 | 97 |
| adverse q2 | 27283 | 27027 | 97 |
| adverse q3 | 35939 | 35324 | 97 |
| adverse q4 | 42128 | 40971 | 97 |
| adverse q5 | 42004 | 39689 | 97 |
| other q1 | 90430 | 90025 | 131 |
| other q2 | 61975 | 61160 | 131 |
| other q3 | 40348 | 39322 | 131 |
| other q4 | 26196 | 24712 | 131 |
| other q5 | 13526 | 12076 | 131 |

| State | Stock-days | Complete windows | Share |
|---|---:|---:|---:|
| adverse | 163146 | 158760 | 97.3116104593% |
| other | 232475 | 227295 | 97.7718034197% |
| unknown | 0 | 0 | unavailable |

Input-only failures: ['1718 usable bootstrap draws, fewer than 1,900', '1 spells, fewer than 5']

## V2

| Cell | Candidates | Valid windows | Dates |
|---|---:|---:|---:|
| adverse q1 | 38021 | 37824 | 83 |
| adverse q2 | 30479 | 30146 | 83 |
| adverse q3 | 25878 | 25553 | 83 |
| adverse q4 | 25205 | 24636 | 83 |
| adverse q5 | 25546 | 24214 | 83 |
| other q1 | 68201 | 67950 | 145 |
| other q2 | 58779 | 58041 | 145 |
| other q3 | 50409 | 49093 | 145 |
| other q4 | 43119 | 41047 | 145 |
| other q5 | 29984 | 27551 | 145 |

| State | Stock-days | Complete windows | Share |
|---|---:|---:|---:|
| adverse | 145129 | 142373 | 98.1009998002% |
| other | 250492 | 243682 | 97.2813503026% |
| unknown | 0 | 0 | unavailable |

Input-only failures: ['1715 usable bootstrap draws, fewer than 1,900', '2 spells, fewer than 5']

## V3

| Cell | Candidates | Valid windows | Dates |
|---|---:|---:|---:|
| adverse q1 | 64137 | 63922 | 224 |
| adverse q2 | 51954 | 51499 | 228 |
| adverse q3 | 41763 | 41133 | 228 |
| adverse q4 | 37429 | 36485 | 228 |
| adverse q5 | 33936 | 31912 | 228 |
| other q1 | 42085 | 41852 | 228 |
| other q2 | 37304 | 36688 | 228 |
| other q3 | 34524 | 33513 | 228 |
| other q4 | 30895 | 29198 | 228 |
| other q5 | 21594 | 19853 | 228 |

| State | Stock-days | Complete windows | Share |
|---|---:|---:|---:|
| adverse | 229219 | 224951 | 98.1380252073% |
| other | 166402 | 161104 | 96.8161440367% |
| unknown | 0 | 0 | unavailable |

Input-only failures: []

## Development regression and artifact integrity

```json
{
  "development_regression": {
    "reference": "data/t1/rehearsal_20261018T105905Z.json",
    "current": "data\\t1\\rehearsal_20261018T161737Z.json",
    "analytical_fields_identical": true,
    "current_sha256": "4b09754265f68251f2d71c60596f0cc29c3c940303783e5ba12d0958644c96ff",
    "prior_seconds": {
      "load": 12.2,
      "features": 17.9,
      "rehearsal": 1.7,
      "total": 31.9
    },
    "current_seconds": {
      "load": 11.6,
      "features": 15.7,
      "rehearsal": 1.7,
      "total": 29.0
    },
    "prior_peak_memory": 2100277248,
    "current_peak_memory": 2098688000
  },
  "development_hashes_before": {
    "docs/desk/t1_development_results_20261018.md": "f8b65100574d19f16026b04722dc5c6c05df84e7a35577e89255c51262439483",
    "docs/desk/t1_development_manifest_20261018.json": "3ef3bf6bbfee0f13e67ed15b1e9f935b1b7aed490f219c18b812ef724fa7408b",
    "data/t1/development_20261018.json": "023f1828e1fdc5cce93de987ca83a71c7deedb13ca163021c608e9f9d90579f8",
    "data/t1/development_20261018.started.json": "1fc5a98286153062d89aa322dc7c16046d72b45a5587029df0ba83c265b2d377"
  },
  "development_hashes_after": {
    "docs/desk/t1_development_results_20261018.md": "f8b65100574d19f16026b04722dc5c6c05df84e7a35577e89255c51262439483",
    "docs/desk/t1_development_manifest_20261018.json": "3ef3bf6bbfee0f13e67ed15b1e9f935b1b7aed490f219c18b812ef724fa7408b",
    "data/t1/development_20261018.json": "023f1828e1fdc5cce93de987ca83a71c7deedb13ca163021c608e9f9d90579f8",
    "data/t1/development_20261018.started.json": "1fc5a98286153062d89aa322dc7c16046d72b45a5587029df0ba83c265b2d377"
  }
}
```
