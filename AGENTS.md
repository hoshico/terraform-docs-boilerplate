# AGENTS.md

## 1. プロジェクト概要

このリポジトリは、AWSインフラの通信要件をコードとして管理し、
Terraformによるインフラ構築と、設計ドキュメントの自動生成・AI編集を実現する
ボイラープレートです。

主な目的は以下のとおりです。

- AWSの通信要件をGitHubで一元管理する
- 通信要件をYAMLで定義する
- YAMLからTerraformの設定を生成・反映する
- YAMLを正本として、AIがAWS構成図（draw.io）を編集する
- draw.ioからSVGを出力し、GitHub上で閲覧できるようにする
- YAMLから通信要件一覧（CSV）を生成する
- GitHub Actionsで検証と生成処理を自動化する
- Terraformと設計ドキュメントを同じリポジトリで管理する

最終的には、通信要件の変更をPull Requestでレビューするだけで、
Terraformと設計ドキュメントの整合性を維持できる構成を目指します。

---

## 2. 技術スタック

| 用途 | 技術 |
|---|---|
| 通信要件定義 | YAML |
| YAML構文・スタイル検証 | yamllint |
| YAMLスキーマ検証 | JSON Schema |
| スキーマ検証ツール | check-jsonschema |
| インフラ構築 | Terraform |
| AWS構成図 | draw.io（diagrams.net） |
| 図の表示形式 | SVG |
| 通信要件一覧 | CSV |
| 検証・CSV生成スクリプト | Python |
| CI/CD | GitHub Actions |
| バージョン管理 | Git / GitHub |

### 使用しない技術

- TypeScript
- Valibot
- Node.jsを前提とした独自ツール

原則として、Terraform・Python・既存CLIツールを利用する。

---

## 3. 基本設計方針

### 3.1 YAMLをSingle Source of Truthとする

通信要件はYAMLを正本として管理する。

Terraformや設計ドキュメントに同じ通信要件を重複定義しない。

```text
Communication Requirements (YAML)
                |
                +-- Validation
                |     +-- yamllint
                |     +-- JSON Schema
                |
                +-- Terraform
                |     +-- Security Groups
                |
                +-- Python
                |     +-- CSV
                |
                +-- AI
                      +-- draw.io
                             +-- SVG
```

### 3.2 TerraformはYAMLを直接参照する

Terraformでは `yamldecode()` を使用する。

```hcl
locals {
  communication = yamldecode(
    file("${path.module}/../requirements/communication.yaml")
  )
}
```

YAMLの通信要件をもとに、必要なSecurity Groupルールなどを作成する。

ただし、すべての通信要件がSecurity Groupで表現できるわけではない。

例えば以下は個別に扱う。

- Security Groupで制御する通信
- VPC Endpointを利用する通信
- 外部SaaSへのHTTPS通信
- SAML / OIDCによる認証通信

通信要件とAWSリソースの対応を明確にすること。

### 3.3 設計ドキュメントを管理する

通信要件YAMLを基に、以下の設計ドキュメントを管理する。

1. CSV形式の通信要件一覧（自動生成）
2. AWS公式アイコンを使用したdraw.io構成図（AIが編集）
3. GitHub上で表示するSVG（draw.ioから出力）

CSV は自動生成するため直接編集しない。draw.io 図は `docs/diagrams/AGENTS.md` の規約に従って AI が編集し、変更後に SVG を出力する。

---

## 4. ディレクトリ構成

以下は推奨構成であり、既存のディレクトリ構成がある場合はそれを優先する。

```text
.
├── AGENTS.md
├── README.md
│
├── requirements/
│   ├── communication.yaml
│   └── communication.schema.json
│
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
│
├── scripts/
│   └── generate_csv.py
│
├── docs/
│   ├── diagrams/
│   │   ├── communication.drawio
│   │   └── communication.svg
│   └── tables/
│       └── communication.csv
│
└── .github/
    └── workflows/
        └── validate.yml
```

必要に応じてディレクトリやファイルを追加してよい。

ただし、最初から過度に複雑な構成にしないこと。

---

## 5. 通信要件YAML

初期PoCでは、以下のAWS構成を対象とする。

```text
ALB
 |
 | TCP 3000
 v
ECS
 |
 | TCP 5432
 v
RDS (PostgreSQL)
```

YAMLの定義例：

```yaml
resources:
  alb:
    type: aws_alb
    label: Application Load Balancer

  ecs:
    type: aws_ecs
    label: ECS Application

  rds:
    type: aws_rds
    label: PostgreSQL

communications:
  - id: alb-to-ecs
    source: alb
    destination: ecs
    protocol: tcp
    port: 3000
    description: ALBからECSへのアプリケーション通信

  - id: ecs-to-rds
    source: ecs
    destination: rds
    protocol: tcp
    port: 5432
    description: ECSからRDSへのデータベース接続
```

### YAML設計時の注意点

- 通信要件には一意のIDを付与する
- sourceとdestinationはresourcesで定義したIDを参照する
- protocolとportを明示する
- 通信目的をdescriptionに記載する
- 必要に応じて環境情報を追加できる設計にする
- Terraform固有の値と論理的な通信要件を可能な限り分離する

YAMLの構造はPoCで検証しながら改善してよい。

---

## 6. YAMLバリデーション

### 6.1 yamllint

