# -*- coding: utf-8 -*-
"""
名称：验证300只候选人工核验填写结果完整性闸口报告.py
作用：验证117人工核验填写结果完整性闸口可生成，且当前无完整核验时阻断101/102放行。
触发方式：python 验证300只候选人工核验填写结果完整性闸口报告.py
依赖：Python标准库；生成300只候选人工核验填写结果完整性闸口报告.py；300只候选人工核验填写结果完整性闸口规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写验收日志；不写入核验结果；不修改103；不刷新101/102；不修改候选清单；不触发发送链路；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建人工核验填写结果完整性闸口验收脚本。
标识：stock-trial-pool-300-manual-verification-completeness-gate-verify
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
    script = root / "02脚本" / "生成300只候选人工核验填写结果完整性闸口报告.py"
    rule_path = root / "01配置" / "300只候选人工核验填写结果完整性闸口规则.json"
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
    gate = report.get("闸口结论", {})
    checks.append(check("当前阻断101/102放行", gate.get("是否允许刷新101/102放行") is False, gate))
    checks.append(check("候选闸口数量正确", len(report.get("候选闸口结果", [])) == 5, len(report.get("候选闸口结果", []))))
    checks.append(check("任务质量数量正确", report.get("任务质量统计", {}).get("任务数量") == 30, report.get("任务质量统计", {})))
    checks.append(check("可放行候选数量为0", gate.get("可放行候选数量") == 0, gate))
    checks.append(check("放行条件完整", len(report.get("候选放行条件", [])) >= 5, report.get("候选放行条件", [])))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作关闭", all(value is False for value in safety.values()), safety))
    text = markdown.read_text(encoding="utf-8-sig") if markdown.exists() else ""
    checks.append(check("Markdown包含结论和候选闸口", "结论" in text and "候选闸口" in text, str(markdown)))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {"生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "通过": passed, "失败": failed, "检查项": checks, "输出文件": str(latest)}
    log_dir = root / "04日志" / "人工核验完整性闸口"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = log_dir / f"trial-pool-300-manual-verification-completeness-gate-verify-{stamp}.json"
    latest_log = log_dir / "trial-pool-300-manual-verification-completeness-gate-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
