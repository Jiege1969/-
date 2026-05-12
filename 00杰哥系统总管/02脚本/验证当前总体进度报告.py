"""
名称：验证当前总体进度报告.py
作用：生成并验证当前总体进度报告，确认统一进度口径、总体验收和真实动作关闭状态完整。
触发方式：python 验证当前总体进度报告.py
依赖：Python 标准库；生成当前总体进度报告.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证进度报告；不联网；不写库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建当前总体进度报告验收脚本；2026-04-28 适配范围值进度口径。
标识：current-progress-report-verify
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


def has_range(value: Any) -> bool:
    return isinstance(value, dict) and isinstance(value.get("下限"), int) and isinstance(value.get("上限"), int) and value.get("下限") <= value.get("上限")


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    script = manager / "02脚本" / "生成当前总体进度报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "阶段判定" / "当前总体进度报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    closed = report.get("仍然关闭", [])
    progress = report.get("进度估算", {})
    rules = report.get("进度口径说明", {})
    checks = [
        check("进度报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("进度报告存在", report_path.exists(), str(report_path)),
        check("进度口径说明存在", bool(rules.get("核心原则")) and bool(rules.get("禁止混用")), rules),
        check("总体进度为范围值", has_range(progress.get("多功能智能体总体")), progress.get("多功能智能体总体")),
        check("基础阶段进度为范围值", has_range(progress.get("基础可用版阶段")), progress.get("基础可用版阶段")),
        check("股票系统进度为范围值", has_range(progress.get("股票研究系统")), progress.get("股票研究系统")),
        check("真实动作未放行", report.get("最终闸口", {}).get("是否允许真实动作") is False, report.get("最终闸口", {})),
        check("税收仍关闭", any("税收" in item for item in closed), closed),
        check("旧系统写入仍关闭", any("旧系统" in item for item in closed), closed),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "current-progress-report-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "阶段判定"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"current-progress-report-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "current-progress-report-verify-最新.json"
    text = json.dumps(verify, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
