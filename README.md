# DX Without Excel

ExcelのないDXソリューション - チーム管理システム

## 🚀 プロジェクト概要

このプロジェクトは、Excelに依存せずにチーム管理を行うためのWebアプリケーションです。StreamlitとPythonを使用して構築されています。

## 📁 プロジェクト構造

```
dx-without-excel/
├── src/
│   ├── domain/          # ドメインロジック
│   │   └── team.py      # チームエンティティ
│   └── presentation/    # プレゼンテーション層
│       ├── app.py       # Streamlitアプリケーション
│       └── team_manager.py  # チーム管理サービス
├── tests/
│   └── unit/           # ユニットテスト
│       ├── domain/
│       └── presentation/
├── pyproject.toml      # プロジェクト設定
└── Makefile           # 開発用コマンド
```

## 🧪 テスト & カバレッジ

このプロジェクトでは高品質なコードを保つために、包括的なテストスイートとカバレッジ測定を実装しています。

### カバレッジ目標
- **目標カバレッジ率**: 95%以上
- **現在のカバレッジ**: 100% ✅

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

## 🛠 開発環境セットアップ

### セットアップ手順

```bash
# 依存関係のインストール
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

## 🚀 本番運用

```bash
# アプリケーションの起動
uv run streamlit run src/presentation/app.py
```

ブラウザで `http://localhost:8501` にアクセスしてアプリケーションを利用できます。
