# Clock and log test audit (18 October 2026)

Scope: explicit current-clock calls and ingestion/log entry points under tests/.
Only the ingestion-health status test was changed. This is a test problem:
the live retry check correctly skips a repeat after an evening run has started.
The fixed test uses 21:00 IST on 2026-10-18 for both the runner and health display,
and one separate log per status case under its per-test TemporaryDirectory.
No production function, clock default, retry condition or task changed.

Other observed clock/log dependencies (listed, not fixed):

| Test location | Dependency | Log isolation |
|---|---|---|
| test_battery_retry.py, MainRetryTest | Real datetime.now(IST) in setUp and real runner clock | Per-test temporary log; deliberately reused for a retry sequence |
| test_ingestion_progress.py, IngestionProgressTest / LowBatteryGuardTest | Real runner and health-display clocks; market_today in the low-battery assertion | Per-test temporary log; power subcases clear it |
| test_nightly_tree_guard.py, main/skip tests | Real runner clock and health-display clock | Per-test temporary log; some skip subcases intentionally share it |
| test_desk_brief.py, test_nightly_brief_is_told_which_run_is_writing_it | Real runner clock | Private temporary log |
| test_price_band_catch_up.py, test_the_missed_list_is_ingested_and_tonights_404_stays_unknown | Real current IST date in expected knowledge date and ingestion clock | Temporary database |
| test_t1_source_probe.py, ProbeLimitsTest | Real probe timestamps; budget test constructs datetime.now(UTC)-1 hour; pacing test measures elapsed time | Per-test temporary request ledger |
| test_000_logs_isolation.py, test_the_p8055_scenario_now_lands_in_the_temporary_folder | Real runner clock / market_today; writes the default dated brief | Private ingestion log, but brief uses suite-shared temporary logs directory; cleaned afterwards |
| test_000_logs_isolation.py, test_every_writer_resolves_into_the_temporary_folder | Writes default brief_2099-01-01.txt | Suite-shared temporary logs directory; cleaned afterwards |
| test_angel_stream_capacity_test.py, ProbeRunTest.run_probe | Fixed fake clock, but summaries use default logs_dir() | Suite-shared temporary logs directory; globbed summaries removed after each run |

`tests/__init__.py` redirects PRAMAN_LOGS_DIR to a suite-wide temporary folder.
The suite's final real-log integrity test checks that production logs were untouched.
The listed dependencies are an audit inventory, not claims that all are failing.

Validation: full suite 1,039 tests in 186.212 seconds, OK (exit 0). Existing P8-088 ResourceWarnings remain unfixed.
