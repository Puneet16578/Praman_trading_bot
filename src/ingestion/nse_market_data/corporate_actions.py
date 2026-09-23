"""NSE corporate-actions ingestion: bonus issues and stock splits, tiered by knowledge_date
confidence. Demergers and capital reductions are ingested separately, as exclusion markers only
(see CLAUDE.md's "demergers are unadjustable" scope boundary) -- they never get a ratio or a tier
from this scheme. These are two distinct, accurately-labeled real action types (DEMERGER,
CAPITAL_REDUCTION), not one type standing in for the other -- both share the same underlying
reason for exclusion (a real, structural, mechanical price-level break for which NSE discloses no
adjustment ratio at announcement time; see is_capital_reduction_subject's docstring and
docs/phase5_event_catalogue.md Sec.4j for why "no disclosed ratio" is the actual shared criterion,
not "is a demerger" specifically), but action_type always records what actually happened, never
which one it was excluded alongside.

Two NSE endpoints, neither individually sufficient (found and measured during Phase 3 source
evaluation, this session's transcript):
- `corporates-corporateActions`: clean, structured ratio in `subject` (e.g. "Bonus 1:3"), but its
  `caBroadcastDate` field is null on every row checked -- no reliable announcement date.
- `corporate-announcements`: precise, real disclosure timestamps (`sort_date`), but its own
  free-text ratio is auto-generated and can itself be wrong (verified against the actual filed
  PDF for AURIGROW: `subject` said "1:1" and was correct; the announcement's auto-text said
  "11104000:111040000" and was wrong -- a stray extra zero, not a company filing error).

Design conclusion from that verification: `subject` is the ratio's source of truth; the
announcement is the knowledge_date's source of truth; the announcement's own parsed ratio is
corroboration only, never the primary number. The four-tier `confidence_tier` scheme below makes
that conclusion explicit and queryable per row, rather than a design note nobody enforces.
"""
from __future__ import annotations
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Callable

import requests

from ...bitemporal.store import write_facts

CONFIRMED = "CONFIRMED"
MATCHED_UNCONFIRMED = "MATCHED_UNCONFIRMED"
EX_DATE_FALLBACK = "EX_DATE_FALLBACK"
QUARANTINE = "QUARANTINE"  # never written to the store -- logged only
DEMERGER_EXCLUSION = "DEMERGER_EXCLUSION"  # not part of the confidence scheme; see module docstring
CAPITAL_REDUCTION_EXCLUSION = "CAPITAL_REDUCTION_EXCLUSION"  # same handling as DEMERGER_EXCLUSION
                                                              # (no ratio, excluded not adjusted),
                                                              # named for its own action_type so a
                                                              # capital-reduction row never carries
                                                              # a demerger-shaped tier

BONUS = "BONUS"
SPLIT = "SPLIT"
DEMERGER = "DEMERGER"
CAPITAL_REDUCTION = "CAPITAL_REDUCTION"
RIGHTS = "RIGHTS"              # P8-007 corrections: a real action type, previously silently
                                # folded into "unhandled" alongside dividends/AGMs/etc.
RATIO_CONFLICT = "RATIO_CONFLICT"  # P8-007 corrections: what QUARANTINE bonus/split rows become
                                    # once written (see build_rows_and_report) -- a real bonus/
                                    # split happened, but the subject and announcement ratios
                                    # disagree, so no ratio is trusted enough to adjust by

RIGHTS_EXCLUSION = "RIGHTS_EXCLUSION"          # own tier name, mirrors DEMERGER_EXCLUSION
RATIO_CONFLICT_EXCLUSION = "RATIO_CONFLICT_EXCLUSION"  # own tier name, mirrors DEMERGER_EXCLUSION

# P8-009 root-cause fix: action types with no adjustment factor -- single source of truth for
# BOTH event_catalogue.py's vectorized fast path (STRUCTURAL_BREAK_ACTION_TYPES) and
# price_adjustment.py's per-pair-verified slow path (UNADJUSTABLE_ACTION_TYPES). These used to be
# two independently hand-mirrored tuples; adding RIGHTS/RATIO_CONFLICT to only one of them (the
# original P8-007 corrections change) silently left the other checking a stale, incomplete list.
# Both modules now import this single tuple instead of redefining their own copy, so the two
# cannot drift apart again by construction, not by discipline.
STRUCTURAL_BREAK_ACTION_TYPES = (DEMERGER, CAPITAL_REDUCTION, RIGHTS, RATIO_CONFLICT)

