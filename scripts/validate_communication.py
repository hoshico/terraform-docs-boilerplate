"""通信要件 YAML の整合性チェック。

JSON Schema では検証しにくい以下の項目を確認する。

- 通信 ID の重複
- 未定義の source / destination
- source と destination が同一の通信
"""

import sys
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "requirements" / "communication.yaml"


def validate(data: dict) -> list[str]:
    errors = []
    resource_ids = set(data["resources"])
    seen_ids = set()

    for comm in data["communications"]:
        comm_id = comm["id"]
        if comm_id in seen_ids:
            errors.append(f"{comm_id}: 通信 ID が重複しています")
        seen_ids.add(comm_id)

        for key in ("source", "destination"):
            if comm[key] not in resource_ids:
                errors.append(f"{comm_id}: {key} '{comm[key]}' が resources に定義されていません")

        if comm["source"] == comm["destination"]:
            errors.append(f"{comm_id}: source と destination が同じです")

    return errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    errors = validate(data)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1

    print(f"OK: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
