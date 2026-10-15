"""通信要件 YAML から draw.io 構成図を生成する。

Region > VPC > AZ > サブネットの枠を描き、resources を subnet / layout に従って配置する。
subnet を持たないリソース（Users など）は Region の上に並べる。
via を持つ通信は「source -> via -> destination」の 2 本の矢印で描く。
矢印と重ならないよう、リソース名はアイコンの右側に表示する。
"""

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import yaml

from validate_communication import DEFAULT_PATH, validate

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs" / "diagrams" / "communication.drawio"

# 以下のスタイルは draw.io の AWS4 アイコンライブラリ（mxgraph.aws4.*）に合わせる

# リソースタイプ -> (アイコン識別子, AWS カテゴリ色)。サービスアイコン（背景色付き）として描く
SERVICE_ICONS = {
    "aws_alb": ("elastic_load_balancing", "#8C4FFF"),
    "aws_ecs": ("ecs", "#ED7100"),
    "aws_rds": ("rds", "#C925D1"),
}
# リソースタイプ -> (シェイプ名, 色)。背景なしのアイコンとして描く
PLAIN_ICONS = {
    "aws_nat_gateway": ("nat_gateway", "#8C4FFF"),
    "users": ("users", "#232F3D"),
    "internet": ("internet", "#232F3D"),
}

LABEL_RIGHT = "labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=8;"
ICON_BASE = (
    "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;dashed=0;"
    "html=0;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;" + LABEL_RIGHT
)
SERVICE_ICON_STYLE = ICON_BASE + "fillColor={color};strokeColor=#ffffff;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{icon};"
PLAIN_ICON_STYLE = ICON_BASE + "fillColor={color};strokeColor=none;shape=mxgraph.aws4.{icon};"
# VPC の枠線上に置くため、ラベルに背景色を付けて枠線と重ならないようにする
IGW_STYLE = PLAIN_ICON_STYLE.format(icon="internet_gateway", color="#8C4FFF") + "labelBackgroundColor=#ffffff;"
FALLBACK_STYLE = "rounded=1;whiteSpace=wrap;html=0;fontColor=#232F3E;strokeColor=#232F3E;"

GROUP_BASE = (
    "outlineConnect=0;gradientColor=none;html=0;whiteSpace=wrap;fontSize=12;fontStyle=0;"
    "pointerEvents=0;verticalAlign=top;align=left;spacingLeft=30;dashed=0;shape=mxgraph.aws4.group;"
)
REGION_STYLE = GROUP_BASE + "grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fillColor=none;fontColor=#147EBA;dashed=1;"
VPC_STYLE = GROUP_BASE + "grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fillColor=none;fontColor=#AAB7B8;"
SUBNET_STYLES = {
    "public": GROUP_BASE + "grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#F2F6E8;fontColor=#248814;",
    "private": GROUP_BASE + "grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#E6F6F7;fontColor=#147EBA;",
}
# AZ 名は左寄せにして、上方向へ伸びる矢印と重ならないようにする
AZ_STYLE = "fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;align=left;spacingLeft=10;fontStyle=0;fontColor=#147EBA;whiteSpace=wrap;html=0;"

EDGE_STYLE = (
    "endArrow=block;endFill=1;html=0;fontSize=12;"
    "strokeColor=#232F3E;fontColor=#232F3E;labelBackgroundColor=#ffffff;"
)
REPLICATION_STYLE = (
    "endArrow=none;dashed=1;html=0;fontSize=11;"
    "strokeColor=#C925D1;fontColor=#C925D1;labelBackgroundColor=#ffffff;"
)

# レイアウト（px）
ICON = 60
MARGIN = 40
EXTERNAL_Y = 20
EXTERNAL_STEP = 220
EXTERNAL_LANE_Y = 120
REGION_Y = 200
GROUP_PAD = 30
GROUP_HEADER = 40
VPC_HEADER = 50
AZ_W = 440
AZ_GAP = 40
AZ_HEADER = 40
SUBNET_PAD = 20
SUBNET_H = 170
SUBNET_GAP = 20
ICON_OFFSET_X = 180
ICON_OFFSET_Y = 65
ICON_STEP_X = 170
REPLICATION_DROP = 25


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2


