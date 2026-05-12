# -*- coding: utf-8 -*-
"""
名称：生成内容处理系统状态摘要.py
作用：汇总内容素材索引、批处理计划、转换预演和真实转换禁用态，生成内容处理系统日常状态摘要。
触发方式：python 生成内容处理系统状态摘要.py
依赖：Python标准库；内容素材索引；内容批处理计划；内容转换预演；内容处理本地转换门禁报告；内容处理真实转换禁用态检查。
所属系统：02杰哥扩展系统/04内容处理系统
安全边界：只读取内容处理系统本地数据和日志；只写入03数据/06状态摘要；不执行真实转换；不触发n8n；不发送企业微信；不写旧系统；不接入税收业务。
创建/修改记录：2026-04-29 创建内容处理系统状态摘要生成脚本。
标识：content-processing-system-status-summary-generate
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


def count_items(data: Any, keys: list[str]) -> int:
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return len(value)
            if isinstance(value, int):
                return value
    return 0


def build_markdown(report: dict[str, Any]) -> str:
    summary = report["汇总"]
    return "\n".join(
        [
            "# 内容处理系统状态摘要",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{summary['状态']}",
            f"- 素材数量：{summary['素材数量']}",
            f"- 批处理任务数：{summary['批处理任务数']}",
            f"- 转换预演数：{summary['转换预演数']}",
            f"- 门禁失败脚本数：{summary['门禁失败脚本数']}",
            f"- 真实转换状态：{summary['真实转换状态']}",
            "",
            "## 安全边界",
            "",
            "- 当前只允许素材索引、计划生成、转换预演和门禁检查。",
            "- 真实转换、n8n触发、企业微信发送、旧系统写入均保持关闭。",
        ]
    ) + "\n"


def main() -> int:
    root = module_root()
    data_root = root / "03数据"
    output_dir = data_root / "06状态摘要"
    index_report = load_json(data_root / "02登记索引" / "内容素材索引_最新.json", {})
    plan_report = load_json(data_root / "03批处理计划" / "内容批处理计划_最新.json", {})
    preview_report = load_json(data_root / "04转换预演" / "内容转换预演_最新.json", {})
    gate_report = load_json(data_root / "05本地转换门禁" / "内容处理本地转换门禁报告_最新.json", {})
    disabled_report = load_json(data_root / "05本地转换门禁" / "内容处理真实转换禁用态检查_最新.json", {})

    scripts = gate_report.get("脚本执行", [])
    failed_scripts = [item for item in scripts if item.get("退出码") != 0]
    disabled_ok = disabled_report.get("执行器状态") == "禁用态" and disabled_report.get("是否执行真实转换") is False
    status = "healthy" if not failed_scripts and disabled_ok else "degraded"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "content-processing-system-status-summary",
        "所属系统": "02杰哥扩展系统/04内容处理系统",
        "汇总": {
            "状态": status,
            "素材数量": count_items(index_report, ["素材", "assets", "asset_count"]),
            "批处理任务数": count_items(plan_report, ["任务", "计划", "jobs", "task_count"]),
            "转换预演数": count_items(preview_report, ["预演", "previews", "preview_count"]),
            "门禁脚本数量": len(scripts),
            "门禁失败脚本数": len(failed_scripts),
            "真实转换状态": disabled_report.get("执行器状态", "未知"),
            "是否执行真实转换": disabled_report.get("是否执行真实转换"),
        },
        "安全边界": {
            "执行真实转换": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "接入税收": False,
        },
    }

    output_json = output_dir / "content-processing-system-status-summary-最新.json"
    output_md = output_dir / "内容处理系统状态摘要_最新.md"
    write_json(output_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    print(json.dumps({"状态": status, "输出": str(output_json), "摘要": str(output_md)}, ensure_ascii=False))
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
