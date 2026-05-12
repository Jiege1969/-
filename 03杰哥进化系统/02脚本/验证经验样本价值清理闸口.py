# -*- coding: utf-8 -*-
"""
名称：验证经验样本价值清理闸口.py
作用：生成并验证经验样本价值清理闸口报告，确认清理依据是价值提炼而非时间，且当前不执行清理动作。
触发方式：python 验证经验样本价值清理闸口.py
依赖：Python标准库；生成经验样本价值清理闸口报告.py。
所属系统：03杰哥进化系统
安全边界：只生成和验证候选清单；不删除；不移动；不覆盖；不自动归档；不自动固化方法；不写旧系统。
创建/修改记录：2026-04-28 创建经验样本价值清理闸口验证脚本。
标识：evolution-sample-cleanup-gate-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def evolution_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = evolution_root()
    script = root / "02脚本" / "生成经验样本价值清理闸口报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "06清理闸口" / "经验样本价值清理闸口报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    summary = report.get("汇总", {})
    switches = report.get("默认开关", {})
    principle = report.get("生命周期原则", "")
    checks = [
        check("清理闸口报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("清理闸口报告文件存在", report_path.exists(), str(report_path)),
        check("清理依据不是时间", "不是时间长短" in principle and "价值提炼" in principle, principle),
        check("样本数量大于零", summary.get("样本数量", 0) > 0, summary),
        check("通用方法来源存在", summary.get("通用方法来源卡片数量", 0) > 0, summary),
        check("能够生成归档候选", summary.get("人工归档候选数量", 0) > 0, summary),
        check("删除数量为零", summary.get("删除数量") == 0, summary),
        check("移动数量为零", summary.get("移动数量") == 0, summary),
        check("覆盖数量为零", summary.get("覆盖数量") == 0, summary),
        check("删除开关关闭", switches.get("允许删除样本") is False, switches),
        check("移动开关关闭", switches.get("允许移动样本") is False, switches),
        check("自动归档开关关闭", switches.get("允许自动归档") is False, switches),
        check("只生成候选清单开启", switches.get("允许只生成候选清单") is True, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "evolution-sample-cleanup-gate-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = root / "04日志" / "清理闸口"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"evolution-sample-cleanup-gate-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "evolution-sample-cleanup-gate-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
