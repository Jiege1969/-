"""
名称：验证本职工作底座.py
作用：验证 v3 本职工作系统第一阶段配置、模板和任务计划脚本是否可用。
触发方式：python 验证本职工作底座.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读取 v3 本职工作配置，只运行本地计划脚本；不读取真实涉密资料、不自动发送。
创建/修改记录：2026-04-26 创建第一阶段本职工作底座验证脚本。
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


def module_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "03本职工作系统"


def log_dir() -> Path:
    target = v3_root() / "00杰哥系统总管" / "04日志" / "本职工作验收"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {
        "检查项": name,
        "结果": "通过" if condition else "失败",
        "详情": detail,
    }


def main() -> int:
    root = module_root()
    config = load_json(root / "01配置" / "本职工作配置.json")
    template = load_json(root / "01配置" / "办公材料模板.json")
    script = root / "02脚本" / "生成办公材料计划.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    latest_plan = root / "03数据" / "02任务计划" / "办公材料计划_最新.json"
    latest_draft = root / "03数据" / "03输出草稿" / "办公材料草稿框架_最新.json"
    plan_data = load_json(latest_plan) if latest_plan.exists() else {}
    draft_data = load_json(latest_draft) if latest_draft.exists() else {}

    checks = [
        check("本职工作配置", "材料类型" in config and "输出规则" in config, config.get("说明")),
        check("办公材料模板", "模板" in template and isinstance(template.get("模板"), list), template.get("说明")),
        check("计划脚本执行", result.returncode == 0, (result.stdout or "").strip() or (result.stderr or "").strip()),
        check("最新任务计划", latest_plan.exists(), str(latest_plan)),
        check("任务计划结构", "任务列表" in plan_data and "安全边界" in plan_data, plan_data.get("材料类型")),
        check("最新草稿框架", latest_draft.exists(), str(latest_draft)),
        check("草稿框架结构", "草稿模板" in draft_data and "默认风格" in draft_data, draft_data.get("默认风格")),
    ]

    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "work-base-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output = log_dir() / f"work-base-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest_output = log_dir() / "work-base-verify-最新.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
