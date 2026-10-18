# T1 locked development results (18 October 2026)

Development only: 2019-10-01 through 2024-12-31. **2025: PARTIALLY EXPOSED**; prior shadow studies viewed aggregate adverse-move rates, but no trading model was fitted or selected on it. No 2025 input or outcome payload was opened for this run and no hold-out evaluation was performed.

Code commit before the run: `a4aa42ddba347517f0f00b4c0870231b758b3dc5`. Input hashes were recorded before real outcome access;
the complete manifest is reproduced below. Results are locked; no threshold or setting was changed after outcome access.

Timing ASSUMPTIONS: same-session EQ bars subject to their stored knowledge dates; index/VIX through D-1; ISIN snapshots from S+1, ignoring October download dates. Missing inputs remain missing, including the five late-known sessions and 2022-08-08. Weekend sessions excluded everywhere.

Eligible stock-days: 1620100; identity-exclusion category: **186581**.
Identity exclusions include rows that also fail fund/ATR conditions; they are not all otherwise eligible equities.
Decision sessions: 1277, 2019-10-01 to 2024-12-02.
Purged sessions (20): 2024-12-03, 2024-12-04, 2024-12-05, 2024-12-06, 2024-12-09, 2024-12-10, 2024-12-11, 2024-12-12, 2024-12-13, 2024-12-16, 2024-12-17, 2024-12-18, 2024-12-19, 2024-12-20, 2024-12-23, 2024-12-24, 2024-12-26, 2024-12-27, 2024-12-30, 2024-12-31.
Purged bars complete the final windows but supply no decisions or bootstrap dates. Empty dates remain in blocks.

Features and adverse20 share price inputs and the decision-close anchor. Volatility quintiles reduce imbalance but do not remove mechanical coupling or establish causation. These are historical conditional associations, not profitability, calibration, readiness or permission to change live risk limits.

## Frozen quintiles and baseline V0

ATR% linear quintile boundaries: [3.1605964603389842, 3.9592760180995112, 4.76384909369999, 5.857440286897999]. Ties go upward.
Development candidate weights (including missing outcomes): {1: 0.2, 2: 0.2, 3: 0.2, 4: 0.2, 5: 0.2}.

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| V0 q1 | 324020 | 314459 | 9561 | 1114 | 7045 | 2.24035566 |
| V0 q2 | 324020 | 312338 | 11682 | 1107 | 12951 | 4.14646953 |
| V0 q3 | 324020 | 309607 | 14413 | 1114 | 19371 | 6.25664148 |
| V0 q4 | 324020 | 305272 | 18748 | 1114 | 29213 | 9.56949868 |
| V0 q5 | 324020 | 299350 | 24670 | 1114 | 49202 | 16.43627860 |

## Preregistered decisions

All differences and interval endpoints below are percentage points. Family intervals are 98.333333% (three contrasts); 95% intervals are descriptive. Bootstrap: 2,000 draws, seed 20261001, 60-session blocks for V1/V2 and 20 for V3; linear percentiles. Every usable draw meets all cell sample minimums.

| Variant | Verdict | Standardised difference pp | Family interval pp | 95% interval pp | Positive quintiles | State coverage | Usable / unusable | Spells |
|---|---|---:|---|---|---:|---:|---|---|
| V1 | FAIL | 3.04997524 | [-1.94362883, 10.65590136] | [-1.23137106, 8.65275778] | 5/5 | 100.00000000% | 2000 / 0 | 9 |
| V2 | FAIL | 6.43782516 | [-3.53869400, 25.50255506] | [-2.38591817, 21.29010370] | 5/5 | 85.73402876% | 1999 / 1 | 13 |
| V3 | FAIL | -1.25378450 | [-2.36239255, -0.53342089] | [-2.07782079, -0.68141498] | 1/5 | 98.41256713% | 2000 / 0 | not required |

## V1: full cells and comparisons