@dataclass
class Node:
    """図上に描くアイコン 1 つ分。per_az などでは 1 リソースが複数ノードになる。"""

    cell_id: str
    label: str
    style: str
    box: Box
    az: int | None
    row: int | None


class Diagram:
    def __init__(self) -> None:
        self.mxfile = ET.Element("mxfile")
        diagram = ET.SubElement(self.mxfile, "diagram", id="communication", name="communication")
        model = ET.SubElement(diagram, "mxGraphModel", grid="1", gridSize="10", background="#ffffff")
        self.root = ET.SubElement(model, "root")
        ET.SubElement(self.root, "mxCell", id="0")
        ET.SubElement(self.root, "mxCell", id="1", parent="0")

    def vertex(self, cell_id: str, label: str, style: str, box: Box) -> None:
        cell = ET.SubElement(self.root, "mxCell", id=cell_id, value=label, style=style, vertex="1", parent="1")
        ET.SubElement(
            cell, "mxGeometry",
            x=fmt(box.x), y=fmt(box.y), width=fmt(box.w), height=fmt(box.h),
            **{"as": "geometry"},
        )

    def edge(
        self, cell_id: str, label: str, style: str, source: str, target: str,
        label_pos: float = 0, points: list[tuple[float, float]] | None = None,
    ) -> None:
        cell = ET.SubElement(
            self.root, "mxCell",
            id=cell_id, value=label, style=style, edge="1", parent="1", source=source, target=target,
        )
        attrs = {"relative": "1", "as": "geometry"}
        if label_pos:
            attrs["x"] = fmt(label_pos)
        geometry = ET.SubElement(cell, "mxGeometry", **attrs)
        if points:
            array = ET.SubElement(geometry, "Array", **{"as": "points"})
            for x, y in points:
                ET.SubElement(array, "mxPoint", x=fmt(x), y=fmt(y))

    def tree(self) -> ET.ElementTree:
        tree = ET.ElementTree(self.mxfile)
        ET.indent(tree)
        return tree


