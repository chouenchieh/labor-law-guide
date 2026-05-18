---
name: labor-law-guide
description: 从零生成国别劳动合规指南。通过 CDP Proxy 操控 NotebookLM——Discover 搜来源 → 逐章提问提取答案 → DeepSeek 生成小结 → 生成 Word。禁止使用 WebSearch/WebFetch，所有信息获取在 NotebookLM 浏览器内完成。
metadata:
  author: enChieh
  version: "3.2.0"
---

# Labor Law Guide Skill

面向出海中国企业的国别劳动法律合规指南生成器。输入国家名，输出桌面 Word 文件。

## 硬约束

**禁止使用 WebSearch、WebFetch 或任何站外搜索工具获取法律内容。** 所有法律信息通过 CDP Proxy 在 NotebookLM 内完成——Discover 搜索来源，聊天框提问获取答案。NotebookLM 是法律内容的唯一数据源。

**Discover 搜索必须用目标国语言。** 韩国用韩语、德国用德语、日本用日语。英语仅作目标国语言搜索结果不足时的补充。

**法律体系表（law.go.kr 链接）和 DeepSeek 生成小结是例外**——这两部分不是法律内容本身，是输出格式所需。

## 启动前检查

```bash
node scripts/check-deps.mjs
```

确保输出 `proxy: ready`。CDP Proxy 在 `http://localhost:3456`。

如果 Chrome 未以远程调试模式启动：

```bash
# 用硬链接创建非默认 user-data-dir（Chrome 148+ 要求）
cp -al "$HOME/Library/Application Support/Google/Chrome" /tmp/chrome-profile-link
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --user-data-dir=/tmp/chrome-profile-link &
```

## 完整流程（7 步）

### Step 1：创建 NotebookLM 笔记本并配置系统提示词

#### 1.1 打开 NotebookLM

```bash
curl -s "http://localhost:3456/new?url=https://notebooklm.google.com/"
# 返回 {"targetId": "ABC123..."}
```

将返回的 targetId 记为 `${TAB}`。

#### 1.2 确认已登录

```bash
curl -s -X POST "http://localhost:3456/eval?target=${TAB}" \
  -d 'document.body.textContent.includes("<YOUR_EMAIL>") ? "logged in" : "NOT LOGGED IN"'
```

如果未登录则手动登录后继续。

#### 1.3 创建新笔记本

截图确认当前页面，找到"新建"或"New"或"Create"按钮，用 `clickAt` 点击：

```bash
curl -s -X POST "http://localhost:3456/clickAt?target=${TAB}" \
  -d 'button:has-text("新建")'
```

等待 3 秒后确认进入笔记本（URL 包含 `notebooklm.google.com/notebook/`）：

```bash
curl -s "http://localhost:3456/info?target=${TAB}"
```

#### 1.4 设置笔记本系统提示词（核心步骤）

找到设置入口（齿轮图标或 Custom instructions）：

```bash
# 截图先找到设置按钮位置
curl -s -X POST "http://localhost:3456/screenshot?target=${TAB}" > /tmp/nlm_setup.png
```

分析截图找到设置入口后点击进入。然后在 "Custom instructions" 文本框中填入以下系统提示词（**根据目标国家替换 `<目标国中文名>`**）：

```
You are a senior attorney at a leading international law firm. Write a labor law compliance guide for Chinese enterprises investing in <目标国中文名>. 

Tone: Calm, factual, professional. No metaphors, no embellishment. State the law as it is.

Output length: Longer / comprehensive.

Structure: For each topic, break it down into specific knowledge points (知识点). For each knowledge point:
- First state the legal content (法律规定/实际情况)
- Then provide the corresponding compliance advice for Chinese companies (对出海中国企业的合规建议)

The reader is a Chinese business owner or HR manager trying to understand and comply with <目标国中文名> labor law. Be practical and specific in your advice.
```

**填充提示词的方法**（NotebookLM 是 Angular SPA）：

