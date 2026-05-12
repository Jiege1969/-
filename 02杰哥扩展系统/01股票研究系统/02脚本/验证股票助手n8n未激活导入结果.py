# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-n8n-inactive-import-result.py
Purpose: Verify that the stock assistant workflow was imported into isolated n8n and remains inactive.
Trigger: python 验证股票助手n8n未激活导入结果.py
Dependencies: Python standard library, Docker CLI, latest inactive import log.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads isolated n8n workflow list and local logs only; does not enable, trigger, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created inactive n8n import result verifier.
Marker: stock-assistant-n8n-inactive-import-result-verify
"""

from __future__ import annotations

import json
import subprocess
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


def run(args: list[str]) -> tuple[int, str, str]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return completed.returncode, completed.stdout, completed.stderr


def main() -> int:
    root = module_root()
    latest_import = root / "04日志" / "n8n未激活导入" / "stock-assistant-n8n-inactive-import-最新.json"
    record = load_json(latest_import)
    workflow_name = record.get("工作流名称", "股票助手企业微信查询适配器未激活导入件")
    code_false, inactive_out, inactive_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"])
    code_true, active_out, active_err = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=true"])
    checks = [
        {"检查项": "导入记录存在", "通过": latest_import.exists(), "说明": str(latest_import)},
        {"检查项": "导入记录成功", "通过": record.get("是否导入成功且保持未激活") is True, "说明": str(record.get("是否导入成功且保持未激活"))},
        {"检查项": "工作流存在于未激活列表", "通过": code_false == 0 and workflow_name in inactive_out, "说明": inactive_out.strip() or inactive_err.strip()},
        {"检查项": "工作流不在激活列表", "通过": workflow_name not in active_out, "说明": active_out.strip() or active_err.strip()},
        {"检查项": "未执行真实动作", "通过": all(record.get("实际动作", {}).get(key) is False for key in ["启用n8n", "触发n8n", "写旧系统", "发送企业微信", "写正式库", "调用券商接口", "自动交易"]), "说明": str(record.get("实际动作", {}))},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检查结果": checks, "通过": len(checks) - len(failed), "失败": len(failed)}
    log_dir = root / "04日志" / "n8n未激活导入结果"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-inactive-import-result-verify-{stamp}.json"
    latest = log_dir / "stock-assistant-n8n-inactive-import-result-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
