# 開発環境のバージョン管理方針

Mac / Windows / CI（GitHub Actions）でツールのバージョン差異を出さないための方針。

> ステータス：方針のみ決定。各設定ファイルは未作成。

## 前提

- Docker（Dev Container 含む）は使用しない
- Node.js を前提としたツールは使用しない（[AGENTS.md](../AGENTS.md) 参照）

## 全体像

| 対象 | 固定方法 | コミットするファイル |
|---|---|---|
| Terraform / Python / uv | mise | `mise.toml` |
| Python ライブラリ | uv | `pyproject.toml`, `uv.lock` |
| Terraform プロバイダ | lock ファイル | `.terraform.lock.hcl` |
| 改行コード | Git | `.gitattributes` |
| draw.io | CI で固定 / ローカルは推奨バージョンを記載 | なし |

## 1. CLI ツール：mise

[mise](https://mise.jdx.dev/) でツールのバージョンをリポジトリ単位で固定する。Windows / Mac / Linux 対応。

```toml
# mise.toml
[tools]
terraform = "1.16.4"
python = "3.12"
uv = "<固定するバージョン>"
```

インストール：

```sh
# Windows
winget install jdx.mise
# Mac
brew install mise

# リポジトリ直下で
mise install
```

CI では `jdx/mise-action` を使い、同じ `mise.toml` を読み込む。

## 2. Python ライブラリ：uv

[uv](https://docs.astral.sh/uv/) で依存を管理し、`uv.lock` で間接依存まで固定する。

```toml
# pyproject.toml
[project]
name = "terraform-docs-boilerplate"
requires-python = ">=3.12"
dependencies = ["pyyaml", "yamllint", "check-jsonschema"]
```

```sh
uv sync                                   # 依存のインストール
uv run python scripts/generate_csv.py     # スクリプト実行
uv run yamllint requirements/
```

- `uv run` を使うことで、OS ごとの venv 有効化方法（`activate` / `Activate.ps1`）の違いを吸収する
- Python スクリプトは標準ライブラリ優先。外部依存は PyYAML 程度に留める

## 3. Terraform

- `versions.tf` で本体バージョンを制約する

  ```hcl
  terraform {
    required_version = "~> 1.16.0"
  }
  ```

- `.terraform.lock.hcl` をコミットする。生成時は全 OS 分のハッシュを記録する（Windows で `init` した際の差分を防ぐ）

  ```sh
  terraform providers lock \
    -platform=windows_amd64 \
    -platform=darwin_arm64 \
    -platform=linux_amd64
  ```

## 4. Windows 対策

- `.gitattributes` で改行を LF に統一する（CRLF だと yamllint が失敗する）

  ```gitattributes
  * text=auto eol=lf
  ```

- 自動化スクリプトは shell ではなく Python で書く
- パス操作は `pathlib` を使う
- ファイル出力時は `encoding="utf-8"`, `newline="\n"` を明示し、OS による生成物の差分を防ぐ

## 5. draw.io

draw.io は mise / uv で管理できず、バージョンにより SVG 出力が変わる可能性がある。

- SVG の生成と差分チェックは CI（固定バージョン）でのみ行う
- ローカルでの SVG 生成は確認用とする
- ローカルでもバージョンを揃える場合は、推奨バージョンを指定してインストールする

  ```sh
  # Windows
  winget install JGraph.Draw --version <推奨バージョン>
  # Mac
  brew install --cask drawio
  ```