```bash
curl -s -X POST "http://localhost:3456/eval?target=${TAB}" \
  -d 'var ta=document.querySelector("textarea, [contenteditable=true]"); ta.focus(); document.execCommand("insertText",false,"<提示词内容>"); JSON.stringify({val:ta.value?.substring(0,50)})'
```

**不能**用 `input.value = xxx`——Angular zone.js 不会感知到变更。

确认输出长度选项设为 "Longer"，然后保存。

#### 1.5 记录工作目录

```bash
mkdir -p /tmp/nlm_doc/<country_slug>
curl -s "http://localhost:3456/info?target=${TAB}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps({'notebook_url': d['url']}))" > /tmp/nlm_doc/<country_slug>/notebook_info.json
```

### Step 2：Discover 添加来源（16 个领域）

#### 2.1 搜索语言规则

从 `references/search-prompts.yaml` 读取 16 个领域。每个领域的 `zh` 字段是中文参考，**翻译为目标国语言**后填入 Discover。

示例：
- 韩国 → 翻译成韩语
- 德国 → 翻译成德语
- 日本 → 翻译成日语

#### 2.2 逐领域搜索并添加来源

对每个领域重复以下步骤：

**a. 打开 Discover 面板**（首次）或搜索框

```bash
# 用截图确认位置后点击
curl -s -X POST "http://localhost:3456/clickAt?target=${TAB}" \
  -d 'button:has-text("Discover")'
```

**b. 用目标国语言填入搜索词**

```bash
curl -s -X POST "http://localhost:3456/eval?target=${TAB}" \
  -d 'var input=document.querySelector("input[type=text], textarea, [contenteditable=true]"); input.focus(); document.execCommand("insertText",false,"<目标国语言关键词>"); "filled"'
```

**c. 提交搜索**

```bash
# 优先用 clickAt 点击搜索按钮
curl -s -X POST "http://localhost:3456/clickAt?target=${TAB}" \
  -d 'button:has-text("Search")'
```

如果没有搜索按钮文本，用 Enter 键（Discover 不是 Angular，原生事件可用）：

```bash
curl -s -X POST "http://localhost:3456/eval?target=${TAB}" \
  -d 'var input=document.querySelector("input[type=text]"); input.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter",code:"Enter",bubbles:true})); "enter"'
```

**d. 等待结果加载**（5 秒后截图确认）

```bash
sleep 5
curl -s -X POST "http://localhost:3456/screenshot?target=${TAB}" > /tmp/nlm_discover_<area_index>.png
```

**e. 逐个添加结果——不做筛选**

Discover 返回什么就导什么。逐个点击"Add"或"添加"按钮导入所有可见结果，每次添加后等 3 秒。不筛选、不判断来源质量，全部导入。

**f. 等待处理完成**

```bash
curl -s -X POST "http://localhost:3456/eval?target=${TAB}" \
  -d 'JSON.stringify({pending:document.querySelectorAll("[class*=spinner],[class*=loading],[class*=progress]").length})'
```

`pending` 为 0 则继续下一个领域。

**g. 目标国语言结果不足时**，用英语关键词再搜一次，补充 3-5 个来源。

**h. 保存进度**

```bash
python3 -c "
import json
ck = {'current_area_index': <N>, 'total_areas': 16, 'areas_done': <LIST>}
with open('/tmp/nlm_doc/<country_slug>/checkpoint.json', 'w') as f:
    json.dump(ck, f, ensure_ascii=False, indent=2)
"
```

### Step 3：逐章提交问题并提取答案（18 个问题）

#### 3.1 关键机制

NotebookLM 是 Angular SPA，以下方法已经验证有效：

| 操作 | 正确方法 | 错误方法 |
|------|---------|---------|
| 填充文本框 | `execCommand('insertText', false, "...")` | `input.value = "..."` |
| 点击提交 | `clickAt` (CDP 真实鼠标事件) | `btn.click()` / `dispatchEvent(KeyboardEvent)` |
| 等待完成 | 轮询 `"正在思考"` 是否消失 | 匹配 "1. 内容与分析" |
| 提取答案 | `lastIndexOf(keywords)` → `indexOf("keep_pin")` | 全文搜索 |

