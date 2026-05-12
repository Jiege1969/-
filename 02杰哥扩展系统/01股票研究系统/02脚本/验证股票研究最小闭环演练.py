# -*- coding: utf-8 -*-
"""
名称：验证股票研究最小闭环演练.py
作用：验证股票研究最小闭环演练已经形成可验收结果，作为D盘旧系统退役前置检查之一。
触发方式：python 验证股票研究最小闭环演练.py
依赖：Python标准库；运行股票研究最小闭环演练.py；股票研究最小闭环演练日志。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读闭环演练日志和输出文件；不触发n8n；不发送企业微信；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-30 创建股票研究最小闭环演练验收脚本。
标识：stock-minimal-review-loop-verify
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = module_root()
    latest = root / "04日志" / "股票研究最小闭环演练" / "stock-minimal-review-loop-run-最新.json"
    report = load_json(latest)
    checks = [
        {"名称": "闭环演练日志存在", "通过": bool(report), "详情": str(latest)},
        {"名称": "闭环演练无失败项", "通过": report.get("失败") == 0, "详情": report.get("失败")},
        {"名称": "执行结果不少于七步", "通过": len(report.get("执行结果", [])) >= 7, "详情": len(report.get("执行结果", []))},
        {"名称": "验收文件全部存在", "通过": all(item.get("存在") for item in report.get("验收文件", [])), "详情": report.get("验收文件", [])},
        {"名称": "高风险动作关闭", "通过": all(value is False for value in report.get("安全边界", {}).values()), "详情": report.get("安全边界", {})},
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票研究最小闭环演练验收通过。" if failed == 0 else "股票研究最小闭环演练验收未通过。",
    }
    output_dir = root / "04日志" / "股票研究最小闭环演练"
    output = output_dir / f"stock-minimal-review-loop-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    write_json(output, verify)
    write_json(output_dir / "stock-minimal-review-loop-verify-最新.json", verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
