#!/usr/bin/env python3
"""Generate chapter summaries using DeepSeek API.
Usage: python3 gen_summaries.py --answers answers.json --short "韩国" --output summaries.json
"""
import json, time, argparse, urllib.request, urllib.error, os, sys

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = "https://api.deepseek.com/v1/chat/completions"

if not API_KEY:
    print("Error: DEEPSEEK_API_KEY environment variable not set", file=sys.stderr)
    sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("--answers", required=True)
parser.add_argument("--short", required=True, help="Short country name for chapter titles")
parser.add_argument("--output", required=True)
args = parser.parse_args()

with open(args.answers) as f:
    answers = json.load(f)

chapters = [
    (f"CA:第1章 外商投资企业在{args.short}用工主体资格合规", "外商投资企业用工主体资格合规"),
    (f"CA:第2章 用工形式选择", "用工形式选择"),
    (f"CA:第3章 劳动合同订立合规", "劳动合同订立合规"),
    (f"CA:第4章 劳动合同履行与变更合规", "劳动合同履行与变更合规"),
    (f"CA:第5章 劳动合同解除与终止合规", "劳动合同解除与终止合规"),
    (f"CA:第6章 工作时间与休息休假合规", "工作时间与休息休假合规"),
    (f"CA:第7章 工作薪酬合规管理", "工作薪酬合规管理"),
    (f"CA:第8章 公积金及保险合规", "公积金及保险合规"),
    (f"CA:第9章 劳动保护与职业安全合规", "劳动保护与职业安全合规"),
    (f"CA:第10章 商业秘密保护与竞业限制合规", "商业秘密保护与竞业限制合规"),
    (f"CA:第11章 特殊员工保护合规", "特殊员工保护合规"),
    (f"CA:第12章 反歧视与反性骚扰合规", "反歧视与反性骚扰合规"),
    (f"CA:第13章 {args.short}工会运作合规", "工会运作合规"),
    (f"CA:第14章 企业内部民主管理合规", "企业内部民主管理合规"),
    (f"CA:第15章 {args.short}劳动争议解决机制", "劳动争议解决机制"),
]

summaries = {}
for summary_key, answer_key in chapters:
    content = answers.get(answer_key, "")
    if not content:
        print(f"SKIP {summary_key}: no content")
        summaries[summary_key] = "（本章小结生成失败）"
        continue

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一位资深律所合伙人。请根据本章内容写一段150-250字的本章小结，概括核心法律要点和关键合规建议。语气专业、平和，不要比喻。"},
            {"role": "user", "content": f"请为以下章节内容写一段本章小结（150-250字）：\n\n{content[:3000]}"}
        ],
        "max_tokens": 500,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(API_URL, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    })

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            summary = result["choices"][0]["message"]["content"].strip()
            summaries[summary_key] = summary
            print(f"OK {summary_key}: {len(summary)} chars")
    except Exception as e:
        print(f"ERR {summary_key}: {e}")
        summaries[summary_key] = "（本章小结生成失败）"

    time.sleep(1)

with open(args.output, "w") as f:
    json.dump(summaries, f, ensure_ascii=False, indent=2)
print(f"\nSaved {len(summaries)} summaries to {args.output}")
