# -*- coding: utf-8 -*-
"""生成三业务反馈样本闭环只读入队与候选生成包。

本包只提供字段规范、三业务示例样本和候选生成规则说明；不自动吸收反馈，
不转正式规则，不改运行配置，不触发任何业务接口。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "74三业务反馈样本闭环只读入队与候选生成包"

FIELD_SPEC_JSON = DATA_DIR / "三业务反馈样本字段规范_最新.json"
FIELD_SPEC_MD = DATA_DIR / "三业务反馈样本字段规范_最新.md"
SAMPLE_JSON = DATA_DIR / "三业务反馈示例样本_最新.json"
CANDIDATE_RULE_MD = DATA_DIR / "候选生成规则说明_最新.md"
PACKAGE_JSON = DATA_DIR / "三业务反馈样本闭环只读入队与候选生成包_最新.json"


REQUIRED_FIELDS: list[dict[str, Any]] = [
    {"字段": "样本ID", "类型": "string", "必填": True, "说明": "本包内唯一的反馈样本编号。"},
    {"字段": "来源", "类型": "string", "必填": True, "说明": "只读样本来源，必须指向本包示例或人工离线摘录。"},
    {"字段": "业务线", "类型": "enum", "必填": True, "允许值": ["税收", "股票", "视频"]},
    {"字段": "输入原文", "类型": "string", "必填": True, "说明": "用户反馈原文或离线摘录。"},
    {"字段": "系统输出摘要", "类型": "string", "必填": True, "说明": "仅记录既有输出摘要，不生成新结论。"},
    {"字段": "用户判定", "类型": "string", "必填": True, "说明": "用户对输出的判定或复核意见。"},
    {"字段": "问题类型", "类型": "enum", "必填": True, "允许值": ["理解偏差", "摘要遗漏", "口径不清", "风险提示不足", "交易化表达", "脚本不清", "分镜遗漏", "预检误判", "其他"]},
    {"字段": "建议动作", "类型": "string", "必填": True, "说明": "候选层建议，不得直接改正式规则。"},
    {"字段": "是否触红线", "类型": "boolean", "必填": True, "默认值": False},
    {"字段": "是否可自动吸收", "类型": "boolean", "必填": True, "默认值": False},
    {"字段": "需人工确认", "类型": "boolean", "必填": True, "默认值": True},
]

EXAMPLE_SAMPLES: list[dict[str, Any]] = [
    {
        "样本ID": "TBFRQ-TAX-001",
        "来源": "本包示例样本/税收/离线反馈",
        "业务线": "税收",
        "输入原文": "用户反馈：上次回答把小规模纳税人的口径说得太笼统，缺少适用前提。",
        "系统输出摘要": "既有输出只概括了申报口径，未展开适用条件和人工复核提示。",
        "用户判定": "部分正确，需补充前提条件。",
        "问题类型": "口径不清",
        "建议动作": "生成候选说明：补充适用前提、资料清单和需人工复核提示。",
        "是否触红线": False,
        "是否可自动吸收": False,
        "需人工确认": True,
    },
    {
        "样本ID": "TBFRQ-STOCK-001",
        "来源": "本包示例样本/股票/离线反馈",
        "业务线": "股票",
        "输入原文": "用户反馈：复盘摘要里风险提示太弱，容易被误解成直接买卖建议。",
        "系统输出摘要": "既有输出展示了走势复盘，但风险边界和非交易建议说明不足。",
        "用户判定": "表达有交易化倾向，需人工复核。",
        "问题类型": "风险提示不足",
        "建议动作": "生成候选说明：增强风险提示，弱化交易化措辞，仅保留展示层改写建议。",
        "是否触红线": False,
        "是否可自动吸收": False,
        "需人工确认": True,
    },
    {
        "样本ID": "TBFRQ-VIDEO-001",
        "来源": "本包示例样本/视频/离线反馈",
        "业务线": "视频",
        "输入原文": "用户反馈：短视频脚本第二段跳转太快，分镜缺少产品画面说明。",
        "系统输出摘要": "既有输出保留了三段式脚本，但第二段分镜描述不完整。",
        "用户判定": "部分正确，建议补充分镜。",
        "问题类型": "分镜遗漏",
        "建议动作": "生成候选说明：补充第二段分镜占位和人工确认点，不触发渲染发布。",
        "是否触红线": False,
        "是否可自动吸收": False,
        "需人工确认": True,
    },
]

SAFETY_BOUNDARY: dict[str, bool] = {
    "真实发送企业微信": False,
    "接n8n": False,
    "接券商": False,
    "交易": False,
    "登录税局": False,
    "接财税软件": False,
    "自动转正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载服务": False,
    "触发业务接口": False,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_field_spec() -> dict[str, Any]:
    return {
        "名称": "三业务反馈样本字段规范",
        "版本": "readonly-queue-candidate-v1",
        "生成时间": now_text(),
        "覆盖业务": ["税收", "股票", "视频"],
        "默认不自动吸收": True,
        "不转正式规则": True,
        "候选需人工确认": True,
        "字段列表": REQUIRED_FIELDS,
        "安全边界": SAFETY_BOUNDARY,
    }


def build_package(field_spec: dict[str, Any]) -> dict[str, Any]:
    generated_at = field_spec["生成时间"]
    return {
        "名称": "三业务反馈样本闭环只读入队与候选生成包",
        "生成时间": generated_at,
        "状态": "three_business_feedback_readonly_queue_candidate_ready",
        "基于": "第三轮三业务用户反馈样本闭环模板包",
        "覆盖业务": ["税收", "股票", "视频"],
        "默认不自动吸收": True,
        "不转正式规则": True,
        "只读预演": True,
        "字段规范": field_spec,
        "示例样本": EXAMPLE_SAMPLES,
        "候选生成规则": [
            "只读取本包三业务反馈示例样本。",
            "每条样本生成一条候选入队预演条目。",
            "候选条目必须保留来源、业务线、问题类型、建议动作。",
            "候选条目必须设置需人工确认=true、是否可自动吸收=false、转正式规则=false。",
            "候选结果只写入本包数据目录，不写正式规则、不改运行配置、不触发业务接口。",
        ],
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "字段规范JSON": str(FIELD_SPEC_JSON),
            "字段规范Markdown": str(FIELD_SPEC_MD),
            "示例样本JSON": str(SAMPLE_JSON),
            "候选生成规则说明": str(CANDIDATE_RULE_MD),
            "总包JSON": str(PACKAGE_JSON),
        },
    }


def build_field_md(field_spec: dict[str, Any]) -> str:
    lines = [
        "# 三业务反馈样本字段规范",
        "",
        f"- 版本：{field_spec['版本']}",
        f"- 生成时间：{field_spec['生成时间']}",
        "- 覆盖业务：税收、股票、视频",
        "- 默认不自动吸收：true",
        "- 不转正式规则：true",
        "- 候选需人工确认：true",
        "",
        "| 字段 | 类型 | 必填 | 说明 |",
        "| --- | --- | --- | --- |",
    ]
    for item in field_spec["字段列表"]:
        detail = item.get("说明") or "允许值：" + "、".join(item.get("允许值", []))
        lines.append(f"| {item['字段']} | {item['类型']} | {str(item['必填']).lower()} | {detail} |")
    lines.extend(["", "## 安全边界", ""])
    for name, allowed in field_spec["安全边界"].items():
        lines.append(f"- {name}：{str(allowed).lower()}")
    lines.append("")
    return "\n".join(lines)


def build_rule_md(package: dict[str, Any]) -> str:
    lines = [
        "# 候选生成规则说明",
        "",
        "本说明只用于只读入队预演。执行脚本只读取本包示例样本，输出候选入队预演结果。",
        "",
        "## 规则",
        "",
    ]
    lines.extend(f"- {rule}" for rule in package["候选生成规则"])
    lines.extend(
        [
            "",
            "## 禁止动作",
            "",
        ]
    )
    lines.extend(f"- {name}" for name, allowed in package["安全边界"].items() if allowed is False)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    field_spec = build_field_spec()
    package = build_package(field_spec)

    write_json(FIELD_SPEC_JSON, field_spec)
    write_text(FIELD_SPEC_MD, build_field_md(field_spec))
    write_json(SAMPLE_JSON, {"名称": "三业务反馈示例样本", "生成时间": field_spec["生成时间"], "样本列表": EXAMPLE_SAMPLES})
    write_text(CANDIDATE_RULE_MD, build_rule_md(package))
    write_json(PACKAGE_JSON, package)

    print(json.dumps({"状态": package["状态"], "样本数": len(EXAMPLE_SAMPLES), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
