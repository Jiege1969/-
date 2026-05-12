# -*- coding: utf-8 -*-
"""
名称：生成视频制作系统状态摘要.py
作用：汇总视频素材候选、分镜素材匹配、主题化预演和真实渲染禁用态，生成视频制作系统日常状态摘要。
触发方式：python 生成视频制作系统状态摘要.py
依赖：Python标准库；视频素材候选；视频分镜素材匹配；视频主题化预演；视频素材本地整理门禁报告；视频真实渲染禁用态检查。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只读取视频制作系统本地数据和日志；只写入03数据/09状态摘要；不调用剪辑软件；不执行真实渲染；不触发n8n；不发送企业微信；不写旧系统。
创建/修改记录：2026-04-29 创建视频制作系统状态摘要生成脚本。
标识：video-production-system-status-summary-generate
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
            "# 视频制作系统状态摘要",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 总体状态：{summary['状态']}",
            f"- 素材候选数：{summary['素材候选数']}",
            f"- 主题方案数：{summary['主题方案数']}",
            f"- 字幕要点数：{summary['字幕要点数']}",
            f"- 门禁失败脚本数：{summary['门禁失败脚本数']}",
            f"- 真实渲染状态：{summary['真实渲染状态']}",
            "",
            "## 安全边界",
            "",
            "- 当前只允许素材候选、分镜匹配、主题化预演和门禁检查。",
            "- 剪辑软件调用、真实渲染、n8n触发、企业微信发送、旧系统写入均保持关闭。",
        ]
    ) + "\n"


def main() -> int:
    root = module_root()
    data_root = root / "03数据"
    output_dir = data_root / "09状态摘要"
    candidate_report = load_json(data_root / "05素材候选" / "视频素材候选_最新.json", {})
    match_report = load_json(data_root / "06分镜素材匹配" / "视频分镜素材匹配_最新.json", {})
    theme_report = load_json(data_root / "07主题化预演" / "视频主题化预演_最新.json", {})
    gate_report = load_json(data_root / "08本地整理门禁" / "视频素材本地整理门禁报告_最新.json", {})
    disabled_report = load_json(data_root / "08本地整理门禁" / "视频真实渲染禁用态检查_最新.json", {})

    scripts = gate_report.get("脚本执行", [])
    failed_scripts = [item for item in scripts if item.get("退出码") != 0]
    disabled_ok = disabled_report.get("执行器状态") == "禁用态" and disabled_report.get("是否调用剪辑软件") is False
    status = "healthy" if not failed_scripts and disabled_ok else "degraded"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "video-production-system-status-summary",
        "所属系统": "02杰哥扩展系统/02视频制作系统",
        "汇总": {
            "状态": status,
            "素材候选数": count_items(candidate_report, ["素材候选", "候选", "candidates", "candidate_count"]),
            "分镜素材匹配数": count_items(match_report, ["匹配", "matches", "match_count"]),
            "主题方案数": count_items(theme_report, ["主题方案", "主题方案数量"]),
            "字幕要点数": count_items(theme_report, ["字幕要点", "字幕要点数量"]),
            "门禁脚本数量": len(scripts),
            "门禁失败脚本数": len(failed_scripts),
            "真实渲染状态": disabled_report.get("执行器状态", "未知"),
            "是否调用剪辑软件": disabled_report.get("是否调用剪辑软件"),
        },
        "安全边界": {
            "调用剪辑软件": False,
            "执行真实渲染": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "接入交易": False,
        },
    }

    output_json = output_dir / "video-production-system-status-summary-最新.json"
    output_md = output_dir / "视频制作系统状态摘要_最新.md"
    write_json(output_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    print(json.dumps({"状态": status, "输出": str(output_json), "摘要": str(output_md)}, ensure_ascii=False))
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