#### 3.2 逐个提交问题

从 `references/chapter-questions.yaml` 读取 18 个问题的 `keywords`。

**每个问题的操作流程：**

**a. 填充输入框**

```bash
curl -s -X POST "http://localhost:3456/eval?target=${TAB}" \
  -d 'var ta=document.querySelector("textarea[placeholder*='\''提问'\''], textarea[placeholder*='\''创作'\'']"); ta.focus(); document.execCommand("insertText",false,"<KEYWORDS>"); JSON.stringify({val:ta.value})'
```

`insertText` 触发 Angular zone.js 的 input 事件，确保框架感知到文本变更。

**b. 点击提交按钮**

```bash
curl -s -X POST "http://localhost:3456/clickAt?target=${TAB}" \
  -d 'button[aria-label="提交"]'
```

**c. 轮询等待答案完成**

```bash
# 每 15-20 秒轮询，最多等 120 秒
curl -s -X POST "http://localhost:3456/eval?target=${TAB}" \
  -d 'document.body.textContent.includes("正在思考") ? "thinking" : "done"'
```

**d. 提取答案**

```bash
curl -s -X POST "http://localhost:3456/eval?target=${TAB}" \
  -d 'var all=document.body.textContent; var start=all.lastIndexOf("<KEYWORDS>"); var end=all.indexOf("keep_pin", start); all.substring(start, end>start?end:start+5000)'
```

用 `lastIndexOf` 定位最近一次提交的问题，用 `keep_pin` 标记答案结尾。

**e. 保存到 checkpoint**

```bash
python3 -c "
import json
with open('/tmp/nlm_doc/<country_slug>/checkpoint.json') as f:
    ck = json.load(f)
ck['answers']['<QUESTION_ID>'] = '''<ANSWER_TEXT>'''
ck['questions_completed'] += 1
with open('/tmp/nlm_doc/<country_slug>/checkpoint.json', 'w') as f:
    json.dump(ck, f, ensure_ascii=False, indent=2)
"
```

#### 3.3 导出 answers.json

```bash
python3 -c "
import json
with open('/tmp/nlm_doc/<country_slug>/checkpoint.json') as f:
    ck = json.load(f)
with open('/tmp/nlm_doc/<country_slug>/answers.json', 'w') as f:
    json.dump(ck['answers'], f, ensure_ascii=False, indent=2)
"
```

### Step 4：生成章节小结 + 法律体系表

#### 4.1 DeepSeek 生成章节小结

```bash
# 使用 gen_summaries.py 脚本（需要 DEEPSEEK_API_KEY 环境变量）
python3 ~/.claude/skills/labor-law-guide/scripts/gen_summaries.py \
    --answers /tmp/nlm_doc/<country_slug>/answers.json \
    --short "<short>" \
    --output /tmp/nlm_doc/<country_slug>/summaries.json
```

#### 4.2 创建法律体系表 config.yaml

搜索目标国主要劳动法律，收集：法律原名、law.go.kr（或等效官方链接）、中文简介。创建 config.yaml：

```yaml
legal_system:
  font: "<目标国字体系列>"  # e.g. "Malgun Gothic" for Korean
  laws:
    - ["法律原名 (中文译名)", "https://law.go.kr/...", "中文简介"]
    - ...
```

法律表应覆盖：
- 宪法中的劳动权条款
- 核心劳动基准法
- 工会与集体谈判法
- 工资与工时法
- 职业安全法
- 社会保险法（工伤、雇佣、年金、健康保险）
- 平等就业与反歧视法
- 非典型用工法（固定期限、派遣）
- 外国人雇佣法
- 劳动监察与争议解决法
- 其他目标国特有劳动法规

#### 4.3 验证法律链接（必须执行）

config.yaml 中的链接必须逐一打开验证，确保每个链接打开的页面确实是该法律。

