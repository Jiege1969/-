# -*- coding: utf-8 -*-
"""
名称：生成公司概况补全底稿.py
作用：从现有L5、用户增强池、公司品质档案中整理公司概况缺口和可用线索，生成待人工核验底稿。
触发方式：python 生成公司概况补全底稿.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地数据；只写03数据/171公司概况补全底稿；不反写公司品质档案；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-company-profile-draft
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


MISSING_VALUES = {"", "待接入", "待补充", "未知", None}


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def index_by_code(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("代码", "")).strip(): item for item in items if item.get("代码")}


def is_missing(value: Any) -> bool:
    return value in MISSING_VALUES


def pick(*values: Any) -> str:
    for value in values:
        if not is_missing(value):
            return str(value)
    return "待核验"


def build_profile_clue(item: dict[str, Any], enhance: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
    industry = pick(
        item.get("行业"),
        item.get("申万一级行业"),
        enhance.get("行业"),
        quality.get("申万一级行业"),
    )
    sub_field = pick(
        item.get("细分领域"),
        item.get("细分行业"),
        enhance.get("细分领域"),
        quality.get("细分行业"),
    )
    tags = enhance.get("标签") if isinstance(enhance.get("标签"), list) else []
    category = pick(enhance.get("名单分类"), item.get("名单分类"), "待核验")
    focus_level = pick(enhance.get("关注级别"), "待核验")

    profile = quality.get("公司概况") if isinstance(quality.get("公司概况"), dict) else {}
    missing_fields = [name for name, value in profile.items() if is_missing(value)]
    if not profile:
        missing_fields = ["核心业务", "行业地位", "主营产品", "主要客户或下游", "未来方向"]

    clue_parts = []
    if industry != "待核验":
        clue_parts.append(f"行业线索：{industry}")
    if sub_field != "待核验":
        clue_parts.append(f"细分线索：{sub_field}")
    if tags:
        clue_parts.append("标签线索：" + "、".join(str(tag) for tag in tags[:6]))
    if category != "待核验":
        clue_parts.append(f"名单分类：{category}")
    if focus_level != "待核验":
        clue_parts.append(f"关注级别：{focus_level}")

    if clue_parts:
        draft_sentence = "；".join(clue_parts) + "。以上仅为现有池内标签线索，需用公司公告、年报或F10资料人工核验后写入正式档案。"
    else:
        draft_sentence = "现有池内缺少可用概况线索，需人工从公告、年报或F10资料补充。"

    return {
        "代码": item.get("代码") or enhance.get("代码") or quality.get("代码"),
        "展示代码": item.get("展示代码") or enhance.get("展示代码") or quality.get("展示代码"),
        "名称": item.get("名称") or enhance.get("名称") or quality.get("名称"),
        "行业": industry,
        "细分领域": sub_field,
        "是否用户增强": bool(enhance),
        "是否当前L5": bool(item),
        "公司品质档位": quality.get("公司品质档位", "待核验"),
        "缺失字段": missing_fields,
        "可用线索": clue_parts,
        "前台概况底稿": draft_sentence,
        "建议动作": "人工核验后，再写入公司品质档案/公司经营快照；本脚本不自动反写。",
    }


def build_markdown(report: dict[str, Any]) -> str:
    pending_stocks = [item for item in report["股票"] if item.get("缺失字段")]
    lines = [
        f"# 公司概况补全底稿 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 当前处理股票：{report['股票数量']}只",
        f"- 当前L5股票：{report['当前L5数量']}只",
        f"- 需要补公司概况：{report['需要补概况数量']}只",
        f"- 已有公司概况：{report['已有概况数量']}只",
        "- 本底稿只提供线索，不把推断当事实写入正式档案。",
        "",
        "## 二、优先补全清单",
        "",
        "| 优先级 | 代码 | 名称 | 行业 | 细分领域 | 品质档位 | 缺失字段 |",
        "|---:|---|---|---|---|---|---|",
    ]
    if pending_stocks:
        for idx, item in enumerate(pending_stocks, 1):
            missing = "、".join(item.get("缺失字段", []))
            lines.append(
                f"| {idx} | {item.get('代码')} | {item.get('名称')} | {item.get('行业')} | "
                f"{item.get('细分领域')} | {item.get('公司品质档位')} | {missing} |"
            )
    else:
        lines.append("| - | - | - | - | - | - | 无待补字段 |")

    lines.extend(["", "## 三、逐股线索", ""])
    for item in pending_stocks:
        lines.extend([
            f"### {item.get('名称')}({item.get('代码')})",
            "",
            f"- 前台概况底稿：{item.get('前台概况底稿')}",
            f"- 建议动作：{item.get('建议动作')}",
            "",
        ])

    lines.extend([
        "## 四、安全边界",
        "",
        "- 不反写公司品质档案。",
        "- 不触发n8n，不发送企业微信。",
        "- 不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    l5_data = load_json(root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json", {})
    enhance_data = load_json(root / "03数据" / "131用户增强观察池" / "用户增强观察池_最新.json", {})
    quality_data = load_json(root / "03数据" / "168公司品质档案" / "公司品质档案_最新.json", {})

    l5_items = l5_data.get("股票池", []) if isinstance(l5_data, dict) else []
    enhance_map = index_by_code(enhance_data.get("股票池", []) if isinstance(enhance_data, dict) else [])
    quality_map = index_by_code(quality_data.get("股票档案", []) if isinstance(quality_data, dict) else [])

    selected_codes: list[str] = []
    for item in l5_items:
        code = item.get("代码")
        if code and code not in selected_codes:
            selected_codes.append(code)

    for code in enhance_map:
        if len(selected_codes) >= 30:
            break
        if code not in selected_codes:
            selected_codes.append(code)

    stocks = []
    for code in selected_codes:
        item = next((row for row in l5_items if row.get("代码") == code), {})
        stocks.append(build_profile_clue(item, enhance_map.get(code, {}), quality_map.get(code, {})))

    pending_count = sum(1 for item in stocks if item.get("缺失字段"))
    report = {
        "名称": "公司概况补全底稿",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成公司概况补全底稿.py",
        "定位": "为前台结论式报告补公司概况线索，只生成待核验底稿，不自动反写正式档案。",
        "股票数量": len(stocks),
        "当前L5数量": len(l5_items),
        "需要补概况数量": pending_count,
        "已有概况数量": len(stocks) - pending_count,
        "股票": stocks,
        "安全边界": {
            "是否反写公司品质档案": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "171公司概况补全底稿"
    output_json = output_dir / f"公司概况补全底稿_{stamp}.json"
    output_md = output_dir / f"公司概况补全底稿_{stamp}.md"
    latest_json = output_dir / "公司概况补全底稿_最新.json"
    latest_md = output_dir / "公司概况补全底稿_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)

    print(json.dumps({
        "状态": "完成",
        "股票数量": len(stocks),
        "需要补概况数量": report["需要补概况数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
