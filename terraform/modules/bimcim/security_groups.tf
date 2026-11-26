# ---------------------------------------------------------------
# Security Groups
#
# AGENTS.md 9章の記述ルールに従う。
# - specifications/communication.yaml のリソース 1 つにつき Security Group を 1 つ作る
# - YAML の通信に対応するルールには CommunicationId タグを付ける
# - 1 つの通信は、宛先側の ingress と送信元側の egress の 2 ルールに対応する
# ---------------------------------------------------------------

resource "aws_security_group" "alb" {
  name        = "${var.name_prefix}-sg-alb"
  description = "Application Load Balancer"
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-sg-alb"
  }
}

resource "aws_security_group" "web_ap" {
  name        = "${var.name_prefix}-sg-web-ap"
  description = "Web/AP (EC2)"
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-sg-web-ap"
  }
}

resource "aws_security_group" "ecs" {
  name        = "${var.name_prefix}-sg-ecs"
  description = "ECS Service (Fargate)"
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-sg-ecs"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.name_prefix}-sg-rds"
  description = "RDS for PostgreSQL"
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-sg-rds"
  }
}

resource "aws_security_group" "efs" {
  name        = "${var.name_prefix}-sg-efs"
  description = "Amazon EFS"
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-sg-efs"
  }
}

# ---------------------------------------------------------------
# users-to-alb（TCP 443）
# ---------------------------------------------------------------

resource "aws_vpc_security_group_ingress_rule" "alb_from_users" {
  for_each = toset(var.alb_ingress_cidrs)

  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443

  tags = {
    CommunicationId = "users-to-alb"
  }
}

# ---------------------------------------------------------------
# alb-to-web-ap（TCP 80）
# ---------------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "alb_to_web_ap" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.web_ap.id
  ip_protocol                  = "tcp"
  from_port                    = 80
  to_port                      = 80

  tags = {
    CommunicationId = "alb-to-web-ap"
  }
}

resource "aws_vpc_security_group_ingress_rule" "web_ap_from_alb" {
  security_group_id            = aws_security_group.web_ap.id
  referenced_security_group_id = aws_security_group.alb.id
  ip_protocol                  = "tcp"
  from_port                    = 80
  to_port                      = 80

  tags = {
    CommunicationId = "alb-to-web-ap"
  }
}

# ---------------------------------------------------------------
# alb-to-ecs（TCP 3000）
# ---------------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "alb_to_ecs" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.ecs.id
  ip_protocol                  = "tcp"
  from_port                    = 3000
  to_port                      = 3000

  tags = {
    CommunicationId = "alb-to-ecs"
  }
}

resource "aws_vpc_security_group_ingress_rule" "ecs_from_alb" {
  security_group_id            = aws_security_group.ecs.id
  referenced_security_group_id = aws_security_group.alb.id
  ip_protocol                  = "tcp"
  from_port                    = 3000
  to_port                      = 3000

  tags = {
    CommunicationId = "alb-to-ecs"
  }
}

# ---------------------------------------------------------------
# web-ap-to-rds / ecs-to-rds（TCP 5432）
# ---------------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "web_ap_to_rds" {
  security_group_id            = aws_security_group.web_ap.id
  referenced_security_group_id = aws_security_group.rds.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432

  tags = {
    CommunicationId = "web-ap-to-rds"
  }
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_web_ap" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.web_ap.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432

  tags = {
    CommunicationId = "web-ap-to-rds"
  }
}

resource "aws_vpc_security_group_egress_rule" "ecs_to_rds" {
  security_group_id            = aws_security_group.ecs.id
  referenced_security_group_id = aws_security_group.rds.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432

  tags = {
    CommunicationId = "ecs-to-rds"
  }
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_ecs" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.ecs.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432

  tags = {
    CommunicationId = "ecs-to-rds"
  }
}

# ---------------------------------------------------------------
# web-ap-to-efs / ecs-to-efs（TCP 2049）
# ---------------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "web_ap_to_efs" {
  security_group_id            = aws_security_group.web_ap.id
  referenced_security_group_id = aws_security_group.efs.id
  ip_protocol                  = "tcp"
  from_port                    = 2049
  to_port                      = 2049

  tags = {
    CommunicationId = "web-ap-to-efs"
  }
}

resource "aws_vpc_security_group_ingress_rule" "efs_from_web_ap" {
  security_group_id            = aws_security_group.efs.id
  referenced_security_group_id = aws_security_group.web_ap.id
  ip_protocol                  = "tcp"
  from_port                    = 2049
  to_port                      = 2049

  tags = {
    CommunicationId = "web-ap-to-efs"
  }
}

resource "aws_vpc_security_group_egress_rule" "ecs_to_efs" {
  security_group_id            = aws_security_group.ecs.id
  referenced_security_group_id = aws_security_group.efs.id
  ip_protocol                  = "tcp"
  from_port                    = 2049
  to_port                      = 2049

  tags = {
    CommunicationId = "ecs-to-efs"
  }
}

resource "aws_vpc_security_group_ingress_rule" "efs_from_ecs" {
  security_group_id            = aws_security_group.efs.id
  referenced_security_group_id = aws_security_group.ecs.id
  ip_protocol                  = "tcp"
  from_port                    = 2049
  to_port                      = 2049

  tags = {
    CommunicationId = "ecs-to-efs"
  }
}

# ---------------------------------------------------------------
# web-ap-to-internet / ecs-to-internet（TCP 443、NAT Gateway 経由）
# 宛先が Security Group を持たないため egress のみ
# ---------------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "web_ap_to_internet" {
  security_group_id = aws_security_group.web_ap.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443

  tags = {
    CommunicationId = "web-ap-to-internet"
  }
}

resource "aws_vpc_security_group_egress_rule" "ecs_to_internet" {
  security_group_id = aws_security_group.ecs.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443

  tags = {
    CommunicationId = "ecs-to-internet"
  }
}

# ---------------------------------------------------------------
# web-ap-to-s3 / ecs-to-s3（TCP 443、S3 Gateway Endpoint 経由）
# 宛先は S3 のマネージドプレフィックスリスト
# ---------------------------------------------------------------

resource "aws_vpc_security_group_egress_rule" "web_ap_to_s3" {
  security_group_id = aws_security_group.web_ap.id
  prefix_list_id    = aws_vpc_endpoint.s3.prefix_list_id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443

  tags = {
    CommunicationId = "web-ap-to-s3"
  }
}

resource "aws_vpc_security_group_egress_rule" "ecs_to_s3" {
  security_group_id = aws_security_group.ecs.id
  prefix_list_id    = aws_vpc_endpoint.s3.prefix_list_id
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443

  tags = {
    CommunicationId = "ecs-to-s3"
  }
}