Decision reasons: family-adjusted interval lower bound -0.0194 not above zero

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse q1 | 60802 | 54899 | 5903 | 268 | 1465 | 2.66853677 |
| adverse q2 | 70138 | 63576 | 6562 | 261 | 3192 | 5.02076255 |
| adverse q3 | 74937 | 68674 | 6263 | 268 | 5458 | 7.94769491 |
| adverse q4 | 83920 | 77441 | 6479 | 268 | 9401 | 12.13956431 |
| adverse q5 | 117826 | 108780 | 9046 | 268 | 23431 | 21.53980511 |
| other q1 | 263218 | 259560 | 3658 | 846 | 5580 | 2.14979196 |
| other q2 | 253882 | 248762 | 5120 | 846 | 9759 | 3.92302683 |
| other q3 | 249083 | 240933 | 8150 | 846 | 13913 | 5.77463444 |
| other q4 | 240100 | 227831 | 12269 | 846 | 19812 | 8.69591934 |
| other q5 | 206194 | 190570 | 15624 | 846 | 25771 | 13.52311487 |

| Quintile | Risk difference pp | Risk ratio (secondary) | Predicted positive sign |
|---|---:|---:|---|
| 1 | 0.51874481 | 1.24130001 | True |
| 2 | 1.09773572 | 1.27981856 | True |
| 3 | 2.17306046 | 1.37631135 | True |
| 4 | 3.44364497 | 1.39600700 | True |
| 5 | 8.01669025 | 1.59281388 | True |

Outcome availability by state (no availability threshold):

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse | 407623 | 373370 | 34253 | 268 | 42947 | 11.50253100 |
| other | 1212477 | 1167656 | 44821 | 846 | 74835 | 6.40899374 |
| unknown | 0 | 0 | 0 | 0 | 0 | unavailable |

Matched V0: 1541026 rows, 95.11919017% of eligible stock-days;
standardised rate 7.72984879%; descriptive 95% [4.64550255, 12.25618055];
family [4.25781897, 13.23995738]; usable paired draws 2000.
Both variant state and outcome must be known. Same draws and usable-draw mask as the contrast.

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| matched V0 q1 | 314459 | 314459 | 0 | 1114 | 7045 | 2.24035566 |
| matched V0 q2 | 312338 | 312338 | 0 | 1107 | 12951 | 4.14646953 |
| matched V0 q3 | 309607 | 309607 | 0 | 1114 | 19371 | 6.25664148 |
| matched V0 q4 | 305272 | 305272 | 0 | 1114 | 29213 | 9.56949868 |
| matched V0 q5 | 299350 | 299350 | 0 | 1114 | 49202 | 16.43627860 |

| Spell | First | Last | Adverse sessions |
|---:|---|---|---:|
| 1 | 2019-10-03 | 2019-10-17 | 10 |
| 2 | 2020-02-27 | 2020-07-17 | 95 |
| 3 | 2022-01-25 | 2022-07-29 | 96 |
| 4 | 2022-09-27 | 2022-09-29 | 2 |
| 5 | 2023-02-23 | 2023-04-27 | 39 |
| 6 | 2023-12-19 | 2024-03-14 | 46 |
| 7 | 2024-05-06 | 2024-06-11 | 26 |
| 8 | 2024-07-23 | 2024-08-16 | 9 |
| 9 | 2024-10-31 | 2024-11-25 | 10 |

## V2: full cells and comparisons

Decision reasons: family-adjusted interval lower bound -0.0354 not above zero

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse q1 | 34373 | 34210 | 163 | 139 | 1806 | 5.27915814 |
| adverse q2 | 34455 | 34207 | 248 | 135 | 2836 | 8.29070073 |
| adverse q3 | 36382 | 35872 | 510 | 139 | 3919 | 10.92495540 |
| adverse q4 | 39416 | 38652 | 764 | 139 | 5666 | 14.65900859 |
| adverse q5 | 57485 | 55279 | 2206 | 139 | 15024 | 27.17849455 |
| other q1 | 250855 | 241682 | 9173 | 810 | 4407 | 1.82347051 |
| other q2 | 244215 | 233239 | 10976 | 807 | 8315 | 3.56501271 |
| other q3 | 240428 | 227542 | 12886 | 810 | 12578 | 5.52777070 |
| other q4 | 235996 | 219971 | 16025 | 810 | 19078 | 8.67296144 |
| other q5 | 215372 | 196503 | 18869 | 810 | 28599 | 14.55397628 |