```bash
# 创建新 tab 用于验证
VERIFY_TAB=$(curl -s "http://localhost:3456/new?url=about:blank" | python3 -c "import sys,json; print(json.load(sys.stdin)['targetId'])")

# 抽出所有法律链接
python3 -c "
import yaml
with open('/tmp/nlm_doc/<country_slug>/config.yaml') as f:
    config = yaml.safe_load(f)
laws = config['legal_system']['laws']
for i, law in enumerate(laws):
    print(f'{i}|{law[0][:60]}|{law[1]}')" > /tmp/nlm_doc/<country_slug>/laws_verify.txt

# 逐个打开验证
while IFS='|' read -r idx name url; do
  curl -s "http://localhost:3456/navigate?target=${VERIFY_TAB}&url=${url}" > /dev/null
  sleep 4
  TITLE=$(curl -s "http://localhost:3456/info?target=${VERIFY_TAB}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('title','FAIL'))")
  echo "${idx}: ${name} → ${TITLE}"
done < /tmp/nlm_doc/<country_slug>/laws_verify.txt
```

验证标准：页面标题（`/info` 返回的 `title`）须包含法律核心信息（编号、年份，如 `UU No. 13 Tahun 2003`）。

链接错误的修复流程：
1. 用 Google 搜索 `site:<官方域名> <法律编号>` 找正确链接
2. 打开正确链接验证标题
3. 修改 config.yaml 中的 URL
4. 若目标国官方数据库无该法，改用替代官方来源（如劳工部 JDIH）
5. 若完全找不到官方链接，从 config.yaml 中删除该条目并加注释说明

### Step 5：生成 Word 文档

```bash
python3 ~/.claude/skills/labor-law-guide/scripts/build_word.py \
    --answers /tmp/nlm_doc/<country_slug>/answers.json \
    --summaries /tmp/nlm_doc/<country_slug>/summaries.json \
    --config /tmp/nlm_doc/<country_slug>/config.yaml \
    --country "<目标国中文名>" \
    --short "<简称>" \
    --country-en "<English Name>" \
    --output ~/Desktop/<目标国中文名>劳动合规指南（2026版）初稿.docx
```

文档结构：
- 封面（华文隶书 36pt 国名 + 英文标题 Times New Roman 22pt）
- 前言
- 外商投资环境 / 劳动合规概要 / 劳动法律体系（含法律表）
- 目录
- 六大板块 15 章正文 + 本章小结
- 特别声明 / 联系人 / 浩天简介

### Step 6：下载法律 PDF + DeepSeek 翻译中文对照表 + 打包

#### 6.1 创建输出文件夹

```bash
FOLDER=~/Desktop/<目标国中文名>劳动合规指南
mkdir -p "${FOLDER}/法律法规原文PDF"
```

#### 6.2 下载每部法律的 PDF 原文

```bash
DL_TAB=$(curl -s "http://localhost:3456/new?url=about:blank" | python3 -c "import sys,json; print(json.load(sys.stdin)['targetId'])")

while IFS='|' read -r idx name url; do
  curl -s "http://localhost:3456/navigate?target=${DL_TAB}&url=${url}" > /dev/null
  sleep 5
  
  PDF_URL=$(curl -s -X POST "http://localhost:3456/eval?target=${DL_TAB}" \
    -d "var links=document.querySelectorAll('a[href*=\".pdf\"]'); links.length>0 ? links[0].href : 'NOT_FOUND'")
  
  SAFE_NAME=$(echo "$name" | sed 's/[\/:]/_/g' | cut -c1-50)
  
  if echo "$PDF_URL" | grep -q "NOT_FOUND"; then
    echo "NO PDF: $name — skipping"
  else
    ACTUAL_URL=$(echo "$PDF_URL" | python3 -c "import sys,json; print(json.load(sys.stdin)['value'])")
    curl -s -L -o "${FOLDER}/法律法规原文PDF/${SAFE_NAME}.pdf" "$ACTUAL_URL"
    echo "DOWNLOADED: ${SAFE_NAME}.pdf"
  fi
done < /tmp/nlm_doc/<country_slug>/laws_verify.txt
```