# Measured from the 253 cases where v1 (earliest-in-a-200-day-window) matching agreed with
# `subject` -- see docs/phase3_corporate_actions.md for the full distribution
# (min=28, median=44, p95=65, max=121). A matched announcement whose gap to the ex-date falls
# outside this range doesn't look like a normal board-to-ex-date sequence and is downgraded to
# EX_DATE_FALLBACK rather than trusted.
MIN_GAP_DAYS = 28
MAX_GAP_DAYS = 121
MATCH_WINDOW_DAYS = 121  # covers the measured max; the fetch window (below) is wider, for margin
FETCH_WINDOW_DAYS = 200

DEFERRED_PATTERNS = [
    r"\bdeferred\b", r"propose to consider", r"scheduled to consider",
    r"will also consider", r"is scheduled to be held.{0,40}to consider",
    r"shall.{0,20}also consider", r"in their meeting scheduled",
]
DEFERRED_RE = re.compile("|".join(DEFERRED_PATTERNS), re.I)

# ---------- Parsers ----------

def parse_subject_ratio(subject: str) -> dict | None:
    """P8-007 corrections (docs/phase10_p8007_corrections.md): the Bonus pattern used to require
    `\\s+` immediately after "Bonus", missing the real, hyphen-attached NSE phrasing "Bonus- 1:2"
    (confirmed live: AJANTPHARM, 2022-06-22). Widened to `[\\s\\-:.]*` -- any combination of
    whitespace, hyphen, colon, or period between "Bonus" and the ratio's first digit -- so it
    still matches the plain "Bonus 1:2" form and also "Bonus-1:2", "Bonus- 1:2", "Bonus:1:2"."""
    s = (subject or "").strip()
    m = re.search(r"\bBonus[\s\-:.]*(\d+)\s*:\s*(\d+)\b", s, re.I)
    if m:
        new, old = int(m.group(1)), int(m.group(2))
        return {"type": BONUS, "numerator": float(new), "denominator": float(old), "factor": (new + old) / old, "raw": f"{new}:{old}"}
    m = re.search(r"From\s*(?:Rs\.?|Re\.?)\s*(\d+(?:\.\d+)?)\s*/?-?\s*Per Share\s*To\s*(?:Rs\.?|Re\.?)\s*(\d+(?:\.\d+)?)\s*/?-?\s*Per Share", s, re.I)
    if m:
        old_fv, new_fv = float(m.group(1)), float(m.group(2))
        return {"type": SPLIT, "numerator": old_fv, "denominator": new_fv, "factor": old_fv / new_fv, "raw": f"{old_fv}->{new_fv}"}
    return None

# Explicit, enumerated exceptions -- NOT a general pattern -- for real demergers whose NSE subject
# text has no safe generalizable substring. "Scheme Of Arrangement" was considered and rejected as
# a general pattern: it also matches real, ratio-bearing, non-demerger actions in this same store
# (e.g. "Scheme Of Arrangement - Bonus Ncrps 4:1" for RADIOCITY/TVSMOTOR/SIYSIL/TVSHLTD), so
# widening the substring would misclassify those as unadjustable demergers instead of leaving them
# correctly unhandled. Confirmed real demergers (docs/phase5_event_catalogue.md Sec.4d/4e),
# externally verified: IIFL Holdings' 2019 three-way split, and the KPIT/Birlasoft composite
# scheme's demerger-of-engineering-business component. Both predate bhavcopy's own data start
# (2019-10-01) and are therefore currently inert for every computed number in this project --
# recorded for completeness and in case the ingested history is ever extended backward.
_KNOWN_DEMERGER_EXCEPTIONS: frozenset[tuple[str, str]] = frozenset({
    ("IIFL", "2019-05-30"),
    ("BSOFT", "2019-01-24"),
})

