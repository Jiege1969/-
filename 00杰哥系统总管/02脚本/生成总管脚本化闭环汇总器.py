# -*- coding: utf-8 -*-
"""
名称：生成总管脚本化闭环汇总器.py
作用：汇总当前施工面板、接续包、验收报告和清债收口报告，生成当前总管闭环状态。
触发方式：python 生成总管脚本化闭环汇总器.py
所属系统：00杰哥系统总管
安全边界：只读当前入口并写00总管最新报告；不写05备份；不触发n8n；不发送企业微信；不调用券商接口。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
DOC_DIR = MANAGER / "07文档"
REPORT_JSON = OUT_DIR / "总管脚本化闭环汇总器_最新.json"
REPORT_MD = OUT_DIR / "总管脚本化闭环汇总器_最新.md"
USAGE_MD = DOC_DIR / "总管脚本化闭环使用说明_20260505.md"
HANDOFF_MD = DOC_DIR / "总管脚本化闭环交接说明_20260505.md"

EVIDENCE_FILES = {
    "当前施工面板": MANAGER / "07文档" / "当前施工面板.md",
    "一键接续施工包": MANAGER / "03数据" / "开工上下文" / "一键接续施工包_最新.md",
    "开工上下文摘要": MANAGER / "03数据" / "开工上下文" / "开工上下文摘要_最新.md",
    "施工接续卡片": MANAGER / "03数据" / "施工接续" / "施工接续卡片_最新.md",
    "最新验收报告": MANAGER / "03数据" / "验收报告" / "验收报告_最新.md",
    "第34轮05备份收口报告": OUT_DIR / "摸清家底找差距第三十四轮05备份资产分层清债收口_最新.md",
    "清债原则": OUT_DIR / "摸清家底找差距清债原则_最新.md",
}


def read_text(path: Path, limit: int = 1200) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")[:limit]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def card(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
        "摘要": read_text(path, 600) if path.suffix.lower() in {".md", ".txt"} else "",
    }


def inventory(directory: Path, pattern: str = "*") -> dict[str, Any]:
    files = [p for p in directory.rglob(pattern) if p.is_file()]
    latest = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:12]
    return {
        "目录": str(directory),
        "文件数量": len(files),
        "总字节": sum(p.stat().st_size for p in files),
        "最新文件": [str(p) for p in latest],
    }


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    evidence = {name: card(path) for name, path in EVIDENCE_FILES.items()}
    missing = [name for name, item in evidence.items() if not item["存在"]]
    report = {
        "名称": "总管脚本化闭环汇总器",
        "生成时间": now,
        "结论": "通过" if not missing else "存在缺口",
        "当前口径": "摸清家底找差距清债进行中；当前入口只认施工面板、接续包、验收报告、施工接续卡片和最新收口报告。",
        "证据读取": evidence,
        "缺失证据": missing,
        "总管脚本盘点": inventory(MANAGER / "02脚本", "*.py"),
        "总管配置盘点": inventory(MANAGER / "01配置"),
        "总管运行状态盘点": inventory(OUT_DIR),
        "下一步优先级": [
            "继续第35轮旧施工脚本和旧验收器清债。",
            "证实无当前依赖、且会写旧备份/旧时间戳/旧进度口径的脚本直接删除。",
            "仍需兼容的旧入口只允许调用当前链路，不得再生成05备份或旧摘要。",
        ],
        "安全边界": {
            "写05备份": False,
            "触发n8n": False,
            "发送企业微信真实消息": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    lines = [
        "# 总管脚本化闭环汇总器",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        "- 当前口径：摸清家底找差距清债进行中，当前入口只认最新资产和最新验收链。",
        f"- 总管 Python 脚本数量：{report['总管脚本盘点']['文件数量']}",
        f"- 总管运行状态文件数量：{report['总管运行状态盘点']['文件数量']}",
        "",
        "## 证据读取",
        "",
    ]
    for name, item in evidence.items():
        status = "存在" if item["存在"] else "缺失"
        lines.append(f"- {name}：{status}。{item['路径']}")
    lines.extend(["", "## 下一步优先级", ""])
    for index, item in enumerate(report["下一步优先级"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 安全边界", "", "本轮只读汇总并写00总管报告；未写05备份，未触发 n8n，未发送企业微信，未调用券商接口，未自动交易。"])

    usage = f"""# 总管脚本化闭环使用说明

生成时间：{now}

## 使用顺序

1. 运行 `生成总管脚本化闭环汇总器.py`。
2. 运行 `生成一键接续施工包自动刷新.py`。
3. 运行 `验证总管脚本化闭环.py`。
4. 运行 `验证一键接续施工包.py`。
5. 运行 `读取开工上下文.py`。

## 安全边界

这些脚本只读取当前证据并写入00总管最新报告、接续包和上下文摘要；不得写05备份，不得触发 n8n、发送企业微信、调用券商接口或自动交易。
"""
    handoff = f"""# 总管脚本化闭环交接说明

生成时间：{now}

## 当前状态

总管闭环已切换到清债口径：只保留当前入口、当前验收链、清债原则和必要回滚资产，不再保留旧施工快照、旧归档包或旧进度摘要。

## 后续接手

继续第35轮旧施工脚本和旧验收器清债；凡证实无当前依赖且会写旧备份、旧时间戳或旧进度摘要的脚本，直接删除或改成兼容当前链路。
"""
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines))
    write_text(USAGE_MD, usage)
    write_text(HANDOFF_MD, handoff)
    print(json.dumps({"状态": report["结论"], "脚本数量": report["总管脚本盘点"]["文件数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if report["结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