| Quintile | Risk difference pp | Risk ratio (secondary) | Predicted positive sign |
|---|---:|---:|---|
| 1 | 3.45568763 | 2.89511572 | True |
| 2 | 4.72568802 | 2.32557396 | True |
| 3 | 5.39718470 | 1.97637637 | True |
| 4 | 5.98604715 | 1.69019645 | True |
| 5 | 12.62451827 | 1.86742743 | True |

Outcome availability by state (no availability threshold):

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse | 202111 | 198220 | 3891 | 139 | 29251 | 14.75683584 |
| other | 1186866 | 1118937 | 67929 | 810 | 72977 | 6.52199364 |
| unknown | 231123 | 223869 | 7254 | 165 | 15554 | 6.94781323 |

Matched V0: 1317157 rows, 81.30096908% of eligible stock-days;
standardised rate 7.91549399%; descriptive 95% [4.67660476, 13.00208487];
family [4.28725895, 14.00411189]; usable paired draws 1999.
Both variant state and outcome must be known. Same draws and usable-draw mask as the contrast.

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| matched V0 q1 | 275892 | 275892 | 0 | 949 | 6213 | 2.25196816 |
| matched V0 q2 | 267446 | 267446 | 0 | 942 | 11151 | 4.16943981 |
| matched V0 q3 | 263414 | 263414 | 0 | 949 | 16497 | 6.26276508 |
| matched V0 q4 | 258623 | 258623 | 0 | 949 | 24744 | 9.56759453 |
| matched V0 q5 | 251782 | 251782 | 0 | 949 | 43623 | 17.32570239 |

| Spell | First | Last | Adverse sessions |
|---:|---|---|---:|
| 1 | 2019-12-16 | 2019-12-24 | 3 |
| 2 | 2020-02-17 | 2020-04-03 | 23 |
| 3 | 2020-09-24 | 2020-09-24 | 1 |
| 4 | 2021-03-25 | 2021-04-19 | 3 |
| 5 | 2021-08-20 | 2021-08-26 | 3 |
| 6 | 2021-11-18 | 2021-12-24 | 8 |
| 7 | 2022-02-14 | 2022-07-05 | 25 |
| 8 | 2022-10-21 | 2022-11-22 | 5 |
| 9 | 2022-12-22 | 2023-03-28 | 37 |
| 10 | 2023-10-23 | 2023-11-01 | 5 |
| 11 | 2024-03-06 | 2024-03-27 | 9 |
| 12 | 2024-06-04 | 2024-06-04 | 1 |
| 13 | 2024-10-04 | 2024-11-21 | 16 |

## V3: full cells and comparisons

Decision reasons: standardised difference -0.0125 below 0.01; family-adjusted interval lower bound -0.0236 not above zero; positive sign in 1 of 5 quintiles

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse q1 | 220672 | 214871 | 5801 | 1076 | 4006 | 1.86437444 |
| adverse q2 | 206941 | 200725 | 6216 | 1078 | 7616 | 3.79424586 |
| adverse q3 | 189745 | 183547 | 6198 | 1080 | 10200 | 5.55715975 |
| adverse q4 | 173888 | 166823 | 7065 | 1091 | 14577 | 8.73800375 |
| adverse q5 | 170007 | 159735 | 10272 | 1095 | 26450 | 16.55867531 |
| other q1 | 99012 | 95308 | 3704 | 1094 | 2987 | 3.13404961 |
| other q2 | 112789 | 107418 | 5371 | 1088 | 5297 | 4.93120334 |
| other q3 | 129971 | 121859 | 8112 | 1095 | 9086 | 7.45615835 |
| other q4 | 145257 | 133738 | 11519 | 1095 | 14367 | 10.74264607 |
| other q5 | 146100 | 132358 | 13742 | 1095 | 21862 | 16.51732423 |

| Quintile | Risk difference pp | Risk ratio (secondary) | Predicted positive sign |
|---|---:|---:|---|
| 1 | -1.26967517 | 0.59487713 | False |
| 2 | -1.13695748 | 0.76943610 | False |
| 3 | -1.89899860 | 0.74531139 | False |
| 4 | -2.00464232 | 0.81339399 | False |
| 5 | 0.04135108 | 1.00250350 | True |

