# -*- coding: utf-8 -*-
"""验证三业务反馈人工确认状态机与候选生效前闸口包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_DIR = ROOT / "03数据" / "80三业务反馈人工确认状态机与候选生效前闸口包"
LOG_DIR = ROOT / "04日志" / "三业务反馈人工确认状态机与候选生效前闸口包验收"

STATE_MACHINE_JSON = DATA_DIR / "人工确认状态机定义_最新.json"
STATE_MACHINE_MD = DATA_DIR / "人工确认状态机定义_最新.md"
LOCAL_SAMPLE_JSON = DATA_DIR / "本包人工确认状态机示例候选_最新.json"
PRE_EFFECT_GATE_JSON = DATA_DIR / "候选生效前闸口定义_最新.json"
PACKAGE_JSON = DATA_DIR / "三业务反馈人工确认状态机与候选生效前闸口包_最新.json"
PREVIEW_JSON = DATA_DIR / "人工确认状态迁移预演结果_最新.json"
PREVIEW_MD = DATA_DIR / "人工确认状态迁移预演结果_最新.md"
CANDIDATE_GATE_JSON = DATA_DIR / "候选生效前闸口预演清单_最新.json"
LOG_JSON = LOG_DIR / "three-business-feedback-confirmation-state-machine-verify-最新.json"

REQUIRED_BUSINESSES = {"税收", "股票", "视频"}
REQUIRED_STATES = {"待确认", "已确认待总管复核", "驳回", "冻结", "可提交正式规则申请草案"}
REQUIRED_CANDIDATE_FIELDS = {"候选ID", "去重键", "当前状态", "允许下一状态", "阻断原因", "需总管确认"}
REQUIRED_OUTPUTS = [
    STATE_MACHINE_JSON,
    STATE_MACHINE_MD,
    LOCAL_SAMPLE_JSON,
    PRE_EFFECT_GATE_JSON,
    PACKAGE_JSON,
    PREVIEW_JSON,
    PREVIEW_MD,
    CANDIDATE_GATE_JSON,
]
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_state_machine(state_machine: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    states = {item.get("状态") for item in state_machine.get("状态集合", [])}
    if states != REQUIRED_STATES:
        errors.append("状态机状态集合必须完整覆盖：待确认、已确认待总管复核、驳回、冻结、可提交正式规则申请草案")

    transitions = state_machine.get("允许迁移", {})
    if set(transitions) != REQUIRED_STATES:
        errors.append("状态机允许迁移必须为每个状态提供定义")
    for source, transition_items in transitions.items():
        if source not in REQUIRED_STATES:
            errors.append(f"状态机存在未知来源状态：{source}")
        if not isinstance(transition_items, list) or not transition_items:
            errors.append(f"{source} 必须至少有一个允许下一状态")
            continue
        for item in transition_items:
            if item.get("目标状态") not in REQUIRED_STATES:
                errors.append(f"{source} 存在非法目标状态：{item.get('目标状态')}")

    gate = state_machine.get("全局闸口", {})
    if gate.get("自动生效") is not False:
        errors.append("状态机全局闸口必须声明自动生效=false")
    if gate.get("写正式规则") is not False:
        errors.append("状态机全局闸口必须声明写正式规则=false")
    if gate.get("需总管确认") is not True:
        errors.append("状态机全局闸口必须声明需总管确认=true")
    if gate.get("候选层停留") is not True:
        errors.append("状态机全局闸口必须声明候选层停留=true")
    return errors


def validate_candidate(candidate: dict[str, Any], valid_transitions: dict[str, list[str]]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_CANDIDATE_FIELDS - set(candidate))
    if missing:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 缺少候选字段：{', '.join(missing)}")
    if candidate.get("业务线") not in REQUIRED_BUSINESSES:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 业务线不合格")
    if candidate.get("当前状态") not in REQUIRED_STATES:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 当前状态不合格")
    allowed = candidate.get("允许下一状态")
    if not isinstance(allowed, list) or not allowed:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 允许下一状态不能为空")
    else:
        if set(allowed) != set(valid_transitions.get(candidate.get("当前状态"), [])):
            errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 允许下一状态与状态机定义不一致")
    if not candidate.get("阻断原因"):
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 阻断原因不能为空")
    if candidate.get("需总管确认") is not True:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 需总管确认必须为 true")
    if candidate.get("自动生效") is not False:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 自动生效必须为 false")
    if candidate.get("写正式规则") is not False:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 写正式规则必须为 false")
    if candidate.get("候选层停留") is not True:
        errors.append(f"{candidate.get('候选ID', 'UNKNOWN')} 必须停留候选层")
    return errors


def main() -> int:
    errors: list[str] = []
    for path in REQUIRED_OUTPUTS:
        if not path.exists():
            errors.append(f"必要产物不存在：{path}")

    state_machine = read_json(STATE_MACHINE_JSON) if STATE_MACHINE_JSON.exists() else {}
    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    gate_definition = read_json(PRE_EFFECT_GATE_JSON) if PRE_EFFECT_GATE_JSON.exists() else {}
    preview = read_json(PREVIEW_JSON) if PREVIEW_JSON.exists() else {}
    gate_list = read_json(CANDIDATE_GATE_JSON) if CANDIDATE_GATE_JSON.exists() else {}
    candidates = preview.get("候选条目", [])

    errors.extend(validate_state_machine(state_machine))

    if package.get("状态") != "three_business_feedback_confirmation_state_machine_gate_ready":
        errors.append("生成包状态不正确")
    for source_name, data in [("生成包", package), ("候选生效前闸口定义", gate_definition), ("预演结果", preview), ("闸口预演清单", gate_list)]:
        if data.get("自动生效") is not False:
            errors.append(f"{source_name} 必须声明自动生效=false")
        if data.get("写正式规则") is not False:
            errors.append(f"{source_name} 必须声明写正式规则=false")
        if data.get("需总管确认") is not True:
            errors.append(f"{source_name} 必须声明需总管确认=true")

    if preview.get("总体状态") != "pass":
        errors.append("状态迁移预演总体状态必须为 pass")
    if preview.get("错误数") != 0:
        errors.append("状态迁移预演错误数必须为 0")

    for name in FORBIDDEN_ACTIONS:
        if package.get("红线动作", {}).get(name) is not False:
            errors.append(f"红线动作 {name} 必须为 false")
        if state_machine.get("红线动作", {}).get(name) is not False:
            errors.append(f"状态机红线动作 {name} 必须为 false")

    valid_transitions = {
        source: [item.get("目标状态") for item in transition_items]
        for source, transition_items in state_machine.get("允许迁移", {}).items()
    }
    candidate_businesses = {item.get("业务线") for item in candidates}
    if candidate_businesses != REQUIRED_BUSINESSES:
        errors.append("候选必须覆盖税收/股票/视频")
    if len(candidates) < 3:
        errors.append("候选条目不得少于 3 条")
    for candidate in candidates:
        errors.extend(validate_candidate(candidate, valid_transitions))

    transition_preview = preview.get("迁移预演", [])
    if len(transition_preview) != len(candidates):
        errors.append("迁移预演条目数必须与候选条目一致")
    for item in transition_preview:
        if item.get("迁移后仍停留候选层") is not True:
            errors.append(f"{item.get('候选ID', 'UNKNOWN')} 迁移后必须仍停留候选层")
        if item.get("自动生效") is not False:
            errors.append(f"{item.get('候选ID', 'UNKNOWN')} 迁移预演自动生效必须为 false")
        if item.get("写正式规则") is not False:
            errors.append(f"{item.get('候选ID', 'UNKNOWN')} 迁移预演写正式规则必须为 false")
        if item.get("需总管确认") is not True:
            errors.append(f"{item.get('候选ID', 'UNKNOWN')} 迁移预演需总管确认必须为 true")

    report = {
        "名称": "三业务反馈人工确认状态机与候选生效前闸口包验收",
        "验收时间": now_text(),
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "错误": errors,
        "指标": {
            "覆盖三业务": candidate_businesses == REQUIRED_BUSINESSES,
            "状态机完整": not validate_state_machine(state_machine),
            "自动生效全部为false": all(item.get("自动生效") is False for item in candidates) and preview.get("自动生效") is False,
            "写正式规则全部为false": all(item.get("写正式规则") is False for item in candidates) and preview.get("写正式规则") is False,
            "需总管确认全部为true": all(item.get("需总管确认") is True for item in candidates) and preview.get("需总管确认") is True,
            "预演错误数": preview.get("错误数"),
            "候选条目数": len(candidates),
            "迁移预演条目数": len(transition_preview),
        },
        "文件": {
            "状态机定义": str(STATE_MACHINE_JSON),
            "候选生效前闸口定义": str(PRE_EFFECT_GATE_JSON),
            "状态迁移预演结果": str(PREVIEW_JSON),
            "候选生效前闸口预演清单": str(CANDIDATE_GATE_JSON),
            "验收日志": str(LOG_JSON),
        },
    }

    write_json(LOG_JSON, report)
    print(json.dumps({"通过": report["通过"], "错误数": report["错误数"], "日志": str(LOG_JSON)}, ensure_ascii=False))
    return 0 if report["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