def is_demerger_subject(subject: str, symbol: str | None = None, ex_date: str | None = None) -> bool:
    """`symbol`/`ex_date` are optional and only consulted against the enumerated exception list
    above -- every other case is decided purely from `subject` text, unchanged from before.
    Deliberately narrow: "demerger" (the vast majority, all 90 currently-detected real cases) and
    the hyphenated "de-merger"/"de merger" variant (TTML, 2019-07-11 -- the one real, safely
    generalizable phrasing gap found by direct audit; occurs exactly once in the full 17,827-row
    raw source, docs/phase5_event_catalogue.md Sec.4e). Does NOT match "reduction of capital" --
    that is a distinct real action type with its own accurate label; see
    is_capital_reduction_subject below, not folded in here."""
    s = (subject or "").lower()
    if "demerger" in s or "de-merger" in s or "de merger" in s:
        return True
    if symbol is not None and ex_date is not None and (symbol, ex_date) in _KNOWN_DEMERGER_EXCEPTIONS:
        return True
    return False

def is_rights_subject(subject: str) -> bool:
    """P8-007 corrections: a Rights issue (confirmed real case: M&MFIN, 2020-07-22,
    "Rights 1:1 @ Premium Rs 48/-") is a distinct, real action type -- it has a disclosed ratio,
    but adjusting for a rights issue is a different, more complex mechanism than a bonus/split's
    simple multiplicative factor (it depends on the ratio AND the subscription premium, and on
    theoretical ex-rights price, not on the ratio alone). Not attempted here: like a demerger,
    treated conservatively as a structural-break EXCLUSION MARKER (no ratio, no factor) rather
    than guessed at. Checked to not overmatch: this endpoint's subjects are corporate-action
    labels ("Rights X:Y @ Premium Rs Z/-"), not general prose, so a bare "rights" substring check
    is safe here -- it does not need to exclude something like "voting rights" language the way a
    free-text disclosure body might."""
    return "rights" in (subject or "").lower()

def is_capital_reduction_subject(subject: str) -> bool:
    """A capital reduction -- shares extinguished or face value cut, whether to return value to
    shareholders, write off accumulated losses, or (per a share-swap capital reduction) transfer
    value out to another entity's shareholders -- is unadjustable for the same underlying reason
    a demerger is: NSE discloses no ratio for it, because none is fixed at announcement time in
    the way a bonus/split ratio is (docs/phase5_event_catalogue.md Sec.4j). Deliberately a
    SEPARATE classifier from is_demerger_subject, not folded into it: a capital reduction is a
    real, distinct action type (recorded as CAPITAL_REDUCTION, never mislabeled DEMERGER) that
    happens to need the same exclude-don't-adjust treatment. Checked directly against the full
    17,827-row raw source before being enabled: exactly 3 real rows anywhere in this project's
    ingested data use this phrase (MAXIND 2022-07-26, MELSTAR 2024-08-16, EASTSILK 2024-11-22) --
    low enough that even if none of the three specific historical cases were demergers or
    share-swaps, the over-exclusion cost of matching this phrase generally is negligible."""
    s = (subject or "").lower()
    return "reduction of capital" in s or "capital reduction" in s