Outcome availability by state (no availability threshold):

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| adverse | 961253 | 925701 | 35552 | 1095 | 62849 | 6.78934127 |
| other | 633129 | 590681 | 42448 | 1095 | 53599 | 9.07410260 |
| unknown | 25718 | 24644 | 1074 | 19 | 1334 | 5.41308229 |

Matched V0: 1516382 rows, 93.59804950% of eligible stock-days;
standardised rate 7.78597874%; descriptive 95% [4.86643616, 11.36811500];
family [4.47463765, 12.05534270]; usable paired draws 2000.
Both variant state and outcome must be known. Same draws and usable-draw mask as the contrast.

| Group | Candidates | Valid | Missing | Distinct dates with valid outcome | Adverse20 count | Rate % |
|---|---:|---:|---:|---:|---:|---:|
| matched V0 q1 | 310179 | 310179 | 0 | 1095 | 6993 | 2.25450466 |
| matched V0 q2 | 308143 | 308143 | 0 | 1088 | 12913 | 4.19058684 |
| matched V0 q3 | 305406 | 305406 | 0 | 1095 | 19286 | 6.31487266 |
| matched V0 q4 | 300561 | 300561 | 0 | 1095 | 28944 | 9.62999192 |
| matched V0 q5 | 292093 | 292093 | 0 | 1095 | 48312 | 16.53993762 |

## Input exclusions by development year

| Year | Cause | Stock-days |
|---|---|---:|
| 2019 | eligible | 41498 |
| 2019 | atr_window_incomplete | 679 |
| 2019 | atr_window_unadjustable | 10 |
| 2019 | fund_unit | 2116 |
| 2019 | identity_unknown | 44475 |
| 2020 | eligible | 269361 |
| 2020 | atr_window_incomplete | 63694 |
| 2020 | atr_window_unadjustable | 503 |
| 2020 | bar_not_known_by_decision | 3054 |
| 2020 | fund_unit | 18046 |
| 2020 | identity_unknown | 18760 |
| 2021 | eligible | 335560 |
| 2021 | atr_window_incomplete | 11838 |
| 2021 | atr_window_unadjustable | 365 |
| 2021 | bar_not_known_by_decision | 4787 |
| 2021 | fund_unit | 22796 |
| 2021 | identity_unknown | 12597 |
| 2022 | eligible | 304746 |
| 2022 | atr_window_incomplete | 69757 |
| 2022 | atr_window_unadjustable | 468 |
| 2022 | bar_not_known_by_decision | 8431 |
| 2022 | fund_unit | 27482 |
| 2022 | identity_unknown | 25491 |
| 2023 | eligible | 343175 |
| 2023 | atr_window_incomplete | 35993 |
| 2023 | atr_window_unadjustable | 539 |
| 2023 | bar_not_known_by_decision | 5205 |
| 2023 | fund_unit | 33707 |
| 2023 | identity_unknown | 25776 |
| 2024 | eligible | 325760 |
| 2024 | atr_window_incomplete | 10970 |
| 2024 | atr_window_unadjustable | 595 |
| 2024 | bar_not_known_by_decision | 1784 |
| 2024 | fund_unit | 23950 |
| 2024 | identity_unknown | 59482 |

## Descriptive input coverage and distributions (no extra contrasts)

