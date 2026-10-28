# diagrams

`requirements/communication.yaml` を正本とする構成図（draw.io / SVG）を配置するディレクトリ。

`communication.drawio` は AI が YAML を参照して編集する。編集時は必ず [AGENTS.md](AGENTS.md) のスタイルと整合性の規約に従う。

| ファイル | 更新方法 |
|---|---|
| `communication.drawio` | AI が YAML と `AGENTS.md` を基に編集 |
| `communication.svg` | `uv run python scripts/export_svg.py`（draw.io デスクトップが必要） |

SVG は draw.io のバージョンにより出力が変わる可能性がある。`communication.drawio` を変更したら SVG を更新し、内容と表示を確認する。