def parse_announcement_ratio(text: str, hint: str) -> dict | None:
    """Corroboration only -- see module docstring. Never the source of the stored ratio."""
    if hint == BONUS:
        matches = re.findall(r"(?:in the proportion of|in the ratio of|at the ratio of|in the ration of)\s*(\d+)\s*:\s*(\d+)", text, re.I)
        if not matches:
            return None
        factors = {(int(n), int(o)): (int(n) + int(o)) / int(o) for n, o in matches}
        if len(set(factors.values())) > 1:
            return {"factor": None, "raw": "AMBIGUOUS:" + str(matches)}
        (n, o), factor = next(iter(factors.items()))
        return {"factor": factor, "raw": f"{n}:{o}"}

    if hint == SPLIT:
        matches = re.findall(
            r"subdivision\s*(?:/\s*split)?\s*of\s*([\d,]+)\s*equity shares?\s*(?:\([^)]*\)\s*)?of\s*(?:Rs\.?|Re\.?)?\s*(\d+(?:\.\d+)?)\s*each\s*into\s*([\d,]+)\s*equity shares?\s*(?:\([^)]*\)\s*)?of\s*(?:Rs\.?|Re\.?)?\s*(\d+(?:\.\d+)?)\s*each",
            text, re.I)
        if matches:
            results = set()
            for n1, fv1, n2, fv2 in matches:
                n1, n2, fv1, fv2 = int(n1.replace(",", "")), int(n2.replace(",", "")), float(fv1), float(fv2)
                if n1 == 0 or fv2 == 0:
                    return {"factor": None, "raw": f"DEGENERATE n1={n1} fv2={fv2}"}
                factor_by_count = round(n2 / n1, 6)
                factor_by_fv = round(fv1 / fv2, 6)
                if abs(factor_by_count - factor_by_fv) > 0.001:
                    return {"factor": None, "raw": f"INTERNAL_MISMATCH count={factor_by_count} fv={factor_by_fv}"}
                results.add(factor_by_fv)
            if len(results) > 1:
                return {"factor": None, "raw": "AMBIGUOUS:" + str(matches)}
            return {"factor": next(iter(results)), "raw": str(matches[0])}

        fv_matches = re.findall(
            r"face value of\s*(?:Rs\.?|Re\.?)\s*(\d+(?:\.\d+)?)\s*/?-?\s*each.{0,60}?(?:to|into).{0,60}?face value of\s*(?:Rs\.?|Re\.?)\s*(\d+(?:\.\d+)?)\s*/?-?\s*each",
            text, re.I)
        if fv_matches:
            results = {round(float(fv1) / float(fv2), 6) for fv1, fv2 in fv_matches}
            if len(results) > 1:
                return {"factor": None, "raw": "AMBIGUOUS_FV:" + str(fv_matches)}
            return {"factor": next(iter(results)), "raw": f"FV:{fv_matches[0]}"}
        return None
    return None

def is_deferred_text(text: str) -> bool:
    return bool(DEFERRED_RE.search(text or ""))

# ---------- Matching (closest-preceding, cluster-collapsed, deferred-filtered) ----------

def collapse_clusters(matches: list[dict]) -> list[dict]:
    """Same-type announcements for one symbol within 1 hour of each other are one same-session
    correction cluster; only the latest survives. Confirmed real case: KITEX published a bonus
    ratio of "2:2" then corrected it to "2:1" 38 seconds later -- the correction, not the typo, is
    what actually became public and must be what knowledge_date reflects."""
    if not matches:
        return matches
    ordered = sorted(matches, key=lambda r: r.get("sort_date", ""))
    clusters: list[list[dict]] = [[ordered[0]]]
    for m in ordered[1:]:
        prev = clusters[-1][-1]
        t1 = datetime.strptime(prev["sort_date"], "%Y-%m-%d %H:%M:%S")
        t2 = datetime.strptime(m["sort_date"], "%Y-%m-%d %H:%M:%S")
        if (t2 - t1) <= timedelta(hours=1):
            clusters[-1].append(m)
        else:
            clusters.append([m])
    return [cluster[-1] for cluster in clusters]

def find_announcement(announcements: list[dict], ex_date: date, action_type: str) -> tuple[dict | None, int | None]:
    """Returns (matched_announcement_or_None, gap_days_or_None). `announcements` is the already-
    fetched (up to FETCH_WINDOW_DAYS before ex_date) raw list for one symbol; this function applies
    no network access, only in-memory filtering -- confirmed real case: UEL ran two separate bonus
    rounds four months apart, and a naive earliest-in-window match grabbed the wrong one; closest-
    preceding-the-ex-date fixes it.
    """
    desc_wanted = "bonus" if action_type == BONUS else "stock split"
    raw_matches = [row for row in announcements if (row.get("desc") or "").strip().lower() == desc_wanted]
    if not raw_matches:
        return None, None

    collapsed = collapse_clusters(raw_matches)
    match_floor = ex_date - timedelta(days=MATCH_WINDOW_DAYS)
    candidates = []
    for m in collapsed:
        ann_dt = datetime.strptime(m["sort_date"], "%Y-%m-%d %H:%M:%S")
        if ann_dt.date() > ex_date or ann_dt.date() < match_floor:
            continue
        if is_deferred_text(m.get("attchmntText", "") or ""):
            continue
        candidates.append((ann_dt, m))
    if not candidates:
        return None, None
    candidates.sort(key=lambda pair: pair[0])
    best_dt, best = candidates[-1]
    return best, (ex_date - best_dt.date()).days

# ---------- Tiering ----------

