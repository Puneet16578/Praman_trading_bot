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
| Q4 | 8038 / 7987 / 51 | 4073 / 4043 / 30 | 14.2482 [12.6044, 16.0250]; draws=2000 | 15.4588 [14.0437, 16.9511]; draws=2000 | 1.2107 [-0.5802, 2.8971]; draws=2000 | 1378 / 1221 | 0.2000 |
| Q5 | 6602 / 6551 / 51 | 5510 / 5410 / 100 | 24.8970 [20.0457, 30.8091]; draws=2000 | 23.4381 [20.5091, 26.9710]; draws=2000 | -1.4589 [-4.5245, 1.5146]; draws=2000 | 1230 / 1271 | 0.2000 |

| Comparison | Estimate and interval, percentage points |
|---|---|
| Unstratified gap, same valid-volatility population | 5.9787 [5.0802, 6.8353]; draws=2000 |
| Standardized gap | 0.7383 [-0.2839, 1.7104]; draws=2000 |
| Attenuation: unstratified minus standardized | 5.2404 [4.5232, 6.0541]; draws=2000 |

### Volatility control: Filled only

Missing volatility by screening state: `{"SCREEN_FAIL": {"missing_outcomes": 0, "n": 0}, "SCREEN_PASS": {"missing_outcomes": 0, "n": 0}}`.

| Quintile | PASS candidates / valid / missing | FAIL candidates / valid / missing | PASS rate % [95% CI] | FAIL rate % [95% CI] | FAIL minus PASS, pp [95% CI] | PASS / FAIL valid dates | Weight |
|---|---:|---:|---|---|---|---:|---:|
| Q1 | 11289 / 11248 / 41 | 778 / 773 / 5 | 2.6849 [2.1391, 3.3129]; draws=2000 | 4.2691 [2.7544, 5.9446]; draws=2000 | 1.5842 [0.1574, 3.0733]; draws=2000 | 1334 / 474 | 0.1995 |
| Q2 | 10492 / 10465 / 27 | 1613 / 1604 / 9 | 5.8672 [5.0638, 6.7496]; draws=2000 | 6.6085 [5.4068, 7.9223]; draws=2000 | 0.7413 [-0.5714, 2.1115]; draws=2000 | 1385 / 761 | 0.2001 |
| Q3 | 9345 / 9310 / 35 | 2764 / 2745 / 19 | 9.4200 [8.3632, 10.6681]; draws=2000 | 11.1111 [9.6147, 12.6159]; draws=2000 | 1.6911 [0.2033, 3.0279]; draws=2000 | 1417 / 1043 | 0.2002 |
| Q4 | 8037 / 7987 / 50 | 4073 / 4043 / 30 | 14.2482 [12.6044, 16.0250]; draws=2000 | 15.4588 [14.0437, 16.9511]; draws=2000 | 1.2107 [-0.5802, 2.8971]; draws=2000 | 1378 / 1221 | 0.2002 |
| Q5 | 6600 / 6550 / 50 | 5507 / 5408 / 99 | 24.9008 [20.0457, 30.8135]; draws=2000 | 23.4467 [20.5174, 26.9921]; draws=2000 | -1.4540 [-4.5242, 1.5178]; draws=2000 | 1230 / 1271 | 0.2001 |

| Comparison | Estimate and interval, percentage points |
|---|---|
| Unstratified gap, same valid-volatility population | 6.0233 [5.1280, 6.8886]; draws=2000 |
| Standardized gap | 0.7542 [-0.2635, 1.7283]; draws=2000 |
| Attenuation: unstratified minus standardized | 5.2692 [4.5448, 6.1018]; draws=2000 |

### Fill-cap breaches

Original passes 45770; original fills 45763; original NO_FILL 7; unknown inputs 0; variant abstentions 6; variant fills 45757.

Original filled passes already exceeding a quantitative cap at the decision: 0. Unknown locked components: 45763; unknown historical-gap components: 0.

| Any-cap comparison | Breaches / evaluated fills | Rate % [95% CI] | Valid dates |
|---|---:|---|---:|
| baseline | 23929 / 45763 | 52.2890 [50.7701, 53.7131]; draws=2000 | 1465 |
| variant | 7084 / 45757 | 15.4818 [14.6001, 16.4519]; draws=2000 | 1465 |
| paired_baseline | see paired rate / 45757 | 52.2936 [50.7730, 53.7134]; draws=2000 | 1465 |
| paired_variant | see paired rate / 45757 | 15.4818 [14.6001, 16.4519]; draws=2000 | 1465 |

