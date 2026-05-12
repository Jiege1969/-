# -*- coding: utf-8 -*-
"""
名称：清理知识库日志旧流水.py
作用：清理 01 智能系统 04日志/知识库 下已确认可再生、无当前依赖的旧时间戳日志。
安全边界：只删除 04日志/知识库 内旧时间戳 .json；保留“最新”锚点；不触发 n8n；不发送企业微信；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
LOG_DIR = SYSTEM_ROOT / "01杰哥智能系统" / "04日志" / "知识库"
STATUS_DIR = SYSTEM_ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
TS_RE = re.compile(r"\d{8}[-_]\d{4,6}|\d{8}_\d{6}")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def classify(path: Path) -> str:
    return TS_RE.sub("<ts>", path.name)


def main() -> int:
    if not LOG_DIR.exists():
        report = {
            "名称": "知识库日志旧流水清理",
            "执行时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00"),
            "当前结论": "未通过",
            "失败": [f"目录不存在：{LOG_DIR}"],
        }
        write_json(STATUS_DIR / "知识库日志旧流水清理_最新.json", report)
        return 1

    files = [item for item in LOG_DIR.iterdir() if item.is_file()]
    latest_files = [item for item in files if "最新" in item.name]
    candidates = [
        item
        for item in files
        if item.suffix.lower() == ".json"
        and "最新" not in item.name
        and TS_RE.search(item.name)
    ]

    pattern_summary: dict[str, dict[str, Any]] = {}
    for item in files:
        key = classify(item)
        entry = pattern_summary.setdefault(
            key,
            {"模式": key, "文件数": 0, "最新锚点": 0, "旧时间戳": 0, "字节": 0},
        )
        entry["文件数"] += 1
        entry["字节"] += item.stat().st_size
        if "最新" in item.name:
            entry["最新锚点"] += 1
        if TS_RE.search(item.name):
            entry["旧时间戳"] += 1

    deleted: list[dict[str, Any]] = []
    failures: list[str] = []
    for item in sorted(candidates, key=lambda p: p.name):
        size = item.stat().st_size
        try:
            item.unlink()
            deleted.append({"路径": str(item), "字节": size, "模式": classify(item)})
        except OSError as exc:
            failures.append(f"{item}: {exc}")

    remaining_files = [item for item in LOG_DIR.iterdir() if item.is_file()]
    remaining_timestamps = [
        item
        for item in remaining_files
        if item.suffix.lower() == ".json"
        and "最新" not in item.name
        and TS_RE.search(item.name)
    ]

    report = {
        "名称": "知识库日志旧流水清理",
        "执行时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00"),
        "当前结论": "通过" if not failures and not remaining_timestamps else "未通过",
        "目标目录": str(LOG_DIR),
        "清理前文件数": len(files),
        "清理前最新锚点": len(latest_files),
        "候选旧时间戳": len(candidates),
        "删除数量": len(deleted),
        "删除字节": sum(item["字节"] for item in deleted),
        "剩余旧时间戳": len(remaining_timestamps),
        "模式汇总": sorted(pattern_summary.values(), key=lambda item: (-item["旧时间戳"], item["模式"])),
        "删除文件": deleted,
        "失败": failures,
        "保留原则": [
            "保留固定最新锚点",
            "保留正式数据、正式扩容执行报告、备份目录和不可再生资产",
            "删除 04日志/知识库 内无当前依赖的可再生旧验收日志",
        ],
        "安全边界": {
            "未触发n8n": True,
            "未发送企业微信": True,
            "未调用券商接口": True,
            "未自动交易": True,
            "未删除正式知识库数据": True,
        },
    }

    md_lines = [
        "# 知识库日志旧流水清理",
        "",
        f"- 执行时间：{report['执行时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 目标目录：`{LOG_DIR}`",
        f"- 清理前文件数：{report['清理前文件数']}",
        f"- 清理前最新锚点：{report['清理前最新锚点']}",
        f"- 候选旧时间戳：{report['候选旧时间戳']}",
        f"- 删除数量：{report['删除数量']}",
        f"- 删除字节：{report['删除字节']}",
        f"- 剩余旧时间戳：{report['剩余旧时间戳']}",
        "",
        "## 模式汇总",
        "",
    ]
    for entry in report["模式汇总"]:
        md_lines.append(
            f"- `{entry['模式']}`：文件 {entry['文件数']}，最新 {entry['最新锚点']}，旧时间戳 {entry['旧时间戳']}，字节 {entry['字节']}"
        )
    md_lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 未触发 n8n。",
            "- 未发送企业微信。",
            "- 未调用券商接口。",
            "- 未自动交易。",
            "- 未删除正式知识库数据、正式扩容执行报告、备份目录或不可再生资产。",
        ]
    )

    write_json(STATUS_DIR / "知识库日志旧流水清理_最新.json", report)
    write_text(STATUS_DIR / "知识库日志旧流水清理_最新.md", "\n".join(md_lines) + "\n")
    print(json.dumps({"状态": report["当前结论"], "删除数量": report["删除数量"], "剩余旧时间戳": report["剩余旧时间戳"]}, ensure_ascii=False))
    return 0 if report["当前结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
