# T1 locked 2025 hold-out results

Hold-out only: decisions and outcome windows inside 2025; pre-2025 warm-up reads allowed. **2025: PARTIALLY EXPOSED**; prior shadow studies viewed aggregate adverse-move rates, but no trading model was fitted or selected on it. No input or outcome payload after 2025-12-31 was opened for this run.

Code commit before the run: `250df4cad6c84df237b2775427145cba5fe57d74`. Input hashes were recorded before real outcome access;
the complete manifest is reproduced below. Results are locked; no threshold or setting was changed after outcome access.

Timing ASSUMPTIONS: same-session EQ bars subject to their stored knowledge dates; index/VIX through D-1; ISIN snapshots from S+1, ignoring October download dates. Missing inputs remain missing, including the five late-known sessions and 2022-08-08. Weekend sessions excluded everywhere.

Eligible stock-days: 395621; identity-exclusion category: **21301**.
Identity exclusions include rows that also fail fund/ATR conditions; they are not all otherwise eligible equities.
Decision sessions: 228, 2025-01-01 to 2025-12-02.
Purged sessions (20): 2025-12-03, 2025-12-04, 2025-12-05, 2025-12-08, 2025-12-09, 2025-12-10, 2025-12-11, 2025-12-12, 2025-12-15, 2025-12-16, 2025-12-17, 2025-12-18, 2025-12-19, 2025-12-22, 2025-12-23, 2025-12-24, 2025-12-26, 2025-12-29, 2025-12-30, 2025-12-31.
Purged bars complete the final windows but supply no decisions or bootstrap dates. Empty dates remain in blocks.

Features and adverse20 share price inputs and the decision-close anchor. Volatility quintiles reduce imbalance but do not remove mechanical coupling or establish causation. These are historical conditional associations, not profitability, calibration, readiness or permission to change live risk limits.

## Frozen quintiles and baseline V0

ATR% linear quintile boundaries: [3.1605964603389842, 3.9592760180995112, 4.76384909369999, 5.857440286897999]. Ties go upward.
Development candidate weights (including missing outcomes): {1: 0.2, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.2}.

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| V0 q1 | 106222 | 105774 | 448 | 228 | 1967 | 1.85962524 |
| V0 q2 | 89258 | 88187 | 1071 | 228 | 4016 | 4.55395920 |
| V0 q3 | 76287 | 74646 | 1641 | 228 | 5623 | 7.53288857 |
| V0 q4 | 68324 | 65683 | 2641 | 228 | 7277 | 11.07897021 |
| V0 q5 | 55530 | 51765 | 3765 | 228 | 7782 | 15.03332367 |

## Preregistered decisions

All differences and interval endpoints below are percentage points. Family intervals are 98.333333% (three contrasts); 95% intervals are descriptive. Bootstrap: 2,000 draws, seed 20261001, 60-session blocks for V1/V2 and 20 for V3; linear percentiles. Every usable draw meets all cell sample minimums.

| Variant | Verdict | Standardised difference pp | Family interval pp | 95% interval pp | Positive quintiles | State coverage | Usable / unusable | Spells |
|---|---|---:|---|---|---:|---:|---|---|
| V1 | INCONCLUSIVE | 5.26446789 | [-2.69681851, 13.12989538] | [-2.27453232, 11.69274235] | 5/5 | 100.00000000% | 1718 / 282 | 1 |
| V2 | INCONCLUSIVE | 2.75591813 | [-1.23308042, 8.18126362] | [-1.02638122, 6.70965987] | 4/5 | 100.00000000% | 1715 / 285 | 2 |
| V3 | not met | -0.77197864 | [-2.14217082, 0.94409393] | [-1.91878297, 0.74107580] | 1/5 | 100.00000000% | 2000 / 0 | not required |

## V1: full cells and comparisons

