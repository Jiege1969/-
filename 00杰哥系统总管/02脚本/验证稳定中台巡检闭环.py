"""
名称：验证稳定中台巡检闭环.py
作用：验证稳定中台巡检计划和只读巡检执行报告，确认阻断当前主线的巡检项通过且安全边界关闭。
触发方式：python 验证稳定中台巡检闭环.py
依赖：Python 标准库；生成稳定中台巡检计划.py；执行稳定中台只读巡检.py。
所属系统：00杰哥系统总管
安全边界：只生成计划和只读巡检报告；不创建计划任务；不重启服务；不触发n8n；不发送企业微信；不写旧系统。
创建/修改记录：2026-04-27 创建稳定中台巡检闭环验收脚本；2026-05-04 区分阻断当前主线与非阻断诊断项。
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


def run_script(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = v3_root()
    plan_result = run_script(root / "00杰哥系统总管" / "02脚本" / "生成稳定中台巡检计划.py")
    patrol_result = run_script(root / "00杰哥系统总管" / "02脚本" / "执行稳定中台只读巡检.py")
    plan_path = root / "00杰哥系统总管" / "03数据" / "稳定中台" / "稳定中台巡检计划_最新.json"
    patrol_path = root / "00杰哥系统总管" / "04日志" / "稳定中台" / "stable-hub-readonly-patrol-最新.json"
    plan = load_json(plan_path) if plan_path.exists() else {}
    patrol = load_json(patrol_path) if patrol_path.exists() else {}
    switches = list(plan.get("执行开关", {}).values()) + list(patrol.get("执行开关", {}).values())
    checks = [
        check("巡检计划生成成功", plan_result.returncode == 0, plan_result.stdout.strip() or plan_result.stderr.strip()),
        check("只读巡检执行成功", patrol_result.returncode == 0, patrol_result.stdout.strip() or patrol_result.stderr.strip()),
        check("巡检计划存在", plan_path.exists(), str(plan_path)),
        check("巡检报告存在", patrol_path.exists(), str(patrol_path)),
        check("阻断当前主线巡检项全部通过", patrol.get("汇总", {}).get("失败") == 0, patrol.get("汇总", {})),
        check("非阻断失败项已进入诊断记录", patrol.get("汇总", {}).get("非阻断失败", 0) >= 0 and "非阻断失败项" in patrol, {"非阻断失败": patrol.get("汇总", {}).get("非阻断失败")}),
        check("巡检项目数量匹配", len(plan.get("巡检项目", [])) == patrol.get("汇总", {}).get("项目总数"), {"计划": len(plan.get("巡检项目", [])), "报告": patrol.get("汇总", {}).get("项目总数")}),
        check("安全边界全部关闭", all(value is False for value in switches), {"开关数量": len(switches)}),
    ]
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stable-hub-patrol-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "00杰哥系统总管" / "04日志" / "稳定中台"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"stable-hub-patrol-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if report["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
