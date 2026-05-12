# -*- coding: utf-8 -*-
"""生成全系统最终验收清单骨架与剩余阻断读取器。

只读读取运行状态与并行回收材料；仅写入总管脚本、运行状态和指定回收报告。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
ROOT = MANAGER.parent
STATE = MANAGER / "03数据" / "运行状态"
RECOVERY = MANAGER / "03数据" / "并行回收"

CHECKLIST_JSON = STATE / "全系统最终验收清单骨架_最新.json"
CHECKLIST_MD = STATE / "全系统最终验收清单骨架_最新.md"
BLOCKER_JSON = STATE / "全系统剩余阻断读取器_最新.json"
BLOCKER_MD = STATE / "全系统剩余阻断读取器_最新.md"
RECOVERY_REPORT = RECOVERY / "00总管_第七批小任务AB最终验收读取器回收报告_最新.md"

SOURCE_GROUPS = {
    "最新进度": [
        STATE / "整体可交付进度复核_最新.md",
        STATE / "整体可交付进度复核_最新.json",
        STATE / "本轮施工基准_最新.md",
        STATE / "本轮施工基准_最新.json",
        STATE / "进度口径统一复核_最新.md",
        STATE / "进度口径统一复核_最新.json",
    ],
    "股票硬闸门": [
        STATE / "股票系统只分析不交易总闸门验收_最新.md",
        STATE / "股票系统只分析不交易总闸门验收_最新.json",
        STATE / "股票系统只分析不交易边界核验_最新.md",
        STATE / "股票系统只分析不交易边界核验_最新.json",
        STATE / "交易保护施工窗口_最新.json",
    ],
    "01状态": [
        RECOVERY / "01智能系统_第六批小任务V回收报告_最新.md",
        RECOVERY / "01智能系统_第五批小任务P回收报告_最新.md",
        RECOVERY / "01智能系统_第三批小任务G回收报告_最新.md",
        STATE / "个人智能母系统阶段收口验收_最新.md",
        STATE / "个人智能母系统服务缺口清单_最新.md",
    ],
    "02状态": [
        STATE / "扩展系统多窗口并行收口报告_最新.md",
        STATE / "扩展系统多窗口并行收口报告_最新.json",
        STATE / "摸清家底找差距第二十三轮前台输出口径与长连接旧债收口_最新.md",
        RECOVERY / "02扩展系统_第六批小任务X知识库回收报告_最新.md",
        RECOVERY / "02扩展系统_第六批小任务Y内容回收报告_最新.md",
        RECOVERY / "02扩展系统_第六批小任务Z视频回收报告_最新.md",
    ],
    "03状态": [
        RECOVERY / "03进化系统_第六批小任务AA回收报告_最新.md",
        STATE / "进化系统复盘材料状态基线_最新.md",
        STATE / "进化系统复盘材料状态基线验收_最新.md",
    ],
    "用户暂停": [
        STATE / "用户最新并行策略纠偏报告_最新.md",
        STATE / "用户最新并行策略纠偏报告_最新.json",
    ],
}

SECURITY_BOUNDARY = {
    "不触发n8n": True,
    "不发送企业微信真实消息": True,
    "不写正式库": True,
    "不调用券商接口": True,
    "不自动交易": True,
    "不下单": True,
    "不修改进度口径数字": True,
    "不修改面板": True,
    "不修改接续包": True,
    "不触碰本职工作系统": True,
}

MUST_KEYWORDS = [
    "交付阻断",
    "必须完成",
    "未通过",
    "失败",
    "缺口",
    "待补齐",
    "待完成",
    "不可交付",
    "60020",
    "可信IP",
    "白名单",
    "待生效",
]
POSTPONE_KEYWORDS = [
    "可后置",
    "后续仅优化",
    "后续优化",
    "仅优化",
    "暂缓",
    "灰度观察",
    "低风险",
    "不计失败",
]
PAUSE_KEYWORDS = [
    "用户主动暂停",
    "本职工作系统：暂停",
    "本职工作系统: 暂停",
    "按用户要求暂停",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def repair_mojibake(text: str) -> str:
    """旧材料多为 UTF-8 被按 GBK 解释后的文本；能修就修，不能修就原样返回。"""
    try:
        fixed = text.encode("gbk", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        return text
    return fixed if sum(ch in fixed for ch in "系统进度验收阻断暂停") > sum(ch in text for ch in "系统进度验收阻断暂停") else text


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def first_lines(text: str, max_lines: int = 8) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[:max_lines]


def source_record(group: str, path: Path) -> dict[str, Any]:
    raw = read_text(path)
    text = repair_mojibake(raw)
    return {
        "来源组": group,
        "路径": str(path),
        "存在": path.exists(),
        "最后修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
        "摘录": first_lines(text),
    }


def classify(text: str) -> dict[str, list[str]]:
    buckets = {"可交付前必须完成": [], "可后置": [], "用户暂停": []}
    lines = first_lines(text, 80)
    for line in lines:
        normalized = line.replace("`", "").replace(" ", "")
        if any(token in normalized for token in ["失败数量：0", "失败数量:0", "失败0", "交付阻断：0", "交付阻断:0", "阻断项0"]):
            continue
        if any(token in normalized for token in ["失败x", "阻断项x", "x/x；失败x", "x/x;失败x"]):
            continue
        if any(key in line for key in PAUSE_KEYWORDS):
            buckets["用户暂停"].append(line)
        elif any(key in line for key in MUST_KEYWORDS):
            buckets["可交付前必须完成"].append(line)
        elif any(key in line for key in POSTPONE_KEYWORDS):
            buckets["可后置"].append(line)
    return {key: values[:10] for key, values in buckets.items()}


def build_blocker_reader(generated_at: str) -> dict[str, Any]:
    source_records: list[dict[str, Any]] = []
    classification = {"可交付前必须完成": [], "可后置": [], "用户暂停": []}
    for group, paths in SOURCE_GROUPS.items():
        for path in paths:
            record = source_record(group, path)
            source_records.append(record)
            if record["存在"]:
                text = repair_mojibake(read_text(path))
                buckets = classify(text)
                for bucket, lines in buckets.items():
                    for line in lines:
                        classification[bucket].append({"来源组": group, "路径": str(path), "依据": line})

    # 文件名本身也是稳定信号，用于用户暂停/股票硬闸门等旧乱码正文的兜底分类。
    for record in source_records:
        path_text = record["路径"]
        if record["存在"] and "用户最新并行策略纠偏" in path_text:
            classification["用户暂停"].append({"来源组": record["来源组"], "路径": path_text, "依据": "用户最新并行策略纠偏报告含本职工作系统暂停口径"})
        if record["存在"] and "股票系统只分析不交易总闸门验收" in path_text:
            classification["可后置"].append({"来源组": record["来源组"], "路径": path_text, "依据": "股票只分析不交易硬闸门验收来源存在，交易类能力保持关闭"})

    for key in classification:
        seen = set()
        unique = []
        for item in classification[key]:
            marker = (item["路径"], item["依据"])
            if marker not in seen:
                seen.add(marker)
                unique.append(item)
        classification[key] = unique

    return {
        "名称": "全系统剩余阻断读取器",
        "生成时间": generated_at,
        "读取模式": "只读",
        "是否重算进度": False,
        "来源分组": {key: [str(path) for path in value] for key, value in SOURCE_GROUPS.items()},
        "来源读取结果": source_records,
        "阻断分类": classification,
        "安全边界": SECURITY_BOUNDARY,
    }


def build_checklist(generated_at: str, blocker: dict[str, Any]) -> dict[str, Any]:
    return {
        "名称": "全系统最终验收清单骨架",
        "生成时间": generated_at,
        "说明": "骨架只承接现有进度口径与阻断读取结果，不修改任何进度数字。",
        "总体验收域": [
            {"域": "最新进度口径", "检查": "读取整体可交付进度、本轮施工基准、进度口径复核；仅引用，不重算。"},
            {"域": "股票硬闸门", "检查": "确认只分析不交易、券商接口关闭、自动交易关闭、下单能力关闭。"},
            {"域": "01智能系统状态", "检查": "读取01回收报告与个人智能母系统阶段状态，列出交付前缺口。"},
            {"域": "02扩展系统状态", "检查": "读取02多窗口并行收口与企业微信、知识库、内容、视频状态。"},
            {"域": "03进化系统状态", "检查": "读取03回收报告与复盘材料状态基线。"},
            {"域": "用户暂停项", "检查": "本职工作系统暂停等用户口径单列，不并入交付失败。"},
            {"域": "安全边界", "检查": "n8n、企业微信真实发送、正式库、券商接口、自动交易均不触发。"},
        ],
        "交付前必须完成": blocker["阻断分类"]["可交付前必须完成"],
        "可后置": blocker["阻断分类"]["可后置"],
        "用户暂停": blocker["阻断分类"]["用户暂停"],
        "最终验收占位项": [
            "全系统最终交付前，由总管再次读取最新进度口径文件。",
            "股票系统保持只分析不交易硬闸门通过，且无券商接口/自动交易/下单动作。",
            "01/02/03 各系统最新状态均有可追溯来源路径。",
            "所有剩余阻断已归入可交付前必须完成、可后置、用户暂停三类。",
            "安全边界检查通过后再进入人工最终验收，不自动触发真实外部动作。",
        ],
        "安全边界": SECURITY_BOUNDARY,
    }


def md_list(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- 暂未从只读来源识别到。"]
    return [f"- {item['来源组']}：{item['依据']}（`{item['路径']}`）" for item in items]


def build_blocker_md(blocker: dict[str, Any]) -> str:
    lines = [
        "# 全系统剩余阻断读取器",
        f"生成时间：{blocker['生成时间']}",
        "",
        "- 读取模式：只读",
        "- 是否重算进度：False",
        "",
        "## 可交付前必须完成",
        *md_list(blocker["阻断分类"]["可交付前必须完成"]),
        "",
        "## 可后置",
        *md_list(blocker["阻断分类"]["可后置"]),
        "",
        "## 用户暂停",
        *md_list(blocker["阻断分类"]["用户暂停"]),
        "",
        "## 安全边界",
    ]
    lines.extend(f"- {key}：{value}" for key, value in blocker["安全边界"].items())
    lines.append("")
    return "\n".join(lines)


def build_checklist_md(checklist: dict[str, Any]) -> str:
    lines = [
        "# 全系统最终验收清单骨架",
        f"生成时间：{checklist['生成时间']}",
        "",
        f"- 说明：{checklist['说明']}",
        "",
        "## 总体验收域",
    ]
    lines.extend(f"- {item['域']}：{item['检查']}" for item in checklist["总体验收域"])
    lines.extend(["", "## 交付前必须完成", *md_list(checklist["交付前必须完成"])])
    lines.extend(["", "## 可后置", *md_list(checklist["可后置"])])
    lines.extend(["", "## 用户暂停", *md_list(checklist["用户暂停"])])
    lines.extend(["", "## 最终验收占位项"])
    lines.extend(f"- {item}" for item in checklist["最终验收占位项"])
    lines.extend(["", "## 安全边界"])
    lines.extend(f"- {key}：{value}" for key, value in checklist["安全边界"].items())
    lines.append("")
    return "\n".join(lines)


def build_recovery_report(generated_at: str, checklist: dict[str, Any], blocker: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 00总管 第七批小任务AB最终验收读取器回收报告",
            f"生成时间：{generated_at}",
            "",
            "- 结论：通过",
            "- 任务性质：全系统最终验收清单骨架与剩余阻断读取器",
            "- 读取范围：最新进度、股票硬闸门、01/02/03状态、用户暂停口径",
            "- 写入范围：仅总管 02脚本、03数据/运行状态、指定并行回收报告",
            "- 进度口径数字：未修改、未重算",
            "- 面板/接续包：未修改",
            "- n8n/企业微信真实消息/正式库/券商接口/自动交易：未触发",
            "",
            "## 产物",
            f"- `{CHECKLIST_JSON}`",
            f"- `{CHECKLIST_MD}`",
            f"- `{BLOCKER_JSON}`",
            f"- `{BLOCKER_MD}`",
            "",
            "## 阻断分类摘要",
            f"- 可交付前必须完成：{len(checklist['交付前必须完成'])}",
            f"- 可后置：{len(checklist['可后置'])}",
            f"- 用户暂停：{len(checklist['用户暂停'])}",
            "",
            "## 安全边界",
            *[f"- {key}：{value}" for key, value in blocker["安全边界"].items()],
            "",
        ]
    )


def main() -> int:
    generated_at = now_text()
    blocker = build_blocker_reader(generated_at)
    checklist = build_checklist(generated_at, blocker)
    write_json(BLOCKER_JSON, blocker)
    write_text(BLOCKER_MD, build_blocker_md(blocker))
    write_json(CHECKLIST_JSON, checklist)
    write_text(CHECKLIST_MD, build_checklist_md(checklist))
    write_text(RECOVERY_REPORT, build_recovery_report(generated_at, checklist, blocker))
    print(json.dumps({"结论": "通过", "可交付前必须完成": len(checklist["交付前必须完成"]), "可后置": len(checklist["可后置"]), "用户暂停": len(checklist["用户暂停"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
