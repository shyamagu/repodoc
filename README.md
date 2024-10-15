# Repodoc

## Repodoc概要

ソースコードリポジトリを分析し、リポジトリに関する総合レポートを作成するツールです。
分析結果に対して問い合わせをすることで、GitHub Copilot Chatと同様のチャット機能も実現しています。が、チャット機能は保守性や品質の観点から GitHub Copilot Chat の利用を推奨します。


## 必要条件

このプロジェクトを実行するためには、以下のパッケージが必要です。

- Python 3.11+
- pip（Pythonパッケージマネージャー）

## インストール方法

1. このリポジトリをクローンします。
    ```bash
    git clone <このリポジトリのURL>
    ```

2. 仮想環境を作成します（推奨）。
    ```bash
    python -m venv venv
    ```

3. 仮想環境をアクティベートします（2.の手順を実行した場合）。
   - Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. 必要なPythonパッケージをインストールします。
    ```bash
    pip install -r requirements.txt
    ```

## 環境設定

1. `.env` ファイルを作成し、以下の変数を設定します。
    ```plaintext
    AZURE_OPENAI_ENDPOINT=<YOUR_AZURE_OPENAI_ENDPOINT>
    AZURE_OPENAI_API_KEY=<YOUR_AZURE_OPENAI_API_KEY>
    MODEL_DEPLOYMENT_NAME=<YOUR_MODEL_DEPLOYMENT_NAME>
    ```

## 使用方法

### リポジトリの分析

1. `analyze_repo.py` スクリプトを実行して、指定されたフォルダを分析します。
    ```bash
    python analyze_repo.py
    ```

2. プロンプトに従いフォルダパスを入力し、分析を開始します。

### チャットボットとの対話

1. `chat.py` スクリプトを実行して、チャット機能を開始します。
    ```bash
    python chat.py
    ```

2. プロンプトに従い、リポジトリに関する質問を入力してください。

### レポートの生成

1. `report.py` スクリプトを実行して、`stats_final.json` に基づくリポジトリ解析レポートのHTMLファイルを生成します。
    ```bash
    python report.py
    ```

2. `report.html` ファイルが生成され、ブラウザで開くことで解析されたレポートを閲覧できます。

### `.repodocignore`ファイルの使用方法

`.repodocignore` ファイルは、解析時に無視するファイルやフォルダを指定できます。

#### 例
```
# バイナリファイルを無視
*.bin

# buildフォルダを無視
/build/

# 一時ファイルを無視
*.tmp
```
このファイルをリポジトリのルートに配置すると、`analyze_repo.py` 実行時に自動で読み込まれます。

## ファイル生成

- **統計データファイル**
  - `stats_intermediate.json`: 分析途中のデータが保存されます。

- **最終分析結果ファイル**
  - `stats_final.json`: 最終的な分析結果が保存されます。

- **レポートファイル**
  - `report.html`: `report.py` により生成された、解析結果を示すHTMLレポートです。

## サンプルプロジェクト
`samplep`フォルダにテスト用に試せるプロジェクトを用意しています。
コード規模が小さいため課金の観点でも容易に試せるようにしています。不要であれば削除してください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。