@dataclass(frozen=True)
class ClassificationResult:
    tier: str
    knowledge_date: str  # ISO date
    gap_days: int | None
    downgraded_for_gap: bool
    subject_ratio_raw: str
    announcement_ratio_raw: str | None

def classify_bonus_split(subj_parsed: dict, ex_date: date, announcements: list[dict]) -> ClassificationResult:
    ann_match, gap_days = find_announcement(announcements, ex_date, subj_parsed["type"])

    if ann_match is None:
        return ClassificationResult(EX_DATE_FALLBACK, ex_date.isoformat(), None, False, subj_parsed["raw"], None)

    if not (MIN_GAP_DAYS <= gap_days <= MAX_GAP_DAYS):
        return ClassificationResult(EX_DATE_FALLBACK, ex_date.isoformat(), gap_days, True, subj_parsed["raw"], None)

    knowledge_date = ann_match["sort_date"][:10]
    ann_parsed = parse_announcement_ratio(ann_match.get("attchmntText", "") or "", subj_parsed["type"])
    if ann_parsed is not None and ann_parsed.get("factor") is not None:
        if abs(ann_parsed["factor"] - subj_parsed["factor"]) <= 0.001:
            return ClassificationResult(CONFIRMED, knowledge_date, gap_days, False, subj_parsed["raw"], ann_parsed["raw"])
        return ClassificationResult(QUARANTINE, knowledge_date, gap_days, False, subj_parsed["raw"], ann_parsed["raw"])

    return ClassificationResult(MATCHED_UNCONFIRMED, knowledge_date, gap_days, False, subj_parsed["raw"],
                                 ann_parsed["raw"] if ann_parsed else None)

# ---------- Row construction + bulk ingestion ----------

@dataclass
class IngestionReport:
    tier_counts: dict[str, int]
    downgraded_count: int
    quarantined: list[dict]  # not written; logged for review
    unhandled_action_types: int  # dividends, buybacks, AGMs, mergers-other-than-demerger, etc. --
                                  # out of scope this session. Rights issues moved OUT of this
                                  # bucket in P8-007 corrections -- see is_rights_subject -- since
                                  # they get their own exclusion-marker handling now, not a silent
                                  # count alongside truly no-adjustment-needed types like dividends.

def announcement_cache_key(symbol: str, ex_date: date) -> str:
    """A symbol with two separate bonus/split rounds needs two separate announcement windows --
    keying by symbol alone would risk anchoring a 200-day fetch window to the wrong ex_date and
    missing an earlier round's announcement entirely (this is exactly the UEL failure mode the
    matching logic was built to avoid; the cache key must not reintroduce it one level up)."""
    return f"{symbol}|{ex_date.isoformat()}"

def resolve_isin_symbol(raw_symbol: str, ex_date: date, candidate_date_ranges: dict[str, tuple[str, str]]) -> str:
    """P8-010 fix: NSE's live corporate-actions endpoint reports a security's entire history under
    its CURRENT symbol string, retroactively -- not the symbol actually in effect on `ex_date`
    (confirmed real case: HEG renamed to HEGAM around 2026-09-07; every HEGAM-labeled action,
    including a 2019 buyback, shares HEG's own ISIN). `candidate_date_ranges` is this ISIN's known
    symbols, each mapped to its own real EQ bhavcopy (first, last) trading-date range -- returns
    whichever candidate's window actually covers `ex_date`, i.e. the symbol this project's OWN
    price series needs the action filed under to be usable. Falls back to `raw_symbol` unchanged
    if no candidate's window covers it (including single-symbol ISINs, where this is a safe
    no-op, not a guess)."""
    ex_iso = ex_date.isoformat()
    for symbol, (lo, hi) in candidate_date_ranges.items():
        if lo <= ex_iso <= hi:
            return symbol
    return raw_symbol

