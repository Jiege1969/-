"""
名称：生成n8n导入前审查包.py
作用：根据 n8n 工作流草案清单和导入前审查规则，生成导入候选、风险清单和回滚方案。
触发方式：python 生成n8n导入前审查包.py
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只生成本地审查包，不调用 n8n API，不导入工作流，不启用 webhook。
创建/修改记录：2026-04-26 创建 n8n 导入前审查包生成脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[3]


def config_dir() -> Path:
    return v3_root() / "01杰哥智能系统" / "01配置"


def draft_dir() -> Path:
    target = v3_root() / "01杰哥智能系统" / "03数据" / "工作流草案"
    target.mkdir(parents=True, exist_ok=True)
    return target


def review_dir() -> Path:
    target = v3_root() / "01杰哥智能系统" / "03数据" / "工作流导入审查"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_manifest() -> dict[str, Any]:
    path = draft_dir() / "n8n工作流草案清单_最新.json"
    return load_json(path)


def evaluate_draft(draft: dict[str, Any], first_batch: set[str], delayed: set[str]) -> dict[str, Any]:
    name = draft.get("名称", "")
    webhook = draft.get("Webhook草案", {})
    risks = []
    if draft.get("是否允许自动触发") is not False:
        risks.append("草案存在自动触发风险")
    if webhook.get("是否启用") is not False:
        risks.append("Webhook 未保持关闭")
    if name in delayed:
        risks.append("高风险或需业务复核，暂缓导入")
    recommendation = "建议第一批导入候选" if name in first_batch and not risks else "暂缓导入"
    return {
        "工作流名": name,
        "草案文件": draft.get("草案文件"),
        "Webhook路径": webhook.get("路径"),
        "是否允许自动触发": draft.get("是否允许自动触发"),
        "Webhook是否启用": webhook.get("是否启用"),
        "风险": risks,
        "建议": recommendation,
    }


def build_review_package() -> dict[str, Any]:
    rules = load_json(config_dir() / "n8n导入前审查规则.json")
    contract = load_json(config_dir() / "n8n接口契约.json")
    manifest = latest_manifest()
    strategy = rules.get("导入策略", {})
    first_batch = set(strategy.get("第一批建议", []))
    delayed = set(strategy.get("暂缓导入", []))
    evaluated = [evaluate_draft(item, first_batch, delayed) for item in manifest.get("工作流草案", [])]
    blockers = []
    if contract.get("执行边界", {}).get("允许真实执行") is not False:
        blockers.append("n8n 契约未关闭真实执行")
    if manifest.get("是否调用n8n") is not False:
        blockers.append("草案生成过程调用了 n8n")
    if any(item.get("是否允许自动触发") is not False for item in evaluated):
        blockers.append("存在自动触发工作流")
    if any(item.get("Webhook是否启用") is not False for item in evaluated):
        blockers.append("存在已启用 Webhook")

    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "仅审查包",
        "是否调用n8n": False,
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "规则状态": rules.get("状态"),
        "导入前必须满足": rules.get("导入前必须满足", []),
        "禁止导入条件": rules.get("禁止导入条件", []),
        "回滚方案": rules.get("回滚方案模板", {}),
        "工作流评估": evaluated,
        "阻断项": blockers,
        "第一批候选": [item for item in evaluated if item.get("建议") == "建议第一批导入候选"],
        "结论": "可进入人工审查" if not blockers else "存在阻断项，禁止导入",
    }
    output = review_dir() / f"n8n导入前审查包_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = review_dir() / "n8n导入前审查包_最新.json"
    latest.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"工作流数量": len(evaluated), "阻断项": len(blockers), "输出": str(output)}, ensure_ascii=True))
    return package


def main() -> int:
    build_review_package()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
