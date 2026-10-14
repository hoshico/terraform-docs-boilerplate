# diagrams

`requirements/communication.yaml` から自動生成される構成図（draw.io / SVG）を配置するディレクトリ。

生成物のため直接編集しない。

| ファイル | 生成コマンド |
|---|---|
| `communication.drawio` | `uv run python scripts/generate_diagram.py` |
| `communication.svg` | `uv run python scripts/export_svg.py`（draw.io デスクトップが必要） |

SVG は draw.io のバージョンにより出力が変わる可能性がある。差分チェックは CI（固定バージョン）で行う。
