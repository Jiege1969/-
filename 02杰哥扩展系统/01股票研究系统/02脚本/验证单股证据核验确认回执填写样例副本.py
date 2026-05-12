# -*- coding: utf-8 -*-
"""
名称：验证单股证据核验确认回执填写样例副本.py
作用：验证212确认回执填写样例副本可生成，且不覆盖正式205回执和191 CSV。
触发方式：手动验收、股票系统日常一键运行或C+++总验收调用。
依赖：生成单股证据核验确认回执填写样例副本.py、205确认回执草案。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：04日志/单股证据核验确认回执填写样例副本/single-stock-evidence-confirmation-receipt-filled-example-copy-verify-最新.json。
安全边界：只运行212样例副本生成脚本并读取本地结果；不覆盖205，不覆盖191 CSV，不写191台账，不写172/175/178，不写正式档案，不触发n8n，不发送企业微信，不调用券商接口，不自动交易，不更新施工接续包。
创建/修改记录：2026-05-03 创建212确认回执填写样例副本验证脚本。
标识：single-stock-evidence-confirmation-receipt-filled-example-copy-verify
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
    script = root / "02脚本" / "生成单股证据核验确认回执填写样例副本.py"
    out_dir = root / "03数据" / "212单股证据核验确认回执填写样例副本"
    latest_json = out_dir / "单股证据核验确认回执填写样例副本_最新.json"
    latest_md = out_dir / "单股证据核验确认回执填写样例副本_最新.md"
    latest_csv = out_dir / "单股证据核验确认回执填写样例副本_最新.csv"
    receipt_csv = root / "03数据" / "205单股证据核验191候选采用确认回执草案" / "单股证据核验191候选采用确认回执草案_最新.csv"
    original_csv = root / "03数据" / "191单股证据核验人工填写台账" / "单股证据核验人工填写CSV表单_最新.csv"
    before_receipt = receipt_csv.read_text(encoding="utf-8-sig") if receipt_csv.exists() else ""
    before_191 = original_csv.read_text(encoding="utf-8-sig") if original_csv.exists() else ""
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
    after_receipt = receipt_csv.read_text(encoding="utf-8-sig") if receipt_csv.exists() else ""
    after_191 = original_csv.read_text(encoding="utf-8-sig") if original_csv.exists() else ""
    report = load_json(latest_json, {}) or {}
    summary = report.get("汇总", {}) if isinstance(report.get("汇总"), dict) else {}
    rows = report.get("样例回执", []) if isinstance(report.get("样例回执"), list) else []
    boundary = report.get("安全边界", {}) if isinstance(report.get("安全边界"), dict) else {}
    checks = [
        check("生成脚本存在", script.exists(), str(script)),
        check("生成脚本执行成功", run.returncode == 0, run.stdout.strip() or run.stderr.strip()),
        check("最新JSON存在", latest_json.exists(), str(latest_json)),
        check("最新Markdown存在", latest_md.exists(), str(latest_md)),
        check("最新CSV存在", latest_csv.exists(), str(latest_csv)),
        check("样例三条链路齐全", int(summary.get("样例链路数") or 0) == 3 and len(rows) == 3, summary),
        check("样例不是正式回执且不得写191", summary.get("是否正式回执") is False and summary.get("是否允许用于写191") is False, summary),
        check("样例字段符合210确认格式", all(row.get("确认结果") == "确认采用" and row.get("核验状态") == "已核验" and row.get("核验人") and row.get("核验日期") for row in rows), rows),
        check("未覆盖205回执CSV", before_receipt == after_receipt, str(receipt_csv)),
        check("未覆盖原191CSV", before_191 == after_191, str(original_csv)),
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
    log_dir = root / "04日志" / "单股证据核验确认回执填写样例副本"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"single-stock-evidence-confirmation-receipt-filled-example-copy-verify-{stamp}.json"
    latest = log_dir / "single-stock-evidence-confirmation-receipt-filled-example-copy-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(latest)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