Paired any-cap difference (variant minus baseline), percentage points: -36.8119 [-37.7521, -35.7696]; draws=2000.

Conditional excess sizes are percentages **over that cap**, among breaches of that cap. Zero-inclusive sizes use every evaluable fill. Empty breach groups are unavailable.

| Cap / variant | Breaches / fills | Breach rate % [95% CI] | Conditional median excess % [95% CI] | Conditional p90 excess % [95% CI] | Breach dates | Zero-inclusive median excess % [95% CI] | Zero-inclusive p90 excess % [95% CI] |
|---|---:|---|---|---|---:|---|---|
| per_trade / baseline | 13904 / 45763 | 30.3826 [29.1097, 31.6754]; draws=2000 | 11.5011 [11.0132, 11.9752]; draws=2000 | 40.6666 [39.3715, 42.3315]; draws=2000 | 1429 | 0.0000 [0.0000, 0.0000]; draws=2000 | 18.0011 [16.8708, 19.2737]; draws=2000 |
| per_trade / variant | 7084 / 45757 | 15.4818 [14.6001, 16.4519]; draws=2000 | 10.1757 [9.7317, 10.6876]; draws=2000 | 41.5112 [39.3049, 43.9077]; draws=2000 | 1333 | 0.0000 [0.0000, 0.0000]; draws=2000 | 6.1797 [5.1854, 7.3577]; draws=2000 |
| open_risk / baseline | 2 / 45763 | 0.0044 [0.0000, 0.0111]; draws=2000 | 2.8276 [0.2202, 5.4350]; draws=1747 SMALL SAMPLE | 4.9136 [0.2202, 5.4350]; draws=1747 SMALL SAMPLE | 2 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| open_risk / variant | 0 / 45757 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_stock / baseline | 15465 / 45763 | 33.7937 [32.6225, 34.9313]; draws=2000 | 0.8320 [0.8028, 0.8590]; draws=2000 | 3.1458 [3.0220, 3.2837]; draws=2000 | 1376 | 0.0000 [0.0000, 0.0000]; draws=2000 | 1.4360 [1.3760, 1.4950]; draws=2000 |
| per_stock / variant | 61 / 45757 | 0.1333 [0.1010, 0.1696]; draws=2000 | 2.2000 [1.3760, 3.0820]; draws=2000 | 7.0840 [5.0185, 7.8083]; draws=2000 | 59 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_sector / baseline | 0 / 45763 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_sector / variant | 0 / 45757 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| order_adv / baseline | 121 / 45763 | 0.2644 [0.2192, 0.3158]; draws=2000 | 1.5852 [1.0790, 2.0753]; draws=2000 | 5.4994 [5.0029, 7.9391]; draws=2000 | 115 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| order_adv / variant | 5 / 45757 | 0.0109 [0.0022, 0.0218]; draws=2000 | 1.4510 [0.7260, 3.2781]; draws=1989 SMALL SAMPLE | 2.6546 [1.3054, 3.2781]; draws=1989 SMALL SAMPLE | 5 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| exit_days / baseline | 0 / 45763 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| exit_days / variant | 0 / 45757 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |

