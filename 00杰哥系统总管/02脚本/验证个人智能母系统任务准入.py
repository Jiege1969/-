# -*- coding: utf-8 -*-
"""
名称：验证个人智能母系统任务准入.py
作用：验证任务准入规则和任务准入报告脚本在典型状态下的允许、延后、需要许可、禁止判断。
触发方式：python 验证个人智能母系统任务准入.py
依赖：Python标准库；生成个人智能母系统任务准入报告.py；个人智能母系统任务准入规则.json。
所属系统：00杰哥系统总管。
输出：00杰哥系统总管/04日志/个人智能母系统任务准入/task-admission-verify-*.json。
安全边界：只读验证并写总管日志；不执行任务、不重启服务、不触发n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：personal-ai-task-admission-verify；任务准入验收；只读验证。
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


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def has_header(path: Path) -> bool:
    text = path.read_text(encoding="utf-8-sig", errors="replace")[:1200]
    return all(key in text for key in ["名称", "作用", "触发方式", "依赖", "所属系统", "输出", "安全边界", "标识"])


def run_case(script: Path, case: dict[str, str]) -> dict[str, Any]:
    args = [
        sys.executable,
        str(script),
        "--task", case["task"],
        "--level", case["level"],
        "--type", case["type"],
        "--action", case["action"],
        "--system", case.get("system", "00总管"),
        "--now", case["now"],
        "--ignore-resource-pressure",
    ]
    result = subprocess.run(
        args,
        cwd=str(script.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    latest = manager_root() / "03数据" / "运行状态" / "个人智能母系统任务准入_最新.json"
    parsed = load_json(latest, {})
    return {"returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "parsed": parsed}


def add(checks: list[dict[str, Any]], name: str, ok: bool, detail: Any) -> None:
    checks.append({"名称": name, "通过": bool(ok), "说明": detail})


def main() -> int:
    manager = manager_root()
    config = manager / "01配置" / "个人智能母系统任务准入规则.json"
    script = manager / "02脚本" / "生成个人智能母系统任务准入报告.py"
    checks: list[dict[str, Any]] = []
    add(checks, "任务准入规则存在", config.exists(), str(config))
    rules = load_json(config, {})
    add(checks, "任务准入规则可解析", bool(rules.get("状态准入策略")), list(rules.keys()))
    add(checks, "任务准入脚本存在", script.exists(), str(script))
    add(checks, "任务准入脚本含标准标头", script.exists() and has_header(script), str(script))

    cases = [
        {
            "name": "交易保护只读允许",
            "now": "2026-05-06 10:00:00",
            "task": "开市状态检查",
            "level": "L0",
            "type": "L0只读巡检",
            "action": "只读检查",
            "expected": "允许执行",
        },
        {
            "name": "交易保护服务级禁止",
            "now": "2026-05-06 10:00:00",
            "task": "重启股票入口",
            "level": "L2",
            "type": "L2服务级操作",
            "action": "重启19300",
            "expected": "禁止执行",
        },
        {
            "name": "收市股票分析允许",
            "now": "2026-05-06 16:00:00",
            "task": "盘后推荐生成",
            "level": "L0",
            "type": "股票收市分析",
            "action": "股票数据采集和报告生成",
            "expected": "允许执行",
        },
        {
            "name": "夜间服务级需许可",
            "now": "2026-05-06 23:00:00",
            "task": "重载模型服务",
            "level": "L2",
            "type": "L2服务级操作",
            "action": "重载配置",
            "expected": "需要许可令",
        },
        {
            "name": "自动交易硬阻断",
            "now": "2026-05-06 16:00:00",
            "task": "股票交易测试",
            "level": "L3",
            "type": "L3破坏性操作",
            "action": "自动交易买入",
            "expected": "禁止执行",
        },
    ]
    case_results = {}
    for case in cases:
        result = run_case(script, case)
        actual = result.get("parsed", {}).get("准入结论")
        case_results[case["name"]] = result
        add(checks, f"{case['name']}判断正确", result["returncode"] == 0 and actual == case["expected"], {"期望": case["expected"], "实际": actual, "报告": result.get("parsed", {})})

    latest = manager / "03数据" / "运行状态" / "个人智能母系统任务准入_最新.json"
    add(checks, "最新任务准入状态存在", latest.exists(), str(latest))
    if latest.exists():
        data = load_json(latest, {})
        safety = data.get("安全边界", {})
        add(checks, "任务准入安全边界全部为False", safety and not any(bool(value) for value in safety.values()), safety)

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "个人智能母系统任务准入验证",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "检查项": checks,
        "样本结果": case_results,
        "安全边界": {
            "是否执行任务": False,
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    out_dir = manager / "04日志" / "个人智能母系统任务准入"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = out_dir / f"task-admission-verify-{stamp}.json"
    latest_output = out_dir / "task-admission-verify-最新.json"
    write_json(output, report)
    write_json(latest_output, report)
    print(json.dumps({"通过": report["通过"], "失败": report["失败"], "输出": str(latest_output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
