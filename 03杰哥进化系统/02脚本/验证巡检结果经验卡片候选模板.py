# -*- coding: utf-8 -*-
"""
名称：验证巡检结果经验卡片候选模板.py
作用：生成并验证巡检结果经验卡片候选模板，确认当前只生成候选，不进入正式经验库。
触发方式：python 验证巡检结果经验卡片候选模板.py
依赖：Python标准库；生成巡检结果经验卡片候选模板.py。
所属系统：03杰哥进化系统
安全边界：只生成和验证经验候选模板；不生成正式经验卡片；不自动提炼通用方法；不自动固化规则；不删除；不移动；不写旧系统。
创建/修改记录：2026-04-28 创建巡检结果经验卡片候选模板验证脚本。
标识：patrol-result-experience-candidate-template-verify
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
    evolution = evolution_root()
    generator = evolution / "02脚本" / "生成巡检结果经验卡片候选模板.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = evolution / "03数据" / "06巡检经验候选" / "巡检结果经验卡片候选模板_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    summary = report.get("汇总", {})
    switches = report.get("默认开关", {})
    checks = [
        check("候选模板生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("候选模板文件存在", report_path.exists(), str(report_path)),
        check("候选数量足够", summary.get("候选数量", 0) >= 5, summary),
        check("正式经验卡片数量为零", summary.get("正式经验卡片数量") == 0, summary),
        check("自动提炼通用方法数量为零", summary.get("自动提炼通用方法数量") == 0, summary),
        check("自动固化规则数量为零", summary.get("自动固化规则数量") == 0, summary),
        check("删除样本数量为零", summary.get("删除样本数量") == 0, summary),
        check("移动样本数量为零", summary.get("移动样本数量") == 0, summary),
        check("写旧系统数量为零", summary.get("写旧系统数量") == 0, summary),
        check("正式经验卡片开关关闭", switches.get("允许生成正式经验卡片") is False, switches),
        check("自动提炼开关关闭", switches.get("允许自动提炼通用方法") is False, switches),
        check("自动固化开关关闭", switches.get("允许自动固化规则") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "patrol-result-experience-candidate-template-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = evolution / "04日志" / "巡检经验候选"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"patrol-result-experience-candidate-template-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "patrol-result-experience-candidate-template-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
