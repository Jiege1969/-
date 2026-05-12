# -*- coding: utf-8 -*-
"""
名称：验证300只候选精选推送人工确认回执.py
作用：验证精选推送人工确认回执是否可生成、是否阻断未确认或无入选草案的真实发送前检查。
触发方式：python 验证300只候选精选推送人工确认回执.py
依赖：Python标准库；生成300只候选精选推送人工确认回执.py；300只候选精选推送人工确认回执规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地产物并写入验收日志；不触发发送链路；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只候选精选推送人工确认回执验收脚本。
标识：stock-trial-pool-300-selected-push-human-confirmation-verify
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
    script = root / "02脚本" / "生成300只候选精选推送人工确认回执.py"
    rule_path = root / "01配置" / "300只候选精选推送人工确认回执规则.json"
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
    checks.append(check("确认字段完整", len(report.get("确认回执空白模板", {})) >= 8, report.get("确认回执空白模板", {})))
    checks.append(check("无入选或未确认时阻断", report.get("真实发送前检查准入", {}).get("是否允许进入真实发送前检查") is False, report.get("真实发送前检查准入", {})))
    checks.append(check("真实发送关闭", report.get("是否企业微信真实发送") is False and report.get("是否触发发送链路") is False, {"是否企业微信真实发送": report.get("是否企业微信真实发送"), "是否触发发送链路": report.get("是否触发发送链路")}))
    safety = report.get("安全边界", {})
    checks.append(check("高风险动作未触发", all(value is False for value in safety.values()), safety))
    text = markdown.read_text(encoding="utf-8-sig") if markdown.exists() else ""
    checks.append(check("Markdown包含阻断原因", "阻断原因" in text and "安全边界" in text, "确认回执报告"))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "输出文件": str(latest)
    }
    output_dir = root / "04日志" / "精选推送人工确认回执"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"trial-pool-300-selected-push-human-confirmation-verify-{stamp}.json"
    latest_log = output_dir / "trial-pool-300-selected-push-human-confirmation-verify-最新.json"
    write_json(output, result)
    write_json(latest_log, result)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
