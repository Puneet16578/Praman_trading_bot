# S1 development primary result lock - 21 October 2026

This locks the completed primary phase only, without recomputation. It is not the full protocol report. The original JSON envelope still says STARTED because the overall invocation did not finish. Its stash blob bytes are unchanged. Git stash apply converted line endings; the exact blob bytes were restored before locking.

## Incident and provenance

One authorised run was prepared at about 08:31 IST on 21 October 2026 through `s1_development_once_20261021.py`, which was uncommitted at the time. The attempt marker records the precise evaluation start at 08:35:49.999675 IST. The primary phase finished and was saved; its observed file modification time was 12:06:06 IST. The process then ended before the eight sensitivities were completed; none has a saved result. It probably ended when the session hit its usage limit (cause unverified). The wrapper may have begun a sensitivity before termination; no completion or error log survives to establish that. Nothing was rerun.

The provenance copy is `docs/desk/provenance/s1_development_once_20261021.py`. Its decoded source exactly matches `meta.invocation_source` in the saved JSON; the copy matches the original wrapper bytes. It is historical provenance, not a command to rerun. The frozen runner code is unchanged from b539e7e; the invocation records commit fa162897a02564b78934fc43ee471868445ff59a.

JSON SHA-256: `2d3c312399d8fa5083f73a4a46eeab17b594f89ef0204f59bcddcde61c6cf354`. Size: 8310313 bytes.

## Rules and observed-field presence

All requested observed fields are present for both horizons: group valid trades, distinct dates, missing count/denominator and fraction; usable draws for all four tests; and annual trade counts for 2021-2024. No outcome values were displayed before locking. Threshold constants are not recorded as dedicated JSON fields; they are fixed by the registration and frozen code at b539e7e. Some constants are also quoted in the embedded wrapper.

Registration references: `docs/desk/s1_unexplained_drop_prereg.md`. Code references: `desk/s1/statistics.py` at b539e7e.

| Registered rule (verbatim, line) | Frozen code (verbatim, lines) |
|---|---|
| 164: Minimums: at least 100 valid trades and 30 distinct decision dates per group, horizon and period. Missing outcomes must be at most 5%; denominator is filled trades excluding boundary-censored trades. No-fills/fill failures are not filled trades. | 25: `missing = sum(r["status"] == "MISSING" for r in rows)`<br>26: `denominator = len(valid)+missing`<br>33: `distinct_dates=len({r["day"] for r in valid}), missing=missing, filled_denominator=denominator,`<br>34: `missing_rate=missing/denominator if denominator else None,`<br>58: `return stats["valid"] >= 100 and stats["distinct_dates"] >= 30 and \`<br>59: `stats["missing_rate"] is not None and stats["missing_rate"] <= .05` |
| 166: A draw is usable for a test only if it meets that test's sample minimums. Each test needs at least 1,900 usable draws, otherwise it is INCONCLUSIVE. Test (a) requires only the unexplained group; (b) requires both. An inadequate explained group must not invalidate (a). Count distinct original decision dates, not repeated bootstrap copies as new dates. | 10: `SEED, DRAWS, BLOCK, MIN_USABLE = 20261001, 2000, 20, 1900`<br>79: `usable = (n >= 100) & (distinct >= 30) & (rate <= .05)`<br>78: `rate = np.divide(miss, n+miss, out=np.ones_like(n), where=n+miss > 0)`<br>128: `for key, test, enough in (("a", a, adequate(stats["unexplained"])),`<br>129: `("b", b, all(adequate(s) for s in stats.values()))):`<br>130: `test["state"] = ("INCONCLUSIVE" if not enough or test["usable_draws"] < MIN_USABLE else` |
| 168: For development consistency, a year with fewer than 30 valid trades counts as not positive. In 2025, each half-year needs at least 30 valid unexplained trades; otherwise replication consistency is INCONCLUSIVE. With sufficient trades, both January–June and July–December means must be strictly positive. Exactly zero is not positive. | 95: `bins = ("2021", "2022", "2023", "2024") if period == "development" else ("H1", "H2")`<br>102: `cells[key] = dict(n=len(part), mean=mean, positive=len(part) >= 30 and mean > 0)` |
| 162: \| (c) Consistency \| Development unexplained mean strictly positive in at least three of 2021, 2022, 2023 and 2024. \| | 106: `required = 3 if period == "development" else 2`<br>107: `state = "PASS" if sum(c["positive"] for c in cells.values()) >= required else "FAIL"` |
| 160: \| (a) Strategy \| Unexplained mean net return ≥ +0.25% per trade and family-adjusted interval strictly above zero. \| | 125: `a["estimate"] = stats["unexplained"]["mean"]`<br>131: `"PASS" if test["estimate"] >= .0025 and test["family_interval"][0] > 0 else "FAIL")` |
| 161: \| (b) Label \| Unexplained minus explained mean net return ≥ +0.25 percentage points and family-adjusted interval strictly above zero. \| | 126: `b["estimate"] = (stats["unexplained"]["mean"]-stats["explained"]["mean"]`<br>127: `if all(s["mean"] is not None for s in stats.values()) else None)`<br>131: `"PASS" if test["estimate"] >= .0025 and test["family_interval"][0] > 0 else "FAIL")` |
| 172: At each horizon, S1 PASS requires (a) and (c), with its applicable information requirements satisfied. With adequate information, failure of either means FAIL. Failure of an applicable information minimum means INCONCLUSIVE, not evidence of no effect. | 133: `verdict = ("INCONCLUSIVE" if "INCONCLUSIVE" in (a["state"], c["state"]) else`<br>134: `"PASS" if a["state"] == c["state"] == "PASS" else "FAIL")` |

## Attempt marker

Path: `data/s1/development_20261021.attempt.json` (ignored by Git; retained locally, contents preserved here).

```json
{"started_utc": "2026-10-21T03:05:49.999675+00:00", "input_sha256": "c0d88d62719f090d1bde5430e9801ddad57d03715555f37914d2d6c3597bb309"}
```

No dedicated run log was found among the stash contents; terminal-session output is no longer available. Post-run store hashes and a final invocation completion record are absent. No store was opened by this locking procedure.

The eight registered sensitivities will run as a separate, sensitivities-only invocation, whatever the primary verdict.

The primary took approximately 3 hours 30 minutes, from its marker timestamp to the observed saved-file modification time; this is an elapsed-time estimate, not an instrumented phase duration. No sensitivities or 2025 evaluation were launched in this locking session.

## Correction - 21 October 2026

The earlier cause line was wrong. The usage-limit message came after the 08:56 check, but the primary was saved at 12:06:06, so the limit did not end the process. It ended between 12:06 and 13:36; the exact time and cause are unknown.

The evaluation ran as a separate process that the session polled, not as a foreground command.

The recorded SHA-256, `2d3c312399d8fa5083f73a4a46eeab17b594f89ef0204f59bcddcde61c6cf354`, covers the committed Git blob (8,310,313 bytes), identical to the stash blob used for the lock. It does not cover the earlier CRLF-converted working copy. The S1 development JSON attribute disables line-ending conversion for primary and future sensitivity outputs. A fresh checkout through Git checkout-index with that attribute produced the recorded SHA-256.
