# -*- coding: utf-8 -*-
"""
名称：验证300只候选公告财务行业事件正文核验任务.py
作用：验证300只候选公告财务行业事件正文核验任务是否可生成、任务是否覆盖推送前候选、安全边界是否保持。
触发方式：python 验证300只候选公告财务行业事件正文核验任务.py
依赖：Python标准库；生成300只候选公告财务行业事件正文核验任务.py；300只候选公告财务行业事件正文核验任务规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写入验收日志；不联网抓取；不下载正文；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选公告财务行业事件正文核验任务验收脚本。
标识：stock-trial-pool-300-event-body-verification-task-verify
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
    script = root / "02脚本" / "生成300只候选公告财务行业事件正文核验任务.py"
    rule_path = root / "01配置" / "300只候选公告财务行业事件正文核验任务规则.json"
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
    tasks = report.get("核验任务", [])
    candidate_count = int(report.get("推送前候选数量", 0))
    checks.append(check("候选覆盖存在", candidate_count > 0, candidate_count))
    checks.append(check("任务数量覆盖三类入口", len(tasks) >= candidate_count * 3, {"tasks": len(tasks), "candidate_count": candidate_count}))
    required = {"任务ID", "代码", "名称", "任务类型", "优先级", "入口名称", "来源级别", "URL", "核验结果"}
    missing = [task.get("任务ID") or "未知" for task in tasks if not required.issubset(set(task))]
    checks.append(check("任务字段完整", not missing, missing or "完整"))
    pending = all(task.get("核验结果", {}).get("状态") == "待人工核验" for task in tasks)
    checks.append(check("任务默认待人工核验", pending, "待人工核验"))
    has_official = any("官方" in str(task.get("来源级别", "")) or "交易所" in str(task.get("来源级别", "")) for task in tasks)
    checks.append(check("包含官方或交易所入口", has_official, "官方/交易所入口"))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作未触发", all(value is False for value in safety.values()), safety))
    text = markdown.read_text(encoding="utf-8-sig") if markdown.exists() else ""
    checks.append(check("Markdown包含任务清单", "## 任务清单" in text and "待人工核验" in text, "任务清单"))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest)
    }
    output_dir = root / "04日志" / "事件正文核验任务"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"trial-pool-300-event-body-verification-task-verify-{stamp}.json"
    latest_log = output_dir / "trial-pool-300-event-body-verification-task-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
