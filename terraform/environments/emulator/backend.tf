# エミュレーターは状態をメモリに保持するため、tfstate もローカルに置く。
# エミュレーターを再起動したら、このディレクトリの terraform.tfstate も削除すること。
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