def build_isin_candidates_for_actions(conn, actions: list[dict], isin_map: dict[str, str]) -> dict[str, dict[str, tuple[str, str]]]:
    """DB-touching wrapper for `resolve_isin_symbol`: for every ISIN actually present in `actions`
    that `isin_map` (see `src/ingestion/nse_market_data/isin_mapping.py`) resolves to more than one
    symbol, fetch each candidate symbol's own real EQ bhavcopy date range. Only queries the ISINs
    actually needed, not the whole map -- cheap even for a full historical sweep. Not called by
    `build_rows_and_report` itself (which stays a pure function); callers that touch the DB
    (`ingest_corporate_actions`) compute this once and pass it through."""
    by_isin: dict[str, set[str]] = defaultdict(set)
    for symbol, isin in isin_map.items():
        by_isin[isin].add(symbol)

    isins_needed = {a.get("isin") for a in actions if a.get("isin")}
    multi_symbol_isins = {isin: symbols for isin, symbols in by_isin.items()
                           if isin in isins_needed and len(symbols) > 1}
    if not multi_symbol_isins:
        return {}

    all_candidate_symbols = sorted({s for symbols in multi_symbol_isins.values() for s in symbols})
    placeholders = ",".join("?" * len(all_candidate_symbols))
    rows = conn.execute(
        f"SELECT symbol, MIN(event_date) lo, MAX(event_date) hi FROM bhavcopy "
        f"WHERE series='EQ' AND symbol IN ({placeholders}) GROUP BY symbol",
        tuple(all_candidate_symbols),
    ).fetchall()
    date_ranges = {r["symbol"]: (r["lo"], r["hi"]) for r in rows}

    return {isin: {s: date_ranges[s] for s in symbols if s in date_ranges}
            for isin, symbols in multi_symbol_isins.items()}

