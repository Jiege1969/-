# -*- coding: utf-8 -*-
"""
名称：验证300只候选过热与量能持续性诊断报告.py
作用：验证111过热与量能持续性诊断报告可生成，且不改评分、不发送、不交易。
触发方式：python 验证300只候选过热与量能持续性诊断报告.py
依赖：Python标准库；生成300只候选过热与量能持续性诊断报告.py；300只候选过热与量能持续性诊断规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写验收日志；不修改评分规则；不修改候选清单；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建过热与量能持续性诊断验收脚本。
标识：stock-trial-pool-300-overheat-volume-continuity-diagnosis-verify
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
    script = root / "02脚本" / "生成300只候选过热与量能持续性诊断报告.py"
    rule_path = root / "01配置" / "300只候选过热与量能持续性诊断规则.json"
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
    rows = report.get("候选诊断", [])
    checks.append(check("候选诊断数量正确", len(rows) == 5, len(rows)))
    checks.append(check("包含过热等级", all(row.get("短线过热等级") in ("低", "中", "高") for row in rows), rows))
    checks.append(check("包含量能持续等级", all(row.get("量能持续等级") in ("弱", "一般", "强") for row in rows), rows))
    checks.append(check("包含关键指标", all(row.get("关键指标", {}).get("3日均量/10日均量") is not None for row in rows), rows))
    checks.append(check("包含观察标签", all(row.get("观察标签") for row in rows), rows))
    checks.append(check("摘要包含短线过热字段", "短线过热中高候选" in report.get("摘要", {}), report.get("摘要", {})))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作关闭", all(value is False for value in safety.values()), safety))
    text = markdown.read_text(encoding="utf-8-sig") if markdown.exists() else ""
    checks.append(check("Markdown包含诊断和安全边界", "候选诊断" in text and "安全边界" in text, str(markdown)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(latest)}
    log_dir = root / "04日志" / "过热与量能持续性诊断"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"trial-pool-300-overheat-volume-continuity-diagnosis-verify-{stamp}.json"
    latest_log = log_dir / "trial-pool-300-overheat-volume-continuity-diagnosis-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
