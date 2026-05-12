# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验人工填写说明卡.py
作用：验证 191 人工填写说明卡可以生成，并且保持只读/说明性质。
触发方式：python 验证单股证据核验人工填写说明卡.py
依赖：生成单股证据核验人工填写说明卡.py、191单股证据核验人工填写台账。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验人工填写说明卡/single-stock-evidence-manual-guide-verify-最新.json。
安全边界：只运行本地说明卡生成脚本并检查产物；不联网抓取、不写正式档案、不触发n8n、不发送企业微信、不调用券商接口、不自动交易。
标识：single-stock-evidence-manual-guide-verify
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
    script = root / "02脚本" / "生成单股证据核验人工填写说明卡.py"
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    latest_json = out_dir / "单股证据核验人工填写说明卡_最新.json"
    latest_md = out_dir / "单股证据核验人工填写说明卡_最新.md"
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
    checks.append(check("三条链路齐全", len(report.get("链路", [])) == 3, [item.get("链路") for item in report.get("链路", [])]))
    run_order = report.get("填完后运行顺序", [])
    checks.append(check("填完后运行顺序齐全", len(run_order) >= 6, run_order))
    checks.append(check(
        "运行顺序包含198质量闸口和197预演",
        any("191填写质量闸口" in str(item) for item in run_order) and any("191完成后预演检查" in str(item) for item in run_order),
        run_order,
    ))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作全部关闭", bool(safety) and all(value is False for value in safety.values()), safety))
    md_text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown包含安全边界", "不联网抓取" in md_text and "不自动交易" in md_text, str(latest_md)))
    checks.append(check("Markdown包含198/197/193提醒", "198/197/193" in md_text, str(latest_md)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "单股证据核验人工填写说明卡"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-manual-guide-verify-{stamp}.json"
    latest_log = log_dir / "single-stock-evidence-manual-guide-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_log)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
