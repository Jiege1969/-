# -*- coding: utf-8 -*-
"""
名称：生成股票系统真实发送入口清点报告.py
作用：清点股票系统中与企业微信真实发送相关的脚本和05入口工具，确认真实发送路径已收口到专用复测控制器。
触发方式：python 生成股票系统真实发送入口清点报告.py
依赖：02脚本目录、05入口工具BAT入口。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地脚本和05入口工具BAT；只写03数据/160真实发送入口清点；不调用企业微信API；不真实发送企业微信；不触发n8n；不调用券商接口；不自动交易。
标识：stock-real-send-entry-inventory
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


PATTERNS = ["--real-send", "--real-wecom", "真实发送", "企业微信真实", "企微真实"]
APPROVED_CONTROLLER = "股票系统企微真实推送复测控制器.py"
APPROVED_ENTRY = "股票系统企微真实推送复测_确认可信IP后真实发送.bat"
SAFE_JUMP_ENTRY = "股票系统交付控制台_企微真实复测_需先加可信IP.bat"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return ""


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def hit_lines(path: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for idx, line in enumerate(read_text(path).splitlines(), start=1):
        if any(pattern in line for pattern in PATTERNS):
            hits.append({"行号": idx, "内容": line.strip()[:240]})
    return hits


def classify_script(path: Path, hits: list[dict[str, Any]]) -> str:
    name = path.name
    text = read_text(path)
    if name == APPROVED_CONTROLLER:
        return "专用真实复测控制器"
    if "验证" in name or "生成" in name or "禁用态" in name or "模拟" in name:
        return "本地报告/验收/禁用态相关"
    if "--real-send" in text or "--real-wecom" in text:
        return "具备显式真实发送参数的历史/专项脚本"
    if hits:
        return "含真实发送表述"
    return "无"


def classify_bat(path: Path, hits: list[dict[str, Any]]) -> str:
    name = path.name
    text = read_text(path)
    if name == APPROVED_ENTRY and APPROVED_CONTROLLER in text and "choice /M" in text:
        return "当前专用真实复测入口，含二次确认"
    if name == SAFE_JUMP_ENTRY and APPROVED_ENTRY in text:
        return "旧入口安全跳转，不直接真实发送"
    if APPROVED_CONTROLLER in text and "--real-send" in text:
        return "调用专用控制器"
    if "--real-send" in text or "--real-wecom" in text:
        return "需复核：入口工具BAT含真实发送参数"
    if hits:
        return "含真实发送表述"
    return "无"


def scan_scripts(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((root / "02脚本").glob("*.py")):
        hits = hit_lines(path)
        if not hits:
            continue
        rows.append({
            "文件": str(path),
            "文件名": path.name,
            "类型": "python脚本",
            "分类": classify_script(path, hits),
            "命中数量": len(hits),
            "命中行": hits[:20],
        })
    return rows


def scan_entry_bats(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    entry_dir = root / "05入口工具"
    for path in sorted(entry_dir.glob("股票系统*.bat")):
        hits = hit_lines(path)
        if not hits:
            continue
        rows.append({
            "文件": str(path),
            "文件名": path.name,
            "类型": "入口工具BAT",
            "分类": classify_bat(path, hits),
            "命中数量": len(hits),
            "命中行": hits[:20],
        })
    return rows


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统真实发送入口清点报告 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 当前结论：{report['清点结论']}",
        f"- 入口工具真实发送风险入口数量：{report['统计']['入口工具需复核入口数']}",
        f"- 专用真实复测入口：`{report['专用真实复测入口']}`",
        f"- 旧入口安全跳转：`{report['旧入口安全跳转']}`",
        "",
        "## 二、05入口工具BAT入口",
        "",
    ]
    for item in report["入口工具BAT入口"]:
        lines.append(f"- {item['文件名']}：{item['分类']}，命中{item['命中数量']}处")
    lines.extend(["", "## 三、脚本命中概览", ""])
    for item in report["脚本入口"]:
        lines.append(f"- {item['文件名']}：{item['分类']}，命中{item['命中数量']}处")
    lines.extend([
        "",
        "## 四、安全边界",
        "",
        "- 本报告只扫描本地文件。",
        "- 不调用企业微信API。",
        "- 不真实发送企业微信。",
        "- 不触发n8n。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(root: Path, script_path: Path, target: Path) -> Path:
    bat = root / "05入口工具" / "股票系统真实发送入口清点报告_打开.bat"
    write_text(bat, (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'python "{script_path}"\r\n'
        f'start "" "{target}"\r\n'
    ))
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()

    script_rows = scan_scripts(root)
    bat_rows = scan_entry_bats(root)
    entry_review = [
        item for item in bat_rows
        if item["分类"] == "需复核：入口工具BAT含真实发送参数"
    ]
    approved_ok = any(item["文件名"] == APPROVED_ENTRY and "二次确认" in item["分类"] for item in bat_rows)
    safe_jump_ok = any(item["文件名"] == SAFE_JUMP_ENTRY and "安全跳转" in item["分类"] for item in bat_rows)

    if entry_review:
        conclusion = "需复核：仍存在05入口工具BAT直接含真实发送参数"
    elif approved_ok and safe_jump_ok:
        conclusion = "通过：05入口工具真实发送路径已收口到专用控制器，旧入口为安全跳转"
    else:
        conclusion = "待复核：专用入口或旧入口安全跳转状态不完整"

    report = {
        "名称": "股票系统真实发送入口清点报告",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统真实发送入口清点报告.py",
        "清点结论": conclusion,
        "专用真实复测入口": str(root / "05入口工具" / APPROVED_ENTRY),
        "旧入口安全跳转": str(root / "05入口工具" / SAFE_JUMP_ENTRY),
        "统计": {
            "脚本命中数": len(script_rows),
            "入口工具BAT命中数": len(bat_rows),
            "入口工具需复核入口数": len(entry_review),
        },
        "入口工具BAT入口": bat_rows,
        "脚本入口": script_rows,
        "安全边界": {
            "是否调用企业微信API": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "160真实发送入口清点"
    latest_json = output_dir / "股票系统真实发送入口清点报告_最新.json"
    latest_md = output_dir / "股票系统真实发送入口清点报告_最新.md"
    markdown = build_markdown(report)
    write_json(latest_json, report)
    write_text(latest_md, markdown)
    bat = write_entry_open_bat(root, root / "02脚本" / "生成股票系统真实发送入口清点报告.py", latest_md)

    print(json.dumps({
        "状态": "完成",
        "清点结论": conclusion,
        "入口工具需复核入口数": len(entry_review),
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