| Feature | Known | Total | Min / Q25 / median / Q75 / max |
|---|---:|---:|---|
| share_above50 | 969 | 1277 | [0.0048115477145148355, 0.3990895295902883, 0.56973058637084, 0.7474509803921568, 0.9580306698950767] |
| share_above200 | 397 | 1277 | [0.26444833625218916, 0.6333630686886709, 0.726161369193154, 0.8001651527663088, 0.9569377990430622] |
| net_breadth | 1228 | 1277 | [-0.9800142755174875, -0.28114958311997557, 0.0009765625, 0.20517777699493928, 0.8700927908636689] |
| new_high_rate | 303 | 1277 | [0.0, 0.020779644159973285, 0.04037558685446009, 0.06459761348563056, 0.17007358953393295] |
| new_low_rate | 303 | 1277 | [0.0, 0.0016549444289243476, 0.0038314176245210726, 0.01151395349754783, 0.17346938775510204] |
| dispersion | 1228 | 1277 | [0.0166148888920308, 0.025011679181864335, 0.027312638598653734, 0.030382085208051076, 0.05629265909668989] |
| atr_pct | 1620100 | 1620100 | [0.3216036713984348, 3.3712952635596896, 4.346707501447884, 5.527494123467456, 524.22131147541] |
| rel_ew_1 | 1620100 | 1620100 | [-1.0200057054810423, -0.014728225918142795, -0.003321404234939174, 0.010238231291999174, 0.5980196791301016] |
| rel_ew_5 | 1614651 | 1620100 | [-1.053193238096295, -0.0354564715879457, -0.008947561533763325, 0.02324790543594856, 1.9056084157890447] |
| rel_ew_20 | 1594382 | 1620100 | [-1.141251792254339, -0.08007697229771292, -0.024102224979863293, 0.045025729269056076, 2.786670771350151] |
| rel_ew_60 | 1197253 | 1620100 | [-1.3911323190491782, -0.16748389813154532, -0.06289354499880484, 0.06807860777973923, 6.80326279959105] |
| rel_n50_1 | 1620100 | 1620100 | [-0.9976325547141156, -0.014488125845386501, -0.001991281602763184, 0.012040497147388085, 0.6059076551400878] |
| rel_n50_5 | 1620100 | 1620100 | [-1.0309311167829787, -0.03263161229973835, -0.00409423397162284, 0.029795638167916694, 1.902028139636127] |
| rel_n50_20 | 1610668 | 1620100 | [-1.060073074485415, -0.06343405677194261, -0.004380741439273361, 0.06962842883370379, 2.9777299318192845] |
| rel_n50_60 | 1223452 | 1620100 | [-1.2217984475259733, -0.10556345336254772, -0.0026022986505780388, 0.13684082571745126, 7.458926479648061] |

Descriptive NIFTY 50 trend (D-1): {'known': 1277, 'unknown': 0, 'below_average': 208}.

## Input manifest recorded before outcome access

