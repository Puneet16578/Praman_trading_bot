"""Daily Desk and weekly Praman backups, with a restore check before retention."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desk.backups import CONFIG_PATH, run_backups


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()
    for report in run_backups(args.config):
        print(json.dumps(report, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
