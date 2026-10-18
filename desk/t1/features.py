"""T1 features, point-in-time, from Praman's store (read-only) and the official index inputs.

No outcome is loaded or computed here (no adverse20, no forward price). Every value for decision
session D (end of session) uses only:
- stock bars whose knowledge_date is on or before D (the store has one vintage per bar);
- corporate actions with ex-date on or before D (every action in the store was known by its
  ex-date, so a fully back-adjusted series gives exactly the as-of ratios within a window); a
  window containing an unadjustable action (demerger, rights, ratio conflict, capital reduction)
  is UNKNOWN;
- official index and VIX closes through D-1 (known from the next session: T1 addendum 2);
- equity identity from the latest dated ISIN snapshot on or before D containing the symbol.
A missing bar is never forward-filled; a window needs every one of its bars.

Calendar of global sessions: before 2019-10-01 (no stock data), the official index's weekday
sessions; from 2019-10-01, the store's sessions plus any weekday index session the store lacks
(2022-08-08), on which every stock is missing. A weekend special session (budget Saturday,
Muhurat, special Saturday) is in the calendar only when the store has it: four are stored, each from
the following weekday holiday's file, and four are not (P8-070). Both choices are stated in the
coverage report and docs/desk/t1_coverage_decisions_20261018.md for the user's review.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

from desk.t1.inputs import SERIES, is_weekday

STUDY_START, STUDY_END = "2019-10-01", "2025-12-31"
DEVELOPMENT_END, HOLDOUT_YEAR = "2024-12-31", "2025"
FORWARD_SESSIONS = 20
ADJUSTABLE = ("BONUS", "SPLIT")
UNADJUSTABLE = ("DEMERGER", "RIGHTS", "RATIO_CONFLICT", "CAPITAL_REDUCTION")
UNKNOWN, EQUITY, FUND = 0, 1, 2


class StudyWindowRefused(ValueError):
    """T1 inputs end at 2025-12-31; nothing in the forward window is touched."""


@dataclass
class Panel:
    sessions: list[str]
    symbols: list[str]
    raw_close: np.ndarray            # [session, symbol], NaN when there is no stored EQ bar
    close: np.ndarray                # fully back-adjusted
    high: np.ndarray
    low: np.ndarray
    known: np.ndarray                # session index from which the bar is known (inf if missing)
    breaks: np.ndarray               # cumulative count of unadjustable ex-dates
    identity: np.ndarray             # UNKNOWN / EQUITY / FUND
    index: dict = field(default_factory=dict)          # series -> closes on the calendar (NaN missing)
    store_missing_sessions: list = field(default_factory=list)
    weekend_specials: list = field(default_factory=list)
    forward_sessions: list = field(default_factory=list)   # 2026 session dates, for censoring only
    open: np.ndarray | None = None   # fully back-adjusted; the outcome step checks it (desk/t1_outcome)


def build_calendar(store_sessions: set[str], index_dates: set[str], end: str = STUDY_END):
    weekday_index = {d for d in index_dates if is_weekday(d) and d <= end}
    before = sorted(d for d in weekday_index if d < STUDY_START)
    stored = {d for d in store_sessions if STUDY_START <= d <= end}
    missing = sorted(d for d in weekday_index if d >= STUDY_START and d not in stored)
    sessions = before + sorted(stored | set(missing))
    specials = sorted(d for d in index_dates if not is_weekday(d) and d <= end)
    return sessions, missing, specials


def _rolling_sum(x: np.ndarray, w: int) -> np.ndarray:
    """Sum over the last `w` rows ending at each row (NaN for the first w-1 rows)."""
    c = np.cumsum(np.concatenate([np.zeros((1,) + x.shape[1:]), x], axis=0), axis=0)
    out = np.full(x.shape, np.nan)
    out[w - 1:] = c[w:] - c[:-w]
    return out


def _rolling_max(x: np.ndarray, w: int) -> np.ndarray:
    from numpy.lib.stride_tricks import sliding_window_view
    out = np.full(x.shape, np.nan)
    if x.shape[0] >= w:
        out[w - 1:] = sliding_window_view(x, w, axis=0).max(axis=-1)
    return out


def window_valid(p: Panel, w: int, lag: int = 0) -> np.ndarray:
    """[d, s]: the `w` bars ending at session d - lag are all stored, all known by session d (the
    decision), and no unadjustable ex-date falls after the window's first bar through its last."""
    n = len(p.sessions)
    valid = np.zeros(p.raw_close.shape, dtype=bool)
    if n < w + lag:
        return valid
    present = (~np.isnan(p.raw_close)) & (np.nan_to_num(p.raw_close) > 0)
    count = _rolling_sum(present.astype(float), w)                      # by window end e
    kmax = _rolling_max(np.where(np.isinf(p.known), 1e12, p.known), w)
    brk_ok = np.zeros(p.raw_close.shape, dtype=bool)
    brk_ok[w - 1:] = (p.breaks[w - 1:] - p.breaks[:n - w + 1]) == 0
    e = np.arange(n) - lag                                              # window end for decision d
    ok = e >= w - 1
    d = np.arange(n)[ok]
    ee = e[ok]
    valid[d] = (count[ee] == w) & (kmax[ee] <= d[:, None]) & brk_ok[ee]
    return valid


