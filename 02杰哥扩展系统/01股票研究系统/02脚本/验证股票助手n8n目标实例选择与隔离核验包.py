# -*- coding: utf-8 -*-
"""
Name: verify-stock-assistant-n8n-target-isolation-package.py
Purpose: Verify the readonly n8n target selection and isolation package for the stock assistant.
Trigger: python 验证股票助手n8n目标实例选择与隔离核验包.py
Dependencies: Python standard library; generator script for stock assistant n8n target isolation package.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Reads local reports and writes verification logs only; does not import, enable, trigger, restart, send, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created the first readonly n8n target isolation package verifier.
Marker: stock-assistant-n8n-target-isolation-package-verify
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


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    checks.append({"检查项": name, "通过": ok, "说明": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票助手n8n目标实例选择与隔离核验包.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = root / "03数据" / "66n8n目标实例选择与隔离核验" / "股票助手n8n目标实例选择与隔离核验包_最新.json"
    report = load_json(latest)
    candidates = report.get("候选实例判定", [])
    actions = report.get("实际动作", {})
    checks: list[dict[str, Any]] = []

    old_protected = [item for item in candidates if item.get("判定") == "旧系统保护实例"]
    unsafe_selected_old = any(item.get("判定") == "旧系统保护实例" and item.get("可作为导入目标") for item in candidates)
    selected = report.get("选定目标", "")
    safe = report.get("是否具备安全导入目标") is True

    add_check(checks, "最新核验包存在", latest.exists(), str(latest))
    add_check(checks, "Docker只读查询完成", report.get("Docker只读查询成功") is True, str(report.get("Docker只读查询错误", "")))
    add_check(checks, "至少识别到n8n候选", report.get("候选实例数量", 0) >= 1, str(report.get("候选实例数量", 0)))
    add_check(checks, "旧系统n8n被保护", bool(old_protected), json.dumps(old_protected, ensure_ascii=False))
    add_check(checks, "旧系统未被选为导入目标", not unsafe_selected_old, json.dumps(candidates, ensure_ascii=False))
    add_check(checks, "预期新系统目标已登记", report.get("预期新系统目标", {}).get("容器名") == "jiege_v3_n8n", str(report.get("预期新系统目标", {})))
    add_check(checks, "未安全时必须阻断导入", safe or "暂不具备安全导入目标" in report.get("当前结论", ""), report.get("当前结论", ""))
    add_check(checks, "安全时只能选择新系统目标", (not safe) or selected == "jiege_v3_n8n", selected)
    add_check(checks, "未执行n8n真实动作", all(actions.get(key) is False for key in ["导入n8n", "启用n8n", "触发n8n", "重启服务", "写旧系统", "发送企业微信", "写正式库", "调用券商接口", "自动交易"]), str(actions))

    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查结果": checks,
        "通过": len(checks) - len(failed),
        "失败": len(failed),
    }
    log_dir = root / "04日志" / "n8n目标实例选择与隔离核验"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-assistant-n8n-target-isolation-package-verify-{stamp}.json"
    latest_output = log_dir / "stock-assistant-n8n-target-isolation-package-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
