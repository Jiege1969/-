# -*- coding: utf-8 -*-
"""
名称：验证巡检结果经验卡片候选汇总.py
作用：作为00总管验收入口，调用03进化系统的巡检结果经验卡片候选模板验证脚本并汇总结果。
触发方式：python 验证巡检结果经验卡片候选汇总.py
依赖：Python标准库；03杰哥进化系统/02脚本/验证巡检结果经验卡片候选模板.py。
所属系统：00杰哥系统总管
安全边界：只调用候选模板验证脚本并写入总管日志；不生成正式经验卡片；不自动提炼；不自动固化；不删除；不移动；不写旧系统。
创建/修改记录：2026-04-28 创建总管层巡检结果经验卡片候选汇总验证入口。
标识：patrol-result-experience-candidate-template-verify
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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    script = root / "03杰哥进化系统" / "02脚本" / "验证巡检结果经验卡片候选模板.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    passed = result.returncode == 0
    report = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "patrol-result-experience-candidate-template-verify",
        "被调用脚本": str(script),
        "返回码": result.returncode,
        "输出": result.stdout.strip(),
        "错误": result.stderr.strip(),
        "安全边界": {
            "是否生成正式经验卡片": False,
            "是否自动提炼": False,
            "是否自动固化": False,
            "是否删除": False,
            "是否移动": False,
            "是否写旧系统": False
        },
        "汇总": {
            "通过": 1 if passed else 0,
            "失败": 0 if passed else 1
        }
    }
    output_dir = manager / "04日志" / "进化系统"
    output = output_dir / f"patrol-result-experience-candidate-manager-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "patrol-result-experience-candidate-manager-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps(report["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
