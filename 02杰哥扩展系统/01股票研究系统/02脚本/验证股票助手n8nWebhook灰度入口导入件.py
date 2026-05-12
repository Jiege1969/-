# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-n8n-webhook-gray-entry-artifact.py
Purpose: Verify the inactive n8n webhook gray entry artifact for stock assistant.
Trigger: python 验证股票助手n8nWebhook灰度入口导入件.py
Dependencies: Python standard library; webhook gray entry artifact generator.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local workflow artifact and writes verification logs only; does not import, enable, trigger, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created inactive webhook gray entry artifact verifier.
Marker: stock-assistant-n8n-webhook-gray-entry-artifact-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票助手n8nWebhook灰度入口导入件.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = root / "03数据" / "74n8nWebhook灰度入口导入件" / "股票助手n8nWebhook灰度入口导入件_最新.json"
    workflow = load_json(latest)
    text = json.dumps(workflow, ensure_ascii=False)
    checks = [
        {"检查项": "导入件存在", "通过": latest.exists(), "说明": str(latest)},
        {"检查项": "active为false", "通过": workflow.get("active") is False, "说明": str(workflow.get("active"))},
        {"检查项": "包含Webhook节点", "通过": "n8n-nodes-base.webhook" in text, "说明": "需要Webhook入口"},
        {"检查项": "包含响应节点", "通过": "n8n-nodes-base.respondToWebhook" in text, "说明": "需要返回响应"},
        {"检查项": "路径固定", "通过": "jiege-stock-wework-gray" in text, "说明": "灰度路径固定"},
        {"检查项": "危险动作关闭", "通过": "\"real_send\": false" in text.lower() and "\"auto_trade\": false" in text.lower(), "说明": "真实发送和交易关闭"},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检查结果": checks, "通过": len(checks) - len(failed), "失败": len(failed)}
    log_dir = root / "04日志" / "n8nWebhook灰度入口导入件"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-webhook-gray-entry-artifact-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-n8n-webhook-gray-entry-artifact-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
