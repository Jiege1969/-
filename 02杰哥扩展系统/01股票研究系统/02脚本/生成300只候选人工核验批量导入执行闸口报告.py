# -*- coding: utf-8 -*-
"""
名称：生成300只候选人工核验批量导入执行闸口报告.py
作用：综合119校验和120预演，判断是否允许进入人工确认后的103导入执行；只判断不导入。
触发方式：python 生成300只候选人工核验批量导入执行闸口报告.py
依赖：Python标准库；300只候选人工核验批量导入执行闸口规则.json；119校验报告；120导入预演。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读119/120并写121闸口报告；不写入核验结果；不修改103；不导入填报表；不应用103派生任务；不刷新101/102；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-05-01 创建人工核验批量导入执行闸口报告脚本。
标识：stock-trial-pool-300-manual-verification-batch-import-execution-gate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def block_reasons(validation: dict[str, Any], preview: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    validation_summary = validation.get("摘要", {})
    preview_summary = preview.get("摘要", {})
    if validation_summary.get("缺失列"):
        reasons.append("119校验报告存在缺失列")
    if validation_summary.get("问题数量", 0) != 0:
        reasons.append("119校验报告存在问题")
    if validation_summary.get("是否可进入导入前人工确认") is not True:
        reasons.append("119校验报告未允许进入导入前人工确认")
    if preview_summary.get("问题数量", 0) != 0:
        reasons.append("120预演存在问题")
    if preview_summary.get("已填写行数", 0) <= 0:
        reasons.append("120预演显示尚无已填写行")
    if preview_summary.get("将产生变更的任务数", 0) <= 0:
        reasons.append("120预演显示无待导入变更")
    if preview_summary.get("是否可进入导入前人工确认") is not True:
        reasons.append("120预演未允许进入导入前人工确认")
    return reasons


def build_markdown(report: dict[str, Any]) -> str:
    gate = report["闸口结论"]
    lines = [
        "# 300只候选人工核验批量导入执行闸口报告",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 是否允许进入人工确认导入103：{gate['是否允许进入人工确认导入103']}",
        f"- 阻断原因数量：{len(gate['阻断原因'])}",
        f"- 当前结论：{gate['当前结论']}",
        "",
        "## 阻断原因",
        ""
    ]
    if gate["阻断原因"]:
        for item in gate["阻断原因"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无阻断原因。")
    lines.extend(["", "## 输入摘要", ""])
    validation = report.get("119校验摘要", {})
    preview = report.get("120预演摘要", {})
    lines.append(f"- 119行数：{validation.get('行数')}")
    lines.append(f"- 119已填写任务数量：{validation.get('已填写任务数量')}")
    lines.append(f"- 119问题数量：{validation.get('问题数量')}")
    lines.append(f"- 120已填写行数：{preview.get('已填写行数')}")
    lines.append(f"- 120待导入变更任务数：{preview.get('将产生变更的任务数')}")
    lines.append(f"- 120问题数量：{preview.get('问题数量')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只候选人工核验批量导入执行闸口规则.json"
    rule = load_json(rule_path)
    validation_path = root / "03数据" / "119人工核验批量填报模板" / "300只候选人工核验批量填报表校验报告_最新.json"
    preview_path = root / "03数据" / "120人工核验批量导入预演" / "300只候选人工核验批量填报导入预演_最新.json"
    validation = load_json(validation_path)
    preview = load_json(preview_path)
    reasons = block_reasons(validation, preview)
    allowed = not reasons
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "输入文件": {
            "119批量填报校验报告": str(validation_path),
            "120批量导入预演": str(preview_path)
        },
        "119校验摘要": validation.get("摘要", {}),
        "120预演摘要": preview.get("摘要", {}),
        "允许进入导入前人工确认条件": rule.get("允许进入导入前人工确认条件", []),
        "闸口结论": {
            "是否允许进入人工确认导入103": allowed,
            "阻断原因": reasons,
            "当前结论": "允许进入人工确认导入103，但本闸口不执行导入。" if allowed else "禁止进入导入103；需先补齐119填报并通过120预演。"
        },
        "安全边界": rule.get("安全边界", {})
    }
    output_dir = root / rule["输出"]["数据目录"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"300只候选人工核验批量导入执行闸口报告_{stamp}.json"
    latest_json = output_dir / rule["输出"]["最新JSON"]
    output_md = output_dir / f"300只候选人工核验批量导入执行闸口报告_{stamp}.md"
    latest_md = output_dir / rule["输出"]["最新Markdown"]
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否允许进入人工确认导入103": allowed, "阻断原因数量": len(reasons), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
