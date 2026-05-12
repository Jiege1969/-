# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验正式回执填写前自检.py
作用：验证215正式回执填写前自检可生成，且不写正式205和191。
触发方式：手动验收、股票系统日常一键运行或C+++总验收调用。
依赖：生成单股证据核验正式回执填写前自检.py、205/210/212/214状态文件。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验正式回执填写前自检/single-stock-evidence-formal-confirmation-receipt-prefill-check-verify-最新.json。
安全边界：只运行215自检生成脚本并读取本地结果；不覆盖205，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建215正式回执填写前自检验证脚本。
标识：single-stock-evidence-formal-confirmation-receipt-prefill-check-verify
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
    script = root / "02脚本" / "生成单股证据核验正式回执填写前自检.py"
    out_dir = root / "03数据" / "215单股证据核验正式回执填写前自检"
    latest_json = out_dir / "单股证据核验正式回执填写前自检_最新.json"
    latest_md = out_dir / "单股证据核验正式回执填写前自检_最新.md"
    watched = [
        root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.csv",
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
    details = report.get("链路自检", []) if isinstance(report.get("链路自检"), list) else []
    boundary = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    checks = [
        check("生成脚本存在", script.exists(), str(script)),
        check("生成脚本执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()),
        check("最新JSON存在", latest_json.exists(), str(latest_json)),
        check("最新Markdown存在", latest_md.exists(), str(latest_md)),
        check("正式回执三条链路齐全", int(summary.get("正式回执行数") or 0) == 3 and len(details) == 3, summary),
        check("214待办链路三条齐全", int(summary.get("214待办链路数") or 0) == 3, summary),
        check(
            "206闸口放行状态与确认完成度一致",
            (summary.get("是否允许进入206闸口") is False and int(summary.get("当前缺失字段总数") or 0) >= 9)
            or (summary.get("是否允许进入206闸口") is True and int(summary.get("当前缺失字段总数") or 0) == 0 and int(summary.get("当前达到确认完成格式链路数") or 0) == 3),
            summary,
        ),
        check(
            "缺失字段状态与正式回执阶段一致",
            int(summary.get("当前缺失字段总数") or 0) >= 9
            or (int(summary.get("当前缺失字段总数") or 0) == 0 and int(summary.get("当前达到确认完成格式链路数") or 0) == 3),
            summary,
        ),
        check("正式文件未被修改", before == after, {"before_keys": list(before), "after_keys": list(after)}),
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
    log_dir = root / "04日志" / "单股证据核验正式回执填写前自检"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-formal-confirmation-receipt-prefill-check-verify-{stamp}.json"
    latest = log_dir / "single-stock-evidence-formal-confirmation-receipt-prefill-check-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
