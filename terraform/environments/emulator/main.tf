module "bimcim" {
  source = "../../modules/bimcim"

  region      = "ap-northeast-1"
  name_prefix = "bimcim-pro"

  # 検証用：削除しやすくする
  db_deletion_protection = false
  db_skip_final_snapshot = true
}
