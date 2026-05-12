# -*- coding: utf-8 -*-
"""
名称：验证股票证据核验导入执行闸口.py
作用：验证181闸口允许已通过记录进入人工确认执行，同时保留未通过记录阻断，不执行正式导入。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成股票证据核验导入执行闸口.py"
    latest = root / "03数据" / "181证据核验导入执行闸口" / "股票证据核验导入执行闸口_最新.json"
    checks = [check("181生成脚本存在", script.exists(), str(script))]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )
    checks.append(check("181生成脚本执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    report = load_json(latest, {}) or {}
    chains = report.get("链路", []) if isinstance(report.get("链路"), list) else []
    checks.append(check("181最新报告存在", latest.exists(), str(latest)))
    checks.append(check("链路数量为3", len(chains) == 3, len(chains)))
    ready_total = sum(int(chain.get("可执行记录数") or 0) for chain in chains)
    checks.append(check("已通过记录计数可解析", ready_total >= 0, ready_total))
    checks.append(check("允许状态基于已通过记录", bool(report.get("是否允许任何正式导入")) == (ready_total > 0), report.get("总结论")))
    checks.append(check("未通过记录保留阻断说明", all("执行范围" in chain for chain in chains), chains))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作全部关闭", bool(safety) and all(value is False for value in safety.values()), safety))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
    }
    log_dir = root / "04日志" / "股票证据核验导入执行闸口"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"stock-evidence-import-execution-gate-verify-{stamp}.json"
    latest_log = log_dir / "stock-evidence-import-execution-gate-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_log)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
