# -*- coding: utf-8 -*-
"""生成股票线第七批统一影子验收总表。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "股票线第七批统一影子验收总表_最新.json"
MD_OUT = DATA_DIR / "股票线第七批统一影子验收总表_最新.md"
QUEUE_PATH = DATA_DIR / "股票线第七批低风险续建队列_最新.json"


CHECKS = [
    {"check_id": "AUTO7-ACCEPT-001", "name": "标准前台报告输出门禁样例验收", "result_file": "标准前台报告输出门禁样例验收结果_最新.json"},
    {"check_id": "AUTO7-ACCEPT-002", "name": "财报资金证据字段化补齐样例验收", "result_file": "财报资金证据字段化补齐样例验收结果_最新.json"},
    {"check_id": "AUTO7-ACCEPT-003", "name": "行业价格连续观测字段化补齐样例验收", "result_file": "行业价格连续观测字段化补齐样例验收结果_最新.json"},
    {"check_id": "AUTO7-ACCEPT-004", "name": "企业微信模拟问答回归验收样例验收", "result_file": "企业微信模拟问答回归验收样例验收结果_最新.json"},
    {"check_id": "AUTO7-ACCEPT-005", "name": "第七批低风险续建队列验收", "result_file": "股票线第七批低风险续建队列验收_最新.json"},
]


def load_result(file_name: str) -> dict:
    path = DATA_DIR / file_name
    if not path.exists():
        return {"exists": False, "passed": False, "errors": [f"缺少{file_name}"], "metrics": {}}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return {
        "exists": True,
        "passed": data.get("passed") is True,
        "errors": data.get("errors", []),
        "metrics": data.get("metrics", {}),
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig")) if QUEUE_PATH.exists() else {}
    records = [{**check, **load_result(check["result_file"])} for check in CHECKS]
    queue_summary = queue.get("summary", {})
    all_passed = all(item["passed"] for item in records)
    asset = {
        "name": "股票线第七批统一影子验收总表",
        "version": "v1.0",
        "generated_at": now,
        "asset_identity": "W2第七批统一影子验收总表",
        "status": "shadow_acceptance_summary",
        "purpose": "汇总第七批低风险施工资产验收状态，确认前台门禁、财报资金字段化、行业价格字段化、本地企业微信模拟问答均已形成影子闭环。",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_score_write": True,
        "not_formal_rule_update": True,
        "records": records,
        "queue_summary": queue_summary,
        "blocked_register_only": queue.get("blocked_queue", []),
        "summary": {
            "check_count": len(records),
            "exists_count": len([item for item in records if item["exists"]]),
            "passed_count": len([item for item in records if item["passed"]]),
            "failed_count": len([item for item in records if not item["passed"]]),
            "queue_completed_count": queue_summary.get("completed_count", 0),
            "queue_count": queue_summary.get("queue_count", 0),
            "allow_shadow_acceptance_claim": all_passed,
            "allow_real_wecom_send": False,
            "allow_formal_entry": False,
            "allow_formal_score_update": False,
            "allow_auto_trade": False,
        },
        "user_value": [
            "前台回答已有独立门禁，能拦住对象不明、缺口不说、后台指标堆叠和交易执行词。",
            "财报资金证据已字段化，缺口会限制前台结论和置信度。",
            "行业价格连续观测已字段化，并诚实标出价格源缺口。",
            "企业微信问答已完成本地模拟回归，仍未真实外发。",
        ],
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
            "not_order": True,
            "not_position_adjustment": True,
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第七批统一影子验收总表",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：W2第七批统一影子验收总表",
        "- 状态：shadow_acceptance_summary",
        f"- 影子验收通过：{'是' if all_passed else '否'}",
        f"- 队列完成：{queue_summary.get('completed_count', 0)}/{queue_summary.get('queue_count', 0)}",
        "- 真实系统触发：否",
        "",
        "## 验收明细",
        "",
        "| 检查项 | 文件存在 | 是否通过 |",
        "| --- | --- | --- |",
    ]
    for item in records:
        lines.append(f"| {item['name']} | {'是' if item['exists'] else '否'} | {'是' if item['passed'] else '否'} |")
    lines.extend(["", "## 对使用者的价值", ""])
    lines.extend([f"- {item}" for item in asset["user_value"]])
    lines.extend(["", "## 边界", "", "- 不接n8n。", "- 不真实发送企业微信。", "- 不改服务、19310、正式入口、正式配置、正式库。", "- 不接券商接口，不新增买卖、下单、仓位调整或自动交易能力。"])
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