Decision reasons: 1718 usable bootstrap draws, fewer than 1,900; 1 spells, fewer than 5

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse q1 | 15792 | 15749 | 43 | 97 | 518 | 3.28909772 |
| adverse q2 | 27283 | 27027 | 256 | 97 | 1960 | 7.25200725 |
| adverse q3 | 35939 | 35324 | 615 | 97 | 3824 | 10.82550108 |
| adverse q4 | 42128 | 40971 | 1157 | 97 | 5750 | 14.03431696 |
| adverse q5 | 42004 | 39689 | 2315 | 97 | 6582 | 16.58394013 |
| other q1 | 90430 | 90025 | 405 | 131 | 1449 | 1.60955290 |
| other q2 | 61975 | 61160 | 815 | 131 | 2056 | 3.36167430 |
| other q3 | 40348 | 39322 | 1026 | 131 | 1799 | 4.57504705 |
| other q4 | 26196 | 24712 | 1484 | 131 | 1527 | 6.17918420 |
| other q5 | 13526 | 12076 | 1450 | 131 | 1200 | 9.93706525 |

| Quintile | Risk difference pp | Risk ratio (secondary) | Predicted positive sign |
|---|---:|---:|---|
| 1 | 1.67954482 | 2.04348532 | True |
| 2 | 3.89033296 | 2.15726052 | True |
| 3 | 6.25045403 | 2.36620541 | True |
| 4 | 7.85513275 | 2.27122489 | True |
| 5 | 6.64687488 | 1.66889718 | True |

Outcome availability by state (no availability threshold):

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse | 163146 | 158760 | 4386 | 97 | 18634 | 11.73721340 |
| other | 232475 | 227295 | 5180 | 131 | 8031 | 3.53329374 |
| unknown | 0 | 0 | 0 | 0 | 0 | unavailable |

Matched V0: 386055 rows, 97.58202927% of eligible stock-days;
standardised rate 8.01175338%; descriptive 95% [2.02025413, 10.18652815];
family [1.75308590, 11.22615554]; usable paired draws 1718.
Both variant state and outcome must be known. Same draws and usable-draw mask as the contrast.

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| matched V0 q1 | 105774 | 105774 | 0 | 228 | 1967 | 1.85962524 |
| matched V0 q2 | 88187 | 88187 | 0 | 228 | 4016 | 4.55395920 |
| matched V0 q3 | 74646 | 74646 | 0 | 228 | 5623 | 7.53288857 |
| matched V0 q4 | 65683 | 65683 | 0 | 228 | 7277 | 11.07897021 |
| matched V0 q5 | 51765 | 51765 | 0 | 228 | 7782 | 15.03332367 |

| Spell | First | Last | Adverse sessions |
|---:|---|---|---:|
| 1 | 2025-01-07 | 2025-06-04 | 97 |

## V2: full cells and comparisons

Decision reasons: 1715 usable bootstrap draws, fewer than 1,900; 2 spells, fewer than 5

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse q1 | 38021 | 37824 | 197 | 83 | 701 | 1.85332064 |
| adverse q2 | 30479 | 30146 | 333 | 83 | 1618 | 5.36721290 |
| adverse q3 | 25878 | 25553 | 325 | 83 | 2507 | 9.81098110 |
| adverse q4 | 25205 | 24636 | 569 | 83 | 3478 | 14.11755155 |
| adverse q5 | 25546 | 24214 | 1332 | 83 | 4185 | 17.28338977 |
| other q1 | 68201 | 67950 | 251 | 145 | 1266 | 1.86313466 |
| other q2 | 58779 | 58041 | 738 | 145 | 2398 | 4.13156217 |
| other q3 | 50409 | 49093 | 1316 | 145 | 3116 | 6.34713707 |
| other q4 | 43119 | 41047 | 2072 | 145 | 3799 | 9.25524399 |
| other q5 | 29984 | 27551 | 2433 | 145 | 3597 | 13.05578745 |

| Quintile | Risk difference pp | Risk ratio (secondary) | Predicted positive sign |
|---|---:|---:|---|
| 1 | -0.00981401 | 0.99473253 | False |
| 2 | 1.23565073 | 1.29907591 | True |
| 3 | 3.46384403 | 1.54573330 | True |
| 4 | 4.86230756 | 1.52535704 | True |
| 5 | 4.22760233 | 1.32381060 | True |

Outcome availability by state (no availability threshold):

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse | 145129 | 142373 | 2756 | 83 | 12489 | 8.77202840 |
| other | 250492 | 243682 | 6810 | 145 | 14176 | 5.81741778 |
| unknown | 0 | 0 | 0 | 0 | 0 | unavailable |

