# -*- coding: utf-8 -*-
"""生成三业务反馈人工确认状态机与候选生效前闸口包。

本包只生成候选层状态机、示例候选和生效前闸口定义；不触发外部系统，
不自动生效，不写正式规则。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "80三业务反馈人工确认状态机与候选生效前闸口包"
SOURCE_77_LEDGER_JSON = ROOT / "03数据" / "77三业务反馈候选复跑去重与人工确认台账包" / "人工确认台账_最新.json"

STATE_MACHINE_JSON = DATA_DIR / "人工确认状态机定义_最新.json"
STATE_MACHINE_MD = DATA_DIR / "人工确认状态机定义_最新.md"
LOCAL_SAMPLE_JSON = DATA_DIR / "本包人工确认状态机示例候选_最新.json"
PRE_EFFECT_GATE_JSON = DATA_DIR / "候选生效前闸口定义_最新.json"
PACKAGE_JSON = DATA_DIR / "三业务反馈人工确认状态机与候选生效前闸口包_最新.json"

REQUIRED_BUSINESSES = ["税收", "股票", "视频"]
REQUIRED_STATES = ["待确认", "已确认待总管复核", "驳回", "冻结", "可提交正式规则申请草案"]
FORBIDDEN_ACTIONS = [
    "真实发送企业微信",
    "接n8n",
    "接券商",
    "交易",
    "登录税局",
    "接财税软件",
    "自动转正式规则",
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
    return re.sub(r"\s+", "", text)


def build_dedupe_key(business: str, issue_type: str, action: str) -> str:
    raw = "|".join([normalize(business), normalize(issue_type), normalize(action)])
    return "dedupe-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def build_state_machine(generated_at: str) -> dict[str, Any]:
    transitions = {
        "待确认": [
            {"目标状态": "已确认待总管复核", "触发": "人工确认通过", "闸口": "仍停留候选层，等待总管复核"},
            {"目标状态": "驳回", "触发": "人工驳回", "闸口": "候选不得生效"},
            {"目标状态": "冻结", "触发": "人工冻结", "闸口": "候选不得生效"},
        ],
        "已确认待总管复核": [
            {"目标状态": "可提交正式规则申请草案", "触发": "总管复核通过草案", "闸口": "只生成申请草案，不写正式规则"},
            {"目标状态": "驳回", "触发": "总管复核驳回", "闸口": "候选不得生效"},
            {"目标状态": "冻结", "触发": "总管复核冻结", "闸口": "候选不得生效"},
        ],
        "驳回": [
            {"目标状态": "待确认", "触发": "人工补充后重新提交", "闸口": "重新进入候选确认层"},
            {"目标状态": "冻结", "触发": "驳回后冻结", "闸口": "候选不得生效"},
        ],
        "冻结": [
            {"目标状态": "待确认", "触发": "总管解冻后重提", "闸口": "重新进入候选确认层"},
        ],
        "可提交正式规则申请草案": [
            {"目标状态": "冻结", "触发": "总管要求暂停草案", "闸口": "草案暂停，禁止自动转正式规则"},
        ],
    }
    return {
        "名称": "三业务反馈人工确认状态机定义",
        "版本": "confirmation-state-machine-v1",
        "生成时间": generated_at,
        "状态集合": [
            {"状态": "待确认", "说明": "候选等待人工确认，不能生效"},
            {"状态": "已确认待总管复核", "说明": "人工已确认，但仍需总管复核，不能生效"},
            {"状态": "驳回", "说明": "候选被驳回，不能生效"},
            {"状态": "冻结", "说明": "候选冻结，不能生效"},
            {"状态": "可提交正式规则申请草案", "说明": "只允许形成正式规则申请草案，禁止自动写正式规则"},
        ],
        "允许迁移": transitions,
        "全局闸口": {
            "候选层停留": True,
            "自动生效": False,
            "写正式规则": False,
            "需总管确认": True,
            "可提交正式规则申请草案不等于正式规则生效": True,
        },
        "覆盖业务": REQUIRED_BUSINESSES,
        "红线动作": {name: False for name in FORBIDDEN_ACTIONS},
    }


def build_gate_definition(generated_at: str) -> dict[str, Any]:
    return {
        "名称": "候选生效前闸口定义",
        "生成时间": generated_at,
        "适用业务": REQUIRED_BUSINESSES,
        "闸口结论": "所有候选必须停在候选层，正式规则申请草案也不得自动生效",
        "自动生效": False,
        "写正式规则": False,
        "需总管确认": True,
        "候选层停留": True,
        "硬性字段": {
            "自动生效": False,
            "写正式规则": False,
            "需总管确认": True,
            "候选层停留": True,
        },
        "候选必备字段": ["候选ID", "去重键", "当前状态", "允许下一状态", "阻断原因", "需总管确认"],
        "阻断原因模板": {
            "待确认": "等待人工确认，候选不得生效",
            "已确认待总管复核": "等待总管复核，候选不得生效",
            "驳回": "驳回状态，候选不得生效",
            "冻结": "冻结状态，候选不得生效",
            "可提交正式规则申请草案": "仅可提交正式规则申请草案，禁止自动写正式规则",
        },
        "红线动作": {name: False for name in FORBIDDEN_ACTIONS},
    }


def build_local_samples(generated_at: str) -> dict[str, Any]:
    samples = [
        {
            "候选ID": "CONFIRM-SEED-TAX-001",
            "业务线": "税收",
            "来源": "本包示例/税收/人工确认状态机",
            "问题类型": "口径不清",
            "建议动作": "补充资料清单和人工确认提示，仅生成候选说明。",
        },
        {
            "候选ID": "CONFIRM-SEED-STOCK-001",
            "业务线": "股票",
            "来源": "本包示例/股票/人工确认状态机",
            "问题类型": "风险提示不足",
            "建议动作": "补充风险边界和非交易建议声明，仅生成候选说明。",
        },
        {
            "候选ID": "CONFIRM-SEED-VIDEO-001",
            "业务线": "视频",
            "来源": "本包示例/视频/人工确认状态机",
            "问题类型": "分镜遗漏",
            "建议动作": "补充分镜占位和人工确认点，不触发渲染发布。",
        },
    ]
    for item in samples:
        item["去重键"] = build_dedupe_key(item["业务线"], item["问题类型"], item["建议动作"])
        item["当前状态"] = "待确认"
        item["需总管确认"] = True
        item["自动生效"] = False
        item["写正式规则"] = False
    return {
        "名称": "本包人工确认状态机示例候选",
        "生成时间": generated_at,
        "读取范围说明": "执行脚本可读取本包示例和/或第77包人工确认台账产物",
        "示例候选": samples,
    }


def build_state_machine_md(state_machine: dict[str, Any]) -> str:
    lines = [
        "# 三业务反馈人工确认状态机定义",
        "",
        f"- 版本：{state_machine['版本']}",
        f"- 生成时间：{state_machine['生成时间']}",
        "- 候选层停留：true",
        "- 自动生效：false",
        "- 写正式规则：false",
        "- 需总管确认：true",
        "",
        "## 状态集合",
        "",
    ]
    for item in state_machine["状态集合"]:
        lines.append(f"- {item['状态']}：{item['说明']}")
    lines.extend(["", "## 允许迁移", ""])
    for source, transitions in state_machine["允许迁移"].items():
        for transition in transitions:
            lines.append(f"- {source} -> {transition['目标状态']}：{transition['触发']}；{transition['闸口']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    generated_at = now_text()
    state_machine = build_state_machine(generated_at)
    gate_definition = build_gate_definition(generated_at)
    local_samples = build_local_samples(generated_at)
    package = {
        "名称": "三业务反馈人工确认状态机与候选生效前闸口包",
        "生成时间": generated_at,
        "状态": "three_business_feedback_confirmation_state_machine_gate_ready",
        "承接来源": str(SOURCE_77_LEDGER_JSON),
        "读取范围": ["本包示例", "第77包人工确认台账产物"],
        "覆盖业务": REQUIRED_BUSINESSES,
        "状态集合": REQUIRED_STATES,
        "候选层停留": True,
        "自动生效": False,
        "写正式规则": False,
        "需总管确认": True,
        "不自动转正式规则": True,
        "红线动作": {name: False for name in FORBIDDEN_ACTIONS},
        "输出文件": {
            "状态机定义JSON": str(STATE_MACHINE_JSON),
            "状态机定义Markdown": str(STATE_MACHINE_MD),
            "本包示例候选JSON": str(LOCAL_SAMPLE_JSON),
            "候选生效前闸口定义JSON": str(PRE_EFFECT_GATE_JSON),
            "总包JSON": str(PACKAGE_JSON),
        },
    }

    write_json(STATE_MACHINE_JSON, state_machine)
    write_text(STATE_MACHINE_MD, build_state_machine_md(state_machine))
    write_json(LOCAL_SAMPLE_JSON, local_samples)
    write_json(PRE_EFFECT_GATE_JSON, gate_definition)
    write_json(PACKAGE_JSON, package)

    print(json.dumps({"状态": package["状态"], "状态数": len(REQUIRED_STATES), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
