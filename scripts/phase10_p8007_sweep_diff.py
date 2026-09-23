"""P8-007 corrections, item 1 (second half): diff the staged full live sweep
(scripts/phase10_p8007_full_sweep_staging.py's output, a SEPARATE staging DB) against the
production corporate_actions table. Read-only against both databases -- writes nothing, changes
nothing. Every difference is reported, grouped by cause; nothing is filtered out to make a number
look better.

The shape scan (scripts/phase10_scan_split_bonus_shapes.py) only sees large ratios large enough to
move return_1d by 33-90% -- a 1:10 bonus is a -9% day, invisible to it. This diff, by contrast,
compares the full disclosed action record directly, so it is the only real completeness check for
smaller ratios.

Comparison key: (symbol, action_type, event_date) -- the table's own business_key
(src/bitemporal/schema.py). Rows sharing that exact key are compared field-by-field for
ratio/knowledge_date/confidence_tier drift. Rows NOT sharing that exact key are bucketed by cause
below rather than dumped as one undifferentiated list, because two of the causes are already known
and expected going in:
  - the staging sweep runs the P8-007-corrected code (RIGHTS/RATIO_CONFLICT exclusion markers,
    widened Bonus regex) that production has never been run with -- rows of those two types, or
    rows whose subject only the fixed regex can parse, are not a live-vs-cache completeness gap,
    they are this session's own code change becoming visible for the first time.
  - production's 702 rows are 699 from a single old cached JSON file plus 3 from one
    weekly_ingest.py run (P8-008) -- not the output of any full sweep -- so "present live, absent
    from ours" is the EXPECTED, not surprising, main finding of this script.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.bitemporal.connection import get_connection, init_db
from src.bitemporal.guard import read_as_of
from src.config.settings import get_settings
from src.ingestion.nse_market_data.corporate_actions import RATIO_CONFLICT, RIGHTS

ROOT = Path(__file__).resolve().parents[1]
STAGING_DB_PATH = ROOT / "data" / "processed" / "praman_staging_p8007_sweep.db"

# The OLD (pre-P8-007-corrections) Bonus regex, reproduced exactly as it stood before this
# session's fix, purely to test "would the OLD code have parsed this subject at all" -- see
# git show HEAD~1:src/ingestion/nse_market_data/corporate_actions.py for the historical source.
import re
_OLD_BONUS_RE = re.compile(r"\bBonus\s+(\d+)\s*:\s*(\d+)\b", re.I)


def old_regex_would_have_matched(details: str | None) -> bool:
    return bool(_OLD_BONUS_RE.search(details or ""))


def load_rows(conn) -> dict[tuple[str, str, str], dict]:
    rows = read_as_of(conn, "corporate_actions", "2099-01-01")
    return {(r["symbol"], r["action_type"], r["event_date"]): dict(r) for r in rows}


def main() -> None:
    settings = get_settings()
    prod_conn = get_connection(settings.database_path)
    init_db(prod_conn)
    prod = load_rows(prod_conn)
    prod_conn.close()

    if not STAGING_DB_PATH.exists():
        print(f"Staging DB not found at {STAGING_DB_PATH} -- run "
              f"scripts/phase10_p8007_full_sweep_staging.py first.")
        return
    staging_conn = get_connection(str(STAGING_DB_PATH))
    init_db(staging_conn)
    staging = load_rows(staging_conn)
    staging_conn.close()

    print(f"Production corporate_actions: {len(prod)} rows")
    print(f"Staging (live sweep) corporate_actions: {len(staging)} rows")

    prod_keys = set(prod)
    staging_keys = set(staging)
    common_keys = prod_keys & staging_keys
    only_staging = staging_keys - prod_keys
    only_prod = prod_keys - staging_keys

    print(f"\nExact (symbol, action_type, event_date) matches: {len(common_keys)}")
    print(f"Present live, absent from ours: {len(only_staging)}")
    print(f"Present in ours, absent live: {len(only_prod)}")

    # --- present live, absent from ours: bucket by cause ---
    prod_symbols = {k[0] for k in prod_keys}
    bucket_new_type = []       # RIGHTS / RATIO_CONFLICT -- this session's own code fix, expected
    bucket_regex_gap = []      # BONUS the OLD regex would have missed (the "Bonus-" gap)
    bucket_new_symbol = []     # symbol never in production's corporate_actions at all
    bucket_new_for_known_symbol = []  # symbol known, this action/date is genuinely new

    for key in only_staging:
        symbol, action_type, event_date = key
        row = staging[key]
        if action_type in (RIGHTS, RATIO_CONFLICT):
            bucket_new_type.append((key, row))
            continue
        if action_type == "BONUS" and not old_regex_would_have_matched(row.get("details")):
            bucket_regex_gap.append((key, row))
            continue
        if symbol not in prod_symbols:
            bucket_new_symbol.append((key, row))
        else:
            bucket_new_for_known_symbol.append((key, row))

    print(f"\n=== PRESENT LIVE, ABSENT FROM OURS ({len(only_staging)}) -- grouped by cause ===")
    print(f"  A. New action type from this session's own code fix (RIGHTS/RATIO_CONFLICT, "
          f"expected -- see P8-007 corrections items 2-3): {len(bucket_new_type)}")
    print(f"  B. BONUS the OLD (pre-fix) regex could not parse at all -- the 'Bonus-' hyphen gap "
          f"(item 3): {len(bucket_regex_gap)}")
    print(f"  C. Symbol never in production corporate_actions at all -- genuinely new to our "
          f"records: {len(bucket_new_symbol)}")
    print(f"  D. Symbol known to production, this action/date is new -- candidate genuinely "
          f"missed action: {len(bucket_new_for_known_symbol)}")

    univastu_hits = [k for k in only_staging if k[0] == "UNIVASTU"]
    print(f"\n  UNIVASTU rows present live, absent from ours: {len(univastu_hits)}")
    for k in univastu_hits:
        print(f"    {k} -> {staging[k]}")

    def _print_bucket(name: str, items: list) -> None:
        print(f"\n-- {name} ({len(items)}) --")
        for key, row in sorted(items)[:50]:
            print(f"  {key[0]:16s} {key[1]:16s} {key[2]}  ratio={row.get('ratio_numerator')}:"
                  f"{row.get('ratio_denominator')}  tier={row.get('confidence_tier')}  "
                  f"details={str(row.get('details'))[:60]!r}")
        if len(items) > 50:
            print(f"  ... and {len(items) - 50} more")

    _print_bucket("Bucket A: new action type (code fix)", bucket_new_type)
    _print_bucket("Bucket B: regex-gap BONUS rows", bucket_regex_gap)
    _print_bucket("Bucket C: brand-new symbol", bucket_new_symbol)
    _print_bucket("Bucket D: known symbol, new action/date", bucket_new_for_known_symbol)

    # --- present in ours, absent live ---
    print(f"\n=== PRESENT IN OURS, ABSENT LIVE ({len(only_prod)}) ===")
    for key in sorted(only_prod)[:50]:
        row = prod[key]
        print(f"  {key[0]:16s} {key[1]:16s} {key[2]}  ratio={row.get('ratio_numerator')}:"
              f"{row.get('ratio_denominator')}  tier={row.get('confidence_tier')}  "
              f"source_file={row.get('source_file')}")
    if len(only_prod) > 50:
        print(f"  ... and {len(only_prod) - 50} more")

    # --- same key, different content ---
    print(f"\n=== SAME (symbol, action_type, event_date), DIFFERENT CONTENT ===")
    ratio_diffs, knowledge_date_diffs, tier_diffs = [], [], []
    for key in common_keys:
        p, s = prod[key], staging[key]
        if (p.get("ratio_numerator"), p.get("ratio_denominator")) != (s.get("ratio_numerator"), s.get("ratio_denominator")):
            ratio_diffs.append((key, p, s))
        if p.get("knowledge_date") != s.get("knowledge_date"):
            knowledge_date_diffs.append((key, p, s))
        if p.get("confidence_tier") != s.get("confidence_tier"):
            tier_diffs.append((key, p, s))

    print(f"  Ratio differs: {len(ratio_diffs)}")
    for key, p, s in ratio_diffs[:30]:
        print(f"    {key}: ours={p.get('ratio_numerator')}:{p.get('ratio_denominator')} "
              f"live={s.get('ratio_numerator')}:{s.get('ratio_denominator')}")
    print(f"  knowledge_date differs: {len(knowledge_date_diffs)}")
    for key, p, s in knowledge_date_diffs[:30]:
        print(f"    {key}: ours={p.get('knowledge_date')} live={s.get('knowledge_date')}")
    print(f"  confidence_tier differs: {len(tier_diffs)}")
    for key, p, s in tier_diffs[:30]:
        print(f"    {key}: ours={p.get('confidence_tier')} live={s.get('confidence_tier')}")


if __name__ == "__main__":
    main()
