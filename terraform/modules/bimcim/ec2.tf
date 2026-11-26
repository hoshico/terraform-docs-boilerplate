# ---------------------------------------------------------------
# Web/AP（EC2）：各 AZ の Private subnet に 1 台ずつ
# Systems Manager（Session Manager）で管理し、EFS を /mnt/efs にマウントする
# ---------------------------------------------------------------

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "web_ap" {
  name               = "${var.name_prefix}-web-ap"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

resource "aws_iam_role_policy_attachment" "web_ap_ssm" {
  role       = aws_iam_role.web_ap.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "web_ap" {
  name = "${var.name_prefix}-web-ap"
  role = aws_iam_role.web_ap.name
}

resource "aws_instance" "web_ap" {
  for_each = aws_subnet.private

  ami                    = data.aws_ami.al2023.id
  instance_type          = var.web_ap_instance_type
  subnet_id              = each.value.id
  vpc_security_group_ids = [aws_security_group.web_ap.id]
  iam_instance_profile   = aws_iam_instance_profile.web_ap.name

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = <<-EOT
    #!/bin/bash
    dnf install -y amazon-efs-utils
    mkdir -p /mnt/efs
    echo "${aws_efs_file_system.this.id}:/ /mnt/efs efs _netdev,tls 0 0" >> /etc/fstab
    mount -a
  EOT

  tags = {
    Name = "${var.name_prefix}-web-ap-${each.key}"
  }

  depends_on = [aws_efs_mount_target.this]
}
