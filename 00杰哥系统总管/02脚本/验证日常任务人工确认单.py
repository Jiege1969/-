"""
名称：验证日常任务人工确认单.py
作用：验证日常任务人工确认单生成、风险边界、税收暂停和禁止自动执行规则。
触发方式：python 验证日常任务人工确认单.py
依赖：Python 标准库；提交日常任务到人工确认队列.py；生成日常任务人工确认单.py。
所属系统：00杰哥系统总管
安全边界：只在 01系统 06临时 演练目录生成确认单；不触发n8n、不发送企业微信、不写旧系统、不施工税收业务。
创建/修改记录：2026-04-27 创建日常任务人工确认单验收脚本。
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


def run_script(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(path), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    submit_script = root / "01杰哥智能系统" / "02脚本" / "智能体大脑" / "提交日常任务到人工确认队列.py"
    confirm_script = root / "01杰哥智能系统" / "02脚本" / "智能体大脑" / "生成日常任务人工确认单.py"
    submit_result = run_script(submit_script, "--demo")
    confirm_result = run_script(confirm_script, "--demo")
    confirm_dir = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "人工确认单"
    latest_json = confirm_dir / "日常任务人工确认单_最新.json"
    latest_md = confirm_dir / "日常任务人工确认单_最新.md"
    confirmations = load_json(latest_json) if latest_json.exists() else []
    safety_values = [value for item in confirmations for value in item.get("安全边界", {}).values()]
    checks = [
        check("演练任务提交成功", submit_result.returncode == 0, submit_result.stdout.strip() or submit_result.stderr.strip()),
        check("人工确认单生成成功", confirm_result.returncode == 0, confirm_result.stdout.strip() or confirm_result.stderr.strip()),
        check("人工确认单json存在", latest_json.exists(), str(latest_json)),
        check("人工确认单markdown存在", latest_md.exists(), str(latest_md)),
        check("确认单数量正确", len(confirmations) == 4, len(confirmations)),
        check("所有确认单禁止自动执行", all(value is False for value in safety_values), "只确认不执行"),
        check("税收确认单保持暂停", any(item.get("任务类型") == "税收业务" and "暂停" in item.get("当前状态", "") for item in confirmations), "税收业务暂停"),
        check("每个确认单包含放行条件", all(item.get("放行条件") for item in confirmations), "放行条件完整"),
        check("每个确认单包含禁止动作", all(item.get("禁止动作") for item in confirmations), "禁止动作完整"),
    ]
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "daily-task-confirmation-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "日常可用版"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "daily-task-confirmation-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
