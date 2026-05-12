# -*- coding: utf-8 -*-
"""
名称：验证股票判断复盘到期提醒与人工填写清单.py
作用：验证判断复盘到期提醒清单可生成，且不写验证结论、不改规则、不触发外部动作。
触发方式：python 验证股票判断复盘到期提醒与人工填写清单.py
安全边界：只运行本地生成脚本并检查产物；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
标识：stock-judgment-review-due-manual-checklist-verify
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


def load_json(path: Path, default: Any) -> Any:
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
    script = root / "02脚本" / "生成股票判断复盘到期提醒与人工填写清单.py"
    latest_json = root / "03数据" / "188判断复盘到期提醒与人工填写清单" / "股票判断复盘到期提醒与人工填写清单_最新.json"
    latest_md = root / "03数据" / "188判断复盘到期提醒与人工填写清单" / "股票判断复盘到期提醒与人工填写清单_最新.md"
    checks: list[dict[str, Any]] = [
        check("脚本存在", script.exists(), str(script)),
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )
    checks.append(check("脚本执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    checks.append(check("最新JSON存在", latest_json.exists(), str(latest_json)))
    checks.append(check("Markdown报告存在", latest_md.exists(), str(latest_md)))
    report = load_json(latest_json, {})
    summary = report.get("摘要", {}) if isinstance(report, dict) else {}
    checks.append(check("验证任务数量非零", int(summary.get("验证任务数量") or 0) > 0, summary))
    checks.append(check("待填字段存在", bool(report.get("人工必填字段")) if isinstance(report, dict) else False, report.get("人工必填字段") if isinstance(report, dict) else None))
    safety = report.get("安全边界", {}) if isinstance(report, dict) else {}
    checks.append(check("高风险动作关闭", bool(safety) and all(value is False for value in safety.values()), safety))
    text = latest_md.read_text(encoding="utf-8-sig") if latest_md.exists() else ""
    checks.append(check("Markdown包含到期清单", "到期清单" in text and "人工填写字段" in text, str(latest_md)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest_json),
    }
    log_dir = root / "04日志" / "复盘到期提醒与人工填写清单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"stock-judgment-review-due-manual-checklist-verify-{stamp}.json"
    latest_log = log_dir / "stock-judgment-review-due-manual-checklist-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest_log)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