#### 6.3 DeepSeek 翻译生成中文法律对照表

```bash
python3 -c "
import json, urllib.request, time, yaml

# DeepSeek 翻译法律体系表（需 DEEPSEEK_API_KEY 环境变量）
python3 -c "
import json, os, time, yaml, urllib.request

API_KEY = os.environ['DEEPSEEK_API_KEY']
API_URL = 'https://api.deepseek.com/v1/chat/completions'

with open('/tmp/nlm_doc/<country_slug>/config.yaml') as f:
    config = yaml.safe_load(f)
laws = config['legal_system']['laws']

translations = []
for name, url, desc in laws:
    payload = json.dumps({
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': '你是目标国法律翻译专家。请将以下法律信息整理为中文对照条目。保留法律原文名称，翻译简介为流畅中文。输出格式：法律原文[换行]中文名称：[翻译][换行]简介：[翻译后的中文简介][换行]链接：[URL]'},
            {'role': 'user', 'content': f'法律原文: {name}\n链接: {url}\n简介: {desc}'}
        ],
        'max_tokens': 400,
        'temperature': 0.3,
    }).encode()

    req = urllib.request.Request(API_URL, data=payload, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}',
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            translations.append(result['choices'][0]['message']['content'].strip())
            print(f'OK: {name[:40]}...')
    except Exception as e:
        translations.append(f'{name}\n翻译失败: {e}')
    time.sleep(1)

with open('/tmp/nlm_doc/<country_slug>/law_translations.json', 'w') as f:
    json.dump(translations, f, ensure_ascii=False, indent=2)
print(f'Translated {len(translations)} laws')
"
"

# 生成 Word 对照表
python3 ~/.claude/skills/labor-law-guide/scripts/build_law_reference.py \
    --translations /tmp/nlm_doc/<country_slug>/law_translations.json \
    --font "<目标国字体>" \
    --output "${FOLDER}/<目标国中文名>法律法规中文对照表.docx"
```

#### 6.4 移动合规指南到文件夹并验证

```bash
mv ~/Desktop/<目标国中文名>劳动合规指南（2026版）初稿.docx "${FOLDER}/"

echo "=== 输出文件夹结构 ==="
find "${FOLDER}" -type f | sort
echo ""
echo "=== 文件大小 ==="
du -sh "${FOLDER}"/*
```

最终输出文件夹 `~/Desktop/<目标国中文名>劳动合规指南/` 包含：
- `<目标国中文名>劳动合规指南（2026版）初稿.docx`
- `法律法规中文对照表.docx`（DeepSeek 翻译）
- `法律法规原文PDF/`（下载的 PDF 原文）
- `法律文本模板/`（Step 7——外文原文 + DeepSeek 中文翻译对照）

### Step 7：搜索法律文本模板 + DeepSeek 翻译中文对照

#### 7.1 搜索并下载目标国劳动法律文本模板

通过 CDP + Google 搜索目标国的以下模板（用目标国语言搜索）：

| # | 模板类型 | 搜索关键词示例（印尼语） |
|---|---------|----------------------|
| 1 | 固定期限劳动合同 | `contoh perjanjian kerja waktu tertentu PKWT doc pdf` |
| 2 | 无固定期限劳动合同 | `contoh perjanjian kerja waktu tidak tertentu PKWTT doc pdf` |
| 3 | 录用通知书/Offer Letter | `contoh surat penawaran kerja offer letter doc pdf` |
| 4 | 员工手册/企业规章 | `contoh peraturan perusahaan buku pedoman karyawan pdf` |
| 5 | 解除劳动合同通知 | `contoh surat pemutusan hubungan kerja PHK pdf` |
| 6 | 保密协议 | `contoh perjanjian kerahasiaan non disclosure agreement pdf` |
| 7 | 竞业限制协议 | `contoh perjanjian non kompetisi non compete agreement pdf` |
| 8 | 试用期评估表 | `contoh form evaluasi masa percobaan karyawan pdf` |
| 9 | 警告信/纪律处分 | `contoh surat peringatan karyawan SP1 SP2 SP3 pdf` |
| 10 | 辞职信/辞职协议 | `contoh surat pengunduran diri resignation letter pdf` |

