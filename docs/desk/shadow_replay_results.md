# Desk shadow replay results

This is reconstructed, observational research, not evidence that either live-trading gate is met.

## Limitations and missingness

Current identity mappings reconstruct historical membership. Historical map freshness is unavailable. Candidates use an empty hypothetical portfolio. Fixed-band history is sparse; unknown bands are never zero. Labels and screening share price inputs and the event close; ATR stops mechanically affect stop outcomes. The 2026 period is descriptive only. Intervals are unadjusted for multiple comparisons.

All tails use 20 global sessions; incomplete price windows are missing for 20-session statistics. Entry gaps use the first global session when observed, even if the rest of the window is missing. Adjusted paths use a constant share basis. Execution records retain the identical nightly raw-open, frozen-quantity convention; entry action dates can therefore differ from adjusted tail gaps. Circuit locks require all daily OHLC at the tick-rounded lower limit, using the previous market session report. This is only a daily-data proxy.

Reason groups describe the same semantic check with numeric values and symbols removed; exact reasons remain in the raw artifact. Gate/reason groups overlap and are not additive or independent. Each cohort resamples event-date clusters 2,000 times with seed 20261001. The all-candidate cohort is primary; filled-only is a selection-conditioned sensitivity.

## Provenance

```json
{
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
}
```

## Primary 2019-2025

### All candidates

| Group | Events | Dates | NO_FILL | Zero size | Invalid | Incomplete 20 | Missing 90 | Band covered / unknown | Warning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SCREEN_PASS | 45707 | 1465 | 7 | 0 | 0 | 206 | 597 | 0 / 914140 |  |
| G1 | 47 | 47 | 17 | 17 | 17 | 23 | 1 | 0 / 940 |  |
| G1:security_missing | 47 | 47 | 17 | 17 | 17 | 23 | 1 | 0 / 940 |  |
| G2 | 137 | 126 | 39 | 39 | 39 | 40 | 2 | 0 / 2740 |  |
| G2:required_dimension_delivery | 137 | 126 | 39 | 39 | 39 | 40 | 2 | 0 / 2740 |  |
| G2:required_dimension_price | 134 | 124 | 39 | 39 | 39 | 40 | 2 | 0 / 2680 |  |
| G2:required_dimension_volume | 134 | 124 | 39 | 39 | 39 | 40 | 2 | 0 / 2680 |  |
| G3 | 231 | 215 | 88 | 88 | 88 | 90 | 3 | 0 / 4620 |  |
| G3:structural_break | 231 | 215 | 88 | 88 | 88 | 90 | 3 | 0 / 4620 |  |
| G4 | 3195 | 1135 | 14 | 14 | 14 | 43 | 46 | 0 / 63900 |  |
| G4:ASM | 3186 | 1131 | 14 | 14 | 14 | 38 | 46 | 0 / 63720 |  |
| G4:GSM | 9 | 9 | 0 | 0 | 0 | 5 | 0 | 0 / 180 | small sample |
| G5 | 12424 | 1418 | 189 | 188 | 136 | 289 | 161 | 0 / 248480 |  |
| G5:no_plan | 136 | 129 | 136 | 136 | 136 | 136 | 5 | 0 / 2720 |  |
| G5:order_ADV_cap | 12236 | 1415 | 1 | 0 | 0 | 153 | 156 | 0 / 244720 |  |
| G5:stressed_exit_cap | 2455 | 839 | 0 | 0 | 0 | 79 | 29 | 0 / 49100 |  |
| G5:unknown_coverage | 52 | 52 | 52 | 52 | 0 | 0 | 0 | 0 / 1040 |  |
| G6 | 253 | 226 | 188 | 188 | 136 | 137 | 5 | 0 / 5060 |  |
| G6:no_plan | 136 | 129 | 136 | 136 | 136 | 136 | 5 | 0 / 2720 |  |
| G6:open_risk_cap | 65 | 57 | 0 | 0 | 0 | 1 | 0 | 0 / 1300 |  |
| G6:unknown_coverage | 52 | 52 | 52 | 52 | 0 | 0 | 0 | 0 / 1040 |  |
| SCREEN_FAIL | 14987 | 1454 | 189 | 188 | 136 | 299 | 199 | 0 / 299740 |  |

