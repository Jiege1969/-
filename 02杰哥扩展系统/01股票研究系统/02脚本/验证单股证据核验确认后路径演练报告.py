# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验确认后路径演练报告.py
作用：验证213确认后路径演练报告可生成，且只模拟放行、不改正式205/210/211/191。
触发方式：手动验收、股票系统日常一键运行或C+++总验收调用。
依赖：生成单股证据核验确认后路径演练报告.py、212确认回执填写样例副本。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验确认后路径演练报告/single-stock-evidence-post-confirmation-path-rehearsal-report-verify-最新.json。
安全边界：只运行213演练报告生成脚本并读取本地结果；不覆盖205，不覆盖210，不覆盖211，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建213确认后路径演练报告验证脚本。
标识：single-stock-evidence-post-confirmation-path-rehearsal-report-verify
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
    script = root / "02脚本" / "生成单股证据核验确认后路径演练报告.py"
    out_dir = root / "03数据" / "213单股证据核验确认后路径演练报告"
    latest_json = out_dir / "单股证据核验确认后路径演练报告_最新.json"
    latest_md = out_dir / "单股证据核验确认后路径演练报告_最新.md"
    watched = [
        root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.csv",
        root / "03数据" / "210单股证据核验确认回执状态面板" / "单股证据核验确认回执状态面板_最新.json",
        root / "03数据" / "211单股证据核验回执后调度清单" / "单股证据核验回执后调度清单_最新.json",
        root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv",
    ]
    before = {str(path): path.read_text(encoding="utf-8-sig") if path.exists() else "" for path in watched}
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
    after = {str(path): path.read_text(encoding="utf-8-sig") if path.exists() else "" for path in watched}
    report = load_json(latest_json, {}) or {}
    summary = report.get("汇总", {}) if isinstance(report.get("汇总"), dict) else {}
    steps = report.get("模拟调度步骤", []) if isinstance(report.get("模拟调度步骤"), list) else []
    boundary = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    checks = [
        check("生成脚本存在", script.exists(), str(script)),
        check("生成脚本执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()),
        check("最新JSON存在", latest_json.exists(), str(latest_json)),
        check("最新Markdown存在", latest_md.exists(), str(latest_md)),
        check("样例可模拟三链路确认完成", summary.get("模拟是否三链路确认完成") is True and int(summary.get("样例有效链路数") or 0) == 3, summary),
        check("模拟五步调度均允许", int(summary.get("模拟允许调度步骤数") or 0) == 5 and len(steps) == 5 and all(item.get("模拟是否允许") is True for item in steps), steps),
        check("正式文件未被修改", before == after, {"before_keys": list(before), "after_keys": list(after)}),
        check("报告声明不影响正式205/210/211", summary.get("是否影响正式205") is False and summary.get("是否影响正式210") is False and summary.get("是否影响正式211") is False, summary),
        check("安全边界不写正式链路", bool(boundary) and all(value is False for value in boundary.values()), boundary),
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "单股证据核验确认后路径演练报告"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-post-confirmation-path-rehearsal-report-verify-{stamp}.json"
    latest = log_dir / "single-stock-evidence-post-confirmation-path-rehearsal-report-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
