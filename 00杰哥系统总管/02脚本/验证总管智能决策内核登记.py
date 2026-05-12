# -*- coding: utf-8 -*-
"""
名称：验证总管智能决策内核登记.py
作用：生成并验证总管智能决策内核登记报告，确认大模型、OpenClaw、n8n、执行器、闸口和进化系统职责边界清晰。
触发方式：python 验证总管智能决策内核登记.py
依赖：Python 标准库；生成模型资源池登记.py；生成总管智能决策内核登记.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证决策内核报告；不调用模型；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建总管智能决策内核登记验证脚本。
标识：manager-decision-core-register-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def run_python(script: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    model_script = manager / "02脚本" / "生成模型资源池登记.py"
    core_script = manager / "02脚本" / "生成总管智能决策内核登记.py"
    model_result = run_python(model_script)
    core_result = run_python(core_script)
    report_path = manager / "03数据" / "智能决策内核" / "总管智能决策内核登记_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    switches = report.get("当前默认开关", {})
    openclaw = report.get("OpenClaw边界", {})
    duty = report.get("职责分工", {})
    checks = [
        check("模型资源池登记生成成功", model_result.returncode == 0, model_result.stdout.strip() or model_result.stderr.strip()),
        check("决策内核登记生成成功", core_result.returncode == 0, core_result.stdout.strip() or core_result.stderr.strip()),
        check("决策内核登记文件存在", report_path.exists(), str(report_path)),
        check("决策流程不少于八步", len(report.get("决策流程", [])) >= 8, report.get("决策流程", [])),
        check("大模型不直接执行真实动作", "不直接执行真实动作" in duty.get("大模型", ""), duty),
        check("OpenClaw只做消息网关", "消息入口和出口" in duty.get("OpenClaw", ""), duty),
        check("n8n为唯一逻辑调度中心", "唯一逻辑调度中心" in duty.get("n8n", ""), duty),
        check("OpenClaw禁止业务判断", any("业务if else判断" in item for item in openclaw.get("禁止", [])), openclaw),
        check("真实联网默认关闭", switches.get("允许真实联网") is False, switches),
        check("正式库写入默认关闭", switches.get("允许正式库写入") is False, switches),
        check("n8n真实触发默认关闭", switches.get("允许n8n真实触发") is False, switches),
        check("税收业务默认关闭", switches.get("允许税收业务") is False, switches),
        check("旧系统写入默认关闭", switches.get("允许旧系统写入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "manager-decision-core-register-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "智能决策内核"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"manager-decision-core-register-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "manager-decision-core-register-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
