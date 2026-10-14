# AGENTS.md

## 1. プロジェクト概要

このリポジトリは、AWSインフラの通信要件をコードとして管理し、
Terraformによるインフラ構築と設計ドキュメントの自動生成を実現する
ボイラープレートです。

主な目的は以下のとおりです。

- AWSの通信要件をGitHubで一元管理する
- 通信要件をYAMLで定義する
- YAMLからTerraformの設定を生成・反映する
- YAMLからAWS構成図（draw.io）を自動生成する
- draw.ioからSVGを生成し、GitHub上で閲覧できるようにする
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
| 自動生成スクリプト | Python |
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
                      +-- CSV
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

### 3.3 設計ドキュメントは自動生成する

通信要件YAMLから以下を生成する。

1. CSV形式の通信要件一覧
2. AWS公式アイコンを使用したdraw.io構成図
3. GitHub上で表示するSVG

生成されたファイルは原則として直接編集しない。

変更が必要な場合は、元となるYAMLまたは生成処理を修正する。

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
│   ├── generate_diagram.py
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

## 7. draw.io生成

### 7.1 基本方針

Pythonを使用して、通信要件YAMLからdraw.io形式のXMLを生成する。

draw.ioではAWSのアーキテクチャアイコンを使用する。

対象例：

- Application Load Balancer
- Amazon ECS
- Amazon RDS
- Amazon EC2
- Amazon S3
- Amazon VPC

### 7.2 AWSアイコン

AWS公式のArchitecture Iconsを使用する。

https://aws.amazon.com/architecture/icons/

draw.ioのAWSアイコンライブラリを利用する方法も検討する。

アイコンの識別子はリソースタイプから判定する。

例：

```text
aws_alb -> ALB icon
aws_ecs -> ECS icon
aws_rds -> RDS icon
```

draw.ioのXML生成時には、使用するアイコンのスタイル識別子を確認すること。

### 7.3 レイアウト

初期PoCでは、上から下への単純なレイアウトとする。

```text
ALB
 |
 v
ECS
 |
 v
RDS
```

将来的には以下を検討する。

- VPCの枠
- Public / Private Subnet
- Availability Zone
- 通信方向
- ポート番号
- 環境別の構成図

ただし、初期段階では自動レイアウトの高度化を優先しない。

---

## 8. SVG生成

draw.ioファイルからSVGを生成する。

基本フロー：

```text
communication.yaml
        |
        v
generate_diagram.py
        |
        v
communication.drawio
        |
        v
draw.io CLI
        |
        v
communication.svg
```

draw.io CLIなどを使用してエクスポートする。

生成したSVGはGitHubのREADMEから参照する。

```markdown
![AWS Communication Diagram](docs/diagrams/communication.svg)
```

AWSアイコンがSVGに正しく出力されることを確認する。

---

## 9. CSV生成

YAMLのcommunicationsからCSVを生成する。

出力イメージ：

| ID | Source | Destination | Protocol | Port | Description |
|---|---|---|---|---|---|
| alb-to-ecs | alb | ecs | tcp | 3000 | ALBからECSへの通信 |
| ecs-to-rds | ecs | rds | tcp | 5432 | ECSからRDSへの通信 |

CSVはYAMLから自動生成する。

手動での編集は行わない。

---

## 10. Terraform

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

## 11. GitHub Actions

Pull Request時に以下を実行する。

1. yamllint
2. JSON Schema検証
3. 追加の整合性チェック
4. CSV生成
5. draw.io生成
6. SVG生成
7. Terraform fmt
8. Terraform validate

生成物をGitで管理する場合は、
生成前後に差分がないことも検証する。

Terraform planは、AWS認証情報や対象環境が整備された段階で追加する。

GitHub ActionsからAWSへアクセスする場合は、
長期アクセスキーではなくOIDCによる認証を優先する。

---

## 12. 実装順序

以下の順序で実装する。

### Phase 1：通信要件の定義

- communication.yamlを作成
- JSON Schemaを作成
- yamllintを導入
- YAMLの検証を実装

### Phase 2：ドキュメント生成

- YAMLからCSVを生成
- YAMLからdraw.ioを生成
- AWSアイコンを表示
- draw.ioからSVGを生成
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

## 13. Codexへの作業指示

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
- 生成物に通信要件を直接記述しない
- 再生成しても結果が安定するようにする
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

## 14. 最初のゴール

初期PoCの完成条件は以下とする。

- ALB → ECS → RDSの通信要件がYAMLで定義されている
- YAMLの構文とスキーマが検証できる
- YAMLからCSVが生成できる
- YAMLからAWSアイコン付きdraw.ioが生成できる
- draw.ioからSVGが生成できる
- GitHub上でSVGを表示できる
- TerraformからYAMLを読み込める
- Terraformの静的検証が成功する

まずは小さく動作する構成を完成させ、
その後に複数環境や複雑なAWS構成への対応を進める。