```bash
mkdir -p "${FOLDER}/法律文本模板/原文"
mkdir -p "${FOLDER}/法律文本模板/中文翻译"

TMPL_TAB=$(curl -s "http://localhost:3456/new?url=about:blank" | python3 -c "import sys,json; print(json.load(sys.stdin)['targetId'])")

# 逐个搜索并下载
declare -A TEMPLATES
TEMPLATES=(
  ["固定期限劳动合同"]="contoh perjanjian kerja waktu tertentu PKWT filetype:pdf"
  ["无固定期限劳动合同"]="contoh perjanjian kerja waktu tidak tertentu PKWTT filetype:pdf"
  ["录用通知书"]="contoh surat penawaran kerja offer letter filetype:pdf"
  ["员工手册"]="contoh peraturan perusahaan pedoman karyawan filetype:pdf"
  ["解除劳动合同通知"]="contoh surat PHK pemutusan hubungan kerja filetype:pdf"
  ["保密协议"]="contoh perjanjian kerahasiaan karyawan filetype:pdf"
  ["竞业限制协议"]="contoh perjanjian non kompetisi filetype:pdf"
  ["警告信"]="contoh surat peringatan SP1 karyawan filetype:pdf"
  ["辞职信"]="contoh surat pengunduran diri resignation filetype:pdf"
  ["试用期评估表"]="form evaluasi masa percobaan karyawan filetype:pdf"
)

for KEY in "${!TEMPLATES[@]}"; do
  QUERY="${TEMPLATES[$KEY]}"
  ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''${QUERY}'''))")
  
  curl -s "http://localhost:3456/navigate?target=${TMPL_TAB}&url=https://www.google.com/search?q=${ENCODED}" > /dev/null
  sleep 5
  
  # 提取前 3 个 PDF 链接并依次尝试下载
  LINKS=$(curl -s -X POST "http://localhost:3456/eval?target=${TMPL_TAB}" \
    -d "var links=document.querySelectorAll('a[href*=\".pdf\"]'); var urls=[]; for(var i=0;i<Math.min(links.length,3);i++){urls.push(links[i].href)}; JSON.stringify(urls)")
  
  # 尝试下载第一个可用的 PDF
  PDFS=$(echo "$LINKS" | python3 -c "
import sys, json
try:
    urls = json.loads(sys.stdin.read())['value']
    urls = json.loads(urls) if isinstance(urls, str) else urls
    for u in urls[:3]:
        print(u)
except: pass
")
  
  FIRST_PDF=$(echo "$PDFS" | head -1)
  if [ -n "$FIRST_PDF" ]; then
    SAFE_KEY=$(echo "$KEY" | sed 's/[\/: ]/_/g')
    curl -s -L -o "${FOLDER}/法律文本模板/原文/${SAFE_KEY}.pdf" "$FIRST_PDF" 2>/dev/null && echo "DOWNLOADED: $KEY" || echo "FAILED: $KEY"
  else
    echo "NO RESULT: $KEY"
  fi
done
```

#### 7.2 DeepSeek 翻译模板为中文

