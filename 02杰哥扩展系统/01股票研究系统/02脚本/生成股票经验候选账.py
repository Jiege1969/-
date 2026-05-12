# -*- coding: utf-8 -*-
"""
名称：生成股票经验候选账.py
作用：根据判断复盘账和验证结果账生成候选经验，不自动采纳、不自动改规则。
触发方式：python 生成股票经验候选账.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读04日志/复盘账本；只写经验候选账；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不自动修改评分规则。
标识：stock-experience-candidate-generate
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_result(value: Any) -> str:
    text = str(value or "").strip()
    if text in {"有效", "部分有效", "无效", "未验证"}:
        return text
    return "未验证"


def build_candidates(replay_records: list[dict[str, Any]], validation_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    main_reason_counter = Counter(str(item.get("判断主因") or "未标注") for item in replay_records)
    quality_counter = Counter(str(item.get("公司品质档位") or "待核验") for item in replay_records)

    if replay_records:
        top_reason, top_count = main_reason_counter.most_common(1)[0]
        candidates.append({
            "候选经验": f"近期判断记录中，'{top_reason}' 是出现最多的判断主因，应在周复盘时重点观察其后续有效率。",
            "依据": f"判断复盘账共 {len(replay_records)} 条记录，其中 {top_reason} 出现 {top_count} 次。",
            "提议动作": "暂不修改规则；等待验证结果账积累后，再判断是否调整对应权重。",
            "状态": "待人工确认",
            "生成日期": datetime.now().strftime("%Y-%m-%d"),
        })

        pending_quality = quality_counter.get("待核验", 0)
        if pending_quality:
            candidates.append({
                "候选经验": "公司品质档位为'待核验'的记录仍占一定比例，标准报告的公司概况和财务质量解释力不足。",
                "依据": f"当前判断复盘账中，公司品质待核验记录 {pending_quality} 条。",
                "提议动作": "优先补齐进入L5和用户增强池股票的公司品质档案，不直接调低分数。",
                "状态": "待人工确认",
                "生成日期": datetime.now().strftime("%Y-%m-%d"),
            })

    grouped: dict[str, list[str]] = defaultdict(list)
    for item in validation_records:
        key = str(item.get("判断主因") or item.get("主因") or "未标注")
        grouped[key].append(normalize_result(item.get("人工确认结果") or item.get("验证结果") or item.get("初步验证建议")))

    for reason, results in grouped.items():
        checked = [r for r in results if r != "未验证"]
        if len(checked) < 5:
            continue
        valid_count = sum(1 for r in checked if r in {"有效", "部分有效"})
        ratio = valid_count / len(checked)
        if ratio < 0.4:
            candidates.append({
                "候选经验": f"'{reason}' 类判断在已验证样本中的有效率偏低，可能需要降低自动加权或提高入选门槛。",
                "依据": f"已验证 {len(checked)} 条，有效或部分有效 {valid_count} 条，有效率 {ratio:.0%}。",
                "提议动作": "进入人工复核，不自动修改L6/L5规则。",
                "状态": "待人工确认",
                "生成日期": datetime.now().strftime("%Y-%m-%d"),
            })
        elif ratio >= 0.7:
            candidates.append({
                "候选经验": f"'{reason}' 类判断在已验证样本中的有效率较高，可作为后续规则优化候选。",
                "依据": f"已验证 {len(checked)} 条，有效或部分有效 {valid_count} 条，有效率 {ratio:.0%}。",
                "提议动作": "进入人工复核，观察是否提高该类主因的报告优先级。",
                "状态": "待人工确认",
                "生成日期": datetime.now().strftime("%Y-%m-%d"),
            })

    if not candidates:
        candidates.append({
            "候选经验": "当前样本量不足，暂不提炼规则经验。",
            "依据": "判断复盘账或验证结果账尚未形成足够样本。",
            "提议动作": "继续积累报告、判断主因和验证结果。",
            "状态": "待人工确认",
            "生成日期": datetime.now().strftime("%Y-%m-%d"),
        })
    return candidates


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票经验候选账 - {report['生成时间']}",
        "",
        "## 说明",
        "",
        "- 本文件只生成候选经验。",
        "- 不自动采纳。",
        "- 不自动修改评分、权重、冷却期或推送规则。",
        "",
        "## 候选经验",
        "",
    ]
    for idx, item in enumerate(report["候选经验"], start=1):
        lines.append(f"### {idx}. {item.get('候选经验')}")
        lines.append(f"- 依据：{item.get('依据')}")
        lines.append(f"- 提议动作：{item.get('提议动作')}")
        lines.append(f"- 状态：{item.get('状态')}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    replay_path = root / "04日志" / "复盘" / "判断复盘账_最新.json"
    validation_path = root / "04日志" / "复盘" / "验证结果账_最新.json"
    latest_path = root / "04日志" / "复盘" / "经验候选账_最新.json"
    stamp_path = root / "04日志" / "复盘" / f"经验候选账_{stamp}.json"
    latest_md = root / "04日志" / "复盘" / "经验候选账_最新.md"
    stamp_md = root / "04日志" / "复盘" / f"经验候选账_{stamp}.md"

    replay_records = load_json(replay_path, [])
    validation_records = load_json(validation_path, [])
    if not isinstance(replay_records, list):
        replay_records = []
    if not isinstance(validation_records, list):
        validation_records = []

    report = {
        "名称": "经验候选账",
        "版本": "v1.0",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "判断复盘记录数": len(replay_records),
        "验证结果记录数": len(validation_records),
        "说明": "候选经验必须人工确认后，才能手工固化到规则文件。",
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否自动修改规则": False,
        },
        "候选经验": build_candidates(replay_records, validation_records),
    }
    write_json(latest_path, report)
    write_json(stamp_path, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    write_text(stamp_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "候选经验数": len(report["候选经验"]),
        "输出": str(latest_path),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
