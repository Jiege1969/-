# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-n8n-inactive-import-artifact.py
Purpose: Verify the sanitized active=false n8n workflow artifact before import.
Trigger: python 验证股票助手n8n未激活导入件.py
Dependencies: Python standard library; inactive import artifact generator.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local workflow artifact and writes verification logs only; does not import, enable, trigger, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created inactive n8n import artifact verifier.
Marker: stock-assistant-n8n-inactive-import-artifact-verify
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
    generator = root / "02脚本" / "生成股票助手n8n未激活导入件.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = root / "03数据" / "69n8n未激活导入件" / "股票助手n8n未激活导入件_最新.json"
    workflow = load_json(latest)
    text = json.dumps(workflow, ensure_ascii=False)
    checks = [
        {"检查项": "导入件存在", "通过": latest.exists(), "说明": str(latest)},
        {"检查项": "active为false", "通过": workflow.get("active") is False, "说明": str(workflow.get("active"))},
        {"检查项": "节点数量完整", "通过": len(workflow.get("nodes", [])) >= 4, "说明": str(len(workflow.get("nodes", [])))},
        {"检查项": "连接存在", "通过": bool(workflow.get("connections")), "说明": str(workflow.get("connections", {}))},
        {"检查项": "无企业微信真实发送", "通过": "corpsecret" not in text.lower() and "access_token" not in text.lower(), "说明": "未包含企业微信凭据"},
        {"检查项": "无券商交易接口", "通过": "broker_api\": true" not in text.lower() and "auto_trade\": true" not in text.lower() and "trade': true" not in text.lower(), "说明": "未包含券商交易调用"},
        {"检查项": "标记必须保持未激活", "通过": workflow.get("meta", {}).get("must_remain_inactive") is True, "说明": str(workflow.get("meta", {}))},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检查结果": checks, "通过": len(checks) - len(failed), "失败": len(failed)}
    log_dir = root / "04日志" / "n8n未激活导入件"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-inactive-import-artifact-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-n8n-inactive-import-artifact-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