Matched V0: 386055 rows, 97.58202927% of eligible stock-days;
standardised rate 8.01175338%; descriptive 95% [2.26381048, 10.27880343];
family [2.02505418, 11.29240884]; usable paired draws 1715.
Both variant state and outcome must be known. Same draws and usable-draw mask as the contrast.

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| matched V0 q1 | 105774 | 105774 | 0 | 228 | 1967 | 1.85962524 |
| matched V0 q2 | 88187 | 88187 | 0 | 228 | 4016 | 4.55395920 |
| matched V0 q3 | 74646 | 74646 | 0 | 228 | 5623 | 7.53288857 |
| matched V0 q4 | 65683 | 65683 | 0 | 228 | 7277 | 11.07897021 |
| matched V0 q5 | 51765 | 51765 | 0 | 228 | 7782 | 15.03332367 |

| Spell | First | Last | Adverse sessions |
|---:|---|---|---:|
| 1 | 2025-01-06 | 2025-04-09 | 37 |
| 2 | 2025-07-28 | 2025-12-02 | 46 |

## V3: full cells and comparisons

Decision reasons: standardised difference -0.0077 below 0.01; family-adjusted interval lower bound -0.0214 not above zero; positive sign in 1 of 5 quintiles

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse q1 | 64137 | 63922 | 215 | 224 | 1195 | 1.86946591 |
| adverse q2 | 51954 | 51499 | 455 | 228 | 2271 | 4.40979436 |
| adverse q3 | 41763 | 41133 | 630 | 228 | 3018 | 7.33717453 |
| adverse q4 | 37429 | 36485 | 944 | 228 | 3851 | 10.55502261 |
| adverse q5 | 33936 | 31912 | 2024 | 228 | 4562 | 14.29556280 |
| other q1 | 42085 | 41852 | 233 | 228 | 772 | 1.84459524 |
| other q2 | 37304 | 36688 | 616 | 228 | 1745 | 4.75632359 |
| other q3 | 34524 | 33513 | 1011 | 228 | 2605 | 7.77310297 |
| other q4 | 30895 | 29198 | 1697 | 228 | 3426 | 11.73368039 |
| other q5 | 21594 | 19853 | 1741 | 228 | 3220 | 16.21921120 |

| Quintile | Risk difference pp | Risk ratio (secondary) | Predicted positive sign |
|---|---:|---:|---|
| 1 | 0.02487067 | 1.01348300 | True |
| 2 | -0.34652923 | 0.92714347 | False |
| 3 | -0.43592844 | 0.94391835 | False |
| 4 | -1.17865778 | 0.89954918 | False |
| 5 | -1.92364840 | 0.88139692 | False |

Outcome availability by state (no availability threshold):

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse | 229219 | 224951 | 4268 | 228 | 14897 | 6.62233109 |
| other | 166402 | 161104 | 5298 | 228 | 11768 | 7.30459827 |
| unknown | 0 | 0 | 0 | 0 | 0 | unavailable |

Matched V0: 386055 rows, 97.58202927% of eligible stock-days;
standardised rate 8.01175338%; descriptive 95% [2.98367212, 13.06712871];
family [2.57636716, 14.33710726]; usable paired draws 2000.
Both variant state and outcome must be known. Same draws and usable-draw mask as the contrast.

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| matched V0 q1 | 105774 | 105774 | 0 | 228 | 1967 | 1.85962524 |
| matched V0 q2 | 88187 | 88187 | 0 | 228 | 4016 | 4.55395920 |
| matched V0 q3 | 74646 | 74646 | 0 | 228 | 5623 | 7.53288857 |
| matched V0 q4 | 65683 | 65683 | 0 | 228 | 7277 | 11.07897021 |
| matched V0 q5 | 51765 | 51765 | 0 | 228 | 7782 | 15.03332367 |

## Input exclusions by hold-out year

| Year | Cause | Stock-days |
|---|---|---:|
| 2025 | eligible | 395621 |
| 2025 | atr_window_incomplete | 11981 |
| 2025 | atr_window_unadjustable | 993 |
| 2025 | fund_unit | 52516 |
| 2025 | identity_unknown | 21301 |

## Descriptive input coverage and distributions (no extra contrasts)

