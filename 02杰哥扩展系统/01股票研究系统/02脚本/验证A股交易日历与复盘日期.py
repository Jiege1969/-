# -*- coding: utf-8 -*-
"""
名称：验证A股交易日历与复盘日期.py
作用：验证A股交易日历和300只候选T+1/T+3/T+5复盘日期是否生成正确、安全边界是否保持。
触发方式：python 验证A股交易日历与复盘日期.py
依赖：Python标准库；生成A股交易日历与复盘日期.py；A股交易日历与复盘日期规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读交易日历复盘日期结果并写入验收日志；不联网；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建A股交易日历与复盘日期验收脚本。
标识：stock-a-share-trading-calendar-review-date-verify
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def main() -> int:
    root = module_root()
    script = root / "02脚本" / "生成A股交易日历与复盘日期.py"
    rule_path = root / "01配置" / "A股交易日历与复盘日期规则.json"
    checks: list[dict[str, Any]] = [
        check("脚本存在", script.exists(), str(script)),
        check("规则存在", rule_path.exists(), str(rule_path)),
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

    rule = load_json(rule_path)
    output_dir = root / rule["输出"]["数据目录"]
    calendar_latest = output_dir / rule["输出"]["交易日历最新文件"]
    ledger_latest = output_dir / rule["输出"]["复盘日期账本最新文件"]
    report_latest = output_dir / rule["输出"]["报告文件"]
    checks.append(check("交易日历存在", calendar_latest.exists(), str(calendar_latest)))
    checks.append(check("复盘日期账本存在", ledger_latest.exists(), str(ledger_latest)))
    checks.append(check("Markdown报告存在", report_latest.exists(), str(report_latest)))

    calendar = load_json(calendar_latest) if calendar_latest.exists() else {}
    ledger = load_json(ledger_latest) if ledger_latest.exists() else {}
    day_map = {item.get("日期"): item for item in calendar.get("日历", [])}
    checks.append(check("劳动节休市识别", all(day_map.get(day, {}).get("是否交易日") is False for day in ["2026-05-01", "2026-05-04", "2026-05-05"]), "2026-05-01/04/05应休市"))
    checks.append(check("5月6日开市识别", day_map.get("2026-05-06", {}).get("是否交易日") is True, day_map.get("2026-05-06")))
    expected = {"T+1": "2026-05-06", "T+3": "2026-05-08", "T+5": "2026-05-12"}
    checks.append(check("周期日期正确", ledger.get("周期日期") == expected, ledger.get("周期日期")))
    no_placeholders = all(
        plan.get("目标交易日") not in ("", "待接入交易日历确认", "交易日历覆盖不足")
        for item in ledger.get("复盘账本", [])
        for plan in item.get("验证计划", [])
        if plan.get("周期") in expected
    )
    checks.append(check("复盘日期不再占位", no_placeholders, "所有T+1/T+3/T+5均应有具体交易日"))
    forbidden = {}
    forbidden.update(calendar.get("安全边界", {}))
    forbidden.update(ledger.get("安全边界", {}))
    checks.append(check("高风险动作未触发", all(value is False for value in forbidden.values()), json.dumps(forbidden, ensure_ascii=False)))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(ledger_latest),
    }
    log_dir = root / "04日志" / "交易日历复盘日期"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"a-share-trading-calendar-review-date-verify-{stamp}.json"
    latest = log_dir / "a-share-trading-calendar-review-date-verify-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
