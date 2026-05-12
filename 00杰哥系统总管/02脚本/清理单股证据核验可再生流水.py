# -*- coding: utf-8 -*-
"""
名称：清理单股证据核验可再生流水.py
作用：删除 190/192/193 单股证据核验链路中已由最新锚点承接的旧时间戳流水。
触发方式：python 清理单股证据核验可再生流水.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：仅处理 190/192/193 三个可再生目录；不处理 191 人工填写台账；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-05-06 创建单股证据核验可再生流水清理入口。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
STOCK_DATA = ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据"
OUT_DIR = MANAGER / "03数据" / "运行状态"
LOG_DIR = MANAGER / "04日志" / "清债执行"

TARGET_DIRS = [
    STOCK_DATA / "190单股证据核验工作包",
    STOCK_DATA / "192单股证据核验台账同步预览",
    STOCK_DATA / "193单股证据核验模板同步执行闸口",
]

TIMESTAMP_RE = re.compile(r"\d{8}[-_]\d{6}")


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00")


def is_deletable(path: Path) -> bool:
    if path.suffix.lower() not in {".json", ".md"}:
        return False
    name = path.name
    if "最新" in name or "latest" in name.lower():
        return False
    return bool(TIMESTAMP_RE.search(name))


def dir_state(directory: Path) -> dict[str, Any]:
    files = [item for item in directory.iterdir() if item.is_file()] if directory.exists() else []
    latest = [item for item in files if "最新" in item.name or "latest" in item.name.lower()]
    candidates = [item for item in files if is_deletable(item)]
    return {
        "目录": str(directory),
        "存在": directory.exists(),
        "文件数量": len(files),
        "最新锚点数量": len(latest),
        "候选数量": len(candidates),
        "候选": candidates,
    }


def safe_unlink(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    allowed = [directory.resolve() for directory in TARGET_DIRS]
    if not any(resolved.parent == directory for directory in allowed):
        raise RuntimeError(f"拒绝删除非目标目录文件：{resolved}")
    size = resolved.stat().st_size
    resolved.unlink()
    return {"路径": str(resolved), "字节": size}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 单股证据核验可再生流水清理",
        "",
        f"- 执行时间：{report['执行时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 删除数量：{report['删除数量']}",
        f"- 删除字节：{report['删除字节']}",
        "",
        "## 目录状态",
        "",
        "| 目录 | 最新锚点 | 删除候选 |",
        "|---|---:|---:|",
    ]
    for item in report["目录状态"]:
        lines.append(f"| `{item['目录']}` | {item['最新锚点数量']} | {item['候选数量']} |")
    lines.extend(["", "## 删除清单"])
    if report["删除文件"]:
        lines.extend([f"- `{item['路径']}`：{item['字节']} 字节" for item in report["删除文件"]])
    else:
        lines.append("- 无。")
    lines.extend([
        "",
        "## 保留边界",
        "- 191 单股证据核验人工填写台账不在本脚本处理范围内。",
        "- 三个目标目录内的 `最新` 锚点全部保留。",
        "- 只删除可再生工作包、同步预览、执行闸口的旧时间戳 `.json/.md` 流水。",
        "",
        "## 安全边界",
        "- 未触发 n8n；未发送企业微信；未调用券商接口；未自动交易；未写正式业务库。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    states = [dir_state(directory) for directory in TARGET_DIRS]
    failures = [item for item in states if not item["存在"] or item["最新锚点数量"] == 0]
    deleted: list[dict[str, Any]] = []
    if not failures:
        for state in states:
            for candidate in state["候选"]:
                deleted.append(safe_unlink(candidate))
    report = {
        "名称": "单股证据核验可再生流水清理",
        "执行时间": now_text(),
        "当前结论": "通过" if not failures else "未通过",
        "目录状态": [
            {key: value for key, value in item.items() if key != "候选"}
            for item in states
        ],
        "失败": failures,
        "删除数量": len(deleted),
        "删除字节": sum(item["字节"] for item in deleted),
        "删除文件": deleted,
        "安全边界": {
            "不处理191人工填写台账": True,
            "未触发n8n": True,
            "未发送企业微信": True,
            "未调用券商接口": True,
            "未自动交易": True,
            "未写正式业务库": True,
        },
    }
    json_text = json.dumps(report, ensure_ascii=False, indent=2)
    (OUT_DIR / "单股证据核验可再生流水清理_最新.json").write_text(json_text, encoding="utf-8")
    (LOG_DIR / "stock-single-evidence-regenerable-flow-cleanup-最新.json").write_text(json_text, encoding="utf-8")
    (OUT_DIR / "单股证据核验可再生流水清理_最新.md").write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "状态": report["当前结论"],
        "删除数量": report["删除数量"],
        "删除字节": report["删除字节"],
        "输出": str(OUT_DIR / "单股证据核验可再生流水清理_最新.md"),
    }, ensure_ascii=False))
    return 0 if report["当前结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
