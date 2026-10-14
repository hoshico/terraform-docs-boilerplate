"""通信要件 YAML の整合性チェック。

JSON Schema では検証しにくい以下の項目を確認する。

- 通信 ID・サブネット ID の重複
- 未定義の source / destination / subnet
- source と destination が同一の通信
- サブネットの cidrs の数と AZ の数の不一致
- layout とサブネット・AZ 数の組み合わせ
"""

import sys
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "requirements" / "communication.yaml"


def validate_network(data: dict) -> list[str]:
    errors = []
    network = data["network"]
    az_count = len(network["availability_zones"])
    subnet_ids = set()

    for subnet in network["subnets"]:
        if subnet["id"] in subnet_ids:
            errors.append(f"subnet {subnet['id']}: サブネット ID が重複しています")
        subnet_ids.add(subnet["id"])

        if len(subnet["cidrs"]) != az_count:
            errors.append(
                f"subnet {subnet['id']}: cidrs の数（{len(subnet['cidrs'])}）が"
                f" availability_zones の数（{az_count}）と一致しません"
            )

    for resource_id, resource in data["resources"].items():
        layout = resource.get("layout", "single")
        subnet = resource.get("subnet")

        if subnet is not None and subnet not in subnet_ids:
            errors.append(f"resource {resource_id}: subnet '{subnet}' が network.subnets に定義されていません")
        if subnet is None and "layout" in resource:
            errors.append(f"resource {resource_id}: layout を指定する場合は subnet が必要です")
        if layout == "primary_standby" and az_count < 2:
            errors.append(f"resource {resource_id}: primary_standby には 2 つ以上の AZ が必要です")

    return errors


def validate_communications(data: dict) -> list[str]:
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


def validate(data: dict) -> list[str]:
    return validate_network(data) + validate_communications(data)


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
