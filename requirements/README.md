# requirements

通信要件を管理するディレクトリ。`communication.yaml` が正本。

| ファイル | 内容 |
|---|---|
| `communication.yaml` | 通信要件（network / resources / communications） |
| `communication.schema.json` | `communication.yaml` の JSON Schema |

## communication.yaml の構造

| キー | 内容 |
|---|---|
| `network` | Region・VPC・AZ・サブネット（AZ ごとの CIDR）。構成図の枠になる |
| `resources` | 通信の端点となるリソース。`subnet` と `layout` で配置先を指定する |
| `communications` | リソース間の通信（protocol / port / description） |

### resources の配置

`subnet` を省略したリソース（`type: users` / `type: internet` など）は VPC 外に配置する。

| `layout` | 配置 | 例 |
|---|---|---|
| `single`（省略時） | 先頭の AZ に 1 つ | 単一 AZ の EC2 |
| `span` | AZ をまたいで 1 つ | ALB |
| `per_az` | 各 AZ に 1 つずつ | ECS タスク |
| `primary_standby` | 先頭の AZ に Primary、2 番目の AZ に Standby | RDS Multi-AZ |

`primary_standby` のリソースへの通信は Primary にのみ向ける。Primary・Standby 間のレプリケーションは AWS 管理の通信のため、通信要件には含めず構成図に点線で示す。

### communications の via

NAT Gateway のように、Security Group で制御しない中継点を経由する通信は `via` で指定する。

```yaml
- id: ecs-to-aws-services
  source: ecs
  destination: aws-services
  via: nat
  protocol: tcp
  port: 443
```

`via` には VPC 内（`subnet` を持つ）リソースを指定する。構成図では `source -> via -> destination` の 2 本の矢印で描く。

## 検証

リポジトリ直下で以下を順に実行する。

```sh
uv run yamllint .
uv run check-jsonschema --schemafile requirements/communication.schema.json requirements/communication.yaml
uv run python scripts/validate_communication.py
```
