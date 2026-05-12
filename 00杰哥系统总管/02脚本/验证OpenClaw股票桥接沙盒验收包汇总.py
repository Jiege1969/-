# -*- coding: utf-8 -*-
"""
名称：验证OpenClaw股票桥接沙盒验收包汇总.py
作用：由00总管统一验证股票研究系统OpenClaw股票桥接沙盒验收包。
触发方式：python 验证OpenClaw股票桥接沙盒验收包汇总.py
依赖：Python标准库；02扩展系统/01股票研究系统/02脚本/验证OpenClaw股票桥接沙盒验收包.py。
所属系统：00杰哥系统总管
安全边界：只运行本地沙盒验收汇总；不调用真实OpenClaw；不调用n8n API；不导入n8n；不启用Webhook；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-28 创建OpenClaw股票桥接沙盒验收包总管验收汇总。
标识：stock-openclaw-bridge-sandbox-acceptance-package-summary-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = system_root()
    stock_verify = root / "02杰哥扩展系统" / "01股票研究系统" / "02脚本" / "验证OpenClaw股票桥接沙盒验收包.py"
    result = subprocess.run([sys.executable, str(stock_verify)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    checks = [
        {"名称": "OpenClaw股票桥接沙盒验收包验收脚本存在", "通过": stock_verify.exists(), "详情": str(stock_verify)},
        {"名称": "OpenClaw股票桥接沙盒验收包验收通过", "通过": result.returncode == 0, "详情": {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()}},
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "OpenClaw股票桥接沙盒验收包已纳入总管统一验收。" if failed == 0 else "OpenClaw股票桥接沙盒验收包总管验收存在失败项。",
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "OpenClaw股票桥接沙盒验收"
    output = output_dir / f"stock-openclaw-bridge-sandbox-acceptance-package-summary-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-openclaw-bridge-sandbox-acceptance-package-summary-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