```bash
python3 -c "
import json, urllib.request, time, os, glob

API_KEY = os.environ['DEEPSEEK_API_KEY']
API_URL = 'https://api.deepseek.com/v1/chat/completions'

TEMPLATE_DIR = '${FOLDER}/法律文本模板/原文'
OUT_DIR = '${FOLDER}/法律文本模板/中文翻译'

for pdf_file in glob.glob(TEMPLATE_DIR + '/*.pdf'):
    basename = os.path.splitext(os.path.basename(pdf_file))[0]
    out_file = os.path.join(OUT_DIR, basename + '.txt')
    
    payload = json.dumps({
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': f'你是一位法律翻译专家。请将以下目标国劳动法律文本模板翻译为中文，保留原文结构和条款编号。同时附上对模板用途和使用场景的中文说明。'},
            {'role': 'user', 'content': f'请翻译此劳动法律文本模板为中文，说明其用途：文件来源为 {basename}'}
        ],
        'max_tokens': 2000,
        'temperature': 0.3,
    }).encode()

    req = urllib.request.Request(API_URL, data=payload, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}',
    })
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            translation = result['choices'][0]['message']['content'].strip()
            with open(out_file, 'w') as f:
                f.write(f'# {basename}\n\n')
                f.write('## 中文翻译\n\n')
                f.write(translation)
            print(f'TRANSLATED: {basename}')
    except Exception as e:
        print(f'ERR {basename}: {e}')
    time.sleep(1)
print('Template translations complete')
"
```

#### 7.3 生成模板对照 Word 文档

```bash
python3 -c "
from docx import Document
from docx.shared import Pt, Cm
import glob, os

doc = Document()
for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)

style = doc.styles['Normal']
style.font.name = '等线'
style.font.size = Pt(11)

title = doc.add_paragraph()
title.alignment = 1  # center
run = title.add_run('目标国劳动法律文本模板（双语对照）')
run.font.size = Pt(16)
run.font.bold = True
run.font.name = '黑体'

doc.add_paragraph()

TEMPLATE_DIR = '${FOLDER}/法律文本模板/中文翻译'
for txt_file in sorted(glob.glob(TEMPLATE_DIR + '/*.txt')):
    with open(txt_file) as f:
        content = f.read()
    
    # Split sections by ## markers
    lines = content.strip().split('\n')
    for line in lines:
        p = doc.add_paragraph()
        if line.startswith('# '):
            run = p.add_run(line[2:])
            run.font.size = Pt(14)
            run.font.bold = True
        elif line.startswith('## '):
            run = p.add_run(line[3:])
            run.font.size = Pt(12)
            run.font.bold = True
        else:
            run = p.add_run(line)
            run.font.size = Pt(10)

doc.save('${FOLDER}/法律文本模板/法律文本模板中文对照.docx')
print('Template reference doc created')
"
```

#### 7.4 验证模板完整度

```bash
echo "=== 模板文件夹 ==="
echo "原文 PDF:"
ls -la "${FOLDER}/法律文本模板/原文/" 2>/dev/null | tail -n +2 | wc -l
echo "中文翻译:"
ls -la "${FOLDER}/法律文本模板/中文翻译/" 2>/dev/null | tail -n +2 | wc -l
```

目标：至少收集 8 种类型的文本模板，每种均有外文原文和中文翻译对照。

## 异常速查

| 症状 | 处理 |
|------|------|
| 找不到按钮/输入框 | 截图查看页面，针对性写选择器 |
| Discover 目标国语言无结果 | 换英语关键词重搜 |
| 提问不触发 Angular 提交 | 确认用 `execCommand('insertText')` + `clickAt` |
| 答案超时（>120s） | 重试最多 3 次，仍失败则跳过该问题 |
| 流程中断 | 从 `/tmp/nlm_doc/<country_slug>/checkpoint.json` 恢复 |
| eval 报错 | 重试 1 次，仍失败则 `/info` 检查 tab 是否存活 |
| DeepSeek 小结生成超时 | timeout 设 120s，单个失败不影响其他章节 |
| Chrome 授权弹窗阻塞 CDP | 先手动点"允许"，再调用 CDP 命令 |

## 关键参考文件

| 文件 | 用途 |
|------|------|
| `references/search-prompts.yaml` | 16 个 Discover 搜索领域（zh/en 关键词） |
| `references/chapter-questions.yaml` | 18 个提问关键词 |
| `references/chapter-structure.yaml` | 章节结构定义 |
| `scripts/build_word.py` | Word 文档生成脚本 |
