"""通信要件 YAML から通信要件一覧 CSV を生成する。

Excel（Windows）で文字化けしないよう、BOM 付き UTF-8 で出力する。
"""

import csv
import sys
from pathlib import Path

import yaml

from validate_communication import DEFAULT_PATH, validate

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs" / "tables" / "communication.csv"

HEADER = ["ID", "Source", "Destination", "Via", "Protocol", "Port", "Description"]


def main() -> int:
    data = yaml.safe_load(DEFAULT_PATH.read_text(encoding="utf-8"))

    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        for comm in data["communications"]:
            writer.writerow([
                comm["id"],
                comm["source"],
                comm["destination"],
                comm.get("via", ""),
                comm["protocol"],
                comm["port"],
                comm["description"],
            ])

    print(f"Generated: {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
