"""
名称：验证日常任务放行预案.py
作用：验证日常任务放行预案生成、税收暂停、高风险评审和真实动作关闭状态。
触发方式：python 验证日常任务放行预案.py
依赖：Python 标准库；提交日常任务到人工确认队列.py；生成日常任务人工确认单.py；生成日常任务放行预案.py。
所属系统：00杰哥系统总管
安全边界：只在 01系统 06临时 演练目录生成预案；不触发n8n、不发送企业微信、不写旧系统、不施工税收业务。
创建/修改记录：2026-04-27 创建日常任务放行预案验收脚本。
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
    brain_dir = root / "01杰哥智能系统" / "02脚本" / "智能体大脑"
    submit_result = run_script(brain_dir / "提交日常任务到人工确认队列.py", "--demo")
    confirmation_result = run_script(brain_dir / "生成日常任务人工确认单.py", "--demo")
    release_result = run_script(brain_dir / "生成日常任务放行预案.py", "--demo")
    release_dir = root / "01杰哥智能系统" / "06临时" / "日常任务入口演练" / "放行预案"
    latest_json = release_dir / "日常任务放行预案_最新.json"
    latest_md = release_dir / "日常任务放行预案_最新.md"
    plans = load_json(latest_json) if latest_json.exists() else []
    safety_values = [value for item in plans for value in item.get("执行开关", {}).values()]
    checks = [
        check("演练任务提交成功", submit_result.returncode == 0, submit_result.stdout.strip() or submit_result.stderr.strip()),
        check("人工确认单生成成功", confirmation_result.returncode == 0, confirmation_result.stdout.strip() or confirmation_result.stderr.strip()),
        check("放行预案生成成功", release_result.returncode == 0, release_result.stdout.strip() or release_result.stderr.strip()),
        check("放行预案json存在", latest_json.exists(), str(latest_json)),
        check("放行预案markdown存在", latest_md.exists(), str(latest_md)),
        check("放行预案数量正确", len(plans) == 4, len(plans)),
        check("税收任务禁止放行", any(item.get("任务类型") == "税收业务" and "禁止放行" in item.get("放行结论", "") for item in plans), "税收暂停"),
        check("高风险任务不进入真实执行", all("真实执行" not in item.get("放行结论", "") or "不进入真实执行" in item.get("放行结论", "") for item in plans if item.get("风险等级") == "高"), "高风险仅评审"),
        check("所有真实动作开关关闭", all(value is False for value in safety_values), "只生成预案"),
        check("每个预案包含回滚要求", all(item.get("回滚要求") for item in plans), "回滚要求完整"),
        check("每个预案包含禁止动作", all(item.get("禁止动作") for item in plans), "禁止动作完整"),
    ]
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "daily-task-release-plan-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "日常可用版"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "daily-task-release-plan-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
