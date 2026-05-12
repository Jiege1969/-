# -*- coding: utf-8 -*-
"""
验证第六批小任务 AA：读取路径、6 样本、可计入、仍需人工确认、
真实动作禁用、本职工作暂停继承和安全边界。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


TASK_NAME = "第六批小任务AA_第五批成果可交付前规则审计样本"
DATA_DIR_NAME = "26第六批小任务AA_第五批成果可交付前规则审计样本"


def root() -> Path:
    return Path(r"D:\杰哥智能化系统")


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def build_verify_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 第六批小任务AA：第五批成果可交付前规则审计样本验收报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 验收结论：{report['验收结论']}",
        f"- 通过项：{report['汇总']['通过']}",
        f"- 失败项：{report['汇总']['失败']}",
        f"- 审计样本数量：{report['审计样本数量']}",
        f"- 读取路径数量：{report['读取路径数量']}",
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
            "- 真实外部 API 禁用。",
            "- 本职工作系统不触碰。",
            "- 真实媒体生成或发布禁用。",
            "",
        ]
    )
    return "\n".join(lines)


def refresh_recovery_report(recovery_path: Path, report: dict[str, Any]) -> None:
    text = recovery_path.read_text(encoding="utf-8-sig") if recovery_path.exists() else "# 03进化系统_第六批小任务AA回收报告_最新\n"
    text = text.replace("- 验收结果：待验证", f"- 验收结果：{report['验收结论']}")
    marker = "## 验证脚本结果"
    base = text.split(marker)[0].rstrip()
    lines = [
        base,
        "",
        marker,
        "",
        f"- 验证时间：{report['生成时间']}",
        f"- 验收结论：{report['验收结论']}",
        f"- 通过项：{report['汇总']['通过']}",
        f"- 失败项：{report['汇总']['失败']}",
        f"- 审计样本数量：{report['审计样本数量']}",
        f"- 读取路径数量：{report['读取路径数量']}",
        f"- 可计入样本数：{report['可计入样本数']}",
        f"- 仍需人工确认样本数：{report['仍需人工确认样本数']}",
        f"- 验收JSON：`{report['验收JSON']}`",
        f"- 验收Markdown：`{report['验收Markdown']}`",
        "",
    ]
    write_text(recovery_path, "\n".join(lines))


def main() -> int:
    evo = root() / "03杰哥进化系统"
    script_dir = evo / "02脚本"
    data_dir = evo / "03数据" / DATA_DIR_NAME
    generator = script_dir / "生成第六批小任务AA_第五批成果可交付前规则审计样本.py"
    latest_json = data_dir / f"{TASK_NAME}_最新.json"
    latest_md = data_dir / f"{TASK_NAME}_最新.md"
    doc_path = evo / "07文档" / "第六批小任务AA_第五批成果可交付前规则审计样本说明_最新.md"
    recovery_path = root() / "00杰哥系统总管" / "03数据" / "并行回收" / "03进化系统_第六批小任务AA回收报告_最新.md"

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
    add_check(checks, "规则审计样本JSON存在", latest_json.exists(), str(latest_json))
    add_check(checks, "规则审计样本Markdown存在", latest_md.exists(), str(latest_md))
    add_check(checks, "规则审计说明文档存在", doc_path.exists(), str(doc_path))
    add_check(checks, "固定AA回收报告存在", recovery_path.exists(), str(recovery_path))

    payload = json.loads(latest_json.read_text(encoding="utf-8-sig")) if latest_json.exists() else {}
    reports = payload.get("读取报告", [])
    samples = payload.get("可交付前规则审计样本", [])
    safety = payload.get("安全边界", {})
    unified = payload.get("统一审计口径", {})
    windows = {item.get("窗口") for item in reports}
    sample_windows = {item.get("来源窗口") for item in samples}

    add_check(checks, "读取路径包含P/Q/R/S/T/U", {"P", "Q", "R", "S", "T", "U"}.issubset(windows), sorted(windows))
    add_check(checks, "读取路径均存在", all(item.get("存在") for item in reports), reports)
    add_check(checks, "读取路径均已读取", all(item.get("已读取") for item in reports), reports)
    add_check(checks, "审计样本数量为6", len(samples) == 6, len(samples))
    add_check(checks, "六个来源窗口齐全", {"P", "Q", "R", "S", "T", "U"}.issubset(sample_windows), sorted(sample_windows))
    add_check(checks, "可计入口径存在且样本均可计入", "可计入" in unified and all(s.get("可计入") is True for s in samples), unified)
    add_check(checks, "仍需人工确认口径存在", "仍需人工确认" in unified and any(s.get("仍需人工确认") is True for s in samples), unified)
    add_check(checks, "真实动作禁用口径为真", unified.get("真实动作禁用") is True and all(s.get("真实动作禁用") is True for s in samples), unified)
    add_check(checks, "本职工作暂停继承口径为真", unified.get("本职工作暂停继承") is True and all(s.get("本职工作暂停继承") is True for s in samples), unified)
    add_check(checks, "安全阻断不失败口径为真", unified.get("安全阻断不失败") is True and all(s.get("安全阻断不按失败处理") is True for s in samples), unified)
    add_check(checks, "n8n触发禁用", safety.get("触发n8n") is False and unified.get("n8n触发禁用") is True, safety)
    add_check(checks, "企业微信真实发送禁用", safety.get("企业微信真实发送") is False and unified.get("企业微信真实发送禁用") is True, safety)
    add_check(checks, "正式库写入禁用", safety.get("写正式库") is False and unified.get("正式库写入禁用") is True, safety)
    add_check(checks, "券商接口禁用", safety.get("调用券商接口") is False and unified.get("券商接口禁用") is True, safety)
    add_check(checks, "自动交易禁用", safety.get("自动交易") is False and unified.get("自动交易禁用") is True, safety)
    add_check(checks, "真实外部API禁用", safety.get("真实外部API") is False, safety)
    add_check(checks, "本职工作系统不触碰", safety.get("触碰本职工作系统") is False, safety)
    add_check(checks, "真实媒体生成或发布禁用", safety.get("真实媒体生成或发布") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report: dict[str, Any] = {
        "生成时间": now_text(),
        "任务": TASK_NAME,
        "验收结论": "通过" if failed == 0 else "失败",
        "汇总": {"通过": passed, "失败": failed},
        "审计样本数量": len(samples),
        "读取路径数量": len(reports),
        "可计入样本数": sum(1 for item in samples if item.get("可计入") is True),
        "仍需人工确认样本数": sum(1 for item in samples if item.get("仍需人工确认") is True),
        "检查项": checks,
        "安全边界": safety,
    }

    latest_verify_json = data_dir / f"{TASK_NAME}_验收_最新.json"
    latest_verify_md = data_dir / f"{TASK_NAME}_验收_最新.md"
    verify_report["验收JSON"] = str(latest_verify_json)
    verify_report["验收Markdown"] = str(latest_verify_md)
    write_json(latest_verify_json, verify_report)
    write_text(latest_verify_md, build_verify_markdown(verify_report))
    refresh_recovery_report(recovery_path, verify_report)

    print(json.dumps({"验收结论": verify_report["验收结论"], "通过": passed, "失败": failed, "审计样本数量": len(samples)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
