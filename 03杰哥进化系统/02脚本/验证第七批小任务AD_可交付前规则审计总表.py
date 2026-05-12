# -*- coding: utf-8 -*-
"""
验证第七批并行小任务 AD：03进化 / 可交付前规则审计总表。

验收只运行本地生成脚本并检查产物内容；不触发真实外部动作。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
TASK_NAME = "第七批小任务AD_可交付前规则审计总表"
SCRIPT_DIR = ROOT / "03杰哥进化系统" / "02脚本"
DATA_DIR = ROOT / "03杰哥进化系统" / "03数据" / "27第七批小任务AD_可交付前规则审计总表"
DOC_PATH = ROOT / "03杰哥进化系统" / "07文档" / f"{TASK_NAME}说明_最新.md"
RECOVERY_PATH = ROOT / "00杰哥系统总管" / "03数据" / "并行回收" / "03进化系统_第七批小任务AD规则审计回收报告_最新.md"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def build_verify_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 第七批小任务AD：可交付前规则审计总表验收报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 验收结论：{report['验收结论']}",
        f"- 通过项：{report['汇总']['通过']}",
        f"- 失败项：{report['汇总']['失败']}",
        f"- 输入来源数量：{report['输入来源数量']}",
        f"- 审计项数量：{report['审计项数量']}",
        f"- 安全阻断不失败：{report['安全阻断不失败']}",
        f"- 真实动作禁用：{report['真实动作禁用']}",
        f"- 用户暂停继承：{report['用户暂停继承']}",
        "",
        "## 检查项",
        "",
    ]
    for check in report["检查项"]:
        mark = "通过" if check["通过"] else "失败"
        lines.append(f"- {mark}：{check['检查项']}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- n8n 触发禁用。",
            "- 企业微信真实发送禁用。",
            "- 正式库写入禁用。",
            "- 券商接口禁用。",
            "- 自动交易禁用。",
            "- 本职工作系统不触碰。",
            "- 安全阻断作为合规边界，不按失败处理。",
            "",
        ]
    )
    return "\n".join(lines)


def refresh_recovery_report(report: dict[str, Any]) -> None:
    text = read_text(RECOVERY_PATH) or "# 03进化系统_第七批小任务AD规则审计回收报告_最新\n"
    text = text.replace("- 验收结果：待验收", f"- 验收结果：{report['验收结论']}")
    marker = "## 验收脚本结果"
    base = text.split(marker)[0].rstrip()
    lines = [
        base,
        "",
        marker,
        "",
        f"- 验收时间：{report['生成时间']}",
        f"- 验收结论：{report['验收结论']}",
        f"- 通过项：{report['汇总']['通过']}",
        f"- 失败项：{report['汇总']['失败']}",
        f"- 输入来源数量：{report['输入来源数量']}",
        f"- 已读取来源数量：{report['已读取来源数量']}",
        f"- 审计项数量：{report['审计项数量']}",
        f"- 安全阻断不失败：{report['安全阻断不失败']}",
        f"- 真实动作禁用：{report['真实动作禁用']}",
        f"- 用户暂停继承：{report['用户暂停继承']}",
        f"- 验收JSON：`{report['验收JSON']}`",
        f"- 验收Markdown：`{report['验收Markdown']}`",
        "",
    ]
    write_text(RECOVERY_PATH, "\n".join(lines))


def main() -> int:
    generator = SCRIPT_DIR / "生成第七批小任务AD_可交付前规则审计总表.py"
    latest_json = DATA_DIR / f"{TASK_NAME}_最新.json"
    latest_md = DATA_DIR / f"{TASK_NAME}_最新.md"

    result = subprocess.run(
        [sys.executable, str(generator)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码为0", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "审计总表JSON存在", latest_json.exists(), str(latest_json))
    add_check(checks, "审计总表Markdown存在", latest_md.exists(), str(latest_md))
    add_check(checks, "审计说明文档存在", DOC_PATH.exists(), str(DOC_PATH))
    add_check(checks, "指定并行回收报告存在", RECOVERY_PATH.exists(), str(RECOVERY_PATH))

    payload = json.loads(read_text(latest_json)) if latest_json.exists() else {}
    sources = payload.get("输入来源", [])
    rows = payload.get("可交付前规则审计总表", [])
    bans = payload.get("禁止真实动作", {})
    conclusion = payload.get("统一结论", {})

    source_categories = {item.get("类别") for item in sources}
    row_names = {item.get("审计项") for item in rows}

    add_check(checks, "读取股票硬闸门来源", "股票硬闸门" in source_categories and any(item.get("已读取") for item in sources if item.get("类别") == "股票硬闸门"), source_categories)
    add_check(checks, "读取并行策略来源", "并行策略" in source_categories and any(item.get("已读取") for item in sources if item.get("类别") == "并行策略"), source_categories)
    add_check(checks, "读取第五批成果", {"第五批成果", "第五批窗口"}.issubset(source_categories), source_categories)
    add_check(checks, "读取第六批成果", {"第六批成果", "第六批窗口"}.issubset(source_categories), source_categories)
    add_check(checks, "读取03进化U/AA样本", "03进化样本" in source_categories and sum(1 for item in sources if item.get("类别") == "03进化样本" and item.get("已读取")) >= 2, sources)
    add_check(checks, "审计总表包含6项", len(rows) == 6, len(rows))
    add_check(checks, "审计总表包含股票硬闸门项", "股票硬闸门继承" in row_names, row_names)
    add_check(checks, "审计总表包含并行策略项", "并行策略继承" in row_names, row_names)
    add_check(checks, "审计总表包含本职工作暂停项", "本职工作暂停继承" in row_names, row_names)
    add_check(checks, "安全阻断不失败为真", conclusion.get("安全阻断不失败") is True and all(row.get("安全阻断不失败") is True for row in rows), conclusion)
    add_check(checks, "真实动作禁用为真", conclusion.get("真实动作禁用") is True and all(row.get("真实动作禁用") is True for row in rows), conclusion)
    add_check(checks, "用户暂停继承为真", conclusion.get("用户暂停继承") is True and all(row.get("用户暂停继承") is True for row in rows), conclusion)
    add_check(checks, "n8n真实触发禁用", bans.get("触发n8n") is False, bans)
    add_check(checks, "企业微信真实消息禁用", bans.get("发送企业微信真实消息") is False, bans)
    add_check(checks, "正式库写入禁用", bans.get("写正式库") is False, bans)
    add_check(checks, "券商接口禁用", bans.get("调用券商接口") is False, bans)
    add_check(checks, "自动交易禁用", bans.get("自动交易") is False, bans)
    add_check(checks, "本职工作系统不触碰", bans.get("触碰本职工作系统") is False, bans)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report: dict[str, Any] = {
        "生成时间": now_text(),
        "任务": TASK_NAME,
        "验收结论": "通过" if failed == 0 else "失败",
        "汇总": {"通过": passed, "失败": failed},
        "输入来源数量": len(sources),
        "已读取来源数量": sum(1 for item in sources if item.get("已读取")),
        "审计项数量": len(rows),
        "安全阻断不失败": conclusion.get("安全阻断不失败") is True,
        "真实动作禁用": conclusion.get("真实动作禁用") is True,
        "用户暂停继承": conclusion.get("用户暂停继承") is True,
        "禁止真实动作": bans,
        "检查项": checks,
    }
    verify_json = DATA_DIR / f"{TASK_NAME}_验收_最新.json"
    verify_md = DATA_DIR / f"{TASK_NAME}_验收_最新.md"
    verify_report["验收JSON"] = str(verify_json)
    verify_report["验收Markdown"] = str(verify_md)
    write_json(verify_json, verify_report)
    write_text(verify_md, build_verify_markdown(verify_report))
    refresh_recovery_report(verify_report)

    print(json.dumps({"验收结论": verify_report["验收结论"], "通过": passed, "失败": failed}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
