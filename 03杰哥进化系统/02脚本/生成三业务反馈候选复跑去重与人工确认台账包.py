# -*- coding: utf-8 -*-
"""生成三业务反馈候选复跑去重与人工确认台账包。

本包只生成复跑去重预演所需的字段规范、示例重复样本和台账模板；不写正式规则、
不自动吸收、不修改运行配置、不触发任何外部业务链路。
"""

from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "77三业务反馈候选复跑去重与人工确认台账包"
SOURCE_74_DIR = ROOT / "03数据" / "74三业务反馈样本闭环只读入队与候选生成包"

FIELD_SPEC_JSON = DATA_DIR / "复跑去重与人工确认台账字段规范_最新.json"
FIELD_SPEC_MD = DATA_DIR / "复跑去重与人工确认台账字段规范_最新.md"
LOCAL_SAMPLE_JSON = DATA_DIR / "本包复跑去重示例候选_最新.json"
LEDGER_TEMPLATE_JSON = DATA_DIR / "人工确认台账模板_最新.json"
LEDGER_TEMPLATE_MD = DATA_DIR / "人工确认台账模板_最新.md"
PACKAGE_JSON = DATA_DIR / "三业务反馈候选复跑去重与人工确认台账包_最新.json"

SOURCE_74_PREVIEW_JSON = SOURCE_74_DIR / "候选入队预演结果_最新.json"

REQUIRED_BUSINESSES = ["税收", "股票", "视频"]
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


def build_field_spec(generated_at: str) -> dict[str, Any]:
    return {
        "名称": "三业务反馈候选复跑去重与人工确认台账字段规范",
        "版本": "rerun-dedupe-ledger-v1",
        "生成时间": generated_at,
        "只读复跑": True,
        "覆盖业务": REQUIRED_BUSINESSES,
        "默认需人工确认": True,
        "默认自动生效": False,
        "不写正式规则": True,
        "不自动吸收": True,
        "候选必备字段": [
            {"字段": "候选ID", "类型": "string", "必填": True},
            {"字段": "去重键", "类型": "string", "必填": True},
            {"字段": "业务线", "类型": "enum", "必填": True, "允许值": REQUIRED_BUSINESSES},
            {"字段": "来源", "类型": "string", "必填": True},
            {"字段": "问题类型", "类型": "string", "必填": True},
            {"字段": "建议动作", "类型": "string", "必填": True},
            {"字段": "需人工确认", "类型": "boolean", "必填": True, "固定值": True},
            {"字段": "自动生效", "类型": "boolean", "必填": True, "固定值": False},
            {"字段": "重复状态", "类型": "enum", "必填": True, "允许值": ["唯一候选", "重复候选"]},
            {"字段": "重复计数", "类型": "integer", "必填": True},
        ],
        "台账必备字段": [
            {"字段": "台账ID", "类型": "string", "必填": True},
            {"字段": "候选ID", "类型": "string", "必填": True},
            {"字段": "去重键", "类型": "string", "必填": True},
            {"字段": "业务线", "类型": "enum", "必填": True, "允许值": REQUIRED_BUSINESSES},
            {"字段": "来源", "类型": "string", "必填": True},
            {"字段": "问题类型", "类型": "string", "必填": True},
            {"字段": "建议动作", "类型": "string", "必填": True},
            {"字段": "台账状态", "类型": "enum", "必填": True, "默认值": "待确认"},
            {"字段": "需人工确认", "类型": "boolean", "必填": True, "固定值": True},
            {"字段": "自动生效", "类型": "boolean", "必填": True, "固定值": False},
            {"字段": "确认人", "类型": "string", "必填": False, "默认值": ""},
            {"字段": "确认时间", "类型": "string", "必填": False, "默认值": ""},
            {"字段": "确认意见", "类型": "string", "必填": False, "默认值": ""},
        ],
        "红线动作": {name: False for name in FORBIDDEN_ACTIONS},
    }


def build_local_samples(generated_at: str) -> dict[str, Any]:
    items = [
        {
            "候选ID": "RERUN-SEED-TAX-DUP-001",
            "来源": "本包示例/税收/重复候选复跑样本",
            "业务线": "税收",
            "问题类型": "口径不清",
            "建议动作": "生成候选说明：补充适用前提、资料清单和需人工复核提示。",
            "需人工确认": True,
            "自动生效": False,
            "样本说明": "用于复跑去重，预期与第74包税收候选形成同去重键重复。",
        },
        {
            "候选ID": "RERUN-SEED-STOCK-UNIQ-001",
            "来源": "本包示例/股票/人工确认台账字段样本",
            "业务线": "股票",
            "问题类型": "风险提示不足",
            "建议动作": "生成候选说明：补充风险边界、非交易建议声明和人工确认提示。",
            "需人工确认": True,
            "自动生效": False,
            "样本说明": "用于确认股票业务字段覆盖，不自动生效。",
        },
        {
            "候选ID": "RERUN-SEED-VIDEO-UNIQ-001",
            "来源": "本包示例/视频/人工确认台账字段样本",
            "业务线": "视频",
            "问题类型": "分镜遗漏",
            "建议动作": "生成候选说明：补充分镜画面占位、口播节奏和人工确认提示。",
            "需人工确认": True,
            "自动生效": False,
            "样本说明": "用于确认视频业务字段覆盖，不触发渲染发布。",
        },
    ]
    for item in items:
        item["去重键"] = build_dedupe_key(item)
    return {
        "名称": "本包复跑去重示例候选",
        "生成时间": generated_at,
        "只读复跑": True,
        "样本列表": items,
    }


