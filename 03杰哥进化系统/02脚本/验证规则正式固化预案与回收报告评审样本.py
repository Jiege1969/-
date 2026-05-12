# -*- coding: utf-8 -*-
"""
名称：验证规则正式固化预案与回收报告评审样本.py
作用：验证小任务 I 的规则数量、样本数量、A-F 报告读取、真实动作禁用和正式库禁用。
安全边界：只运行本地生成与验证；不触发 n8n、不真实发送、不调用券商接口、不自动交易、不写正式库。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PACKAGE_NAME = "规则正式固化预案与总管回收报告自动评审样本"


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return system_root().parents[0]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def build_verify_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 规则正式固化预案与回收报告评审样本验收报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 验收结论：{report['验收结论']}",
        f"- 通过项：{report['汇总']['通过']}",
        f"- 失败项：{report['汇总']['失败']}",
        f"- 规则数量：{report['规则数量']}",
        f"- 样本数量：{report['样本数量']}",
        f"- 交付阻断数量：{report['交付阻断数量']}",
        f"- 安全阻断数量：{report['安全阻断数量']}",
        "",
        "## 检查项",
        "",
    ]
    for check in report["检查项"]:
        mark = "通过" if check["通过"] else "失败"
        lines.append(f"- {mark}：{check['名称']}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 自动交易禁用。",
            "- 券商接口未调用。",
            "- n8n 未触发。",
            "- 企业微信真实发送未触发。",
            "- 正式库未写入。",
            "- 只写授权目录和指定总管回收报告。",
            "",
        ]
    )
    return "\n".join(lines)


def refresh_recovery_report(recovery_path: Path, verify_report: dict[str, Any]) -> None:
    text = recovery_path.read_text(encoding="utf-8-sig") if recovery_path.exists() else "# 03进化系统_第三批小任务I回收报告_最新\n"
    marker = "## 验证脚本结果"
    base = text.split(marker)[0].rstrip()
    lines = [
        base,
        "",
        marker,
        "",
        f"- 验证时间：{verify_report['生成时间']}",
        f"- 验收结论：{verify_report['验收结论']}",
        f"- 通过项：{verify_report['汇总']['通过']}",
        f"- 失败项：{verify_report['汇总']['失败']}",
        f"- 规则数量：{verify_report['规则数量']}",
        f"- 样本数量：{verify_report['样本数量']}",
        f"- A-F报告读取：{','.join(verify_report['读取报告窗口'])}",
        f"- 交付阻断数量：{verify_report['交付阻断数量']}",
        f"- 安全阻断数量：{verify_report['安全阻断数量']}",
        f"- 验收 JSON：{verify_report['验收JSON']}",
        f"- 验收 Markdown：{verify_report['验收Markdown']}",
        "",
    ]
    write_text(recovery_path, "\n".join(lines))


def main() -> int:
    root = system_root()
    all_root = repo_root()
    generator = root / "02脚本" / "生成规则正式固化预案与回收报告评审样本.py"
    data_dir = root / "03数据" / "24规则正式固化预案与回收报告评审"
    latest_json = data_dir / f"{PACKAGE_NAME}_最新.json"
    latest_md = data_dir / f"{PACKAGE_NAME}_最新.md"
    doc_path = root / "07文档" / "规则正式固化预案接入口径_最新.md"
    recovery_path = all_root / "00杰哥系统总管" / "03数据" / "并行回收" / "03进化系统_第三批小任务I回收报告_最新.md"

    result = subprocess.run(
        [sys.executable, str(generator)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码为 0", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "正式固化预案 JSON 存在", latest_json.exists(), str(latest_json))
    add_check(checks, "正式固化预案 Markdown 存在", latest_md.exists(), str(latest_md))
    add_check(checks, "接入口径文档存在", doc_path.exists(), str(doc_path))
    add_check(checks, "固定回收报告存在", recovery_path.exists(), str(recovery_path))

    payload = load_json(latest_json) if latest_json.exists() else {}
    rules = payload.get("正式固化预案", [])
    samples = payload.get("自动评审输出样本", [])
    report_reviews = payload.get("A-F回收报告读取结果", [])
    safety = payload.get("安全边界", {})
    sample_names = {sample.get("样本名") for sample in samples}
    report_windows = {item.get("窗口") for item in report_reviews}

    required_rule_fields = {"规则ID", "适用系统", "触发条件", "阻断/降级动作", "证据要求", "回滚方式"}
    required_samples = {"通过计入", "安全阻断不失败", "交付阻断需退回", "越权真实动作阻断"}

    add_check(checks, "规则数量不少于 5", len(rules) >= 5, len(rules))
    add_check(checks, "规则字段完整", all(required_rule_fields.issubset(rule) for rule in rules), rules)
    add_check(checks, "样本数量为 4", len(samples) == 4, len(samples))
    add_check(checks, "四类样本齐全", required_samples.issubset(sample_names), sorted(sample_names))
    add_check(checks, "A-F 报告均被读取", {"A", "B", "C", "D", "E", "F"}.issubset(report_windows), sorted(report_windows))
    add_check(checks, "A-F 报告路径均存在", all(item.get("存在") for item in report_reviews), report_reviews)
    add_check(checks, "通过计入样本可计入", any(s.get("样本名") == "通过计入" and s.get("是否可计入进度") is True for s in samples), samples)
    add_check(checks, "安全阻断不失败样本可计入", any(s.get("样本名") == "安全阻断不失败" and s.get("安全阻断") is True and s.get("是否可计入进度") is True for s in samples), samples)
    add_check(checks, "交付阻断样本不可计入", any(s.get("样本名") == "交付阻断需退回" and s.get("交付阻断") is True and s.get("是否可计入进度") is False for s in samples), samples)
    add_check(checks, "越权真实动作样本双阻断", any(s.get("样本名") == "越权真实动作阻断" and s.get("交付阻断") is True and s.get("安全阻断") is True and s.get("是否可计入进度") is False for s in samples), samples)
    add_check(checks, "自动交易禁用", safety.get("自动交易启用") is False, safety)
    add_check(checks, "券商接口未调用", safety.get("券商接口调用") is False, safety)
    add_check(checks, "n8n/真实发送禁用", safety.get("n8n触发") is False and safety.get("企业微信真实发送") is False, safety)
    add_check(checks, "正式库禁用", safety.get("正式库写入") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report: dict[str, Any] = {
        "生成时间": now_text(),
        "任务": "规则正式固化预案与总管回收报告自动评审读取验收",
        "验收结论": "通过" if failed == 0 else "失败",
        "汇总": {"通过": passed, "失败": failed},
        "规则数量": len(rules),
        "样本数量": len(samples),
        "读取报告窗口": sorted(report_windows),
        "交付阻断数量": sum(1 for sample in samples if sample.get("交付阻断")),
        "安全阻断数量": sum(1 for sample in samples if sample.get("安全阻断")),
        "检查项": checks,
        "安全边界": safety,
        "验收对象": str(latest_json),
    }

    tag = stamp()
    version_json = data_dir / f"{PACKAGE_NAME}_验收_{tag}.json"
    version_md = data_dir / f"{PACKAGE_NAME}_验收_{tag}.md"
    latest_verify_json = data_dir / f"{PACKAGE_NAME}_验收_最新.json"
    latest_verify_md = data_dir / f"{PACKAGE_NAME}_验收_最新.md"
    verify_report["验收JSON"] = str(latest_verify_json)
    verify_report["验收Markdown"] = str(latest_verify_md)

    write_json(version_json, verify_report)
    write_json(latest_verify_json, verify_report)
    markdown = build_verify_markdown(verify_report)
    write_text(version_md, markdown)
    write_text(latest_verify_md, markdown)
    refresh_recovery_report(recovery_path, verify_report)

    print(json.dumps({"验收结论": verify_report["验收结论"], "通过": passed, "失败": failed, "交付阻断数量": verify_report["交付阻断数量"], "安全阻断数量": verify_report["安全阻断数量"]}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
