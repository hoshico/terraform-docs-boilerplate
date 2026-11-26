output "vpc_id" {
  description = "VPC ID"
  value       = module.bimcim.vpc_id
}

output "subnet_ids" {
  description = "サブネット ID（種別・AZ ごと）"
  value       = module.bimcim.subnet_ids
}

output "firewall_endpoint_ids" {
  description = "Network Firewall endpoint ID（AZ ごと）"
  value       = module.bimcim.firewall_endpoint_ids
}

output "alb_dns_name" {
  description = "ALB の DNS 名"
  value       = module.bimcim.alb_dns_name
}

output "web_ap_instance_ids" {
  description = "Web/AP（EC2）のインスタンス ID（AZ ごと）"
  value       = module.bimcim.web_ap_instance_ids
}

output "ecr_repository_url" {
  description = "アプリケーションイメージの ECR リポジトリ URL"
  value       = module.bimcim.ecr_repository_url
}

output "ecs_cluster_name" {
  description = "ECS クラスター名"
  value       = module.bimcim.ecs_cluster_name
}

output "rds_endpoint" {
  description = "RDS のエンドポイント"
  value       = module.bimcim.rds_endpoint
}

output "efs_id" {
  description = "EFS のファイルシステム ID"
  value       = module.bimcim.efs_id
}

output "s3_bucket_name" {
  description = "S3 バケット名"
  value       = module.bimcim.s3_bucket_name
}
