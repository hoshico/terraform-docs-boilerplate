# diagrams

`requirements/communication.yaml` を正本とする構成図（draw.io / SVG）を配置するディレクトリ。

`communication.drawio` は AI が YAML を参照して編集する。編集時は必ず
[AGENTS.md](AGENTS.md) の AWS 構成図の規約に従う。

| ファイル | 更新方法 |
|---|---|
| `communication.drawio` | AI が YAML と `AGENTS.md` を基に編集 |
| `communication.svg` | `uv run python scripts/export_svg.py`（draw.io デスクトップが必要） |

SVG は draw.io のバージョンにより出力が変わる可能性がある。`communication.drawio` を変更したら SVG を更新し、内容と表示を確認する。

## AI Skill / MCP のセットアップ

このリポジトリには、GitHub Copilot が自動検出するプロジェクト Skill を
`.github/skills/aws-drawio/SKILL.md` に置いている。AWS の図を更新するときは、
この Skill と `AGENTS.md` を適用する。

draw.io の生成・形状検索・SVG 出力には、draw.io 公式プラグインを各クライアントへ
導入する。

```sh
# Codex CLI
codex plugin marketplace add jgraph/drawio-mcp
codex plugin add drawio@drawio

# GitHub Copilot CLI
copilot plugin marketplace add jgraph/drawio-mcp
copilot plugin install drawio@drawio
```

チャット内プレビューと AWS4 形状検索を使いたい場合は、MCP App Server
`https://mcp.draw.io/mcp` をクライアントの MCP 設定へ追加する。ホスト型 MCP には
図の内容を送信するため、機密情報を含む図ではローカル MCP または公式プラグインの
ローカル出力を使う。