| Feature | Known | Total | Min / Q25 / median / Q75 / max |
|---|---:|---:|---|
| share_above50 | 228 | 228 | [0.04179471419791026, 0.24864539434075858, 0.3623649483091933, 0.6115474846425613, 0.893491124260355] |
| share_above200 | 228 | 228 | [0.07826747720364742, 0.21990146780890893, 0.383978093521662, 0.454506315212026, 0.5574144486692015] |
| net_breadth | 228 | 228 | [-0.9163916391639164, -0.38787295793951604, -0.0830496562221716, 0.23446890278481272, 0.9241071428571429] |
| new_high_rate | 228 | 228 | [0.0, 0.006096255025186476, 0.013540681998413958, 0.02113503907457283, 0.03274760383386582] |
| new_low_rate | 228 | 228 | [0.0, 0.0032, 0.011881607428553502, 0.03771287952925029, 0.35771704180064307] |
| dispersion | 228 | 228 | [0.016930297423979526, 0.021938700295453986, 0.02353090613161812, 0.026096891936470214, 0.041345715632825075] |
| atr_pct | 395621 | 395621 | [0.4794578929424263, 3.093025990826748, 3.9811526905216965, 5.095751528805879, 22.490226739640335] |
| rel_ew_1 | 395621 | 395621 | [-0.4845138729443155, -0.012344758612480664, -0.0021031165436321965, 0.009475449767061769, 0.3372720159634192] |
| rel_ew_5 | 395621 | 395621 | [-0.5395898908244708, -0.02838708883514969, -0.005276710425568619, 0.021454688101772056, 1.0675504662204933] |
| rel_ew_20 | 395621 | 395621 | [-0.6010797095794568, -0.061639434889213605, -0.015135638748536533, 0.04152752441990154, 1.5669468279861998] |
| rel_ew_60 | 369839 | 395621 | [-0.6436600221424822, -0.11551252692274563, -0.03686722880542083, 0.06058371389902509, 2.624634137164947] |
| rel_n50_1 | 395621 | 395621 | [-0.5057275489522481, -0.01391531889480524, -0.002318300027899123, 0.009972841950939948, 0.3303043245399402] |
| rel_n50_5 | 395621 | 395621 | [-0.5471856422401011, -0.03399569868298746, -0.007552658375854393, 0.021331459133986597, 1.0309101638813425] |
| rel_n50_20 | 394972 | 395621 | [-0.6119790925275208, -0.07667284901070173, -0.024831155933303373, 0.03550502169745268, 1.319339792304287] |
| rel_n50_60 | 369250 | 395621 | [-0.7276331653716557, -0.14242217069582203, -0.04938508725950336, 0.056412837855793374, 2.5761392916001746] |

Descriptive NIFTY 50 trend (D-1): {'known': 228, 'unknown': 0, 'below_average': 73}.

## Input manifest recorded before outcome access

