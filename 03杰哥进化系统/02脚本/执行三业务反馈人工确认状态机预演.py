# -*- coding: utf-8 -*-
"""执行三业务反馈人工确认状态机预演。

只读取本包状态机/示例和第77包人工确认台账产物，生成候选层状态迁移
预演；所有迁移均停在候选层，不自动生效，不写正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "80三业务反馈人工确认状态机与候选生效前闸口包"
SOURCE_77_LEDGER_JSON = ROOT / "03数据" / "77三业务反馈候选复跑去重与人工确认台账包" / "人工确认台账_最新.json"

STATE_MACHINE_JSON = DATA_DIR / "人工确认状态机定义_最新.json"
LOCAL_SAMPLE_JSON = DATA_DIR / "本包人工确认状态机示例候选_最新.json"
PACKAGE_JSON = DATA_DIR / "三业务反馈人工确认状态机与候选生效前闸口包_最新.json"
PREVIEW_JSON = DATA_DIR / "人工确认状态迁移预演结果_最新.json"
PREVIEW_MD = DATA_DIR / "人工确认状态迁移预演结果_最新.md"
CANDIDATE_GATE_JSON = DATA_DIR / "候选生效前闸口预演清单_最新.json"

REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
REQUIRED_STATES = ["待确认", "已确认待总管复核", "驳回", "冻结", "可提交正式规则申请草案"]


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


def allowed_next(state_machine: dict[str, Any], state: str) -> list[str]:
    return [item["目标状态"] for item in state_machine.get("允许迁移", {}).get(state, [])]


def block_reason(state: str) -> str:
    reasons = {
        "待确认": "等待人工确认，候选不得生效",
        "已确认待总管复核": "等待总管复核，候选不得生效",
        "驳回": "驳回状态，候选不得生效",
        "冻结": "冻结状态，候选不得生效",
        "可提交正式规则申请草案": "仅可提交正式规则申请草案，禁止自动写正式规则",
    }
    return reasons[state]


def load_source_candidates(errors: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    read_files: list[str] = []
    candidates: list[dict[str, Any]] = []
    if SOURCE_77_LEDGER_JSON.exists():
        ledger = read_json(SOURCE_77_LEDGER_JSON)
        read_files.append(str(SOURCE_77_LEDGER_JSON))
        for item in ledger.get("台账条目", []):
            candidates.append(
                {
                    "候选ID": item.get("候选ID"),
                    "去重键": item.get("去重键"),
                    "业务线": item.get("业务线"),
                    "来源": item.get("来源"),
                    "问题类型": item.get("问题类型"),
                    "建议动作": item.get("建议动作"),
                    "来源台账ID": item.get("台账ID"),
                    "来源台账状态": item.get("台账状态"),
                    "来源文件": str(SOURCE_77_LEDGER_JSON),
                }
            )
    elif LOCAL_SAMPLE_JSON.exists():
        local_sample = read_json(LOCAL_SAMPLE_JSON)
        read_files.append(str(LOCAL_SAMPLE_JSON))
        for item in local_sample.get("示例候选", []):
            candidates.append(
                {
                    "候选ID": item.get("候选ID"),
                    "去重键": item.get("去重键"),
                    "业务线": item.get("业务线"),
                    "来源": item.get("来源"),
                    "问题类型": item.get("问题类型"),
                    "建议动作": item.get("建议动作"),
                    "来源台账ID": "",
                    "来源台账状态": item.get("当前状态", "待确认"),
                    "来源文件": str(LOCAL_SAMPLE_JSON),
                }
            )
    else:
        errors.append("缺少第77包台账产物和本包示例候选，无法预演")
    return candidates, read_files


def validate_source_candidate(item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ["候选ID", "去重键", "业务线", "来源", "问题类型", "建议动作"]:
        if not item.get(field):
            errors.append(f"{item.get('候选ID', 'UNKNOWN')} 缺少字段：{field}")
    if item.get("业务线") not in REQUIRED_BUSINESSES:
        errors.append(f"{item.get('候选ID', 'UNKNOWN')} 业务线不在税收/股票/视频范围")
    return errors


def build_candidate_items(candidates: list[dict[str, Any]], state_machine: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, source in enumerate(candidates):
        current_state = REQUIRED_STATES[index % len(REQUIRED_STATES)]
        next_states = allowed_next(state_machine, current_state)
        items.append(
            {
                "候选ID": source["候选ID"],
                "去重键": source["去重键"],
                "业务线": source["业务线"],
                "来源": source["来源"],
                "问题类型": source["问题类型"],
                "建议动作": source["建议动作"],
                "来源台账ID": source.get("来源台账ID", ""),
                "来源台账状态": source.get("来源台账状态", ""),
                "当前状态": current_state,
                "允许下一状态": next_states,
                "阻断原因": block_reason(current_state),
                "需总管确认": True,
                "自动生效": False,
                "写正式规则": False,
                "候选层停留": True,
                "正式规则申请草案": current_state == "可提交正式规则申请草案",
            }
        )
    return items


def build_transition_preview(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    preview: list[dict[str, Any]] = []
    for item in items:
        next_states = item["允许下一状态"]
        target_state = next_states[0] if next_states else item["当前状态"]
        preview.append(
            {
                "候选ID": item["候选ID"],
                "业务线": item["业务线"],
                "预演前状态": item["当前状态"],
                "预演目标状态": target_state,
                "迁移是否允许": target_state in next_states,
                "迁移后仍停留候选层": True,
                "自动生效": False,
                "写正式规则": False,
                "需总管确认": True,
                "阻断原因": item["阻断原因"],
            }
        )
    return preview


def build_preview_md(report: dict[str, Any]) -> str:
    lines = [
        "# 人工确认状态迁移预演结果",
        "",
        f"- 预演时间：{report['预演时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 错误数：{report['错误数']}",
        "- 自动生效：false",
        "- 写正式规则：false",
        "- 需总管确认：true",
        "",
        "| 候选ID | 业务线 | 当前状态 | 允许下一状态 | 阻断原因 | 需总管确认 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["候选条目"]:
        lines.append(
            f"| {item['候选ID']} | {item['业务线']} | {item['当前状态']} | "
            f"{'、'.join(item['允许下一状态'])} | {item['阻断原因']} | {str(item['需总管确认']).lower()} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    errors: list[str] = []
    if not STATE_MACHINE_JSON.exists():
        errors.append(f"状态机定义不存在：{STATE_MACHINE_JSON}")
        state_machine: dict[str, Any] = {}
    else:
        state_machine = read_json(STATE_MACHINE_JSON)

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    if package.get("状态") != "three_business_feedback_confirmation_state_machine_gate_ready":
        errors.append("第80包生成状态不正确或未生成")
    if package.get("自动生效") is not False:
        errors.append("总包必须声明自动生效=false")
    if package.get("写正式规则") is not False:
        errors.append("总包必须声明写正式规则=false")
    if package.get("需总管确认") is not True:
        errors.append("总包必须声明需总管确认=true")

    source_candidates, read_files = load_source_candidates(errors)
    for item in source_candidates:
        errors.extend(validate_source_candidate(item))

    candidate_items = build_candidate_items(source_candidates, state_machine) if not errors else []
    candidate_businesses = {item.get("业务线") for item in candidate_items}
    if candidate_businesses != REQUIRED_BUSINESSES:
        errors.append("候选必须覆盖税收/股票/视频三业务")

    transition_preview = build_transition_preview(candidate_items)
    generated_at = now_text()
    report = {
        "名称": "三业务反馈人工确认状态迁移预演结果",
        "预演时间": generated_at,
        "总体状态": "pass" if not errors else "fail",
        "错误数": len(errors),
        "错误": errors,
        "读取文件": read_files + [str(STATE_MACHINE_JSON), str(PACKAGE_JSON)],
        "覆盖业务": sorted(candidate_businesses),
        "状态集合": REQUIRED_STATES,
        "候选层停留": True,
        "自动生效": False,
        "写正式规则": False,
        "需总管确认": True,
        "候选条目": candidate_items,
        "迁移预演": transition_preview,
        "汇总": {
            "候选数": len(candidate_items),
            "业务数": len(candidate_businesses),
            "候选层停留数": sum(1 for item in candidate_items if item.get("候选层停留") is True),
            "自动生效数": sum(1 for item in candidate_items if item.get("自动生效") is True),
            "写正式规则数": sum(1 for item in candidate_items if item.get("写正式规则") is True),
            "需总管确认数": sum(1 for item in candidate_items if item.get("需总管确认") is True),
            "错误数": len(errors),
        },
        "输出文件": {
            "状态迁移预演JSON": str(PREVIEW_JSON),
            "状态迁移预演Markdown": str(PREVIEW_MD),
            "候选生效前闸口预演清单": str(CANDIDATE_GATE_JSON),
        },
    }
    gate_list = {
        "名称": "候选生效前闸口预演清单",
        "生成时间": generated_at,
        "自动生效": False,
        "写正式规则": False,
        "需总管确认": True,
        "候选层停留": True,
        "候选条目": candidate_items,
    }

    write_json(PREVIEW_JSON, report)
    write_text(PREVIEW_MD, build_preview_md(report))
    write_json(CANDIDATE_GATE_JSON, gate_list)

    print(json.dumps({"总体状态": report["总体状态"], "错误数": report["错误数"], "候选数": len(candidate_items), "输出": str(PREVIEW_JSON)}, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
