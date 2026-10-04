# Shadow replay follow-up 2: fixed entry limit

Research only. The active rulebook and paper entry convention are unchanged.

Limit = decision price + 0.5 ATR20. Fill at the next open if at/below the limit; otherwise at the limit only if that session low reaches it. Quantity stays frozen.

Adverse20 is the unchanged 20-session, decision-price-referenced outcome, conditional on fills. Daily bars cannot establish intraday ordering, queue priority or tradability. The 2026 sample is descriptive spent hold-out. Unknown inputs are counted separately within nonfills; they are not evidence of an untouched limit.

Intervals: 2,000 paired event-date-cluster draws, seed 20261001, percentile 95%. Size statistics condition on breaches; different conventions can have different cohorts. No tuning or multiplicity adjustment. Full statistic denominators, date counts, usable draws and small-sample warnings are in the JSON companion.

## Primary 2019-2025

Corrected passes: 45770.

| Convention | Fills | Nonfills (unknown) | Per-trade breaches | Missing adverse20 among fills |
|---|---:|---:|---:|---:|
| baseline | 45763 | 7 (7) | 13904 | 203 |
| limit | 44443 | 1327 (7) | 12210 | 196 |

| Statistic | Baseline [95% CI] | Limit [95% CI] | Limit minus baseline [95% CI] |
|---|---|---|---|
| fill_rate, % / difference pp | 99.9847 [99.9720, 99.9956]; draws=2000 | 97.1007 [96.7853, 97.3754]; draws=2000 | -2.8840 [-3.1989, -2.6112]; draws=2000 |
| per_trade_breach_rate, % / difference pp | 30.3826 [29.1097, 31.6754]; draws=2000 | 27.4734 [26.2321, 28.7334]; draws=2000 | -2.9092 [-3.1380, -2.7006]; draws=2000 |
| adverse20_rate, % / difference pp | 10.0132 [8.7042, 11.6820]; draws=2000 | 10.1544 [8.8112, 11.8757]; draws=2000 | 0.1412 [0.0894, 0.1975]; draws=2000 |
| Conditional excess median, % of cap | 11.5011 [11.0132, 11.9752]; draws=2000 | 9.5964 [9.2635, 9.9557]; draws=2000 | -1.9048 [-2.1578, -1.6550]; draws=2000 |
| Conditional excess p90, % of cap | 40.6666 [39.3715, 42.3315]; draws=2000 | 24.0816 [23.9474, 24.1822]; draws=2000 | -16.5850 [-18.2106, -15.3348]; draws=2000 |

Limit executions: 39184 at open; 5259 at limit; 1320 observed no touch.

Common-fill sensitivity (44443 events):

- per_trade_breach_rate: baseline 28.7582 [27.4823, 30.0202]; draws=2000%; limit 27.4734 [26.2321, 28.7334]; draws=2000%; difference -1.2848 [-1.4053, -1.1699]; draws=2000 pp.
- adverse20_rate: baseline 10.1544 [8.8112, 11.8757]; draws=2000%; limit 10.1544 [8.8112, 11.8757]; draws=2000%; difference 0.0000 [0.0000, 0.0000]; draws=2000 pp.

## Descriptive 2026

Corrected passes: 7142.

| Convention | Fills | Nonfills (unknown) | Per-trade breaches | Missing adverse20 among fills |
|---|---:|---:|---:|---:|
| baseline | 7140 | 2 (2) | 1819 | 305 |
| limit | 6972 | 170 (2) | 1602 | 299 |

| Statistic | Baseline [95% CI] | Limit [95% CI] | Limit minus baseline [95% CI] |
|---|---|---|---|
| fill_rate, % / difference pp | 99.9720 [99.9266, 100.0000]; draws=2000 | 97.6197 [96.3165, 98.4938]; draws=2000 | -2.3523 [-3.6539, -1.4832]; draws=2000 |
| per_trade_breach_rate, % / difference pp | 25.4762 [22.2953, 29.2609]; draws=2000 | 22.9776 [20.1529, 26.3608]; draws=2000 | -2.4986 [-3.4803, -1.7599]; draws=2000 |
| adverse20_rate, % / difference pp | 7.7396 [6.2974, 9.2312]; draws=2000 | 7.8376 [6.4254, 9.3259]; draws=2000 | 0.0980 [-0.0153, 0.2298]; draws=2000 |
| Conditional excess median, % of cap | 11.2510 [9.6204, 13.1254]; draws=2000 | 8.9597 [7.8176, 10.5030]; draws=2000 | -2.2913 [-3.1843, -1.5553]; draws=2000 |
| Conditional excess p90, % of cap | 38.4660 [33.1634, 45.1496]; draws=2000 | 23.8981 [23.0572, 24.2148]; draws=2000 | -14.5679 [-21.0109, -9.6451]; draws=2000 |

Limit executions: 6305 at open; 667 at limit; 168 observed no touch.

Common-fill sensitivity (6972 events):

- per_trade_breach_rate: baseline 24.0677 [21.2226, 27.6002]; draws=2000%; limit 22.9776 [20.1529, 26.3608]; draws=2000%; difference -1.0901 [-1.4631, -0.7781]; draws=2000 pp.
- adverse20_rate: baseline 7.8376 [6.4254, 9.3259]; draws=2000%; limit 7.8376 [6.4254, 9.3259]; draws=2000%; difference 0.0000 [0.0000, 0.0000]; draws=2000 pp.

## Provenance

```json
{
  "code_commit": "47272e21186cac5fc1d4ee05ed5ec2164b92400a",
  "preregistration_commit": "cb89f96faf4cca466482474352bb49a4da2b4f10",
  "run_date": "2026-10-04",
  "seed": 20261001,
  "bootstrap_replicates": 2000,
  "raw_sha256": "9a71fcf32912a42e69ae207ee3c8ef47d7e84f72f11e00e012198938d6d299a3",
  "base_results_sha256": "1db07387814bf2d83e1ed94e14fa03bcb160d125a5e8deaa82a6f9cb5e3d1c32",
  "source_hashes": {
    "docs/desk/shadow_replay_followup2_prereg.md": "a871dcc68381ceb05fe97f60a7e68232230798a614f1e50a7cb42c545d81e005",
    "desk/shadow_followup2.py": "6641b7378d15f3357070a01831108b0163427113f7588100a4333502cfd17190",
    "scripts/desk_shadow_followup2.py": "bafa3596bf1221b686f69107ebaa1e8843ad919621c3030c411053ce3d75b9fe",
    "tests/test_shadow_followup2.py": "1e389371c272d8707003fb7c5cf171cdec8239d40d28b5e4b78ec9c6057fdfe5",
    "desk/shadow_followup.py": "8a984defd9d95e51fd84e617bfb7be732c244d66cd5ccf18009bd7f16d9cdcad",
    "desk/risk/officer.py": "b18d806e3d60f88adc371ce922127bbc61f5f59c63734616d335ff3a88d05d22"
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
  "limit_atr_multiple": 0.5,
  "snapshot_sha256": "8f0608c703ba850806e19199c1454cc4657b7a5772bc4ae3bfc86df3eb04627f",
  "execution_path": "data/processed/desk_shadow_followup2_execution.jsonl",
  "execution_sha256": "16b6d22865e9ab109e7a6f20543631644619ef3bbc908c42f254792c8aabbda2"
}
```