YAMLの構文およびスタイルを検証する。

### 6.2 JSON Schema

以下を検証する。

- 必須フィールド
- データ型
- protocolの許可値
- portの範囲（1〜65535）
- resourcesとcommunicationsの基本構造

### 6.3 追加の整合性チェック

JSON Schemaだけでは検証が難しい項目については、
必要に応じてPythonで検証する。

例：

- 通信IDの重複
- 未定義のsource / destination
- 不正なリソース参照

バリデーションに失敗した場合は、生成処理を中断する。

---

## 7. draw.io 編集と SVG 出力

`requirements/communication.yaml` を正本として、AI が `docs/diagrams/communication.drawio` を編集する。Python スクリプトで draw.io XML を自動生成しない。

AI は `docs/diagrams/AGENTS.md` の規約に従い、AWS4 アイコン、配色、レイアウト、通信線のスタイルを維持する。YAML にないリソースや通信を図へ追加しない。

図を更新したら、draw.io から `docs/diagrams/communication.svg` を出力する。SVG は GitHub の README から参照する。

```markdown
![AWS Communication Diagram](docs/diagrams/communication.svg)
```

---

## 8. CSV生成

YAMLのcommunicationsからCSVを生成する。

出力イメージ：

| ID | Source | Destination | Protocol | Port | Description |
|---|---|---|---|---|---|
| alb-to-ecs | alb | ecs | tcp | 3000 | ALBからECSへの通信 |
| ecs-to-rds | ecs | rds | tcp | 5432 | ECSからRDSへの通信 |

CSVはYAMLから自動生成する。

手動での編集は行わない。

---

## 9. Terraform

### 基本方針

- TerraformはYAMLを `yamldecode()` で読み込む
- 通信要件からSecurity Groupルールを生成する
- `for_each` を利用し、通信IDを安定したキーとして扱う
- AWSリソースIDとYAMLの論理IDの対応を明確にする
- Terraformの変更内容はplanで確認する

### 注意点

- すべての通信をSecurity Groupルールに変換しない
- ingress / egressの方向を正しく扱う
- 必要以上に広いCIDRを許可しない
- Security Group間参照を優先的に検討する
- Terraformの差分が意図しないリソース削除を引き起こさないようにする

初期PoCでは、実際のAWS環境へのデプロイを必須としない。

---

## 10. GitHub Actions

Pull Request時に以下を実行する。

1. yamllint
2. JSON Schema検証
3. 追加の整合性チェック
4. CSV生成
5. Terraform fmt
6. Terraform validate

生成物をGitで管理する場合は、
生成前後に差分がないことも検証する。

Terraform planは、AWS認証情報や対象環境が整備された段階で追加する。

GitHub ActionsからAWSへアクセスする場合は、
長期アクセスキーではなくOIDCによる認証を優先する。

---

## 11. 実装順序

以下の順序で実装する。

### Phase 1：通信要件の定義

- communication.yamlを作成
- JSON Schemaを作成
- yamllintを導入
- YAMLの検証を実装

### Phase 2：ドキュメント生成

- YAMLからCSVを生成
- YAMLを正本としてAIがdraw.ioを編集
- draw.ioからSVGを出力
- READMEにSVGを表示

### Phase 3：Terraform連携

- TerraformでYAMLを読み込む
- 通信要件とSecurity Groupを対応させる
- Terraform fmt / validateを実行
- Terraform planで変更内容を確認

### Phase 4：CI/CD

- GitHub Actionsを導入
- PR時にYAMLを検証
- ドキュメント生成を検証
- Terraformの静的検証を実行

---

## 12. Codexへの作業指示

このリポジトリで作業するAIエージェントは、以下のルールに従うこと。

### 実装前

1. 既存のディレクトリ構成を確認する
2. 既存ファイルの内容を確認する
3. 必要な変更内容を整理する
4. 既存の設計方針との整合性を確認する

### 実装時

- TypeScriptを使用しない
- 必要以上に依存ライブラリを増やさない
- Pythonは標準ライブラリを優先する
- YAMLを通信要件の正本として扱う
- 図に記載する通信要件をYAMLと一致させる
- スクリプトはローカルでも実行可能にする
- シンプルで理解しやすい実装を優先する

### 検証時

- YAMLのバリデーションを実行する
- 生成したCSVの内容を確認する
- draw.ioファイルが開けることを確認する
- SVGでAWSアイコンが表示されることを確認する
- Terraform fmt / validateを実行する

### 禁止事項

- ユーザーの許可なくAWSリソースを作成・変更・削除しない
- ユーザーの許可なくTerraform applyを実行しない
- AWS認証情報やシークレットをリポジトリに保存しない
- 既存ファイルを理由なく削除しない
- YAMLとTerraformに通信要件を二重管理しない

---

## 13. 最初のゴール

初期PoCの完成条件は以下とする。

- ALB → ECS → RDSの通信要件がYAMLで定義されている
- YAMLの構文とスキーマが検証できる
- YAMLからCSVが生成できる
- YAMLと整合するAWSアイコン付きdraw.ioをAIが編集できる
- draw.ioからSVGを出力できる
- GitHub上でSVGを表示できる
- TerraformからYAMLを読み込める
- Terraformの静的検証が成功する

まずは小さく動作する構成を完成させ、
その後に複数環境や複雑なAWS構成への対応を進める。
