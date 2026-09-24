"""Amendment 5 prep, item 1: measure whether the P8-013 global-horizon label's OWN missingness is
correlated with model inputs -- a claim Amendment 4 asserted but never actually measured (it only
measured the gradient on the OLD own-session definition, then adopted a new definition and assumed,
without checking, that the new definition's own ~5pp of newly-missing TRAIN events behaved the same
way). TRAIN, by cap_band, volume_ratio_high, delivery_low, and ASM status at event_date, using the
CURRENT phase8_relabel_t0_relative.csv (the P8-013 global-horizon label) side by side with the
preserved OLD (own-session) label for direct comparison.

Also measures item 1(b): of the new definition's MISSING events, what share has a BE/BZ close for
the same security within the 10-session staleness window before target_date -- the specific
mechanism hypothesized (an EQ -> BE -> EQ temporary trade-for-trade stint is invisible to
extend_with_series, which only appends BE/BZ rows STRICTLY AFTER the primary series' own LAST-EVER
EQ date, missing a stint that resolves back to EQ afterward).
"""
from __future__ import annotations
import bisect
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.config.settings import get_settings

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE_PATH = ROOT / "data" / "processed" / "event_catalogue_loose_zscore_only.csv"
CLASS_PATH = ROOT / "data" / "processed" / "event_classifications.csv"
NEW_LABEL_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative.csv"
OLD_LABEL_PATH = ROOT / "data" / "processed" / "phase8_relabel_t0_relative_OLD_own_session.csv"
MARKET_INDEX_PATH = ROOT / "data" / "processed" / "market_index.csv"

TRAIN_CUTOFF = "2026-01-01"
HORIZON = 90
STALENESS_CAP = 10

DELIVERY_THRESHOLD = 13.3333
VOLUME_RATIO_BAND_MEDIAN = {
    "Micro": 5.0926, "Small": 6.8397, "Mid": 7.6364, "Large": 8.6042, "Mega": 7.4616,
}


