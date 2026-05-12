"""
名称：验证日常任务入口队列.py
作用：演练并验证日常任务入口的路由、人工确认队列、税收暂停和看板生成能力。
触发方式：python 验证日常任务入口队列.py
依赖：Python 标准库；提交日常任务到人工确认队列.py；生成日常任务队列看板.py。
所属系统：00杰哥系统总管
安全边界：只写入 01系统 06临时 演练目录和 00系统验收日志；不触发n8n、不发送企业微信、不写旧系统、不施工税收业务。
创建/修改记录：2026-04-27 创建日常任务入口队列验收脚本。
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()] if path.exists() else []


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    submit_script = root / "01杰哥智能系统" / "02脚本" / "智能体大脑" / "提交日常任务到人工确认队列.py"
    board_script = root / "01杰哥智能系统" / "02脚本" / "智能体大脑" / "生成日常任务队列看板.py"
    submit_result = run_script(submit_script, "--demo")
    board_result = run_script(board_script, "--demo")
    queue_path = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "任务队列_最新.jsonl"
    board_path = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "日常任务队列看板.md"
    tasks = read_jsonl(queue_path)
    types = {item.get("路由结果", {}).get("任务类型") for item in tasks}
    safety_values = [value for item in tasks for value in item.get("安全边界", {}).values()]
    checks = [
        check("演练提交脚本执行成功", submit_result.returncode == 0, submit_result.stdout.strip() or submit_result.stderr.strip()),
        check("看板生成脚本执行成功", board_result.returncode == 0, board_result.stdout.strip() or board_result.stderr.strip()),
        check("演练队列存在", queue_path.exists(), str(queue_path)),
        check("演练看板存在", board_path.exists(), str(board_path)),
        check("演练任务数量正确", len(tasks) == 4, len(tasks)),
        check("股票任务进入股票研究路由", "股票研究" in types, sorted(types)),
        check("本职工作任务进入本职工作路由", "本职工作" in types, sorted(types)),
        check("系统运维任务进入系统运维路由", "系统运维" in types, sorted(types)),
        check("税收任务被暂停登记", any(item.get("路由结果", {}).get("任务类型") == "税收业务" and item.get("路由结果", {}).get("是否暂停") is True for item in tasks), sorted(types)),
        check("所有任务等待人工确认", all(item.get("路由结果", {}).get("是否需要人工确认") is True for item in tasks), "人工确认队列"),
        check("未触发真实业务动作", all(value is False for value in safety_values), "只登记不执行"),
    ]
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "daily-task-entry-queue-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "日常可用版"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "daily-task-entry-queue-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
