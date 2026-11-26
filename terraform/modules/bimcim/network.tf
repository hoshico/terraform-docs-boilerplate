# specifications/communication.yaml の network と同じ値にする
locals {
  vpc_cidr = "10.20.0.0/18"

  azs = {
    "1a" = "${var.region}a"
    "1c" = "${var.region}c"
  }

  subnet_cidrs = {
    firewall = { "1a" = "10.20.11.0/24", "1c" = "10.20.12.0/24" }
    public   = { "1a" = "10.20.1.0/24", "1c" = "10.20.2.0/24" }
    private  = { "1a" = "10.20.8.0/24", "1c" = "10.20.9.0/24" }
  }
}

resource "aws_vpc" "this" {
  cidr_block           = local.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.name_prefix}-vpc"
  }
}

# ---------------------------------------------------------------
# Subnets
# ---------------------------------------------------------------

resource "aws_subnet" "firewall" {
  for_each = local.subnet_cidrs.firewall

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = local.azs[each.key]

  tags = {
    Name = "${var.name_prefix}-subnet-fw-${each.key}"
  }
}

resource "aws_subnet" "public" {
  for_each = local.subnet_cidrs.public

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = local.azs[each.key]

  tags = {
    Name = "${var.name_prefix}-subnet-pb-${each.key}"
  }
}

resource "aws_subnet" "private" {
  for_each = local.subnet_cidrs.private

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = local.azs[each.key]

  tags = {
    Name = "${var.name_prefix}-subnet-pr-${each.key}"
  }
}

# ---------------------------------------------------------------
# Internet Gateway / NAT Gateway
# ---------------------------------------------------------------

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-igw"
  }
}

resource "aws_eip" "nat" {
  for_each = aws_subnet.public

  domain = "vpc"

  tags = {
    Name = "${var.name_prefix}-eip-nat-${each.key}"
  }
}

resource "aws_nat_gateway" "this" {
  for_each = aws_subnet.public

  subnet_id     = each.value.id
  allocation_id = aws_eip.nat[each.key].id

  tags = {
    Name = "${var.name_prefix}-nat-${each.key}"
  }

  depends_on = [aws_internet_gateway.this]
}

# ---------------------------------------------------------------
# Route tables
#
# インターネットとの通信は、行き・帰りとも同じ AZ の Network Firewall endpoint を経由させる。
#   IGW -> (IGW edge RT) -> Firewall endpoint -> Public subnet (ALB / NAT)
#   Public subnet -> Firewall endpoint -> (Firewall RT) -> IGW
#   Private subnet -> NAT Gateway（S3 宛ては S3 Gateway Endpoint）
# ---------------------------------------------------------------

# IGW に関連付けるエッジルートテーブル（戻りの通信を Firewall endpoint へ向ける）
resource "aws_route_table" "igw_edge" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-rt-igw-edge"
  }
}

resource "aws_route" "igw_edge_to_firewall" {
  for_each = aws_subnet.public

  route_table_id         = aws_route_table.igw_edge.id
  destination_cidr_block = each.value.cidr_block
  vpc_endpoint_id        = local.firewall_endpoint_ids[each.key]
}

resource "aws_route_table_association" "igw_edge" {
  gateway_id     = aws_internet_gateway.this.id
  route_table_id = aws_route_table.igw_edge.id
}

# Firewall subnet：インターネット宛ては IGW へ
resource "aws_route_table" "firewall" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-rt-fw"
  }
}

resource "aws_route" "firewall_to_igw" {
  route_table_id         = aws_route_table.firewall.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "firewall" {
  for_each = aws_subnet.firewall

  subnet_id      = each.value.id
  route_table_id = aws_route_table.firewall.id
}

# Public subnet：インターネット宛ては同じ AZ の Firewall endpoint へ
resource "aws_route_table" "public" {
  for_each = aws_subnet.public

  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-rt-pb-${each.key}"
  }
}

resource "aws_route" "public_to_firewall" {
  for_each = aws_subnet.public

  route_table_id         = aws_route_table.public[each.key].id
  destination_cidr_block = "0.0.0.0/0"
  vpc_endpoint_id        = local.firewall_endpoint_ids[each.key]
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public[each.key].id
}

# Private subnet：インターネット宛ては同じ AZ の NAT Gateway へ
resource "aws_route_table" "private" {
  for_each = aws_subnet.private

  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-rt-pr-${each.key}"
  }
}

resource "aws_route" "private_to_nat" {
  for_each = aws_subnet.private

  route_table_id         = aws_route_table.private[each.key].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this[each.key].id
}

resource "aws_route_table_association" "private" {
  for_each = aws_subnet.private

  subnet_id      = each.value.id
  route_table_id = aws_route_table.private[each.key].id
}

# ---------------------------------------------------------------
# S3 Gateway Endpoint
# ---------------------------------------------------------------

resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [for rt in aws_route_table.private : rt.id]

  tags = {
    Name = "${var.name_prefix}-vpce-s3"
  }
}
