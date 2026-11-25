# terraform

`specifications/communication.yaml` の構成（BimcimVPC `10.20.0.0/18`）を構築する Terraform。

## 構成

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

## AWS Emulator で確認する

[AWS Emulator](https://docs.aws.amazon.com/emulator/latest/userguide/what-is-service.html) を起動した状態で、`use_emulator=true` を指定する。
エンドポイントは `https://127.0.0.1:9297`、CA バンドルは `~/.aws/emulator/9297/ca.pem` を既定値としている（変数で変更可）。

```sh
cd terraform
terraform init
terraform plan  -var use_emulator=true -var db_skip_final_snapshot=true -var db_deletion_protection=false
terraform apply -var use_emulator=true -var db_skip_final_snapshot=true -var db_deletion_protection=false
```

認証情報はエミュレーターが出力するもの（`~/.aws/emulator/9297/` 配下）を `AWS_PROFILE` などで指定するか、
エミュレーターを認証なし（`--auth off`）で起動する。詳細はエミュレーターのドキュメントを確認すること。

注意点：

- エミュレーターは状態をメモリに保持する。再起動すると tfstate と食い違うため、`terraform.tfstate` を削除してから再実行する
- IAM・リソースポリシーは評価されない。Security Group などの通信制御の動作確認には使えない
- RDS / EFS には既知の不具合がある（[issues/things-that-do-not-work](https://github.com/aws/aws-emulator/tree/main/issues/things-that-do-not-work)）。apply 後の plan で差分が出ることがある

## 実際の AWS に適用する場合

- `certificate_arn` に ACM 証明書を指定する（未指定だと自己署名証明書を作成し、秘密鍵が tfstate に入る）
- `alb_ingress_cidrs` を CloudWAF の送信元 IP などに絞る
- ECS タスクを起動するには、ECR リポジトリにイメージ（既定タグ `latest`）を push しておく
