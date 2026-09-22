# Phase 9 — Adversarial Lint, README, Data/Legal Hygiene, Register Consistency

> **Update, 2026-09-22: both `P8-003` items below are now resolved — see
> `docs/DEFECT_REGISTER.md`'s `P8-003` entry for the applied fix and re-verification (326/326
> tests pass).** This document's own body is left as originally written (the findings, not yet
> the resolution) so the audit's original state stays auditable; read the register entry for
> current status.

## Summary (read this first)

**Top finding, most consequential: `src/classification/event_classifier.py`'s `PROVENANCE_NOTE` and
`DISCRIMINATIVE_POWER_NOTE` — rendered into every live report — still state the withdrawn AUC
0.611-0.70 ceiling as current fact.** This is a code fix, not a doc fix, so it is reported here and
queued (`P8-003`) rather than applied without approval. **Adversarial lint pass: `banned_terms.py`
missed all 11 of 11 hand-written adversarial phrasings tested** (e.g. "artificially inflated,"
"insider trading," "strong buy," "highly suspicious," "orchestrated," "circular trading") — every
one is a plausible LLM narrative phrasing that would sail through the invariant-12 lint uncaught.
Reported with real test output, not applied as a code change, for the same reason. **Data/legal
hygiene: clean.** `.gitignore` already excludes `data/raw/`, `data/processed/` (1.4GB, incl. the
1.4GB sqlite DB), `.env`, `*.db`; zero data files are tracked in git; no secrets, no TODO/FIXME, no
`pickle`/`eval`/`exec` found in `src/`. **Register consistency: verified, one format fix applied**
(23 table rows / 19 sections, matching the established "Low severity = row-only" convention
exactly — the 4 row-only entries are P3-001/002/003 and the just-added P8-002; `P8-001`'s Status
column reworded to lead with a status word like every other row). **README.md written** — this
project had none.

---

## 1. Adversarial lint pass

`src/agent/banned_terms.py` enforces CLAUDE.md invariant 12 ("NEVER STATE A CONCLUSION ABOUT
MANIPULATION") via three detector families: `DIRECT_TERM_PATTERNS` (manipulation, fraud, pump-and-
dump, scam, rigged, ponzi), `RANKING_PATTERNS` (a suspicion/manipulation-shaped score or rank),
`RHETORICAL_PATTERNS` (a leading question). The module's own docstring states plainly that it
expects false negatives and does not assume 100% coverage — this section is that adversarial check,
run for the first time as its own exercise rather than incidentally.

