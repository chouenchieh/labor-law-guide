# 労働法コンプライアンスガイド生成スキル

日本企業の海外進出向け、国別労働法コンプライアンスガイド自動生成ツール。国名を入力するだけで、完全な Word コンプライアンスガイドがデスクトップに出力されます。

## 仕組み

CDP（Chrome DevTools Protocol）Proxy を通じてブラウザ上の Google NotebookLM を操作：
Discover で対象国の労働法ソースを検索 → 章ごとに質問を送信して回答を抽出 → 構造化された Word 文書を生成。

```
国名入力 → NotebookLM Discover ソース検索 → 18 件の Q&A 抽出 → Word ガイド生成
```

## 環境要件

| 依存 | バージョン | 説明 |
|------|-----------|------|
| Node.js | 22+ | ネイティブ WebSocket サポート |
| Python | 3.9+ | 文書生成スクリプト |
| Chrome | 任意 | リモートデバッグ有効で起動が必要 |
| Google アカウント | - | NotebookLM にログイン |

### 1. Python 依存パッケージのインストール

```bash
pip install python-docx pyyaml
```

### 2. DeepSeek API キーの設定（任意）

章の要約生成に使用。設定しなくてもメインガイドは生成可能（要約は「保留中」と表示）。

```bash
export DEEPSEEK_API_KEY="sk-xxxxxxxx"
```

### 3. Chrome をリモートデバッグモードで起動

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 &
```

**Linux:**
```bash
google-chrome --remote-debugging-port=9222 &
```

**Windows:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

> Chrome 148+ ではデフォルト以外のプロファイルディレクトリが必要です。問題が発生した場合、一時プロファイルを作成：
> ```bash
> cp -al "$HOME/Library/Application Support/Google/Chrome" /tmp/chrome-profile-link
> /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile-link &
> ```

### 4. CDP Proxy の起動

```bash
node scripts/cdp-proxy.mjs
```

このターミナルを起動したままにしてください。Proxy は `http://localhost:3456` で待ち受けます。

### 5. 環境チェック

```bash
node scripts/check-deps.mjs
```

以下の出力が確認できれば準備完了：
```
node: ok (v22.x)
chrome: ok (port 9222)
proxy: ready
```

### 6. NotebookLM にログイン

Chrome で https://notebooklm.google.com/ にアクセスし、Google アカウントでログイン。

### 7. 初回セットアップ（事務所・担当者情報）

```bash
python3 scripts/setup.py
```

事務所名、担当者などの情報を入力すると `config.yaml` が生成されます。以降、生成するすべてのガイドにこれらの情報が埋め込まれます。

## 使い方

このスキルを Claude Code にロードし、国名を入力：

```
/labor-law-guide ベトナム
```

全体的な流れ（詳細は [SKILL.md](SKILL.md) を参照）：

| ステップ | 誰が | 内容 |
|---------|------|------|
| 1 | あなた | Claude が生成したシステムプロンプトを NotebookLM に貼り付け |
| 2 | あなた | Claude が生成した 16 の検索キーワードで Discover 検索しソースをインポート |
| 3 | Claude | CDP 経由で NotebookLM に 18 の質問を送信し回答を抽出 |
| 4 | Claude | DeepSeek で章の要約を生成 + 法令体系表を作成 |
| 5 | Claude | Word 文書をデスクトップに生成 |
| 6 | Claude | 法令原文 PDF をダウンロードしフォルダ構成を整理 |

## 出力構成

```
~/Desktop/<国名>労働コンプライアンスガイド/
├── <国名>労働コンプライアンスガイド（2026版）初稿.docx   # メインガイド
├── 法令原文PDF/                                          # ダウンロードした法令原文
└── 法律文本模板/                                         # ダウンロードしたテンプレート原文
    └── 原文/
```

## ファイル構成

```
labor-law-guide/
├── SKILL.md                        # スキル定義（Claude が実行する完全なワークフロー）
├── README.md                       # 中国語 README（中国企業の海外進出向け）
├── README.en.md                    # 英語 README
├── README.ja.md                    # 日本語 README（日本企業の海外進出向け）
├── scripts/
│   ├── cdp-proxy.mjs              # CDP Proxy サーバー（Node.js）
│   ├── check-deps.mjs             # 環境チェックスクリプト
│   ├── setup.py                   # 初回セットアップ（事務所・担当者情報）
│   ├── build_word.py              # メインガイド Word 文書生成
│   ├── build_law_reference.py     # 法令对照表 Word 生成
│   └── gen_summaries.py           # DeepSeek 章要約生成
└── references/
    ├── chapter-questions.yaml     # 18 の質問キーワード
    ├── chapter-structure.yaml     # 6 部 15 章の固定構造
    ├── search-prompts.yaml        # 16 の Discover 検索分野
    ├── config-template.yaml       # 国別設定テンプレート
    └── doc-format-spec.md         # Word 文書フォーマット仕様
```

## 注意事項

- 法的内容はすべて NotebookLM がインポートされたソースに基づいて生成したものであり、正式な法的意見を構成するものではありません
- NotebookLM は最大 300 ソースまでサポート。16 分野で約 100〜150 ソース、上限内に収まります
- 具体的な法的問題については、対象国の資格を持つ専門弁護士に相談することをお勧めします
