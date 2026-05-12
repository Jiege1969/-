# -*- coding: utf-8 -*-
"""
名称：验证股票助手n8n未激活导入执行前只读核验包汇总.py
作用：在00总管汇总验证股票助手n8n未激活导入执行前只读核验包是否通过本地验收并形成最新产物。
触发方式：python 验证股票助手n8n未激活导入执行前只读核验包汇总.py
依赖：Python标准库；02杰哥扩展系统/01股票研究系统/02脚本/验证股票助手n8n未激活导入执行前只读核验包.py。
所属系统：00杰哥系统总管
安全边界：只读取本地验收结果并写入00总管04日志；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不导入n8n；不启用n8n；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手n8n未激活导入执行前只读核验包总管汇总验收脚本。
标识：stock-assistant-n8n-inactive-import-preexecution-readonly-check-summary-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def manager_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return manager_root().parent


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    checks.append({"检查项": name, "通过": ok, "说明": detail})


def main() -> int:
    manager = manager_root()
    root = system_root()
    stock_root = root / "02杰哥扩展系统" / "01股票研究系统"
    verifier = stock_root / "02脚本" / "验证股票助手n8n未激活导入执行前只读核验包.py"
    subprocess.run([sys.executable, str(verifier)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest_verify = stock_root / "04日志" / "n8n未激活导入执行前只读核验" / "stock-assistant-n8n-inactive-import-preexecution-readonly-check-verify-最新.json"
    latest_package = stock_root / "03数据" / "64n8n未激活导入执行前只读核验" / "股票助手n8n未激活导入执行前只读核验包_最新.json"
    verify_result = load_json(latest_verify)
    package = load_json(latest_package)
    checks: list[dict[str, Any]] = []
    add_check(checks, "股票模块本地验收通过", verify_result.get("失败") == 0, str(latest_verify))
    add_check(checks, "最新核验包可读", latest_package.exists() and package.get("是否具备执行前只读核验条件") is True, str(latest_package))
    add_check(checks, "阻断条件完整", len(package.get("阻断条件", [])) >= 8, str(package.get("阻断条件", [])))

    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查结果": checks,
        "通过": len(checks) - len(failed),
        "失败": len(failed),
    }
    log_dir = manager / "04日志" / "股票n8n未激活导入执行前只读核验"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-inactive-import-preexecution-readonly-check-summary-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-n8n-inactive-import-preexecution-readonly-check-summary-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
