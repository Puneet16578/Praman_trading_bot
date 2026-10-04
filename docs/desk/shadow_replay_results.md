# Desk shadow replay results

This is reconstructed, observational research, not evidence that either live-trading gate is met.

## Limitations and missingness

Current identity mappings reconstruct historical membership. Historical map freshness is unavailable. Candidates use an empty hypothetical portfolio. Fixed-band history is sparse; unknown bands are never zero. Labels and screening share price inputs and the event close; ATR stops mechanically affect stop outcomes. The 2026 period is descriptive only. Intervals are unadjusted for multiple comparisons.

All tails use 20 global sessions; incomplete price windows are missing for 20-session statistics. Entry gaps use the first global session when observed, even if the rest of the window is missing. Adjusted paths use a constant share basis. Execution records retain the identical nightly raw-open, frozen-quantity convention; entry action dates can therefore differ from adjusted tail gaps. Circuit locks require all daily OHLC at the tick-rounded lower limit, using the previous market session report. This is only a daily-data proxy.

Reason groups describe the same semantic check with numeric values and symbols removed; exact reasons remain in the raw artifact. Gate/reason groups overlap and are not additive or independent. Each cohort resamples event-date clusters 2,000 times with seed 20261001. The all-candidate cohort is primary; filled-only is a selection-conditioned sensitivity.

## Provenance

```json
{
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
}
```

## Primary 2019-2025

### All candidates

| Group | Events | Dates | NO_FILL | Zero size | Invalid | Incomplete 20 | Missing 90 | Band covered / unknown | Warning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SCREEN_PASS | 45770 | 1465 | 7 | 0 | 0 | 206 | 597 | 0 / 915400 |  |
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
| G5 | 12353 | 1416 | 189 | 188 | 136 | 289 | 161 | 0 / 247060 |  |
| G5:no_plan | 136 | 129 | 136 | 136 | 136 | 136 | 5 | 0 / 2720 |  |
| G5:order_ADV_cap | 12165 | 1413 | 1 | 0 | 0 | 153 | 156 | 0 / 243300 |  |
| G5:stressed_exit_cap | 2420 | 829 | 0 | 0 | 0 | 79 | 28 | 0 / 48400 |  |
| G5:unknown_coverage | 52 | 52 | 52 | 52 | 0 | 0 | 0 | 0 / 1040 |  |
| G6 | 248 | 221 | 188 | 188 | 136 | 137 | 5 | 0 / 4960 |  |
| G6:no_plan | 136 | 129 | 136 | 136 | 136 | 136 | 5 | 0 / 2720 |  |
| G6:open_risk_cap | 60 | 52 | 0 | 0 | 0 | 1 | 0 | 0 / 1200 |  |
| G6:unknown_coverage | 52 | 52 | 52 | 52 | 0 | 0 | 0 | 0 / 1040 |  |
| SCREEN_FAIL | 14924 | 1454 | 189 | 188 | 136 | 299 | 199 | 0 / 298480 |  |

