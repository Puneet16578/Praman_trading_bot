# Shadow replay follow-up results

Registered follow-up to previously known aggregate results. All intervals below are 95% event-date-cluster bootstrap intervals with 2,000 replicates, seed 20261001. They are descriptive and not adjusted for multiple comparisons.

## Limitations and scope

- ATR20 ends on the decision date and includes the event bar. Price inputs are shared with screening and outcomes; quintiles are an incomplete observational control.
- The 2026 period is a spent hold-out, reported descriptively. No forward-window events are read.
- The 90% rule is a fixed research variant. Active rulebook, sizing and journals are unchanged. At the fill both variants are checked against the original 100% caps.
- Zero-share variants abstain; they are not counted as safe fills. Unknown frozen inputs are excluded explicitly. Missing locked-circuit scenarios remain missing under the original convention.
- Original raw-opening execution and corporate-action conventions, current identity maps and empty hypothetical portfolios remain. No independent predictive-edge or readiness claim follows.

## Frozen primary volatility boundaries

ATR20 / decision price in percent: 3.2975, 4.0429, 4.7966, 5.8627.

Ties go to the upper interval. These boundaries are reused for 2026 and filled-only comparisons.

## Primary 2019-2025

Candidates: 60694; missing original 90-session labels: 796. Labels are retained unchanged; the controlled outcome is the original adverse20 measure.

### Volatility control: All candidates

Missing volatility by screening state: `{"SCREEN_FAIL": {"missing_outcomes": 136, "n": 136}, "SCREEN_PASS": {"missing_outcomes": 0, "n": 0}}`.

| Quintile | PASS candidates / valid / missing | FAIL candidates / valid / missing | PASS rate % [95% CI] | FAIL rate % [95% CI] | FAIL minus PASS, pp [95% CI] | PASS / FAIL valid dates | Weight |
|---|---:|---:|---|---|---|---:|---:|
| Q1 | 11290 / 11248 / 42 | 822 / 817 / 5 | 2.6849 [2.1391, 3.3129]; draws=2000 | 4.1616 [2.6843, 5.7764]; draws=2000 | 1.4766 [0.1149, 2.9062]; draws=2000 | 1334 / 499 | 0.2000 |
| Q2 | 10493 / 10466 / 27 | 1618 / 1609 / 9 | 5.8762 [5.0723, 6.7659]; draws=2000 | 6.6501 [5.4429, 7.9744]; draws=2000 | 0.7739 [-0.5255, 2.1770]; draws=2000 | 1385 / 765 | 0.2000 |
| Q3 | 9347 / 9312 / 35 | 2765 / 2746 / 19 | 9.4180 [8.3614, 10.6647]; draws=2000 | 11.1071 [9.6111, 12.6157]; draws=2000 | 1.6891 [0.1999, 3.0198]; draws=2000 | 1417 / 1043 | 0.2000 |
| Q4 | 8010 / 7959 / 51 | 4101 / 4071 / 30 | 14.2229 [12.5739, 15.9769]; draws=2000 | 15.4999 [14.0845, 16.9934]; draws=2000 | 1.2770 [-0.4817, 2.9403]; draws=2000 | 1376 / 1223 | 0.2000 |
| Q5 | 6567 / 6516 / 51 | 5545 / 5445 / 100 | 24.9233 [20.0603, 30.8298]; draws=2000 | 23.4160 [20.4978, 26.9277]; draws=2000 | -1.5073 [-4.6465, 1.4601]; draws=2000 | 1227 / 1272 | 0.2000 |

| Comparison | Estimate and interval, percentage points |
|---|---|
| Unstratified gap, same valid-volatility population | 6.0133 [5.1103, 6.8875]; draws=2000 |
| Standardized gap | 0.7419 [-0.2846, 1.7245]; draws=2000 |
| Attenuation: unstratified minus standardized | 5.2714 [4.5501, 6.0895]; draws=2000 |

### Volatility control: Filled only

Missing volatility by screening state: `{"SCREEN_FAIL": {"missing_outcomes": 0, "n": 0}, "SCREEN_PASS": {"missing_outcomes": 0, "n": 0}}`.