def fmt(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def resource_style(resource_type: str) -> str:
    if resource_type in SERVICE_ICONS:
        icon, color = SERVICE_ICONS[resource_type]
        return SERVICE_ICON_STYLE.format(icon=icon, color=color)
    if resource_type in PLAIN_ICONS:
        icon, color = PLAIN_ICONS[resource_type]
        return PLAIN_ICON_STYLE.format(icon=icon, color=color)
    print(f"WARNING: {resource_type} のアイコンが未定義のため矩形で表示します", file=sys.stderr)
    return FALLBACK_STYLE


def build_diagram(data: dict) -> ET.ElementTree:
    network = data["network"]
    azs = network["availability_zones"]
    subnets = network["subnets"]

    # 枠の位置を計算する
    az_h = AZ_HEADER + len(subnets) * SUBNET_H + (len(subnets) - 1) * SUBNET_GAP + SUBNET_PAD
    vpc_w = 2 * GROUP_PAD + len(azs) * AZ_W + (len(azs) - 1) * AZ_GAP
    vpc = Box(MARGIN + GROUP_PAD, REGION_Y + GROUP_HEADER, vpc_w, VPC_HEADER + az_h + GROUP_PAD)
    region = Box(MARGIN, REGION_Y, vpc.w + 2 * GROUP_PAD, GROUP_HEADER + vpc.h + GROUP_PAD)
    az_boxes = [
        Box(vpc.x + GROUP_PAD + i * (AZ_W + AZ_GAP), vpc.y + VPC_HEADER, AZ_W, az_h)
        for i in range(len(azs))
    ]
    subnet_rows = {subnet["id"]: row for row, subnet in enumerate(subnets)}

    def subnet_box(row: int, az: int) -> Box:
        az_box = az_boxes[az]
        return Box(
            az_box.x + SUBNET_PAD,
            az_box.y + AZ_HEADER + row * (SUBNET_H + SUBNET_GAP),
            AZ_W - 2 * SUBNET_PAD,
            SUBNET_H,
        )

    # リソースをノードに展開する
    nodes: dict[str, list[Node]] = {}
    slot_in_subnet: dict[str, int] = {}

    for resource_id, resource in data["resources"].items():
        if "subnet" not in resource:
            continue
        style = resource_style(resource["type"])
        label = resource["label"]
        row = subnet_rows[resource["subnet"]]
        layout = resource.get("layout", "single")

        if layout == "span":
            y = subnet_box(row, 0).y + ICON_OFFSET_Y
            nodes[resource_id] = [Node(f"resource-{resource_id}", label, style, Box(vpc.cx - ICON / 2, y, ICON, ICON), None, row)]
            continue

        slot = slot_in_subnet.get(resource["subnet"], 0)
        slot_in_subnet[resource["subnet"]] = slot + 1

        def place(az: int) -> Box:
            sb = subnet_box(row, az)
            return Box(sb.x + ICON_OFFSET_X + slot * ICON_STEP_X, sb.y + ICON_OFFSET_Y, ICON, ICON)

        if layout == "per_az":
            nodes[resource_id] = [
                Node(f"resource-{resource_id}-{az}", label, style, place(i), i, row) for i, az in enumerate(azs)
            ]
        elif layout == "primary_standby":
            nodes[resource_id] = [
                Node(f"resource-{resource_id}-primary", f"{label}\n(Primary)", style, place(0), 0, row),
                Node(f"resource-{resource_id}-standby", f"{label}\n(Standby)", style, place(1), 1, row),
            ]
        else:
            nodes[resource_id] = [Node(f"resource-{resource_id}", label, style, place(0), 0, row)]

    # VPC 外のリソース。via 経由で到達する宛先は、最後の経由ノードの真上に置く。
    # それ以外（Users など）は VPC の中央上（Internet Gateway の真上）に並べる
    via_targets = {c["destination"]: c["via"] for c in data["communications"] if "via" in c}
    centered = [
        rid for rid, r in data["resources"].items() if "subnet" not in r and rid not in via_targets
    ]
    for resource_id, resource in data["resources"].items():
        if "subnet" in resource:
            continue
        if resource_id in via_targets:
            x = nodes[via_targets[resource_id]][-1].box.x
        else:
            j = centered.index(resource_id)
            x = vpc.cx - ICON / 2 + (j - (len(centered) - 1) / 2) * EXTERNAL_STEP
        box = Box(x, EXTERNAL_Y, ICON, ICON)
        nodes[resource_id] = [Node(f"resource-{resource_id}", resource["label"], resource_style(resource["type"]), box, None, None)]

    def route(s: Node, t: Node) -> tuple[str, list[tuple[float, float]] | None]:
        """矢印の接続位置と経由点を返す。横位置が異なる場合は、行間の隙間を通して直角に結ぶ。"""
        if t.row is None:
            # VPC 外（上）へ向かう
            style = "exitX=0.5;exitY=0;entryX=0.5;entryY=1;"
            if s.box.cx == t.box.cx:
                return style, None
            return style, [(s.box.cx, EXTERNAL_LANE_Y), (t.box.cx, EXTERNAL_LANE_Y)]
        if s.row is not None and t.row < s.row:
            # 上の行へ向かう
            style = "exitX=0.5;exitY=0;entryX=0.5;entryY=1;"
            if s.box.cx == t.box.cx:
                return style, None
            gap_y = subnet_box(t.row, 0).y + SUBNET_H + SUBNET_GAP / 2
            return style, [(s.box.cx, gap_y), (t.box.cx, gap_y)]
        # 下の行へ向かう
        if s.box.cx == t.box.cx:
            return "", None
        # 上辺の中央は上向きの矢印が使うことがあるため、左寄りに入れる
        entry_x = t.box.x + ICON * 0.25
        gap_y = subnet_box(t.row, 0).y - SUBNET_GAP / 2
        return "exitX=0.5;exitY=1;entryX=0.25;entryY=0;", [(s.box.cx, gap_y), (entry_x, gap_y)]

    def pair(sources: list[Node], targets: list[Node]) -> list[tuple[Node, Node]]:
        # 両端が AZ ごとに配置されている場合は同じ AZ 同士だけを結ぶ
        return [
            (s, t) for s in sources for t in targets
            if not (len(sources) > 1 and len(targets) > 1 and s.az != t.az)
        ]

    diagram = Diagram()

    # 1. 枠（背面）
    diagram.vertex("region", network["region"], REGION_STYLE, region)
    diagram.vertex("vpc", f"{network['vpc']['label']} ({network['vpc']['cidr']})", VPC_STYLE, vpc)
    for i, az in enumerate(azs):
        diagram.vertex(f"az-{az}", az, AZ_STYLE, az_boxes[i])
        for row, subnet in enumerate(subnets):
            diagram.vertex(
                f"subnet-{subnet['id']}-{az}",
                f"{subnet['label']}\n{subnet['cidrs'][i]}",
                SUBNET_STYLES[subnet["type"]],
                subnet_box(row, i),
            )

    # 2. 通信（枠とアイコンの間）
    for comm in data["communications"]:
        sources = nodes[comm["source"]]
        targets = nodes[comm["destination"]]
        # primary_standby への通信は Primary にのみ向ける
        if data["resources"][comm["destination"]].get("layout") == "primary_standby":
            targets = targets[:1]

        label = f"{comm['protocol'].upper()} {comm['port']}"

        if "via" in comm:
            # source -> via にラベルを付け、via -> destination はラベルなしで描く。
            # ラベルは via 寄りに置き、行間を通る他の矢印と重ならないようにする
            via_nodes = nodes[comm["via"]]
            legs = [(s, v, label, 0.5) for s, v in pair(sources, via_nodes)]
            used_vias = [v for v in via_nodes if any(leg[1] is v for leg in legs)]
            legs += [(v, t, "", 0) for v, t in pair(used_vias, targets)]
        else:
            # VPC 外からの通信は Internet Gateway と重ならないよう、ラベルを始点寄りにする
            label_pos = -0.6 if "subnet" not in data["resources"][comm["source"]] else 0
            legs = [(s, t, label, label_pos) for s, t in pair(sources, targets)]

        for s, t, leg_label, label_pos in legs:
            style, points = route(s, t)
            diagram.edge(
                f"communication-{comm['id']}-{s.cell_id}-{t.cell_id}",
                leg_label, EDGE_STYLE + style, s.cell_id, t.cell_id, label_pos, points,
            )

    # Multi-AZ のレプリケーション（通信要件ではなく AWS 管理の通信のため、点線で示す）
    for resource_id, resource in data["resources"].items():
        if resource.get("layout") != "primary_standby":
            continue
        primary, standby = nodes[resource_id]
        drop_y = primary.box.y + ICON + REPLICATION_DROP
        diagram.edge(
            f"replication-{resource_id}", "Synchronous replication", REPLICATION_STYLE + "exitX=0.5;exitY=1;entryX=0.5;entryY=1;",
            primary.cell_id, standby.cell_id,
            points=[(primary.box.cx, drop_y), (standby.box.cx, drop_y)],
        )

    # 3. アイコン（前面）。Internet Gateway は public サブネットがある場合に VPC の上辺へ置く
    if any(subnet["type"] == "public" for subnet in subnets):
        diagram.vertex("internet-gateway", "Internet gateway", IGW_STYLE, Box(vpc.cx - ICON / 2, vpc.y - ICON / 2, ICON, ICON))
    for resource_nodes in nodes.values():
        for node in resource_nodes:
            diagram.vertex(node.cell_id, node.label, node.style, node.box)

    return diagram.tree()


def main() -> int:
    data = yaml.safe_load(DEFAULT_PATH.read_text(encoding="utf-8"))

    errors = validate(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    tree = build_diagram(data)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as f:
        tree.write(f, encoding="unicode")
        f.write("\n")

    print(f"Generated: {OUTPUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
