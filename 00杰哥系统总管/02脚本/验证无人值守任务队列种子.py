# -*- coding: utf-8 -*-
"""
名称：验证无人值守任务队列种子.py
作用：生成并验证无人值守任务队列种子，确认样例任务状态合法且未触发执行器或n8n。
触发方式：python 验证无人值守任务队列种子.py
依赖：Python 标准库；生成无人值守任务队列种子.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证样例任务队列；不触发执行器；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建无人值守任务队列种子验证脚本。
标识：unattended-task-queue-seed-verify
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


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    script = manager / "02脚本" / "生成无人值守任务队列种子.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "无人值守守护" / "无人值守任务队列种子_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    queue = report.get("任务队列", [])
    summary = report.get("汇总", {})
    switches = report.get("默认开关", {})
    checks = [
        check("任务队列种子生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("任务队列种子文件存在", report_path.exists(), str(report_path)),
        check("至少四个样例任务", summary.get("任务数量", 0) >= 4, summary),
        check("所有任务状态合法", all(item.get("状态是否合法") is True for item in queue), queue),
        check("包含禁止执行样例", summary.get("禁止执行数量", 0) >= 1, summary),
        check("未触发执行器", summary.get("触发执行器数量") == 0, summary),
        check("未触发n8n", summary.get("触发n8n数量") == 0, summary),
        check("执行器触发开关关闭", switches.get("允许触发执行器") is False, switches),
        check("n8n触发开关关闭", switches.get("允许触发n8n") is False, switches),
        check("税收业务关闭", switches.get("允许税收业务") is False, switches),
        check("旧系统写入关闭", switches.get("允许旧系统写入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "unattended-task-queue-seed-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "无人值守守护"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "unattended-task-queue-seed-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
