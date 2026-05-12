# -*- coding: utf-8 -*-
"""
名称：验证300只候选复盘到期提醒与人工填写清单.py
作用：验证114复盘到期提醒与人工填写清单可生成，且不创建系统定时任务、不抓行情、不写复盘结论。
触发方式：python 验证300只候选复盘到期提醒与人工填写清单.py
依赖：Python标准库；生成300只候选复盘到期提醒与人工填写清单.py；300只候选复盘到期提醒与人工填写清单规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写验收日志；不创建系统定时任务；不联网抓取行情；不写入复盘结论；不修改评分规则；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建复盘到期提醒与人工填写清单验收脚本。
标识：stock-trial-pool-300-review-due-manual-checklist-verify
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
    script = root / "02脚本" / "生成300只候选复盘到期提醒与人工填写清单.py"
    rule_path = root / "01配置" / "300只候选复盘到期提醒与人工填写清单规则.json"
    checks: list[dict[str, Any]] = [
        check("规则存在", rule_path.exists(), str(rule_path)),
        check("脚本存在", script.exists(), str(script))
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    run = subprocess.run([sys.executable, str(script)], cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=120)
    checks.append(check("脚本执行", run.returncode == 0, run.stdout.strip() or run.stderr.strip()))
    rule = load_json(rule_path)
    latest = root / rule["输出"]["数据目录"] / rule["输出"]["最新文件"]
    markdown = root / rule["输出"]["数据目录"] / rule["输出"]["报告文件"]
    checks.append(check("最新JSON存在", latest.exists(), str(latest)))
    checks.append(check("Markdown报告存在", markdown.exists(), str(markdown)))
    report = load_json(latest) if latest.exists() else {}
    groups = report.get("按日期提醒清单", [])
    checks.append(check("复盘日期数量正确", len(groups) == 3, len(groups)))
    checks.append(check("复盘任务数量正确", report.get("摘要", {}).get("复盘任务数量") == 15, report.get("摘要", {})))
    checks.append(check("每个复盘日5项任务", all(group.get("任务数量") == 5 for group in groups), groups))
    checks.append(check("待填字段存在", all(task.get("待填字段") for group in groups for task in group.get("任务", [])), groups))
    checks.append(check("后续联动存在", len(report.get("后续联动", [])) >= 3, report.get("后续联动", [])))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作关闭", all(value is False for value in safety.values()), safety))
    text = markdown.read_text(encoding="utf-8-sig") if markdown.exists() else ""
    checks.append(check("Markdown包含到期清单和后续联动", "到期清单" in text and "后续联动" in text, str(markdown)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(latest)}
    log_dir = root / "04日志" / "复盘到期提醒与人工填写清单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"trial-pool-300-review-due-manual-checklist-verify-{stamp}.json"
    latest_log = log_dir / "trial-pool-300-review-due-manual-checklist-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
