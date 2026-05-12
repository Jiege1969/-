# -*- coding: utf-8 -*-
"""
名称：验证全闭环保障主控.py
作用：验证全闭环保障主控规则、执行报告和安全边界是否可用。
触发方式：python 验证全闭环保障主控.py
依赖：Python标准库；全闭环保障主控规则.json；full_cycle_guard_latest.json。
所属系统：00杰哥系统总管
安全边界：只读验证，不删除、不覆盖、不触发n8n、不发送企业微信、不写正式库、不接交易接口。
创建/修改记录：2026-04-28 创建全闭环保障主控验证脚本。
标识：full-cycle-guard-controller-verify
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
RULE = ROOT / "00杰哥系统总管" / "01配置" / "全闭环保障主控规则.json"
LATEST = ROOT / "00杰哥系统总管" / "03数据" / "全闭环保障" / "full-cycle-guard_latest.json"
STATE_ENV = ROOT / "01杰哥智能系统" / "03数据" / "运行状态" / "system_health.env"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    checks: list[dict[str, object]] = []
    checks.append({"name": "规则文件存在", "ok": RULE.exists()})
    checks.append({"name": "最新报告存在", "ok": LATEST.exists()})
    checks.append({"name": "状态文件存在", "ok": STATE_ENV.exists()})

    if RULE.exists():
        rule = load_json(RULE)
        checks.append({"name": "核心闭环五步齐全", "ok": rule.get("核心闭环") == ["检测", "判断", "执行", "验证", "记录"]})
        checks.append({"name": "运行时五层齐全", "ok": len(rule.get("运行时五层", [])) == 5})
        checks.append({"name": "工作四层齐全", "ok": len(rule.get("工作四层", [])) == 4})
        hard = rule.get("硬边界", {})
        checks.append({"name": "交易接口禁止", "ok": hard.get("交易接口") == "禁止接入"})
        checks.append({"name": "发送企业微信禁止自动执行", "ok": hard.get("发送企业微信消息") == "禁止自动执行"})

    if LATEST.exists():
        report = load_json(LATEST)
        checks.append({"name": "报告包含决策", "ok": bool(report.get("decision"))})
        checks.append({"name": "报告包含步骤", "ok": len(report.get("steps", [])) >= 5})
        safety = report.get("safety", {})
        forbidden_flags = [
            "delete_files",
            "overwrite",
            "disable_scheduled_task",
            "edit_wsl_crontab",
            "edit_systemd",
            "stop_protected_old_jiege",
            "trigger_n8n",
            "send_wework",
            "write_formal_db",
            "broker_api",
            "auto_trade",
        ]
        checks.append({"name": "安全边界全部为false", "ok": all(safety.get(flag) is False for flag in forbidden_flags)})
        checks.append({"name": "v3模型数不少于12", "ok": report.get("summary", {}).get("v3_ollama_model_count", 0) >= 12})

    ok = all(item["ok"] for item in checks)
    result = {
        "ok": ok,
        "passed": sum(1 for item in checks if item["ok"]),
        "total": len(checks),
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