| Quintile | PASS candidates / valid / missing | FAIL candidates / valid / missing | PASS rate % [95% CI] | FAIL rate % [95% CI] | FAIL minus PASS, pp [95% CI] | PASS / FAIL valid dates | Weight |
|---|---:|---:|---|---|---|---:|---:|
| Q1 | 11289 / 11248 / 41 | 778 / 773 / 5 | 2.6849 [2.1391, 3.3129]; draws=2000 | 4.2691 [2.7544, 5.9446]; draws=2000 | 1.5842 [0.1574, 3.0733]; draws=2000 | 1334 / 474 | 0.1995 |
| Q2 | 10492 / 10465 / 27 | 1613 / 1604 / 9 | 5.8672 [5.0638, 6.7496]; draws=2000 | 6.6085 [5.4068, 7.9223]; draws=2000 | 0.7413 [-0.5714, 2.1115]; draws=2000 | 1385 / 761 | 0.2001 |
| Q3 | 9345 / 9310 / 35 | 2764 / 2745 / 19 | 9.4200 [8.3632, 10.6681]; draws=2000 | 11.1111 [9.6147, 12.6159]; draws=2000 | 1.6911 [0.2033, 3.0279]; draws=2000 | 1417 / 1043 | 0.2002 |
| Q4 | 8009 / 7959 / 50 | 4101 / 4071 / 30 | 14.2229 [12.5739, 15.9769]; draws=2000 | 15.4999 [14.0845, 16.9934]; draws=2000 | 1.2770 [-0.4817, 2.9403]; draws=2000 | 1376 / 1223 | 0.2002 |
| Q5 | 6565 / 6515 / 50 | 5542 / 5443 / 99 | 24.9271 [20.0603, 30.8382]; draws=2000 | 23.4246 [20.5092, 26.9381]; draws=2000 | -1.5025 [-4.6533, 1.4815]; draws=2000 | 1227 / 1272 | 0.2001 |

| Comparison | Estimate and interval, percentage points |
|---|---|
| Unstratified gap, same valid-volatility population | 6.0578 [5.1531, 6.9353]; draws=2000 |
| Standardized gap | 0.7577 [-0.2672, 1.7424]; draws=2000 |
| Attenuation: unstratified minus standardized | 5.3001 [4.5692, 6.1379]; draws=2000 |

### Fill-cap breaches

Original passes 45707; original fills 45700; original NO_FILL 7; unknown inputs 0; variant abstentions 6; variant fills 45694.

Original filled passes already exceeding a quantitative cap at the decision: 12693. Unknown locked components: 45700; unknown historical-gap components: 0.

| Any-cap comparison | Breaches / evaluated fills | Rate % [95% CI] | Valid dates |
|---|---:|---|---:|
| baseline | 25105 / 45700 | 54.9344 [53.4084, 56.3274]; draws=2000 | 1465 |
| variant | 7055 / 45694 | 15.4397 [14.5615, 16.4109]; draws=2000 | 1465 |
| paired_baseline | see paired rate / 45694 | 54.9394 [53.4120, 56.3323]; draws=2000 | 1465 |
| paired_variant | see paired rate / 45694 | 15.4397 [14.5615, 16.4109]; draws=2000 | 1465 |

Paired any-cap difference (variant minus baseline), percentage points: -39.4997 [-40.4329, -38.4606]; draws=2000.

Conditional excess sizes are percentages **over that cap**, among breaches of that cap. Zero-inclusive sizes use every evaluable fill. Empty breach groups are unavailable.

| Cap / variant | Breaches / fills | Breach rate % [95% CI] | Conditional median excess % [95% CI] | Conditional p90 excess % [95% CI] | Breach dates | Zero-inclusive median excess % [95% CI] | Zero-inclusive p90 excess % [95% CI] |
|---|---:|---|---|---|---:|---|---|
| per_trade / baseline | 15080 / 45700 | 32.9978 [31.6747, 34.3514]; draws=2000 | 11.6317 [11.1621, 12.1240]; draws=2000 | 40.7112 [39.3066, 42.2396]; draws=2000 | 1443 | 0.0000 [0.0000, 0.0000]; draws=2000 | 19.5695 [18.4212, 20.8008]; draws=2000 |
| per_trade / variant | 7055 / 45694 | 15.4397 [14.5615, 16.4109]; draws=2000 | 10.1540 [9.7104, 10.6759]; draws=2000 | 41.3068 [39.2551, 43.8437]; draws=2000 | 1331 | 0.0000 [0.0000, 0.0000]; draws=2000 | 6.1257 [5.1044, 7.2631]; draws=2000 |
| open_risk / baseline | 3 / 45700 | 0.0066 [0.0000, 0.0150]; draws=2000 | 0.2202 [0.1609, 5.4350]; draws=1901 SMALL SAMPLE | 4.3921 [0.1609, 5.4350]; draws=1901 SMALL SAMPLE | 3 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| open_risk / variant | 0 / 45694 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_stock / baseline | 16097 / 45700 | 35.2232 [34.0158, 36.4241]; draws=2000 | 0.8480 [0.8188, 0.8700]; draws=2000 | 3.2000 [3.0575, 3.3256]; draws=2000 | 1377 | 0.0000 [0.0000, 0.0000]; draws=2000 | 1.5169 [1.4560, 1.5871]; draws=2000 |
| per_stock / variant | 61 / 45694 | 0.1335 [0.1012, 0.1698]; draws=2000 | 2.2000 [1.3760, 3.0820]; draws=2000 | 7.0840 [5.0185, 7.8083]; draws=2000 | 59 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_sector / baseline | 0 / 45700 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_sector / variant | 0 / 45694 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| order_adv / baseline | 128 / 45700 | 0.2801 [0.2358, 0.3313]; draws=2000 | 1.2993 [1.0614, 1.6250]; draws=2000 | 5.5692 [4.7136, 7.3200]; draws=2000 | 123 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| order_adv / variant | 2 / 45694 | 0.0044 [0.0000, 0.0110]; draws=2000 | 1.3782 [1.3054, 1.4510]; draws=1734 SMALL SAMPLE | 1.4364 [1.3054, 1.4510]; draws=1734 SMALL SAMPLE | 2 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| exit_days / baseline | 0 / 45700 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| exit_days / variant | 0 / 45694 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |

