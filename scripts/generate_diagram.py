"""通信要件 YAML から draw.io 構成図を生成する。

初期 PoC として、resources を YAML の定義順に上から下へ並べる。
矢印と重ならないよう、リソース名はアイコンの右側に表示する。
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from validate_communication import DEFAULT_PATH, validate

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "docs" / "diagrams" / "communication.drawio"

# リソースタイプ -> (draw.io の AWS アイコン識別子, AWS カテゴリ色)
# 識別子は draw.io の AWS4 アイコンライブラリ（mxgraph.aws4.*）に合わせる
AWS_ICONS = {
    "aws_alb": ("elastic_load_balancing", "#8C4FFF"),
    "aws_ecs": ("ecs", "#ED7100"),
    "aws_rds": ("rds", "#C925D1"),
}

ICON_STYLE = (
    "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;"
    "fillColor={color};strokeColor=#ffffff;dashed=0;"
    "labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=8;"
    "html=0;fontSize=12;fontStyle=0;aspect=fixed;"
    "shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.{icon};"
)
FALLBACK_STYLE = "rounded=1;whiteSpace=wrap;html=0;fontColor=#232F3E;strokeColor=#232F3E;"
EDGE_STYLE = (
    "endArrow=block;endFill=1;html=0;fontSize=12;"
    "strokeColor=#232F3E;fontColor=#232F3E;labelBackgroundColor=#ffffff;"
)

ICON_SIZE = 78
X = 120
Y_START = 40
Y_STEP = 180


def resource_style(resource_type: str) -> str:
    if resource_type not in AWS_ICONS:
        print(f"WARNING: {resource_type} のアイコンが未定義のため矩形で表示します", file=sys.stderr)
        return FALLBACK_STYLE
    icon, color = AWS_ICONS[resource_type]
    return ICON_STYLE.format(icon=icon, color=color)


def build_diagram(data: dict) -> ET.ElementTree:
    mxfile = ET.Element("mxfile")
    diagram = ET.SubElement(mxfile, "diagram", id="communication", name="communication")
    model = ET.SubElement(diagram, "mxGraphModel", grid="1", gridSize="10", background="#ffffff")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    for i, (resource_id, resource) in enumerate(data["resources"].items()):
        cell = ET.SubElement(
            root, "mxCell",
            id=f"resource-{resource_id}",
            value=resource["label"],
            style=resource_style(resource["type"]),
            vertex="1",
            parent="1",
        )
        ET.SubElement(
            cell, "mxGeometry",
            x=str(X), y=str(Y_START + i * Y_STEP),
            width=str(ICON_SIZE), height=str(ICON_SIZE),
            **{"as": "geometry"},
        )

    for comm in data["communications"]:
        cell = ET.SubElement(
            root, "mxCell",
            id=f"communication-{comm['id']}",
            value=f"{comm['protocol'].upper()} {comm['port']}",
            style=EDGE_STYLE,
            edge="1",
            parent="1",
            source=f"resource-{comm['source']}",
            target=f"resource-{comm['destination']}",
        )
        ET.SubElement(cell, "mxGeometry", relative="1", **{"as": "geometry"})

    tree = ET.ElementTree(mxfile)
    ET.indent(tree)
    return tree


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