| Group / statistic | Estimate | n events / denominator | Missing events | 95% interval (usable draws) | Difference vs PASS | Difference 95% interval (usable draws) |
|---|---:|---:|---:|---|---:|---|
| SCREEN_PASS / signed_return_90d | -0.021353 | 45110 / 45110 | 597 | -0.025721, -0.017177 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / collapse | 0.588761 | 45110 / 45110 | 597 | 0.577961, 0.599023 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / adverse20 | 0.099998 | 45501 / 45501 | 206 | 0.086882, 0.116749 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / stop_gap | 0.039076 | 45501 / 45501 | 206 | 0.034756, 0.044280 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / entry_gap | 0.002699 | 45578 / 45578 | 129 | 0.000909, 0.005650 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_decision | 0.096999 | 45501 / 45501 | 206 | 0.092679, 0.102403 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_fill | 0.102308 | 45497 / 45497 | 210 | 0.098442, 0.106819 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / locked_rate [small sample] | unavailable | 0 / 0 | 45707 | unavailable (0) | unavailable | unavailable (0) |
| G1 / signed_return_90d | -0.053483 | 46 / 46 | 1 | -0.116156, 0.012668 (2000) | -0.032130 | -0.095214, 0.035391 (2000) |
| G1 / collapse | 0.608696 | 46 / 46 | 1 | 0.456522, 0.750000 (2000) | 0.019935 | -0.132372, 0.162324 (2000) |
| G1 / adverse20 [small sample] | 0.250000 | 24 / 24 | 23 | 0.079923, 0.437500 (2000) | 0.150002 | -0.020972, 0.335786 (2000) |
| G1 / stop_gap [small sample] | 0.125000 | 24 / 24 | 23 | 0.000000, 0.269318 (2000) | 0.085924 | -0.039171, 0.230450 (2000) |
| G1 / entry_gap | 0.000000 | 30 / 30 | 17 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G1 / mae_decision [small sample] | 0.138969 | 24 / 24 | 23 | 0.092798, 0.187440 (2000) | 0.041969 | -0.003953, 0.090929 (2000) |
| G1 / mae_fill [small sample] | 0.165184 | 24 / 24 | 23 | 0.114218, 0.218603 (2000) | 0.062876 | 0.012367, 0.116548 (2000) |
| G1 / locked_rate [small sample] | unavailable | 0 / 0 | 47 | unavailable (0) | unavailable | unavailable (0) |
| G1:security_missing / signed_return_90d | -0.053483 | 46 / 46 | 1 | -0.116156, 0.012668 (2000) | -0.032130 | -0.095214, 0.035391 (2000) |
| G1:security_missing / collapse | 0.608696 | 46 / 46 | 1 | 0.456522, 0.750000 (2000) | 0.019935 | -0.132372, 0.162324 (2000) |
| G1:security_missing / adverse20 [small sample] | 0.250000 | 24 / 24 | 23 | 0.079923, 0.437500 (2000) | 0.150002 | -0.020972, 0.335786 (2000) |
| G1:security_missing / stop_gap [small sample] | 0.125000 | 24 / 24 | 23 | 0.000000, 0.269318 (2000) | 0.085924 | -0.039171, 0.230450 (2000) |
| G1:security_missing / entry_gap | 0.000000 | 30 / 30 | 17 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G1:security_missing / mae_decision [small sample] | 0.138969 | 24 / 24 | 23 | 0.092798, 0.187440 (2000) | 0.041969 | -0.003953, 0.090929 (2000) |
| G1:security_missing / mae_fill [small sample] | 0.165184 | 24 / 24 | 23 | 0.114218, 0.218603 (2000) | 0.062876 | 0.012367, 0.116548 (2000) |
| G1:security_missing / locked_rate [small sample] | unavailable | 0 / 0 | 47 | unavailable (0) | unavailable | unavailable (0) |
| G2 / signed_return_90d | -0.022913 | 135 / 135 | 2 | -0.081767, 0.033264 (2000) | -0.001559 | -0.061189, 0.054935 (2000) |
| G2 / collapse | 0.548148 | 135 / 135 | 2 | 0.469685, 0.632820 (2000) | -0.040613 | -0.120744, 0.043286 (2000) |
| G2 / adverse20 | 0.144330 | 97 / 97 | 40 | 0.075467, 0.220000 (2000) | 0.044332 | -0.022207, 0.115112 (2000) |
| G2 / stop_gap | 0.041237 | 97 / 97 | 40 | 0.009091, 0.085714 (2000) | 0.002161 | -0.032792, 0.048212 (2000) |
| G2 / entry_gap | 0.000000 | 97 / 97 | 40 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G2 / mae_decision | 0.103010 | 97 / 97 | 40 | 0.085802, 0.121667 (2000) | 0.006011 | -0.010720, 0.023692 (2000) |
| G2 / mae_fill | 0.110434 | 97 / 97 | 40 | 0.092652, 0.129091 (2000) | 0.008126 | -0.008391, 0.026095 (2000) |
| G2 / locked_rate [small sample] | unavailable | 0 / 0 | 137 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_delivery / signed_return_90d | -0.022913 | 135 / 135 | 2 | -0.081767, 0.033264 (2000) | -0.001559 | -0.061189, 0.054935 (2000) |
| G2:required_dimension_delivery / collapse | 0.548148 | 135 / 135 | 2 | 0.469685, 0.632820 (2000) | -0.040613 | -0.120744, 0.043286 (2000) |
| G2:required_dimension_delivery / adverse20 | 0.144330 | 97 / 97 | 40 | 0.075467, 0.220000 (2000) | 0.044332 | -0.022207, 0.115112 (2000) |
| G2:required_dimension_delivery / stop_gap | 0.041237 | 97 / 97 | 40 | 0.009091, 0.085714 (2000) | 0.002161 | -0.032792, 0.048212 (2000) |
| G2:required_dimension_delivery / entry_gap | 0.000000 | 97 / 97 | 40 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G2:required_dimension_delivery / mae_decision | 0.103010 | 97 / 97 | 40 | 0.085802, 0.121667 (2000) | 0.006011 | -0.010720, 0.023692 (2000) |
| G2:required_dimension_delivery / mae_fill | 0.110434 | 97 / 97 | 40 | 0.092652, 0.129091 (2000) | 0.008126 | -0.008391, 0.026095 (2000) |
| G2:required_dimension_delivery / locked_rate [small sample] | unavailable | 0 / 0 | 137 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_price / signed_return_90d | -0.007840 | 132 / 132 | 2 | -0.051879, 0.035927 (2000) | 0.013513 | -0.030512, 0.056136 (2000) |
| G2:required_dimension_price / collapse | 0.545455 | 132 / 132 | 2 | 0.463759, 0.629930 (2000) | -0.043306 | -0.124057, 0.041901 (2000) |
| G2:required_dimension_price / adverse20 | 0.127660 | 94 / 94 | 40 | 0.064499, 0.197802 (2000) | 0.027662 | -0.036455, 0.094915 (2000) |
| G2:required_dimension_price / stop_gap | 0.042553 | 94 / 94 | 40 | 0.009344, 0.088496 (2000) | 0.003477 | -0.032248, 0.051193 (2000) |
| G2:required_dimension_price / entry_gap | 0.000000 | 94 / 94 | 40 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G2:required_dimension_price / mae_decision | 0.097666 | 94 / 94 | 40 | 0.081180, 0.115162 (2000) | 0.000667 | -0.015443, 0.016962 (2000) |
| G2:required_dimension_price / mae_fill | 0.103906 | 94 / 94 | 40 | 0.088237, 0.120658 (2000) | 0.001598 | -0.013212, 0.017322 (2000) |
| G2:required_dimension_price / locked_rate [small sample] | unavailable | 0 / 0 | 134 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_volume / signed_return_90d | -0.007840 | 132 / 132 | 2 | -0.051879, 0.035927 (2000) | 0.013513 | -0.030512, 0.056136 (2000) |
| G2:required_dimension_volume / collapse | 0.545455 | 132 / 132 | 2 | 0.463759, 0.629930 (2000) | -0.043306 | -0.124057, 0.041901 (2000) |
| G2:required_dimension_volume / adverse20 | 0.127660 | 94 / 94 | 40 | 0.064499, 0.197802 (2000) | 0.027662 | -0.036455, 0.094915 (2000) |
| G2:required_dimension_volume / stop_gap | 0.042553 | 94 / 94 | 40 | 0.009344, 0.088496 (2000) | 0.003477 | -0.032248, 0.051193 (2000) |
| G2:required_dimension_volume / entry_gap | 0.000000 | 94 / 94 | 40 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G2:required_dimension_volume / mae_decision | 0.097666 | 94 / 94 | 40 | 0.081180, 0.115162 (2000) | 0.000667 | -0.015443, 0.016962 (2000) |
| G2:required_dimension_volume / mae_fill | 0.103906 | 94 / 94 | 40 | 0.088237, 0.120658 (2000) | 0.001598 | -0.013212, 0.017322 (2000) |
| G2:required_dimension_volume / locked_rate [small sample] | unavailable | 0 / 0 | 134 | unavailable (0) | unavailable | unavailable (0) |
| G3 / signed_return_90d | 0.013525 | 228 / 228 | 3 | -0.029076, 0.055942 (2000) | 0.034878 | -0.008082, 0.077298 (2000) |
| G3 / collapse | 0.521930 | 228 / 228 | 3 | 0.457625, 0.587393 (2000) | -0.066831 | -0.131895, -0.000767 (2000) |
| G3 / adverse20 | 0.170213 | 141 / 141 | 90 | 0.110294, 0.230795 (2000) | 0.070215 | 0.009508, 0.132757 (2000) |
| G3 / stop_gap | 0.085106 | 141 / 141 | 90 | 0.040541, 0.131397 (2000) | 0.046030 | 0.001529, 0.091338 (2000) |
| G3 / entry_gap | 0.000000 | 143 / 143 | 88 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G3 / mae_decision | 0.117780 | 141 / 141 | 90 | 0.101219, 0.134943 (2000) | 0.020781 | 0.003972, 0.038507 (2000) |
| G3 / mae_fill | 0.124647 | 141 / 141 | 90 | 0.108547, 0.140469 (2000) | 0.022339 | 0.006196, 0.038807 (2000) |
| G3 / locked_rate [small sample] | unavailable | 0 / 0 | 231 | unavailable (0) | unavailable | unavailable (0) |
| G3:structural_break / signed_return_90d | 0.013525 | 228 / 228 | 3 | -0.029076, 0.055942 (2000) | 0.034878 | -0.008082, 0.077298 (2000) |
| G3:structural_break / collapse | 0.521930 | 228 / 228 | 3 | 0.457625, 0.587393 (2000) | -0.066831 | -0.131895, -0.000767 (2000) |
| G3:structural_break / adverse20 | 0.170213 | 141 / 141 | 90 | 0.110294, 0.230795 (2000) | 0.070215 | 0.009508, 0.132757 (2000) |
| G3:structural_break / stop_gap | 0.085106 | 141 / 141 | 90 | 0.040541, 0.131397 (2000) | 0.046030 | 0.001529, 0.091338 (2000) |
| G3:structural_break / entry_gap | 0.000000 | 143 / 143 | 88 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G3:structural_break / mae_decision | 0.117780 | 141 / 141 | 90 | 0.101219, 0.134943 (2000) | 0.020781 | 0.003972, 0.038507 (2000) |
| G3:structural_break / mae_fill | 0.124647 | 141 / 141 | 90 | 0.108547, 0.140469 (2000) | 0.022339 | 0.006196, 0.038807 (2000) |
| G3:structural_break / locked_rate [small sample] | unavailable | 0 / 0 | 231 | unavailable (0) | unavailable | unavailable (0) |
| G4 / signed_return_90d | -0.034995 | 3149 / 3149 | 46 | -0.046127, -0.024182 (2000) | -0.013641 | -0.024952, -0.002359 (2000) |
| G4 / collapse | 0.597332 | 3149 / 3149 | 46 | 0.576738, 0.617871 (2000) | 0.008572 | -0.010992, 0.028769 (2000) |
| G4 / adverse20 | 0.190990 | 3152 / 3152 | 43 | 0.174385, 0.209824 (2000) | 0.090992 | 0.073195, 0.108036 (2000) |
| G4 / stop_gap | 0.073921 | 3152 / 3152 | 43 | 0.064077, 0.084333 (2000) | 0.034845 | 0.024906, 0.045285 (2000) |
| G4 / entry_gap | 0.002205 | 3174 / 3174 | 21 | 0.000913, 0.003990 (2000) | -0.000493 | -0.002876, 0.001531 (2000) |
| G4 / mae_decision | 0.126055 | 3152 / 3152 | 43 | 0.121049, 0.131374 (2000) | 0.029056 | 0.024516, 0.033444 (2000) |
| G4 / mae_fill | 0.139451 | 3152 / 3152 | 43 | 0.134364, 0.144857 (2000) | 0.037143 | 0.032780, 0.041666 (2000) |
| G4 / locked_rate [small sample] | unavailable | 0 / 0 | 3195 | unavailable (0) | unavailable | unavailable (0) |
| G4:ASM / signed_return_90d | -0.034716 | 3140 / 3140 | 46 | -0.045959, -0.023880 (2000) | -0.013362 | -0.024769, -0.002091 (2000) |
| G4:ASM / collapse | 0.596815 | 3140 / 3140 | 46 | 0.576132, 0.617593 (2000) | 0.008054 | -0.011615, 0.028190 (2000) |
| G4:ASM / adverse20 | 0.190915 | 3148 / 3148 | 38 | 0.174349, 0.209845 (2000) | 0.090917 | 0.073114, 0.108032 (2000) |
| G4:ASM / stop_gap | 0.074015 | 3148 / 3148 | 38 | 0.064150, 0.084415 (2000) | 0.034939 | 0.025036, 0.045386 (2000) |
| G4:ASM / entry_gap | 0.002212 | 3165 / 3165 | 21 | 0.000917, 0.004006 (2000) | -0.000487 | -0.002866, 0.001540 (2000) |
| G4:ASM / mae_decision | 0.126062 | 3148 / 3148 | 38 | 0.121011, 0.131404 (2000) | 0.029063 | 0.024510, 0.033480 (2000) |
| G4:ASM / mae_fill | 0.139426 | 3148 / 3148 | 38 | 0.134329, 0.144831 (2000) | 0.037118 | 0.032724, 0.041625 (2000) |
| G4:ASM / locked_rate [small sample] | unavailable | 0 / 0 | 3186 | unavailable (0) | unavailable | unavailable (0) |
| G4:GSM / signed_return_90d [small sample] | -0.132269 | 9 / 9 | 0 | -0.230099, -0.031760 (2000) | -0.110915 | -0.209546, -0.011307 (2000) |
| G4:GSM / collapse [small sample] | 0.777778 | 9 / 9 | 0 | 0.499038, 1.000000 (2000) | 0.189017 | -0.100670, 0.416219 (2000) |
| G4:GSM / adverse20 [small sample] | 0.250000 | 4 / 4 | 5 | 0.000000, 1.000000 (1966) | 0.150002 | -0.111361, 0.891099 (1966) |
| G4:GSM / stop_gap [small sample] | 0.000000 | 4 / 4 | 5 | 0.000000, 0.000000 (1966) | -0.039076 | -0.044277, -0.034677 (1966) |
| G4:GSM / entry_gap [small sample] | 0.000000 | 9 / 9 | 0 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G4:GSM / mae_decision [small sample] | 0.120905 | 4 / 4 | 5 | 0.069841, 0.213514 (1966) | 0.023906 | -0.026461, 0.113155 (1966) |
| G4:GSM / mae_fill [small sample] | 0.159566 | 4 / 4 | 5 | 0.095689, 0.269011 (1966) | 0.057258 | -0.003325, 0.163610 (1966) |
| G4:GSM / locked_rate [small sample] | unavailable | 0 / 0 | 9 | unavailable (0) | unavailable | unavailable (0) |
| G5 / signed_return_90d | -0.033960 | 12263 / 12263 | 161 | -0.039886, -0.027555 (2000) | -0.012606 | -0.019407, -0.005151 (2000) |
| G5 / collapse | 0.636957 | 12263 / 12263 | 161 | 0.624488, 0.648118 (2000) | 0.048196 | 0.035881, 0.060279 (2000) |
| G5 / adverse20 | 0.157396 | 12135 / 12135 | 289 | 0.140142, 0.178683 (2000) | 0.057398 | 0.047528, 0.067807 (2000) |
| G5 / stop_gap | 0.056448 | 12135 / 12135 | 289 | 0.051674, 0.061792 (2000) | 0.017372 | 0.012442, 0.022473 (2000) |
| G5 / entry_gap | 0.000979 | 12262 / 12262 | 162 | 0.000083, 0.002498 (2000) | -0.001720 | -0.003306, -0.000501 (2000) |
| G5 / mae_decision | 0.117929 | 12135 / 12135 | 289 | 0.112785, 0.124319 (2000) | 0.020929 | 0.017774, 0.024206 (2000) |
| G5 / mae_fill | 0.137747 | 12083 / 12083 | 341 | 0.133129, 0.143231 (2000) | 0.035439 | 0.032304, 0.038753 (2000) |
| G5 / locked_rate [small sample] | unavailable | 0 / 0 | 12424 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / signed_return_90d | -0.049994 | 131 / 131 | 5 | -0.101690, 0.001204 (2000) | -0.028640 | -0.079978, 0.022851 (2000) |
| G5:no_plan / collapse | 0.595420 | 131 / 131 | 5 | 0.508471, 0.682563 (2000) | 0.006659 | -0.077988, 0.095436 (2000) |
| G5:no_plan / adverse20 [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / stop_gap [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / entry_gap [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / mae_decision [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / mae_fill [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / locked_rate [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:order_ADV_cap / signed_return_90d | -0.033702 | 12080 / 12080 | 156 | -0.039678, -0.027123 (2000) | -0.012349 | -0.019414, -0.004914 (2000) |
| G5:order_ADV_cap / collapse | 0.637417 | 12080 / 12080 | 156 | 0.624797, 0.648672 (2000) | 0.048656 | 0.036201, 0.060883 (2000) |
| G5:order_ADV_cap / adverse20 | 0.157908 | 12083 / 12083 | 153 | 0.140559, 0.179236 (2000) | 0.057910 | 0.047969, 0.068409 (2000) |
| G5:order_ADV_cap / stop_gap | 0.056608 | 12083 / 12083 | 153 | 0.051885, 0.061919 (2000) | 0.017532 | 0.012510, 0.022691 (2000) |
| G5:order_ADV_cap / entry_gap | 0.000901 | 12210 / 12210 | 26 | 0.000083, 0.002249 (2000) | -0.001798 | -0.003518, -0.000502 (2000) |
| G5:order_ADV_cap / mae_decision | 0.118201 | 12083 / 12083 | 153 | 0.113049, 0.124606 (2000) | 0.021202 | 0.018041, 0.024507 (2000) |
| G5:order_ADV_cap / mae_fill | 0.137747 | 12083 / 12083 | 153 | 0.133129, 0.143231 (2000) | 0.035439 | 0.032304, 0.038753 (2000) |
| G5:order_ADV_cap / locked_rate [small sample] | unavailable | 0 / 0 | 12236 | unavailable (0) | unavailable | unavailable (0) |
| G5:stressed_exit_cap / signed_return_90d | -0.025738 | 2426 / 2426 | 29 | -0.040529, -0.009934 (2000) | -0.004384 | -0.019477, 0.011545 (2000) |
| G5:stressed_exit_cap / collapse | 0.636026 | 2426 / 2426 | 29 | 0.613498, 0.658264 (2000) | 0.047266 | 0.024374, 0.070435 (2000) |
| G5:stressed_exit_cap / adverse20 | 0.182239 | 2376 / 2376 | 79 | 0.156813, 0.208782 (2000) | 0.082241 | 0.060789, 0.105620 (2000) |
| G5:stressed_exit_cap / stop_gap | 0.077441 | 2376 / 2376 | 79 | 0.066782, 0.088450 (2000) | 0.038365 | 0.026976, 0.049545 (2000) |
| G5:stressed_exit_cap / entry_gap | 0.001224 | 2451 / 2451 | 4 | 0.000000, 0.002806 (2000) | -0.001475 | -0.003666, 0.000486 (2000) |
| G5:stressed_exit_cap / mae_decision | 0.120558 | 2376 / 2376 | 79 | 0.113195, 0.128626 (2000) | 0.023559 | 0.017076, 0.030281 (2000) |
| G5:stressed_exit_cap / mae_fill | 0.151595 | 2376 / 2376 | 79 | 0.144724, 0.158813 (2000) | 0.049287 | 0.043229, 0.055761 (2000) |
| G5:stressed_exit_cap / locked_rate [small sample] | unavailable | 0 / 0 | 2455 | unavailable (0) | unavailable | unavailable (0) |
| G5:unknown_coverage / signed_return_90d | -0.053314 | 52 / 52 | 0 | -0.100919, -0.004742 (2000) | -0.031960 | -0.079888, 0.015935 (2000) |
| G5:unknown_coverage / collapse | 0.634615 | 52 / 52 | 0 | 0.500000, 0.763170 (2000) | 0.045855 | -0.086338, 0.172025 (2000) |
| G5:unknown_coverage / adverse20 | 0.038462 | 52 / 52 | 0 | 0.000000, 0.098039 (2000) | -0.061536 | -0.105267, -0.001550 (2000) |
| G5:unknown_coverage / stop_gap | 0.019231 | 52 / 52 | 0 | 0.000000, 0.063492 (2000) | -0.019845 | -0.040540, 0.020662 (2000) |
| G5:unknown_coverage / entry_gap | 0.019231 | 52 / 52 | 0 | 0.000000, 0.063492 (2000) | 0.016532 | -0.002381, 0.057748 (2000) |
| G5:unknown_coverage / mae_decision | 0.054696 | 52 / 52 | 0 | 0.040710, 0.069969 (2000) | -0.042303 | -0.054963, -0.028418 (2000) |
| G5:unknown_coverage / mae_fill [small sample] | unavailable | 0 / 0 | 52 | unavailable (0) | unavailable | unavailable (0) |
| G5:unknown_coverage / locked_rate [small sample] | unavailable | 0 / 0 | 52 | unavailable (0) | unavailable | unavailable (0) |
| G6 / signed_return_90d | -0.033906 | 248 / 248 | 5 | -0.070520, 0.005826 (2000) | -0.012553 | -0.049229, 0.026374 (2000) |
| G6 / collapse | 0.612903 | 248 / 248 | 5 | 0.552297, 0.670783 (2000) | 0.024142 | -0.036011, 0.081417 (2000) |
| G6 / adverse20 | 0.163793 | 116 / 116 | 137 | 0.097345, 0.227723 (2000) | 0.063795 | -0.001472, 0.128241 (2000) |
| G6 / stop_gap | 0.094828 | 116 / 116 | 137 | 0.043469, 0.150951 (2000) | 0.055752 | 0.004266, 0.111373 (2000) |
| G6 / entry_gap | 0.008547 | 117 / 117 | 136 | 0.000000, 0.028777 (2000) | 0.005848 | -0.002381, 0.023031 (2000) |
| G6 / mae_decision | 0.098120 | 116 / 116 | 137 | 0.082348, 0.114784 (2000) | 0.001121 | -0.014556, 0.017371 (2000) |
| G6 / mae_fill | 0.159546 | 64 / 64 | 189 | 0.136302, 0.182136 (2000) | 0.057238 | 0.034323, 0.080173 (2000) |
| G6 / locked_rate [small sample] | unavailable | 0 / 0 | 253 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / signed_return_90d | -0.049994 | 131 / 131 | 5 | -0.101690, 0.001204 (2000) | -0.028640 | -0.079978, 0.022851 (2000) |
| G6:no_plan / collapse | 0.595420 | 131 / 131 | 5 | 0.508471, 0.682563 (2000) | 0.006659 | -0.077988, 0.095436 (2000) |
| G6:no_plan / adverse20 [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / stop_gap [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / entry_gap [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / mae_decision [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / mae_fill [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / locked_rate [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:open_risk_cap / signed_return_90d | 0.014043 | 65 / 65 | 0 | -0.077147, 0.117997 (2000) | 0.035396 | -0.055430, 0.139420 (2000) |
| G6:open_risk_cap / collapse | 0.630769 | 65 / 65 | 0 | 0.508190, 0.742867 (2000) | 0.042008 | -0.083080, 0.155486 (2000) |
| G6:open_risk_cap / adverse20 | 0.265625 | 64 / 64 | 1 | 0.161753, 0.372888 (2000) | 0.165627 | 0.061569, 0.270951 (2000) |
| G6:open_risk_cap / stop_gap | 0.156250 | 64 / 64 | 1 | 0.069432, 0.250000 (2000) | 0.117174 | 0.030488, 0.211559 (2000) |
| G6:open_risk_cap / entry_gap | 0.000000 | 65 / 65 | 0 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G6:open_risk_cap / mae_decision | 0.133402 | 64 / 64 | 1 | 0.108251, 0.157363 (2000) | 0.036403 | 0.011263, 0.060442 (2000) |
| G6:open_risk_cap / mae_fill | 0.159546 | 64 / 64 | 1 | 0.136302, 0.182136 (2000) | 0.057238 | 0.034323, 0.080173 (2000) |
| G6:open_risk_cap / locked_rate [small sample] | unavailable | 0 / 0 | 65 | unavailable (0) | unavailable | unavailable (0) |
| G6:unknown_coverage / signed_return_90d | -0.053314 | 52 / 52 | 0 | -0.100919, -0.004742 (2000) | -0.031960 | -0.079888, 0.015935 (2000) |
| G6:unknown_coverage / collapse | 0.634615 | 52 / 52 | 0 | 0.500000, 0.763170 (2000) | 0.045855 | -0.086338, 0.172025 (2000) |
| G6:unknown_coverage / adverse20 | 0.038462 | 52 / 52 | 0 | 0.000000, 0.098039 (2000) | -0.061536 | -0.105267, -0.001550 (2000) |
| G6:unknown_coverage / stop_gap | 0.019231 | 52 / 52 | 0 | 0.000000, 0.063492 (2000) | -0.019845 | -0.040540, 0.020662 (2000) |
| G6:unknown_coverage / entry_gap | 0.019231 | 52 / 52 | 0 | 0.000000, 0.063492 (2000) | 0.016532 | -0.002381, 0.057748 (2000) |
| G6:unknown_coverage / mae_decision | 0.054696 | 52 / 52 | 0 | 0.040710, 0.069969 (2000) | -0.042303 | -0.054963, -0.028418 (2000) |
| G6:unknown_coverage / mae_fill [small sample] | unavailable | 0 / 0 | 52 | unavailable (0) | unavailable | unavailable (0) |
| G6:unknown_coverage / locked_rate [small sample] | unavailable | 0 / 0 | 52 | unavailable (0) | unavailable | unavailable (0) |
| SCREEN_FAIL / signed_return_90d | -0.031802 | 14788 / 14788 | 199 | -0.037272, -0.025817 (2000) | -0.010449 | -0.017266, -0.003606 (2000) |
| SCREEN_FAIL / collapse | 0.625304 | 14788 / 14788 | 199 | 0.613814, 0.636060 (2000) | 0.036543 | 0.025401, 0.047795 (2000) |
| SCREEN_FAIL / adverse20 | 0.160131 | 14688 / 14688 | 299 | 0.144310, 0.178904 (2000) | 0.060133 | 0.051103, 0.068875 (2000) |
| SCREEN_FAIL / stop_gap | 0.056917 | 14688 / 14688 | 299 | 0.052449, 0.062002 (2000) | 0.017841 | 0.013229, 0.022488 (2000) |
| SCREEN_FAIL / entry_gap | 0.001282 | 14821 / 14821 | 166 | 0.000403, 0.002750 (2000) | -0.001417 | -0.003013, -0.000218 (2000) |
| SCREEN_FAIL / mae_decision | 0.118141 | 14688 / 14688 | 299 | 0.113453, 0.124015 (2000) | 0.021142 | 0.018374, 0.023981 (2000) |
| SCREEN_FAIL / mae_fill | 0.136177 | 14636 / 14636 | 351 | 0.131836, 0.141211 (2000) | 0.033869 | 0.031196, 0.036579 (2000) |
| SCREEN_FAIL / locked_rate [small sample] | unavailable | 0 / 0 | 14987 | unavailable (0) | unavailable | unavailable (0) |

### Filled only

| Group | Events | Dates | NO_FILL | Zero size | Invalid | Incomplete 20 | Missing 90 | Band covered / unknown | Warning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SCREEN_PASS | 45700 | 1465 | 0 | 0 | 0 | 203 | 595 | 0 / 914000 |  |
| G1 | 30 | 30 | 0 | 0 | 0 | 6 | 1 | 0 / 600 |  |
| G1:security_missing | 30 | 30 | 0 | 0 | 0 | 6 | 1 | 0 / 600 |  |
| G2 | 98 | 96 | 0 | 0 | 0 | 1 | 1 | 0 / 1960 |  |
| G2:required_dimension_delivery | 98 | 96 | 0 | 0 | 0 | 1 | 1 | 0 / 1960 |  |
| G2:required_dimension_price | 95 | 93 | 0 | 0 | 0 | 1 | 1 | 0 / 1900 |  |
| G2:required_dimension_volume | 95 | 93 | 0 | 0 | 0 | 1 | 1 | 0 / 1900 |  |
| G3 | 143 | 136 | 0 | 0 | 0 | 2 | 2 | 0 / 2860 |  |
| G3:structural_break | 143 | 136 | 0 | 0 | 0 | 2 | 2 | 0 / 2860 |  |
| G4 | 3181 | 1135 | 0 | 0 | 0 | 29 | 45 | 0 / 63620 |  |
| G4:ASM | 3172 | 1131 | 0 | 0 | 0 | 24 | 45 | 0 / 63440 |  |
| G4:GSM | 9 | 9 | 0 | 0 | 0 | 5 | 0 | 0 / 180 | small sample |
| G5 | 12235 | 1415 | 0 | 0 | 0 | 152 | 155 | 0 / 244700 |  |
| G5:order_ADV_cap | 12235 | 1415 | 0 | 0 | 0 | 152 | 155 | 0 / 244700 |  |
| G5:stressed_exit_cap | 2455 | 839 | 0 | 0 | 0 | 79 | 29 | 0 / 49100 |  |
| G6 | 65 | 57 | 0 | 0 | 0 | 1 | 0 | 0 / 1300 |  |
| G6:open_risk_cap | 65 | 57 | 0 | 0 | 0 | 1 | 0 | 0 / 1300 |  |
| SCREEN_FAIL | 14798 | 1452 | 0 | 0 | 0 | 162 | 193 | 0 / 295960 |  |

| Group / statistic | Estimate | n events / denominator | Missing events | 95% interval (usable draws) | Difference vs PASS | Difference 95% interval (usable draws) |
|---|---:|---:|---:|---|---:|---|
| SCREEN_PASS / signed_return_90d | -0.021337 | 45105 / 45105 | 595 | -0.025706, -0.017164 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / collapse | 0.588715 | 45105 / 45105 | 595 | 0.577896, 0.598978 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / adverse20 | 0.099985 | 45497 / 45497 | 203 | 0.086868, 0.116735 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / stop_gap | 0.039079 | 45497 / 45497 | 203 | 0.034757, 0.044284 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / entry_gap | 0.002699 | 45574 / 45574 | 126 | 0.000909, 0.005650 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_decision | 0.096996 | 45497 / 45497 | 203 | 0.092680, 0.102395 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_fill | 0.102308 | 45497 / 45497 | 203 | 0.098442, 0.106819 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / locked_rate [small sample] | unavailable | 0 / 0 | 45700 | unavailable (0) | unavailable | unavailable (0) |
| G1 / signed_return_90d [small sample] | -0.031005 | 29 / 29 | 1 | -0.114212, 0.057869 (2000) | -0.009668 | -0.093346, 0.079483 (2000) |
| G1 / collapse [small sample] | 0.551724 | 29 / 29 | 1 | 0.370370, 0.733333 (2000) | -0.036991 | -0.215633, 0.143603 (2000) |
| G1 / adverse20 [small sample] | 0.250000 | 24 / 24 | 6 | 0.079923, 0.437500 (2000) | 0.150015 | -0.020920, 0.335806 (2000) |
| G1 / stop_gap [small sample] | 0.125000 | 24 / 24 | 6 | 0.000000, 0.269318 (2000) | 0.085921 | -0.039178, 0.230447 (2000) |
| G1 / entry_gap | 0.000000 | 30 / 30 | 0 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G1 / mae_decision [small sample] | 0.138969 | 24 / 24 | 6 | 0.092798, 0.187440 (2000) | 0.041972 | -0.003950, 0.090937 (2000) |
| G1 / mae_fill [small sample] | 0.165184 | 24 / 24 | 6 | 0.114218, 0.218603 (2000) | 0.062876 | 0.012367, 0.116548 (2000) |
| G1 / locked_rate [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G1:security_missing / signed_return_90d [small sample] | -0.031005 | 29 / 29 | 1 | -0.114212, 0.057869 (2000) | -0.009668 | -0.093346, 0.079483 (2000) |
| G1:security_missing / collapse [small sample] | 0.551724 | 29 / 29 | 1 | 0.370370, 0.733333 (2000) | -0.036991 | -0.215633, 0.143603 (2000) |
| G1:security_missing / adverse20 [small sample] | 0.250000 | 24 / 24 | 6 | 0.079923, 0.437500 (2000) | 0.150015 | -0.020920, 0.335806 (2000) |
| G1:security_missing / stop_gap [small sample] | 0.125000 | 24 / 24 | 6 | 0.000000, 0.269318 (2000) | 0.085921 | -0.039178, 0.230447 (2000) |
| G1:security_missing / entry_gap | 0.000000 | 30 / 30 | 0 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G1:security_missing / mae_decision [small sample] | 0.138969 | 24 / 24 | 6 | 0.092798, 0.187440 (2000) | 0.041972 | -0.003950, 0.090937 (2000) |
| G1:security_missing / mae_fill [small sample] | 0.165184 | 24 / 24 | 6 | 0.114218, 0.218603 (2000) | 0.062876 | 0.012367, 0.116548 (2000) |
| G1:security_missing / locked_rate [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G2 / signed_return_90d | -0.010430 | 97 / 97 | 1 | -0.091206, 0.070074 (2000) | 0.010906 | -0.070332, 0.090738 (2000) |
| G2 / collapse | 0.505155 | 97 / 97 | 1 | 0.407747, 0.606742 (2000) | -0.083561 | -0.181278, 0.013799 (2000) |
| G2 / adverse20 | 0.144330 | 97 / 97 | 1 | 0.075467, 0.220000 (2000) | 0.044345 | -0.022167, 0.115151 (2000) |
| G2 / stop_gap | 0.041237 | 97 / 97 | 1 | 0.009091, 0.085714 (2000) | 0.002158 | -0.032797, 0.048208 (2000) |
| G2 / entry_gap | 0.000000 | 97 / 97 | 1 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G2 / mae_decision | 0.103010 | 97 / 97 | 1 | 0.085802, 0.121667 (2000) | 0.006014 | -0.010720, 0.023690 (2000) |
| G2 / mae_fill | 0.110434 | 97 / 97 | 1 | 0.092652, 0.129091 (2000) | 0.008126 | -0.008391, 0.026095 (2000) |
| G2 / locked_rate [small sample] | unavailable | 0 / 0 | 98 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_delivery / signed_return_90d | -0.010430 | 97 / 97 | 1 | -0.091206, 0.070074 (2000) | 0.010906 | -0.070332, 0.090738 (2000) |
| G2:required_dimension_delivery / collapse | 0.505155 | 97 / 97 | 1 | 0.407747, 0.606742 (2000) | -0.083561 | -0.181278, 0.013799 (2000) |
| G2:required_dimension_delivery / adverse20 | 0.144330 | 97 / 97 | 1 | 0.075467, 0.220000 (2000) | 0.044345 | -0.022167, 0.115151 (2000) |
| G2:required_dimension_delivery / stop_gap | 0.041237 | 97 / 97 | 1 | 0.009091, 0.085714 (2000) | 0.002158 | -0.032797, 0.048208 (2000) |
| G2:required_dimension_delivery / entry_gap | 0.000000 | 97 / 97 | 1 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G2:required_dimension_delivery / mae_decision | 0.103010 | 97 / 97 | 1 | 0.085802, 0.121667 (2000) | 0.006014 | -0.010720, 0.023690 (2000) |
| G2:required_dimension_delivery / mae_fill | 0.110434 | 97 / 97 | 1 | 0.092652, 0.129091 (2000) | 0.008126 | -0.008391, 0.026095 (2000) |
| G2:required_dimension_delivery / locked_rate [small sample] | unavailable | 0 / 0 | 98 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_price / signed_return_90d | 0.011133 | 94 / 94 | 1 | -0.045842, 0.068567 (2000) | 0.032470 | -0.025066, 0.089263 (2000) |
| G2:required_dimension_price / collapse | 0.500000 | 94 / 94 | 1 | 0.400000, 0.602201 (2000) | -0.088715 | -0.187111, 0.011587 (2000) |
| G2:required_dimension_price / adverse20 | 0.127660 | 94 / 94 | 1 | 0.064499, 0.197802 (2000) | 0.027675 | -0.036438, 0.094927 (2000) |
| G2:required_dimension_price / stop_gap | 0.042553 | 94 / 94 | 1 | 0.009344, 0.088496 (2000) | 0.003474 | -0.032249, 0.051186 (2000) |
| G2:required_dimension_price / entry_gap | 0.000000 | 94 / 94 | 1 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G2:required_dimension_price / mae_decision | 0.097666 | 94 / 94 | 1 | 0.081180, 0.115162 (2000) | 0.000670 | -0.015440, 0.016960 (2000) |
| G2:required_dimension_price / mae_fill | 0.103906 | 94 / 94 | 1 | 0.088237, 0.120658 (2000) | 0.001598 | -0.013212, 0.017322 (2000) |
| G2:required_dimension_price / locked_rate [small sample] | unavailable | 0 / 0 | 95 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_volume / signed_return_90d | 0.011133 | 94 / 94 | 1 | -0.045842, 0.068567 (2000) | 0.032470 | -0.025066, 0.089263 (2000) |
| G2:required_dimension_volume / collapse | 0.500000 | 94 / 94 | 1 | 0.400000, 0.602201 (2000) | -0.088715 | -0.187111, 0.011587 (2000) |
| G2:required_dimension_volume / adverse20 | 0.127660 | 94 / 94 | 1 | 0.064499, 0.197802 (2000) | 0.027675 | -0.036438, 0.094927 (2000) |
| G2:required_dimension_volume / stop_gap | 0.042553 | 94 / 94 | 1 | 0.009344, 0.088496 (2000) | 0.003474 | -0.032249, 0.051186 (2000) |
| G2:required_dimension_volume / entry_gap | 0.000000 | 94 / 94 | 1 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G2:required_dimension_volume / mae_decision | 0.097666 | 94 / 94 | 1 | 0.081180, 0.115162 (2000) | 0.000670 | -0.015440, 0.016960 (2000) |
| G2:required_dimension_volume / mae_fill | 0.103906 | 94 / 94 | 1 | 0.088237, 0.120658 (2000) | 0.001598 | -0.013212, 0.017322 (2000) |
| G2:required_dimension_volume / locked_rate [small sample] | unavailable | 0 / 0 | 95 | unavailable (0) | unavailable | unavailable (0) |
| G3 / signed_return_90d | 0.049438 | 141 / 141 | 2 | -0.003185, 0.106458 (2000) | 0.070774 | 0.018813, 0.128416 (2000) |
| G3 / collapse | 0.496454 | 141 / 141 | 2 | 0.414279, 0.577183 (2000) | -0.092261 | -0.176716, -0.011719 (2000) |
| G3 / adverse20 | 0.170213 | 141 / 141 | 2 | 0.110294, 0.230795 (2000) | 0.070228 | 0.009526, 0.132766 (2000) |
| G3 / stop_gap | 0.085106 | 141 / 141 | 2 | 0.040541, 0.131397 (2000) | 0.046027 | 0.001527, 0.091336 (2000) |
| G3 / entry_gap | 0.000000 | 143 / 143 | 0 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G3 / mae_decision | 0.117780 | 141 / 141 | 2 | 0.101219, 0.134943 (2000) | 0.020784 | 0.003970, 0.038515 (2000) |
| G3 / mae_fill | 0.124647 | 141 / 141 | 2 | 0.108547, 0.140469 (2000) | 0.022339 | 0.006196, 0.038807 (2000) |
| G3 / locked_rate [small sample] | unavailable | 0 / 0 | 143 | unavailable (0) | unavailable | unavailable (0) |
| G3:structural_break / signed_return_90d | 0.049438 | 141 / 141 | 2 | -0.003185, 0.106458 (2000) | 0.070774 | 0.018813, 0.128416 (2000) |
| G3:structural_break / collapse | 0.496454 | 141 / 141 | 2 | 0.414279, 0.577183 (2000) | -0.092261 | -0.176716, -0.011719 (2000) |
| G3:structural_break / adverse20 | 0.170213 | 141 / 141 | 2 | 0.110294, 0.230795 (2000) | 0.070228 | 0.009526, 0.132766 (2000) |
| G3:structural_break / stop_gap | 0.085106 | 141 / 141 | 2 | 0.040541, 0.131397 (2000) | 0.046027 | 0.001527, 0.091336 (2000) |
| G3:structural_break / entry_gap | 0.000000 | 143 / 143 | 0 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G3:structural_break / mae_decision | 0.117780 | 141 / 141 | 2 | 0.101219, 0.134943 (2000) | 0.020784 | 0.003970, 0.038515 (2000) |
| G3:structural_break / mae_fill | 0.124647 | 141 / 141 | 2 | 0.108547, 0.140469 (2000) | 0.022339 | 0.006196, 0.038807 (2000) |
| G3:structural_break / locked_rate [small sample] | unavailable | 0 / 0 | 143 | unavailable (0) | unavailable | unavailable (0) |
| G4 / signed_return_90d | -0.034772 | 3136 / 3136 | 45 | -0.045932, -0.023902 (2000) | -0.013436 | -0.024928, -0.002254 (2000) |
| G4 / collapse | 0.596939 | 3136 / 3136 | 45 | 0.576034, 0.617397 (2000) | 0.008224 | -0.011350, 0.028311 (2000) |
| G4 / adverse20 | 0.190990 | 3152 / 3152 | 29 | 0.174385, 0.209824 (2000) | 0.091005 | 0.073193, 0.108050 (2000) |
| G4 / stop_gap | 0.073921 | 3152 / 3152 | 29 | 0.064077, 0.084333 (2000) | 0.034842 | 0.024905, 0.045281 (2000) |
| G4 / entry_gap | 0.002205 | 3174 / 3174 | 7 | 0.000913, 0.003990 (2000) | -0.000493 | -0.002876, 0.001531 (2000) |
| G4 / mae_decision | 0.126055 | 3152 / 3152 | 29 | 0.121049, 0.131374 (2000) | 0.029059 | 0.024522, 0.033453 (2000) |
| G4 / mae_fill | 0.139451 | 3152 / 3152 | 29 | 0.134364, 0.144857 (2000) | 0.037143 | 0.032780, 0.041666 (2000) |
| G4 / locked_rate [small sample] | unavailable | 0 / 0 | 3181 | unavailable (0) | unavailable | unavailable (0) |
| G4:ASM / signed_return_90d | -0.034492 | 3127 / 3127 | 45 | -0.045688, -0.023562 (2000) | -0.013155 | -0.024614, -0.001956 (2000) |
| G4:ASM / collapse | 0.596418 | 3127 / 3127 | 45 | 0.575684, 0.616939 (2000) | 0.007703 | -0.012221, 0.027871 (2000) |
| G4:ASM / adverse20 | 0.190915 | 3148 / 3148 | 24 | 0.174349, 0.209845 (2000) | 0.090930 | 0.073149, 0.108039 (2000) |
| G4:ASM / stop_gap | 0.074015 | 3148 / 3148 | 24 | 0.064150, 0.084415 (2000) | 0.034936 | 0.025035, 0.045382 (2000) |
| G4:ASM / entry_gap | 0.002212 | 3165 / 3165 | 7 | 0.000917, 0.004006 (2000) | -0.000487 | -0.002867, 0.001539 (2000) |
| G4:ASM / mae_decision | 0.126062 | 3148 / 3148 | 24 | 0.121011, 0.131404 (2000) | 0.029066 | 0.024508, 0.033485 (2000) |
| G4:ASM / mae_fill | 0.139426 | 3148 / 3148 | 24 | 0.134329, 0.144831 (2000) | 0.037118 | 0.032724, 0.041625 (2000) |
| G4:ASM / locked_rate [small sample] | unavailable | 0 / 0 | 3172 | unavailable (0) | unavailable | unavailable (0) |
| G4:GSM / signed_return_90d [small sample] | -0.132269 | 9 / 9 | 0 | -0.230099, -0.031760 (2000) | -0.110932 | -0.209551, -0.011318 (2000) |
| G4:GSM / collapse [small sample] | 0.777778 | 9 / 9 | 0 | 0.499038, 1.000000 (2000) | 0.189063 | -0.100626, 0.416246 (2000) |
| G4:GSM / adverse20 [small sample] | 0.250000 | 4 / 4 | 5 | 0.000000, 1.000000 (1966) | 0.150015 | -0.111311, 0.891097 (1966) |
| G4:GSM / stop_gap [small sample] | 0.000000 | 4 / 4 | 5 | 0.000000, 0.000000 (1966) | -0.039079 | -0.044281, -0.034683 (1966) |
| G4:GSM / entry_gap [small sample] | 0.000000 | 9 / 9 | 0 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G4:GSM / mae_decision [small sample] | 0.120905 | 4 / 4 | 5 | 0.069841, 0.213514 (1966) | 0.023909 | -0.026455, 0.113155 (1966) |
| G4:GSM / mae_fill [small sample] | 0.159566 | 4 / 4 | 5 | 0.095689, 0.269011 (1966) | 0.057258 | -0.003325, 0.163610 (1966) |
| G4:GSM / locked_rate [small sample] | unavailable | 0 / 0 | 9 | unavailable (0) | unavailable | unavailable (0) |
| G5 / signed_return_90d | -0.033702 | 12080 / 12080 | 155 | -0.039678, -0.027123 (2000) | -0.012366 | -0.019443, -0.004919 (2000) |
| G5 / collapse | 0.637417 | 12080 / 12080 | 155 | 0.624797, 0.648672 (2000) | 0.048702 | 0.036248, 0.060929 (2000) |
| G5 / adverse20 | 0.157908 | 12083 / 12083 | 152 | 0.140559, 0.179236 (2000) | 0.057923 | 0.047978, 0.068401 (2000) |
| G5 / stop_gap | 0.056608 | 12083 / 12083 | 152 | 0.051885, 0.061919 (2000) | 0.017529 | 0.012507, 0.022690 (2000) |
| G5 / entry_gap | 0.000901 | 12210 / 12210 | 25 | 0.000083, 0.002249 (2000) | -0.001798 | -0.003518, -0.000502 (2000) |
| G5 / mae_decision | 0.118201 | 12083 / 12083 | 152 | 0.113049, 0.124606 (2000) | 0.021205 | 0.018044, 0.024511 (2000) |
| G5 / mae_fill | 0.137747 | 12083 / 12083 | 152 | 0.133129, 0.143231 (2000) | 0.035439 | 0.032304, 0.038753 (2000) |
| G5 / locked_rate [small sample] | unavailable | 0 / 0 | 12235 | unavailable (0) | unavailable | unavailable (0) |
| G5:order_ADV_cap / signed_return_90d | -0.033702 | 12080 / 12080 | 155 | -0.039678, -0.027123 (2000) | -0.012366 | -0.019443, -0.004919 (2000) |
| G5:order_ADV_cap / collapse | 0.637417 | 12080 / 12080 | 155 | 0.624797, 0.648672 (2000) | 0.048702 | 0.036248, 0.060929 (2000) |
| G5:order_ADV_cap / adverse20 | 0.157908 | 12083 / 12083 | 152 | 0.140559, 0.179236 (2000) | 0.057923 | 0.047978, 0.068401 (2000) |
| G5:order_ADV_cap / stop_gap | 0.056608 | 12083 / 12083 | 152 | 0.051885, 0.061919 (2000) | 0.017529 | 0.012507, 0.022690 (2000) |
| G5:order_ADV_cap / entry_gap | 0.000901 | 12210 / 12210 | 25 | 0.000083, 0.002249 (2000) | -0.001798 | -0.003518, -0.000502 (2000) |
| G5:order_ADV_cap / mae_decision | 0.118201 | 12083 / 12083 | 152 | 0.113049, 0.124606 (2000) | 0.021205 | 0.018044, 0.024511 (2000) |
| G5:order_ADV_cap / mae_fill | 0.137747 | 12083 / 12083 | 152 | 0.133129, 0.143231 (2000) | 0.035439 | 0.032304, 0.038753 (2000) |
| G5:order_ADV_cap / locked_rate [small sample] | unavailable | 0 / 0 | 12235 | unavailable (0) | unavailable | unavailable (0) |
| G5:stressed_exit_cap / signed_return_90d | -0.025738 | 2426 / 2426 | 29 | -0.040529, -0.009934 (2000) | -0.004401 | -0.019499, 0.011534 (2000) |
| G5:stressed_exit_cap / collapse | 0.636026 | 2426 / 2426 | 29 | 0.613498, 0.658264 (2000) | 0.047311 | 0.024441, 0.070454 (2000) |
| G5:stressed_exit_cap / adverse20 | 0.182239 | 2376 / 2376 | 79 | 0.156813, 0.208782 (2000) | 0.082254 | 0.060803, 0.105624 (2000) |
| G5:stressed_exit_cap / stop_gap | 0.077441 | 2376 / 2376 | 79 | 0.066782, 0.088450 (2000) | 0.038362 | 0.026969, 0.049544 (2000) |
| G5:stressed_exit_cap / entry_gap | 0.001224 | 2451 / 2451 | 4 | 0.000000, 0.002806 (2000) | -0.001475 | -0.003667, 0.000485 (2000) |
| G5:stressed_exit_cap / mae_decision | 0.120558 | 2376 / 2376 | 79 | 0.113195, 0.128626 (2000) | 0.023562 | 0.017079, 0.030290 (2000) |
| G5:stressed_exit_cap / mae_fill | 0.151595 | 2376 / 2376 | 79 | 0.144724, 0.158813 (2000) | 0.049287 | 0.043229, 0.055761 (2000) |
| G5:stressed_exit_cap / locked_rate [small sample] | unavailable | 0 / 0 | 2455 | unavailable (0) | unavailable | unavailable (0) |
| G6 / signed_return_90d | 0.014043 | 65 / 65 | 0 | -0.077147, 0.117997 (2000) | 0.035380 | -0.055458, 0.139402 (2000) |
| G6 / collapse | 0.630769 | 65 / 65 | 0 | 0.508190, 0.742867 (2000) | 0.042054 | -0.083027, 0.155550 (2000) |
| G6 / adverse20 | 0.265625 | 64 / 64 | 1 | 0.161753, 0.372888 (2000) | 0.165640 | 0.061581, 0.270972 (2000) |
| G6 / stop_gap | 0.156250 | 64 / 64 | 1 | 0.069432, 0.250000 (2000) | 0.117171 | 0.030486, 0.211546 (2000) |
| G6 / entry_gap | 0.000000 | 65 / 65 | 0 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G6 / mae_decision | 0.133402 | 64 / 64 | 1 | 0.108251, 0.157363 (2000) | 0.036406 | 0.011263, 0.060440 (2000) |
| G6 / mae_fill | 0.159546 | 64 / 64 | 1 | 0.136302, 0.182136 (2000) | 0.057238 | 0.034323, 0.080173 (2000) |
| G6 / locked_rate [small sample] | unavailable | 0 / 0 | 65 | unavailable (0) | unavailable | unavailable (0) |
| G6:open_risk_cap / signed_return_90d | 0.014043 | 65 / 65 | 0 | -0.077147, 0.117997 (2000) | 0.035380 | -0.055458, 0.139402 (2000) |
| G6:open_risk_cap / collapse | 0.630769 | 65 / 65 | 0 | 0.508190, 0.742867 (2000) | 0.042054 | -0.083027, 0.155550 (2000) |
| G6:open_risk_cap / adverse20 | 0.265625 | 64 / 64 | 1 | 0.161753, 0.372888 (2000) | 0.165640 | 0.061581, 0.270972 (2000) |
| G6:open_risk_cap / stop_gap | 0.156250 | 64 / 64 | 1 | 0.069432, 0.250000 (2000) | 0.117171 | 0.030486, 0.211546 (2000) |
| G6:open_risk_cap / entry_gap | 0.000000 | 65 / 65 | 0 | 0.000000, 0.000000 (2000) | -0.002699 | -0.005650, -0.000909 (2000) |
| G6:open_risk_cap / mae_decision | 0.133402 | 64 / 64 | 1 | 0.108251, 0.157363 (2000) | 0.036406 | 0.011263, 0.060440 (2000) |
| G6:open_risk_cap / mae_fill | 0.159546 | 64 / 64 | 1 | 0.136302, 0.182136 (2000) | 0.057238 | 0.034323, 0.080173 (2000) |
| G6:open_risk_cap / locked_rate [small sample] | unavailable | 0 / 0 | 65 | unavailable (0) | unavailable | unavailable (0) |
| SCREEN_FAIL / signed_return_90d | -0.031562 | 14605 / 14605 | 193 | -0.037209, -0.025566 (2000) | -0.010226 | -0.017022, -0.003499 (2000) |
| SCREEN_FAIL / collapse | 0.625539 | 14605 / 14605 | 193 | 0.613907, 0.636371 (2000) | 0.036824 | 0.025342, 0.048327 (2000) |
| SCREEN_FAIL / adverse20 | 0.160563 | 14636 / 14636 | 162 | 0.144633, 0.179295 (2000) | 0.060578 | 0.051531, 0.069353 (2000) |
| SCREEN_FAIL / stop_gap | 0.057051 | 14636 / 14636 | 162 | 0.052600, 0.062090 (2000) | 0.017972 | 0.013341, 0.022700 (2000) |
| SCREEN_FAIL / entry_gap | 0.001219 | 14769 / 14769 | 29 | 0.000405, 0.002532 (2000) | -0.001480 | -0.003186, -0.000216 (2000) |
| SCREEN_FAIL / mae_decision | 0.118366 | 14636 / 14636 | 162 | 0.113687, 0.124228 (2000) | 0.021370 | 0.018567, 0.024225 (2000) |
| SCREEN_FAIL / mae_fill | 0.136177 | 14636 / 14636 | 162 | 0.131836, 0.141211 (2000) | 0.033869 | 0.031196, 0.036579 (2000) |
| SCREEN_FAIL / locked_rate [small sample] | unavailable | 0 / 0 | 14798 | unavailable (0) | unavailable | unavailable (0) |

## Descriptive 2026

### All candidates

| Group | Events | Dates | NO_FILL | Zero size | Invalid | Incomplete 20 | Missing 90 | Band covered / unknown | Warning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SCREEN_PASS | 7133 | 172 | 2 | 0 | 0 | 307 | 2720 | 0 / 142660 |  |
| G1 | 15 | 13 | 6 | 6 | 6 | 9 | 3 | 0 / 300 | small sample |
| G1:security_missing | 15 | 13 | 6 | 6 | 6 | 9 | 3 | 0 / 300 | small sample |
| G2 | 17 | 13 | 11 | 11 | 11 | 11 | 4 | 0 / 340 | small sample |
| G2:required_dimension_delivery | 17 | 13 | 11 | 11 | 11 | 11 | 4 | 0 / 340 | small sample |
| G2:required_dimension_price | 17 | 13 | 11 | 11 | 11 | 11 | 4 | 0 / 340 | small sample |
| G2:required_dimension_volume | 17 | 13 | 11 | 11 | 11 | 11 | 4 | 0 / 340 | small sample |
| G3 | 41 | 36 | 18 | 18 | 18 | 21 | 25 | 0 / 820 |  |
| G3:structural_break | 41 | 36 | 18 | 18 | 18 | 21 | 25 | 0 / 820 |  |
| G4 | 380 | 149 | 4 | 4 | 4 | 45 | 214 | 0 / 7600 |  |
| G4:ASM | 368 | 147 | 4 | 4 | 4 | 45 | 211 | 0 / 7360 |  |
| G4:GSM | 16 | 15 | 0 | 0 | 0 | 0 | 5 | 0 / 320 | small sample |
| G5 | 2258 | 172 | 34 | 33 | 30 | 196 | 827 | 0 / 45160 |  |
| G5:no_plan | 30 | 26 | 30 | 30 | 30 | 30 | 19 | 0 / 600 |  |
| G5:order_ADV_cap | 2225 | 172 | 1 | 0 | 0 | 166 | 807 | 0 / 44500 |  |
| G5:stressed_exit_cap | 495 | 152 | 0 | 0 | 0 | 56 | 195 | 0 / 9900 |  |
| G5:unknown_coverage | 3 | 3 | 3 | 3 | 0 | 0 | 1 | 0 / 60 | small sample |
| G6 | 58 | 49 | 33 | 33 | 30 | 32 | 39 | 0 / 1160 |  |
| G6:no_plan | 30 | 26 | 30 | 30 | 30 | 30 | 19 | 0 / 600 |  |
| G6:open_risk_cap | 25 | 25 | 0 | 0 | 0 | 2 | 19 | 0 / 500 | small sample |
| G6:unknown_coverage | 3 | 3 | 3 | 3 | 0 | 0 | 1 | 0 / 60 | small sample |
| SCREEN_FAIL | 2535 | 172 | 34 | 33 | 30 | 222 | 982 | 0 / 50700 |  |

| Group / statistic | Estimate | n events / denominator | Missing events | 95% interval (usable draws) | Difference vs PASS | Difference 95% interval (usable draws) |
|---|---:|---:|---:|---|---:|---|
| SCREEN_PASS / signed_return_90d | 0.009993 | 4413 / 4413 | 2720 | -0.000660, 0.020042 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / collapse | 0.522547 | 4413 / 4413 | 2720 | 0.499095, 0.546089 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / adverse20 | 0.077351 | 6826 / 6826 | 307 | 0.063049, 0.092229 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / stop_gap | 0.046880 | 6826 / 6826 | 307 | 0.035386, 0.058641 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / entry_gap | 0.001966 | 7120 / 7120 | 13 | 0.000452, 0.004323 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_decision | 0.093090 | 6826 / 6826 | 307 | 0.085971, 0.100254 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_fill | 0.095534 | 6826 / 6826 | 307 | 0.088195, 0.103005 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / locked_rate [small sample] | unavailable | 0 / 0 | 7133 | unavailable (0) | unavailable | unavailable (0) |
| G1 / signed_return_90d [small sample] | -0.093560 | 12 / 12 | 3 | -0.198243, 0.013581 (2000) | -0.103553 | -0.208198, 0.005396 (2000) |
| G1 / collapse [small sample] | 0.750000 | 12 / 12 | 3 | 0.500000, 1.000000 (2000) | 0.227453 | -0.029704, 0.476116 (2000) |
| G1 / adverse20 [small sample] | 0.333333 | 6 / 6 | 9 | 0.000000, 0.666667 (1985) | 0.255982 | -0.083029, 0.603407 (1985) |
| G1 / stop_gap [small sample] | 0.000000 | 6 / 6 | 9 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058566, -0.035396 (1985) |
| G1 / entry_gap [small sample] | 0.000000 | 9 / 9 | 6 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G1 / mae_decision [small sample] | 0.151035 | 6 / 6 | 9 | 0.095898, 0.187902 (1985) | 0.057945 | 0.000535, 0.098124 (1985) |
| G1 / mae_fill [small sample] | 0.176217 | 6 / 6 | 9 | 0.112224, 0.226771 (1985) | 0.080683 | 0.016323, 0.129399 (1985) |
| G1 / locked_rate [small sample] | unavailable | 0 / 0 | 15 | unavailable (0) | unavailable | unavailable (0) |
| G1:security_missing / signed_return_90d [small sample] | -0.093560 | 12 / 12 | 3 | -0.198243, 0.013581 (2000) | -0.103553 | -0.208198, 0.005396 (2000) |
| G1:security_missing / collapse [small sample] | 0.750000 | 12 / 12 | 3 | 0.500000, 1.000000 (2000) | 0.227453 | -0.029704, 0.476116 (2000) |
| G1:security_missing / adverse20 [small sample] | 0.333333 | 6 / 6 | 9 | 0.000000, 0.666667 (1985) | 0.255982 | -0.083029, 0.603407 (1985) |
| G1:security_missing / stop_gap [small sample] | 0.000000 | 6 / 6 | 9 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058566, -0.035396 (1985) |
| G1:security_missing / entry_gap [small sample] | 0.000000 | 9 / 9 | 6 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G1:security_missing / mae_decision [small sample] | 0.151035 | 6 / 6 | 9 | 0.095898, 0.187902 (1985) | 0.057945 | 0.000535, 0.098124 (1985) |
| G1:security_missing / mae_fill [small sample] | 0.176217 | 6 / 6 | 9 | 0.112224, 0.226771 (1985) | 0.080683 | 0.016323, 0.129399 (1985) |
| G1:security_missing / locked_rate [small sample] | unavailable | 0 / 0 | 15 | unavailable (0) | unavailable | unavailable (0) |
| G2 / signed_return_90d [small sample] | 0.102897 | 13 / 13 | 4 | -0.092541, 0.285221 (2000) | 0.092904 | -0.099429, 0.276887 (2000) |
| G2 / collapse [small sample] | 0.461538 | 13 / 13 | 4 | 0.200000, 0.727273 (2000) | -0.061009 | -0.326617, 0.204375 (2000) |
| G2 / adverse20 [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.077351 | -0.092244, -0.063049 (1985) |
| G2 / stop_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058659, -0.035350 (1985) |
| G2 / entry_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.001966 | -0.004324, -0.000451 (1985) |
| G2 / mae_decision [small sample] | 0.061875 | 6 / 6 | 11 | 0.015747, 0.135075 (1985) | -0.031215 | -0.075644, 0.039942 (1985) |
| G2 / mae_fill [small sample] | 0.061087 | 6 / 6 | 11 | 0.019049, 0.137909 (1985) | -0.034447 | -0.075555, 0.042791 (1985) |
| G2 / locked_rate [small sample] | unavailable | 0 / 0 | 17 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_delivery / signed_return_90d [small sample] | 0.102897 | 13 / 13 | 4 | -0.092541, 0.285221 (2000) | 0.092904 | -0.099429, 0.276887 (2000) |
| G2:required_dimension_delivery / collapse [small sample] | 0.461538 | 13 / 13 | 4 | 0.200000, 0.727273 (2000) | -0.061009 | -0.326617, 0.204375 (2000) |
| G2:required_dimension_delivery / adverse20 [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.077351 | -0.092244, -0.063049 (1985) |
| G2:required_dimension_delivery / stop_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058659, -0.035350 (1985) |
| G2:required_dimension_delivery / entry_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.001966 | -0.004324, -0.000451 (1985) |
| G2:required_dimension_delivery / mae_decision [small sample] | 0.061875 | 6 / 6 | 11 | 0.015747, 0.135075 (1985) | -0.031215 | -0.075644, 0.039942 (1985) |
| G2:required_dimension_delivery / mae_fill [small sample] | 0.061087 | 6 / 6 | 11 | 0.019049, 0.137909 (1985) | -0.034447 | -0.075555, 0.042791 (1985) |
| G2:required_dimension_delivery / locked_rate [small sample] | unavailable | 0 / 0 | 17 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_price / signed_return_90d [small sample] | 0.102897 | 13 / 13 | 4 | -0.092541, 0.285221 (2000) | 0.092904 | -0.099429, 0.276887 (2000) |
| G2:required_dimension_price / collapse [small sample] | 0.461538 | 13 / 13 | 4 | 0.200000, 0.727273 (2000) | -0.061009 | -0.326617, 0.204375 (2000) |
| G2:required_dimension_price / adverse20 [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.077351 | -0.092244, -0.063049 (1985) |
| G2:required_dimension_price / stop_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058659, -0.035350 (1985) |
| G2:required_dimension_price / entry_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.001966 | -0.004324, -0.000451 (1985) |
| G2:required_dimension_price / mae_decision [small sample] | 0.061875 | 6 / 6 | 11 | 0.015747, 0.135075 (1985) | -0.031215 | -0.075644, 0.039942 (1985) |
| G2:required_dimension_price / mae_fill [small sample] | 0.061087 | 6 / 6 | 11 | 0.019049, 0.137909 (1985) | -0.034447 | -0.075555, 0.042791 (1985) |
| G2:required_dimension_price / locked_rate [small sample] | unavailable | 0 / 0 | 17 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_volume / signed_return_90d [small sample] | 0.102897 | 13 / 13 | 4 | -0.092541, 0.285221 (2000) | 0.092904 | -0.099429, 0.276887 (2000) |
| G2:required_dimension_volume / collapse [small sample] | 0.461538 | 13 / 13 | 4 | 0.200000, 0.727273 (2000) | -0.061009 | -0.326617, 0.204375 (2000) |
| G2:required_dimension_volume / adverse20 [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.077351 | -0.092244, -0.063049 (1985) |
| G2:required_dimension_volume / stop_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058659, -0.035350 (1985) |
| G2:required_dimension_volume / entry_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.001966 | -0.004324, -0.000451 (1985) |
| G2:required_dimension_volume / mae_decision [small sample] | 0.061875 | 6 / 6 | 11 | 0.015747, 0.135075 (1985) | -0.031215 | -0.075644, 0.039942 (1985) |
| G2:required_dimension_volume / mae_fill [small sample] | 0.061087 | 6 / 6 | 11 | 0.019049, 0.137909 (1985) | -0.034447 | -0.075555, 0.042791 (1985) |
| G2:required_dimension_volume / locked_rate [small sample] | unavailable | 0 / 0 | 17 | unavailable (0) | unavailable | unavailable (0) |
| G3 / signed_return_90d [small sample] | 0.009794 | 16 / 16 | 25 | -0.145893, 0.227483 (2000) | -0.000198 | -0.158163, 0.217715 (2000) |
| G3 / collapse [small sample] | 0.562500 | 16 / 16 | 25 | 0.300000, 0.800000 (2000) | 0.039953 | -0.221814, 0.283510 (2000) |
| G3 / adverse20 [small sample] | 0.200000 | 20 / 20 | 21 | 0.000000, 0.434851 (2000) | 0.122649 | -0.074405, 0.358873 (2000) |
| G3 / stop_gap [small sample] | 0.000000 | 20 / 20 | 21 | 0.000000, 0.000000 (2000) | -0.046880 | -0.058641, -0.035386 (2000) |
| G3 / entry_gap [small sample] | 0.000000 | 21 / 21 | 20 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G3 / mae_decision [small sample] | 0.094681 | 20 / 20 | 21 | 0.040926, 0.158532 (2000) | 0.001591 | -0.052955, 0.066187 (2000) |
| G3 / mae_fill [small sample] | 0.119633 | 20 / 20 | 21 | 0.067975, 0.178833 (2000) | 0.024099 | -0.029011, 0.081981 (2000) |
| G3 / locked_rate [small sample] | unavailable | 0 / 0 | 41 | unavailable (0) | unavailable | unavailable (0) |
| G3:structural_break / signed_return_90d [small sample] | 0.009794 | 16 / 16 | 25 | -0.145893, 0.227483 (2000) | -0.000198 | -0.158163, 0.217715 (2000) |
| G3:structural_break / collapse [small sample] | 0.562500 | 16 / 16 | 25 | 0.300000, 0.800000 (2000) | 0.039953 | -0.221814, 0.283510 (2000) |
| G3:structural_break / adverse20 [small sample] | 0.200000 | 20 / 20 | 21 | 0.000000, 0.434851 (2000) | 0.122649 | -0.074405, 0.358873 (2000) |
| G3:structural_break / stop_gap [small sample] | 0.000000 | 20 / 20 | 21 | 0.000000, 0.000000 (2000) | -0.046880 | -0.058641, -0.035386 (2000) |
| G3:structural_break / entry_gap [small sample] | 0.000000 | 21 / 21 | 20 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G3:structural_break / mae_decision [small sample] | 0.094681 | 20 / 20 | 21 | 0.040926, 0.158532 (2000) | 0.001591 | -0.052955, 0.066187 (2000) |
| G3:structural_break / mae_fill [small sample] | 0.119633 | 20 / 20 | 21 | 0.067975, 0.178833 (2000) | 0.024099 | -0.029011, 0.081981 (2000) |
| G3:structural_break / locked_rate [small sample] | unavailable | 0 / 0 | 41 | unavailable (0) | unavailable | unavailable (0) |
| G4 / signed_return_90d | -0.058868 | 166 / 166 | 214 | -0.121200, 0.017743 (2000) | -0.068861 | -0.128047, 0.002924 (2000) |
| G4 / collapse | 0.656627 | 166 / 166 | 214 | 0.582845, 0.726190 (2000) | 0.134079 | 0.059293, 0.203486 (2000) |
| G4 / adverse20 | 0.158209 | 335 / 335 | 45 | 0.117647, 0.205500 (2000) | 0.080858 | 0.041079, 0.125093 (2000) |
| G4 / stop_gap | 0.053731 | 335 / 335 | 45 | 0.030483, 0.079577 (2000) | 0.006852 | -0.018671, 0.034607 (2000) |
| G4 / entry_gap | 0.002681 | 373 / 373 | 7 | 0.000000, 0.008571 (2000) | 0.000715 | -0.003681, 0.007071 (2000) |
| G4 / mae_decision | 0.119816 | 335 / 335 | 45 | 0.110846, 0.130034 (2000) | 0.026726 | 0.016812, 0.036807 (2000) |
| G4 / mae_fill | 0.130498 | 335 / 335 | 45 | 0.121342, 0.141090 (2000) | 0.034964 | 0.024140, 0.045810 (2000) |
| G4 / locked_rate [small sample] | unavailable | 0 / 0 | 380 | unavailable (0) | unavailable | unavailable (0) |
| G4:ASM / signed_return_90d | -0.053965 | 157 / 157 | 211 | -0.119980, 0.025541 (2000) | -0.063958 | -0.126348, 0.010756 (2000) |
| G4:ASM / collapse | 0.649682 | 157 / 157 | 211 | 0.576268, 0.720783 (2000) | 0.127135 | 0.053097, 0.198870 (2000) |
| G4:ASM / adverse20 | 0.160991 | 323 / 323 | 45 | 0.119559, 0.209465 (2000) | 0.083639 | 0.042921, 0.129462 (2000) |
| G4:ASM / stop_gap | 0.055728 | 323 / 323 | 45 | 0.031746, 0.082508 (2000) | 0.008848 | -0.017574, 0.037338 (2000) |
| G4:ASM / entry_gap | 0.002770 | 361 / 361 | 7 | 0.000000, 0.008929 (2000) | 0.000804 | -0.003681, 0.007388 (2000) |
| G4:ASM / mae_decision | 0.119275 | 323 / 323 | 45 | 0.110120, 0.129809 (2000) | 0.026185 | 0.016227, 0.036750 (2000) |
| G4:ASM / mae_fill | 0.129051 | 323 / 323 | 45 | 0.119673, 0.139701 (2000) | 0.033517 | 0.022727, 0.044313 (2000) |
| G4:ASM / locked_rate [small sample] | unavailable | 0 / 0 | 368 | unavailable (0) | unavailable | unavailable (0) |
| G4:GSM / signed_return_90d [small sample] | -0.181708 | 11 / 11 | 5 | -0.270548, -0.078682 (2000) | -0.191701 | -0.280555, -0.089655 (2000) |
| G4:GSM / collapse [small sample] | 0.818182 | 11 / 11 | 5 | 0.500000, 1.000000 (2000) | 0.295635 | -0.002061, 0.488609 (2000) |
| G4:GSM / adverse20 [small sample] | 0.062500 | 16 / 16 | 0 | 0.000000, 0.200000 (2000) | -0.014851 | -0.088319, 0.122512 (2000) |
| G4:GSM / stop_gap [small sample] | 0.000000 | 16 / 16 | 0 | 0.000000, 0.000000 (2000) | -0.046880 | -0.058641, -0.035386 (2000) |
| G4:GSM / entry_gap [small sample] | 0.000000 | 16 / 16 | 0 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G4:GSM / mae_decision [small sample] | 0.125924 | 16 / 16 | 0 | 0.096908, 0.155183 (2000) | 0.032834 | 0.003331, 0.060831 (2000) |
| G4:GSM / mae_fill [small sample] | 0.158339 | 16 / 16 | 0 | 0.123480, 0.190345 (2000) | 0.062805 | 0.026950, 0.094324 (2000) |
| G4:GSM / locked_rate [small sample] | unavailable | 0 / 0 | 16 | unavailable (0) | unavailable | unavailable (0) |
| G5 / signed_return_90d | -0.045859 | 1431 / 1431 | 827 | -0.062361, -0.029812 (2000) | -0.055851 | -0.074553, -0.036745 (2000) |
| G5 / collapse | 0.622642 | 1431 / 1431 | 827 | 0.574725, 0.670888 (2000) | 0.100094 | 0.060296, 0.138711 (2000) |
| G5 / adverse20 | 0.125121 | 2062 / 2062 | 196 | 0.098641, 0.154353 (2000) | 0.047770 | 0.027290, 0.071340 (2000) |
| G5 / stop_gap | 0.055286 | 2062 / 2062 | 196 | 0.042959, 0.069385 (2000) | 0.008407 | -0.004944, 0.022313 (2000) |
| G5 / entry_gap | 0.001351 | 2220 / 2220 | 38 | 0.000000, 0.003111 (2000) | -0.000615 | -0.002375, 0.001216 (2000) |
| G5 / mae_decision | 0.107676 | 2062 / 2062 | 196 | 0.096763, 0.118762 (2000) | 0.014586 | 0.007600, 0.021448 (2000) |
| G5 / mae_fill | 0.121726 | 2058 / 2058 | 200 | 0.110924, 0.133079 (2000) | 0.026192 | 0.019401, 0.033178 (2000) |
| G5 / locked_rate [small sample] | unavailable | 0 / 0 | 2258 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / signed_return_90d [small sample] | 0.037061 | 11 / 11 | 19 | -0.128804, 0.211483 (2000) | 0.027068 | -0.136285, 0.202656 (2000) |
| G5:no_plan / collapse [small sample] | 0.454545 | 11 / 11 | 19 | 0.166346, 0.727273 (2000) | -0.068002 | -0.363314, 0.206087 (2000) |
| G5:no_plan / adverse20 [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / stop_gap [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / entry_gap [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / mae_decision [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / mae_fill [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / locked_rate [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:order_ADV_cap / signed_return_90d | -0.046516 | 1418 / 1418 | 807 | -0.063005, -0.030817 (2000) | -0.056509 | -0.075194, -0.037671 (2000) |
| G5:order_ADV_cap / collapse | 0.624118 | 1418 / 1418 | 807 | 0.576437, 0.672619 (2000) | 0.101571 | 0.060966, 0.140832 (2000) |
| G5:order_ADV_cap / adverse20 | 0.125304 | 2059 / 2059 | 166 | 0.098642, 0.154509 (2000) | 0.047952 | 0.027403, 0.071488 (2000) |
| G5:order_ADV_cap / stop_gap | 0.054881 | 2059 / 2059 | 166 | 0.042571, 0.068872 (2000) | 0.008001 | -0.005296, 0.021802 (2000) |
| G5:order_ADV_cap / entry_gap | 0.001353 | 2217 / 2217 | 8 | 0.000000, 0.003114 (2000) | -0.000613 | -0.002374, 0.001218 (2000) |
| G5:order_ADV_cap / mae_decision | 0.107789 | 2059 / 2059 | 166 | 0.096893, 0.118815 (2000) | 0.014699 | 0.007667, 0.021615 (2000) |
| G5:order_ADV_cap / mae_fill | 0.121726 | 2058 / 2058 | 167 | 0.110924, 0.133079 (2000) | 0.026192 | 0.019401, 0.033178 (2000) |
| G5:order_ADV_cap / locked_rate [small sample] | unavailable | 0 / 0 | 2225 | unavailable (0) | unavailable | unavailable (0) |
| G5:stressed_exit_cap / signed_return_90d | -0.066275 | 300 / 300 | 195 | -0.091652, -0.040442 (2000) | -0.076268 | -0.102849, -0.049400 (2000) |
| G5:stressed_exit_cap / collapse | 0.670000 | 300 / 300 | 195 | 0.598745, 0.736488 (2000) | 0.147453 | 0.086587, 0.206142 (2000) |
| G5:stressed_exit_cap / adverse20 | 0.166287 | 439 / 439 | 56 | 0.121836, 0.216286 (2000) | 0.088936 | 0.049969, 0.132688 (2000) |
| G5:stressed_exit_cap / stop_gap | 0.045558 | 439 / 439 | 56 | 0.026722, 0.065729 (2000) | -0.001321 | -0.022857, 0.021021 (2000) |
| G5:stressed_exit_cap / entry_gap | 0.000000 | 495 / 495 | 0 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G5:stressed_exit_cap / mae_decision | 0.117533 | 439 / 439 | 56 | 0.105833, 0.129595 (2000) | 0.024443 | 0.015935, 0.033492 (2000) |
| G5:stressed_exit_cap / mae_fill | 0.137509 | 439 / 439 | 56 | 0.126035, 0.149550 (2000) | 0.041975 | 0.033545, 0.050925 (2000) |
| G5:stressed_exit_cap / locked_rate [small sample] | unavailable | 0 / 0 | 495 | unavailable (0) | unavailable | unavailable (0) |
| G5:unknown_coverage / signed_return_90d [small sample] | -0.035617 | 2 / 2 | 1 | -0.178454, 0.107220 (1756) | -0.045610 | -0.195341, 0.103977 (1756) |
| G5:unknown_coverage / collapse [small sample] | 0.500000 | 2 / 2 | 1 | 0.000000, 1.000000 (1756) | -0.022547 | -0.535650, 0.493671 (1756) |
| G5:unknown_coverage / adverse20 [small sample] | 0.000000 | 3 / 3 | 0 | 0.000000, 0.000000 (1912) | -0.077351 | -0.092188, -0.063113 (1912) |
| G5:unknown_coverage / stop_gap [small sample] | 0.333333 | 3 / 3 | 0 | 0.000000, 1.000000 (1912) | 0.286454 | -0.055223, 0.955119 (1912) |
| G5:unknown_coverage / entry_gap [small sample] | 0.000000 | 3 / 3 | 0 | 0.000000, 0.000000 (1912) | -0.001966 | -0.004345, -0.000452 (1912) |
| G5:unknown_coverage / mae_decision [small sample] | 0.029715 | 3 / 3 | 0 | 0.000000, 0.082346 (1912) | -0.063375 | -0.096266, -0.009401 (1912) |
| G5:unknown_coverage / mae_fill [small sample] | unavailable | 0 / 0 | 3 | unavailable (0) | unavailable | unavailable (0) |
| G5:unknown_coverage / locked_rate [small sample] | unavailable | 0 / 0 | 3 | unavailable (0) | unavailable | unavailable (0) |
| G6 / signed_return_90d [small sample] | -0.028560 | 19 / 19 | 39 | -0.129294, 0.073055 (2000) | -0.038553 | -0.137008, 0.059877 (2000) |
| G6 / collapse [small sample] | 0.631579 | 19 / 19 | 39 | 0.444444, 0.823529 (2000) | 0.109032 | -0.075843, 0.294456 (2000) |
| G6 / adverse20 [small sample] | 0.153846 | 26 / 26 | 32 | 0.032258, 0.312500 (2000) | 0.076495 | -0.048081, 0.234934 (2000) |
| G6 / stop_gap [small sample] | 0.076923 | 26 / 26 | 32 | 0.000000, 0.192339 (2000) | 0.030043 | -0.052178, 0.146972 (2000) |
| G6 / entry_gap [small sample] | 0.000000 | 28 / 28 | 30 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G6 / mae_decision [small sample] | 0.108953 | 26 / 26 | 32 | 0.078446, 0.141556 (2000) | 0.015863 | -0.014624, 0.047517 (2000) |
| G6 / mae_fill [small sample] | 0.137134 | 23 / 23 | 35 | 0.103110, 0.176061 (2000) | 0.041600 | 0.007450, 0.078725 (2000) |
| G6 / locked_rate [small sample] | unavailable | 0 / 0 | 58 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / signed_return_90d [small sample] | 0.037061 | 11 / 11 | 19 | -0.128804, 0.211483 (2000) | 0.027068 | -0.136285, 0.202656 (2000) |
| G6:no_plan / collapse [small sample] | 0.454545 | 11 / 11 | 19 | 0.166346, 0.727273 (2000) | -0.068002 | -0.363314, 0.206087 (2000) |
| G6:no_plan / adverse20 [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / stop_gap [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / entry_gap [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / mae_decision [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / mae_fill [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / locked_rate [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:open_risk_cap / signed_return_90d [small sample] | -0.146513 | 6 / 6 | 19 | -0.219321, -0.073234 (1996) | -0.156506 | -0.226464, -0.082169 (1996) |
| G6:open_risk_cap / collapse [small sample] | 1.000000 | 6 / 6 | 19 | 1.000000, 1.000000 (1996) | 0.477453 | 0.453898, 0.500907 (1996) |
| G6:open_risk_cap / adverse20 [small sample] | 0.173913 | 23 / 23 | 2 | 0.038462, 0.352989 (2000) | 0.096562 | -0.043507, 0.271573 (2000) |
| G6:open_risk_cap / stop_gap [small sample] | 0.043478 | 23 / 23 | 2 | 0.000000, 0.148148 (2000) | -0.003401 | -0.055635, 0.097821 (2000) |
| G6:open_risk_cap / entry_gap [small sample] | 0.000000 | 25 / 25 | 0 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G6:open_risk_cap / mae_decision [small sample] | 0.119288 | 23 / 23 | 2 | 0.086820, 0.155294 (2000) | 0.026198 | -0.005131, 0.060706 (2000) |
| G6:open_risk_cap / mae_fill [small sample] | 0.137134 | 23 / 23 | 2 | 0.103110, 0.176061 (2000) | 0.041600 | 0.007450, 0.078725 (2000) |
| G6:open_risk_cap / locked_rate [small sample] | unavailable | 0 / 0 | 25 | unavailable (0) | unavailable | unavailable (0) |
| G6:unknown_coverage / signed_return_90d [small sample] | -0.035617 | 2 / 2 | 1 | -0.178454, 0.107220 (1756) | -0.045610 | -0.195341, 0.103977 (1756) |
| G6:unknown_coverage / collapse [small sample] | 0.500000 | 2 / 2 | 1 | 0.000000, 1.000000 (1756) | -0.022547 | -0.535650, 0.493671 (1756) |
| G6:unknown_coverage / adverse20 [small sample] | 0.000000 | 3 / 3 | 0 | 0.000000, 0.000000 (1912) | -0.077351 | -0.092188, -0.063113 (1912) |
| G6:unknown_coverage / stop_gap [small sample] | 0.333333 | 3 / 3 | 0 | 0.000000, 1.000000 (1912) | 0.286454 | -0.055223, 0.955119 (1912) |
| G6:unknown_coverage / entry_gap [small sample] | 0.000000 | 3 / 3 | 0 | 0.000000, 0.000000 (1912) | -0.001966 | -0.004345, -0.000452 (1912) |
| G6:unknown_coverage / mae_decision [small sample] | 0.029715 | 3 / 3 | 0 | 0.000000, 0.082346 (1912) | -0.063375 | -0.096266, -0.009401 (1912) |
| G6:unknown_coverage / mae_fill [small sample] | unavailable | 0 / 0 | 3 | unavailable (0) | unavailable | unavailable (0) |
| G6:unknown_coverage / locked_rate [small sample] | unavailable | 0 / 0 | 3 | unavailable (0) | unavailable | unavailable (0) |
| SCREEN_FAIL / signed_return_90d | -0.042917 | 1553 / 1553 | 982 | -0.060937, -0.025695 (2000) | -0.052910 | -0.072003, -0.034866 (2000) |
| SCREEN_FAIL / collapse | 0.618802 | 1553 / 1553 | 982 | 0.574669, 0.663380 (2000) | 0.096255 | 0.058510, 0.133964 (2000) |
| SCREEN_FAIL / adverse20 | 0.128837 | 2313 / 2313 | 222 | 0.102877, 0.158095 (2000) | 0.051486 | 0.031265, 0.074481 (2000) |
| SCREEN_FAIL / stop_gap | 0.053178 | 2313 / 2313 | 222 | 0.041782, 0.066075 (2000) | 0.006298 | -0.006440, 0.020140 (2000) |
| SCREEN_FAIL / entry_gap | 0.001603 | 2495 / 2495 | 40 | 0.000376, 0.003307 (2000) | -0.000363 | -0.002294, 0.001583 (2000) |
| SCREEN_FAIL / mae_decision | 0.108430 | 2313 / 2313 | 222 | 0.097881, 0.119042 (2000) | 0.015339 | 0.008893, 0.021820 (2000) |
| SCREEN_FAIL / mae_fill | 0.121737 | 2309 / 2309 | 226 | 0.111502, 0.132263 (2000) | 0.026203 | 0.019735, 0.032700 (2000) |
| SCREEN_FAIL / locked_rate [small sample] | unavailable | 0 / 0 | 2535 | unavailable (0) | unavailable | unavailable (0) |

### Filled only

| Group | Events | Dates | NO_FILL | Zero size | Invalid | Incomplete 20 | Missing 90 | Band covered / unknown | Warning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SCREEN_PASS | 7131 | 172 | 0 | 0 | 0 | 305 | 2718 | 0 / 142620 |  |
| G1 | 9 | 8 | 0 | 0 | 0 | 3 | 3 | 0 / 180 | small sample |
| G1:security_missing | 9 | 8 | 0 | 0 | 0 | 3 | 3 | 0 / 180 | small sample |
| G2 | 6 | 5 | 0 | 0 | 0 | 0 | 3 | 0 / 120 | small sample |
| G2:required_dimension_delivery | 6 | 5 | 0 | 0 | 0 | 0 | 3 | 0 / 120 | small sample |
| G2:required_dimension_price | 6 | 5 | 0 | 0 | 0 | 0 | 3 | 0 / 120 | small sample |
| G2:required_dimension_volume | 6 | 5 | 0 | 0 | 0 | 0 | 3 | 0 / 120 | small sample |
| G3 | 23 | 20 | 0 | 0 | 0 | 3 | 8 | 0 / 460 | small sample |
| G3:structural_break | 23 | 20 | 0 | 0 | 0 | 3 | 8 | 0 / 460 | small sample |
| G4 | 376 | 148 | 0 | 0 | 0 | 41 | 211 | 0 / 7520 |  |
| G4:ASM | 364 | 146 | 0 | 0 | 0 | 41 | 208 | 0 / 7280 |  |
| G4:GSM | 16 | 15 | 0 | 0 | 0 | 0 | 5 | 0 / 320 | small sample |
| G5 | 2224 | 172 | 0 | 0 | 0 | 166 | 807 | 0 / 44480 |  |
| G5:order_ADV_cap | 2224 | 172 | 0 | 0 | 0 | 166 | 807 | 0 / 44480 |  |
| G5:stressed_exit_cap | 495 | 152 | 0 | 0 | 0 | 56 | 195 | 0 / 9900 |  |
| G6 | 25 | 25 | 0 | 0 | 0 | 2 | 19 | 0 / 500 | small sample |
| G6:open_risk_cap | 25 | 25 | 0 | 0 | 0 | 2 | 19 | 0 / 500 | small sample |
| SCREEN_FAIL | 2501 | 172 | 0 | 0 | 0 | 192 | 962 | 0 / 50020 |  |

| Group / statistic | Estimate | n events / denominator | Missing events | 95% interval (usable draws) | Difference vs PASS | Difference 95% interval (usable draws) |
|---|---:|---:|---:|---|---:|---|
| SCREEN_PASS / signed_return_90d | 0.009993 | 4413 / 4413 | 2718 | -0.000660, 0.020042 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / collapse | 0.522547 | 4413 / 4413 | 2718 | 0.499095, 0.546089 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / adverse20 | 0.077351 | 6826 / 6826 | 305 | 0.063049, 0.092229 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / stop_gap | 0.046880 | 6826 / 6826 | 305 | 0.035386, 0.058641 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / entry_gap | 0.001966 | 7120 / 7120 | 11 | 0.000452, 0.004323 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_decision | 0.093090 | 6826 / 6826 | 305 | 0.085971, 0.100254 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_fill | 0.095534 | 6826 / 6826 | 305 | 0.088195, 0.103005 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / locked_rate [small sample] | unavailable | 0 / 0 | 7131 | unavailable (0) | unavailable | unavailable (0) |
| G1 / signed_return_90d [small sample] | -0.099101 | 6 / 6 | 3 | -0.241209, 0.101578 (1985) | -0.109093 | -0.253741, 0.094895 (1985) |
| G1 / collapse [small sample] | 0.833333 | 6 / 6 | 3 | 0.400000, 1.000000 (1985) | 0.310786 | -0.138507, 0.495230 (1985) |
| G1 / adverse20 [small sample] | 0.333333 | 6 / 6 | 3 | 0.000000, 0.666667 (1985) | 0.255982 | -0.083029, 0.603407 (1985) |
| G1 / stop_gap [small sample] | 0.000000 | 6 / 6 | 3 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058566, -0.035396 (1985) |
| G1 / entry_gap [small sample] | 0.000000 | 9 / 9 | 0 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G1 / mae_decision [small sample] | 0.151035 | 6 / 6 | 3 | 0.095898, 0.187902 (1985) | 0.057945 | 0.000535, 0.098124 (1985) |
| G1 / mae_fill [small sample] | 0.176217 | 6 / 6 | 3 | 0.112224, 0.226771 (1985) | 0.080683 | 0.016323, 0.129399 (1985) |
| G1 / locked_rate [small sample] | unavailable | 0 / 0 | 9 | unavailable (0) | unavailable | unavailable (0) |
| G1:security_missing / signed_return_90d [small sample] | -0.099101 | 6 / 6 | 3 | -0.241209, 0.101578 (1985) | -0.109093 | -0.253741, 0.094895 (1985) |
| G1:security_missing / collapse [small sample] | 0.833333 | 6 / 6 | 3 | 0.400000, 1.000000 (1985) | 0.310786 | -0.138507, 0.495230 (1985) |
| G1:security_missing / adverse20 [small sample] | 0.333333 | 6 / 6 | 3 | 0.000000, 0.666667 (1985) | 0.255982 | -0.083029, 0.603407 (1985) |
| G1:security_missing / stop_gap [small sample] | 0.000000 | 6 / 6 | 3 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058566, -0.035396 (1985) |
| G1:security_missing / entry_gap [small sample] | 0.000000 | 9 / 9 | 0 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G1:security_missing / mae_decision [small sample] | 0.151035 | 6 / 6 | 3 | 0.095898, 0.187902 (1985) | 0.057945 | 0.000535, 0.098124 (1985) |
| G1:security_missing / mae_fill [small sample] | 0.176217 | 6 / 6 | 3 | 0.112224, 0.226771 (1985) | 0.080683 | 0.016323, 0.129399 (1985) |
| G1:security_missing / locked_rate [small sample] | unavailable | 0 / 0 | 9 | unavailable (0) | unavailable | unavailable (0) |
| G2 / signed_return_90d [small sample] | 0.323378 | 3 / 3 | 3 | -0.089519, 0.529826 (1724) | 0.313385 | -0.107311, 0.527951 (1724) |
| G2 / collapse [small sample] | 0.333333 | 3 / 3 | 3 | 0.000000, 1.000000 (1724) | -0.189214 | -0.539943, 0.495449 (1724) |
| G2 / adverse20 [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.077351 | -0.092244, -0.063049 (1985) |
| G2 / stop_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058659, -0.035350 (1985) |
| G2 / entry_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.001966 | -0.004324, -0.000451 (1985) |
| G2 / mae_decision [small sample] | 0.061875 | 6 / 6 | 0 | 0.015747, 0.135075 (1985) | -0.031215 | -0.075644, 0.039942 (1985) |
| G2 / mae_fill [small sample] | 0.061087 | 6 / 6 | 0 | 0.019049, 0.137909 (1985) | -0.034447 | -0.075555, 0.042791 (1985) |
| G2 / locked_rate [small sample] | unavailable | 0 / 0 | 6 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_delivery / signed_return_90d [small sample] | 0.323378 | 3 / 3 | 3 | -0.089519, 0.529826 (1724) | 0.313385 | -0.107311, 0.527951 (1724) |
| G2:required_dimension_delivery / collapse [small sample] | 0.333333 | 3 / 3 | 3 | 0.000000, 1.000000 (1724) | -0.189214 | -0.539943, 0.495449 (1724) |
| G2:required_dimension_delivery / adverse20 [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.077351 | -0.092244, -0.063049 (1985) |
| G2:required_dimension_delivery / stop_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058659, -0.035350 (1985) |
| G2:required_dimension_delivery / entry_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.001966 | -0.004324, -0.000451 (1985) |
| G2:required_dimension_delivery / mae_decision [small sample] | 0.061875 | 6 / 6 | 0 | 0.015747, 0.135075 (1985) | -0.031215 | -0.075644, 0.039942 (1985) |
| G2:required_dimension_delivery / mae_fill [small sample] | 0.061087 | 6 / 6 | 0 | 0.019049, 0.137909 (1985) | -0.034447 | -0.075555, 0.042791 (1985) |
| G2:required_dimension_delivery / locked_rate [small sample] | unavailable | 0 / 0 | 6 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_price / signed_return_90d [small sample] | 0.323378 | 3 / 3 | 3 | -0.089519, 0.529826 (1724) | 0.313385 | -0.107311, 0.527951 (1724) |
| G2:required_dimension_price / collapse [small sample] | 0.333333 | 3 / 3 | 3 | 0.000000, 1.000000 (1724) | -0.189214 | -0.539943, 0.495449 (1724) |
| G2:required_dimension_price / adverse20 [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.077351 | -0.092244, -0.063049 (1985) |
| G2:required_dimension_price / stop_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058659, -0.035350 (1985) |
| G2:required_dimension_price / entry_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.001966 | -0.004324, -0.000451 (1985) |
| G2:required_dimension_price / mae_decision [small sample] | 0.061875 | 6 / 6 | 0 | 0.015747, 0.135075 (1985) | -0.031215 | -0.075644, 0.039942 (1985) |
| G2:required_dimension_price / mae_fill [small sample] | 0.061087 | 6 / 6 | 0 | 0.019049, 0.137909 (1985) | -0.034447 | -0.075555, 0.042791 (1985) |
| G2:required_dimension_price / locked_rate [small sample] | unavailable | 0 / 0 | 6 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_volume / signed_return_90d [small sample] | 0.323378 | 3 / 3 | 3 | -0.089519, 0.529826 (1724) | 0.313385 | -0.107311, 0.527951 (1724) |
| G2:required_dimension_volume / collapse [small sample] | 0.333333 | 3 / 3 | 3 | 0.000000, 1.000000 (1724) | -0.189214 | -0.539943, 0.495449 (1724) |
| G2:required_dimension_volume / adverse20 [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.077351 | -0.092244, -0.063049 (1985) |
| G2:required_dimension_volume / stop_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.046880 | -0.058659, -0.035350 (1985) |
| G2:required_dimension_volume / entry_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.001966 | -0.004324, -0.000451 (1985) |
| G2:required_dimension_volume / mae_decision [small sample] | 0.061875 | 6 / 6 | 0 | 0.015747, 0.135075 (1985) | -0.031215 | -0.075644, 0.039942 (1985) |
| G2:required_dimension_volume / mae_fill [small sample] | 0.061087 | 6 / 6 | 0 | 0.019049, 0.137909 (1985) | -0.034447 | -0.075555, 0.042791 (1985) |
| G2:required_dimension_volume / locked_rate [small sample] | unavailable | 0 / 0 | 6 | unavailable (0) | unavailable | unavailable (0) |
| G3 / signed_return_90d [small sample] | 0.007771 | 15 / 15 | 8 | -0.160079, 0.231184 (2000) | -0.002222 | -0.169159, 0.223278 (2000) |
| G3 / collapse [small sample] | 0.600000 | 15 / 15 | 8 | 0.315707, 0.857143 (2000) | 0.077453 | -0.205012, 0.333306 (2000) |
| G3 / adverse20 [small sample] | 0.200000 | 20 / 20 | 3 | 0.000000, 0.434851 (2000) | 0.122649 | -0.074405, 0.358873 (2000) |
| G3 / stop_gap [small sample] | 0.000000 | 20 / 20 | 3 | 0.000000, 0.000000 (2000) | -0.046880 | -0.058641, -0.035386 (2000) |
| G3 / entry_gap [small sample] | 0.000000 | 21 / 21 | 2 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G3 / mae_decision [small sample] | 0.094681 | 20 / 20 | 3 | 0.040926, 0.158532 (2000) | 0.001591 | -0.052955, 0.066187 (2000) |
| G3 / mae_fill [small sample] | 0.119633 | 20 / 20 | 3 | 0.067975, 0.178833 (2000) | 0.024099 | -0.029011, 0.081981 (2000) |
| G3 / locked_rate [small sample] | unavailable | 0 / 0 | 23 | unavailable (0) | unavailable | unavailable (0) |
| G3:structural_break / signed_return_90d [small sample] | 0.007771 | 15 / 15 | 8 | -0.160079, 0.231184 (2000) | -0.002222 | -0.169159, 0.223278 (2000) |
| G3:structural_break / collapse [small sample] | 0.600000 | 15 / 15 | 8 | 0.315707, 0.857143 (2000) | 0.077453 | -0.205012, 0.333306 (2000) |
| G3:structural_break / adverse20 [small sample] | 0.200000 | 20 / 20 | 3 | 0.000000, 0.434851 (2000) | 0.122649 | -0.074405, 0.358873 (2000) |
| G3:structural_break / stop_gap [small sample] | 0.000000 | 20 / 20 | 3 | 0.000000, 0.000000 (2000) | -0.046880 | -0.058641, -0.035386 (2000) |
| G3:structural_break / entry_gap [small sample] | 0.000000 | 21 / 21 | 2 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G3:structural_break / mae_decision [small sample] | 0.094681 | 20 / 20 | 3 | 0.040926, 0.158532 (2000) | 0.001591 | -0.052955, 0.066187 (2000) |
| G3:structural_break / mae_fill [small sample] | 0.119633 | 20 / 20 | 3 | 0.067975, 0.178833 (2000) | 0.024099 | -0.029011, 0.081981 (2000) |
| G3:structural_break / locked_rate [small sample] | unavailable | 0 / 0 | 23 | unavailable (0) | unavailable | unavailable (0) |
| G4 / signed_return_90d | -0.058575 | 165 / 165 | 211 | -0.121287, 0.018912 (2000) | -0.068567 | -0.128049, 0.004330 (2000) |
| G4 / collapse | 0.654545 | 165 / 165 | 211 | 0.580626, 0.724364 (2000) | 0.131998 | 0.055848, 0.202283 (2000) |
| G4 / adverse20 | 0.158209 | 335 / 335 | 41 | 0.117647, 0.205500 (2000) | 0.080858 | 0.041079, 0.125093 (2000) |
| G4 / stop_gap | 0.053731 | 335 / 335 | 41 | 0.030483, 0.079577 (2000) | 0.006852 | -0.018671, 0.034607 (2000) |
| G4 / entry_gap | 0.002681 | 373 / 373 | 3 | 0.000000, 0.008571 (2000) | 0.000715 | -0.003681, 0.007071 (2000) |
| G4 / mae_decision | 0.119816 | 335 / 335 | 41 | 0.110846, 0.130034 (2000) | 0.026726 | 0.016812, 0.036807 (2000) |
| G4 / mae_fill | 0.130498 | 335 / 335 | 41 | 0.121342, 0.141090 (2000) | 0.034964 | 0.024140, 0.045810 (2000) |
| G4 / locked_rate [small sample] | unavailable | 0 / 0 | 376 | unavailable (0) | unavailable | unavailable (0) |
| G4:ASM / signed_return_90d | -0.053624 | 156 / 156 | 208 | -0.120050, 0.025543 (2000) | -0.063617 | -0.126422, 0.011543 (2000) |
| G4:ASM / collapse | 0.647436 | 156 / 156 | 208 | 0.573333, 0.719205 (2000) | 0.124889 | 0.050902, 0.197597 (2000) |
| G4:ASM / adverse20 | 0.160991 | 323 / 323 | 41 | 0.119559, 0.209465 (2000) | 0.083639 | 0.042921, 0.129462 (2000) |
| G4:ASM / stop_gap | 0.055728 | 323 / 323 | 41 | 0.031746, 0.082508 (2000) | 0.008848 | -0.017574, 0.037338 (2000) |
| G4:ASM / entry_gap | 0.002770 | 361 / 361 | 3 | 0.000000, 0.008929 (2000) | 0.000804 | -0.003681, 0.007388 (2000) |
| G4:ASM / mae_decision | 0.119275 | 323 / 323 | 41 | 0.110120, 0.129809 (2000) | 0.026185 | 0.016227, 0.036750 (2000) |
| G4:ASM / mae_fill | 0.129051 | 323 / 323 | 41 | 0.119673, 0.139701 (2000) | 0.033517 | 0.022727, 0.044313 (2000) |
| G4:ASM / locked_rate [small sample] | unavailable | 0 / 0 | 364 | unavailable (0) | unavailable | unavailable (0) |
| G4:GSM / signed_return_90d [small sample] | -0.181708 | 11 / 11 | 5 | -0.270548, -0.078682 (2000) | -0.191701 | -0.280555, -0.089655 (2000) |
| G4:GSM / collapse [small sample] | 0.818182 | 11 / 11 | 5 | 0.500000, 1.000000 (2000) | 0.295635 | -0.002061, 0.488609 (2000) |
| G4:GSM / adverse20 [small sample] | 0.062500 | 16 / 16 | 0 | 0.000000, 0.200000 (2000) | -0.014851 | -0.088319, 0.122512 (2000) |
| G4:GSM / stop_gap [small sample] | 0.000000 | 16 / 16 | 0 | 0.000000, 0.000000 (2000) | -0.046880 | -0.058641, -0.035386 (2000) |
| G4:GSM / entry_gap [small sample] | 0.000000 | 16 / 16 | 0 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G4:GSM / mae_decision [small sample] | 0.125924 | 16 / 16 | 0 | 0.096908, 0.155183 (2000) | 0.032834 | 0.003331, 0.060831 (2000) |
| G4:GSM / mae_fill [small sample] | 0.158339 | 16 / 16 | 0 | 0.123480, 0.190345 (2000) | 0.062805 | 0.026950, 0.094324 (2000) |
| G4:GSM / locked_rate [small sample] | unavailable | 0 / 0 | 16 | unavailable (0) | unavailable | unavailable (0) |
| G5 / signed_return_90d | -0.046658 | 1417 / 1417 | 807 | -0.063146, -0.030910 (2000) | -0.056651 | -0.075328, -0.037671 (2000) |
| G5 / collapse | 0.624559 | 1417 / 1417 | 807 | 0.576730, 0.673051 (2000) | 0.102012 | 0.061345, 0.141423 (2000) |
| G5 / adverse20 | 0.124879 | 2058 / 2058 | 166 | 0.098495, 0.154505 (2000) | 0.047527 | 0.027128, 0.071155 (2000) |
| G5 / stop_gap | 0.054908 | 2058 / 2058 | 166 | 0.042604, 0.068872 (2000) | 0.008028 | -0.005276, 0.021854 (2000) |
| G5 / entry_gap | 0.001354 | 2216 / 2216 | 8 | 0.000000, 0.003117 (2000) | -0.000613 | -0.002373, 0.001221 (2000) |
| G5 / mae_decision | 0.107733 | 2058 / 2058 | 166 | 0.096839, 0.118780 (2000) | 0.014643 | 0.007581, 0.021554 (2000) |
| G5 / mae_fill | 0.121726 | 2058 / 2058 | 166 | 0.110924, 0.133079 (2000) | 0.026192 | 0.019401, 0.033178 (2000) |
| G5 / locked_rate [small sample] | unavailable | 0 / 0 | 2224 | unavailable (0) | unavailable | unavailable (0) |
| G5:order_ADV_cap / signed_return_90d | -0.046658 | 1417 / 1417 | 807 | -0.063146, -0.030910 (2000) | -0.056651 | -0.075328, -0.037671 (2000) |
| G5:order_ADV_cap / collapse | 0.624559 | 1417 / 1417 | 807 | 0.576730, 0.673051 (2000) | 0.102012 | 0.061345, 0.141423 (2000) |
| G5:order_ADV_cap / adverse20 | 0.124879 | 2058 / 2058 | 166 | 0.098495, 0.154505 (2000) | 0.047527 | 0.027128, 0.071155 (2000) |
| G5:order_ADV_cap / stop_gap | 0.054908 | 2058 / 2058 | 166 | 0.042604, 0.068872 (2000) | 0.008028 | -0.005276, 0.021854 (2000) |
| G5:order_ADV_cap / entry_gap | 0.001354 | 2216 / 2216 | 8 | 0.000000, 0.003117 (2000) | -0.000613 | -0.002373, 0.001221 (2000) |
| G5:order_ADV_cap / mae_decision | 0.107733 | 2058 / 2058 | 166 | 0.096839, 0.118780 (2000) | 0.014643 | 0.007581, 0.021554 (2000) |
| G5:order_ADV_cap / mae_fill | 0.121726 | 2058 / 2058 | 166 | 0.110924, 0.133079 (2000) | 0.026192 | 0.019401, 0.033178 (2000) |
| G5:order_ADV_cap / locked_rate [small sample] | unavailable | 0 / 0 | 2224 | unavailable (0) | unavailable | unavailable (0) |
| G5:stressed_exit_cap / signed_return_90d | -0.066275 | 300 / 300 | 195 | -0.091652, -0.040442 (2000) | -0.076268 | -0.102849, -0.049400 (2000) |
| G5:stressed_exit_cap / collapse | 0.670000 | 300 / 300 | 195 | 0.598745, 0.736488 (2000) | 0.147453 | 0.086587, 0.206142 (2000) |
| G5:stressed_exit_cap / adverse20 | 0.166287 | 439 / 439 | 56 | 0.121836, 0.216286 (2000) | 0.088936 | 0.049969, 0.132688 (2000) |
| G5:stressed_exit_cap / stop_gap | 0.045558 | 439 / 439 | 56 | 0.026722, 0.065729 (2000) | -0.001321 | -0.022857, 0.021021 (2000) |
| G5:stressed_exit_cap / entry_gap | 0.000000 | 495 / 495 | 0 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G5:stressed_exit_cap / mae_decision | 0.117533 | 439 / 439 | 56 | 0.105833, 0.129595 (2000) | 0.024443 | 0.015935, 0.033492 (2000) |
| G5:stressed_exit_cap / mae_fill | 0.137509 | 439 / 439 | 56 | 0.126035, 0.149550 (2000) | 0.041975 | 0.033545, 0.050925 (2000) |
| G5:stressed_exit_cap / locked_rate [small sample] | unavailable | 0 / 0 | 495 | unavailable (0) | unavailable | unavailable (0) |
| G6 / signed_return_90d [small sample] | -0.146513 | 6 / 6 | 19 | -0.219321, -0.073234 (1996) | -0.156506 | -0.226464, -0.082169 (1996) |
| G6 / collapse [small sample] | 1.000000 | 6 / 6 | 19 | 1.000000, 1.000000 (1996) | 0.477453 | 0.453898, 0.500907 (1996) |
| G6 / adverse20 [small sample] | 0.173913 | 23 / 23 | 2 | 0.038462, 0.352989 (2000) | 0.096562 | -0.043507, 0.271573 (2000) |
| G6 / stop_gap [small sample] | 0.043478 | 23 / 23 | 2 | 0.000000, 0.148148 (2000) | -0.003401 | -0.055635, 0.097821 (2000) |
| G6 / entry_gap [small sample] | 0.000000 | 25 / 25 | 0 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G6 / mae_decision [small sample] | 0.119288 | 23 / 23 | 2 | 0.086820, 0.155294 (2000) | 0.026198 | -0.005131, 0.060706 (2000) |
| G6 / mae_fill [small sample] | 0.137134 | 23 / 23 | 2 | 0.103110, 0.176061 (2000) | 0.041600 | 0.007450, 0.078725 (2000) |
| G6 / locked_rate [small sample] | unavailable | 0 / 0 | 25 | unavailable (0) | unavailable | unavailable (0) |
| G6:open_risk_cap / signed_return_90d [small sample] | -0.146513 | 6 / 6 | 19 | -0.219321, -0.073234 (1996) | -0.156506 | -0.226464, -0.082169 (1996) |
| G6:open_risk_cap / collapse [small sample] | 1.000000 | 6 / 6 | 19 | 1.000000, 1.000000 (1996) | 0.477453 | 0.453898, 0.500907 (1996) |
| G6:open_risk_cap / adverse20 [small sample] | 0.173913 | 23 / 23 | 2 | 0.038462, 0.352989 (2000) | 0.096562 | -0.043507, 0.271573 (2000) |
| G6:open_risk_cap / stop_gap [small sample] | 0.043478 | 23 / 23 | 2 | 0.000000, 0.148148 (2000) | -0.003401 | -0.055635, 0.097821 (2000) |
| G6:open_risk_cap / entry_gap [small sample] | 0.000000 | 25 / 25 | 0 | 0.000000, 0.000000 (2000) | -0.001966 | -0.004323, -0.000452 (2000) |
| G6:open_risk_cap / mae_decision [small sample] | 0.119288 | 23 / 23 | 2 | 0.086820, 0.155294 (2000) | 0.026198 | -0.005131, 0.060706 (2000) |
| G6:open_risk_cap / mae_fill [small sample] | 0.137134 | 23 / 23 | 2 | 0.103110, 0.176061 (2000) | 0.041600 | 0.007450, 0.078725 (2000) |
| G6:open_risk_cap / locked_rate [small sample] | unavailable | 0 / 0 | 25 | unavailable (0) | unavailable | unavailable (0) |
| SCREEN_FAIL / signed_return_90d | -0.043627 | 1539 / 1539 | 962 | -0.061608, -0.026528 (2000) | -0.053619 | -0.072676, -0.035205 (2000) |
| SCREEN_FAIL / collapse | 0.620533 | 1539 / 1539 | 962 | 0.576103, 0.665477 (2000) | 0.097986 | 0.059583, 0.136037 (2000) |
| SCREEN_FAIL / adverse20 | 0.128627 | 2309 / 2309 | 192 | 0.102617, 0.157972 (2000) | 0.051276 | 0.031155, 0.074499 (2000) |
| SCREEN_FAIL / stop_gap | 0.052837 | 2309 / 2309 | 192 | 0.041482, 0.065673 (2000) | 0.005957 | -0.006737, 0.019673 (2000) |
| SCREEN_FAIL / entry_gap | 0.001606 | 2491 / 2491 | 10 | 0.000377, 0.003313 (2000) | -0.000361 | -0.002292, 0.001587 (2000) |
| SCREEN_FAIL / mae_decision | 0.108482 | 2309 / 2309 | 192 | 0.097965, 0.119115 (2000) | 0.015392 | 0.008916, 0.021903 (2000) |
| SCREEN_FAIL / mae_fill | 0.121737 | 2309 / 2309 | 192 | 0.111502, 0.132263 (2000) | 0.026203 | 0.019735, 0.032700 (2000) |
| SCREEN_FAIL / locked_rate [small sample] | unavailable | 0 / 0 | 2501 | unavailable (0) | unavailable | unavailable (0) |

## Reproduce

`python -u scripts/desk_shadow_replay.py`

Full denominators, missingness reasons and confidence intervals: `shadow_replay_results.json`. Event-level plans, evidence hashes, gates, execution records and labels: the raw artifact named in provenance. Rates and returns above are fractions; MAE is a nonnegative loss fraction. The signed 90-session mean is direction-aware market-relative return, not long-trade profit.
