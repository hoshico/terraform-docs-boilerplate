output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.this.id
}

output "subnet_ids" {
  description = "サブネット ID（種別・AZ ごと）"
  value = {
    firewall = { for k, s in aws_subnet.firewall : k => s.id }
    public   = { for k, s in aws_subnet.public : k => s.id }
    private  = { for k, s in aws_subnet.private : k => s.id }
  }
}

output "firewall_endpoint_ids" {
  description = "Network Firewall endpoint ID（AZ ごと）"
  value       = local.firewall_endpoint_ids
}

output "alb_dns_name" {
  description = "ALB の DNS 名"
  value       = aws_lb.this.dns_name
}

output "web_ap_instance_ids" {
  description = "Web/AP（EC2）のインスタンス ID（AZ ごと）"
  value       = { for k, i in aws_instance.web_ap : k => i.id }
}

output "ecr_repository_url" {
  description = "アプリケーションイメージの ECR リポジトリ URL"
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  description = "ECS クラスター名"
  value       = aws_ecs_cluster.this.name
}

output "rds_endpoint" {
  description = "RDS のエンドポイント"
  value       = aws_db_instance.this.endpoint
}

output "rds_master_user_secret_arn" {
  description = "RDS マスターユーザーのシークレット ARN（Secrets Manager）"
  value       = try(aws_db_instance.this.master_user_secret[0].secret_arn, null)
}

output "efs_id" {
  description = "EFS のファイルシステム ID"
  value       = aws_efs_file_system.this.id
}

output "s3_bucket_name" {
  description = "S3 バケット名"
  value       = aws_s3_bucket.app.bucket
}
