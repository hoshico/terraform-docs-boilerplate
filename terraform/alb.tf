# ---------------------------------------------------------------
# Application Load Balancer
#   HTTPS 443 -> 既定は Web/AP（EC2:80）、var.ecs_path_patterns は ECS（Fargate:3000）
# ---------------------------------------------------------------

resource "aws_lb" "this" {
  name                       = "${var.name_prefix}-alb"
  load_balancer_type         = "application"
  internal                   = false
  security_groups            = [aws_security_group.alb.id]
  subnets                    = [for s in aws_subnet.public : s.id]
  drop_invalid_header_fields = true
}

resource "aws_lb_target_group" "web_ap" {
  name        = "${var.name_prefix}-web-ap"
  port        = 80
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = aws_vpc.this.id

  health_check {
    path    = "/"
    matcher = "200-399"
  }
}

resource "aws_lb_target_group_attachment" "web_ap" {
  for_each = aws_instance.web_ap

  target_group_arn = aws_lb_target_group.web_ap.arn
  target_id        = each.value.id
  port             = 80
}

resource "aws_lb_target_group" "ecs" {
  name        = "${var.name_prefix}-ecs"
  port        = 3000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.this.id

  health_check {
    path    = "/"
    matcher = "200-399"
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = local.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web_ap.arn
  }
}

resource "aws_lb_listener_rule" "ecs" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  condition {
    path_pattern {
      values = var.ecs_path_patterns
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs.arn
  }
}

# ---------------------------------------------------------------
# 証明書
# certificate_arn を指定しない場合は、検証用に自己署名証明書を ACM にインポートする。
# 秘密鍵が tfstate に保存されるため、本番では certificate_arn を指定すること。
# ---------------------------------------------------------------

resource "tls_private_key" "self_signed" {
  count = var.certificate_arn == null ? 1 : 0

  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "tls_self_signed_cert" "self_signed" {
  count = var.certificate_arn == null ? 1 : 0

  private_key_pem       = tls_private_key.self_signed[0].private_key_pem
  validity_period_hours = 24 * 365

  subject {
    common_name = "${var.name_prefix}.example.com"
  }

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]
}

resource "aws_acm_certificate" "self_signed" {
  count = var.certificate_arn == null ? 1 : 0

  private_key      = tls_private_key.self_signed[0].private_key_pem
  certificate_body = tls_self_signed_cert.self_signed[0].cert_pem
}

locals {
  certificate_arn = var.certificate_arn != null ? var.certificate_arn : aws_acm_certificate.self_signed[0].arn
}
