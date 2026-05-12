# -*- coding: utf-8 -*-
"""
名称：生成本职工作系统状态摘要.py
作用：汇总办公材料计划、草稿预演器、正式输出禁用态和本地生成门禁，生成本职工作系统日常状态摘要。
触发方式：python 生成本职工作系统状态摘要.py
依赖：Python标准库；办公材料计划；R03办公材料草稿预演器联检；办公材料本地生成门禁报告；办公材料正式输出禁用态检查。
所属系统：02杰哥扩展系统/03本职工作系统
安全边界：只读取本职工作系统本地草稿、计划和门禁日志；只写入03数据/05状态摘要；不读取涉密资料；不生成正式文档；不覆盖正式文档；不自动外发；不自动上传；不触发n8n；不发送企业微信；不写旧系统。
创建/修改记录：2026-04-29 创建本职工作系统状态摘要生成脚本。
标识：office-work-system-status-summary-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["汇总"]
    return "\n".join(
        [
            "# 本职工作系统状态摘要",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{summary['状态']}",
            f"- 材料类型数量：{summary['材料类型数量']}",
            f"- 草稿模板数量：{summary['草稿模板数量']}",
            f"- R03预演通过数：{summary['R03预演通过数']}",
            f"- R03预演失败数：{summary['R03预演失败数']}",
            f"- 正式输出状态：{summary['正式输出状态']}",
            "",
            "## 安全边界",
            "",
            "- 当前只允许任务计划、草稿框架和本地预演。",
            "- 涉密资料读取、正式文档生成、覆盖、外发、上传、n8n触发、企业微信发送均保持关闭。",
        ]
    ) + "\n"


def main() -> int:
    root = module_root()
    data_root = root / "03数据"
    output_dir = data_root / "05状态摘要"
    plan_report = load_json(data_root / "02任务计划" / "办公材料计划_最新.json", {})
    disabled_report = load_json(data_root / "04本地生成门禁" / "办公材料正式输出禁用态检查_最新.json", {})
    r03_report = load_json(data_root / "04本地生成门禁" / "R03办公材料草稿预演器联检_最新.json", {})

    material_types = plan_report.get("材料类型", [])
    summary = r03_report.get("汇总", {})
    linked_checks = r03_report.get("联检结果", {})
    disabled_ok = disabled_report.get("执行器状态") == "禁用态" and disabled_report.get("是否生成正式文档") is False
    sensitive_off = disabled_report.get("是否读取涉密资料") is False
    n8n_off = disabled_report.get("是否触发n8n") is False
    wecom_off = disabled_report.get("是否企业微信真实发送") is False
    if summary:
        failed = int(summary.get("失败", 0) or 0)
        passed = int(summary.get("通过", 0) or 0)
    else:
        passed = sum(1 for value in linked_checks.values() if value is True)
        failed = sum(1 for value in linked_checks.values() if value is not True)
    status = "healthy" if disabled_ok and sensitive_off and n8n_off and wecom_off and failed == 0 and passed > 0 else "degraded"

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "office-work-system-status-summary",
        "所属系统": "02杰哥扩展系统/03本职工作系统",
        "汇总": {
            "状态": status,
            "材料类型数量": len(material_types),
            "材料类型": material_types,
            "草稿模板数量": disabled_report.get("草稿状态", {}).get("模板数量", 0),
            "R03预演通过数": passed,
            "R03预演失败数": failed,
            "正式输出状态": disabled_report.get("执行器状态", "未知"),
        },
        "安全边界": {
            "读取涉密资料": False,
            "生成正式文档": False,
            "覆盖正式文档": False,
            "自动外发": False,
            "自动上传": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
        },
    }

    output_json = output_dir / "office-work-system-status-summary-最新.json"
    output_md = output_dir / "本职工作系统状态摘要_最新.md"
    write_json(output_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    print(json.dumps({"状态": status, "输出": str(output_json), "摘要": str(output_md)}, ensure_ascii=False))
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
