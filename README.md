# 劳动法合规指南生成技能

面向出海中国企业的国别劳动法律合规指南自动生成器。输入国家名，桌面输出完整的 Word 合规指南。

## 工作原理

通过 CDP (Chrome DevTools Protocol) Proxy 操控浏览器中的 Google NotebookLM：
Discover 搜索目标国劳动法来源 → 逐章提交问题提取答案 → 生成结构化 Word 文档。

```
输入国家名 → NotebookLM Discover 搜索来源 → 18 题问答提取 → 生成 Word 指南
```

## 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Node.js | 22+ | 原生 WebSocket 支持 |
| Python | 3.9+ | 文档生成脚本 |
| Chrome | 任意 | 需以远程调试模式启动 |
| Google 账号 | - | 登录 NotebookLM |

### 1. 安装 Python 依赖

```bash
pip install python-docx pyyaml
```

### 2. 设置 DeepSeek API Key（可选）

用于生成章节小结和法律对照表。不设置也能生成主指南（章节小结会显示为待生成）。

```bash
export DEEPSEEK_API_KEY="sk-xxxxxxxx"
```

### 3. 启动 Chrome 远程调试模式

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

> Chrome 148+ 需要使用非默认 profile 目录。如遇到问题，创建临时 profile：
> ```bash
> cp -al "$HOME/Library/Application Support/Google/Chrome" /tmp/chrome-profile-link
> /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile-link &
> ```

### 4. 启动 CDP Proxy

```bash
node scripts/cdp-proxy.mjs
```

保持该终端运行。Proxy 监听 `http://localhost:3456`。

### 5. 检查环境

```bash
node scripts/check-deps.mjs
```

看到以下输出即就绪：
```
node: ok (v22.x)
chrome: ok (port 9222)
proxy: ready
```

### 6. 登录 NotebookLM

在 Chrome 中访问 https://notebooklm.google.com/ 并登录你的 Google 账号。

### 7. 首次配置（律所和联系人信息）

```bash
python3 scripts/setup.py
```

按提示填写律所名称、联系人等信息，生成 `config.yaml`。之后每次生成指南都会嵌入这些信息。

## 使用方法

在 Claude Code 中加载此 skill 后，输入国家名即可：

```
/labor-law-guide 韩国
```

完整流程详见 [SKILL.md](SKILL.md)，功能与使用说明见 [USAGE.md](USAGE.md)。

**流程概览：**

| 步骤 | 谁做 | 做什么 |
|------|------|------|
| 1 | 你 | 把 Claude 生成的系统提示词粘贴到 NotebookLM |
| 2 | 你 | 把 Claude 生成的 16 个搜索关键词逐领域在 Discover 中搜索导入来源 |
| 3 | Claude | 通过 CDP 操控 NotebookLM 提交 18 个问题并提取答案 |
| 4 | Claude | DeepSeek 生成章节小结 + 建立法律体系表 |
| 5 | Claude | 生成 Word 文档输出到桌面 |
| 6 | Claude | 下载法律 PDF 原文，建立文件夹结构 |

## 输出结构

```
~/Desktop/<国家名>劳动合规指南/
├── <国家名>劳动合规指南（2026版）初稿.docx   # 主指南
├── 法律法规原文PDF/                           # 下载的法律原文
└── 法律文本模板/                              # 下载的模板原文
    └── 原文/
```

## 文件说明

```
labor-law-guide/
├── SKILL.md                        # 技能定义（Claude 执行的完整流程）
├── README.md                       # 中文说明（中国出海企业）
├── README.en.md                    # 英文说明
├── README.ja.md                    # 日文说明（日本出海企业）
├── scripts/
│   ├── cdp-proxy.mjs              # CDP Proxy 服务器（Node.js）
│   ├── check-deps.mjs             # 环境检查脚本
│   ├── setup.py                   # 首次配置（律所/联系人信息）
│   ├── build_word.py              # 主指南 Word 文档生成
│   ├── build_law_reference.py     # 法律对照表 Word 生成
│   └── gen_summaries.py           # DeepSeek 章节小结生成
└── references/
    ├── chapter-questions.yaml     # 18 个提问关键词
    ├── chapter-structure.yaml     # 6 部分 15 章固定结构
    ├── search-prompts.yaml        # 16 个 Discover 搜索领域
    ├── config-template.yaml       # 国家配置模板
    └── doc-format-spec.md         # Word 文档格式规范
```

## 注意

- 法律内容均来自 NotebookLM 基于导入来源的生成结果，不构成正式法律意见
- NotebookLM 最多支持 300 个来源，16 领域约需 100-150 个，在安全范围内
- 建议在具体法律问题上咨询具备目标国执业资质的专业律师
