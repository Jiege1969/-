# -*- coding: utf-8 -*-
"""
Name: 执行六层规则体系治理内核只读检查.py
System: 00杰哥系统总管 / 02脚本
Purpose: 只读检查六层规则体系与治理内核是否已固化为总管规则、文档、进化原则和运行状态证据。
Trigger: 手动执行；后续可接入总管只读巡检。
Dependencies: 系统底层逻辑.md；六层规则体系与治理内核规则.json；治理闭环与先例库使用原则_v1.0.md。
Output: 00杰哥系统总管/03数据/运行状态/六层规则体系治理内核只读检查_最新.json。
Safety: 不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不修改业务规则生效开关。
ChangeLog: 2026-05-10 created; 2026-05-10 switched to JSON-only truth source.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
EVOLUTION = ROOT / "03杰哥进化系统"

RULE_PATH = MANAGER / "01配置" / "六层规则体系与治理内核规则.json"
BOTTOM_LOGIC_PATH = MANAGER / "系统底层逻辑.md"
COMMON_PRINCIPLE_PATH = EVOLUTION / "规则库" / "搭建与施工规范_完整版.md"
DOC_PATH = MANAGER / "07文档" / "杰哥智能化系统六层规则体系与治理内核_v1.0.md"
EVOLUTION_RULE_PATH = EVOLUTION / "规则库" / "治理闭环与先例库使用原则_v1.0.md"
SCRIPT_PATH = MANAGER / "02脚本" / "执行六层规则体系治理内核只读检查.py"
STATE_DIR = MANAGER / "03数据" / "运行状态"
JSON_OUT = STATE_DIR / "六层规则体系治理内核只读检查_最新.json"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def file_status(path: Path) -> dict:
    exists = path.exists()
    item = {
        "路径": str(path),
        "存在": exists,
        "大小": path.stat().st_size if exists else 0,
        "最后修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if exists else None,
    }
    return item


def main() -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    required_files = [BOTTOM_LOGIC_PATH, COMMON_PRINCIPLE_PATH, RULE_PATH, DOC_PATH, EVOLUTION_RULE_PATH, SCRIPT_PATH]
    statuses = [file_status(path) for path in required_files]

    rule = read_json(RULE_PATH) if RULE_PATH.exists() else {}
    layer_names = [item.get("名称") for item in rule.get("六层定义", [])]
    expected_layers = ["底层逻辑", "通用原则", "系统规则", "子系统规则", "流程脚本", "命令动作"]
    layer_ok = layer_names == expected_layers

    capabilities = rule.get("治理内核能力", {})
    expected_capabilities = ["施工门禁器", "治理闭环器", "遗产先例库", "规则血缘追踪", "总管裁决"]
    capability_ok = all(name in capabilities for name in expected_capabilities)

    collected_rule_statuses = []
    for item in rule.get("首批收编规则", []):
        collected_rule_statuses.append({
            "层级": item.get("层级"),
            "文件": item.get("文件"),
            "收编方式": item.get("收编方式"),
            "存在": Path(item.get("文件", "")).exists(),
        })

    safety = rule.get("执行边界", {})
    safety_ok = all([
        safety.get("本规则创建本身不触发n8n") is True,
        safety.get("本规则创建本身不发送企业微信") is True,
        safety.get("本规则创建本身不调用券商接口") is True,
        safety.get("本规则创建本身不自动交易") is True,
        safety.get("本规则创建本身不修改业务规则生效开关") is True,
    ])

    status = "通过" if all(s["存在"] for s in statuses) and layer_ok and capability_ok and safety_ok else "需复核"
    result = {
        "名称": "六层规则体系治理内核只读检查",
        "检查时间": now,
        "状态": status,
        "六层顺序": layer_names,
        "六层顺序正确": layer_ok,
        "治理内核能力": list(capabilities.keys()),
        "治理内核能力完整": capability_ok,
        "配套文件": statuses,
        "首批收编规则": collected_rule_statuses,
        "安全边界确认": {
            "不触发n8n": safety.get("本规则创建本身不触发n8n") is True,
            "不发送企业微信": safety.get("本规则创建本身不发送企业微信") is True,
            "不调用券商接口": safety.get("本规则创建本身不调用券商接口") is True,
            "不自动交易": safety.get("本规则创建本身不自动交易") is True,
            "不修改业务规则生效开关": safety.get("本规则创建本身不修改业务规则生效开关") is True,
            "整体通过": safety_ok,
        },
        "唯一入口确认": {
            "底层逻辑入口": str(BOTTOM_LOGIC_PATH),
            "底层逻辑存在": BOTTOM_LOGIC_PATH.exists(),
            "通用原则入口": str(COMMON_PRINCIPLE_PATH),
            "通用原则存在": COMMON_PRINCIPLE_PATH.exists(),
        },
        "下一步建议": [
            "把施工门禁器脚本化为统一入口。",
            "建立遗产先例库结构化台账。",
            "给关键脚本补规则血缘字段。",
            "让进化系统定期输出治理闭环草案，不直接改生产规则。"
        ],
    }

    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
