# ---------------------------------------------------------------
# Network Firewall
#
# 現状はステートレスで全通信をステートフルエンジンへ渡し、ステートフルルールは未設定（すべて通過）。
# 許可ドメインの制限などは、要件に応じてルールグループを追加する。
# ---------------------------------------------------------------

resource "aws_networkfirewall_firewall_policy" "this" {
  name = "${var.name_prefix}-fw-policy"

  firewall_policy {
    stateless_default_actions          = ["aws:forward_to_sfe"]
    stateless_fragment_default_actions = ["aws:forward_to_sfe"]
  }
}

resource "aws_networkfirewall_firewall" "this" {
  name                = "${var.name_prefix}-fw"
  firewall_policy_arn = aws_networkfirewall_firewall_policy.this.arn
  vpc_id              = aws_vpc.this.id

  dynamic "subnet_mapping" {
    for_each = aws_subnet.firewall

    content {
      subnet_id = subnet_mapping.value.id
    }
  }
}

locals {
  # AZ キー（"1a" / "1c"）ごとの Firewall endpoint ID
  firewall_endpoint_ids = {
    for key, az in local.azs : key => one([
      for state in aws_networkfirewall_firewall.this.firewall_status[0].sync_states :
      state.attachment[0].endpoint_id if state.availability_zone == az
    ])
  }
}
