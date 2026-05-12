# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验模板同步执行闸口.py
作用：验证193模板同步执行闸口可生成，并确认本脚本不执行任何写入或外部动作。
触发方式：手动验收、日常一键运行或197完成后预演检查。
依赖：生成单股证据核验模板同步执行闸口.py、192同步预览。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验模板同步执行闸口/single-stock-evidence-template-sync-gate-verify-最新.json。
安全边界：只运行193闸口生成和本地结构检查；不写172/175/178模板，不写正式档案，不导入正式库，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-template-sync-gate-verify
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
    script = root / "02脚本" / "生成单股证据核验模板同步执行闸口.py"
    latest_json = root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.json"
    latest_md = root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.md"
    checks: list[dict[str, Any]] = [check("生成脚本存在", script.exists(), str(script))]
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
    checks.append(check("生成脚本执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    checks.append(check("最新JSON存在", latest_json.exists(), str(latest_json)))
    checks.append(check("最新Markdown存在", latest_md.exists(), str(latest_md)))
    report = load_json(latest_json, {}) or {}
    checks.append(check("目标股票明确", bool(report.get("目标股票", {}).get("代码")), report.get("目标股票", {})))
    checks.append(check("闸口结论存在", bool(report.get("闸口结论")), report.get("闸口结论")))
    checks.append(check("本脚本不执行写入", report.get("本脚本是否执行写入") is False, report.get("本脚本是否执行写入")))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作全部关闭", bool(safety) and all(value is False for value in safety.values()), safety))
    md_text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown包含闸口结论和安全边界", "闸口结论" in md_text and "安全边界" in md_text, str(latest_md)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "单股证据核验模板同步执行闸口"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-template-sync-gate-verify-{stamp}.json"
    latest_log = log_dir / "single-stock-evidence-template-sync-gate-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_log)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
