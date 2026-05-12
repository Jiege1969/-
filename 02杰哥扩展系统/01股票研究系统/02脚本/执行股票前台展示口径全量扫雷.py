# -*- coding: utf-8 -*-
"""股票前台展示口径全量扫雷。

只扫描和最小修复前台展示层产物；不修改分析引擎、不修改评分逻辑、
不修改推荐名单生成逻辑、不接券商、不交易、不触发 n8n、不发送企业微信。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "246展示口径修复"
RESULT_JSON = OUT_DIR / "股票前台展示口径全量一致性扫雷_最新.json"
RESULT_MD = OUT_DIR / "股票前台展示口径全量一致性扫雷_最新.md"

FRONT_PRODUCT_DIRS = [
    DATA / "24企业微信短回复",
    DATA / "135分层日报",
    DATA / "185专家市场总览",
    DATA / "86图形报告",
]

TEXT_SUFFIXES = {".md", ".json", ".svg"}
RECOMMENDATION_TERMS = [
    "重点推荐",
    "常规推荐",
    "AI日报推荐/观察",
    "今日推荐",
    "每日推荐",
    "买入研究信号",
    "买入信号",
    "卖出研究信号",
    "卖出/退出研究信号",
    "当前进入重点研究",
    "上攻",
    "进攻",
]
RISK_TERMS = ["风险复核", "继续回避", "回避", "暂不建议关注", "离场观望"]
TRADE_LIKE_TERMS = ["买入", "卖出", "下单", "加仓", "减仓", "满仓", "清仓", "仓位"]


def is_front_product(path: Path) -> bool:
    name = path.name
    parent = path.parent.name
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    if parent == "24企业微信短回复":
        return name.startswith("企业微信") and path.suffix.lower() in {".md", ".json"}
    if parent == "135分层日报":
        return name.startswith(("单股标准报告v2_", "AI分析报告_")) and path.suffix.lower() in {".md", ".json"}
    if parent == "185专家市场总览":
        return path.suffix.lower() in {".md", ".json"}
    if parent == "86图形报告":
        return path.suffix.lower() in {".json", ".svg"}
    return False


def front_files() -> list[Path]:
    files: list[Path] = []
    for directory in FRONT_PRODUCT_DIRS:
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if path.is_file() and is_front_product(path):
                files.append(path)
    return sorted(files)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def sanitize_display_text(text: str) -> tuple[str, list[str]]:
    changed: list[str] = []
    safe = text
    replacements = [
        ("买入研究信号", "研究价值信号"),
        ("买入信号", "研究价值信号"),
        ("卖出/退出研究信号", "风险复核信号"),
        ("卖出研究信号", "风险复核信号"),
        ("卖出信号", "风险复核信号"),
        ("未形成明确买入或卖出研究信号", "未形成明确研究价值或风险复核信号"),
        ("未形成明确买入或风险复核信号", "未形成明确研究价值或风险复核信号"),
        ("AI日报推荐/观察", "AI日报研究/观察"),
        ("今日推荐", "今日研究摘要"),
        ("每日推荐", "每日研究摘要"),
        ("推荐数量", "展示数量"),
        ("重点推荐", "高研究价值"),
        ("常规推荐", "常规研究价值"),
        ("当前进入重点研究", "当前进入高研究价值观察"),
        ("上攻", "转强"),
        ("进攻", "转强"),
        ("操作策略：", "当前操作建议："),
        ("关注条件：", "观察条件："),
        ("图文详情：", "图文报告："),
    ]
    for old, new in replacements:
        if old in safe:
            safe = safe.replace(old, new)
            changed.append(f"{old}->{new}")

    new_safe = re.sub(r"重点关注(?!池)", "高研究价值", safe)
    if new_safe != safe:
        safe = new_safe
        changed.append("重点关注->高研究价值")

    new_safe = re.sub(r"(?<!不)(?<!未形成明确)买入", "研究价值", safe)
    if new_safe != safe:
        safe = new_safe
        changed.append("买入->研究价值")

    new_safe = re.sub(r"(?<!不)(?<!未形成明确)卖出", "风险复核", safe)
    if new_safe != safe:
        safe = new_safe
        changed.append("卖出->风险复核")

    safe = safe.replace("未形成明确买入或风险复核研究信号", "未形成明确研究价值或风险复核信号")
    return safe, changed


def hits(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term in text]


def trade_hits(text: str) -> list[str]:
    found: list[str] = []
    for term in TRADE_LIKE_TERMS:
        if term not in text:
            continue
        if term in {"买入", "卖出"}:
            allowed_markers = [
                f"不{term}",
                f"不得{term}",
                f"禁止{term}",
                f"未形成明确{term}",
            ]
            if any(marker in text for marker in allowed_markers):
                continue
        found.append(term)
    return found


def file_result(path: Path, before: str, after: str, changes: list[str]) -> dict[str, Any]:
    recommendation_hits = hits(after, RECOMMENDATION_TERMS)
    risk_hits = hits(after, RISK_TERMS)
    return {
        "路径": str(path),
        "已修复": bool(changes),
        "修复项": changes,
        "推荐关注买入进攻类残留": recommendation_hits,
        "风险回避类命中": risk_hits,
        "是否仍有冲突": bool(recommendation_hits and risk_hits),
        "交易化表达残留": trade_hits(after),
        "修改前字数": len(before),
        "修改后字数": len(after),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checked: list[dict[str, Any]] = []
    for path in front_files():
        before = read_text(path)
        after, changes = sanitize_display_text(before)
        if after != before:
            write_text(path, after)
        checked.append(file_result(path, before, after, changes))

    conflict_files = [item for item in checked if item["是否仍有冲突"]]
    trade_files = [item for item in checked if item["交易化表达残留"]]
    repaired_files = [item for item in checked if item["已修复"]]
    result = {
        "名称": "股票前台展示口径全量一致性扫雷",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查目录": [str(path) for path in FRONT_PRODUCT_DIRS],
        "检查文件数": len(checked),
        "修复文件数": len(repaired_files),
        "仍有冲突文件数": len(conflict_files),
        "交易化表达残留文件数": len(trade_files),
        "通过": not conflict_files and not trade_files,
        "修复文件": repaired_files,
        "冲突文件": conflict_files,
        "交易化表达残留文件": trade_files,
        "检查结果": checked,
        "安全边界": {
            "不接券商": True,
            "不交易": True,
            "不生成买卖指令": True,
            "不修改核心评分引擎": True,
            "不修改推荐名单生成逻辑": True,
            "不接n8n": True,
            "不改企业微信公共配置": True,
            "不真实发送企业微信": True,
        },
    }

    RESULT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票前台展示口径全量一致性扫雷",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 检查文件数：{result['检查文件数']}",
        f"- 修复文件数：{result['修复文件数']}",
        f"- 仍有冲突文件数：{result['仍有冲突文件数']}",
        f"- 交易化表达残留文件数：{result['交易化表达残留文件数']}",
        f"- 是否通过：{'是' if result['通过'] else '否'}",
        "",
        "## 修复文件",
        "",
    ]
    if repaired_files:
        for item in repaired_files:
            lines.append(f"- {item['路径']}：{'; '.join(item['修复项'])}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 未通过项", ""])
    if conflict_files or trade_files:
        for item in conflict_files:
            lines.append(f"- 口径冲突：{item['路径']} | {item['推荐关注买入进攻类残留']} + {item['风险回避类命中']}")
        for item in trade_files:
            lines.append(f"- 交易化表达残留：{item['路径']} | {item['交易化表达残留']}")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 未接券商；未交易；未生成买卖指令；未修改核心评分引擎；未修改推荐名单生成逻辑；未接 n8n；未改企业微信公共配置。",
    ])
    RESULT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
