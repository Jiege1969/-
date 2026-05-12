# -*- coding: utf-8 -*-
"""执行三业务反馈候选复跑去重预演。

只读取第77包示例候选和第74包候选入队预演产物，生成复跑去重结果与人工确认台账；
不写正式规则、不自动吸收、不修改运行配置、不触发外部系统。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "77三业务反馈候选复跑去重与人工确认台账包"
SOURCE_74_DIR = ROOT / "03数据" / "74三业务反馈样本闭环只读入队与候选生成包"

PACKAGE_JSON = DATA_DIR / "三业务反馈候选复跑去重与人工确认台账包_最新.json"
LOCAL_SAMPLE_JSON = DATA_DIR / "本包复跑去重示例候选_最新.json"
SOURCE_74_PREVIEW_JSON = SOURCE_74_DIR / "候选入队预演结果_最新.json"

RERUN_RESULT_JSON = DATA_DIR / "复跑去重预演结果_最新.json"
RERUN_RESULT_MD = DATA_DIR / "复跑去重预演结果_最新.md"
LEDGER_JSON = DATA_DIR / "人工确认台账_最新.json"
LEDGER_MD = DATA_DIR / "人工确认台账_最新.md"

REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
REQUIRED_SOURCE_FIELDS = {"候选ID", "来源", "业务线", "问题类型", "建议动作"}
FORBIDDEN_ACTIONS = [
    "真实发送企业微信",
    "接n8n",
    "接券商",
    "交易",
    "登录税局",
    "接财税软件",
    "自动转正式规则",
    "修改运行配置",
    "修改总管面板",
    "修改一键接续包",
    "重载服务",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalize(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"\s+", "", text)
    return text


def build_dedupe_key(item: dict[str, Any]) -> str:
    raw = "|".join([normalize(item.get("业务线")), normalize(item.get("问题类型")), normalize(item.get("建议动作"))])
    return "dedupe-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def load_source_candidates(errors: list[str]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    if SOURCE_74_PREVIEW_JSON.exists():
        preview_74 = read_json(SOURCE_74_PREVIEW_JSON)
        for item in preview_74.get("候选条目", []):
            candidates.append(
                {
                    "候选ID": item.get("候选ID"),
                    "来源": f"第74包候选入队预演/{item.get('来源', '')}",
                    "业务线": item.get("业务线"),
                    "问题类型": item.get("问题类型"),
                    "建议动作": item.get("建议动作"),
                    "需人工确认": True,
                    "自动生效": False,
                    "来源文件": str(SOURCE_74_PREVIEW_JSON),
                }
            )
    else:
        errors.append(f"第74包候选预演产物不存在：{SOURCE_74_PREVIEW_JSON}")

    if LOCAL_SAMPLE_JSON.exists():
        local_sample = read_json(LOCAL_SAMPLE_JSON)
        for item in local_sample.get("样本列表", []):
            candidates.append(
                {
                    "候选ID": item.get("候选ID"),
                    "来源": item.get("来源"),
                    "业务线": item.get("业务线"),
                    "问题类型": item.get("问题类型"),
                    "建议动作": item.get("建议动作"),
                    "需人工确认": True,
                    "自动生效": False,
                    "来源文件": str(LOCAL_SAMPLE_JSON),
                }
            )
    else:
        errors.append(f"本包复跑示例候选不存在：{LOCAL_SAMPLE_JSON}")

    return candidates


def validate_source(item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(field for field in REQUIRED_SOURCE_FIELDS if not item.get(field))
    if missing:
        errors.append(f"{item.get('候选ID', 'UNKNOWN')} 缺少字段：{', '.join(missing)}")
    if item.get("业务线") not in REQUIRED_BUSINESSES:
        errors.append(f"{item.get('候选ID', 'UNKNOWN')} 业务线不在税收/股票/视频范围内")
    if item.get("需人工确认") is not True:
        errors.append(f"{item.get('候选ID', 'UNKNOWN')} 需人工确认必须为 true")
    if item.get("自动生效") is not False:
        errors.append(f"{item.get('候选ID', 'UNKNOWN')} 自动生效必须为 false")
    return errors


def apply_dedupe(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keyed: dict[str, list[dict[str, Any]]] = {}
    for item in candidates:
        item["去重键"] = build_dedupe_key(item)
        keyed.setdefault(item["去重键"], []).append(item)

    result: list[dict[str, Any]] = []
    for item in candidates:
        group = keyed[item["去重键"]]
        first = group[0]
        is_duplicate = item is not first
        result.append(
            {
                "候选ID": item["候选ID"],
                "去重键": item["去重键"],
                "业务线": item["业务线"],
                "来源": item["来源"],
                "来源文件": item["来源文件"],
                "问题类型": item["问题类型"],
                "建议动作": item["建议动作"],
                "需人工确认": True,
                "自动生效": False,
                "转正式规则": False,
                "重复状态": "重复候选" if is_duplicate else "唯一候选",
                "重复计数": len(group),
                "主候选ID": first["候选ID"],
                "台账状态": "待确认",
            }
        )
    return result


def build_ledger_items(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, item in enumerate(candidates, 1):
        items.append(
            {
                "台账ID": f"LEDGER-RERUN-{index:03d}",
                "候选ID": item["候选ID"],
                "去重键": item["去重键"],
                "业务线": item["业务线"],
                "来源": item["来源"],
                "问题类型": item["问题类型"],
                "建议动作": item["建议动作"],
                "重复状态": item["重复状态"],
                "重复计数": item["重复计数"],
                "主候选ID": item["主候选ID"],
                "台账状态": "待确认",
                "需人工确认": True,
                "自动生效": False,
                "确认人": "",
                "确认时间": "",
                "确认意见": "",
            }
        )
    return items


def build_rerun_md(report: dict[str, Any]) -> str:
    lines = [
        "# 复跑去重预演结果",
        "",
        f"- 预演时间：{report['预演时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 错误数：{report['错误数']}",
        f"- 候选数：{report['汇总']['候选数']}",
        f"- 重复项数：{report['汇总']['重复项数']}",
        f"- 重复键数：{report['汇总']['重复键数']}",
        "",
        "| 候选ID | 去重键 | 业务线 | 问题类型 | 重复状态 | 重复计数 | 需人工确认 | 自动生效 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["候选条目"]:
        lines.append(
            f"| {item['候选ID']} | {item['去重键']} | {item['业务线']} | {item['问题类型']} | "
            f"{item['重复状态']} | {item['重复计数']} | {str(item['需人工确认']).lower()} | {str(item['自动生效']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_ledger_md(ledger: dict[str, Any]) -> str:
    lines = [
        "# 人工确认台账",
        "",
        f"- 生成时间：{ledger['生成时间']}",
        "- 台账状态默认：待确认",
        "- 需人工确认：true",
        "- 自动生效：false",
        "",
        "| 台账ID | 候选ID | 去重键 | 业务线 | 问题类型 | 重复状态 | 台账状态 | 需人工确认 | 自动生效 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in ledger["台账条目"]:
        lines.append(
            f"| {item['台账ID']} | {item['候选ID']} | {item['去重键']} | {item['业务线']} | {item['问题类型']} | "
            f"{item['重复状态']} | {item['台账状态']} | {str(item['需人工确认']).lower()} | {str(item['自动生效']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    errors: list[str] = []
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    if package.get("状态") != "three_business_feedback_rerun_dedupe_ledger_ready":
        errors.append("生成包状态必须为 three_business_feedback_rerun_dedupe_ledger_ready")
    if package.get("只读复跑") is not True:
        errors.append("生成包必须声明只读复跑")
    if package.get("默认自动生效") is not False:
        errors.append("生成包必须声明默认自动生效=false")
    if package.get("默认需人工确认") is not True:
        errors.append("生成包必须声明默认需人工确认=true")
    for name in FORBIDDEN_ACTIONS:
        if package.get("红线动作", {}).get(name) is not False:
            errors.append(f"红线动作 {name} 必须为 false")

    source_candidates = load_source_candidates(errors)
    for item in source_candidates:
        errors.extend(validate_source(item))

    deduped = apply_dedupe(source_candidates) if not errors else []
    duplicate_items = [item for item in deduped if item["重复状态"] == "重复候选"]
    duplicate_keys = {item["去重键"] for item in deduped if item["重复计数"] > 1}
    businesses = {item.get("业务线") for item in deduped}
    if businesses != REQUIRED_BUSINESSES:
        errors.append("复跑候选必须覆盖税收/股票/视频")
    if not duplicate_items and not duplicate_keys:
        errors.append("复跑去重预演必须标记或计数至少一个重复项")
    if any(item.get("自动生效") is not False for item in deduped):
        errors.append("所有候选必须自动生效=false")
    if any(item.get("需人工确认") is not True for item in deduped):
        errors.append("所有候选必须需人工确认=true")

    generated_at = now_text()
    ledger = {
        "名称": "三业务反馈候选人工确认台账",
        "生成时间": generated_at,
        "台账状态默认值": "待确认",
        "只读复跑": True,
        "不写正式规则": True,
        "不自动吸收": True,
        "不改运行配置": True,
        "台账条目": build_ledger_items(deduped),
    }
    report = {
        "名称": "三业务反馈候选复跑去重预演结果",
        "预演时间": generated_at,
        "总体状态": "pass" if not errors else "fail",
        "错误数": len(errors),
        "错误": errors,
        "只读复跑": True,
        "读取范围": [str(PACKAGE_JSON), str(LOCAL_SAMPLE_JSON), str(SOURCE_74_PREVIEW_JSON)],
        "未触发动作": FORBIDDEN_ACTIONS,
        "覆盖业务": sorted(businesses),
        "默认需人工确认": all(item.get("需人工确认") is True for item in deduped),
        "默认自动生效": False,
        "不写正式规则": True,
        "不自动吸收": True,
        "候选条目": deduped,
        "汇总": {
            "候选数": len(deduped),
            "业务数": len(businesses),
            "重复项数": len(duplicate_items),
            "重复键数": len(duplicate_keys),
            "需人工确认数": sum(1 for item in deduped if item.get("需人工确认") is True),
            "自动生效数": sum(1 for item in deduped if item.get("自动生效") is True),
            "错误数": len(errors),
        },
        "输出文件": {
            "复跑去重预演结果JSON": str(RERUN_RESULT_JSON),
            "复跑去重预演结果Markdown": str(RERUN_RESULT_MD),
            "人工确认台账JSON": str(LEDGER_JSON),
            "人工确认台账Markdown": str(LEDGER_MD),
        },
    }

    write_json(RERUN_RESULT_JSON, report)
    write_text(RERUN_RESULT_MD, build_rerun_md(report))
    write_json(LEDGER_JSON, ledger)
    write_text(LEDGER_MD, build_ledger_md(ledger))

    print(json.dumps({"总体状态": report["总体状态"], "错误数": report["错误数"], "候选数": len(deduped), "重复项数": len(duplicate_items), "输出": str(RERUN_RESULT_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
