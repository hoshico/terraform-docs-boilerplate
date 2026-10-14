# terraform-docs-boilerplate

AWS の通信要件を YAML で管理し、Terraform と設計ドキュメント（CSV・draw.io・SVG）を同一リポジトリで生成・管理するためのボイラープレート。

## ディレクトリ構成

```
terraform-docs-boilerplate
├── requirements/   # 通信要件 YAML（正本）と JSON Schema
├── terraform/      # Terraform コード
├── scripts/        # 検証・生成用 Python スクリプト
├── docs/           # 設計書・運用手順書
│   ├── diagrams/   # 構成図（自動生成）
│   └── tables/     # 通信要件一覧 CSV（自動生成）
└── .github/        # GitHub Actions・PR テンプレート
```

詳細な方針は [AGENTS.md](AGENTS.md)、開発環境は [docs/development-environment.md](docs/development-environment.md) を参照。