def build_field_md(field_spec: dict[str, Any]) -> str:
    lines = [
        "# 复跑去重与人工确认台账字段规范",
        "",
        f"- 版本：{field_spec['版本']}",
        f"- 生成时间：{field_spec['生成时间']}",
        "- 只读复跑：true",
        "- 默认需人工确认：true",
        "- 默认自动生效：false",
        "- 不写正式规则：true",
        "",
        "## 候选必备字段",
        "",
        "| 字段 | 类型 | 必填 | 说明 |",
        "| --- | --- | --- | --- |",
    ]
    for item in field_spec["候选必备字段"]:
        detail = item.get("说明") or item.get("固定值") or item.get("默认值") or "，".join(item.get("允许值", []))
        lines.append(f"| {item['字段']} | {item['类型']} | {str(item['必填']).lower()} | {detail} |")
    lines.extend(["", "## 台账必备字段", "", "| 字段 | 类型 | 必填 | 说明 |", "| --- | --- | --- | --- |"])
    for item in field_spec["台账必备字段"]:
        detail = item.get("说明") or item.get("固定值") or item.get("默认值") or "，".join(item.get("允许值", []))
        lines.append(f"| {item['字段']} | {item['类型']} | {str(item['必填']).lower()} | {detail} |")
    lines.extend(["", "## 红线动作", ""])
    lines.extend(f"- {name}：false" for name in field_spec["红线动作"])
    lines.append("")
    return "\n".join(lines)


def build_ledger_template(generated_at: str) -> dict[str, Any]:
    return {
        "名称": "人工确认台账模板",
        "生成时间": generated_at,
        "台账状态默认值": "待确认",
        "需人工确认默认值": True,
        "自动生效默认值": False,
        "不写正式规则": True,
        "台账列": [
            "台账ID",
            "候选ID",
            "去重键",
            "业务线",
            "来源",
            "问题类型",
            "建议动作",
            "重复状态",
            "重复计数",
            "台账状态",
            "需人工确认",
            "自动生效",
            "确认人",
            "确认时间",
            "确认意见",
        ],
        "台账条目": [],
    }


def build_ledger_template_md(template: dict[str, Any]) -> str:
    columns = template["台账列"]
    lines = [
        "# 人工确认台账模板",
        "",
        f"- 生成时间：{template['生成时间']}",
        "- 台账状态默认值：待确认",
        "- 需人工确认默认值：true",
        "- 自动生效默认值：false",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    generated_at = now_text()
    field_spec = build_field_spec(generated_at)
    local_samples = build_local_samples(generated_at)
    ledger_template = build_ledger_template(generated_at)
    package = {
        "名称": "三业务反馈候选复跑去重与人工确认台账包",
        "生成时间": generated_at,
        "状态": "three_business_feedback_rerun_dedupe_ledger_ready",
        "承接来源": str(SOURCE_74_PREVIEW_JSON),
        "只读复跑": True,
        "覆盖业务": REQUIRED_BUSINESSES,
        "默认需人工确认": True,
        "默认自动生效": False,
        "不写正式规则": True,
        "不自动吸收": True,
        "不改运行配置": True,
        "红线动作": {name: False for name in FORBIDDEN_ACTIONS},
        "输出文件": {
            "字段规范JSON": str(FIELD_SPEC_JSON),
            "字段规范Markdown": str(FIELD_SPEC_MD),
            "本包示例候选JSON": str(LOCAL_SAMPLE_JSON),
            "人工确认台账模板JSON": str(LEDGER_TEMPLATE_JSON),
            "人工确认台账模板Markdown": str(LEDGER_TEMPLATE_MD),
            "总包JSON": str(PACKAGE_JSON),
        },
    }

    write_json(FIELD_SPEC_JSON, field_spec)
    write_text(FIELD_SPEC_MD, build_field_md(field_spec))
    write_json(LOCAL_SAMPLE_JSON, local_samples)
    write_json(LEDGER_TEMPLATE_JSON, ledger_template)
    write_text(LEDGER_TEMPLATE_MD, build_ledger_template_md(ledger_template))
    write_json(PACKAGE_JSON, package)

    print(json.dumps({"状态": package["状态"], "示例候选数": len(local_samples["样本列表"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
