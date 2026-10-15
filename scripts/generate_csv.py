"""通信要件 YAML から通信要件一覧を生成する。

- CSV：Excel（Windows）で文字化けしないよう、BOM 付き UTF-8 で出力する
- README：目印コメントの間を Markdown の表で書き換える
"""

import csv
import sys
from pathlib import Path

import yaml

from validate_communication import DEFAULT_PATH, validate

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs" / "tables" / "communication.csv"
README_PATH = ROOT / "README.md"

README_BEGIN = "<!-- BEGIN: communication-table (自動生成のため直接編集しない) -->"
README_END = "<!-- END: communication-table -->"

HEADER = ["ID", "Source", "Destination", "Via", "Protocol", "Port", "Description"]


def build_rows(data: dict) -> list[list[str]]:
    return [
        [
            comm["id"],
            comm["source"],
            comm["destination"],
            comm.get("via", ""),
            comm["protocol"],
            str(comm["port"]),
            comm["description"],
        ]
        for comm in data["communications"]
    ]


def write_csv(rows: list[list[str]]) -> None:
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(rows)


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def update_readme(rows: list[list[str]]) -> bool:
    readme = README_PATH.read_text(encoding="utf-8")
    begin = readme.find(README_BEGIN)
    end = readme.find(README_END)
    if begin == -1 or end == -1 or end < begin:
        print(f"ERROR: README.md に目印コメント（{README_BEGIN} / {README_END}）がありません", file=sys.stderr)
        return False

    lines = [
        "| " + " | ".join(HEADER) + " |",
        "|" + "---|" * len(HEADER),
        *("| " + " | ".join(markdown_cell(v) for v in row) + " |" for row in rows),
    ]
    table = "\n".join(lines)
    updated = readme[: begin + len(README_BEGIN)] + "\n" + table + "\n" + readme[end:]
    README_PATH.write_text(updated, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    data = yaml.safe_load(DEFAULT_PATH.read_text(encoding="utf-8"))

    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    rows = build_rows(data)
    write_csv(rows)
    print(f"Generated: {OUTPUT_PATH.relative_to(ROOT)}")

    if not update_readme(rows):
        return 1
    print(f"Updated: {README_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
