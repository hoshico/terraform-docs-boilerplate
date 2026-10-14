# tables

`requirements/communication.yaml` から自動生成される通信要件一覧（CSV）を配置するディレクトリ。

生成物のため直接編集しない。

| ファイル | 生成コマンド |
|---|---|
| `communication.csv` | `uv run python scripts/generate_csv.py` |

CSV は Excel（Windows）で文字化けしないよう、BOM 付き UTF-8・改行 LF で出力する。
