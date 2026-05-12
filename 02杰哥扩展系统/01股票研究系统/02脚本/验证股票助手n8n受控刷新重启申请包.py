# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-n8n-controlled-refresh-restart-request-package.py
Purpose: Verify the controlled refresh/restart request package for isolated n8n webhook registration.
Trigger: python 验证股票助手n8n受控刷新重启申请包.py
Dependencies: Python standard library; controlled refresh/restart request package generator.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local request reports and writes verification logs only; does not restart, enable, trigger, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created controlled refresh/restart request package verifier.
Marker: stock-assistant-n8n-controlled-refresh-restart-request-package-verify
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
    generator = root / "02脚本" / "生成股票助手n8n受控刷新重启申请包.py"
    completed = subprocess.run([sys.executable, str(generator)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    latest = root / "03数据" / "76n8n受控刷新重启申请" / "股票助手n8n受控刷新重启申请包_最新.json"
    report = load_json(latest)
    actions = report.get("实际动作", {})
    dangerous = [key for key in ["重启n8n", "启用Webhook", "触发Webhook", "调用OpenClaw", "发送企业微信", "写旧系统", "写正式库", "调用券商接口", "自动交易"] if actions.get(key) is not False]
    checks = [
        {"检查项": "申请包存在", "通过": latest.exists(), "说明": str(latest)},
        {"检查项": "生成脚本返回通过", "通过": completed.returncode == 0, "说明": completed.stdout.strip() or completed.stderr.strip()},
        {"检查项": "具备申请条件", "通过": report.get("是否具备申请条件") is True, "说明": str(report.get("是否具备申请条件"))},
        {"检查项": "未执行重启", "通过": report.get("是否已执行重启") is False, "说明": str(report.get("是否已执行重启"))},
        {"检查项": "回滚策略完整", "通过": len(report.get("回滚策略", [])) >= 4, "说明": str(report.get("回滚策略", []))},
        {"检查项": "验收标准完整", "通过": len(report.get("验收标准", [])) >= 6, "说明": str(report.get("验收标准", []))},
        {"检查项": "危险动作关闭", "通过": not dangerous, "说明": str(dangerous)},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检查结果": checks, "通过": len(checks) - len(failed), "失败": len(failed)}
    log_dir = root / "04日志" / "n8n受控刷新重启申请"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-controlled-refresh-restart-request-package-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-n8n-controlled-refresh-restart-request-package-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
