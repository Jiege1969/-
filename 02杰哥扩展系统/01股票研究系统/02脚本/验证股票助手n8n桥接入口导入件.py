# -*- coding: utf-8 -*-
"""
名称：验证股票助手n8n桥接入口导入件.py
作用：验证n8n桥接入口v2导入件是否保持未激活并指向股票桥接入口19302。
触发方式：python 验证股票助手n8n桥接入口导入件.py
依赖：Python标准库；生成股票助手n8n桥接入口导入件.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地导入件并写验证日志；不导入、不启用、不触发n8n；不发送企业微信；不交易。
创建修改记录：2026-04-29 创建n8n桥接入口v2导入件验证脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "03数据" / "84n8n桥接入口导入件"
LOG_DIR = ROOT / "04日志" / "n8n桥接入口导入件"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    generator = ROOT / "02脚本" / "生成股票助手n8n桥接入口导入件.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = OUTPUT_DIR / "股票助手n8n桥接入口导入件_最新.json"
    workflow = load_json(latest)
    text = json.dumps(workflow, ensure_ascii=False)
    checks = [
        {"检查项": "导入件存在", "通过": latest.exists()},
        {"检查项": "active为false", "通过": workflow.get("active") is False},
        {"检查项": "包含Webhook入口", "通过": "n8n-nodes-base.webhook" in text},
        {"检查项": "包含HTTP请求节点", "通过": "n8n-nodes-base.httpRequest" in text},
        {"检查项": "指向股票桥接入口19302", "通过": "host.docker.internal:19302/wecom/stock" in text},
        {"检查项": "危险动作关闭", "通过": "\"real_send\": false" in text.lower() and "\"auto_trade\": false" in text.lower()},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "检查结果": checks, "通过": len(checks) - len(failed), "失败": len(failed)}
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = LOG_DIR / f"stock-n8n-bridge-entry-artifact-verify-{stamp}.json"
    latest_output = LOG_DIR / "stock-n8n-bridge-entry-artifact-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
