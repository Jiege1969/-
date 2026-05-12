# -*- coding: utf-8 -*-
"""
名称：验证重点关注池候选池.py
作用：验证重点关注池候选池生成链路可运行，且不越权到L4或交易动作。
触发方式：python 验证重点关注池候选池.py
依赖：Python标准库；生成重点关注池候选池.py；候选池生成规则.json；重点关注池技术指标_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地候选池生成；不调用大模型；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建重点关注池候选池验收脚本。
标识：stock-focus-candidate-pool-verify
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
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成重点关注池候选池.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report = load_json(root / "03数据" / "14候选池" / "重点关注池候选池_最新.json")
    pool = report.get("候选池", {})
    all_items = pool.get("L5深度研究", []) + pool.get("L6轻度关注", []) + pool.get("L7系统过滤", [])
    checks: list[dict[str, Any]] = []
    add_check(checks, "候选池脚本运行成功", result.returncode == 0, result.stdout.strip())
    add_check(checks, "候选池覆盖重点关注池", report.get("股票数量", 0) >= 19, report.get("股票数量"))
    add_check(checks, "每只股票有评分和层级", all("系统评分" in item and "层级" in item for item in all_items), all_items[:3])
    add_check(checks, "L5动作不自动升级L4", all("不自动升级L4" in item.get("动作", "") for item in pool.get("L5深度研究", [])), pool.get("L5深度研究", []))
    add_check(checks, "真实动作关闭", all(item is False for item in report.get("安全边界", {}).values()), report.get("安全边界", {}))
    add_check(checks, "候选报告已生成", (root / "03数据" / "03研究报告" / "重点关注池候选池报告_最新.md").exists(), "重点关注池候选池报告_最新.md")
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "重点关注池候选池生成链路可运行。" if failed == 0 else "重点关注池候选池生成链路存在失败项。",
    }
    output_dir = root / "04日志" / "候选池"
    output = output_dir / f"stock-focus-candidate-pool-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-focus-candidate-pool-verify-最新.json"
    write_json(output, verify_report)
    write_json(latest, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
