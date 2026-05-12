# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验资料候选处理包.py
作用：验证199资料候选处理包可生成，确认其已处理候选资料但不写191、不触发外部正式动作。
触发方式：手动验收、日常一键运行或C+++总验收调用。
依赖：生成单股证据核验资料候选处理包.py、191资料来源导航卡、requests、bs4、pypdf。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验资料候选处理包/single-stock-evidence-source-candidate-package-verify-最新.json。
安全边界：只运行资料候选处理包生成和本地结构检查；不写191填写值，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
标识：single-stock-evidence-source-candidate-package-verify
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
    script = root / "02脚本" / "生成单股证据核验资料候选处理包.py"
    latest_json = root / "03数据" / "199单股证据核验资料候选处理包" / "单股证据核验资料候选处理包_最新.json"
    latest_md = root / "03数据" / "199单股证据核验资料候选处理包" / "单股证据核验资料候选处理包_最新.md"
    checks = [check("生成脚本存在", script.exists(), str(script))]
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
        timeout=180,
    )
    checks.append(check("生成脚本执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    checks.append(check("最新JSON存在", latest_json.exists() and latest_json.stat().st_size > 1000, str(latest_json)))
    checks.append(check("最新Markdown存在", latest_md.exists() and latest_md.stat().st_size > 1000, str(latest_md)))
    report = load_json(latest_json, {}) or {}
    fetched = report.get("候选资料抓取", []) if isinstance(report.get("候选资料抓取"), list) else []
    successful = [item for item in fetched if item.get("抓取成功")]
    checks.append(check("至少一个候选资料抓取成功", len(successful) >= 1, fetched))
    coverage = report.get("覆盖统计", {}) if isinstance(report.get("覆盖统计"), dict) else {}
    pending_fields = int(coverage.get("待填字段数") or 0)
    candidate_fields = int(coverage.get("已有候选片段字段数") or 0)
    checks.append(check(
        "生成字段候选片段或已完成无需候选",
        candidate_fields > 0 or pending_fields == 0,
        coverage,
    ))
    boundary = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    checks.append(check("安全边界不写191", boundary.get("写191") is False and all(value is False for value in boundary.values()), boundary))
    md_text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown明确不等于事实入账", "不等于事实已入账" in md_text and "不直接写191" in md_text or "不写191" in md_text, str(latest_md)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "单股证据核验资料候选处理包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-source-candidate-package-verify-{stamp}.json"
    latest = log_dir / "single-stock-evidence-source-candidate-package-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
