# requirements

通信要件を管理するディレクトリ。`communication.yaml` が正本。

| ファイル | 内容 |
|---|---|
| `communication.yaml` | 通信要件（resources / communications） |
| `communication.schema.json` | `communication.yaml` の JSON Schema |

## 検証

リポジトリ直下で以下を順に実行する。

```sh
uv run yamllint .
uv run check-jsonschema --schemafile requirements/communication.schema.json requirements/communication.yaml
uv run python scripts/validate_communication.py
```