```json
{
  "code_commit": "a4aa42ddba347517f0f00b4c0870231b758b3dc5",
  "started_at": "2026-10-18T11:08:59.222137+00:00",
  "read_end": "2024-12-31",
  "preregistration_commit": "70ebf4bcd04568b4d94eab3537490eb815bb8bbb",
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
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/02_history_NIFTY50_2018-09-01_2018-12-31.json": "749b3ac91e9fca9f875d60faaf624b4e9082b5a7dcfb945a4c216e81c13541c1",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/03_history_NIFTY50_2019-01-01_2019-12-31.json": "8a4827edb078677c331362ae598dfc61d82917651c4ef50c4246781012eb6e11",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/04_history_NIFTY50_2020-01-01_2020-12-31.json": "8ad52c30a11bf2fe93e954b9f5e3f15d0540f021c49e49a442c24e697af1dc0b",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/05_history_NIFTY50_2021-01-01_2021-12-31.json": "c38bb5cce4cf19083900b5d712b0681b9863febe6008d5b17fa802eee9b30379",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/06_history_NIFTY50_2022-01-01_2022-12-31.json": "e6ca8ffeab0e4fd6fe799e837ccd8cc20ee9ad9d473e683eef2409cb5dd2479c",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/07_history_NIFTY50_2023-01-01_2023-12-31.json": "1a03490f1120ab0f3b365bc0b649027e0eec03ced45e07a91acb757e26ba9521",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/08_history_NIFTY50_2024-01-01_2024-12-31.json": "304477d4e6b899a726478da34c0584de1074cb206614a5ba1eeb5c1adf15ae42",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/10_history_NIFTY500_2018-09-01_2018-12-31.json": "082e4efc0369ab93e83ebef2f1aa4907a70536ab5e33e44fd65458c6da64efa3",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/11_history_NIFTY500_2019-01-01_2019-12-31.json": "4e20add4b77720843648e7d7bc97d8e1703a9399a3a840bc8a925e681079624a",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/12_history_NIFTY500_2020-01-01_2020-12-31.json": "1b7731dbee0a4cbe5122a8211a616322db325b05b42fa37608c02c3d2f331de5",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/13_history_NIFTY500_2021-01-01_2021-12-31.json": "b5a80d9ef606380fd03075caee4ad3547e169b076b07e6b83b4a07acd389c22c",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/14_history_NIFTY500_2022-01-01_2022-12-31.json": "37644a1c7f2851632d1fc76b4a910f03ff83b2bb756850f47bd8d2a9daec12fa",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/15_history_NIFTY500_2023-01-01_2023-12-31.json": "0d5bfd79f1b3c8e9f4f4e9e4956a5e906eeb23ffa415cef476c140f0b696b131",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/16_history_NIFTY500_2024-01-01_2024-12-31.json": "67e6532c6794bd72e5c75a7d16043fe6aa9fd237207b3347b38415e3a6643ae8",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/26_history_INDIAVIX_2018-09-01_2018-12-31.json": "6c4bf9c40638aa6bb2c5109d055a66f6caff220cf980b310eff74e86cfc3a2d9",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/27_history_INDIAVIX_2019-01-01_2019-12-31.json": "057e14df67354be0694ab8c50ccd26ad6f90eff4eb6c3e4387c757974184cc7d",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/28_history_INDIAVIX_2020-01-01_2020-12-31.json": "ff63127849cb572dcda62312b197d4b79ba1fdadcff6ac03b0db4b423b2477c9",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/29_history_INDIAVIX_2021-01-01_2021-12-31.json": "732ff4dd43db4e78ef1746b2c533265f4ae48d9f6022d9df66a7fc2a5a718c19",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/30_history_INDIAVIX_2022-01-01_2022-12-31.json": "7ac300803eab0f7c2e37da0adc54df00ab18fb74756a92aa29f4d0f8bd8c526f",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/31_history_INDIAVIX_2023-01-01_2023-12-31.json": "bb50147e7b52ec90e4d8deb3b4e08924c03ebb6cb0d40bab1cdff09e0e24d08e",
      "D:/Agentic_ai_project/praman/data/raw/t1_sources/phase2/32_history_INDIAVIX_2024-01-01_2024-12-31.json": "a7fde10f0044900d801285dde0f90d2505d8a120a26a0c20e050756aa04eacbf",
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
        "sha256": "624c26fc9818d90da10878e4d67b6a363145d952a017646fcf88053bbe9c9d37",
        "rows": 1300,
        "sql": "SELECT DISTINCT event_date FROM bhavcopy WHERE event_date BETWEEN ? AND ? ORDER BY event_date",
        "parameters": [
          "2019-10-01",
          "2024-12-31"
        ]
      },
      "eq_bars": {
        "sha256": "82ce9caf6613e9984ca60fcc931c4af2af18e6badfcee1e01bb386e20a2a621d",
        "rows": 2199596,
        "sql": "SELECT symbol,event_date,knowledge_date,open_price,high_price,low_price,close_price FROM bhavcopy WHERE series='EQ' AND event_date BETWEEN ? AND ? AND knowledge_date<=? ORDER BY event_date,symbol,row_id",
        "parameters": [
          "2019-10-01",
          "2024-12-31",
          "2024-12-31"
        ]
      },
      "actions": {
        "sha256": "9ff93e744b098be3a76ce588f8f7c1e9f654fe8063d1471eb83be5d911428786",
        "rows": 699,
        "sql": "SELECT symbol,action_type,event_date,knowledge_date,ratio_numerator,ratio_denominator,row_id FROM corporate_actions WHERE event_date<=? AND knowledge_date<=? ORDER BY knowledge_date,row_id",
        "parameters": [
          "2024-12-31",
          "2024-12-31"
        ]
      }
    },
    "hash_encoding": "SHA-256; SQL rows as compact JSON arrays plus LF, in the recorded SQL order"
  }
}
```

No 2025 replication claim is made. Even a development PASS cannot activate a trading policy or satisfy T4. Any subsequent hold-out evaluation needs separate approval.
