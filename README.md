# 売上CSV DX化システム

月次売上ExcelをCSV処理でDX化するシステム

## 🚀 プロジェクト概要

このプロジェクトは、月次売上ExcelをCSV処理でDX化するシステムです。チーム別に異なるデータフォーマットと計算ルールをYAML設定ファイルで管理し、CSV処理による柔軟な売上データ処理を実現します。

### 主な機能

- **チーム別設定管理**: YAML設定ファイルでチーム固有のデータフォーマット・計算ルールを管理
- **四則演算対応計算エンジン**: 括弧付き四則演算、集約関数（SUM、MEAN等）をサポート
- **CSV型変換・検証**: pandasベースの柔軟な型変換とデータ検証
- **Streamlit UI**: 直感的なWeb UIで設定確認・データ処理を実行

## 🧪 テスト & カバレッジ

このプロジェクトでは高品質なコードを保つために、包括的なテストスイートとカバレッジ測定を実装しています。

### カバレッジ目標
- **目標カバレッジ率**: 80%以上

### テスト実行コマンド

```bash
# 基本的なテスト実行
make test

# カバレッジ付きテスト実行
make test-cov

# HTMLカバレッジレポート生成＆表示
make test-cov-html
```

### カバレッジレポート

カバレッジレポートは以下の形式で生成されます：

1. **ターミナル出力**: テスト実行時にコンソールに表示
2. **HTMLレポート**: `htmlcov/index.html` - ブラウザで詳細確認可能
3. **XMLレポート**: `coverage.xml` - CI/CD統合用

### カバレッジ設定

- **対象**: `src/` ディレクトリ内のコード
- **除外**: 
  - `src/presentation/app.py` (Streamlitアプリケーション)
  - テストファイル
  - キャッシュファイル

## ⚙️ 設定ファイル構造

```
config/
├── app.yaml              # アプリケーション全体設定
└── teams/
    ├── team_a.yaml       # 営業チームA設定
    └── team_b.yaml       # 営業チームB設定
```

### チーム設定ファイル例

```yaml
# チーム基本情報
team:
  id: "team_a"
  name: "営業チームA"
  description: "東京エリア担当の営業チーム"

# データフォーマット設定
data_format:
  columns:
    - name: "date"
      type: "datetime"
      format: "%Y-%m-%d"
      required: true
    - name: "quantity"
      type: "int"
      required: true
    - name: "unit_price"
      type: "float"
      required: true

# 計算ルール設定
calculation_rules:
  - name: "gross_revenue"
    formula: "quantity * unit_price"
    description: "粗売上 = 数量 × 単価"
  - name: "monthly_total"
    formula: "SUM(net_revenue)"
    group_by: ["date::month", "sales_rep"]
```

## 🛠 開発環境セットアップ

### セットアップ手順

```bash
# Devbox環境に入る
devbox shell

# 依存関係のインストール（PyYAML含む）
make install

# テスト実行でセットアップ確認
make test-cov

# アプリケーション実行
uv run streamlit run src/presentation/app.py
```

## 📊 その他の開発コマンド

```bash
# コード品質チェック
make lint

# コードフォーマット
make format

# 生成ファイルのクリーンアップ
make clean

# 全コマンドのヘルプ表示
make help
```

## 🚀 使用方法

```bash
# アプリケーションの起動
uv run streamlit run src/presentation/app.py
```

ブラウザで `http://localhost:8501` にアクセス後：

1. **チーム選択**: サイドバーから処理したいチームを選択
2. **データフォーマット確認**: CSV列定義と型情報を確認
3. **計算ルール確認**: 適用される計算式を確認
4. **CSV処理**: （将来実装）CSVファイルをアップロードして処理実行

## 🔧 技術仕様

- **設定管理**: YAML形式でチーム別設定を管理
- **計算エンジン**: ASTベースの安全な四則演算パーサー
- **データ処理**: pandasによる型変換・検証・集計
- **UI**: Streamlitによる直感的なWebインターフェース
- **将来拡張**: 認証認可、外部ストレージ（S3/DB）対応予定
