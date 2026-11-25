provider "aws" {
  region = var.region

  # AWS Emulator 利用時の設定（use_emulator = true のときだけ有効）
  # - 全サービスを 1 つのエンドポイント（既定 https://127.0.0.1:9297）へ向ける
  # - エミュレーターの自己署名証明書を信頼する
  # - S3 はホスト名にバケット名を入れられないため path style にする
  s3_use_path_style = var.use_emulator
  custom_ca_bundle  = var.use_emulator ? pathexpand(var.emulator_ca_bundle) : null

  dynamic "endpoints" {
    for_each = var.use_emulator ? [var.emulator_endpoint] : []

    content {
      acm             = endpoints.value
      cloudwatchlogs  = endpoints.value
      ec2             = endpoints.value
      ecr             = endpoints.value
      ecs             = endpoints.value
      efs             = endpoints.value
      elbv2           = endpoints.value
      iam             = endpoints.value
      networkfirewall = endpoints.value
      rds             = endpoints.value
      s3              = endpoints.value
      secretsmanager  = endpoints.value
      ssm             = endpoints.value
      sts             = endpoints.value
    }
  }

  default_tags {
    tags = {
      Project   = var.name_prefix
      ManagedBy = "terraform"
    }
  }
}
