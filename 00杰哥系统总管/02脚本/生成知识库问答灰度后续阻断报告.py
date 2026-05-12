# -*- coding: utf-8 -*-
"""
名称：生成知识库问答灰度后续阻断报告.py
作用：在灰度材料收口后，列出继续推进知识库问答灰度前必须人工许可的阻断项。
触发方式：python 生成知识库问答灰度后续阻断报告.py
安全边界：只读灰度材料和队列产物并写阻断报告；不填写确认单、不填样本、不放行灰度、不接正式入口、不创建影子入口配置、不调用企业微信、不触发n8n、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "知识库问答灰度后续阻断报告_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度后续阻断报告_最新.md"

MATERIAL_CLOSURE_JSON = OUT_DIR / "知识库问答灰度材料收口包_最新.json"
MATERIAL_CLOSURE_VALIDATION = OUT_DIR / "知识库问答灰度材料收口包验收_最新.json"
CONFIRMATION_TEMPLATE = OUT_DIR / "知识库问答入口人工确认单模板_最新.json"
SAMPLE_TEMPLATE = OUT_DIR / "知识库问答灰度样本清单影子模板_最新.json"
SAMPLE_PRECHECK = OUT_DIR / "知识库问答灰度样本填写预检_最新.json"
TOTAL_GATE = OUT_DIR / "知识库问答灰度总闸门影子验收_最新.json"
QUEUE_JSON = OUT_DIR / "无干扰自动施工队列_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_state(path: Path) -> dict[str, Any]:
    return {"路径": str(path), "存在": path.exists()}


def main() -> int:
    closure = load_json(MATERIAL_CLOSURE_JSON)
    closure_validation = load_json(MATERIAL_CLOSURE_VALIDATION)
    confirmation = load_json(CONFIRMATION_TEMPLATE)
    sample_template = load_json(SAMPLE_TEMPLATE)
    sample_precheck = load_json(SAMPLE_PRECHECK)
    total_gate = load_json(TOTAL_GATE)
    queue = load_json(QUEUE_JSON)

    materials_passed = (
        closure.get("结论") == "通过"
        and closure_validation.get("结论") == "通过"
        and int(closure.get("材料失败数量", 1)) == 0
        and int(closure_validation.get("失败数量", 1)) == 0
    )
    confirmation_state = confirmation.get("默认状态") or confirmation.get("模板默认状态") or "未确认，禁止灰度"
    sample_count = int(sample_template.get("当前真实样本数量", sample_precheck.get("当前样本数量", 0)) or 0)
    total_gate_conclusion = total_gate.get("闸门结论", total_gate.get("结论", ""))

    blockers = [
        {
            "编号": "B001",
            "阻断项": "人工确认单未填写",
            "当前状态": confirmation_state,
            "解除条件": "用户明确填写并确认知识库问答灰度人工确认单。",
            "自动解除": False,
        },
        {
            "编号": "B002",
            "阻断项": "真实灰度样本未填写",
            "当前状态": f"当前真实样本数量 {sample_count}",
            "解除条件": "人工填写受控灰度样本，并通过样本填写预检。",
            "自动解除": False,
        },
        {
            "编号": "B003",
            "阻断项": "未获得用户明确灰度许可",
            "当前状态": "无许可记录",
            "解除条件": "用户在后续施工中明确授权灰度范围、样本和回滚边界。",
            "自动解除": False,
        },
        {
            "编号": "B004",
            "阻断项": "未创建影子入口配置",
            "当前状态": "未创建，且本轮禁止创建",
            "解除条件": "另行获准后只能先创建影子配置，仍不得替换正式入口。",
            "自动解除": False,
        },
        {
            "编号": "B005",
            "阻断项": "正式入口接入仍属于必须停下报告项",
            "当前状态": "阻断",
            "解除条件": "完成影子灰度、回滚验收和用户显式放行后，另行停下报告。",
            "自动解除": False,
        },
    ]

    prohibited_actions = [
        "不得填写人工确认单",
        "不得填入真实灰度样本",
        "不得放行灰度",
        "不得创建影子入口配置",
        "不得接入或替换正式入口",
        "不得调用企业微信接口或真实发送企业微信",
        "不得触发 Webhook 或 n8n",
        "不得启动知识库问答批量任务或模型推理",
        "不得写 Qdrant/PostgreSQL/正式知识库",
        "不得调用券商接口、资金账户、下单或自动交易",
    ]
    next_low_risk = [
        "继续刷新队列状态和阻断原因。",
        "只读检查确认单模板、样本模板和回滚模板是否仍可追踪。",
        "如用户明确授权，下一轮也只能先生成灰度许可接收清单，不直接放行。",
    ]
    safety = {
        "填写人工确认单": False,
        "填入真实样本": False,
        "放行灰度": False,
        "创建影子入口配置": False,
        "接入正式入口": False,
        "调用企业微信接口": False,
        "真实发送企业微信": False,
        "触发Webhook": False,
        "触发n8n": False,
        "启动问答": False,
        "调用模型推理": False,
        "写正式知识库": False,
        "写Qdrant": False,
        "写PostgreSQL": False,
        "调用券商接口": False,
        "自动交易": False,
        "自动放行": False,
    }
    report = {
        "名称": "知识库问答灰度后续阻断报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if materials_passed else "前置材料缺口",
        "阻断结论": "后续灰度继续阻断，不允许自动放行",
        "前置材料收口通过": materials_passed,
        "总闸门结论": total_gate_conclusion,
        "队列建议执行": queue.get("本轮建议执行", {}).get("任务", ""),
        "前置材料": {
            "材料收口包": file_state(MATERIAL_CLOSURE_JSON),
            "材料收口包验收": file_state(MATERIAL_CLOSURE_VALIDATION),
            "人工确认单模板": file_state(CONFIRMATION_TEMPLATE),
            "灰度样本清单影子模板": file_state(SAMPLE_TEMPLATE),
            "灰度样本填写预检": file_state(SAMPLE_PRECHECK),
            "灰度总闸门影子验收": file_state(TOTAL_GATE),
        },
        "必须人工许可阻断项": blockers,
        "禁止动作": prohibited_actions,
        "后续低风险候选": next_low_risk,
        "安全边界": safety,
    }

    lines = [
        "# 知识库问答灰度后续阻断报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 阻断结论：{report['阻断结论']}",
        f"- 前置材料收口通过：{report['前置材料收口通过']}",
        f"- 总闸门结论：{report['总闸门结论']}",
        "",
        "## 必须人工许可阻断项",
        "",
    ]
    for item in blockers:
        lines.append(f"- {item['编号']} {item['阻断项']}：{item['当前状态']}；解除条件：{item['解除条件']}；自动解除：{item['自动解除']}")
    lines.extend(["", "## 禁止动作", ""])
    for item in prohibited_actions:
        lines.append(f"- {item}")
    lines.extend(["", "## 后续低风险候选", ""])
    for item in next_low_risk:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只生成后续阻断报告，不填写确认单，不填真实样本，不放行灰度，不接入正式入口，不调用企业微信，不触发 Webhook/n8n，不写库。")

    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "阻断项数量": len(blockers), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if materials_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