def build_rows_and_report(actions: list[dict], announcements_by_key: dict[str, list[dict]], source_file: str,
                           isin_candidates: dict[str, dict[str, tuple[str, str]]] | None = None) -> tuple[list[dict], IngestionReport]:
    """Pure function: no I/O. `announcements_by_key` must already contain, for every bonus/split
    action, the fetched announcement window keyed by `announcement_cache_key(symbol, ex_date)`
    (see `fetch_all`). `isin_candidates` (from `build_isin_candidates_for_actions`, optional,
    default None = no resolution attempted -- identical behavior to before P8-010) resolves a raw
    action's reported symbol to whichever same-ISIN symbol was actually trading on its ex_date."""
    rows = []
    tier_counts: dict[str, int] = {}
    quarantined = []
    downgraded = 0
    unhandled = 0
    isin_candidates = isin_candidates or {}

    for action in actions:
        if action.get("series") != "EQ":
            continue
        symbol = action["symbol"]
        ex_date = datetime.strptime(action["exDate"], "%d-%b-%Y").date()
        isin = action.get("isin")
        if isin and isin in isin_candidates:
            symbol = resolve_isin_symbol(symbol, ex_date, isin_candidates[isin])
        subject = action.get("subject", "") or ""

        if is_demerger_subject(subject, symbol=symbol, ex_date=ex_date.isoformat()):
            rows.append({
                "symbol": symbol, "action_type": DEMERGER, "event_date": ex_date.isoformat(),
                "knowledge_date": ex_date.isoformat(),  # no reliable announcement path exists; see CLAUDE.md
                "ratio_numerator": None, "ratio_denominator": None,
                "confidence_tier": DEMERGER_EXCLUSION, "details": subject.strip(), "source_file": source_file,
            })
            tier_counts[DEMERGER_EXCLUSION] = tier_counts.get(DEMERGER_EXCLUSION, 0) + 1
            continue

        if is_capital_reduction_subject(subject):
            rows.append({
                "symbol": symbol, "action_type": CAPITAL_REDUCTION, "event_date": ex_date.isoformat(),
                "knowledge_date": ex_date.isoformat(),  # no reliable announcement path exists; see CLAUDE.md
                "ratio_numerator": None, "ratio_denominator": None,
                "confidence_tier": CAPITAL_REDUCTION_EXCLUSION, "details": subject.strip(), "source_file": source_file,
            })
            tier_counts[CAPITAL_REDUCTION_EXCLUSION] = tier_counts.get(CAPITAL_REDUCTION_EXCLUSION, 0) + 1
            continue

        # P8-007 corrections (docs/phase10_p8007_corrections.md): a Rights issue has a disclosed
        # ratio, but this project does not attempt rights-issue price adjustment (a different,
        # more complex mechanism than a bonus/split factor -- see is_rights_subject). Previously
        # silently counted as "unhandled" alongside dividends/AGMs, which need no exclusion at
        # all; now written as its own structural-break exclusion marker, same treatment as a
        # demerger, so the price series does not read a real rights-related move as an unexplained
        # crash while also not silently vanishing from the record.
        if is_rights_subject(subject):
            rows.append({
                "symbol": symbol, "action_type": RIGHTS, "event_date": ex_date.isoformat(),
                "knowledge_date": ex_date.isoformat(),
                "ratio_numerator": None, "ratio_denominator": None,
                "confidence_tier": RIGHTS_EXCLUSION, "details": subject.strip(), "source_file": source_file,
            })
            tier_counts[RIGHTS_EXCLUSION] = tier_counts.get(RIGHTS_EXCLUSION, 0) + 1
            continue

        subj_parsed = parse_subject_ratio(subject)
        if subj_parsed is None:
            unhandled += 1
            continue

        key = announcement_cache_key(symbol, ex_date)
        result = classify_bonus_split(subj_parsed, ex_date, announcements_by_key.get(key, []))

        # P8-007 corrections: QUARANTINE used to mean "never written" -- a real bonus/split DID
        # happen (the subject and announcement simply disagree on the exact ratio), and dropping
        # it entirely left the price series reading a real corporate action as an unexplained
        # crash (confirmed real case: UNIVASTU, 2025-10-13, "Bonus 2:1" vs. the announcement's own
        # garbled auto-parsed ratio "25357180:11995590" -- the same auto-text-quality problem this
        # module's own docstring already documents for AURIGROW). Still logged in `quarantined`
        # for review (unchanged), but now ALSO written as a structural-break exclusion marker
        # under its own action_type (RATIO_CONFLICT) rather than silently vanishing.
        if result.tier == QUARANTINE:
            quarantined.append({
                "symbol": symbol, "ex_date": ex_date.isoformat(), "action_type": subj_parsed["type"],
                "subject_raw": result.subject_ratio_raw, "announcement_raw": result.announcement_ratio_raw,
                "knowledge_date": result.knowledge_date,
            })
            rows.append({
                "symbol": symbol, "action_type": RATIO_CONFLICT, "event_date": ex_date.isoformat(),
                "knowledge_date": result.knowledge_date,
                "ratio_numerator": None, "ratio_denominator": None,
                "confidence_tier": RATIO_CONFLICT_EXCLUSION,
                "details": f"subject={result.subject_ratio_raw} announcement={result.announcement_ratio_raw}",
                "source_file": source_file,
            })
            tier_counts[RATIO_CONFLICT_EXCLUSION] = tier_counts.get(RATIO_CONFLICT_EXCLUSION, 0) + 1
            continue

        tier_counts[result.tier] = tier_counts.get(result.tier, 0) + 1

        if result.downgraded_for_gap:
            downgraded += 1

        rows.append({
            "symbol": symbol, "action_type": subj_parsed["type"], "event_date": ex_date.isoformat(),
            "knowledge_date": result.knowledge_date,
            "ratio_numerator": subj_parsed["numerator"], "ratio_denominator": subj_parsed["denominator"],
            "confidence_tier": result.tier, "details": subject.strip(), "source_file": source_file,
        })

    report = IngestionReport(tier_counts=tier_counts, downgraded_count=downgraded,
                              quarantined=quarantined, unhandled_action_types=unhandled)
    return rows, report

def ingest_corporate_actions(conn, actions: list[dict], announcements_by_key: dict[str, list[dict]], source_file: str,
                              isin_map: dict[str, str] | None = None) -> tuple[IngestionReport, object]:
    """Builds rows (pure), then writes them through the Phase 1 store -- the only write path,
    same as bhavcopy. QUARANTINE rows are never passed to `write_facts`. `isin_map` (P8-010,
    optional, default None = no resolution attempted) enables ISIN-based symbol resolution for
    renamed securities -- see `build_isin_candidates_for_actions`/`resolve_isin_symbol`."""
    isin_candidates = build_isin_candidates_for_actions(conn, actions, isin_map) if isin_map else None
    rows, report = build_rows_and_report(actions, announcements_by_key, source_file, isin_candidates=isin_candidates)
    if not rows:
        from ...bitemporal.store import BulkWriteResult
        return report, BulkWriteResult(inserted=0, skipped_duplicate=0)
    result = write_facts(conn, "corporate_actions", rows)
    return report, result

# ---------- Real network fetch (not used by the fixture-based test suite) ----------