| Cap | Paired rate difference, pp [95% CI] | Conditional median size difference, pp [95% CI] | Conditional p90 size difference, pp [95% CI] |
|---|---|---|---|
| per_trade | -17.5603 [-18.2533, -16.8347]; draws=2000 | -1.4777 [-1.9852, -0.9450]; draws=2000 | 0.5957 [-1.0932, 2.5776]; draws=2000 |
| open_risk | -0.0066 [-0.0151, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |
| per_stock | -35.0943 [-36.3061, -33.9051]; draws=2000 | 1.3520 [0.5430, 2.2401]; draws=2000 | 3.8840 [1.8459, 4.6882]; draws=2000 |
| per_sector | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |
| order_adv | -0.2757 [-0.3267, -0.2315]; draws=2000 | 0.0789 [-0.2986, 0.3371]; draws=1734 | -4.1328 [-5.9033, -3.4160]; draws=1734 |
| exit_days | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |

Size differences compare conditional distributions whose membership can change. Caps overlap; counts cannot be summed. `per_trade` includes costs, `open_risk` uses stress loss, `per_stock` and `per_sector` use position value, `order_adv` uses frozen turnover and `exit_days` uses stressed exit capacity.

## Descriptive 2026

Candidates: 9668; missing original 90-session labels: 3702. Labels are retained unchanged; the controlled outcome is the original adverse20 measure.

### Volatility control: All candidates

Missing volatility by screening state: `{"SCREEN_FAIL": {"missing_outcomes": 30, "n": 30}, "SCREEN_PASS": {"missing_outcomes": 0, "n": 0}}`.

| Quintile | PASS candidates / valid / missing | FAIL candidates / valid / missing | PASS rate % [95% CI] | FAIL rate % [95% CI] | FAIL minus PASS, pp [95% CI] | PASS / FAIL valid dates | Weight |
|---|---:|---:|---|---|---|---:|---:|
| Q1 | 1552 / 1471 / 81 | 126 / 112 / 14 | 3.2631 [2.1769, 4.4761]; draws=2000 | 2.6786 [0.0000, 6.0004]; draws=2000 | -0.5845 [-3.1118, 2.5859]; draws=2000 | 156 / 66 | 0.1741 |
| Q2 | 1657 / 1570 / 87 | 281 / 250 / 31 | 5.6688 [4.2882, 7.1042]; draws=2000 | 4.8000 [2.3695, 7.7494]; draws=2000 | -0.8688 [-3.4760, 2.1192]; draws=2000 | 163 / 104 | 0.2011 |
| Q3 | 1676 / 1603 / 73 | 470 / 439 / 31 | 8.6712 [6.7967, 10.6128]; draws=2000 | 10.9339 [7.8040, 14.4678]; draws=2000 | 2.2627 [-1.0543, 5.8735]; draws=2000 | 163 / 139 | 0.2227 |
| Q4 | 1383 / 1342 / 41 | 583 / 538 / 45 | 9.6125 [6.7084, 12.8226]; draws=2000 | 13.9405 [10.1546, 17.9850]; draws=2000 | 4.3280 [0.2698, 8.2708]; draws=2000 | 161 / 148 | 0.2040 |
| Q5 | 865 / 840 / 25 | 1045 / 974 / 71 | 14.6429 [10.5462, 20.1546]; draws=2000 | 16.4271 [12.1546, 21.7453]; draws=2000 | 1.7842 [-2.1522, 5.3407]; draws=2000 | 150 / 152 | 0.1982 |

| Comparison | Estimate and interval, percentage points |
|---|---|
| Unstratified gap, same valid-volatility population | 5.1486 [3.1265, 7.4481]; draws=2000 |
| Standardized gap | 1.4638 [-0.3020, 3.2083]; draws=2000 |
| Attenuation: unstratified minus standardized | 3.6848 [2.4095, 5.1078]; draws=2000 |

### Volatility control: Filled only

Missing volatility by screening state: `{"SCREEN_FAIL": {"missing_outcomes": 0, "n": 0}, "SCREEN_PASS": {"missing_outcomes": 0, "n": 0}}`.

| Quintile | PASS candidates / valid / missing | FAIL candidates / valid / missing | PASS rate % [95% CI] | FAIL rate % [95% CI] | FAIL minus PASS, pp [95% CI] | PASS / FAIL valid dates | Weight |
|---|---:|---:|---|---|---|---:|---:|
| Q1 | 1551 / 1471 / 80 | 123 / 109 / 14 | 3.2631 [2.1769, 4.4761]; draws=2000 | 2.7523 [0.0000, 6.1407]; draws=2000 | -0.5108 [-3.1118, 2.7603]; draws=2000 | 156 / 65 | 0.1738 |
| Q2 | 1656 / 1570 / 86 | 281 / 250 / 31 | 5.6688 [4.2882, 7.1042]; draws=2000 | 4.8000 [2.3695, 7.7494]; draws=2000 | -0.8688 [-3.4760, 2.1192]; draws=2000 | 163 / 104 | 0.2011 |
| Q3 | 1676 / 1603 / 73 | 469 / 438 / 31 | 8.6712 [6.7967, 10.6128]; draws=2000 | 10.7306 [7.5784, 14.3226]; draws=2000 | 2.0594 [-1.2656, 5.6892]; draws=2000 | 163 / 139 | 0.2227 |
| Q4 | 1383 / 1342 / 41 | 583 / 538 / 45 | 9.6125 [6.7084, 12.8226]; draws=2000 | 13.9405 [10.1546, 17.9850]; draws=2000 | 4.3280 [0.2698, 8.2708]; draws=2000 | 161 / 148 | 0.2041 |
| Q5 | 865 / 840 / 25 | 1045 / 974 / 71 | 14.6429 [10.5462, 20.1546]; draws=2000 | 16.4271 [12.1546, 21.7453]; draws=2000 | 1.7842 [-2.1522, 5.3407]; draws=2000 | 150 / 152 | 0.1983 |

| Comparison | Estimate and interval, percentage points |
|---|---|
| Unstratified gap, same valid-volatility population | 5.1276 [3.1155, 7.4499]; draws=2000 |
| Standardized gap | 1.4323 [-0.3293, 3.1915]; draws=2000 |
| Attenuation: unstratified minus standardized | 3.6953 [2.4096, 5.1214]; draws=2000 |

### Fill-cap breaches

Original passes 7133; original fills 7131; original NO_FILL 2; unknown inputs 0; variant abstentions 0; variant fills 7131.

Original filled passes already exceeding a quantitative cap at the decision: 1958. Unknown locked components: 7131; unknown historical-gap components: 0.

| Any-cap comparison | Breaches / evaluated fills | Rate % [95% CI] | Valid dates |
|---|---:|---|---:|
| baseline | 3232 / 7131 | 45.3232 [41.5731, 49.3948]; draws=2000 | 172 |
| variant | 913 / 7131 | 12.8033 [10.2316, 15.9662]; draws=2000 | 172 |
| paired_baseline | see paired rate / 7131 | 45.3232 [41.5731, 49.3948]; draws=2000 | 172 |
| paired_variant | see paired rate / 7131 | 12.8033 [10.2316, 15.9662]; draws=2000 | 172 |

Paired any-cap difference (variant minus baseline), percentage points: -32.5200 [-34.8248, -30.3219]; draws=2000.

Conditional excess sizes are percentages **over that cap**, among breaches of that cap. Zero-inclusive sizes use every evaluable fill. Empty breach groups are unavailable.

| Cap / variant | Breaches / fills | Breach rate % [95% CI] | Conditional median excess % [95% CI] | Conditional p90 excess % [95% CI] | Breach dates | Zero-inclusive median excess % [95% CI] | Zero-inclusive p90 excess % [95% CI] |
|---|---:|---|---|---|---:|---|---|
| per_trade / baseline | 2061 / 7131 | 28.9020 [25.7632, 32.5136]; draws=2000 | 10.4716 [8.7499, 12.7462]; draws=2000 | 38.1029 [32.5978, 43.0918]; draws=2000 | 171 | 0.0000 [0.0000, 0.0000]; draws=2000 | 16.3579 [13.0009, 21.2566]; draws=2000 |
| per_trade / variant | 913 / 7131 | 12.8033 [10.2316, 15.9662]; draws=2000 | 10.2647 [8.5122, 12.2570]; draws=2000 | 38.8875 [32.2365, 42.4875]; draws=2000 | 159 | 0.0000 [0.0000, 0.0000]; draws=2000 | 3.6664 [0.3084, 7.4588]; draws=2000 |
| open_risk / baseline | 0 / 7131 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| open_risk / variant | 0 / 7131 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_stock / baseline | 2008 / 7131 | 28.1587 [25.4431, 30.9834]; draws=2000 | 0.8325 [0.7496, 0.9500]; draws=2000 | 3.2449 [2.8454, 3.5760]; draws=2000 | 171 | 0.0000 [0.0000, 0.0000]; draws=2000 | 1.2545 [1.0573, 1.5374]; draws=2000 |
| per_stock / variant | 7 / 7131 | 0.0982 [0.0257, 0.2098]; draws=2000 | 2.4320 [1.6236, 6.5000]; draws=1986 SMALL SAMPLE | 6.0864 [2.4320, 6.5000]; draws=1986 SMALL SAMPLE | 5 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_sector / baseline | 0 / 7131 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_sector / variant | 0 / 7131 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| order_adv / baseline | 17 / 7131 | 0.2384 [0.1130, 0.3853]; draws=2000 | 2.2545 [0.9151, 3.9249]; draws=2000 SMALL SAMPLE | 6.4775 [2.9766, 8.2154]; draws=2000 SMALL SAMPLE | 13 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| order_adv / variant | 0 / 7131 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| exit_days / baseline | 0 / 7131 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| exit_days / variant | 0 / 7131 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |

| Cap | Paired rate difference, pp [95% CI] | Conditional median size difference, pp [95% CI] | Conditional p90 size difference, pp [95% CI] |
|---|---|---|---|
| per_trade | -16.0987 [-17.5721, -14.6565]; draws=2000 | -0.2069 [-2.2369, 1.3510]; draws=2000 | 0.7846 [-3.1894, 5.1672]; draws=2000 |
| open_risk | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |
| per_stock | -28.0606 [-30.8715, -25.3553]; draws=2000 | 1.5995 [0.7668, 5.6600]; draws=1986 | 2.8415 [-0.5731, 3.5560]; draws=1986 |
| per_sector | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |
| order_adv | -0.2384 [-0.3853, -0.1130]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |
| exit_days | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |

Size differences compare conditional distributions whose membership can change. Caps overlap; counts cannot be summed. `per_trade` includes costs, `open_risk` uses stress loss, `per_stock` and `per_sector` use position value, `order_adv` uses frozen turnover and `exit_days` uses stressed exit capacity.

## Provenance and reproduction

```json
{
  "code_commit": "d6b7a0b3961418ead8f097f68a5e0d3a028a6cc6",
  "preregistration_commit": "bbd526809b9b0209ba77b63b58a2c0f872dbc85f",
  "base_results_commit": "64ac2f13a3d419ce63b19b8c9c3b6e3e5b063af5",
  "run_date": "2026-10-04",
  "seed": 20261001,
  "bootstrap_replicates": 2000,
  "decision_cap_fraction": 0.9,
  "raw_sha256": "aa619d2e23f113c46e4b4df11307b18bc371837ed5d6bf7069a7d140204acb3d",
  "base_results_git_blob_sha256": "60190f43f429db84738d6a15e3d85bdf282c59fba0fd4cd0134fc9a1424edf69",
  "preregistration_sha256": "28972d41e4d9cd41515cbe7a4558ef9fd5ac3f0403716f1eea7e4f9d41e1c427",
  "source_hashes": {
    "docs/desk/shadow_replay_followup_prereg.md": "28972d41e4d9cd41515cbe7a4558ef9fd5ac3f0403716f1eea7e4f9d41e1c427",
    "desk/shadow_followup.py": "3c5b042cb7aff644c9ca714c53f6debd5f2f7abd8c742dd652b8da4aee99208f",
    "desk/shadow_followup_report.py": "9225ee3e08edc05e5f2363184a8e6dcd7bfb12916de3f6f7f96ab91e729ef320",
    "scripts/desk_shadow_followup.py": "79990986f0303a6f0933bdb51d1542d1fe6f6f2863d2203a685610690f8f87ce",
    "tests/test_shadow_followup.py": "ab2fc2717e111798fd7e4aedcdfe66285d8f6be1b2c5a96d5a8c45d2f804233a"
  },
  "original_provenance": {
    "code_commit": "67df6970d5a8f42bda1093a5c15f6516145b7d0d",
    "run_date": "2026-10-03",
    "rulebook": {
      "rulebook": {
        "version": "v2",
        "dated": "2026-10-02",
        "risk": {
          "circuit_lock_days": 2,
          "capital_allocated_inr": 500000.0,
          "risk_per_trade_pct": 1.0,
          "max_open_risk_pct": 5.0,
          "max_per_stock_pct": 10.0,
          "max_per_sector_pct": 25.0,
          "monthly_drawdown_brake_pct": 6.0,
          "stress_loss_floor_pct_of_position": 10.0
        },
        "liquidity": {
          "max_order_pct_of_adv": 1.0,
          "stressed_volume_factor": 0.25,
          "participation_pct_of_stressed_volume": 10.0,
          "max_days_to_exit_stressed": 3.0
        },
        "surveillance_exclusions": {
          "exclude_trade_for_trade_series": true,
          "max_asm_stage": null,
          "exclude_gsm": true
        },
        "behavioural_brakes": {
          "max_g7_overrides_per_month": 2,
          "consecutive_loss_brake_count": 3,
          "stress_loss_lookback_sessions": 252
        },
        "inference_rules": {
          "thresholds": {}
        },
        "required_evidence_dimensions": {
          "required": [
            "price",
            "volume",
            "delivery",
            "disclosures",
            "surveillance",
            "sector"
          ]
        },
        "paper_to_live_criteria": null,
        "operational_gate": {
          "min_calendar_days": 90,
          "min_closed_paper_trades": 30,
          "max_unlogged_rule_violations": 0,
          "max_open_risk_budget_breaches": 0,
          "require_recorded_exit_on_every_trade": true,
          "max_open_high_severity_defects": 0
        },
        "edge_confidence_gate": {
          "min_logged_opportunities": 1000,
          "min_distinct_market_regimes": 2,
          "require_out_of_sample_evaluation": true,
          "require_positive_expectancy_after_costs": true,
          "bootstrap_confidence_level": 0.95,
          "bootstrap_lower_bound_must_exceed": 0.0,
          "require_equal_weighted_market_comparison": true,
          "require_neighbouring_parameter_stability": true
        },
        "screening": {
          "stop_multiple": 2.0
        }
      },
      "version_file": "desk_rulebook_v2.yaml",
      "sha256": "51711e0efc01f046657b33fb7ffb1306b428310907211d8aedb6a33e536776d9"
    },
    "costs": {
      "costs": {
        "version": "v1",
        "dated": "2026-09-27",
        "securities_transaction_tax": {
          "rate": 0.1,
          "unit": "pct_of_turnover_per_leg",
          "source": "Zerodha official charges page (https://zerodha.com/charges/), checked 2026-09-27",
          "as_of_date": "2026-09-27",
          "status": "CONFIRMED"
        },
        "stamp_duty": {
          "rate": 0.015,
          "unit": "pct_of_buy_value_only",
          "source": "Zerodha official charges page (https://zerodha.com/charges/), checked 2026-09-27",
          "as_of_date": "2026-09-27",
          "status": "CONFIRMED"
        },
        "exchange_transaction_charges": {
          "rate": 0.00307,
          "unit": "pct_of_turnover_per_leg",
          "source": "Zerodha official charges page (https://zerodha.com/charges/), checked 2026-09-27 -- NSE equity delivery transaction charge",
          "as_of_date": "2026-09-27",
          "status": "CONFIRMED"
        },
        "sebi_turnover_fee": {
          "rate": 0.0001,
          "unit": "pct_of_turnover_per_leg",
          "source": "Zerodha official charges page (https://zerodha.com/charges/), checked 2026-09-27 -- SEBI turnover fee, Rs 10/crore",
          "as_of_date": "2026-09-27",
          "status": "CONFIRMED"
        },
        "gst": {
          "rate": 18.0,
          "unit": "pct_of_brokerage_plus_exchange_charges_plus_sebi_fee",
          "source": "Standard GST rate applied to brokerage + exchange transaction charges + SEBI fee, not to principal, STT, stamp duty, or the DP charge",
          "as_of_date": "2026-09-27",
          "status": "TO_VERIFY"
        },
        "depository_charges": {
          "rate": 15.34,
          "unit": "flat_inr_per_scrip_per_sell_transaction",
          "source": "Zerodha official charges page (https://zerodha.com/charges/), checked 2026-09-27 -- CDSL Rs 3.50 + Zerodha Rs 9.50 + GST Rs 2.34, GST-inclusive",
          "as_of_date": "2026-09-27",
          "status": "CONFIRMED"
        },
        "brokerage": {
          "rate": 0.0,
          "unit": "flat_inr_per_order",
          "source": "Zerodha official charges page (https://zerodha.com/charges/), checked 2026-09-27 -- Rs 0 brokerage for equity delivery",
          "as_of_date": "2026-09-27",
          "status": "CONFIRMED"
        },
        "slippage_by_liquidity_bucket": [
          {
            "liquidity_bucket": "high",
            "slippage_pct": 0.05,
            "source": "Modelling ASSUMPTION for retail-sized orders in highly liquid large-cap NSE equities -- not a published or confirmed rate",
            "as_of_date": "2026-09-27",
            "status": "ASSUMPTION"
          },
          {
            "liquidity_bucket": "medium",
            "slippage_pct": 0.15,
            "source": "Modelling ASSUMPTION for retail-sized orders in mid-liquidity NSE equities -- not a published or confirmed rate",
            "as_of_date": "2026-09-27",
            "status": "ASSUMPTION"
          },
          {
            "liquidity_bucket": "low",
            "slippage_pct": 0.4,
            "source": "Modelling ASSUMPTION for retail-sized orders in thin/illiquid NSE equities -- not a published or confirmed rate",
            "as_of_date": "2026-09-27",
            "status": "ASSUMPTION"
          }
        ]
      },
      "version_file": "costs_india_delivery_v1.yaml",
      "sha256": "8670e2e48632cabffd9f5faabf9c43dbb8958c0a44883ac563be084abb03eb96"
    },
    "seed": 20261001,
    "bootstrap_replicates": 2000,
    "catalogue_events": 70638,
    "eligible_events": 70362,
    "outside_period_excluded": 276,
    "raw_path": "data/processed/desk_shadow_replay_round2.jsonl",
    "label_function": "scripts.phase8_robustness_relabel_t0.compute_t0_relative",
    "source_hashes": {
      "data/processed/event_catalogue_loose_zscore_only.csv": "ab6dbe701b223076824f4430db5139dba8ed2ecdf9a5cdef5db29ed8e2e81908",
      "data/processed/market_index.csv": "7c87c1d358d1b790d414a21fa306191d6937faedb3e67dbae14c13010fd89f00",
      "data/raw/nse_symbol_isin_current.json": "2b33925b6b589d46f721a98eb0fb96a1bebba0b31a893e0b733de4137981dc0e",
      "scripts/phase8_robustness_relabel_t0.py": "2ff69581aedd202e4d9ab99e02253bf4575aace1c9ffaed98337f93e7804200d",
      "src/signals/event_catalogue.py": "48490cc7d61fc0f3278c1c22352343a00a3f8d215c6e1f0667bceddff5d7a247",
      "scripts/build_final_event_catalogue.py": "3b979955032a4505e8d65d66d41997641ff4145f90c84ede5813d4ca0423ce01",
      "docs/desk/shadow_replay_prereg.md": "efde2065b0f0ad9983c0bce3edeb4415838e01fd1256977c002490ed95eefd94",
      "scripts/desk_shadow_replay.py": "9c9a2861368004cd9c464e25f6f9d0177c5d60b4532fd3c03324687dd273c12f",
      "desk/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "desk/backups.py": "c0b8e6d0841d87dfd46f26aeeb36b63bf480b60cefefd581b99d56c87e090c2a",
      "desk/circuit_bands.py": "3fe7a28f880cc89e6938896cbe613f4ed0c55c381ab0220d21a2dd570fb835db",
      "desk/cli.py": "9323ca0aebbf286818db643d56fb14402aeca31b3cd4bb0b6322cb5a11356044",
      "desk/evaluate.py": "72b4809e8de9e6868f03744b596fa9adc7e16df06e067812d42cd5b47e56abd2",
      "desk/evidence/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "desk/evidence/bundle.py": "3147c5de44f0c2c47afb0f18dd5036c148ae988cac78fe745b1934cc4a326841",
      "desk/evidence/coverage.py": "49054618e17e6ab011fb47c8ec805d6bd4645e75876a4999fbd0c98d6ed842f0",
      "desk/evidence/types.py": "93740aa2270c2b16b504ed3563203e1906e368950031f2605296baa54d3714b0",
      "desk/gates/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "desk/gates/checks.py": "7f9d649a16cd6e8768ebc675191e2ec6c43bed2b8cf1c855b75957f24bf9e3e0",
      "desk/gates/engine.py": "ab66e2e99871c47a8d9fe827aa889f0bbf8a01e95db59adb4ebe2bd93a63829e",
      "desk/ingestion_health.py": "a9ca2f21fc3acae9c277da1cff663ef4520fcf1135ce1567e3948a85b8fab278",
      "desk/journal/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "desk/journal/store.py": "e2f1ff7721e5eec293c69c7b97232e0e43020c0f555502797d7f7d0a65e0518a",
      "desk/lib/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "desk/lib/connection.py": "67341ec12a6c58a883cd0af148dca6c32970c803fff1b90225038757dff4885a",
      "desk/lib/costs.py": "1ed4a80251661d9801a8ac72fa4214899ff83fc428247463afb3c2fe952bbc77",
      "desk/lib/rulebook.py": "d612e7f74548585a26053b21f1d45beb5a6cdef342ebc3014f815d08079772e4",
      "desk/lib/schema.py": "262f62a843b4c34a6517826f57ab0213d46fde2af89bfd01ca2f6240199831c5",
      "desk/lib/store.py": "3952e6a580595c94cae9c29590c9b76b9365de0116838944e0a1ef0226f47cd1",
      "desk/lib/versioned_config.py": "72ef32ea700879ab5ce85aa5e44db603e8473e0aae0d223a33bb160f2207d187",
      "desk/monitor.py": "b93ecb12316a4a91b40a29605b494a09b2da6e71f0f3b23da2ca0cfe49793848",
      "desk/opportunity_store.py": "ca05663820add9217b41775c28aecf1e3461e858074f4d5e4fee771c7da257bc",
      "desk/outcome_firewall.py": "27c380410f8b33c2afe81607db1610eba837048f13312394bf38cc7c3167b9bb",
      "desk/paper/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "desk/paper/close.py": "3cc8dddecadaf6f72bd02debedb12eb265737bf06e780dc87dbc77997df584f9",
      "desk/paper/execution.py": "5801f08432f25053b1583d742cde70888d167a001722bc79ee8d14eab1ebfe8b",
      "desk/paper/open.py": "51f28c1afa653d52ce679f22cdc595cd89e091eaf2555d13e3806409322a281e",
      "desk/process_quality.py": "a6bf785bd856d49c6c6619cf8248a718841048f8eb101a040e3d17062df9db2b",
      "desk/readiness.py": "bf2799f9cda4962788079367ecf7f17b997b60204b0bee9596969b64aba7f28a",
      "desk/replay.py": "1bc6d771e9c1a2a554283497ab24c823a7158d9270a5c808e6b454341eba206c",
      "desk/research_snapshot.py": "4f2296076c5844ad0b6c3bb2ed89baa68d74a7bbc3acf9a5d9633f5a28f8200f",
      "desk/risk/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "desk/risk/officer.py": "7f132d7939e73abaefb59837f03bcc80d0455ab40008de3c8e141797a9969094",
      "desk/scan.py": "7915f818f26edb7ec0fff696c3a19487a648a515d3ed07e9a6399dabbc192656",
      "desk/screening_plan.py": "01404211463073381113cbe0b32dddadd35c40a1f13702b89d0bcaf832198fd8",
      "desk/shadow_analysis.py": "20e5183c57f5d621fc42fe84848cdb02f5ddce31f6d9c0a4c29afb34bb66d5ae",
      "desk/shadow_report.py": "c8afed18cbe70b44e4de90ff06de7a4f691b38ecef2a06c1c5cf1fe7746b4139"
    },
    "snapshot_sha256": {
      "praman": "8f0608c703ba850806e19199c1454cc4657b7a5772bc4ae3bfc86df3eb04627f",
      "desk": "7d28a9250a38b97e4755139ea325929d674e02c500d6737c247438daa3d4dbff"
    },
    "praman_watermark": "2026-10-03T00:51:11.798416+00:00",
    "desk_watermark": "2026-10-03T01:30:45.805725+00:00",
    "price_cutoff": "2026-10-01",
    "market_index_cutoff": "2026-09-22",
    "raw_sha256": "aa619d2e23f113c46e4b4df11307b18bc371837ed5d6bf7069a7d140204acb3d"
  },
  "database_access": "None: all measurements reuse immutable frozen replay records."
}
```

`python -u scripts/desk_shadow_followup.py`

Full values, sample warnings and usable bootstrap counts: `shadow_replay_followup_results.json`. Protocol: `shadow_replay_followup_prereg.md`. No gate or the 90% factor was tuned.
