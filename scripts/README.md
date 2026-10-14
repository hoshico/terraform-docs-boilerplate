# scripts

検証・生成用の Python スクリプトを配置するディレクトリ。

`uv run python scripts/<script>.py` で実行する。

| スクリプト | 内容 |
|---|---|
| `validate_communication.py` | 通信要件 YAML の整合性チェック（ID 重複・未定義参照など） |
| `generate_csv.py` | 通信要件一覧 CSV（`docs/tables/communication.csv`）を生成 |
| `generate_diagram.py` | 構成図（`docs/diagrams/communication.drawio`）を生成 |
| `export_svg.py` | draw.io CLI で構成図を SVG（`docs/diagrams/communication.svg`）に出力 |

生成スクリプト（`generate_*.py`）は実行前に整合性チェックを行い、失敗した場合は生成を中断する。

`export_svg.py` は draw.io の実行ファイルを環境変数 `DRAWIO_PATH` → PATH → OS ごとの標準インストール先の順で探す。
