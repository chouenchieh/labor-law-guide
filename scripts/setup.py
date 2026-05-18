#!/usr/bin/env python3
"""First-run setup: configure firm info and contact details for generated guides."""

import os
import sys
import yaml

CONFIG_PATH = os.path.expanduser("~/.claude/skills/labor-law-guide/config.yaml")

QUESTIONS = [
    ("firm.name", "律所名称 (Firm name)", "浩天律师事务所"),
    ("firm.address", "律所地址 (Firm address)", ""),
    ("firm.phone", "律所电话 (Firm phone)", ""),
    ("firm.website", "律所网址 (Firm website)", ""),
    ("contact.name", "联系人姓名 (Contact name)", ""),
    ("contact.title", "联系人职位 (Contact title)", ""),
    ("contact.office", "联系人办公室 (Contact office)", ""),
    ("contact.email", "联系人邮箱 (Contact email)", ""),
]

def ask(key, prompt, default):
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    else:
        while True:
            val = input(f"{prompt}: ").strip()
            if val:
                return val
            print("  (必填)")

def main():
    print("=" * 50)
    print("  Labor Law Guide Skill — 首次配置")
    print("=" * 50)
    print()
    print("此信息将写入生成的合规指南封面和文末。")
    print(f"配置保存到: {CONFIG_PATH}")
    print()

    config = {}

    print("--- 律所信息 ---")
    for key, prompt, default in QUESTIONS:
        if key.startswith("firm."):
            section, field = key.split(".")
            config.setdefault(section, {})
            config[section][field] = ask(key, prompt, default)

    print()
    print("--- 联系人信息（显示在指南「联系人」部分）---")
    for key, prompt, default in QUESTIONS:
        if key.startswith("contact."):
            section, field = key.split(".")
            config.setdefault(section, {})
            config[section][field] = ask(key, prompt, default)

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        f.write("# Labor Law Guide Skill 配置文件\n")
        f.write("# 生成指南时通过 --config 参数传入\n\n")
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, indent=2)

    print()
    print(f"配置已保存到 {CONFIG_PATH}")
    print()
    print("使用方法:")
    print(f"  python3 scripts/build_word.py --config {CONFIG_PATH} ...")

if __name__ == "__main__":
    main()
