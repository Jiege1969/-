# -*- coding: utf-8 -*-
"""生成股票线第三批统一影子验收总表。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "股票线第三批统一影子验收总表_最新.json"
MD_OUT = DATA_DIR / "股票线第三批统一影子验收总表_最新.md"
QUEUE_PATH = DATA_DIR / "股票线第三批低风险续建队列_最新.json"


CHECKS = [
    {
        "check_id": "AUTO3-ACCEPT-001",
        "name": "股票提问对象识别与别名映射验收",
        "result_file": "股票提问对象识别与别名映射验收结果_最新.json",
    },
    {
        "check_id": "AUTO3-ACCEPT-002",
        "name": "企业微信前台短答模拟输入输出样例验收",
        "result_file": "企业微信前台短答模拟输入输出样例验收结果_最新.json",
    },
    {
        "check_id": "AUTO3-ACCEPT-003",
        "name": "置信度上限与缺口联动矩阵验收",
        "result_file": "置信度上限与缺口联动矩阵验收结果_最新.json",
    },
    {
        "check_id": "AUTO3-ACCEPT-004",
        "name": "下一次复核日期与复核重点模板验收",
        "result_file": "下一次复核日期与复核重点模板验收结果_最新.json",
    },
    {
        "check_id": "AUTO3-ACCEPT-005",
        "name": "第三批低风险续建队列验收",
        "result_file": "股票线第三批低风险续建队列验收_最新.json",
    },
]


def load_result(file_name: str) -> dict:
    path = DATA_DIR / file_name
    if not path.exists():
        return {"exists": False, "passed": False, "errors": [f"缺少{file_name}"]}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return {
        "exists": True,
        "passed": data.get("passed") is True,
        "errors": data.get("errors", []),
        "metrics": data.get("metrics", {}),
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8-sig")) if QUEUE_PATH.exists() else {}
    records = []
    for check in CHECKS:
        result = load_result(check["result_file"])
        records.append({**check, **result})
    asset = {
        "name": "股票线第三批统一影子验收总表",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W2第三批统一影子验收总表",
        "status": "shadow_acceptance_summary",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_score_write": True,
        "records": records,
        "queue_summary": queue.get("summary", {}),
        "summary": {
            "check_count": len(records),
            "exists_count": len([item for item in records if item["exists"]]),
            "passed_count": len([item for item in records if item["passed"]]),
            "failed_count": len([item for item in records if not item["passed"]]),
            "allow_shadow_acceptance_claim": all(item["passed"] for item in records),
            "allow_real_wecom_send": False,
            "allow_formal_entry": False,
            "allow_formal_score_update": False,
        },
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
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票线第三批统一影子验收总表",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W2第三批统一影子验收总表",
        "- 状态：shadow_acceptance_summary",
        f"- 验收通过：{'是' if asset['summary']['allow_shadow_acceptance_claim'] else '否'}",
        f"- 队列完成：{asset['queue_summary'].get('completed_count', 0)}/{asset['queue_summary'].get('queue_count', 0)}",
        "",
        "| 检查项 | 文件存在 | 是否通过 |",
        "| --- | --- | --- |",
    ]
    for item in records:
        lines.append(f"| {item['name']} | {'是' if item['exists'] else '否'} | {'是' if item['passed'] else '否'} |")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