| Cap | Paired rate difference, pp [95% CI] | Conditional median size difference, pp [95% CI] | Conditional p90 size difference, pp [95% CI] |
|---|---|---|---|
| per_trade | -14.9026 [-15.4829, -14.2881]; draws=2000 | -1.3254 [-1.8058, -0.7639]; draws=2000 | 0.8445 [-0.9848, 2.5535]; draws=2000 |
| open_risk | -0.0044 [-0.0111, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |
| per_stock | -33.6648 [-34.8061, -32.5042]; draws=2000 | 1.3680 [0.5577, 2.2553]; draws=2000 | 3.9382 [1.8769, 4.7346]; draws=2000 |
| per_sector | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |
| order_adv | -0.2535 [-0.3049, -0.2084]; draws=2000 | -0.1342 [-0.8591, 1.7536]; draws=1989 | -2.8449 [-6.0266, -1.8687]; draws=1989 |
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
| Q4 | 1388 / 1347 / 41 | 578 / 533 / 45 | 9.5768 [6.6853, 12.7557]; draws=2000 | 14.0713 [10.2908, 18.1479]; draws=2000 | 4.4945 [0.4196, 8.3563]; draws=2000 | 161 / 147 | 0.2040 |
| Q5 | 869 / 844 / 25 | 1041 / 970 / 71 | 14.6919 [10.6165, 20.0921]; draws=2000 | 16.3918 [12.1310, 21.7543]; draws=2000 | 1.6998 [-2.2390, 5.3083]; draws=2000 | 150 / 152 | 0.1982 |

| Comparison | Estimate and interval, percentage points |
|---|---|
| Unstratified gap, same valid-volatility population | 5.1510 [3.1084, 7.4434]; draws=2000 |
| Standardized gap | 1.4810 [-0.2788, 3.2185]; draws=2000 |
| Attenuation: unstratified minus standardized | 3.6700 [2.3899, 5.0850]; draws=2000 |

### Volatility control: Filled only

Missing volatility by screening state: `{"SCREEN_FAIL": {"missing_outcomes": 0, "n": 0}, "SCREEN_PASS": {"missing_outcomes": 0, "n": 0}}`.

| Quintile | PASS candidates / valid / missing | FAIL candidates / valid / missing | PASS rate % [95% CI] | FAIL rate % [95% CI] | FAIL minus PASS, pp [95% CI] | PASS / FAIL valid dates | Weight |
|---|---:|---:|---|---|---|---:|---:|
| Q1 | 1551 / 1471 / 80 | 123 / 109 / 14 | 3.2631 [2.1769, 4.4761]; draws=2000 | 2.7523 [0.0000, 6.1407]; draws=2000 | -0.5108 [-3.1118, 2.7603]; draws=2000 | 156 / 65 | 0.1738 |
| Q2 | 1656 / 1570 / 86 | 281 / 250 / 31 | 5.6688 [4.2882, 7.1042]; draws=2000 | 4.8000 [2.3695, 7.7494]; draws=2000 | -0.8688 [-3.4760, 2.1192]; draws=2000 | 163 / 104 | 0.2011 |
| Q3 | 1676 / 1603 / 73 | 469 / 438 / 31 | 8.6712 [6.7967, 10.6128]; draws=2000 | 10.7306 [7.5784, 14.3226]; draws=2000 | 2.0594 [-1.2656, 5.6892]; draws=2000 | 163 / 139 | 0.2227 |
| Q4 | 1388 / 1347 / 41 | 578 / 533 / 45 | 9.5768 [6.6853, 12.7557]; draws=2000 | 14.0713 [10.2908, 18.1479]; draws=2000 | 4.4945 [0.4196, 8.3563]; draws=2000 | 161 / 147 | 0.2041 |
| Q5 | 869 / 844 / 25 | 1041 / 970 / 71 | 14.6919 [10.6165, 20.0921]; draws=2000 | 16.3918 [12.1310, 21.7543]; draws=2000 | 1.6998 [-2.2390, 5.3083]; draws=2000 | 150 / 152 | 0.1983 |

| Comparison | Estimate and interval, percentage points |
|---|---|
| Unstratified gap, same valid-volatility population | 5.1300 [3.0878, 7.4334]; draws=2000 |
| Standardized gap | 1.4496 [-0.3115, 3.2206]; draws=2000 |
| Attenuation: unstratified minus standardized | 3.6804 [2.3922, 5.1057]; draws=2000 |

### Fill-cap breaches

Original passes 7142; original fills 7140; original NO_FILL 2; unknown inputs 0; variant abstentions 0; variant fills 7140.

Original filled passes already exceeding a quantitative cap at the decision: 0. Unknown locked components: 7140; unknown historical-gap components: 0.

| Any-cap comparison | Breaches / evaluated fills | Rate % [95% CI] | Valid dates |
|---|---:|---|---:|
| baseline | 2990 / 7140 | 41.8768 [38.0391, 46.1767]; draws=2000 | 172 |
| variant | 917 / 7140 | 12.8431 [10.2781, 16.0055]; draws=2000 | 172 |
| paired_baseline | see paired rate / 7140 | 41.8768 [38.0391, 46.1767]; draws=2000 | 172 |
| paired_variant | see paired rate / 7140 | 12.8431 [10.2781, 16.0055]; draws=2000 | 172 |

Paired any-cap difference (variant minus baseline), percentage points: -29.0336 [-31.5583, -26.7195]; draws=2000.

Conditional excess sizes are percentages **over that cap**, among breaches of that cap. Zero-inclusive sizes use every evaluable fill. Empty breach groups are unavailable.

| Cap / variant | Breaches / fills | Breach rate % [95% CI] | Conditional median excess % [95% CI] | Conditional p90 excess % [95% CI] | Breach dates | Zero-inclusive median excess % [95% CI] | Zero-inclusive p90 excess % [95% CI] |
|---|---:|---|---|---|---:|---|---|
| per_trade / baseline | 1819 / 7140 | 25.4762 [22.2953, 29.2609]; draws=2000 | 11.2510 [9.6204, 13.1254]; draws=2000 | 38.4660 [33.1634, 45.1496]; draws=2000 | 171 | 0.0000 [0.0000, 0.0000]; draws=2000 | 15.1658 [11.5461, 19.7068]; draws=2000 |
| per_trade / variant | 917 / 7140 | 12.8431 [10.2781, 16.0055]; draws=2000 | 10.2647 [8.5272, 12.2736]; draws=2000 | 38.7060 [32.2448, 42.4152]; draws=2000 | 159 | 0.0000 [0.0000, 0.0000]; draws=2000 | 3.7087 [0.3309, 7.6195]; draws=2000 |
| open_risk / baseline | 0 / 7140 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| open_risk / variant | 0 / 7140 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_stock / baseline | 1911 / 7140 | 26.7647 [24.1723, 29.4185]; draws=2000 | 0.8060 [0.7406, 0.9360]; draws=2000 | 3.1520 [2.7714, 3.4768]; draws=2000 | 170 | 0.0000 [0.0000, 0.0000]; draws=2000 | 1.1782 [0.9920, 1.4041]; draws=2000 |
| per_stock / variant | 7 / 7140 | 0.0980 [0.0256, 0.2095]; draws=2000 | 2.4320 [1.6236, 6.5000]; draws=1986 SMALL SAMPLE | 6.0864 [2.4320, 6.5000]; draws=1986 SMALL SAMPLE | 5 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_sector / baseline | 0 / 7140 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| per_sector / variant | 0 / 7140 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| order_adv / baseline | 17 / 7140 | 0.2381 [0.1052, 0.3976]; draws=2000 | 2.0030 [0.5557, 3.9768]; draws=2000 SMALL SAMPLE | 6.0212 [2.3922, 6.8205]; draws=2000 SMALL SAMPLE | 13 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| order_adv / variant | 0 / 7140 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| exit_days / baseline | 0 / 7140 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |
| exit_days / variant | 0 / 7140 | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 SMALL SAMPLE | unavailable [unavailable]; draws=0 SMALL SAMPLE | 0 | 0.0000 [0.0000, 0.0000]; draws=2000 | 0.0000 [0.0000, 0.0000]; draws=2000 |

| Cap | Paired rate difference, pp [95% CI] | Conditional median size difference, pp [95% CI] | Conditional p90 size difference, pp [95% CI] |
|---|---|---|---|
| per_trade | -12.6331 [-13.9801, -11.4143]; draws=2000 | -0.9863 [-2.7505, 0.4416]; draws=2000 | 0.2400 [-3.5899, 3.7870]; draws=2000 |
| open_risk | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |
| per_stock | -26.6667 [-29.2715, -24.1148]; draws=2000 | 1.6260 [0.7839, 5.6712]; draws=1986 | 2.9344 [-0.4717, 3.6613]; draws=1986 |
| per_sector | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |
| order_adv | -0.2381 [-0.3976, -0.1052]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |
| exit_days | 0.0000 [0.0000, 0.0000]; draws=2000 | unavailable [unavailable]; draws=0 | unavailable [unavailable]; draws=0 |

Size differences compare conditional distributions whose membership can change. Caps overlap; counts cannot be summed. `per_trade` includes costs, `open_risk` uses stress loss, `per_stock` and `per_sector` use position value, `order_adv` uses frozen turnover and `exit_days` uses stressed exit capacity.

## Provenance and reproduction

```json
{
  "code_commit": "ed8116090a33e787071942e5eb15cdbb7bf116cc",
  "preregistration_commit": "cb89f96faf4cca466482474352bb49a4da2b4f10",
  "base_results_commit": "78015505efe09d3976aa660d6935ebcb868cde09",
  "superseded_results_commit": "64ac2f13a3d419ce63b19b8c9c3b6e3e5b063af5",
  "run_date": "2026-10-04",
  "seed": 20261001,
  "bootstrap_replicates": 2000,
  "decision_cap_fraction": 0.9,
  "raw_sha256": "9a71fcf32912a42e69ae207ee3c8ef47d7e84f72f11e00e012198938d6d299a3",
  "base_results_git_blob_sha256": "8aca605bd2f5f924cde8c73c398f2f60d1803d44b30e7795d858303d5f2ad6dd",
  "preregistration_sha256": "695789f79fee340756ab359a46bdfa23ddb9a03bb997bf0dd37c33216fcf23f0",
  "source_hashes": {
    "docs/desk/shadow_replay_followup_prereg.md": "695789f79fee340756ab359a46bdfa23ddb9a03bb997bf0dd37c33216fcf23f0",
    "desk/shadow_followup.py": "8a984defd9d95e51fd84e617bfb7be732c244d66cd5ccf18009bd7f16d9cdcad",
    "desk/shadow_followup_report.py": "9225ee3e08edc05e5f2363184a8e6dcd7bfb12916de3f6f7f96ab91e729ef320",
    "scripts/desk_shadow_followup.py": "aa6cb68f7881995a70adda54a3ef6668be9f2190b1bd1b947c17b1a10717337b",
    "tests/test_shadow_followup.py": "ab2fc2717e111798fd7e4aedcdfe66285d8f6be1b2c5a96d5a8c45d2f804233a"
  },
  "original_provenance": {
    "code_commit": "78015505efe09d3976aa660d6935ebcb868cde09",
    "run_date": "2026-10-04",
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
      "docs/desk/shadow_replay_prereg.md": "afca8cc46276dc1cfaebe9f9ab7215479fa717de604f7f7a405bd6941a0c76c0",
      "scripts/desk_shadow_replay.py": "27d03403ca3042d1a1ec4cbbfa5b115c8827b305c03f3cee26dc682e73d490f6",
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
      "desk/gates/checks.py": "e00e029188b6ae130b8aeb94f98254a52b2d575c841b49309bcabae362a360b9",
      "desk/gates/engine.py": "c59d7ad688599aed6d024bedcced2b2043a04fcc09e4d8aed6a8f9fcc2bbee63",
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
      "desk/risk/officer.py": "b18d806e3d60f88adc371ce922127bbc61f5f59c63734616d335ff3a88d05d22",
      "desk/scan.py": "7915f818f26edb7ec0fff696c3a19487a648a515d3ed07e9a6399dabbc192656",
      "desk/screening_plan.py": "fae9172f8f90c8bfe0612875d25a4d3e8fe15b3077f28d1f6a299c925a087d67",
      "desk/shadow_analysis.py": "20e5183c57f5d621fc42fe84848cdb02f5ddce31f6d9c0a4c29afb34bb66d5ae",
      "desk/shadow_followup.py": "8a984defd9d95e51fd84e617bfb7be732c244d66cd5ccf18009bd7f16d9cdcad",
      "desk/shadow_followup_report.py": "9225ee3e08edc05e5f2363184a8e6dcd7bfb12916de3f6f7f96ab91e729ef320",
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
    "raw_sha256": "9a71fcf32912a42e69ae207ee3c8ef47d7e84f72f11e00e012198938d6d299a3"
  },
  "database_access": "None: all measurements reuse immutable frozen replay records."
}
```

`python -u scripts/desk_shadow_followup.py`

Full values, sample warnings and usable bootstrap counts: `shadow_replay_followup_results.json`. Protocol: `shadow_replay_followup_prereg.md`. No gate or the 90% factor was tuned.

## Historical volatility context for assessments

Pooled primary candidate rates, including both screening states. The assessment uses the user-specified rounded boundaries 3.2975 / 4.0429 / 4.7966 / 5.8627; the original controlled comparison above retains its exact unrounded boundaries. This is published retrospective context, never historical gate input.

| Quintile | Candidates / valid / missing | Adverse20 rate % [95% CI] | Date clusters |
|---|---:|---|---:|
| Q1 | 12113 / 12066 / 47 | 2.7847 [2.2393, 3.4274]; draws=2000 | 1337 |
| Q2 | 12110 / 12074 / 36 | 5.9798 [5.2325, 6.8183]; draws=2000 | 1390 |
| Q3 | 12114 / 12060 / 54 | 9.8010 [8.7955, 10.9540]; draws=2000 | 1426 |
| Q4 | 12109 / 12028 / 81 | 14.6575 [13.3062, 16.1296]; draws=2000 | 1435 |
| Q5 | 12112 / 11961 / 151 | 24.2371 [20.3316, 28.8964]; draws=2000 | 1411 |

Reference known on 2026-10-04. Reproduce: `python scripts/desk_volatility_reference.py`.
