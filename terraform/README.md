# terraform

`specifications/communication.yaml` の構成（BimcimVPC `10.20.0.0/18`）を構築する Terraform。

リソース定義は `modules/bimcim` に共通化し、適用先ごとの provider・backend は `environments/` 配下で切り替える。

```text
terraform/
├── modules/
│   └── bimcim/            # リソース定義（全環境で共通）
└── environments/
    └── emulator/          # AWS Emulator（ローカル）向け
```

`plan` / `apply` は `environments/<環境>` ディレクトリで実行する。`modules/` では実行しない。

## modules/bimcim

| ファイル | 内容 |
|---|---|
| `network.tf` | VPC、サブネット（Firewall / Public / Private × 1a・1c）、IGW、NAT Gateway、ルートテーブル、S3 Gateway Endpoint |
| `firewall.tf` | Network Firewall（ポリシーは全通過。ルールは要件に応じて追加） |
| `security_groups.tf` | Security Group とルール（`CommunicationId` タグで YAML の通信と対応） |
| `alb.tf` | ALB（HTTPS 443。既定は Web/AP、`/api/*` は ECS）、検証用の自己署名証明書 |
| `ec2.tf` | Web/AP（EC2 × 2、SSM 管理、EFS マウント） |
| `ecs.tf` | ECR、ECS クラスター、Fargate サービス（EFS マウント） |
| `rds.tf` | RDS for PostgreSQL（Multi-AZ、パスワードは Secrets Manager 管理） |
| `efs.tf` | EFS とマウントターゲット |
| `s3.tf` | S3 バケット |

インターネットとの通信は、行き・帰りとも同じ AZ の Network Firewall endpoint を経由する。

```text
IGW ──(IGW edge RT)──> Firewall endpoint ──> Public subnet（ALB / NAT）
Public subnet ──> Firewall endpoint ──(Firewall RT)──> IGW
Private subnet ──> NAT Gateway（S3 宛ては S3 Gateway Endpoint）
```

## environments/emulator（AWS Emulator）

[AWS Emulator](https://docs.aws.amazon.com/emulator/latest/userguide/what-is-service.html) に対して `plan` / `apply` する環境。

| 項目 | 設定 |
|---|---|
| エンドポイント | `https://127.0.0.1:9297`（全サービス共通） |
| 認証情報 | エミュレーターが書き出す `~/.aws/emulator/9297/emulator_credentials`（`default` プロファイル） |
| CA 証明書 | `~/.aws/emulator/9297/ca.pem` |
| 接続を許可するアカウント | `000000000000`（エミュレーターのアカウント。実際の AWS につながった場合はエラーで止まる） |
| tfstate | ローカル（`environments/emulator/terraform.tfstate`） |

ポートを変えて起動した場合は、`providers.tf` の `emulator_port` を合わせる。

```sh
# エミュレーターを起動した状態で
cd terraform/environments/emulator
terraform init
terraform plan
terraform apply
```

注意点：

- エミュレーターは状態をメモリに保持し、停止すると `~/.aws/emulator/9297/` の認証情報も削除される。再起動したら `terraform.tfstate` を削除してから再実行する
- IAM・リソースポリシーは評価されない。Security Group などの通信制御の動作確認には使えない
- RDS / EFS には既知の不具合がある（[issues/things-that-do-not-work](https://github.com/aws/aws-emulator/tree/main/issues/things-that-do-not-work)）。apply 後の plan で差分が出ることがある

## 実際の AWS 向けの環境を追加する場合

`environments/emulator` をコピーして `environments/<環境名>` を作り、以下を変更する。

- `providers.tf`：`endpoints`・`custom_ca_bundle`・`s3_use_path_style`・認証情報ファイルの指定を削除し、`allowed_account_ids` に対象アカウントの ID を指定する。認証情報は `AWS_PROFILE` などで渡す
- `backend.tf`：tfstate を S3 などのリモートに置く
- `main.tf`：`certificate_arn` に正式な ACM 証明書、`alb_ingress_cidrs` に CloudWAF の送信元 IP などを指定する。`db_deletion_protection` / `db_skip_final_snapshot` は既定値（削除保護あり）に戻す
- `.terraform.lock.hcl`：全 OS 分のハッシュを記録する（`terraform providers lock -platform=windows_amd64 -platform=darwin_arm64 -platform=linux_amd64`）
- `.github/workflows/terraform.yml` の `matrix.environment` に追加する
