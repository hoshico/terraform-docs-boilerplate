variable "region" {
  description = "AWS リージョン（provider と同じ値を指定する）"
  type        = string
}

variable "name_prefix" {
  description = "リソース名の接頭辞"
  type        = string
}

# ---------------------------------------------------------------
# ALB
# ---------------------------------------------------------------

variable "alb_ingress_cidrs" {
  description = "ALB（HTTPS）への接続を許可する CIDR。CloudWAF を経由させる場合は CloudWAF の送信元 IP に絞る"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "certificate_arn" {
  description = "ALB の HTTPS リスナーで使う ACM 証明書の ARN。null の場合は自己署名証明書を作成して ACM にインポートする（検証用）"
  type        = string
  default     = null
}

variable "ecs_path_patterns" {
  description = "ALB で ECS（Fargate）へ振り分けるパス。これ以外は Web/AP（EC2）へ振り分ける"
  type        = list(string)
  default     = ["/api/*"]
}

# ---------------------------------------------------------------
# Web/AP（EC2）
# ---------------------------------------------------------------

variable "web_ap_instance_type" {
  description = "Web/AP サーバーのインスタンスタイプ"
  type        = string
  default     = "t3.small"
}

# ---------------------------------------------------------------
# ECS（Fargate）
# ---------------------------------------------------------------

variable "app_image_tag" {
  description = "ECS タスクで使う ECR イメージのタグ"
  type        = string
  default     = "latest"
}

variable "ecs_desired_count" {
  description = "ECS サービスのタスク数"
  type        = number
  default     = 2
}

# ---------------------------------------------------------------
# RDS
# ---------------------------------------------------------------

variable "db_engine_version" {
  description = "RDS for PostgreSQL のエンジンバージョン"
  type        = string
  default     = "17"
}

variable "db_instance_class" {
  description = "RDS のインスタンスクラス"
  type        = string
  default     = "db.t4g.medium"
}

variable "db_deletion_protection" {
  description = "RDS の削除保護"
  type        = bool
  default     = true
}

variable "db_skip_final_snapshot" {
  description = "RDS 削除時に最終スナップショットを作成しない場合は true（検証環境向け）"
  type        = bool
  default     = false
}