**Method:** 11 hand-written phrasings, each a plausible sentence an LLM narrative agent could
produce (this project is deterministic-by-default with LLM narrative permitted, CLAUDE.md invariant
2 — the lint's whole job is to catch exactly this kind of free-text risk), run through `lint_text()`
directly.

```
MISSED  | This stock shows artificially inflated volume patterns.
MISSED  | This trading pattern appears to be insider trading.
MISSED  | The stock is a strong buy at current levels.
MISSED  | Recommend selling before further decline.
MISSED  | Price target of INR 500 based on this pattern.
MISSED  | This activity is highly suspicious.
MISSED  | The volume pattern looks orchestrated.
MISSED  | This is consistent with circular trading among a small group of accounts.
MISSED  | The trading looks synthetic, not organic.
MISSED  | Investors should be cautious of this stock.
MISSED  | This has all the hallmarks of a coordinated operation.
```

**11 of 11 missed.** Three distinct gap shapes, not one:

1. **Manipulation-adjacent vocabulary outside the fixed `DIRECT_TERMS` list**: "insider trading,"
   "circular trading," "artificially inflated," "orchestrated," "coordinated operation," "synthetic
   [volume]" — all real, specific market-conduct terms a financial-narrative LLM would plausibly
   reach for, none of which are `manipulation`/`fraud`/`pump-and-dump`/`scam`/`rigged`/`ponzi` or a
   substring of them.
2. **Bare "suspicious," uncoupled from a score/rank/rating word** — `RANKING_PATTERNS` only fires
   when `suspicious`/`manipulat*`/`fraud*` co-occurs with `score`/`rank`/`rating`/`index`/`out of
   10` within 40 characters. "This activity is highly suspicious," stated flatly with no numeric
   ranking nearby, is a bare conclusion of exactly the shape CLAUDE.md's own example ("This is a
   pump" is defamation) targets, and is not caught.
3. **CLAUDE.md invariant 12's SECOND half is not covered by this module at all**: "No buy/sell/
   hold, no targets, no ratings" is a distinct requirement from the manipulation-conclusion ban, and
   `banned_terms.py`'s docstring frames its whole scope around invariant 12's manipulation clause
   only. "Strong buy," "recommend selling," "price target of INR 500," and "investors should be
   cautious" all violate the plain text of invariant 12 and are not lint targets at all currently —
   not a narrow miss inside an existing detector, a whole clause of the invariant with no detector
   family assigned to it.

**Not applied as a fix here — reported for approval, consistent with this project's own working
procedure (plan, then implement only after approval) for anything touching a safety-critical
module.** Logged as `P8-003` below (grouped with the code-currency finding, both code changes
awaiting approval rather than applied unilaterally in a documentation-and-audit pass).

## 2. README.md

This project had no top-level `README.md` — confirmed by direct listing, not assumed. Written and
described in §4 below (published as its own file, not duplicated into this doc).

## 3. Data and legal hygiene

**`.gitignore`** already covers the real risk surface: `data/raw/`, `data/processed/` (1.4GB,
including `praman.db`, a 1.36GB sqlite file that must never be committed), `*.db`, `.env`,
`__pycache__/`, `*.pyc`, `.pytest_cache/`. Confirmed via `git ls-files | grep '^data/'` returning
zero rows — no data file has ever been tracked, not merely "currently ignored."

**Secrets:** `grep -rIlE "api[_-]?key|secret|password|token\s*="` across `src/`/`scripts/` returns
one hit, `src/config/settings.py`, and it is the module's own docstring ("frozen dataclass, no
secrets in code") — a false positive from the grep pattern, not a real secret. No `.env` or
credentials file is tracked.

**Banned constructs:** zero `TODO`/`FIXME` comments and zero `pickle`/`eval(`/`exec(` usages
anywhere in `src/` — both explicitly banned by `CLAUDE.md` invariant 5, both clean.

**Legal posture (NSE/SEBI scraping)** is already stated explicitly and consistently in
`praman/CLAUDE.md`'s "Data sourcing" section (a knowing, disclosed decision, not a silent default,
scoped to research/personal use) — this review did not find a second, inconsistent statement of it
anywhere else that would need reconciling. The new `README.md` (§4) links to that section rather
than restating it, so there remains exactly one place this decision is recorded.

## 4. Register consistency

Verified directly, not assumed: **23 table rows, 19 `##` sections** in `DEFECT_REGISTER.md`. The
gap (4) is exactly the established "Low severity, Known-deferred = row only, no full section"
convention already in use before this session (`P3-001`/`P3-002`/`P3-003`) — `P8-002` (this
session's own Low-severity, self-contained finding) follows the same convention correctly. IDs are
sequential within each phase prefix with no gaps or duplicates. One inconsistency found and fixed:
`P8-001`'s table-row Status column did not lead with a status word the way every other row does
("Fixed — ...", "Known-deferred — ...") — reworded to "Corrected, not silently fixed — headline
retracted. See ..." for consistency.

---

## Findings queued for approval (not applied in this pass)

### `P8-003` — production code still states the withdrawn AUC ceiling as current fact

`src/classification/event_classifier.py`'s `PROVENANCE_NOTE` (line 16, rendered into every report's
narrative) and `DISCRIMINATIVE_POWER_NOTE` (line 66, rendered standalone next to every
classification) both state **"Phase 6 measured the combined signal ceiling at 0.611-0.70 held out
on 2025-2026 data"** — the exact figure `docs/phase6_signals.md`'s own dated correction and
`docs/RESULTS.md` §4 now mark WITHDRAWN (`P8-001`; the ceiling's two dominant features reverse sign
under a decoupled label, `docs/phase8b_clean_label_features.md` item 3). Every report this system
generates today cites a number this project's own documentation no longer stands behind. This is a
factual-accuracy issue in a live, defamation-adjacent-invariant-bearing code path (CLAUDE.md
invariant 12), not a documentation gap — queued for explicit approval before editing, per this
project's working procedure, rather than patched silently inside an audit pass.

### `P8-003` (same entry) — `banned_terms.py` coverage gaps found by §1's adversarial pass

Three concrete, evidenced gaps (vocabulary outside `DIRECT_TERMS`, bare "suspicious," and the
entirely-uncovered buy/sell/hold/target clause of invariant 12) — full detail in §1. Also queued
for approval before any pattern is added, since this module gates defamation-risk output and a
change to it should go through the same review any other change to it would.