```json
{
  "code_commit": "250df4cad6c84df237b2775427145cba5fe57d74",
  "started_at": "2026-10-18T16:19:23.895273+00:00",
  "read_end": "2025-12-31",
  "decision_period": [
    "2025-01-01",
    "2025-12-31"
  ],
  "settings": {
    "weekends": "exclude",
    "coverage_numerator": "state_known",
    "usable": "computable_with_sample_minimums",
    "method": "linear",
    "replicates": 2000,
    "seed": 20261001,
    "blocks": {
      "V1": 60,
      "V2": 60,
      "V3": 20
    }
  },
  "development_hashes_before": {
    "docs/desk/t1_development_results_20261018.md": "f8b65100574d19f16026b04722dc5c6c05df84e7a35577e89255c51262439483",
    "docs/desk/t1_development_manifest_20261018.json": "3ef3bf6bbfee0f13e67ed15b1e9f935b1b7aed490f219c18b812ef724fa7408b",
    "data/t1/development_20261018.json": "023f1828e1fdc5cce93de987ca83a71c7deedb13ca163021c608e9f9d90579f8",
    "data/t1/development_20261018.started.json": "1fc5a98286153062d89aa322dc7c16046d72b45a5587029df0ba83c265b2d377"
  },
  "locked_weights": {
    "1": 0.2,
    "2": 0.2,
    "3": 0.2,
    "4": 0.2,
    "5": 0.2
  },
  "used_weights": {
    "1": 0.2,
    "2": 0.2,
    "3": 0.2,
    "4": 0.2,
    "5": 0.2
  },
  "locked_quintile_bounds": [
    3.1605964603389842,
    3.9592760180995112,
    4.76384909369999,
    5.857440286897999
  ],
  "source_sha256": {
    "desk/outcome_firewall.py": "27c380410f8b33c2afe81607db1610eba837048f13312394bf38cc7c3167b9bb",
    "desk/t1/__init__.py": "443f14e2664168a3de4bafcd8f4e018050a6956315dfa01def4c7783e7c49398",
    "desk/t1/bootstrap.py": "efde9307f64b221e9463193ba9ad23d1306960e9c8db2da77685480bb28a1dd8",
    "desk/t1/build.py": "f34067ba28c21918fb300470b0e96b0ab1a302aa34c3357eef274eaa68737eaa",
    "desk/t1/features.py": "d26ae854c8ff180387314e0a0df6dfeba24bf5c9ba9450e05d2d56dfd8bd983e",
    "desk/t1/inputs.py": "06d9e7f1c1174c63cb3d1ddf390cbc9a4a430aeceebb34d96ea786e5040afcae",
    "desk/t1/panel.py": "9c594c0c1c640595653897310a30f4f1f980f0a0395c18746d32e3a512fcf3e5",
    "desk/t1/provenance.py": "103705d685ded020b3880178fdaada803b566eea72f820c3958c0f407b407554",
    "desk/t1/read_guard.py": "47e20d7f29c618814e9fdef67778b29a739892e6a94e7c2c5ee5c06e75bf93d7",
    "desk/t1_outcome/__init__.py": "4d836b5004ef621512ea74817c98660f7b45b529ee4a004d99a396a2251f24fb",
    "desk/t1_outcome/contrasts.py": "457da09cb6ccfdcb127a85f28a86497597eaf57defbcf4d17cd8350d799f963a",
    "desk/t1_outcome/development.py": "21d72f553500e03b2d5108ef16b5a95db891d1481dbb1e5708a610955326f118",
    "desk/t1_outcome/holdout.py": "8bc281467d12378d139ab0b069fb07dc48e734064a219cb078da3bd15eefe689",
    "desk/t1_outcome/reader.py": "59b060b39199583594cdcaf0a237bd49ea7ec25a50a61e2eb7bbaa4323a29625",
    "desk/t1_outcome/rehearsal.py": "c1922d22ea5e7b8542f5f29098cd15fc7ccb54f61c8a7ba52ec02f695195a441",
    "desk/t1_outcome/uncertainty.py": "b3f859791a9821688441dbd60485be31c7e285750ed9518214ef70d9e62e0d23",
    "docs/desk/t1_market_context_prereg.md": "93768152e929ce5bc1e9d78a3ac9af3236e6fced6c648e26142990140a03cfd6",
    "scripts/t1_holdout.py": "6a8a546cd64537ba147ef49f8ece7b540b0eafbbba81f7f9df31e4cdc40db0b7",
    "scripts/t1_rehearsal.py": "f1d655684ceeebe02c7382d08530c576ac6d62956afeff25218e6e7fe48a8c95"
  },
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
  "inputs": {
    "files": {
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2019-11-15.csv": "df3f8a576f3e899dfb43d1cd9ec2609951d535c2d4b78cc68305334def91ab2f",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2019-11-15.csv.sha256.json": "f15b366bb84c93d83f8b357a4d664bd067252c15fb6b420a718a99c5a4c1d1c5",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2020-06-15.csv": "fecd922cc8678c8a0682e3fbd9633ec28465ee9d009ded5cbe8ad146badcee44",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2020-06-15.csv.sha256.json": "533079e3960213c51652fa5da920cb88634d5a52cc0cd8292ac58c59f64f5750",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2021-02-17.csv": "d27f5ccec57175890a5478441cad72d0375bc7757c8665222ad8f5f3d5df6963",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2021-02-17.csv.sha256.json": "e4f58ae95e113486446444d73f642d368177f977f9310832d1585b0a5e1e76cc",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2021-06-15.csv": "c6acb12373e9ae0a039d7e1c9227e05d7701b148bc075ef889226129ee67090e",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2021-06-15.csv.sha256.json": "b7f0e271db3241c7d3923b5fd8e1afaab51c4ef38a9838c5b90454e2b4d78fe3",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2021-07-22.csv": "9036368698180b6f9cd540296ddec3d50bed1ec94c4de21a2809c722c3984c72",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2021-07-22.csv.sha256.json": "e1c854f8b32accda87826c39f2307feb2f7d9385d9c75bd8971f51e8ae24ddde",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2022-06-15.csv": "dc5e610a0aea45b272241961e0cbd6e0ab04841660c8bfaa7019f5fe1cb7a93e",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2022-06-15.csv.sha256.json": "6a7cfd25b92494f5ed64387278b3596e50c07c0042ea750b8893e6c4731870a2",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2023-06-15.csv": "13b6b8c62bfa7489ef5214a37b1885a5f399be4cc636e70b4637e6c5f2e2a51c",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2023-06-15.csv.sha256.json": "e77c7ea3749c076fa10b4f05243f30b42a008b77be889f02ece08026f89d6026",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2025-02-04.csv": "0bde3f85279e4361a52f69bba2726fcb41eb815e776056451652e39053c3b855",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2025-02-04.csv.sha256.json": "5c0498e0ef04e84e2510f15cf05146eea585776baf9d7a72cb489a9795421dcf",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2025-06-16.csv": "da4749aea64a308b6435e1844607af5a76e2f8e0321d1dce15d45cb9f3c720ae",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2025-06-16.csv.sha256.json": "4f5810f3ea29288c50589a8f47f61e1fbccac2c3511b6703e5625480260dba08",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2025-10-13.csv": "a8e081199e26d39ec0327ea57215825ffb36d3f25fe6000b48b3f2ef79ff1866",
      "D:/Agentic_ai_project/praman/data/raw/isin_snapshots/cm_2025-10-13.csv.sha256.json": "5be8a0066e4b29ca8d51b5936d3ccd0b098167910a94d1433872f6ce61af28e3",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/02_snapshot_2018-09-03.csv": "1806666e72eab44182cf5957df5049a11234a20874dc8c5711cbfbe1f7da81a7",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/03_snapshot_2018-12-03.csv": "25edf69766866f1071b7a2ab27b070edc83a459474f9cf3e84824ff439c1e58c",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/04_snapshot_2019-02-04.csv": "7d6428f3efee734ec5a6452fc2fc68bf0d423acd2244094dc02504dbde2339db",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/05_snapshot_2019-08-01.csv": "cb5f8b3487eb1b22eac5b444ca045296ba542e2c048d95e492e742ceab738123",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/06_snapshot_2020-02-03.csv": "118d418ac13e5e1eb2271714c8555cdc23d0ce5eaabf0392dcb25cd2e42cbdfe",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/07_snapshot_2020-08-03.csv": "32933b84cd09b85eecfe6982dd2498c31146beba732bb63780aaa7e52934f1be",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/08_snapshot_2021-02-03.csv": "f577f222009be4aed30c96dc52205a457827122c056b285d57da34322ff8a69b",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/09_snapshot_2021-08-03.csv": "e8ada1a2c411a77151784207f47392f18b67d2016ba485c64fa7a4ef0cf65bbe",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/10_snapshot_2022-02-03.csv": "da89deab05ea27d8ca5f5b2912f1f657fb3a42d3c4b9a5e89a6020c8cc7804a9",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/11_snapshot_2022-08-03.csv": "49325f89112d7a9dba2efc8fa1a29272fc4bc516d4ad46205d60ca04eea62e24",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/12_snapshot_2023-02-03.csv": "b63ae4e18e393e844d921c37f238d824fc4daae16b73ac30caff04f706159729",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/13_snapshot_2023-08-03.csv": "1caa2fddd845bd205b68ecbdb81c172a5f15b3d1a054b9d2db91f20e07164e9d",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/14_snapshot_2024-02-05.csv": "7de1f9c6c213e78573944c59da11df6cfd6198fa8ccaa021e3717692ceb73a43",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/15_snapshot_2024-08-05.csv": "b7c313e4bb915b15b7ce8d2cb0b45022591b1ee221559ab9f176b619db92bea8",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/16_snapshot_2025-02-04.csv": "3a4e5d6476ff696252b557b62fe69b59e4f895cf87b9f2b6df540442d2a29b81",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/17_snapshot_2025-08-04.csv": "5200705d0eddc2f8947c7549379d536f336bdb30aeea607ac873a46edadcec3f",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/02_history_NIFTY50_2018-09-01_2018-12-31.json": "749b3ac91e9fca9f875d60faaf624b4e9082b5a7dcfb945a4c216e81c13541c1",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/03_history_NIFTY50_2019-01-01_2019-12-31.json": "8a4827edb078677c331362ae598dfc61d82917651c4ef50c4246781012eb6e11",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/04_history_NIFTY50_2020-01-01_2020-12-31.json": "8ad52c30a11bf2fe93e954b9f5e3f15d0540f021c49e49a442c24e697af1dc0b",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/05_history_NIFTY50_2021-01-01_2021-12-31.json": "c38bb5cce4cf19083900b5d712b0681b9863febe6008d5b17fa802eee9b30379",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/06_history_NIFTY50_2022-01-01_2022-12-31.json": "e6ca8ffeab0e4fd6fe799e837ccd8cc20ee9ad9d473e683eef2409cb5dd2479c",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/07_history_NIFTY50_2023-01-01_2023-12-31.json": "1a03490f1120ab0f3b365bc0b649027e0eec03ced45e07a91acb757e26ba9521",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/08_history_NIFTY50_2024-01-01_2024-12-31.json": "304477d4e6b899a726478da34c0584de1074cb206614a5ba1eeb5c1adf15ae42",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/09_history_NIFTY50_2025-01-01_2025-12-31.json": "796263a2214e76605e8e65e53260d32da2a0412e79219172ba629cbbbbacb329",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/10_history_NIFTY500_2018-09-01_2018-12-31.json": "082e4efc0369ab93e83ebef2f1aa4907a70536ab5e33e44fd65458c6da64efa3",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/11_history_NIFTY500_2019-01-01_2019-12-31.json": "4e20add4b77720843648e7d7bc97d8e1703a9399a3a840bc8a925e681079624a",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/12_history_NIFTY500_2020-01-01_2020-12-31.json": "1b7731dbee0a4cbe5122a8211a616322db325b05b42fa37608c02c3d2f331de5",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/13_history_NIFTY500_2021-01-01_2021-12-31.json": "b5a80d9ef606380fd03075caee4ad3547e169b076b07e6b83b4a07acd389c22c",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/14_history_NIFTY500_2022-01-01_2022-12-31.json": "37644a1c7f2851632d1fc76b4a910f03ff83b2bb756850f47bd8d2a9daec12fa",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/15_history_NIFTY500_2023-01-01_2023-12-31.json": "0d5bfd79f1b3c8e9f4f4e9e4956a5e906eeb23ffa415cef476c140f0b696b131",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/16_history_NIFTY500_2024-01-01_2024-12-31.json": "67e6532c6794bd72e5c75a7d16043fe6aa9fd237207b3347b38415e3a6643ae8",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/17_history_NIFTY500_2025-01-01_2025-12-31.json": "e6c21c4bea63969700b948a3a84f5c750892f3335c5c17d3fd43841ec04a7ffe",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/26_history_INDIAVIX_2018-09-01_2018-12-31.json": "6c4bf9c40638aa6bb2c5109d055a66f6caff220cf980b310eff74e86cfc3a2d9",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/27_history_INDIAVIX_2019-01-01_2019-12-31.json": "057e14df67354be0694ab8c50ccd26ad6f90eff4eb6c3e4387c757974184cc7d",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/28_history_INDIAVIX_2020-01-01_2020-12-31.json": "ff63127849cb572dcda62312b197d4b79ba1fdadcff6ac03b0db4b423b2477c9",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/29_history_INDIAVIX_2021-01-01_2021-12-31.json": "732ff4dd43db4e78ef1746b2c533265f4ae48d9f6022d9df66a7fc2a5a718c19",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/30_history_INDIAVIX_2022-01-01_2022-12-31.json": "7ac300803eab0f7c2e37da0adc54df00ab18fb74756a92aa29f4d0f8bd8c526f",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/31_history_INDIAVIX_2023-01-01_2023-12-31.json": "bb50147e7b52ec90e4d8deb3b4e08924c03ebb6cb0d40bab1cdff09e0e24d08e",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/32_history_INDIAVIX_2024-01-01_2024-12-31.json": "a7fde10f0044900d801285dde0f90d2505d8a120a26a0c20e050756aa04eacbf",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/33_history_INDIAVIX_2025-01-01_2025-12-31.json": "6ff1dc990dfe7785846030a337f644f86f9b75603b1190ae3aeea85342e76d5e",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/34_snapshot_2021-04-26.csv": "2cb103d8bd4869c38610a145e6c74ae7e165c3b76581f0181dbc1868c83e987f",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/35_snapshot_2021-04-28.csv": "242a156975508dafb0bff770187270009159db34c7e0aaf87b04f163d74d0fcc",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/36_snapshot_2022-09-26.csv": "5af9ce8092e19b00d012756b4b7884bacc2a2bbe91919eeee8958e8c2cf1bd74",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/37_snapshot_2022-09-27.csv": "a6d03fa718f0d226fe08a4e45d6a39004ec441194196f1923dd26ed7838784f3",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/38_snapshot_2022-09-30.csv": "af844847ec431f949f2aa7aa4a3ad213bc526a473c6ab60daa0599f1eb9a065f",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/39_snapshot_2022-10-03.csv": "0760a382e1c72e645c959d9b8cb8dda949a548271c5000bea58cc4098e9b74d7",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/40_snapshot_2022-11-01.csv": "ad7200ed81c654400f997c6612cfe34e08668de7a4f24ebf86068e4c17694b51",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/41_snapshot_2022-11-02.csv": "499c12c4343c728fe56d3a5455bada8338a1f89440d11d9c266afdd7cdd11d72",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/requests.jsonl": "d1c159731a514a2ba626cefcb3d69087ced7368c2f04f39c4bc87ded33482554",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/requests.jsonl": "2dcb69a3c8297091964e7891eb303f01feea55403687baa21da9ac1a6cbf7728"
    },
    "logical_store_rows": {
      "calendar": {
        "sha256": "6bfc44b6c1f95b3e9897b9e3c217baf291c84b81e11dfa6c8d10a1842b547169",
        "rows": 1548,
        "sql": "SELECT DISTINCT event_date FROM bhavcopy WHERE event_date BETWEEN ? AND ? ORDER BY event_date",
        "parameters": [
          "2019-10-01",
          "2025-12-31"
        ]
      },
      "eq_bars": {
        "sha256": "2833fa65f8029f5aaf8ac06d50de80d38394ca59945108235d2b7ed83527c9df",
        "rows": 2729354,
        "sql": "SELECT symbol,event_date,knowledge_date,open_price,high_price,low_price,close_price FROM bhavcopy WHERE series='EQ' AND event_date BETWEEN ? AND ? AND knowledge_date<=? ORDER BY event_date,symbol,row_id",
        "parameters": [
          "2019-10-01",
          "2025-12-31",
          "2025-12-31"
        ]
      },
      "actions": {
        "sha256": "dc687f0e7009fb859ddb305d388774409ed31e4f9d74c8102ef0fd155d2e53b5",
        "rows": 880,
        "sql": "SELECT symbol,action_type,event_date,knowledge_date,ratio_numerator,ratio_denominator,row_id FROM corporate_actions WHERE event_date<=? AND knowledge_date<=? ORDER BY knowledge_date,row_id",
        "parameters": [
          "2025-12-31",
          "2025-12-31"
        ]
      }
    },
    "hash_encoding": "SHA-256; SQL rows as compact JSON arrays plus LF, in the recorded SQL order"
  },
  "development_hashes_after": {
    "docs/desk/t1_development_results_20261018.md": "f8b65100574d19f16026b04722dc5c6c05df84e7a35577e89255c51262439483",
    "docs/desk/t1_development_manifest_20261018.json": "3ef3bf6bbfee0f13e67ed15b1e9f935b1b7aed490f219c18b812ef724fa7408b",
    "data/t1/development_20261018.json": "023f1828e1fdc5cce93de987ca83a71c7deedb13ca163021c608e9f9d90579f8",
    "data/t1/development_20261018.started.json": "1fc5a98286153062d89aa322dc7c16046d72b45a5587029df0ba83c265b2d377"
  }
}
```

Each variant is reported independently under the registered replication rule. PARTIALLY EXPOSED: even replication success is not independent proof of new trading edge and cannot activate risk limits or satisfy T4/readiness.
