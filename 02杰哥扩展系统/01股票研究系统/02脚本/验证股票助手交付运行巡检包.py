# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-delivery-runtime-patrol-package.py
Purpose: Verify the read-only runtime patrol package for stock assistant delivery readiness.
Trigger: python 验证股票助手交付运行巡检包.py
Dependencies: Python standard library; delivery runtime patrol package generator.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Verifies local patrol package only; does not restart, enable, trigger Webhook, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created stock assistant delivery runtime patrol package verifier.
Marker: stock-assistant-delivery-runtime-patrol-package-verify
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
    generator = root / "02脚本" / "生成股票助手交付运行巡检包.py"
    completed = subprocess.run([sys.executable, str(generator)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    latest = root / "03数据" / "80股票助手交付运行巡检包" / "股票助手交付运行巡检包_最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    dangerous = [key for key in ["重启服务", "启用Webhook", "触发Webhook", "调用OpenClaw", "发送企业微信", "写旧系统", "写正式库", "调用券商接口", "自动交易"] if actions.get(key) is not False]
    gates = report.get("安全闸口", {})
    checks = [
        {"检查项": "生成脚本返回通过", "通过": completed.returncode == 0, "说明": completed.stdout.strip() or completed.stderr.strip()},
        {"检查项": "巡检包文件存在", "通过": latest.exists(), "说明": str(latest)},
        {"检查项": "交付使用包存在", "通过": Path(report.get("交付使用包", "")).exists(), "说明": str(report.get("交付使用包", ""))},
        {"检查项": "隔离n8n容器识别", "通过": "jiege_v3_n8n" in report.get("容器状态", {}).get("jiege_v3_n8n", {}).get("标准输出", ""), "说明": report.get("容器状态", {}).get("jiege_v3_n8n", {}).get("标准输出", "")},
        {"检查项": "旧系统保护对象识别", "通过": "jiege_n8n" in report.get("容器状态", {}).get("jiege_n8n保护对象", {}).get("标准输出", ""), "说明": report.get("容器状态", {}).get("jiege_n8n保护对象", {}).get("标准输出", "")},
        {"检查项": "安全闸口关闭", "通过": gates.get("企业微信真实发送") is False and gates.get("OpenClaw真实桥接") is False and gates.get("交易接口") is False and gates.get("旧系统写入") is False, "说明": json.dumps(gates, ensure_ascii=False)},
        {"检查项": "危险动作关闭", "通过": not dangerous, "说明": str(dangerous)}
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检查结果": checks, "通过": len(checks) - len(failed), "失败": len(failed)}
    log_dir = root / "04日志" / "股票助手交付运行巡检包"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-delivery-runtime-patrol-package-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-delivery-runtime-patrol-package-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
