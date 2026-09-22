# Praman

A forensic classifier for unusual price moves on the NSE (India's National Stock Exchange). Given
a stock that moved sharply, Praman determines whether the move has an informational basis (a
disclosure that plausibly explains it) or carries manipulation-*consistent* signatures — and tries
to prove that classification against SEBI enforcement history, exchange surveillance flags, and
subsequent price behaviour, rather than merely asserting it.

**Praman never states a conclusion about manipulation.** Its output is measured signals and their
values — "delivery 11% on 14x average volume; no disclosure in the preceding 10 sessions" is a
fact it will report; "this is a pump" is a conclusion it is built not to state. See
[`CLAUDE.md`](CLAUDE.md) invariant 12 for why, and [`src/agent/banned_terms.py`](src/agent/banned_terms.py)
for the mechanical lint that enforces it on every piece of generated text.

## Status, read before trusting any number

**The project's own headline result was retracted by its own robustness review.** Phase 8's
evaluation initially reported that the classifier's top-tier precision cleared disclosure-tier-alone's
with non-overlapping confidence intervals. A pre-registered follow-up check
(`docs/phase8_robustness_checks.md`, logged as `P8-001` in [`docs/DEFECT_REGISTER.md`](docs/DEFECT_REGISTER.md))
found that result was driven by a mechanical coupling between the outcome label and the
classifier's own momentum input, not by genuine predictive signal — under a label that removes the
coupling, neither disclosure tier nor the classifier shows top-tier lift over its own base rate.

**Start here, in this order, if you're new to this codebase:**

1. [`docs/RESULTS.md`](docs/RESULTS.md) — the one document meant to travel. Leads with the
   retraction above, not the original (now-superseded) headline.
2. [`docs/DEFECT_REGISTER.md`](docs/DEFECT_REGISTER.md) — every defect this project has found in
   itself, including ones in its own evaluation methodology, with root cause and re-verification
   evidence. `P8-003` (open) lists two known, not-yet-fixed issues: production report text still
   citing a withdrawn ceiling figure, and real coverage gaps in the manipulation-language lint.
3. [`docs/phase10_preregistration.md`](docs/phase10_preregistration.md) — the frozen spec for
   whatever redesign follows, committed before any forward evaluation data exists.
4. [`CLAUDE.md`](CLAUDE.md) — the project's own working invariants, data-sourcing decisions (including
   the disclosed, knowing decision to scrape nseindia.com against its Terms of Use, for research/
   personal use only), and recurring-failure-mode notes. Binding on any future work in this repo.

Phase-by-phase detail (data ingestion, event cataloguing, feature measurement, classification
design, the multi-agent evidence layer, and the full evaluation) lives in `docs/phase1_*.md`
through `docs/phase8b_*.md`, in order.

## What this is not

- Not investment advice. No buy/sell/hold, no price targets, no ratings — CLAUDE.md invariant 12,
  enforced (imperfectly — see `P8-003`) by `src/agent/banned_terms.py`.
- Not a validated predictor. Every report renders its own measured discriminative-power ceiling
  and limitations alongside its classification, not in a footnote.
- Not redistributable data. `data/raw/` and `data/processed/` are gitignored on purpose — the NSE
  and SEBI data this project depends on is scraped under a disclosed ToS exception scoped to
  research/personal use, not for redistribution (`CLAUDE.md`, "Data sourcing").

## Setup

```
pip install -r requirements.txt
```

Python dependencies: `jugaad-data` (NSE bhavcopy/ASM/GSM access), `requests` + `beautifulsoup4` +
`pdfplumber` (SEBI order scraping/PDF extraction), `pandas`, `pydantic`, `mcp`.

The bitemporal store is a local sqlite file, path configurable via `PRAMAN_DATABASE_PATH`
(default: `data/processed/praman.db` — see `src/config/settings.py`). It is not checked in; running
the ingestion scripts under `scripts/` builds it from scratch. Full price/volume/delivery history
starts 2019-10-01 — see `CLAUDE.md`'s "Data sourcing" section for why no earlier date is usable.

## Tests

```
pytest tests/
```

26 test files under `tests/`, covering the bitemporal store, ingestion parsers, the event
catalogue, classification rules, and the manipulation-language lint.

## Architecture, in one paragraph

Every fact carries an event date and a knowledge date; every query is as-of a specific date
(`CLAUDE.md` invariant 7 — "bitemporal or nothing"). Corporate-action adjustment, event
cataloguing, and outcome labelling all respect this. The classifier itself is deterministic by
default (`src/classification/event_classifier.py`); an optional multi-agent LLM layer
(`src/agent/`) writes narrative around the same deterministic rule and is re-checked by a
deterministic Adversary and the banned-term lint before anything reaches output — the system
produces complete, grounded output with no language model configured at all.
