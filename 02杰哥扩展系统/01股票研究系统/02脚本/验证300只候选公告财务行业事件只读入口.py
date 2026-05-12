# -*- coding: utf-8 -*-
"""
名称：验证300只候选公告财务行业事件只读入口.py
作用：验证300只候选公告、财务、行业事件只读入口是否可生成、字段是否完整、安全边界是否保持。
触发方式：python 验证300只候选公告财务行业事件只读入口.py
依赖：Python标准库；生成300只候选公告财务行业事件只读入口.py；300只候选公告财务行业事件只读入口规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读入口包并写入验收日志；不抓取正文；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建公告财务行业事件只读入口验收脚本。
标识：stock-trial-pool-300-disclosure-finance-event-readonly-entry-verify
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
    script = root / "02脚本" / "生成300只候选公告财务行业事件只读入口.py"
    rule_path = root / "01配置" / "300只候选公告财务行业事件只读入口规则.json"
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
    latest = root / rule["输出"]["数据目录"] / rule["输出"]["最新文件"]
    markdown = root / rule["输出"]["数据目录"] / rule["输出"]["报告文件"]
    checks.append(check("最新JSON存在", latest.exists(), str(latest)))
    checks.append(check("Markdown报告存在", markdown.exists(), str(markdown)))

    report = load_json(latest) if latest.exists() else {}
    entries = report.get("候选入口", [])
    checks.append(check("入口数量大于0", len(entries) > 0, len(entries)))
    checks.append(check("入口数量与候选数量一致", len(entries) == report.get("候选数量"), {
        "entries": len(entries),
        "candidates": report.get("候选数量"),
    }))
    complete = all(item.get("公告入口") and item.get("财务入口") and item.get("行业事件入口") for item in entries)
    checks.append(check("公告财务行业入口完整", complete, "每只候选均需具备三类入口"))
    supplemental_limited = all(
        "不得作为唯一正式依据" in json.dumps(item, ensure_ascii=False)
        for item in entries
        if "东方财富" in json.dumps(item, ensure_ascii=False)
    )
    checks.append(check("补充来源限制已标注", supplemental_limited, "东方财富等补充入口必须标注不得作为唯一正式依据"))
    forbidden = report.get("安全边界", {})
    safe = all(value is False for value in forbidden.values())
    checks.append(check("高风险动作未触发", safe, json.dumps(forbidden, ensure_ascii=False)))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest),
    }
    output_dir = root / "04日志" / "公告财务行业事件只读入口"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"trial-pool-300-disclosure-finance-event-entry-verify-{stamp}.json"
    latest_log = output_dir / "trial-pool-300-disclosure-finance-event-entry-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