def _session_with_cookie(timeout: float = 20.0) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "application/json",
    })
    session.get("https://www.nseindia.com", timeout=timeout)
    return session

def _fetch_corporate_actions_range(session: requests.Session, from_date: date, to_date: date, timeout: float = 30.0) -> list[dict]:
    r = session.get("https://www.nseindia.com/api/corporates-corporateActions",
                     params={"index": "equities", "from_date": from_date.strftime("%d-%m-%Y"), "to_date": to_date.strftime("%d-%m-%Y")},
                     timeout=timeout)
    r.raise_for_status()
    return r.json()

def fetch_corporate_actions_year(session: requests.Session, year: int, timeout: float = 30.0) -> list[dict]:
    return _fetch_corporate_actions_range(session, date(year, 1, 1), date(year, 12, 31), timeout)

def fetch_announcements_window(session: requests.Session, symbol: str, ex_date: date, timeout: float = 25.0) -> list[dict]:
    from_date = (ex_date - timedelta(days=FETCH_WINDOW_DAYS)).strftime("%d-%m-%Y")
    to_date = ex_date.strftime("%d-%m-%Y")
    r = session.get("https://www.nseindia.com/api/corporate-announcements",
                     params={"index": "equities", "symbol": symbol, "from_date": from_date, "to_date": to_date}, timeout=timeout)
    if r.status_code != 200:
        return []
    return r.json()

def _fetch_announcements_for_actions(session: requests.Session, actions: list[dict],
                                      delay_seconds: float) -> dict[str, list[dict]]:
    """Shared by `fetch_all` and `fetch_recent`: one announcements-window fetch per distinct
    (symbol, ex_date) pair among bonus/split-eligible EQ rows (demergers need no announcement
    fetch at all -- see CLAUDE.md)."""
    session_ = session
    announcements_by_key: dict[str, list[dict]] = {}
    seen: set[str] = set()
    for action in actions:
        if action.get("series") != "EQ":
            continue
        subject = action.get("subject", "") or ""
        if parse_subject_ratio(subject) is None:
            continue  # demergers and unhandled types need no announcement fetch
        symbol = action["symbol"]
        ex_date = datetime.strptime(action["exDate"], "%d-%b-%Y").date()
        key = announcement_cache_key(symbol, ex_date)
        if key in seen:
            continue
        seen.add(key)
        announcements_by_key[key] = fetch_announcements_window(session_, symbol, ex_date)
        time.sleep(delay_seconds)
    return announcements_by_key

def fetch_all(year_from: int, year_to: int, delay_seconds: float = 0.3,
              session_factory: Callable[[], requests.Session] = _session_with_cookie) -> tuple[list[dict], dict[str, list[dict]]]:
    """Real network fetch, full-historical shape: the corporate-actions sweep by whole calendar
    year(s), then one announcements-window fetch per distinct (symbol, ex_date) pair. Not called
    by tests."""
    session = session_factory()
    actions: list[dict] = []
    for year in range(year_from, year_to + 1):
        actions.extend(fetch_corporate_actions_year(session, year))
        time.sleep(delay_seconds)
    announcements_by_key = _fetch_announcements_for_actions(session, actions, delay_seconds)
    return actions, announcements_by_key

def fetch_recent(lookback_days: int = 60, delay_seconds: float = 0.3,
                  session_factory: Callable[[], requests.Session] = _session_with_cookie,
                  today: date | None = None) -> tuple[list[dict], dict[str, list[dict]]]:
    """Real network fetch, weekly-incremental shape: corporate actions over a trailing window
    (default 60 days -- wide enough that an action announced with some lag is still caught by the
    next weekly run, narrow enough to stay fast), reusing the identical announcement-fetch logic
    `fetch_all` uses. Safe to re-run with overlapping windows: `write_facts`'s own
    duplicate-business-key skip (P4-009) makes re-ingesting an already-stored action a no-op, not
    a duplicate row. `today` is injectable for tests; defaults to the real current date."""
    session = session_factory()
    to_date = today or date.today()
    from_date = to_date - timedelta(days=lookback_days)
    actions = _fetch_corporate_actions_range(session, from_date, to_date)
    announcements_by_key = _fetch_announcements_for_actions(session, actions, delay_seconds)
    return actions, announcements_by_key