def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    cap_band = {}
    for row in load_csv(CLASS_PATH):
        cap_band[(row["symbol"], row["event_date"])] = row["cap_band"]

    features = {}
    for row in load_csv(CATALOGUE_PATH):
        key = (row["symbol"], row["event_date"])
        asm = row.get("asm_stage", "") not in ("", "None")
        gsm = row.get("gsm_stage", "") not in ("", "None")
        features[key] = {
            "delivery_pct_percentile_60d": row["delivery_pct_percentile_60d"],
            "volume_ratio": row["volume_ratio"],
            "asm_or_gsm": asm or gsm,
        }

    new_labels = {(r["symbol"], r["event_date"]): r for r in load_csv(NEW_LABEL_PATH)}
    old_labels = {(r["symbol"], r["event_date"]): r for r in load_csv(OLD_LABEL_PATH)}

    train_keys = [k for k in new_labels if k[1] < TRAIN_CUTOFF]
    print(f"TRAIN events (new label file): {len(train_keys)}")

    def bucket(keyfn, label_dict, field="signed_return_90d"):
        agg = defaultdict(lambda: [0, 0])
        for k in train_keys:
            r = label_dict.get(k)
            if r is None:
                continue
            key = keyfn(k)
            if key is None:
                continue
            agg[key][0] += 1
            if r[field] in ("", "None"):
                agg[key][1] += 1
        return agg

    print("\n=== NEW definition (P8-013 global horizon) -- TRAIN missing rate by cap_band ===")
    agg_new = bucket(lambda k: cap_band.get(k), new_labels)
    print("=== OLD definition (own-session) -- TRAIN missing rate by cap_band, for comparison ===")
    agg_old = bucket(lambda k: cap_band.get(k), old_labels)
    print(f"{'band':8s} {'NEW n':>8s} {'NEW miss':>9s} {'NEW rate':>9s}   {'OLD n':>8s} {'OLD miss':>9s} {'OLD rate':>9s}")
    for band in ("Micro", "Small", "Mid", "Large", "Mega"):
        nn, nm = agg_new.get(band, [0, 0])
        on, om = agg_old.get(band, [0, 0])
        nr = 100 * nm / nn if nn else float("nan")
        orr = 100 * om / on if on else float("nan")
        print(f"{band:8s} {nn:8d} {nm:9d} {nr:8.3f}%   {on:8d} {om:9d} {orr:8.3f}%")
    micro_new = 100 * agg_new["Micro"][1] / agg_new["Micro"][0]
    mega_new = 100 * agg_new["Mega"][1] / agg_new["Mega"][0]
    micro_old = 100 * agg_old["Micro"][1] / agg_old["Micro"][0]
    mega_old = 100 * agg_old["Mega"][1] / agg_old["Mega"][0]
    print(f"\nNEW definition Micro-minus-Mega gap: {micro_new - mega_new:.3f}pp")
    print(f"OLD definition Micro-minus-Mega gap: {micro_old - mega_old:.3f}pp")

    print("\n=== NEW definition -- TRAIN missing rate by volume_ratio_high ===")
    def vol_high_key(k):
        band = cap_band.get(k)
        f = features.get(k)
        if band is None or f is None or f["volume_ratio"] in ("", "None"):
            return None
        return "HIGH" if float(f["volume_ratio"]) >= VOLUME_RATIO_BAND_MEDIAN.get(band, float("inf")) else "LOW"
    agg = bucket(vol_high_key, new_labels)
    for k in ("LOW", "HIGH"):
        n, m = agg.get(k, [0, 0])
        rate = 100 * m / n if n else float("nan")
        print(f"  {k:8s} n={n:6d}  missing={m:5d}  rate={rate:.3f}%")

    print("\n=== NEW definition -- TRAIN missing rate by delivery_low ===")
    def delivery_low_key(k):
        f = features.get(k)
        if f is None or f["delivery_pct_percentile_60d"] in ("", "None"):
            return None
        return "LOW" if float(f["delivery_pct_percentile_60d"]) < DELIVERY_THRESHOLD else "HIGH/NORMAL"
    agg = bucket(delivery_low_key, new_labels)
    for k in ("HIGH/NORMAL", "LOW"):
        n, m = agg.get(k, [0, 0])
        rate = 100 * m / n if n else float("nan")
        print(f"  {k:12s} n={n:6d}  missing={m:5d}  rate={rate:.3f}%")

    print("\n=== NEW definition -- TRAIN missing rate by ASM/GSM status at event_date ===")
    def asm_key(k):
        f = features.get(k)
        if f is None:
            return None
        return "FLAGGED" if f["asm_or_gsm"] else "NOT_FLAGGED"
    agg = bucket(asm_key, new_labels)
    for k in ("NOT_FLAGGED", "FLAGGED"):
        n, m = agg.get(k, [0, 0])
        rate = 100 * m / n if n else float("nan")
        print(f"  {k:12s} n={n:6d}  missing={m:5d}  rate={rate:.3f}%")

    # --- item 1(b): of the NEW-definition MISSING events, what share has a BE/BZ close within
    # the 10-session staleness window before target_date? ---
    print("\n=== Item 1(b): NEW-definition MISSING events with a nearby BE/BZ close ===")
    with open(MARKET_INDEX_PATH, encoding="utf-8") as f:
        global_days = [r["date"] for r in csv.DictReader(f)]

    missing_events = []
    for k in train_keys:
        r = new_labels.get(k)
        if r and r["signed_return_90d"] in ("", "None"):
            reason = r.get("excluded_reason", "")
            if reason and reason.startswith("stale beyond"):
                missing_events.append(k)
    print(f"TRAIN events MISSING specifically due to the staleness cap: {len(missing_events)}")

    settings = get_settings()
    conn = get_connection(settings.database_path)
    init_db(conn)

    symbols = sorted({k[0] for k in missing_events})
    placeholders = ",".join("?" * len(symbols))
    be_bz_rows = conn.execute(
        f"SELECT symbol, event_date FROM bhavcopy WHERE series IN ('BE','BZ') AND symbol IN "
        f"({placeholders}) ORDER BY symbol, event_date", tuple(symbols),
    ).fetchall() if symbols else []
    be_bz_by_symbol: dict[str, list[str]] = defaultdict(list)
    for r in be_bz_rows:
        be_bz_by_symbol[r["symbol"]].append(r["event_date"])

    has_nearby_be_bz = 0
    for symbol, event_date in missing_events:
        idx = bisect.bisect_left(global_days, event_date)
        target_idx = idx + HORIZON
        if target_idx >= len(global_days):
            continue
        target_date = global_days[target_idx]
        window_lo_idx = max(0, target_idx - STALENESS_CAP)
        window_lo = global_days[window_lo_idx]
        be_dates = be_bz_by_symbol.get(symbol, [])
        # any BE/BZ date within (window_lo, target_date]?
        lo_pos = bisect.bisect_right(be_dates, window_lo)
        hi_pos = bisect.bisect_right(be_dates, target_date)
        if hi_pos > lo_pos:
            has_nearby_be_bz += 1

    print(f"Of those, have a BE/BZ close within the 10-session staleness window before target_date: "
          f"{has_nearby_be_bz} ({100*has_nearby_be_bz/len(missing_events):.2f}%)" if missing_events else "n=0")

    conn.close()


if __name__ == "__main__":
    main()
