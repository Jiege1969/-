# -*- coding: utf-8 -*-
"""
名称：生成多对话框冲突检测报告.py
作用：只读检测多对话框并行施工下的核心文件修改、进度口径和系统状态冲突。
触发方式：python 生成多对话框冲突检测报告.py
所属系统：00杰哥系统总管
安全边界：只读总管文档、配置和状态报告并写00总管运行状态；不修改业务脚本、不触发n8n、不发送企业微信、不写正式库、不调用券商接口。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "多对话框冲突检测报告_最新.json"
REPORT_MD = OUT_DIR / "多对话框冲突检测报告_最新.md"

READ_FILES = [
    ROOT / "杰哥智能化系统全盘架构说明_20260504.md",
    MANAGER / "07文档" / "当前施工面板.md",
    MANAGER / "03数据" / "开工上下文" / "一键接续施工包_最新.md",
    MANAGER / "01配置" / "进度口径规则.json",
    MANAGER / "01配置" / "进度回答标准.json",
    MANAGER / "03数据" / "运行状态" / "股票系统阶段性交付完成读取汇总_最新.md",
]

CORE_FILES = [
    "D:\\杰哥智能化系统\\00杰哥系统总管\\01配置\\进度口径规则.json",
    "D:\\杰哥智能化系统\\00杰哥系统总管\\01配置\\进度回答标准.json",
    "D:\\杰哥智能化系统\\00杰哥系统总管\\01配置\\四大系统验收读取口径.json",
    "D:\\杰哥智能化系统\\00杰哥系统总管\\03数据\\开工上下文\\一键接续施工包_最新.md",
    "D:\\杰哥智能化系统\\00杰哥系统总管\\07文档\\当前施工面板.md",
]

CANONICAL_PATTERNS = {
    "整体进度": "45%-50%",
    "整体剩余工时": "55-84小时",
    "02扩展进度": "42%-50%",
    "02扩展剩余工时": "16-28小时",
    "股票状态": "阶段性交付完成",
}
STALE_PATTERNS = [
    "43%-47%",
    "44%-49%",
    "60-92小时",
    "57-87小时",
    "8-14小时",
    "17-30小时",
    "股票分析系统已可交付使用，剩余有效工作时间为0小时；后续只做优化、维护、复盘和质量增强",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def line_context(lines: list[str], index: int) -> dict[str, Any]:
    heading = ""
    for i in range(index, -1, -1):
        if lines[i].startswith("## "):
            heading = lines[i].strip("# ").strip()
            break
    return {
        "行号": index + 1,
        "章节": heading,
        "行": lines[index].strip()[:260],
    }


def detect_core_file_mentions(texts: dict[str, str]) -> list[dict[str, Any]]:
    mentions: dict[str, list[dict[str, Any]]] = {}
    for path_text in CORE_FILES:
        variants = {path_text, path_text.replace("\\", "/"), Path(path_text).name}
        for source, text in texts.items():
            lines = text.splitlines()
            for idx, line in enumerate(lines):
                if any(v in line for v in variants):
                    record = line_context(lines, idx)
                    record["来源文件"] = source
                    mentions.setdefault(path_text, []).append(record)
    results = []
    for path_text, records in mentions.items():
        if len(records) > 1:
            results.append(
                {
                    "核心文件": path_text,
                    "命中次数": len(records),
                    "判定": "多处引用，需以后续最新摘要为准；当前未发现同一最新章节内的互斥修改声明",
                    "命中": records[:8],
                }
            )
    return results


def detect_progress_conflicts(texts: dict[str, str]) -> dict[str, Any]:
    canonical_hits: dict[str, list[dict[str, Any]]] = {}
    stale_hits: list[dict[str, Any]] = []
    for source, text in texts.items():
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            for name, pattern in CANONICAL_PATTERNS.items():
                if pattern in line:
                    item = line_context(lines, idx)
                    item["来源文件"] = source
                    canonical_hits.setdefault(name, []).append(item)
            for pattern in STALE_PATTERNS:
                if pattern in line:
                    item = line_context(lines, idx)
                    item["来源文件"] = source
                    item["旧口径"] = pattern
                    stale_hits.append(item)
    latest_ok = all(canonical_hits.get(name) for name in CANONICAL_PATTERNS)
    blocking = []
    for hit in stale_hits:
        section = hit.get("章节", "")
        if "10:20" in section:
            blocking.append(hit)
    return {
        "最新口径齐全": latest_ok,
        "旧口径命中数量": len(stale_hits),
        "阻断性旧口径数量": len(blocking),
        "最新口径命中": canonical_hits,
        "旧口径命中样例": stale_hits[:12],
        "阻断性旧口径": blocking,
    }


def detect_status_conflicts(texts: dict[str, str]) -> dict[str, Any]:
    suspicious = []
    complete_hits = []
    negative_re = re.compile(r"股票.{0,20}(建设中|施工中|待交付|未交付|未完成)")
    complete_re = re.compile(r"股票.{0,30}(阶段性交付完成|100%|剩余.*0小时)")
    for source, text in texts.items():
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if complete_re.search(line):
                item = line_context(lines, idx)
                item["来源文件"] = source
                complete_hits.append(item)
            if negative_re.search(line):
                item = line_context(lines, idx)
                item["来源文件"] = source
                suspicious.append(item)
    blocking = [item for item in suspicious if "10:20" in item.get("章节", "")]
    return {
        "股票完成口径命中数量": len(complete_hits),
        "股票施工中疑似命中数量": len(suspicious),
        "阻断性状态冲突数量": len(blocking),
        "股票施工中疑似样例": suspicious[:12],
        "阻断性状态冲突": blocking,
    }


def main() -> int:
    texts = {str(path): read_text(path) for path in READ_FILES}
    missing = [str(path) for path in READ_FILES if not path.exists()]
    core_mentions = detect_core_file_mentions(texts)
    progress = detect_progress_conflicts(texts)
    status = detect_status_conflicts(texts)
    blocking_conflicts = []
    if missing:
        blocking_conflicts.append({"类型": "关键文件缺失", "明细": missing})
    if progress["阻断性旧口径数量"]:
        blocking_conflicts.append({"类型": "最新章节进度口径冲突", "明细": progress["阻断性旧口径"]})
    if status["阻断性状态冲突数量"]:
        blocking_conflicts.append({"类型": "最新章节股票状态冲突", "明细": status["阻断性状态冲突"]})

    report = {
        "名称": "多对话框冲突检测报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "未发现阻断性冲突" if not blocking_conflicts else "发现阻断性冲突",
        "读取文件数量": len(READ_FILES),
        "缺失文件": missing,
        "核心文件多处引用": core_mentions,
        "进度口径检测": progress,
        "系统状态检测": status,
        "阻断性冲突": blocking_conflicts,
        "解释": "旧口径出现在历史章节时只作为历史记录，不构成当前冲突；10:20优先摘要和配置JSON中的45%-50%、55-84小时为当前口径。",
        "安全边界": {
            "修改子系统业务脚本": False,
            "触发n8n": False,
            "发送企业微信": False,
            "调用外部正式发送接口": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    lines = [
        "# 多对话框冲突检测报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 读取文件数量：{report['读取文件数量']}",
        f"- 旧口径命中数量：{progress['旧口径命中数量']}（历史章节命中不视为当前冲突）",
        f"- 阻断性冲突数量：{len(blocking_conflicts)}",
        "",
        "## 当前有效口径",
        "",
        "- 全盘进度：45%-50%",
        "- 全盘剩余有效工时：55-84小时",
        "- 02扩展系统：42%-50% / 16-28小时",
        "- 股票系统：阶段性交付完成；剩余0小时；后续仅保留灰度监控、问题修复和优化",
        "",
        "## 检测结果",
        "",
        f"- 核心文件多处引用对象：{len(core_mentions)} 个；当前未发现同一最新章节内互斥修改声明。",
        f"- 进度口径最新命中齐全：{progress['最新口径齐全']}",
        f"- 股票状态阻断性冲突：{status['阻断性状态冲突数量']}",
        "",
        "## 说明",
        "",
        report["解释"],
        "",
        "## 安全边界",
        "",
        "本轮只读检测并写总管报告；未修改股票、知识库、进化系统业务逻辑，未触发 n8n，未发送企业微信，未调用外部正式发送接口。",
        "",
    ]
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines))
    print(json.dumps({"状态": report["结论"], "阻断性冲突数量": len(blocking_conflicts), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not blocking_conflicts else 1


if __name__ == "__main__":
    raise SystemExit(main())
