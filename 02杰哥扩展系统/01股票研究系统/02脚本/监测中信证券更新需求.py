# -*- coding: utf-8 -*-
"""
名称：监测中信证券更新需求.py
作用：只读判断中信证券本机资料是否需要更新，并给出受控更新入口建议。
边界：默认只读；不登录券商；不调用券商接口；不交易；不自动启动更新器。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


CITIC_ROOT = Path(r"F:\股票工具\中信证券")
AUTO_UPDATE_EXE = CITIC_ROOT / "AutoUpEx.exe"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def latest_file_time(path: Path, pattern: str) -> str:
    if not path.exists():
        return ""
    latest = max((p.stat().st_mtime for p in path.glob(pattern) if p.is_file()), default=0)
    return datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M:%S") if latest else ""


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() and path.is_file() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 中信证券更新需求监测 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 结论：{report['结论']}",
        f"- 日线最新文件时间：{report['日线最新文件时间'] or '未提取'}",
        f"- 行情缓存更新时间：{report['行情缓存更新时间'] or '未提取'}",
        f"- 更新器存在：{report['更新器']['存在']}",
        "",
        "## 二、建议",
        "",
    ]
    for item in report["建议"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 默认只读监测。",
        "- 不登录券商。",
        "- 不调用券商接口。",
        "- 不交易。",
        "- 不自动启动更新器。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    sh = latest_file_time(CITIC_ROOT / "vipdoc" / "sh" / "lday", "*.day")
    sz = latest_file_time(CITIC_ROOT / "vipdoc" / "sz" / "lday", "*.day")
    bj = latest_file_time(CITIC_ROOT / "vipdoc" / "bj" / "lday", "*.day")
    latest_day = max([x for x in [sh, sz, bj] if x] or [""])
    hq_time = max([
        file_state(CITIC_ROOT / "T0002" / "hq_cache" / "base.dbf")["更新时间"],
        file_state(CITIC_ROOT / "connect.cfg")["更新时间"],
        file_state(CITIC_ROOT / "T0002" / "tmp" / "needautoup.dat")["更新时间"],
    ])
    today = now.strftime("%Y-%m-%d")
    day_is_today = latest_day.startswith(today)
    hq_is_today = hq_time.startswith(today)
    if day_is_today:
        conclusion = "中信日线文件今日已更新"
    elif hq_is_today:
        conclusion = "行情缓存今日活跃，但日线文件尚未更新"
    else:
        conclusion = "中信本机资料可能需要更新"
    suggestions = [
        "保持中信证券客户端运行，优先让软件自身完成行情和资料下载。",
        "若日线长期未更新，可在中信软件内执行数据下载/盘后数据下载，再由股票系统自动读取vipdoc。",
        "AutoUpEx.exe只作为受控更新入口候选，不默认自动执行，避免误改软件环境。",
        "股票系统继续用公开行情作为保底，避免中信日线滞后时主线停摆。",
    ]
    report = {
        "名称": "中信证券更新需求监测",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": conclusion,
        "日线最新文件时间": latest_day,
        "行情缓存更新时间": hq_time,
        "市场日线最新文件时间": {"sh": sh, "sz": sz, "bj": bj},
        "更新器": file_state(AUTO_UPDATE_EXE),
        "更新需求信号": file_state(CITIC_ROOT / "T0002" / "tmp" / "needautoup.dat"),
        "建议": suggestions,
        "安全边界": {
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否自动启动更新器": False,
            "是否交易": False,
        },
    }
    out_dir = module_root() / "03数据" / "288中信证券更新需求监测"
    stamp = now.strftime("%Y%m%d_%H%M%S")
    latest_json = out_dir / "中信证券更新需求监测_最新.json"
    latest_md = out_dir / "中信证券更新需求监测_最新.md"
    write_json(out_dir / f"中信证券更新需求监测_{stamp}.json", report)
    write_text(out_dir / f"中信证券更新需求监测_{stamp}.md", build_markdown(report))
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "结论": conclusion,
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
