# AWS Emulator（https://docs.aws.amazon.com/emulator/latest/userguide/what-is-service.html）向けの provider 設定。
# エミュレーターは起動時に ~/.aws/emulator/<port>/ へ CA 証明書・認証情報・config を書き出す。
locals {
  emulator_port     = 9297
  emulator_endpoint = "https://127.0.0.1:${local.emulator_port}"
  emulator_dir      = pathexpand("~/.aws/emulator/${local.emulator_port}")
}

provider "aws" {
  region = "ap-northeast-1"

  # エミュレーターが書き出す認証情報を使う（実際の AWS の認証情報を使わない）
  shared_credentials_files = ["${local.emulator_dir}/emulator_credentials"]
  shared_config_files      = ["${local.emulator_dir}/config"]
  profile                  = "default"

  # エミュレーターのアカウント（000000000000）以外には接続しない
  allowed_account_ids = ["000000000000"]

  # エミュレーターの自己署名証明書を信頼する
  custom_ca_bundle = "${local.emulator_dir}/ca.pem"

  # S3 はホスト名にバケット名を入れられないため path style にする
  s3_use_path_style = true

  # 全サービスをエミュレーターのエンドポイントへ向ける
  endpoints {
    acm             = local.emulator_endpoint
    cloudwatchlogs  = local.emulator_endpoint
    ec2             = local.emulator_endpoint
    ecr             = local.emulator_endpoint
    ecs             = local.emulator_endpoint
    efs             = local.emulator_endpoint
    elbv2           = local.emulator_endpoint
    iam             = local.emulator_endpoint
    networkfirewall = local.emulator_endpoint
    rds             = local.emulator_endpoint
    s3              = local.emulator_endpoint
    secretsmanager  = local.emulator_endpoint
    ssm             = local.emulator_endpoint
    sts             = local.emulator_endpoint
  }

  default_tags {
    tags = {
      Project     = "bimcim-pro"
      Environment = "emulator"
      ManagedBy   = "terraform"
    }
  }
}
