# 通信の暗号化対応

`specifications/communication.yaml`（BimcimVPC）の通信要件ごとに、通信経路（in-transit）の暗号化方法を整理する。

- 作成日：2026-11-25
- 対象：`specifications/communication.yaml` の communications（11件）
- 「現状」は `terraform/` の現在の実装を指す

## 通信要件ごとの暗号化方法

| ID | Source | Destination | Via | Protocol | Port | Description | 暗号化方式 | 現状 | 必要な対応 |
|---|---|---|---|---|---|---|---|---|---|
| users-to-alb | users | alb |  | tcp | 443 | 利用者からALBへのHTTPS通信（Network Firewall経由） | TLS（ALB の HTTPS リスナーで終端） | 対応済み（HTTPS リスナー、TLS 1.2 以上のポリシー `ELBSecurityPolicy-TLS13-1-2-2021-06`）。ただし `certificate_arn` 未指定時は自己署名証明書 | ・`certificate_arn` に正式な ACM 証明書（Route 53 の独自ドメイン）を指定する<br>・CloudWAF → ALB 間も HTTPS にする（CloudWAF のオリジン設定を HTTPS にする） |
| alb-to-web-ap | alb | web-ap |  | tcp | 80 | ALBからWeb/APサーバーへのHTTP通信 | TLS（ALB → EC2 を HTTPS で再暗号化） | **未対応（平文 HTTP）** | ・Web/AP（nginx / Apache など）で TLS を受ける。証明書は自己署名で可（ALB はターゲットの証明書を検証しない）<br>・ターゲットグループを `protocol = "HTTPS"`、`port = 443` に変更する<br>・ポートが 80 → 443 に変わるため、YAML の port、SG ルール（`alb_to_web_ap` / `web_ap_from_alb`）、構成図のラベルを更新する |
| alb-to-ecs | alb | ecs |  | tcp | 3000 | ALBからECSへのアプリケーション通信 | TLS（ALB → Fargate を HTTPS で再暗号化） | **未対応（平文 HTTP）** | ・コンテナで TLS を受ける。アプリで直接受けるか、サイドカー（nginx / Envoy）で TLS を終端する。証明書は自己署名で可<br>・ターゲットグループを `protocol = "HTTPS"` に変更する（ポート 3000 は維持）<br>・ヘルスチェックも HTTPS にする |
| web-ap-to-rds | web-ap | rds |  | tcp | 5432 | Web/APサーバーからRDSへのデータベース接続 | TLS（PostgreSQL の SSL 接続） | 一部対応（PostgreSQL 17 は `rds.force_ssl` の既定値が 1 のため SSL が強制される。保存時の暗号化は `storage_encrypted = true`） | ・DB パラメータグループを作成し、`rds.force_ssl = 1` を明示する（既定値への依存をなくす）<br>・アプリの接続設定を `sslmode=verify-full` にし、RDS の CA バンドル（`global-bundle.pem`）でサーバー証明書を検証する<br>・`ca_cert_identifier`（例：`rds-ca-rsa2048-g1`）を明示する |
| ecs-to-rds | ecs | rds |  | tcp | 5432 | ECSからRDSへのデータベース接続 | TLS（PostgreSQL の SSL 接続） | 同上 | ・web-ap-to-rds と同じ<br>・CA バンドルはコンテナイメージに含める |
| web-ap-to-efs | web-ap | efs |  | tcp | 2049 | Web/APサーバーからEFSへのNFS接続 | TLS（EFS マウントヘルパーの `tls` オプション） | 対応済み（user_data で `amazon-efs-utils` を使い、`tls` オプション付きでマウント） | ・EFS のファイルシステムポリシーで `aws:SecureTransport = false` を拒否し、TLS なしのマウントを禁止する（`aws_efs_file_system_policy`） |
| ecs-to-efs | ecs | efs |  | tcp | 2049 | ECSからEFSへのNFS接続 | TLS（ECS タスク定義の転送時暗号化） | 対応済み（`transit_encryption = "ENABLED"`） | ・web-ap-to-efs と同じファイルシステムポリシーで強制する |
| web-ap-to-internet | web-ap | internet | nat | tcp | 443 | Web/APサーバーからNAT Gateway・Network Firewall経由でSystems Manager・Garoon・WebexへのHTTPS通信 | TLS（HTTPS） | 対応済み（SG の egress を TCP 443 のみに限定。SSM などの AWS API は HTTPS） | ・アプリから Garoon / Webex への接続で証明書検証を無効にしていないことを確認する（TLS 1.2 以上）<br>・必要に応じて Network Firewall のステートフルルールで、443 番の TLS 以外の通信や許可ドメイン（SNI）以外を拒否する |
| ecs-to-internet | ecs | internet | nat | tcp | 443 | ECSからNAT Gateway・Network Firewall経由でECR・CloudWatch Logs・Autodesk ForgeへのHTTPS通信 | TLS（HTTPS） | 対応済み（SG の egress を TCP 443 のみに限定。ECR・CloudWatch Logs は HTTPS） | ・アプリから Autodesk Forge への接続で証明書検証を無効にしていないことを確認する（TLS 1.2 以上）<br>・Network Firewall のルールは web-ap-to-internet と同じ |
| web-ap-to-s3 | web-ap | s3 |  | tcp | 443 | Web/APサーバーからS3 Gateway Endpoint経由でS3へのHTTPS通信 | TLS（HTTPS） | 一部対応（SG で TCP 443 のみ許可。バケット側では HTTP を拒否していない） | ・バケットポリシーで `aws:SecureTransport = false` を拒否する<br>・あわせて `s3:TlsVersion < 1.2` を拒否する |
| ecs-to-s3 | ecs | s3 |  | tcp | 443 | ECSからS3 Gateway Endpoint経由でS3へのHTTPS通信（ECRイメージレイヤー取得を含む） | TLS（HTTPS） | 同上 | ・web-ap-to-s3 と同じバケットポリシーで強制する（ECR のレイヤー取得は AWS 管理のバケットのため対象外。HTTPS で行われる） |

## 対応の優先度

| 優先度 | 対象 | 理由 |
|---|---|---|
| 高 | alb-to-web-ap、alb-to-ecs | 現状は VPC 内を平文 HTTP で流れている |
| 中 | web-ap-to-rds、ecs-to-rds、web-ap-to-s3、ecs-to-s3、web-ap-to-efs、ecs-to-efs | 暗号化はされているが、サーバー側での強制やクライアント側での証明書検証が明示されていない |
| 低 | users-to-alb、web-ap-to-internet、ecs-to-internet | 暗号化済み。正式な証明書への差し替えと運用上の確認のみ |

## 変更時の注意

- alb-to-web-ap のポートを 443 に変えた場合は、YAML・Terraform の SG ルール・構成図・CSV をそろえて更新する（AGENTS.md 3.2 の照合対象）
- 通信経路の暗号化とは別に、保存時の暗号化（RDS・EFS・EBS は Terraform で有効化済み、S3 は既定の SSE-S3）も確認対象とする