| Group / statistic | Estimate | n events / denominator | Missing events | 95% interval (usable draws) | Difference vs PASS | Difference 95% interval (usable draws) |
|---|---:|---:|---:|---|---:|---|
| SCREEN_PASS / signed_return_90d | -0.021412 | 45173 / 45173 | 597 | -0.025812, -0.017251 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / collapse | 0.588936 | 45173 / 45173 | 597 | 0.578187, 0.599148 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / adverse20 | 0.100145 | 45564 / 45564 | 206 | 0.087057, 0.116815 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / stop_gap | 0.039110 | 45564 / 45564 | 206 | 0.034808, 0.044272 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / entry_gap | 0.002695 | 45641 / 45641 | 129 | 0.000908, 0.005643 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_decision | 0.097064 | 45564 / 45564 | 206 | 0.092727, 0.102446 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_fill | 0.102382 | 45560 / 45560 | 210 | 0.098534, 0.106902 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / locked_rate [small sample] | unavailable | 0 / 0 | 45770 | unavailable (0) | unavailable | unavailable (0) |
| G1 / signed_return_90d | -0.053483 | 46 / 46 | 1 | -0.116156, 0.012668 (2000) | -0.032071 | -0.095113, 0.035453 (2000) |
| G1 / collapse | 0.608696 | 46 / 46 | 1 | 0.456522, 0.750000 (2000) | 0.019760 | -0.132623, 0.162076 (2000) |
| G1 / adverse20 [small sample] | 0.250000 | 24 / 24 | 23 | 0.079923, 0.437500 (2000) | 0.149855 | -0.021114, 0.335681 (2000) |
| G1 / stop_gap [small sample] | 0.125000 | 24 / 24 | 23 | 0.000000, 0.269318 (2000) | 0.085890 | -0.039200, 0.230473 (2000) |
| G1 / entry_gap | 0.000000 | 30 / 30 | 17 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005643, -0.000908 (2000) |
| G1 / mae_decision [small sample] | 0.138969 | 24 / 24 | 23 | 0.092798, 0.187440 (2000) | 0.041905 | -0.004006, 0.090874 (2000) |
| G1 / mae_fill [small sample] | 0.165184 | 24 / 24 | 23 | 0.114218, 0.218603 (2000) | 0.062802 | 0.012295, 0.116475 (2000) |
| G1 / locked_rate [small sample] | unavailable | 0 / 0 | 47 | unavailable (0) | unavailable | unavailable (0) |
| G1:security_missing / signed_return_90d | -0.053483 | 46 / 46 | 1 | -0.116156, 0.012668 (2000) | -0.032071 | -0.095113, 0.035453 (2000) |
| G1:security_missing / collapse | 0.608696 | 46 / 46 | 1 | 0.456522, 0.750000 (2000) | 0.019760 | -0.132623, 0.162076 (2000) |
| G1:security_missing / adverse20 [small sample] | 0.250000 | 24 / 24 | 23 | 0.079923, 0.437500 (2000) | 0.149855 | -0.021114, 0.335681 (2000) |
| G1:security_missing / stop_gap [small sample] | 0.125000 | 24 / 24 | 23 | 0.000000, 0.269318 (2000) | 0.085890 | -0.039200, 0.230473 (2000) |
| G1:security_missing / entry_gap | 0.000000 | 30 / 30 | 17 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005643, -0.000908 (2000) |
| G1:security_missing / mae_decision [small sample] | 0.138969 | 24 / 24 | 23 | 0.092798, 0.187440 (2000) | 0.041905 | -0.004006, 0.090874 (2000) |
| G1:security_missing / mae_fill [small sample] | 0.165184 | 24 / 24 | 23 | 0.114218, 0.218603 (2000) | 0.062802 | 0.012295, 0.116475 (2000) |
| G1:security_missing / locked_rate [small sample] | unavailable | 0 / 0 | 47 | unavailable (0) | unavailable | unavailable (0) |
| G2 / signed_return_90d | -0.022913 | 135 / 135 | 2 | -0.081767, 0.033264 (2000) | -0.001500 | -0.061033, 0.054983 (2000) |
| G2 / collapse | 0.548148 | 135 / 135 | 2 | 0.469685, 0.632820 (2000) | -0.040788 | -0.121044, 0.043061 (2000) |
| G2 / adverse20 | 0.144330 | 97 / 97 | 40 | 0.075467, 0.220000 (2000) | 0.044185 | -0.022318, 0.114981 (2000) |
| G2 / stop_gap | 0.041237 | 97 / 97 | 40 | 0.009091, 0.085714 (2000) | 0.002127 | -0.032815, 0.048122 (2000) |
| G2 / entry_gap | 0.000000 | 97 / 97 | 40 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005643, -0.000908 (2000) |
| G2 / mae_decision | 0.103010 | 97 / 97 | 40 | 0.085802, 0.121667 (2000) | 0.005947 | -0.010800, 0.023599 (2000) |
| G2 / mae_fill | 0.110434 | 97 / 97 | 40 | 0.092652, 0.129091 (2000) | 0.008052 | -0.008467, 0.026010 (2000) |
| G2 / locked_rate [small sample] | unavailable | 0 / 0 | 137 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_delivery / signed_return_90d | -0.022913 | 135 / 135 | 2 | -0.081767, 0.033264 (2000) | -0.001500 | -0.061033, 0.054983 (2000) |
| G2:required_dimension_delivery / collapse | 0.548148 | 135 / 135 | 2 | 0.469685, 0.632820 (2000) | -0.040788 | -0.121044, 0.043061 (2000) |
| G2:required_dimension_delivery / adverse20 | 0.144330 | 97 / 97 | 40 | 0.075467, 0.220000 (2000) | 0.044185 | -0.022318, 0.114981 (2000) |
| G2:required_dimension_delivery / stop_gap | 0.041237 | 97 / 97 | 40 | 0.009091, 0.085714 (2000) | 0.002127 | -0.032815, 0.048122 (2000) |
| G2:required_dimension_delivery / entry_gap | 0.000000 | 97 / 97 | 40 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005643, -0.000908 (2000) |
| G2:required_dimension_delivery / mae_decision | 0.103010 | 97 / 97 | 40 | 0.085802, 0.121667 (2000) | 0.005947 | -0.010800, 0.023599 (2000) |
| G2:required_dimension_delivery / mae_fill | 0.110434 | 97 / 97 | 40 | 0.092652, 0.129091 (2000) | 0.008052 | -0.008467, 0.026010 (2000) |
| G2:required_dimension_delivery / locked_rate [small sample] | unavailable | 0 / 0 | 137 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_price / signed_return_90d | -0.007840 | 132 / 132 | 2 | -0.051879, 0.035927 (2000) | 0.013572 | -0.030469, 0.056200 (2000) |
| G2:required_dimension_price / collapse | 0.545455 | 132 / 132 | 2 | 0.463759, 0.629930 (2000) | -0.043481 | -0.124344, 0.041657 (2000) |
| G2:required_dimension_price / adverse20 | 0.127660 | 94 / 94 | 40 | 0.064499, 0.197802 (2000) | 0.027515 | -0.036536, 0.094726 (2000) |
| G2:required_dimension_price / stop_gap | 0.042553 | 94 / 94 | 40 | 0.009344, 0.088496 (2000) | 0.003443 | -0.032275, 0.051196 (2000) |
| G2:required_dimension_price / entry_gap | 0.000000 | 94 / 94 | 40 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005643, -0.000908 (2000) |
| G2:required_dimension_price / mae_decision | 0.097666 | 94 / 94 | 40 | 0.081180, 0.115162 (2000) | 0.000602 | -0.015521, 0.016889 (2000) |
| G2:required_dimension_price / mae_fill | 0.103906 | 94 / 94 | 40 | 0.088237, 0.120658 (2000) | 0.001523 | -0.013296, 0.017248 (2000) |
| G2:required_dimension_price / locked_rate [small sample] | unavailable | 0 / 0 | 134 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_volume / signed_return_90d | -0.007840 | 132 / 132 | 2 | -0.051879, 0.035927 (2000) | 0.013572 | -0.030469, 0.056200 (2000) |
| G2:required_dimension_volume / collapse | 0.545455 | 132 / 132 | 2 | 0.463759, 0.629930 (2000) | -0.043481 | -0.124344, 0.041657 (2000) |
| G2:required_dimension_volume / adverse20 | 0.127660 | 94 / 94 | 40 | 0.064499, 0.197802 (2000) | 0.027515 | -0.036536, 0.094726 (2000) |
| G2:required_dimension_volume / stop_gap | 0.042553 | 94 / 94 | 40 | 0.009344, 0.088496 (2000) | 0.003443 | -0.032275, 0.051196 (2000) |
| G2:required_dimension_volume / entry_gap | 0.000000 | 94 / 94 | 40 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005643, -0.000908 (2000) |
| G2:required_dimension_volume / mae_decision | 0.097666 | 94 / 94 | 40 | 0.081180, 0.115162 (2000) | 0.000602 | -0.015521, 0.016889 (2000) |
| G2:required_dimension_volume / mae_fill | 0.103906 | 94 / 94 | 40 | 0.088237, 0.120658 (2000) | 0.001523 | -0.013296, 0.017248 (2000) |
| G2:required_dimension_volume / locked_rate [small sample] | unavailable | 0 / 0 | 134 | unavailable (0) | unavailable | unavailable (0) |
| G3 / signed_return_90d | 0.013525 | 228 / 228 | 3 | -0.029076, 0.055942 (2000) | 0.034937 | -0.007991, 0.077302 (2000) |
| G3 / collapse | 0.521930 | 228 / 228 | 3 | 0.457625, 0.587393 (2000) | -0.067006 | -0.132243, -0.000980 (2000) |
| G3 / adverse20 | 0.170213 | 141 / 141 | 90 | 0.110294, 0.230795 (2000) | 0.070068 | 0.009306, 0.132595 (2000) |
| G3 / stop_gap | 0.085106 | 141 / 141 | 90 | 0.040541, 0.131397 (2000) | 0.045997 | 0.001492, 0.091221 (2000) |
| G3 / entry_gap | 0.000000 | 143 / 143 | 88 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005643, -0.000908 (2000) |
| G3 / mae_decision | 0.117780 | 141 / 141 | 90 | 0.101219, 0.134943 (2000) | 0.020716 | 0.003884, 0.038438 (2000) |
| G3 / mae_fill | 0.124647 | 141 / 141 | 90 | 0.108547, 0.140469 (2000) | 0.022265 | 0.006149, 0.038694 (2000) |
| G3 / locked_rate [small sample] | unavailable | 0 / 0 | 231 | unavailable (0) | unavailable | unavailable (0) |
| G3:structural_break / signed_return_90d | 0.013525 | 228 / 228 | 3 | -0.029076, 0.055942 (2000) | 0.034937 | -0.007991, 0.077302 (2000) |
| G3:structural_break / collapse | 0.521930 | 228 / 228 | 3 | 0.457625, 0.587393 (2000) | -0.067006 | -0.132243, -0.000980 (2000) |
| G3:structural_break / adverse20 | 0.170213 | 141 / 141 | 90 | 0.110294, 0.230795 (2000) | 0.070068 | 0.009306, 0.132595 (2000) |
| G3:structural_break / stop_gap | 0.085106 | 141 / 141 | 90 | 0.040541, 0.131397 (2000) | 0.045997 | 0.001492, 0.091221 (2000) |
| G3:structural_break / entry_gap | 0.000000 | 143 / 143 | 88 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005643, -0.000908 (2000) |
| G3:structural_break / mae_decision | 0.117780 | 141 / 141 | 90 | 0.101219, 0.134943 (2000) | 0.020716 | 0.003884, 0.038438 (2000) |
| G3:structural_break / mae_fill | 0.124647 | 141 / 141 | 90 | 0.108547, 0.140469 (2000) | 0.022265 | 0.006149, 0.038694 (2000) |
| G3:structural_break / locked_rate [small sample] | unavailable | 0 / 0 | 231 | unavailable (0) | unavailable | unavailable (0) |
| G4 / signed_return_90d | -0.034995 | 3149 / 3149 | 46 | -0.046127, -0.024182 (2000) | -0.013582 | -0.024868, -0.002291 (2000) |
| G4 / collapse | 0.597332 | 3149 / 3149 | 46 | 0.576738, 0.617871 (2000) | 0.008397 | -0.011136, 0.028604 (2000) |
| G4 / adverse20 | 0.190990 | 3152 / 3152 | 43 | 0.174385, 0.209824 (2000) | 0.090845 | 0.073024, 0.107843 (2000) |
| G4 / stop_gap | 0.073921 | 3152 / 3152 | 43 | 0.064077, 0.084333 (2000) | 0.034811 | 0.024872, 0.045265 (2000) |
| G4 / entry_gap | 0.002205 | 3174 / 3174 | 21 | 0.000913, 0.003990 (2000) | -0.000490 | -0.002866, 0.001533 (2000) |
| G4 / mae_decision | 0.126055 | 3152 / 3152 | 43 | 0.121049, 0.131374 (2000) | 0.028991 | 0.024475, 0.033363 (2000) |
| G4 / mae_fill | 0.139451 | 3152 / 3152 | 43 | 0.134364, 0.144857 (2000) | 0.037069 | 0.032700, 0.041598 (2000) |
| G4 / locked_rate [small sample] | unavailable | 0 / 0 | 3195 | unavailable (0) | unavailable | unavailable (0) |
| G4:ASM / signed_return_90d | -0.034716 | 3140 / 3140 | 46 | -0.045959, -0.023880 (2000) | -0.013304 | -0.024736, -0.001995 (2000) |
| G4:ASM / collapse | 0.596815 | 3140 / 3140 | 46 | 0.576132, 0.617593 (2000) | 0.007879 | -0.011806, 0.028037 (2000) |
| G4:ASM / adverse20 | 0.190915 | 3148 / 3148 | 38 | 0.174349, 0.209845 (2000) | 0.090770 | 0.073044, 0.107890 (2000) |
| G4:ASM / stop_gap | 0.074015 | 3148 / 3148 | 38 | 0.064150, 0.084415 (2000) | 0.034905 | 0.025002, 0.045343 (2000) |
| G4:ASM / entry_gap | 0.002212 | 3165 / 3165 | 21 | 0.000917, 0.004006 (2000) | -0.000483 | -0.002857, 0.001541 (2000) |
| G4:ASM / mae_decision | 0.126062 | 3148 / 3148 | 38 | 0.121011, 0.131404 (2000) | 0.028998 | 0.024463, 0.033403 (2000) |
| G4:ASM / mae_fill | 0.139426 | 3148 / 3148 | 38 | 0.134329, 0.144831 (2000) | 0.037043 | 0.032673, 0.041575 (2000) |
| G4:ASM / locked_rate [small sample] | unavailable | 0 / 0 | 3186 | unavailable (0) | unavailable | unavailable (0) |
| G4:GSM / signed_return_90d [small sample] | -0.132269 | 9 / 9 | 0 | -0.230099, -0.031760 (2000) | -0.110857 | -0.209593, -0.011235 (2000) |
| G4:GSM / collapse [small sample] | 0.777778 | 9 / 9 | 0 | 0.499038, 1.000000 (2000) | 0.188842 | -0.100819, 0.416017 (2000) |
| G4:GSM / adverse20 [small sample] | 0.250000 | 4 / 4 | 5 | 0.000000, 1.000000 (1966) | 0.149855 | -0.111454, 0.890950 (1966) |
| G4:GSM / stop_gap [small sample] | 0.000000 | 4 / 4 | 5 | 0.000000, 0.000000 (1966) | -0.039110 | -0.044267, -0.034732 (1966) |
| G4:GSM / entry_gap [small sample] | 0.000000 | 9 / 9 | 0 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005643, -0.000908 (2000) |
| G4:GSM / mae_decision [small sample] | 0.120905 | 4 / 4 | 5 | 0.069841, 0.213514 (1966) | 0.023841 | -0.026501, 0.113070 (1966) |
| G4:GSM / mae_fill [small sample] | 0.159566 | 4 / 4 | 5 | 0.095689, 0.269011 (1966) | 0.057184 | -0.003413, 0.163512 (1966) |
| G4:GSM / locked_rate [small sample] | unavailable | 0 / 0 | 9 | unavailable (0) | unavailable | unavailable (0) |
| G5 / signed_return_90d | -0.033727 | 12192 / 12192 | 161 | -0.039677, -0.027265 (2000) | -0.012315 | -0.019176, -0.004877 (2000) |
| G5 / collapse | 0.636401 | 12192 / 12192 | 161 | 0.623771, 0.647507 (2000) | 0.047465 | 0.035185, 0.059469 (2000) |
| G5 / adverse20 | 0.156996 | 12064 / 12064 | 289 | 0.139664, 0.178203 (2000) | 0.056851 | 0.046890, 0.067102 (2000) |
| G5 / stop_gap | 0.056366 | 12064 / 12064 | 289 | 0.051517, 0.061719 (2000) | 0.017256 | 0.012286, 0.022288 (2000) |
| G5 / entry_gap | 0.000984 | 12191 / 12191 | 162 | 0.000083, 0.002512 (2000) | -0.001711 | -0.003289, -0.000499 (2000) |
| G5 / mae_decision | 0.117761 | 12064 / 12064 | 289 | 0.112602, 0.124165 (2000) | 0.020697 | 0.017521, 0.023980 (2000) |
| G5 / mae_fill | 0.137618 | 12012 / 12012 | 341 | 0.132984, 0.142994 (2000) | 0.035236 | 0.032106, 0.038546 (2000) |
| G5 / locked_rate [small sample] | unavailable | 0 / 0 | 12353 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / signed_return_90d | -0.049994 | 131 / 131 | 5 | -0.101690, 0.001204 (2000) | -0.028582 | -0.079981, 0.022910 (2000) |
| G5:no_plan / collapse | 0.595420 | 131 / 131 | 5 | 0.508471, 0.682563 (2000) | 0.006484 | -0.078203, 0.095225 (2000) |
| G5:no_plan / adverse20 [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / stop_gap [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / entry_gap [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / mae_decision [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / mae_fill [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / locked_rate [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G5:order_ADV_cap / signed_return_90d | -0.033465 | 12009 / 12009 | 156 | -0.039389, -0.026897 (2000) | -0.012053 | -0.019105, -0.004512 (2000) |
| G5:order_ADV_cap / collapse | 0.636856 | 12009 / 12009 | 156 | 0.624231, 0.648143 (2000) | 0.047920 | 0.035375, 0.060068 (2000) |
| G5:order_ADV_cap / adverse20 | 0.157509 | 12012 / 12012 | 153 | 0.140222, 0.178760 (2000) | 0.057364 | 0.047328, 0.067663 (2000) |
| G5:order_ADV_cap / stop_gap | 0.056527 | 12012 / 12012 | 153 | 0.051762, 0.061815 (2000) | 0.017417 | 0.012393, 0.022560 (2000) |
| G5:order_ADV_cap / entry_gap | 0.000906 | 12139 / 12139 | 26 | 0.000083, 0.002262 (2000) | -0.001789 | -0.003495, -0.000500 (2000) |
| G5:order_ADV_cap / mae_decision | 0.118034 | 12012 / 12012 | 153 | 0.112869, 0.124434 (2000) | 0.020970 | 0.017770, 0.024285 (2000) |
| G5:order_ADV_cap / mae_fill | 0.137618 | 12012 / 12012 | 153 | 0.132984, 0.142994 (2000) | 0.035236 | 0.032106, 0.038546 (2000) |
| G5:order_ADV_cap / locked_rate [small sample] | unavailable | 0 / 0 | 12165 | unavailable (0) | unavailable | unavailable (0) |
| G5:stressed_exit_cap / signed_return_90d | -0.026133 | 2392 / 2392 | 28 | -0.040667, -0.010335 (2000) | -0.004720 | -0.020230, 0.011184 (2000) |
| G5:stressed_exit_cap / collapse | 0.637124 | 2392 / 2392 | 28 | 0.614154, 0.659813 (2000) | 0.048188 | 0.024837, 0.071385 (2000) |
| G5:stressed_exit_cap / adverse20 | 0.182401 | 2341 / 2341 | 79 | 0.157148, 0.208757 (2000) | 0.082256 | 0.061010, 0.105393 (2000) |
| G5:stressed_exit_cap / stop_gap | 0.077317 | 2341 / 2341 | 79 | 0.066447, 0.088533 (2000) | 0.038208 | 0.026717, 0.049466 (2000) |
| G5:stressed_exit_cap / entry_gap | 0.001242 | 2416 / 2416 | 4 | 0.000000, 0.002845 (2000) | -0.001453 | -0.003643, 0.000505 (2000) |
| G5:stressed_exit_cap / mae_decision | 0.120523 | 2341 / 2341 | 79 | 0.113151, 0.128632 (2000) | 0.023459 | 0.016979, 0.030214 (2000) |
| G5:stressed_exit_cap / mae_fill | 0.151615 | 2341 / 2341 | 79 | 0.144757, 0.158906 (2000) | 0.049233 | 0.043124, 0.055821 (2000) |
| G5:stressed_exit_cap / locked_rate [small sample] | unavailable | 0 / 0 | 2420 | unavailable (0) | unavailable | unavailable (0) |
| G5:unknown_coverage / signed_return_90d | -0.053314 | 52 / 52 | 0 | -0.100919, -0.004742 (2000) | -0.031902 | -0.079832, 0.016018 (2000) |
| G5:unknown_coverage / collapse | 0.634615 | 52 / 52 | 0 | 0.500000, 0.763170 (2000) | 0.045680 | -0.086470, 0.172016 (2000) |
| G5:unknown_coverage / adverse20 | 0.038462 | 52 / 52 | 0 | 0.000000, 0.098039 (2000) | -0.061683 | -0.105429, -0.001618 (2000) |
| G5:unknown_coverage / stop_gap | 0.019231 | 52 / 52 | 0 | 0.000000, 0.063492 (2000) | -0.019879 | -0.040643, 0.020647 (2000) |
| G5:unknown_coverage / entry_gap | 0.019231 | 52 / 52 | 0 | 0.000000, 0.063492 (2000) | 0.016536 | -0.002378, 0.057755 (2000) |
| G5:unknown_coverage / mae_decision | 0.054696 | 52 / 52 | 0 | 0.040710, 0.069969 (2000) | -0.042367 | -0.055034, -0.028474 (2000) |
| G5:unknown_coverage / mae_fill [small sample] | unavailable | 0 / 0 | 52 | unavailable (0) | unavailable | unavailable (0) |
| G5:unknown_coverage / locked_rate [small sample] | unavailable | 0 / 0 | 52 | unavailable (0) | unavailable | unavailable (0) |
| G6 / signed_return_90d | -0.036250 | 243 / 243 | 5 | -0.073603, 0.004114 (2000) | -0.014838 | -0.051743, 0.024996 (2000) |
| G6 / collapse | 0.613169 | 243 / 243 | 5 | 0.551584, 0.672340 (2000) | 0.024233 | -0.036674, 0.083040 (2000) |
| G6 / adverse20 | 0.162162 | 111 / 111 | 137 | 0.099081, 0.227282 (2000) | 0.062017 | -0.003102, 0.127324 (2000) |
| G6 / stop_gap | 0.099099 | 111 / 111 | 137 | 0.045861, 0.157420 (2000) | 0.059989 | 0.006359, 0.117161 (2000) |
| G6 / entry_gap | 0.008929 | 112 / 112 | 136 | 0.000000, 0.029712 (2000) | 0.006234 | -0.002378, 0.024575 (2000) |
| G6 / mae_decision | 0.098019 | 111 / 111 | 137 | 0.081889, 0.114568 (2000) | 0.000955 | -0.015166, 0.017565 (2000) |
| G6 / mae_fill | 0.162926 | 59 / 59 | 189 | 0.139714, 0.186442 (2000) | 0.060544 | 0.036897, 0.084550 (2000) |
| G6 / locked_rate [small sample] | unavailable | 0 / 0 | 248 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / signed_return_90d | -0.049994 | 131 / 131 | 5 | -0.101690, 0.001204 (2000) | -0.028582 | -0.079981, 0.022910 (2000) |
| G6:no_plan / collapse | 0.595420 | 131 / 131 | 5 | 0.508471, 0.682563 (2000) | 0.006484 | -0.078203, 0.095225 (2000) |
| G6:no_plan / adverse20 [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / stop_gap [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / entry_gap [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / mae_decision [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / mae_fill [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / locked_rate [small sample] | unavailable | 0 / 0 | 136 | unavailable (0) | unavailable | unavailable (0) |
| G6:open_risk_cap / signed_return_90d | 0.008544 | 60 / 60 | 0 | -0.091387, 0.119308 (2000) | 0.029956 | -0.069423, 0.140851 (2000) |
| G6:open_risk_cap / collapse | 0.633333 | 60 / 60 | 0 | 0.507463, 0.754394 (2000) | 0.044397 | -0.082302, 0.166097 (2000) |
| G6:open_risk_cap / adverse20 | 0.271186 | 59 / 59 | 1 | 0.163238, 0.382988 (2000) | 0.171042 | 0.062727, 0.281877 (2000) |
| G6:open_risk_cap / stop_gap | 0.169492 | 59 / 59 | 1 | 0.075758, 0.275910 (2000) | 0.130382 | 0.037852, 0.237516 (2000) |
| G6:open_risk_cap / entry_gap | 0.000000 | 60 / 60 | 0 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005643, -0.000908 (2000) |
| G6:open_risk_cap / mae_decision | 0.136201 | 59 / 59 | 1 | 0.110681, 0.161558 (2000) | 0.039138 | 0.013276, 0.064370 (2000) |
| G6:open_risk_cap / mae_fill | 0.162926 | 59 / 59 | 1 | 0.139714, 0.186442 (2000) | 0.060544 | 0.036897, 0.084550 (2000) |
| G6:open_risk_cap / locked_rate [small sample] | unavailable | 0 / 0 | 60 | unavailable (0) | unavailable | unavailable (0) |
| G6:unknown_coverage / signed_return_90d | -0.053314 | 52 / 52 | 0 | -0.100919, -0.004742 (2000) | -0.031902 | -0.079832, 0.016018 (2000) |
| G6:unknown_coverage / collapse | 0.634615 | 52 / 52 | 0 | 0.500000, 0.763170 (2000) | 0.045680 | -0.086470, 0.172016 (2000) |
| G6:unknown_coverage / adverse20 | 0.038462 | 52 / 52 | 0 | 0.000000, 0.098039 (2000) | -0.061683 | -0.105429, -0.001618 (2000) |
| G6:unknown_coverage / stop_gap | 0.019231 | 52 / 52 | 0 | 0.000000, 0.063492 (2000) | -0.019879 | -0.040643, 0.020647 (2000) |
| G6:unknown_coverage / entry_gap | 0.019231 | 52 / 52 | 0 | 0.000000, 0.063492 (2000) | 0.016536 | -0.002378, 0.057755 (2000) |
| G6:unknown_coverage / mae_decision | 0.054696 | 52 / 52 | 0 | 0.040710, 0.069969 (2000) | -0.042367 | -0.055034, -0.028474 (2000) |
| G6:unknown_coverage / mae_fill [small sample] | unavailable | 0 / 0 | 52 | unavailable (0) | unavailable | unavailable (0) |
| G6:unknown_coverage / locked_rate [small sample] | unavailable | 0 / 0 | 52 | unavailable (0) | unavailable | unavailable (0) |
| SCREEN_FAIL / signed_return_90d | -0.031666 | 14725 / 14725 | 199 | -0.037245, -0.025676 (2000) | -0.010254 | -0.017075, -0.003432 (2000) |
| SCREEN_FAIL / collapse | 0.624924 | 14725 / 14725 | 199 | 0.613396, 0.635737 (2000) | 0.035988 | 0.024921, 0.047170 (2000) |
| SCREEN_FAIL / adverse20 | 0.159932 | 14625 / 14625 | 299 | 0.144187, 0.178713 (2000) | 0.059787 | 0.050802, 0.068353 (2000) |
| SCREEN_FAIL / stop_gap | 0.056889 | 14625 / 14625 | 299 | 0.052379, 0.061988 (2000) | 0.017779 | 0.013030, 0.022486 (2000) |
| SCREEN_FAIL / entry_gap | 0.001287 | 14758 / 14758 | 166 | 0.000405, 0.002762 (2000) | -0.001408 | -0.003003, -0.000215 (2000) |
| SCREEN_FAIL / mae_decision | 0.118031 | 14625 / 14625 | 299 | 0.113365, 0.123844 (2000) | 0.020967 | 0.018227, 0.023769 (2000) |
| SCREEN_FAIL / mae_fill | 0.136092 | 14573 / 14573 | 351 | 0.131732, 0.141055 (2000) | 0.033710 | 0.031076, 0.036392 (2000) |
| SCREEN_FAIL / locked_rate [small sample] | unavailable | 0 / 0 | 14924 | unavailable (0) | unavailable | unavailable (0) |

### Filled only

| Group | Events | Dates | NO_FILL | Zero size | Invalid | Incomplete 20 | Missing 90 | Band covered / unknown | Warning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SCREEN_PASS | 45763 | 1465 | 0 | 0 | 0 | 203 | 595 | 0 / 915260 |  |
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
| G5 | 12164 | 1413 | 0 | 0 | 0 | 152 | 155 | 0 / 243280 |  |
| G5:order_ADV_cap | 12164 | 1413 | 0 | 0 | 0 | 152 | 155 | 0 / 243280 |  |
| G5:stressed_exit_cap | 2420 | 829 | 0 | 0 | 0 | 79 | 28 | 0 / 48400 |  |
| G6 | 60 | 52 | 0 | 0 | 0 | 1 | 0 | 0 / 1200 |  |
| G6:open_risk_cap | 60 | 52 | 0 | 0 | 0 | 1 | 0 | 0 / 1200 |  |
| SCREEN_FAIL | 14735 | 1452 | 0 | 0 | 0 | 162 | 193 | 0 / 294700 |  |

| Group / statistic | Estimate | n events / denominator | Missing events | 95% interval (usable draws) | Difference vs PASS | Difference 95% interval (usable draws) |
|---|---:|---:|---:|---|---:|---|
| SCREEN_PASS / signed_return_90d | -0.021396 | 45168 / 45168 | 595 | -0.025797, -0.017228 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / collapse | 0.588890 | 45168 / 45168 | 595 | 0.578142, 0.599094 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / adverse20 | 0.100132 | 45560 / 45560 | 203 | 0.087042, 0.116820 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / stop_gap | 0.039113 | 45560 / 45560 | 203 | 0.034810, 0.044279 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / entry_gap | 0.002695 | 45637 / 45637 | 126 | 0.000908, 0.005644 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_decision | 0.097061 | 45560 / 45560 | 203 | 0.092729, 0.102448 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_fill | 0.102382 | 45560 / 45560 | 203 | 0.098534, 0.106902 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / locked_rate [small sample] | unavailable | 0 / 0 | 45763 | unavailable (0) | unavailable | unavailable (0) |
| G1 / signed_return_90d [small sample] | -0.031005 | 29 / 29 | 1 | -0.114212, 0.057869 (2000) | -0.009609 | -0.093363, 0.079622 (2000) |
| G1 / collapse [small sample] | 0.551724 | 29 / 29 | 1 | 0.370370, 0.733333 (2000) | -0.037166 | -0.215910, 0.143531 (2000) |
| G1 / adverse20 [small sample] | 0.250000 | 24 / 24 | 6 | 0.079923, 0.437500 (2000) | 0.149868 | -0.021063, 0.335702 (2000) |
| G1 / stop_gap [small sample] | 0.125000 | 24 / 24 | 6 | 0.000000, 0.269318 (2000) | 0.085887 | -0.039205, 0.230469 (2000) |
| G1 / entry_gap | 0.000000 | 30 / 30 | 0 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G1 / mae_decision [small sample] | 0.138969 | 24 / 24 | 6 | 0.092798, 0.187440 (2000) | 0.041908 | -0.004003, 0.090882 (2000) |
| G1 / mae_fill [small sample] | 0.165184 | 24 / 24 | 6 | 0.114218, 0.218603 (2000) | 0.062802 | 0.012295, 0.116475 (2000) |
| G1 / locked_rate [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G1:security_missing / signed_return_90d [small sample] | -0.031005 | 29 / 29 | 1 | -0.114212, 0.057869 (2000) | -0.009609 | -0.093363, 0.079622 (2000) |
| G1:security_missing / collapse [small sample] | 0.551724 | 29 / 29 | 1 | 0.370370, 0.733333 (2000) | -0.037166 | -0.215910, 0.143531 (2000) |
| G1:security_missing / adverse20 [small sample] | 0.250000 | 24 / 24 | 6 | 0.079923, 0.437500 (2000) | 0.149868 | -0.021063, 0.335702 (2000) |
| G1:security_missing / stop_gap [small sample] | 0.125000 | 24 / 24 | 6 | 0.000000, 0.269318 (2000) | 0.085887 | -0.039205, 0.230469 (2000) |
| G1:security_missing / entry_gap | 0.000000 | 30 / 30 | 0 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G1:security_missing / mae_decision [small sample] | 0.138969 | 24 / 24 | 6 | 0.092798, 0.187440 (2000) | 0.041908 | -0.004003, 0.090882 (2000) |
| G1:security_missing / mae_fill [small sample] | 0.165184 | 24 / 24 | 6 | 0.114218, 0.218603 (2000) | 0.062802 | 0.012295, 0.116475 (2000) |
| G1:security_missing / locked_rate [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G2 / signed_return_90d | -0.010430 | 97 / 97 | 1 | -0.091206, 0.070074 (2000) | 0.010965 | -0.070283, 0.090807 (2000) |
| G2 / collapse | 0.505155 | 97 / 97 | 1 | 0.407747, 0.606742 (2000) | -0.083736 | -0.181488, 0.013563 (2000) |
| G2 / adverse20 | 0.144330 | 97 / 97 | 1 | 0.075467, 0.220000 (2000) | 0.044198 | -0.022328, 0.115020 (2000) |
| G2 / stop_gap | 0.041237 | 97 / 97 | 1 | 0.009091, 0.085714 (2000) | 0.002124 | -0.032816, 0.048117 (2000) |
| G2 / entry_gap | 0.000000 | 97 / 97 | 1 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G2 / mae_decision | 0.103010 | 97 / 97 | 1 | 0.085802, 0.121667 (2000) | 0.005950 | -0.010800, 0.023598 (2000) |
| G2 / mae_fill | 0.110434 | 97 / 97 | 1 | 0.092652, 0.129091 (2000) | 0.008052 | -0.008467, 0.026010 (2000) |
| G2 / locked_rate [small sample] | unavailable | 0 / 0 | 98 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_delivery / signed_return_90d | -0.010430 | 97 / 97 | 1 | -0.091206, 0.070074 (2000) | 0.010965 | -0.070283, 0.090807 (2000) |
| G2:required_dimension_delivery / collapse | 0.505155 | 97 / 97 | 1 | 0.407747, 0.606742 (2000) | -0.083736 | -0.181488, 0.013563 (2000) |
| G2:required_dimension_delivery / adverse20 | 0.144330 | 97 / 97 | 1 | 0.075467, 0.220000 (2000) | 0.044198 | -0.022328, 0.115020 (2000) |
| G2:required_dimension_delivery / stop_gap | 0.041237 | 97 / 97 | 1 | 0.009091, 0.085714 (2000) | 0.002124 | -0.032816, 0.048117 (2000) |
| G2:required_dimension_delivery / entry_gap | 0.000000 | 97 / 97 | 1 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G2:required_dimension_delivery / mae_decision | 0.103010 | 97 / 97 | 1 | 0.085802, 0.121667 (2000) | 0.005950 | -0.010800, 0.023598 (2000) |
| G2:required_dimension_delivery / mae_fill | 0.110434 | 97 / 97 | 1 | 0.092652, 0.129091 (2000) | 0.008052 | -0.008467, 0.026010 (2000) |
| G2:required_dimension_delivery / locked_rate [small sample] | unavailable | 0 / 0 | 98 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_price / signed_return_90d | 0.011133 | 94 / 94 | 1 | -0.045842, 0.068567 (2000) | 0.032529 | -0.025029, 0.089435 (2000) |
| G2:required_dimension_price / collapse | 0.500000 | 94 / 94 | 1 | 0.400000, 0.602201 (2000) | -0.088890 | -0.187227, 0.011512 (2000) |
| G2:required_dimension_price / adverse20 | 0.127660 | 94 / 94 | 1 | 0.064499, 0.197802 (2000) | 0.027528 | -0.036516, 0.094738 (2000) |
| G2:required_dimension_price / stop_gap | 0.042553 | 94 / 94 | 1 | 0.009344, 0.088496 (2000) | 0.003440 | -0.032280, 0.051188 (2000) |
| G2:required_dimension_price / entry_gap | 0.000000 | 94 / 94 | 1 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G2:required_dimension_price / mae_decision | 0.097666 | 94 / 94 | 1 | 0.081180, 0.115162 (2000) | 0.000606 | -0.015517, 0.016887 (2000) |
| G2:required_dimension_price / mae_fill | 0.103906 | 94 / 94 | 1 | 0.088237, 0.120658 (2000) | 0.001523 | -0.013296, 0.017248 (2000) |
| G2:required_dimension_price / locked_rate [small sample] | unavailable | 0 / 0 | 95 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_volume / signed_return_90d | 0.011133 | 94 / 94 | 1 | -0.045842, 0.068567 (2000) | 0.032529 | -0.025029, 0.089435 (2000) |
| G2:required_dimension_volume / collapse | 0.500000 | 94 / 94 | 1 | 0.400000, 0.602201 (2000) | -0.088890 | -0.187227, 0.011512 (2000) |
| G2:required_dimension_volume / adverse20 | 0.127660 | 94 / 94 | 1 | 0.064499, 0.197802 (2000) | 0.027528 | -0.036516, 0.094738 (2000) |
| G2:required_dimension_volume / stop_gap | 0.042553 | 94 / 94 | 1 | 0.009344, 0.088496 (2000) | 0.003440 | -0.032280, 0.051188 (2000) |
| G2:required_dimension_volume / entry_gap | 0.000000 | 94 / 94 | 1 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G2:required_dimension_volume / mae_decision | 0.097666 | 94 / 94 | 1 | 0.081180, 0.115162 (2000) | 0.000606 | -0.015517, 0.016887 (2000) |
| G2:required_dimension_volume / mae_fill | 0.103906 | 94 / 94 | 1 | 0.088237, 0.120658 (2000) | 0.001523 | -0.013296, 0.017248 (2000) |
| G2:required_dimension_volume / locked_rate [small sample] | unavailable | 0 / 0 | 95 | unavailable (0) | unavailable | unavailable (0) |
| G3 / signed_return_90d | 0.049438 | 141 / 141 | 2 | -0.003185, 0.106458 (2000) | 0.070833 | 0.018858, 0.128447 (2000) |
| G3 / collapse | 0.496454 | 141 / 141 | 2 | 0.414279, 0.577183 (2000) | -0.092436 | -0.176888, -0.011927 (2000) |
| G3 / adverse20 | 0.170213 | 141 / 141 | 2 | 0.110294, 0.230795 (2000) | 0.070081 | 0.009325, 0.132591 (2000) |
| G3 / stop_gap | 0.085106 | 141 / 141 | 2 | 0.040541, 0.131397 (2000) | 0.045993 | 0.001488, 0.091219 (2000) |
| G3 / entry_gap | 0.000000 | 143 / 143 | 0 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G3 / mae_decision | 0.117780 | 141 / 141 | 2 | 0.101219, 0.134943 (2000) | 0.020719 | 0.003883, 0.038447 (2000) |
| G3 / mae_fill | 0.124647 | 141 / 141 | 2 | 0.108547, 0.140469 (2000) | 0.022265 | 0.006149, 0.038694 (2000) |
| G3 / locked_rate [small sample] | unavailable | 0 / 0 | 143 | unavailable (0) | unavailable | unavailable (0) |
| G3:structural_break / signed_return_90d | 0.049438 | 141 / 141 | 2 | -0.003185, 0.106458 (2000) | 0.070833 | 0.018858, 0.128447 (2000) |
| G3:structural_break / collapse | 0.496454 | 141 / 141 | 2 | 0.414279, 0.577183 (2000) | -0.092436 | -0.176888, -0.011927 (2000) |
| G3:structural_break / adverse20 | 0.170213 | 141 / 141 | 2 | 0.110294, 0.230795 (2000) | 0.070081 | 0.009325, 0.132591 (2000) |
| G3:structural_break / stop_gap | 0.085106 | 141 / 141 | 2 | 0.040541, 0.131397 (2000) | 0.045993 | 0.001488, 0.091219 (2000) |
| G3:structural_break / entry_gap | 0.000000 | 143 / 143 | 0 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G3:structural_break / mae_decision | 0.117780 | 141 / 141 | 2 | 0.101219, 0.134943 (2000) | 0.020719 | 0.003883, 0.038447 (2000) |
| G3:structural_break / mae_fill | 0.124647 | 141 / 141 | 2 | 0.108547, 0.140469 (2000) | 0.022265 | 0.006149, 0.038694 (2000) |
| G3:structural_break / locked_rate [small sample] | unavailable | 0 / 0 | 143 | unavailable (0) | unavailable | unavailable (0) |
| G4 / signed_return_90d | -0.034772 | 3136 / 3136 | 45 | -0.045932, -0.023902 (2000) | -0.013377 | -0.024841, -0.002141 (2000) |
| G4 / collapse | 0.596939 | 3136 / 3136 | 45 | 0.576034, 0.617397 (2000) | 0.008048 | -0.011641, 0.028153 (2000) |
| G4 / adverse20 | 0.190990 | 3152 / 3152 | 29 | 0.174385, 0.209824 (2000) | 0.090858 | 0.073058, 0.107856 (2000) |
| G4 / stop_gap | 0.073921 | 3152 / 3152 | 29 | 0.064077, 0.084333 (2000) | 0.034808 | 0.024871, 0.045262 (2000) |
| G4 / entry_gap | 0.002205 | 3174 / 3174 | 7 | 0.000913, 0.003990 (2000) | -0.000490 | -0.002866, 0.001532 (2000) |
| G4 / mae_decision | 0.126055 | 3152 / 3152 | 29 | 0.121049, 0.131374 (2000) | 0.028995 | 0.024473, 0.033372 (2000) |
| G4 / mae_fill | 0.139451 | 3152 / 3152 | 29 | 0.134364, 0.144857 (2000) | 0.037069 | 0.032700, 0.041598 (2000) |
| G4 / locked_rate [small sample] | unavailable | 0 / 0 | 3181 | unavailable (0) | unavailable | unavailable (0) |
| G4:ASM / signed_return_90d | -0.034492 | 3127 / 3127 | 45 | -0.045688, -0.023562 (2000) | -0.013096 | -0.024575, -0.001872 (2000) |
| G4:ASM / collapse | 0.596418 | 3127 / 3127 | 45 | 0.575684, 0.616939 (2000) | 0.007528 | -0.012361, 0.027592 (2000) |
| G4:ASM / adverse20 | 0.190915 | 3148 / 3148 | 24 | 0.174349, 0.209845 (2000) | 0.090783 | 0.073054, 0.107902 (2000) |
| G4:ASM / stop_gap | 0.074015 | 3148 / 3148 | 24 | 0.064150, 0.084415 (2000) | 0.034902 | 0.025001, 0.045339 (2000) |
| G4:ASM / entry_gap | 0.002212 | 3165 / 3165 | 7 | 0.000917, 0.004006 (2000) | -0.000483 | -0.002857, 0.001541 (2000) |
| G4:ASM / mae_decision | 0.126062 | 3148 / 3148 | 24 | 0.121011, 0.131404 (2000) | 0.029001 | 0.024461, 0.033412 (2000) |
| G4:ASM / mae_fill | 0.139426 | 3148 / 3148 | 24 | 0.134329, 0.144831 (2000) | 0.037043 | 0.032673, 0.041575 (2000) |
| G4:ASM / locked_rate [small sample] | unavailable | 0 / 0 | 3172 | unavailable (0) | unavailable | unavailable (0) |
| G4:GSM / signed_return_90d [small sample] | -0.132269 | 9 / 9 | 0 | -0.230099, -0.031760 (2000) | -0.110873 | -0.209621, -0.011247 (2000) |
| G4:GSM / collapse [small sample] | 0.777778 | 9 / 9 | 0 | 0.499038, 1.000000 (2000) | 0.188887 | -0.100774, 0.416037 (2000) |
| G4:GSM / adverse20 [small sample] | 0.250000 | 4 / 4 | 5 | 0.000000, 1.000000 (1966) | 0.149868 | -0.111403, 0.890947 (1966) |
| G4:GSM / stop_gap [small sample] | 0.000000 | 4 / 4 | 5 | 0.000000, 0.000000 (1966) | -0.039113 | -0.044274, -0.034737 (1966) |
| G4:GSM / entry_gap [small sample] | 0.000000 | 9 / 9 | 0 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G4:GSM / mae_decision [small sample] | 0.120905 | 4 / 4 | 5 | 0.069841, 0.213514 (1966) | 0.023844 | -0.026502, 0.113070 (1966) |
| G4:GSM / mae_fill [small sample] | 0.159566 | 4 / 4 | 5 | 0.095689, 0.269011 (1966) | 0.057184 | -0.003413, 0.163512 (1966) |
| G4:GSM / locked_rate [small sample] | unavailable | 0 / 0 | 9 | unavailable (0) | unavailable | unavailable (0) |
| G5 / signed_return_90d | -0.033465 | 12009 / 12009 | 155 | -0.039389, -0.026897 (2000) | -0.012069 | -0.019117, -0.004535 (2000) |
| G5 / collapse | 0.636856 | 12009 / 12009 | 155 | 0.624231, 0.648143 (2000) | 0.047965 | 0.035427, 0.060087 (2000) |
| G5 / adverse20 | 0.157509 | 12012 / 12012 | 152 | 0.140222, 0.178760 (2000) | 0.057377 | 0.047334, 0.067678 (2000) |
| G5 / stop_gap | 0.056527 | 12012 / 12012 | 152 | 0.051762, 0.061815 (2000) | 0.017414 | 0.012390, 0.022555 (2000) |
| G5 / entry_gap | 0.000906 | 12139 / 12139 | 25 | 0.000083, 0.002262 (2000) | -0.001789 | -0.003496, -0.000500 (2000) |
| G5 / mae_decision | 0.118034 | 12012 / 12012 | 152 | 0.112869, 0.124434 (2000) | 0.020973 | 0.017779, 0.024282 (2000) |
| G5 / mae_fill | 0.137618 | 12012 / 12012 | 152 | 0.132984, 0.142994 (2000) | 0.035236 | 0.032106, 0.038546 (2000) |
| G5 / locked_rate [small sample] | unavailable | 0 / 0 | 12164 | unavailable (0) | unavailable | unavailable (0) |
| G5:order_ADV_cap / signed_return_90d | -0.033465 | 12009 / 12009 | 155 | -0.039389, -0.026897 (2000) | -0.012069 | -0.019117, -0.004535 (2000) |
| G5:order_ADV_cap / collapse | 0.636856 | 12009 / 12009 | 155 | 0.624231, 0.648143 (2000) | 0.047965 | 0.035427, 0.060087 (2000) |
| G5:order_ADV_cap / adverse20 | 0.157509 | 12012 / 12012 | 152 | 0.140222, 0.178760 (2000) | 0.057377 | 0.047334, 0.067678 (2000) |
| G5:order_ADV_cap / stop_gap | 0.056527 | 12012 / 12012 | 152 | 0.051762, 0.061815 (2000) | 0.017414 | 0.012390, 0.022555 (2000) |
| G5:order_ADV_cap / entry_gap | 0.000906 | 12139 / 12139 | 25 | 0.000083, 0.002262 (2000) | -0.001789 | -0.003496, -0.000500 (2000) |
| G5:order_ADV_cap / mae_decision | 0.118034 | 12012 / 12012 | 152 | 0.112869, 0.124434 (2000) | 0.020973 | 0.017779, 0.024282 (2000) |
| G5:order_ADV_cap / mae_fill | 0.137618 | 12012 / 12012 | 152 | 0.132984, 0.142994 (2000) | 0.035236 | 0.032106, 0.038546 (2000) |
| G5:order_ADV_cap / locked_rate [small sample] | unavailable | 0 / 0 | 12164 | unavailable (0) | unavailable | unavailable (0) |
| G5:stressed_exit_cap / signed_return_90d | -0.026133 | 2392 / 2392 | 28 | -0.040667, -0.010335 (2000) | -0.004737 | -0.020246, 0.011166 (2000) |
| G5:stressed_exit_cap / collapse | 0.637124 | 2392 / 2392 | 28 | 0.614154, 0.659813 (2000) | 0.048233 | 0.024874, 0.071421 (2000) |
| G5:stressed_exit_cap / adverse20 | 0.182401 | 2341 / 2341 | 79 | 0.157148, 0.208757 (2000) | 0.082269 | 0.061078, 0.105404 (2000) |
| G5:stressed_exit_cap / stop_gap | 0.077317 | 2341 / 2341 | 79 | 0.066447, 0.088533 (2000) | 0.038204 | 0.026715, 0.049464 (2000) |
| G5:stressed_exit_cap / entry_gap | 0.001242 | 2416 / 2416 | 4 | 0.000000, 0.002845 (2000) | -0.001453 | -0.003644, 0.000505 (2000) |
| G5:stressed_exit_cap / mae_decision | 0.120523 | 2341 / 2341 | 79 | 0.113151, 0.128632 (2000) | 0.023462 | 0.016983, 0.030221 (2000) |
| G5:stressed_exit_cap / mae_fill | 0.151615 | 2341 / 2341 | 79 | 0.144757, 0.158906 (2000) | 0.049233 | 0.043124, 0.055821 (2000) |
| G5:stressed_exit_cap / locked_rate [small sample] | unavailable | 0 / 0 | 2420 | unavailable (0) | unavailable | unavailable (0) |
| G6 / signed_return_90d | 0.008544 | 60 / 60 | 0 | -0.091387, 0.119308 (2000) | 0.029940 | -0.069431, 0.140822 (2000) |
| G6 / collapse | 0.633333 | 60 / 60 | 0 | 0.507463, 0.754394 (2000) | 0.044443 | -0.082239, 0.166152 (2000) |
| G6 / adverse20 | 0.271186 | 59 / 59 | 1 | 0.163238, 0.382988 (2000) | 0.171055 | 0.062742, 0.281889 (2000) |
| G6 / stop_gap | 0.169492 | 59 / 59 | 1 | 0.075758, 0.275910 (2000) | 0.130378 | 0.037848, 0.237515 (2000) |
| G6 / entry_gap | 0.000000 | 60 / 60 | 0 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G6 / mae_decision | 0.136201 | 59 / 59 | 1 | 0.110681, 0.161558 (2000) | 0.039141 | 0.013280, 0.064370 (2000) |
| G6 / mae_fill | 0.162926 | 59 / 59 | 1 | 0.139714, 0.186442 (2000) | 0.060544 | 0.036897, 0.084550 (2000) |
| G6 / locked_rate [small sample] | unavailable | 0 / 0 | 60 | unavailable (0) | unavailable | unavailable (0) |
| G6:open_risk_cap / signed_return_90d | 0.008544 | 60 / 60 | 0 | -0.091387, 0.119308 (2000) | 0.029940 | -0.069431, 0.140822 (2000) |
| G6:open_risk_cap / collapse | 0.633333 | 60 / 60 | 0 | 0.507463, 0.754394 (2000) | 0.044443 | -0.082239, 0.166152 (2000) |
| G6:open_risk_cap / adverse20 | 0.271186 | 59 / 59 | 1 | 0.163238, 0.382988 (2000) | 0.171055 | 0.062742, 0.281889 (2000) |
| G6:open_risk_cap / stop_gap | 0.169492 | 59 / 59 | 1 | 0.075758, 0.275910 (2000) | 0.130378 | 0.037848, 0.237515 (2000) |
| G6:open_risk_cap / entry_gap | 0.000000 | 60 / 60 | 0 | 0.000000, 0.000000 (2000) | -0.002695 | -0.005644, -0.000908 (2000) |
| G6:open_risk_cap / mae_decision | 0.136201 | 59 / 59 | 1 | 0.110681, 0.161558 (2000) | 0.039141 | 0.013280, 0.064370 (2000) |
| G6:open_risk_cap / mae_fill | 0.162926 | 59 / 59 | 1 | 0.139714, 0.186442 (2000) | 0.060544 | 0.036897, 0.084550 (2000) |
| G6:open_risk_cap / locked_rate [small sample] | unavailable | 0 / 0 | 60 | unavailable (0) | unavailable | unavailable (0) |
| SCREEN_FAIL / signed_return_90d | -0.031424 | 14542 / 14542 | 193 | -0.037088, -0.025489 (2000) | -0.010028 | -0.016901, -0.003115 (2000) |
| SCREEN_FAIL / collapse | 0.625155 | 14542 / 14542 | 193 | 0.613544, 0.636104 (2000) | 0.036264 | 0.024915, 0.047705 (2000) |
| SCREEN_FAIL / adverse20 | 0.160365 | 14573 / 14573 | 162 | 0.144569, 0.179181 (2000) | 0.060233 | 0.051280, 0.068886 (2000) |
| SCREEN_FAIL / stop_gap | 0.057023 | 14573 / 14573 | 162 | 0.052539, 0.062018 (2000) | 0.017910 | 0.013164, 0.022667 (2000) |
| SCREEN_FAIL / entry_gap | 0.001224 | 14706 / 14706 | 29 | 0.000407, 0.002544 (2000) | -0.001471 | -0.003167, -0.000212 (2000) |
| SCREEN_FAIL / mae_decision | 0.118257 | 14573 / 14573 | 162 | 0.113577, 0.124107 (2000) | 0.021196 | 0.018404, 0.024019 (2000) |
| SCREEN_FAIL / mae_fill | 0.136092 | 14573 / 14573 | 162 | 0.131732, 0.141055 (2000) | 0.033710 | 0.031076, 0.036392 (2000) |
| SCREEN_FAIL / locked_rate [small sample] | unavailable | 0 / 0 | 14735 | unavailable (0) | unavailable | unavailable (0) |

## Descriptive 2026

### All candidates

| Group | Events | Dates | NO_FILL | Zero size | Invalid | Incomplete 20 | Missing 90 | Band covered / unknown | Warning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SCREEN_PASS | 7142 | 172 | 2 | 0 | 0 | 307 | 2724 | 0 / 142840 |  |
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
| G5 | 2248 | 172 | 34 | 33 | 30 | 195 | 823 | 0 / 44960 |  |
| G5:no_plan | 30 | 26 | 30 | 30 | 30 | 30 | 19 | 0 / 600 |  |
| G5:order_ADV_cap | 2215 | 172 | 1 | 0 | 0 | 165 | 803 | 0 / 44300 |  |
| G5:stressed_exit_cap | 488 | 152 | 0 | 0 | 0 | 55 | 190 | 0 / 9760 |  |
| G5:unknown_coverage | 3 | 3 | 3 | 3 | 0 | 0 | 1 | 0 / 60 | small sample |
| G6 | 57 | 48 | 33 | 33 | 30 | 32 | 38 | 0 / 1140 |  |
| G6:no_plan | 30 | 26 | 30 | 30 | 30 | 30 | 19 | 0 / 600 |  |
| G6:open_risk_cap | 24 | 24 | 0 | 0 | 0 | 2 | 18 | 0 / 480 | small sample |
| G6:unknown_coverage | 3 | 3 | 3 | 3 | 0 | 0 | 1 | 0 / 60 | small sample |
| SCREEN_FAIL | 2526 | 172 | 34 | 33 | 30 | 222 | 978 | 0 / 50520 |  |

| Group / statistic | Estimate | n events / denominator | Missing events | 95% interval (usable draws) | Difference vs PASS | Difference 95% interval (usable draws) |
|---|---:|---:|---:|---|---:|---|
| SCREEN_PASS / signed_return_90d | 0.009948 | 4418 / 4418 | 2724 | -0.000769, 0.020091 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / collapse | 0.522408 | 4418 / 4418 | 2724 | 0.498973, 0.546060 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / adverse20 | 0.077396 | 6835 / 6835 | 307 | 0.062974, 0.092312 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / stop_gap | 0.046818 | 6835 / 6835 | 307 | 0.035327, 0.058593 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / entry_gap | 0.001964 | 7129 / 7129 | 13 | 0.000451, 0.004316 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_decision | 0.093125 | 6835 / 6835 | 307 | 0.085997, 0.100282 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_fill | 0.095580 | 6835 / 6835 | 307 | 0.088216, 0.103100 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / locked_rate [small sample] | unavailable | 0 / 0 | 7142 | unavailable (0) | unavailable | unavailable (0) |
| G1 / signed_return_90d [small sample] | -0.093560 | 12 / 12 | 3 | -0.198243, 0.013581 (2000) | -0.103508 | -0.208191, 0.005401 (2000) |
| G1 / collapse [small sample] | 0.750000 | 12 / 12 | 3 | 0.500000, 1.000000 (2000) | 0.227592 | -0.029280, 0.476220 (2000) |
| G1 / adverse20 [small sample] | 0.333333 | 6 / 6 | 9 | 0.000000, 0.666667 (1985) | 0.255938 | -0.083013, 0.603326 (1985) |
| G1 / stop_gap [small sample] | 0.000000 | 6 / 6 | 9 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058493, -0.035354 (1985) |
| G1 / entry_gap [small sample] | 0.000000 | 9 / 9 | 6 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G1 / mae_decision [small sample] | 0.151035 | 6 / 6 | 9 | 0.095898, 0.187902 (1985) | 0.057909 | 0.000485, 0.098083 (1985) |
| G1 / mae_fill [small sample] | 0.176217 | 6 / 6 | 9 | 0.112224, 0.226771 (1985) | 0.080637 | 0.016286, 0.129351 (1985) |
| G1 / locked_rate [small sample] | unavailable | 0 / 0 | 15 | unavailable (0) | unavailable | unavailable (0) |
| G1:security_missing / signed_return_90d [small sample] | -0.093560 | 12 / 12 | 3 | -0.198243, 0.013581 (2000) | -0.103508 | -0.208191, 0.005401 (2000) |
| G1:security_missing / collapse [small sample] | 0.750000 | 12 / 12 | 3 | 0.500000, 1.000000 (2000) | 0.227592 | -0.029280, 0.476220 (2000) |
| G1:security_missing / adverse20 [small sample] | 0.333333 | 6 / 6 | 9 | 0.000000, 0.666667 (1985) | 0.255938 | -0.083013, 0.603326 (1985) |
| G1:security_missing / stop_gap [small sample] | 0.000000 | 6 / 6 | 9 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058493, -0.035354 (1985) |
| G1:security_missing / entry_gap [small sample] | 0.000000 | 9 / 9 | 6 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G1:security_missing / mae_decision [small sample] | 0.151035 | 6 / 6 | 9 | 0.095898, 0.187902 (1985) | 0.057909 | 0.000485, 0.098083 (1985) |
| G1:security_missing / mae_fill [small sample] | 0.176217 | 6 / 6 | 9 | 0.112224, 0.226771 (1985) | 0.080637 | 0.016286, 0.129351 (1985) |
| G1:security_missing / locked_rate [small sample] | unavailable | 0 / 0 | 15 | unavailable (0) | unavailable | unavailable (0) |
| G2 / signed_return_90d [small sample] | 0.102897 | 13 / 13 | 4 | -0.092541, 0.285221 (2000) | 0.092949 | -0.099429, 0.277078 (2000) |
| G2 / collapse [small sample] | 0.461538 | 13 / 13 | 4 | 0.200000, 0.727273 (2000) | -0.060870 | -0.326500, 0.204621 (2000) |
| G2 / adverse20 [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.077396 | -0.092345, -0.062954 (1985) |
| G2 / stop_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058619, -0.035296 (1985) |
| G2 / entry_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.001964 | -0.004318, -0.000451 (1985) |
| G2 / mae_decision [small sample] | 0.061875 | 6 / 6 | 11 | 0.015747, 0.135075 (1985) | -0.031250 | -0.075641, 0.039931 (1985) |
| G2 / mae_fill [small sample] | 0.061087 | 6 / 6 | 11 | 0.019049, 0.137909 (1985) | -0.034493 | -0.075636, 0.042761 (1985) |
| G2 / locked_rate [small sample] | unavailable | 0 / 0 | 17 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_delivery / signed_return_90d [small sample] | 0.102897 | 13 / 13 | 4 | -0.092541, 0.285221 (2000) | 0.092949 | -0.099429, 0.277078 (2000) |
| G2:required_dimension_delivery / collapse [small sample] | 0.461538 | 13 / 13 | 4 | 0.200000, 0.727273 (2000) | -0.060870 | -0.326500, 0.204621 (2000) |
| G2:required_dimension_delivery / adverse20 [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.077396 | -0.092345, -0.062954 (1985) |
| G2:required_dimension_delivery / stop_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058619, -0.035296 (1985) |
| G2:required_dimension_delivery / entry_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.001964 | -0.004318, -0.000451 (1985) |
| G2:required_dimension_delivery / mae_decision [small sample] | 0.061875 | 6 / 6 | 11 | 0.015747, 0.135075 (1985) | -0.031250 | -0.075641, 0.039931 (1985) |
| G2:required_dimension_delivery / mae_fill [small sample] | 0.061087 | 6 / 6 | 11 | 0.019049, 0.137909 (1985) | -0.034493 | -0.075636, 0.042761 (1985) |
| G2:required_dimension_delivery / locked_rate [small sample] | unavailable | 0 / 0 | 17 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_price / signed_return_90d [small sample] | 0.102897 | 13 / 13 | 4 | -0.092541, 0.285221 (2000) | 0.092949 | -0.099429, 0.277078 (2000) |
| G2:required_dimension_price / collapse [small sample] | 0.461538 | 13 / 13 | 4 | 0.200000, 0.727273 (2000) | -0.060870 | -0.326500, 0.204621 (2000) |
| G2:required_dimension_price / adverse20 [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.077396 | -0.092345, -0.062954 (1985) |
| G2:required_dimension_price / stop_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058619, -0.035296 (1985) |
| G2:required_dimension_price / entry_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.001964 | -0.004318, -0.000451 (1985) |
| G2:required_dimension_price / mae_decision [small sample] | 0.061875 | 6 / 6 | 11 | 0.015747, 0.135075 (1985) | -0.031250 | -0.075641, 0.039931 (1985) |
| G2:required_dimension_price / mae_fill [small sample] | 0.061087 | 6 / 6 | 11 | 0.019049, 0.137909 (1985) | -0.034493 | -0.075636, 0.042761 (1985) |
| G2:required_dimension_price / locked_rate [small sample] | unavailable | 0 / 0 | 17 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_volume / signed_return_90d [small sample] | 0.102897 | 13 / 13 | 4 | -0.092541, 0.285221 (2000) | 0.092949 | -0.099429, 0.277078 (2000) |
| G2:required_dimension_volume / collapse [small sample] | 0.461538 | 13 / 13 | 4 | 0.200000, 0.727273 (2000) | -0.060870 | -0.326500, 0.204621 (2000) |
| G2:required_dimension_volume / adverse20 [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.077396 | -0.092345, -0.062954 (1985) |
| G2:required_dimension_volume / stop_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058619, -0.035296 (1985) |
| G2:required_dimension_volume / entry_gap [small sample] | 0.000000 | 6 / 6 | 11 | 0.000000, 0.000000 (1985) | -0.001964 | -0.004318, -0.000451 (1985) |
| G2:required_dimension_volume / mae_decision [small sample] | 0.061875 | 6 / 6 | 11 | 0.015747, 0.135075 (1985) | -0.031250 | -0.075641, 0.039931 (1985) |
| G2:required_dimension_volume / mae_fill [small sample] | 0.061087 | 6 / 6 | 11 | 0.019049, 0.137909 (1985) | -0.034493 | -0.075636, 0.042761 (1985) |
| G2:required_dimension_volume / locked_rate [small sample] | unavailable | 0 / 0 | 17 | unavailable (0) | unavailable | unavailable (0) |
| G3 / signed_return_90d [small sample] | 0.009794 | 16 / 16 | 25 | -0.145893, 0.227483 (2000) | -0.000153 | -0.158138, 0.217669 (2000) |
| G3 / collapse [small sample] | 0.562500 | 16 / 16 | 25 | 0.300000, 0.800000 (2000) | 0.040092 | -0.221706, 0.283876 (2000) |
| G3 / adverse20 [small sample] | 0.200000 | 20 / 20 | 21 | 0.000000, 0.434851 (2000) | 0.122604 | -0.074570, 0.358816 (2000) |
| G3 / stop_gap [small sample] | 0.000000 | 20 / 20 | 21 | 0.000000, 0.000000 (2000) | -0.046818 | -0.058593, -0.035327 (2000) |
| G3 / entry_gap [small sample] | 0.000000 | 21 / 21 | 20 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G3 / mae_decision [small sample] | 0.094681 | 20 / 20 | 21 | 0.040926, 0.158532 (2000) | 0.001556 | -0.053050, 0.066152 (2000) |
| G3 / mae_fill [small sample] | 0.119633 | 20 / 20 | 21 | 0.067975, 0.178833 (2000) | 0.024053 | -0.029095, 0.081962 (2000) |
| G3 / locked_rate [small sample] | unavailable | 0 / 0 | 41 | unavailable (0) | unavailable | unavailable (0) |
| G3:structural_break / signed_return_90d [small sample] | 0.009794 | 16 / 16 | 25 | -0.145893, 0.227483 (2000) | -0.000153 | -0.158138, 0.217669 (2000) |
| G3:structural_break / collapse [small sample] | 0.562500 | 16 / 16 | 25 | 0.300000, 0.800000 (2000) | 0.040092 | -0.221706, 0.283876 (2000) |
| G3:structural_break / adverse20 [small sample] | 0.200000 | 20 / 20 | 21 | 0.000000, 0.434851 (2000) | 0.122604 | -0.074570, 0.358816 (2000) |
| G3:structural_break / stop_gap [small sample] | 0.000000 | 20 / 20 | 21 | 0.000000, 0.000000 (2000) | -0.046818 | -0.058593, -0.035327 (2000) |
| G3:structural_break / entry_gap [small sample] | 0.000000 | 21 / 21 | 20 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G3:structural_break / mae_decision [small sample] | 0.094681 | 20 / 20 | 21 | 0.040926, 0.158532 (2000) | 0.001556 | -0.053050, 0.066152 (2000) |
| G3:structural_break / mae_fill [small sample] | 0.119633 | 20 / 20 | 21 | 0.067975, 0.178833 (2000) | 0.024053 | -0.029095, 0.081962 (2000) |
| G3:structural_break / locked_rate [small sample] | unavailable | 0 / 0 | 41 | unavailable (0) | unavailable | unavailable (0) |
| G4 / signed_return_90d | -0.058868 | 166 / 166 | 214 | -0.121200, 0.017743 (2000) | -0.068815 | -0.128004, 0.002882 (2000) |
| G4 / collapse | 0.656627 | 166 / 166 | 214 | 0.582845, 0.726190 (2000) | 0.134218 | 0.059238, 0.203798 (2000) |
| G4 / adverse20 | 0.158209 | 335 / 335 | 45 | 0.117647, 0.205500 (2000) | 0.080813 | 0.041148, 0.125051 (2000) |
| G4 / stop_gap | 0.053731 | 335 / 335 | 45 | 0.030483, 0.079577 (2000) | 0.006913 | -0.018592, 0.034642 (2000) |
| G4 / entry_gap | 0.002681 | 373 / 373 | 7 | 0.000000, 0.008571 (2000) | 0.000717 | -0.003677, 0.007072 (2000) |
| G4 / mae_decision | 0.119816 | 335 / 335 | 45 | 0.110846, 0.130034 (2000) | 0.026690 | 0.016777, 0.036780 (2000) |
| G4 / mae_fill | 0.130498 | 335 / 335 | 45 | 0.121342, 0.141090 (2000) | 0.034918 | 0.024087, 0.045776 (2000) |
| G4 / locked_rate [small sample] | unavailable | 0 / 0 | 380 | unavailable (0) | unavailable | unavailable (0) |
| G4:ASM / signed_return_90d | -0.053965 | 157 / 157 | 211 | -0.119980, 0.025541 (2000) | -0.063913 | -0.126441, 0.010830 (2000) |
| G4:ASM / collapse | 0.649682 | 157 / 157 | 211 | 0.576268, 0.720783 (2000) | 0.127273 | 0.053340, 0.198880 (2000) |
| G4:ASM / adverse20 | 0.160991 | 323 / 323 | 45 | 0.119559, 0.209465 (2000) | 0.083595 | 0.042800, 0.129460 (2000) |
| G4:ASM / stop_gap | 0.055728 | 323 / 323 | 45 | 0.031746, 0.082508 (2000) | 0.008910 | -0.017529, 0.037376 (2000) |
| G4:ASM / entry_gap | 0.002770 | 361 / 361 | 7 | 0.000000, 0.008929 (2000) | 0.000806 | -0.003677, 0.007394 (2000) |
| G4:ASM / mae_decision | 0.119275 | 323 / 323 | 45 | 0.110120, 0.129809 (2000) | 0.026149 | 0.016217, 0.036707 (2000) |
| G4:ASM / mae_fill | 0.129051 | 323 / 323 | 45 | 0.119673, 0.139701 (2000) | 0.033471 | 0.022690, 0.044285 (2000) |
| G4:ASM / locked_rate [small sample] | unavailable | 0 / 0 | 368 | unavailable (0) | unavailable | unavailable (0) |
| G4:GSM / signed_return_90d [small sample] | -0.181708 | 11 / 11 | 5 | -0.270548, -0.078682 (2000) | -0.191656 | -0.280563, -0.089829 (2000) |
| G4:GSM / collapse [small sample] | 0.818182 | 11 / 11 | 5 | 0.500000, 1.000000 (2000) | 0.295773 | -0.001806, 0.489035 (2000) |
| G4:GSM / adverse20 [small sample] | 0.062500 | 16 / 16 | 0 | 0.000000, 0.200000 (2000) | -0.014896 | -0.088366, 0.122452 (2000) |
| G4:GSM / stop_gap [small sample] | 0.000000 | 16 / 16 | 0 | 0.000000, 0.000000 (2000) | -0.046818 | -0.058593, -0.035327 (2000) |
| G4:GSM / entry_gap [small sample] | 0.000000 | 16 / 16 | 0 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G4:GSM / mae_decision [small sample] | 0.125924 | 16 / 16 | 0 | 0.096908, 0.155183 (2000) | 0.032798 | 0.003333, 0.060804 (2000) |
| G4:GSM / mae_fill [small sample] | 0.158339 | 16 / 16 | 0 | 0.123480, 0.190345 (2000) | 0.062759 | 0.026896, 0.094264 (2000) |
| G4:GSM / locked_rate [small sample] | unavailable | 0 / 0 | 16 | unavailable (0) | unavailable | unavailable (0) |
| G5 / signed_return_90d | -0.046017 | 1425 / 1425 | 823 | -0.062689, -0.029812 (2000) | -0.055965 | -0.074630, -0.037174 (2000) |
| G5 / collapse | 0.623860 | 1425 / 1425 | 823 | 0.576158, 0.671535 (2000) | 0.101451 | 0.062133, 0.140274 (2000) |
| G5 / adverse20 | 0.124696 | 2053 / 2053 | 195 | 0.098167, 0.153992 (2000) | 0.047300 | 0.027050, 0.070400 (2000) |
| G5 / stop_gap | 0.055528 | 2053 / 2053 | 195 | 0.043143, 0.069683 (2000) | 0.008711 | -0.004549, 0.022778 (2000) |
| G5 / entry_gap | 0.001357 | 2210 / 2210 | 38 | 0.000000, 0.003124 (2000) | -0.000606 | -0.002364, 0.001227 (2000) |
| G5 / mae_decision | 0.107542 | 2053 / 2053 | 195 | 0.096742, 0.118573 (2000) | 0.014417 | 0.007530, 0.021262 (2000) |
| G5 / mae_fill | 0.121595 | 2049 / 2049 | 199 | 0.110883, 0.132841 (2000) | 0.026015 | 0.019251, 0.033003 (2000) |
| G5 / locked_rate [small sample] | unavailable | 0 / 0 | 2248 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / signed_return_90d [small sample] | 0.037061 | 11 / 11 | 19 | -0.128804, 0.211483 (2000) | 0.027113 | -0.136311, 0.202735 (2000) |
| G5:no_plan / collapse [small sample] | 0.454545 | 11 / 11 | 19 | 0.166346, 0.727273 (2000) | -0.067863 | -0.362939, 0.206121 (2000) |
| G5:no_plan / adverse20 [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / stop_gap [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / entry_gap [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / mae_decision [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / mae_fill [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:no_plan / locked_rate [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G5:order_ADV_cap / signed_return_90d | -0.046679 | 1412 / 1412 | 803 | -0.063045, -0.030900 (2000) | -0.056627 | -0.075272, -0.037556 (2000) |
| G5:order_ADV_cap / collapse | 0.625354 | 1412 / 1412 | 803 | 0.577363, 0.672818 (2000) | 0.102946 | 0.063126, 0.142516 (2000) |
| G5:order_ADV_cap / adverse20 | 0.124878 | 2050 / 2050 | 165 | 0.098260, 0.154171 (2000) | 0.047482 | 0.027162, 0.070624 (2000) |
| G5:order_ADV_cap / stop_gap | 0.055122 | 2050 / 2050 | 165 | 0.042770, 0.069265 (2000) | 0.008304 | -0.004978, 0.022161 (2000) |
| G5:order_ADV_cap / entry_gap | 0.001359 | 2207 / 2207 | 8 | 0.000000, 0.003131 (2000) | -0.000604 | -0.002364, 0.001230 (2000) |
| G5:order_ADV_cap / mae_decision | 0.107656 | 2050 / 2050 | 165 | 0.096830, 0.118671 (2000) | 0.014530 | 0.007586, 0.021393 (2000) |
| G5:order_ADV_cap / mae_fill | 0.121595 | 2049 / 2049 | 166 | 0.110883, 0.132841 (2000) | 0.026015 | 0.019251, 0.033003 (2000) |
| G5:order_ADV_cap / locked_rate [small sample] | unavailable | 0 / 0 | 2215 | unavailable (0) | unavailable | unavailable (0) |
| G5:stressed_exit_cap / signed_return_90d | -0.064910 | 298 / 298 | 190 | -0.090557, -0.039390 (2000) | -0.074857 | -0.101853, -0.048077 (2000) |
| G5:stressed_exit_cap / collapse | 0.667785 | 298 / 298 | 190 | 0.597197, 0.734488 (2000) | 0.145377 | 0.084147, 0.204169 (2000) |
| G5:stressed_exit_cap / adverse20 | 0.166282 | 433 / 433 | 55 | 0.121688, 0.215559 (2000) | 0.088886 | 0.049914, 0.133332 (2000) |
| G5:stressed_exit_cap / stop_gap | 0.043880 | 433 / 433 | 55 | 0.025121, 0.063577 (2000) | -0.002938 | -0.024590, 0.018904 (2000) |
| G5:stressed_exit_cap / entry_gap | 0.000000 | 488 / 488 | 0 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G5:stressed_exit_cap / mae_decision | 0.117204 | 433 / 433 | 55 | 0.105660, 0.129252 (2000) | 0.024078 | 0.015631, 0.033110 (2000) |
| G5:stressed_exit_cap / mae_fill | 0.137264 | 433 / 433 | 55 | 0.125755, 0.149433 (2000) | 0.041683 | 0.033422, 0.050857 (2000) |
| G5:stressed_exit_cap / locked_rate [small sample] | unavailable | 0 / 0 | 488 | unavailable (0) | unavailable | unavailable (0) |
| G5:unknown_coverage / signed_return_90d [small sample] | -0.035617 | 2 / 2 | 1 | -0.178454, 0.107220 (1756) | -0.045564 | -0.195276, 0.104029 (1756) |
| G5:unknown_coverage / collapse [small sample] | 0.500000 | 2 / 2 | 1 | 0.000000, 1.000000 (1756) | -0.022408 | -0.535395, 0.493592 (1756) |
| G5:unknown_coverage / adverse20 [small sample] | 0.000000 | 3 / 3 | 0 | 0.000000, 0.000000 (1912) | -0.077396 | -0.092197, -0.063047 (1912) |
| G5:unknown_coverage / stop_gap [small sample] | 0.333333 | 3 / 3 | 0 | 0.000000, 1.000000 (1912) | 0.286515 | -0.055126, 0.955166 (1912) |
| G5:unknown_coverage / entry_gap [small sample] | 0.000000 | 3 / 3 | 0 | 0.000000, 0.000000 (1912) | -0.001964 | -0.004337, -0.000452 (1912) |
| G5:unknown_coverage / mae_decision [small sample] | 0.029715 | 3 / 3 | 0 | 0.000000, 0.082346 (1912) | -0.063411 | -0.096326, -0.009404 (1912) |
| G5:unknown_coverage / mae_fill [small sample] | unavailable | 0 / 0 | 3 | unavailable (0) | unavailable | unavailable (0) |
| G5:unknown_coverage / locked_rate [small sample] | unavailable | 0 / 0 | 3 | unavailable (0) | unavailable | unavailable (0) |
| G6 / signed_return_90d [small sample] | -0.028560 | 19 / 19 | 38 | -0.129294, 0.073055 (2000) | -0.038508 | -0.136856, 0.059795 (2000) |
| G6 / collapse [small sample] | 0.631579 | 19 / 19 | 38 | 0.444444, 0.823529 (2000) | 0.109171 | -0.075682, 0.295048 (2000) |
| G6 / adverse20 [small sample] | 0.160000 | 25 / 25 | 32 | 0.035683, 0.321429 (2000) | 0.082604 | -0.046596, 0.246530 (2000) |
| G6 / stop_gap [small sample] | 0.080000 | 25 / 25 | 32 | 0.000000, 0.200000 (2000) | 0.033182 | -0.052105, 0.156254 (2000) |
| G6 / entry_gap [small sample] | 0.000000 | 27 / 27 | 30 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G6 / mae_decision [small sample] | 0.110177 | 25 / 25 | 32 | 0.078453, 0.144342 (2000) | 0.017051 | -0.014713, 0.049997 (2000) |
| G6 / mae_fill [small sample] | 0.139806 | 22 / 22 | 35 | 0.104400, 0.179968 (2000) | 0.044225 | 0.009968, 0.082235 (2000) |
| G6 / locked_rate [small sample] | unavailable | 0 / 0 | 57 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / signed_return_90d [small sample] | 0.037061 | 11 / 11 | 19 | -0.128804, 0.211483 (2000) | 0.027113 | -0.136311, 0.202735 (2000) |
| G6:no_plan / collapse [small sample] | 0.454545 | 11 / 11 | 19 | 0.166346, 0.727273 (2000) | -0.067863 | -0.362939, 0.206121 (2000) |
| G6:no_plan / adverse20 [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / stop_gap [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / entry_gap [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / mae_decision [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / mae_fill [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:no_plan / locked_rate [small sample] | unavailable | 0 / 0 | 30 | unavailable (0) | unavailable | unavailable (0) |
| G6:open_risk_cap / signed_return_90d [small sample] | -0.146513 | 6 / 6 | 18 | -0.219321, -0.073234 (1996) | -0.156460 | -0.226459, -0.082229 (1996) |
| G6:open_risk_cap / collapse [small sample] | 1.000000 | 6 / 6 | 18 | 1.000000, 1.000000 (1996) | 0.477592 | 0.453936, 0.501027 (1996) |
| G6:open_risk_cap / adverse20 [small sample] | 0.181818 | 22 / 22 | 2 | 0.040000, 0.368421 (2000) | 0.104422 | -0.040422, 0.285998 (2000) |
| G6:open_risk_cap / stop_gap [small sample] | 0.045455 | 22 / 22 | 2 | 0.000000, 0.150000 (2000) | -0.001363 | -0.055580, 0.104951 (2000) |
| G6:open_risk_cap / entry_gap [small sample] | 0.000000 | 24 / 24 | 0 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G6:open_risk_cap / mae_decision [small sample] | 0.121149 | 22 / 22 | 2 | 0.087787, 0.158782 (2000) | 0.028023 | -0.005140, 0.064090 (2000) |
| G6:open_risk_cap / mae_fill [small sample] | 0.139806 | 22 / 22 | 2 | 0.104400, 0.179968 (2000) | 0.044225 | 0.009968, 0.082235 (2000) |
| G6:open_risk_cap / locked_rate [small sample] | unavailable | 0 / 0 | 24 | unavailable (0) | unavailable | unavailable (0) |
| G6:unknown_coverage / signed_return_90d [small sample] | -0.035617 | 2 / 2 | 1 | -0.178454, 0.107220 (1756) | -0.045564 | -0.195276, 0.104029 (1756) |
| G6:unknown_coverage / collapse [small sample] | 0.500000 | 2 / 2 | 1 | 0.000000, 1.000000 (1756) | -0.022408 | -0.535395, 0.493592 (1756) |
| G6:unknown_coverage / adverse20 [small sample] | 0.000000 | 3 / 3 | 0 | 0.000000, 0.000000 (1912) | -0.077396 | -0.092197, -0.063047 (1912) |
| G6:unknown_coverage / stop_gap [small sample] | 0.333333 | 3 / 3 | 0 | 0.000000, 1.000000 (1912) | 0.286515 | -0.055126, 0.955166 (1912) |
| G6:unknown_coverage / entry_gap [small sample] | 0.000000 | 3 / 3 | 0 | 0.000000, 0.000000 (1912) | -0.001964 | -0.004337, -0.000452 (1912) |
| G6:unknown_coverage / mae_decision [small sample] | 0.029715 | 3 / 3 | 0 | 0.000000, 0.082346 (1912) | -0.063411 | -0.096326, -0.009404 (1912) |
| G6:unknown_coverage / mae_fill [small sample] | unavailable | 0 / 0 | 3 | unavailable (0) | unavailable | unavailable (0) |
| G6:unknown_coverage / locked_rate [small sample] | unavailable | 0 / 0 | 3 | unavailable (0) | unavailable | unavailable (0) |
| SCREEN_FAIL / signed_return_90d | -0.042959 | 1548 / 1548 | 978 | -0.061102, -0.025532 (2000) | -0.052907 | -0.071633, -0.034612 (2000) |
| SCREEN_FAIL / collapse | 0.619509 | 1548 / 1548 | 978 | 0.575673, 0.663642 (2000) | 0.097101 | 0.059999, 0.133964 (2000) |
| SCREEN_FAIL / adverse20 | 0.128906 | 2304 / 2304 | 222 | 0.102994, 0.158145 (2000) | 0.051510 | 0.031084, 0.074434 (2000) |
| SCREEN_FAIL / stop_gap | 0.053385 | 2304 / 2304 | 222 | 0.041896, 0.066423 (2000) | 0.006568 | -0.006221, 0.020399 (2000) |
| SCREEN_FAIL / entry_gap | 0.001609 | 2486 / 2486 | 40 | 0.000378, 0.003316 (2000) | -0.000355 | -0.002281, 0.001588 (2000) |
| SCREEN_FAIL / mae_decision | 0.108384 | 2304 / 2304 | 222 | 0.097886, 0.119015 (2000) | 0.015259 | 0.008837, 0.021743 (2000) |
| SCREEN_FAIL / mae_fill | 0.121702 | 2300 / 2300 | 226 | 0.111609, 0.132307 (2000) | 0.026122 | 0.019752, 0.032567 (2000) |
| SCREEN_FAIL / locked_rate [small sample] | unavailable | 0 / 0 | 2526 | unavailable (0) | unavailable | unavailable (0) |

### Filled only

| Group | Events | Dates | NO_FILL | Zero size | Invalid | Incomplete 20 | Missing 90 | Band covered / unknown | Warning |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| SCREEN_PASS | 7140 | 172 | 0 | 0 | 0 | 305 | 2722 | 0 / 142800 |  |
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
| G5 | 2214 | 172 | 0 | 0 | 0 | 165 | 803 | 0 / 44280 |  |
| G5:order_ADV_cap | 2214 | 172 | 0 | 0 | 0 | 165 | 803 | 0 / 44280 |  |
| G5:stressed_exit_cap | 488 | 152 | 0 | 0 | 0 | 55 | 190 | 0 / 9760 |  |
| G6 | 24 | 24 | 0 | 0 | 0 | 2 | 18 | 0 / 480 | small sample |
| G6:open_risk_cap | 24 | 24 | 0 | 0 | 0 | 2 | 18 | 0 / 480 | small sample |
| SCREEN_FAIL | 2492 | 172 | 0 | 0 | 0 | 192 | 958 | 0 / 49840 |  |

| Group / statistic | Estimate | n events / denominator | Missing events | 95% interval (usable draws) | Difference vs PASS | Difference 95% interval (usable draws) |
|---|---:|---:|---:|---|---:|---|
| SCREEN_PASS / signed_return_90d | 0.009948 | 4418 / 4418 | 2722 | -0.000769, 0.020091 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / collapse | 0.522408 | 4418 / 4418 | 2722 | 0.498973, 0.546060 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / adverse20 | 0.077396 | 6835 / 6835 | 305 | 0.062974, 0.092312 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / stop_gap | 0.046818 | 6835 / 6835 | 305 | 0.035327, 0.058593 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / entry_gap | 0.001964 | 7129 / 7129 | 11 | 0.000451, 0.004316 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_decision | 0.093125 | 6835 / 6835 | 305 | 0.085997, 0.100282 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / mae_fill | 0.095580 | 6835 / 6835 | 305 | 0.088216, 0.103100 (2000) | unavailable | unavailable (0) |
| SCREEN_PASS / locked_rate [small sample] | unavailable | 0 / 0 | 7140 | unavailable (0) | unavailable | unavailable (0) |
| G1 / signed_return_90d [small sample] | -0.099101 | 6 / 6 | 3 | -0.241209, 0.101578 (1985) | -0.109048 | -0.253681, 0.095010 (1985) |
| G1 / collapse [small sample] | 0.833333 | 6 / 6 | 3 | 0.400000, 1.000000 (1985) | 0.310925 | -0.138356, 0.495531 (1985) |
| G1 / adverse20 [small sample] | 0.333333 | 6 / 6 | 3 | 0.000000, 0.666667 (1985) | 0.255938 | -0.083013, 0.603326 (1985) |
| G1 / stop_gap [small sample] | 0.000000 | 6 / 6 | 3 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058493, -0.035354 (1985) |
| G1 / entry_gap [small sample] | 0.000000 | 9 / 9 | 0 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G1 / mae_decision [small sample] | 0.151035 | 6 / 6 | 3 | 0.095898, 0.187902 (1985) | 0.057909 | 0.000485, 0.098083 (1985) |
| G1 / mae_fill [small sample] | 0.176217 | 6 / 6 | 3 | 0.112224, 0.226771 (1985) | 0.080637 | 0.016286, 0.129351 (1985) |
| G1 / locked_rate [small sample] | unavailable | 0 / 0 | 9 | unavailable (0) | unavailable | unavailable (0) |
| G1:security_missing / signed_return_90d [small sample] | -0.099101 | 6 / 6 | 3 | -0.241209, 0.101578 (1985) | -0.109048 | -0.253681, 0.095010 (1985) |
| G1:security_missing / collapse [small sample] | 0.833333 | 6 / 6 | 3 | 0.400000, 1.000000 (1985) | 0.310925 | -0.138356, 0.495531 (1985) |
| G1:security_missing / adverse20 [small sample] | 0.333333 | 6 / 6 | 3 | 0.000000, 0.666667 (1985) | 0.255938 | -0.083013, 0.603326 (1985) |
| G1:security_missing / stop_gap [small sample] | 0.000000 | 6 / 6 | 3 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058493, -0.035354 (1985) |
| G1:security_missing / entry_gap [small sample] | 0.000000 | 9 / 9 | 0 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G1:security_missing / mae_decision [small sample] | 0.151035 | 6 / 6 | 3 | 0.095898, 0.187902 (1985) | 0.057909 | 0.000485, 0.098083 (1985) |
| G1:security_missing / mae_fill [small sample] | 0.176217 | 6 / 6 | 3 | 0.112224, 0.226771 (1985) | 0.080637 | 0.016286, 0.129351 (1985) |
| G1:security_missing / locked_rate [small sample] | unavailable | 0 / 0 | 9 | unavailable (0) | unavailable | unavailable (0) |
| G2 / signed_return_90d [small sample] | 0.323378 | 3 / 3 | 3 | -0.089519, 0.529826 (1724) | 0.313430 | -0.107278, 0.527907 (1724) |
| G2 / collapse [small sample] | 0.333333 | 3 / 3 | 3 | 0.000000, 1.000000 (1724) | -0.189075 | -0.539790, 0.495548 (1724) |
| G2 / adverse20 [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.077396 | -0.092345, -0.062954 (1985) |
| G2 / stop_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058619, -0.035296 (1985) |
| G2 / entry_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.001964 | -0.004318, -0.000451 (1985) |
| G2 / mae_decision [small sample] | 0.061875 | 6 / 6 | 0 | 0.015747, 0.135075 (1985) | -0.031250 | -0.075641, 0.039931 (1985) |
| G2 / mae_fill [small sample] | 0.061087 | 6 / 6 | 0 | 0.019049, 0.137909 (1985) | -0.034493 | -0.075636, 0.042761 (1985) |
| G2 / locked_rate [small sample] | unavailable | 0 / 0 | 6 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_delivery / signed_return_90d [small sample] | 0.323378 | 3 / 3 | 3 | -0.089519, 0.529826 (1724) | 0.313430 | -0.107278, 0.527907 (1724) |
| G2:required_dimension_delivery / collapse [small sample] | 0.333333 | 3 / 3 | 3 | 0.000000, 1.000000 (1724) | -0.189075 | -0.539790, 0.495548 (1724) |
| G2:required_dimension_delivery / adverse20 [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.077396 | -0.092345, -0.062954 (1985) |
| G2:required_dimension_delivery / stop_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058619, -0.035296 (1985) |
| G2:required_dimension_delivery / entry_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.001964 | -0.004318, -0.000451 (1985) |
| G2:required_dimension_delivery / mae_decision [small sample] | 0.061875 | 6 / 6 | 0 | 0.015747, 0.135075 (1985) | -0.031250 | -0.075641, 0.039931 (1985) |
| G2:required_dimension_delivery / mae_fill [small sample] | 0.061087 | 6 / 6 | 0 | 0.019049, 0.137909 (1985) | -0.034493 | -0.075636, 0.042761 (1985) |
| G2:required_dimension_delivery / locked_rate [small sample] | unavailable | 0 / 0 | 6 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_price / signed_return_90d [small sample] | 0.323378 | 3 / 3 | 3 | -0.089519, 0.529826 (1724) | 0.313430 | -0.107278, 0.527907 (1724) |
| G2:required_dimension_price / collapse [small sample] | 0.333333 | 3 / 3 | 3 | 0.000000, 1.000000 (1724) | -0.189075 | -0.539790, 0.495548 (1724) |
| G2:required_dimension_price / adverse20 [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.077396 | -0.092345, -0.062954 (1985) |
| G2:required_dimension_price / stop_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058619, -0.035296 (1985) |
| G2:required_dimension_price / entry_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.001964 | -0.004318, -0.000451 (1985) |
| G2:required_dimension_price / mae_decision [small sample] | 0.061875 | 6 / 6 | 0 | 0.015747, 0.135075 (1985) | -0.031250 | -0.075641, 0.039931 (1985) |
| G2:required_dimension_price / mae_fill [small sample] | 0.061087 | 6 / 6 | 0 | 0.019049, 0.137909 (1985) | -0.034493 | -0.075636, 0.042761 (1985) |
| G2:required_dimension_price / locked_rate [small sample] | unavailable | 0 / 0 | 6 | unavailable (0) | unavailable | unavailable (0) |
| G2:required_dimension_volume / signed_return_90d [small sample] | 0.323378 | 3 / 3 | 3 | -0.089519, 0.529826 (1724) | 0.313430 | -0.107278, 0.527907 (1724) |
| G2:required_dimension_volume / collapse [small sample] | 0.333333 | 3 / 3 | 3 | 0.000000, 1.000000 (1724) | -0.189075 | -0.539790, 0.495548 (1724) |
| G2:required_dimension_volume / adverse20 [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.077396 | -0.092345, -0.062954 (1985) |
| G2:required_dimension_volume / stop_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.046818 | -0.058619, -0.035296 (1985) |
| G2:required_dimension_volume / entry_gap [small sample] | 0.000000 | 6 / 6 | 0 | 0.000000, 0.000000 (1985) | -0.001964 | -0.004318, -0.000451 (1985) |
| G2:required_dimension_volume / mae_decision [small sample] | 0.061875 | 6 / 6 | 0 | 0.015747, 0.135075 (1985) | -0.031250 | -0.075641, 0.039931 (1985) |
| G2:required_dimension_volume / mae_fill [small sample] | 0.061087 | 6 / 6 | 0 | 0.019049, 0.137909 (1985) | -0.034493 | -0.075636, 0.042761 (1985) |
| G2:required_dimension_volume / locked_rate [small sample] | unavailable | 0 / 0 | 6 | unavailable (0) | unavailable | unavailable (0) |
| G3 / signed_return_90d [small sample] | 0.007771 | 15 / 15 | 8 | -0.160079, 0.231184 (2000) | -0.002176 | -0.169164, 0.223311 (2000) |
| G3 / collapse [small sample] | 0.600000 | 15 / 15 | 8 | 0.315707, 0.857143 (2000) | 0.077592 | -0.204867, 0.333693 (2000) |
| G3 / adverse20 [small sample] | 0.200000 | 20 / 20 | 3 | 0.000000, 0.434851 (2000) | 0.122604 | -0.074570, 0.358816 (2000) |
| G3 / stop_gap [small sample] | 0.000000 | 20 / 20 | 3 | 0.000000, 0.000000 (2000) | -0.046818 | -0.058593, -0.035327 (2000) |
| G3 / entry_gap [small sample] | 0.000000 | 21 / 21 | 2 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G3 / mae_decision [small sample] | 0.094681 | 20 / 20 | 3 | 0.040926, 0.158532 (2000) | 0.001556 | -0.053050, 0.066152 (2000) |
| G3 / mae_fill [small sample] | 0.119633 | 20 / 20 | 3 | 0.067975, 0.178833 (2000) | 0.024053 | -0.029095, 0.081962 (2000) |
| G3 / locked_rate [small sample] | unavailable | 0 / 0 | 23 | unavailable (0) | unavailable | unavailable (0) |
| G3:structural_break / signed_return_90d [small sample] | 0.007771 | 15 / 15 | 8 | -0.160079, 0.231184 (2000) | -0.002176 | -0.169164, 0.223311 (2000) |
| G3:structural_break / collapse [small sample] | 0.600000 | 15 / 15 | 8 | 0.315707, 0.857143 (2000) | 0.077592 | -0.204867, 0.333693 (2000) |
| G3:structural_break / adverse20 [small sample] | 0.200000 | 20 / 20 | 3 | 0.000000, 0.434851 (2000) | 0.122604 | -0.074570, 0.358816 (2000) |
| G3:structural_break / stop_gap [small sample] | 0.000000 | 20 / 20 | 3 | 0.000000, 0.000000 (2000) | -0.046818 | -0.058593, -0.035327 (2000) |
| G3:structural_break / entry_gap [small sample] | 0.000000 | 21 / 21 | 2 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G3:structural_break / mae_decision [small sample] | 0.094681 | 20 / 20 | 3 | 0.040926, 0.158532 (2000) | 0.001556 | -0.053050, 0.066152 (2000) |
| G3:structural_break / mae_fill [small sample] | 0.119633 | 20 / 20 | 3 | 0.067975, 0.178833 (2000) | 0.024053 | -0.029095, 0.081962 (2000) |
| G3:structural_break / locked_rate [small sample] | unavailable | 0 / 0 | 23 | unavailable (0) | unavailable | unavailable (0) |
| G4 / signed_return_90d | -0.058575 | 165 / 165 | 211 | -0.121287, 0.018912 (2000) | -0.068522 | -0.128006, 0.004365 (2000) |
| G4 / collapse | 0.654545 | 165 / 165 | 211 | 0.580626, 0.724364 (2000) | 0.132137 | 0.056319, 0.202175 (2000) |
| G4 / adverse20 | 0.158209 | 335 / 335 | 41 | 0.117647, 0.205500 (2000) | 0.080813 | 0.041148, 0.125051 (2000) |
| G4 / stop_gap | 0.053731 | 335 / 335 | 41 | 0.030483, 0.079577 (2000) | 0.006913 | -0.018592, 0.034642 (2000) |
| G4 / entry_gap | 0.002681 | 373 / 373 | 3 | 0.000000, 0.008571 (2000) | 0.000717 | -0.003677, 0.007072 (2000) |
| G4 / mae_decision | 0.119816 | 335 / 335 | 41 | 0.110846, 0.130034 (2000) | 0.026690 | 0.016777, 0.036780 (2000) |
| G4 / mae_fill | 0.130498 | 335 / 335 | 41 | 0.121342, 0.141090 (2000) | 0.034918 | 0.024087, 0.045776 (2000) |
| G4 / locked_rate [small sample] | unavailable | 0 / 0 | 376 | unavailable (0) | unavailable | unavailable (0) |
| G4:ASM / signed_return_90d | -0.053624 | 156 / 156 | 208 | -0.120050, 0.025543 (2000) | -0.063571 | -0.126514, 0.011360 (2000) |
| G4:ASM / collapse | 0.647436 | 156 / 156 | 208 | 0.573333, 0.719205 (2000) | 0.125028 | 0.050824, 0.197517 (2000) |
| G4:ASM / adverse20 | 0.160991 | 323 / 323 | 41 | 0.119559, 0.209465 (2000) | 0.083595 | 0.042800, 0.129460 (2000) |
| G4:ASM / stop_gap | 0.055728 | 323 / 323 | 41 | 0.031746, 0.082508 (2000) | 0.008910 | -0.017529, 0.037376 (2000) |
| G4:ASM / entry_gap | 0.002770 | 361 / 361 | 3 | 0.000000, 0.008929 (2000) | 0.000806 | -0.003677, 0.007394 (2000) |
| G4:ASM / mae_decision | 0.119275 | 323 / 323 | 41 | 0.110120, 0.129809 (2000) | 0.026149 | 0.016217, 0.036707 (2000) |
| G4:ASM / mae_fill | 0.129051 | 323 / 323 | 41 | 0.119673, 0.139701 (2000) | 0.033471 | 0.022690, 0.044285 (2000) |
| G4:ASM / locked_rate [small sample] | unavailable | 0 / 0 | 364 | unavailable (0) | unavailable | unavailable (0) |
| G4:GSM / signed_return_90d [small sample] | -0.181708 | 11 / 11 | 5 | -0.270548, -0.078682 (2000) | -0.191656 | -0.280563, -0.089829 (2000) |
| G4:GSM / collapse [small sample] | 0.818182 | 11 / 11 | 5 | 0.500000, 1.000000 (2000) | 0.295773 | -0.001806, 0.489035 (2000) |
| G4:GSM / adverse20 [small sample] | 0.062500 | 16 / 16 | 0 | 0.000000, 0.200000 (2000) | -0.014896 | -0.088366, 0.122452 (2000) |
| G4:GSM / stop_gap [small sample] | 0.000000 | 16 / 16 | 0 | 0.000000, 0.000000 (2000) | -0.046818 | -0.058593, -0.035327 (2000) |
| G4:GSM / entry_gap [small sample] | 0.000000 | 16 / 16 | 0 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G4:GSM / mae_decision [small sample] | 0.125924 | 16 / 16 | 0 | 0.096908, 0.155183 (2000) | 0.032798 | 0.003333, 0.060804 (2000) |
| G4:GSM / mae_fill [small sample] | 0.158339 | 16 / 16 | 0 | 0.123480, 0.190345 (2000) | 0.062759 | 0.026896, 0.094264 (2000) |
| G4:GSM / locked_rate [small sample] | unavailable | 0 / 0 | 16 | unavailable (0) | unavailable | unavailable (0) |
| G5 / signed_return_90d | -0.046822 | 1411 / 1411 | 803 | -0.063302, -0.031038 (2000) | -0.056769 | -0.075516, -0.037559 (2000) |
| G5 / collapse | 0.625797 | 1411 / 1411 | 803 | 0.577834, 0.673445 (2000) | 0.103389 | 0.063362, 0.143037 (2000) |
| G5 / adverse20 | 0.124451 | 2049 / 2049 | 165 | 0.098010, 0.153538 (2000) | 0.047055 | 0.026517, 0.070264 (2000) |
| G5 / stop_gap | 0.055149 | 2049 / 2049 | 165 | 0.042789, 0.069265 (2000) | 0.008331 | -0.004958, 0.022162 (2000) |
| G5 / entry_gap | 0.001360 | 2206 / 2206 | 8 | 0.000000, 0.003131 (2000) | -0.000604 | -0.002363, 0.001232 (2000) |
| G5 / mae_decision | 0.107599 | 2049 / 2049 | 165 | 0.096777, 0.118666 (2000) | 0.014474 | 0.007529, 0.021342 (2000) |
| G5 / mae_fill | 0.121595 | 2049 / 2049 | 165 | 0.110883, 0.132841 (2000) | 0.026015 | 0.019251, 0.033003 (2000) |
| G5 / locked_rate [small sample] | unavailable | 0 / 0 | 2214 | unavailable (0) | unavailable | unavailable (0) |
| G5:order_ADV_cap / signed_return_90d | -0.046822 | 1411 / 1411 | 803 | -0.063302, -0.031038 (2000) | -0.056769 | -0.075516, -0.037559 (2000) |
| G5:order_ADV_cap / collapse | 0.625797 | 1411 / 1411 | 803 | 0.577834, 0.673445 (2000) | 0.103389 | 0.063362, 0.143037 (2000) |
| G5:order_ADV_cap / adverse20 | 0.124451 | 2049 / 2049 | 165 | 0.098010, 0.153538 (2000) | 0.047055 | 0.026517, 0.070264 (2000) |
| G5:order_ADV_cap / stop_gap | 0.055149 | 2049 / 2049 | 165 | 0.042789, 0.069265 (2000) | 0.008331 | -0.004958, 0.022162 (2000) |
| G5:order_ADV_cap / entry_gap | 0.001360 | 2206 / 2206 | 8 | 0.000000, 0.003131 (2000) | -0.000604 | -0.002363, 0.001232 (2000) |
| G5:order_ADV_cap / mae_decision | 0.107599 | 2049 / 2049 | 165 | 0.096777, 0.118666 (2000) | 0.014474 | 0.007529, 0.021342 (2000) |
| G5:order_ADV_cap / mae_fill | 0.121595 | 2049 / 2049 | 165 | 0.110883, 0.132841 (2000) | 0.026015 | 0.019251, 0.033003 (2000) |
| G5:order_ADV_cap / locked_rate [small sample] | unavailable | 0 / 0 | 2214 | unavailable (0) | unavailable | unavailable (0) |
| G5:stressed_exit_cap / signed_return_90d | -0.064910 | 298 / 298 | 190 | -0.090557, -0.039390 (2000) | -0.074857 | -0.101853, -0.048077 (2000) |
| G5:stressed_exit_cap / collapse | 0.667785 | 298 / 298 | 190 | 0.597197, 0.734488 (2000) | 0.145377 | 0.084147, 0.204169 (2000) |
| G5:stressed_exit_cap / adverse20 | 0.166282 | 433 / 433 | 55 | 0.121688, 0.215559 (2000) | 0.088886 | 0.049914, 0.133332 (2000) |
| G5:stressed_exit_cap / stop_gap | 0.043880 | 433 / 433 | 55 | 0.025121, 0.063577 (2000) | -0.002938 | -0.024590, 0.018904 (2000) |
| G5:stressed_exit_cap / entry_gap | 0.000000 | 488 / 488 | 0 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G5:stressed_exit_cap / mae_decision | 0.117204 | 433 / 433 | 55 | 0.105660, 0.129252 (2000) | 0.024078 | 0.015631, 0.033110 (2000) |
| G5:stressed_exit_cap / mae_fill | 0.137264 | 433 / 433 | 55 | 0.125755, 0.149433 (2000) | 0.041683 | 0.033422, 0.050857 (2000) |
| G5:stressed_exit_cap / locked_rate [small sample] | unavailable | 0 / 0 | 488 | unavailable (0) | unavailable | unavailable (0) |
| G6 / signed_return_90d [small sample] | -0.146513 | 6 / 6 | 18 | -0.219321, -0.073234 (1996) | -0.156460 | -0.226459, -0.082229 (1996) |
| G6 / collapse [small sample] | 1.000000 | 6 / 6 | 18 | 1.000000, 1.000000 (1996) | 0.477592 | 0.453936, 0.501027 (1996) |
| G6 / adverse20 [small sample] | 0.181818 | 22 / 22 | 2 | 0.040000, 0.368421 (2000) | 0.104422 | -0.040422, 0.285998 (2000) |
| G6 / stop_gap [small sample] | 0.045455 | 22 / 22 | 2 | 0.000000, 0.150000 (2000) | -0.001363 | -0.055580, 0.104951 (2000) |
| G6 / entry_gap [small sample] | 0.000000 | 24 / 24 | 0 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G6 / mae_decision [small sample] | 0.121149 | 22 / 22 | 2 | 0.087787, 0.158782 (2000) | 0.028023 | -0.005140, 0.064090 (2000) |
| G6 / mae_fill [small sample] | 0.139806 | 22 / 22 | 2 | 0.104400, 0.179968 (2000) | 0.044225 | 0.009968, 0.082235 (2000) |
| G6 / locked_rate [small sample] | unavailable | 0 / 0 | 24 | unavailable (0) | unavailable | unavailable (0) |
| G6:open_risk_cap / signed_return_90d [small sample] | -0.146513 | 6 / 6 | 18 | -0.219321, -0.073234 (1996) | -0.156460 | -0.226459, -0.082229 (1996) |
| G6:open_risk_cap / collapse [small sample] | 1.000000 | 6 / 6 | 18 | 1.000000, 1.000000 (1996) | 0.477592 | 0.453936, 0.501027 (1996) |
| G6:open_risk_cap / adverse20 [small sample] | 0.181818 | 22 / 22 | 2 | 0.040000, 0.368421 (2000) | 0.104422 | -0.040422, 0.285998 (2000) |
| G6:open_risk_cap / stop_gap [small sample] | 0.045455 | 22 / 22 | 2 | 0.000000, 0.150000 (2000) | -0.001363 | -0.055580, 0.104951 (2000) |
| G6:open_risk_cap / entry_gap [small sample] | 0.000000 | 24 / 24 | 0 | 0.000000, 0.000000 (2000) | -0.001964 | -0.004316, -0.000451 (2000) |
| G6:open_risk_cap / mae_decision [small sample] | 0.121149 | 22 / 22 | 2 | 0.087787, 0.158782 (2000) | 0.028023 | -0.005140, 0.064090 (2000) |
| G6:open_risk_cap / mae_fill [small sample] | 0.139806 | 22 / 22 | 2 | 0.104400, 0.179968 (2000) | 0.044225 | 0.009968, 0.082235 (2000) |
| G6:open_risk_cap / locked_rate [small sample] | unavailable | 0 / 0 | 24 | unavailable (0) | unavailable | unavailable (0) |
| SCREEN_FAIL / signed_return_90d | -0.043671 | 1534 / 1534 | 958 | -0.061467, -0.026619 (2000) | -0.053619 | -0.072868, -0.035444 (2000) |
| SCREEN_FAIL / collapse | 0.621252 | 1534 / 1534 | 958 | 0.576798, 0.665713 (2000) | 0.098843 | 0.061486, 0.136432 (2000) |
| SCREEN_FAIL / adverse20 | 0.128696 | 2300 / 2300 | 192 | 0.102264, 0.157557 (2000) | 0.051300 | 0.030878, 0.074334 (2000) |
| SCREEN_FAIL / stop_gap | 0.053043 | 2300 / 2300 | 192 | 0.041697, 0.065862 (2000) | 0.006226 | -0.006488, 0.020042 (2000) |
| SCREEN_FAIL / entry_gap | 0.001612 | 2482 / 2482 | 10 | 0.000379, 0.003326 (2000) | -0.000352 | -0.002278, 0.001592 (2000) |
| SCREEN_FAIL / mae_decision | 0.108437 | 2300 / 2300 | 192 | 0.097950, 0.119059 (2000) | 0.015311 | 0.008895, 0.021814 (2000) |
| SCREEN_FAIL / mae_fill | 0.121702 | 2300 / 2300 | 192 | 0.111609, 0.132307 (2000) | 0.026122 | 0.019752, 0.032567 (2000) |
| SCREEN_FAIL / locked_rate [small sample] | unavailable | 0 / 0 | 2492 | unavailable (0) | unavailable | unavailable (0) |

## Reproduce

`python -u scripts/desk_shadow_replay.py`

Full denominators, missingness reasons and confidence intervals: `shadow_replay_results.json`. Event-level plans, evidence hashes, gates, execution records and labels: the raw artifact named in provenance. Rates and returns above are fractions; MAE is a nonnegative loss fraction. The signed 90-session mean is direction-aware market-relative return, not long-trade profit.