def _shift(x: np.ndarray, k: int) -> np.ndarray:
    out = np.full(x.shape, np.nan)
    if k < x.shape[0]:
        out[k:] = x[:-k] if k else x
    return out


def _shift_bool(x: np.ndarray, k: int) -> np.ndarray:
    out = np.zeros(x.shape, dtype=bool)
    out[k:] = x[:-k]
    return out


def compute(p: Panel) -> dict:
    """Every T1 feature. Returns market-level arrays [session] and stock-level arrays [session, symbol]."""
    n, m = p.raw_close.shape
    equity = p.identity == EQUITY
    c = p.close
    v2 = window_valid(p, 2)
    r = np.where(v2, c / _shift(c, 1) - 1, np.nan)                     # one-day adjusted return
    basket = v2 & equity & np.isfinite(r)
    N = basket.sum(axis=1).astype(float)
    S = np.where(basket, r, 0.0).sum(axis=1)
    adv = (basket & (r > 0)).sum(axis=1)
    dec = (basket & (r < 0)).sum(axis=1)
    flat = (basket & (r == 0)).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        net = np.where(N > 0, (adv - dec) / N, np.nan)
        dispersion = np.array([np.std(r[i][basket[i]]) if basket[i].any() else np.nan for i in range(n)])
    out = dict(adv=adv, dec=dec, flat=flat, ad_valid=N.astype(int), net_breadth=net, dispersion=dispersion,
               basket_n=N.astype(int), basket_mean=np.where(N > 0, S / np.where(N > 0, N, 1), np.nan))

    def above(w):
        valid = window_valid(p, w) & equity
        mean = _rolling_sum(np.nan_to_num(c), w) / w
        hit = valid & (c > mean)
        cnt = valid.sum(axis=1)
        return hit.sum(axis=1), cnt, np.where(cnt > 0, hit.sum(axis=1) / np.where(cnt > 0, cnt, 1), np.nan)
    out["above50"], out["above50_valid"], out["share_above50"] = above(50)
    out["above200"], out["above200_valid"], out["share_above200"] = above(200)

    valid253 = window_valid(p, 253) & equity
    prev_max = _shift(_rolling_max(np.nan_to_num(c, nan=-np.inf), 252), 1)
    prev_min = -_shift(_rolling_max(np.nan_to_num(-c, nan=-np.inf), 252), 1)
    cnt = valid253.sum(axis=1)
    out["new_high_rate"] = np.where(cnt > 0, (valid253 & (c > prev_max)).sum(axis=1) / np.maximum(cnt, 1), np.nan)
    out["new_low_rate"] = np.where(cnt > 0, (valid253 & (c < prev_min)).sum(axis=1) / np.maximum(cnt, 1), np.nan)
    out["new_hl_valid"] = cnt

    # ATR20: 21 adjusted bars, true range over the last 20.
    v21 = window_valid(p, 21)
    pc = _shift(c, 1)
    tr = np.maximum(p.high, pc) - np.minimum(p.low, pc)
    atr = _rolling_sum(np.nan_to_num(tr), 20) / 20
    out["atr_pct"] = np.where(v21 & (c > 0), atr / c * 100, np.nan)

    # Relative strength against the equal-weight market of eligible equities, focal stock excluded.
    # A day t inside the window counts at decision d with the constituents whose return for t was
    # known by d: K2 is the session from which a stock's return for t is known (both its bars).
    # o = d - t, so the basket for t as seen at d is "K2 - t <= o".
    present = (~np.isnan(p.raw_close)) & (np.nan_to_num(p.raw_close) > 0)
    no_break = np.zeros((n, m), dtype=bool)
    no_break[1:] = (p.breaks[1:] - p.breaks[:-1]) == 0
    stored2 = present & _shift_bool(present, 1) & no_break
    r_all = np.where(stored2, c / _shift(c, 1) - 1, np.nan)
    k_inf = np.where(np.isinf(p.known), 1e12, p.known)
    lag2 = np.maximum(k_inf, np.vstack([np.full((1, m), 1e12), k_inf[:-1]])) - np.arange(n)[:, None]
    ok_r = np.isfinite(r_all) & equity
    max_k = 60
    run_log, run_ok = np.zeros((n, m)), np.ones((n, m), dtype=bool)
    market = {}
    for o in range(max_k):
        member = ok_r & (lag2 <= o)
        S_o = np.where(member, r_all, 0.0).sum(axis=1)
        N_o = member.sum(axis=1).astype(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            others = N_o[:, None] - member
            rm = np.where(member, (S_o[:, None] - np.nan_to_num(r_all)) / others, S_o[:, None] / N_o[:, None])
            a = np.where(others >= 1, np.log1p(rm), np.nan)
        shifted = np.full((n, m), np.nan)
        if o < n:
            shifted[o:] = a[:n - o]                         # day t = d - o, seen at decision d
        run_ok &= np.isfinite(shifted)
        run_log = run_log + np.nan_to_num(shifted)
        if o + 1 in (1, 5, 20, 60):
            market[o + 1] = np.where(run_ok, np.expm1(run_log), np.nan)
    for k in (1, 5, 20, 60):
        vk = window_valid(p, k + 1)
        rs = np.where(vk, c / _shift(c, k) - 1, np.nan)
        out[f"rel_ew_{k}"] = np.where(vk & np.isfinite(market[k]), rs - market[k], np.nan)
    rel20 = out["rel_ew_20"]
    out["v3_negative"] = np.where(np.isfinite(rel20), rel20 < 0, np.nan)

    # Official index states at D from closes through D-1 (T1 addendum 2).
    n50 = p.index.get("NIFTY 50", np.full(n, np.nan))
    n500 = p.index.get("NIFTY 500", np.full(n, np.nan))
    vix = p.index.get("INDIA VIX", np.full(n, np.nan))

    def sma(series, w):
        ok = _rolling_sum(np.isfinite(series).astype(float), w) == w
        return np.where(ok, _rolling_sum(np.nan_to_num(series), w) / w, np.nan)
    n500_prev, sma200_prev = _shift(n500, 1), _shift(sma(n500, 200), 1)
    n50_prev, n50_sma200_prev = _shift(n50, 1), _shift(sma(n50, 200), 1)
    vix_prev = _shift(vix, 1)
    p80 = np.full(n, np.nan)
    for d in range(253, n):              # VIX at d-1 against the 252 closes before it, excluding itself
        window = vix[d - 253:d - 1]
        if np.isfinite(window).all():
            p80[d] = np.percentile(window, 80, method="linear")
    below = np.where(np.isfinite(n500_prev) & np.isfinite(sma200_prev), n500_prev < sma200_prev, np.nan)
    high_vix = np.where(np.isfinite(vix_prev) & np.isfinite(p80), vix_prev > p80, np.nan)
    both = np.isfinite(below) & np.isfinite(high_vix)
    out["v1_adverse"] = np.where(both, (np.nan_to_num(below) > 0) | (np.nan_to_num(high_vix) > 0), np.nan)
    out.update(n500_prev=n500_prev, n500_sma200_prev=sma200_prev, vix_prev=vix_prev, vix_p80_prev=p80,
               n50_prev=n50_prev, n50_sma200_prev=n50_sma200_prev)
    share, netb = out["share_above50"], out["net_breadth"]
    v2_known = np.isfinite(share) & np.isfinite(netb)
    out["v2_adverse"] = np.where(v2_known, (np.nan_to_num(share) < 0.40) & (np.nan_to_num(netb) < 0), np.nan)

    # Descriptive: stock relative to NIFTY 50 over identical endpoints ending D-1.
    for k in (1, 5, 20, 60):
        vk = window_valid(p, k + 1, lag=1)
        rs = np.where(vk, _shift(c, 1) / _shift(c, k + 1) - 1, np.nan)
        ri = _shift(n50, 1) / _shift(n50, k + 1) - 1
        out[f"rel_n50_{k}"] = np.where(vk & np.isfinite(ri)[:, None], rs - ri[:, None], np.nan)
    return out


def exclusion_causes(p: Panel) -> np.ndarray:
    """[d, s] cause for every stored stock-day: '' when eligible for the primary population."""
    n, m = p.raw_close.shape
    stored = ~np.isnan(p.raw_close)
    cause = np.full((n, m), "", dtype=object)
    last = np.arange(n)[:, None]
    late = stored & (p.known > last)
    bad = stored & ~late & ~(np.nan_to_num(p.raw_close) > 0)
    cause[~stored] = "no_bar"
    cause[late] = "bar_not_known_by_decision"
    cause[bad] = "invalid_price"
    rest = stored & ~late & ~bad
    cause[rest & (p.identity == UNKNOWN)] = "identity_unknown"
    cause[rest & (p.identity == FUND)] = "fund_unit"
    rest = rest & (p.identity == EQUITY)
    v21 = window_valid(p, 21)
    brk = np.zeros((n, m), dtype=bool)
    brk[20:] = (p.breaks[20:] - p.breaks[:n - 20]) != 0
    cause[rest & ~v21 & brk] = "atr_window_unadjustable"
    cause[rest & ~v21 & ~brk] = "atr_window_incomplete"
    return cause


def periods(sessions: list[str], forward: list[str]) -> np.ndarray:
    """development / development_purged / holdout_2025 / holdout_censored / outside for each session."""
    full = sessions + [d for d in forward if d > sessions[-1]]
    out = np.full(len(sessions), "outside", dtype=object)
    for i, d in enumerate(sessions):
        if d < STUDY_START or d > STUDY_END:
            continue
        twentieth = full[i + FORWARD_SESSIONS] if i + FORWARD_SESSIONS < len(full) else None
        if d <= DEVELOPMENT_END:
            out[i] = "development" if twentieth is not None and twentieth <= DEVELOPMENT_END else "development_purged"
        else:
            out[i] = "holdout_2025" if twentieth is not None and twentieth <= STUDY_END else "holdout_censored"
    return out


def quintile_bounds(atr_pct: np.ndarray, cause: np.ndarray, period: np.ndarray) -> list[float]:
    """Development-only volatility boundaries: NumPy linear 20/40/60/80 percentiles of every
    eligible development stock-day's ATR% (outcomes are not involved)."""
    dev = (period == "development")[:, None] & (cause == "") & np.isfinite(atr_pct)
    return [float(x) for x in np.percentile(atr_pct[dev], [20, 40, 60, 80], method="linear")]


def quintile(x: np.ndarray, bounds: list[float]) -> np.ndarray:
    """1..5, ties to the upper quintile; NaN stays NaN."""
    q = np.searchsorted(np.asarray(bounds), np.nan_to_num(x), side="right") + 1.0
    return np.where(np.isfinite(x), q, np.nan)


def spells(states: list, gap: int = 20) -> list[dict]:
    """T1 addendum 1: runs of adverse sessions; runs separated by fewer than `gap` known
    non-adverse sessions merge; UNKNOWN sessions never separate. `states` are (date, True/False/None)."""
    result, current, separation = [], None, 0
    for day, state in states:
        if state is True:
            if current is not None and separation < gap:
                current["last"], current["adverse_sessions"] = day, current["adverse_sessions"] + 1
            else:
                if current is not None:
                    result.append(current)
                current = dict(first=day, last=day, adverse_sessions=1)
            separation = 0
        elif state is False:
            separation += 1
    if current is not None:
        result.append(current)
    return result


def refuse_outside_study(end: str) -> None:
    from desk.outcome_firewall import FORWARD_START, OUTCOMES_OPEN     # the one owner of that boundary
    if end > STUDY_END:
        raise StudyWindowRefused(f"T1 features end at {STUDY_END}; {end} is outside the study (and nothing on or after "
                                 f"{FORWARD_START} may be evaluated before {OUTCOMES_OPEN}).")
