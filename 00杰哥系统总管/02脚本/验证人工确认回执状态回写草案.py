# -*- coding: utf-8 -*-
"""
名称：验证人工确认回执状态回写草案.py
作用：生成并验证人工确认回执状态回写草案，确认其不自动回写状态、不签发许可令、不触发真实动作。
触发方式：python 验证人工确认回执状态回写草案.py
依赖：Python标准库；生成人工确认回执状态回写草案.py；验证日常任务人工确认单.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证回执草案；不回写任务状态；不签发许可令；不触发执行器；不触发n8n；不发送企业微信；不写正式库；不写旧系统。
创建/修改记录：2026-04-28 创建人工确认回执状态回写草案验证脚本。
标识：human-confirmation-receipt-state-writeback-draft-verify
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
    confirm_verify = manager / "02脚本" / "验证日常任务人工确认单.py"
    generator = manager / "02脚本" / "生成人工确认回执状态回写草案.py"
    confirm_result = subprocess.run([sys.executable, str(confirm_verify)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "人工确认回执" / "人工确认回执状态回写草案_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    summary = report.get("汇总", {})
    switches = report.get("默认开关", {})
    receipts = report.get("回执草案", [])
    blocked_receipts = [item for item in receipts if item.get("命中阻断类型")]
    checks = [
        check("人工确认单可生成", confirm_result.returncode == 0, confirm_result.stdout.strip() or confirm_result.stderr.strip()),
        check("回执草案生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("回执草案文件存在", report_path.exists(), str(report_path)),
        check("回执数量大于零", summary.get("回执数量", 0) > 0, summary),
        check("存在阻断回执", summary.get("阻断回执数量", 0) > 0, summary),
        check("回写任务状态为零", summary.get("回写任务状态数量") == 0, summary),
        check("签发许可令为零", summary.get("签发许可令数量") == 0, summary),
        check("触发执行器为零", summary.get("触发执行器数量") == 0, summary),
        check("触发n8n为零", summary.get("触发n8n数量") == 0, summary),
        check("真实发送为零", summary.get("真实发送数量") == 0, summary),
        check("写正式库为零", summary.get("写正式库数量") == 0, summary),
        check("写旧系统为零", summary.get("写旧系统数量") == 0, summary),
        check("自动回写开关关闭", switches.get("允许自动回写任务状态") is False, switches),
        check("自动签发许可令关闭", switches.get("允许自动签发许可令") is False, switches),
        check("阻断回执不能直接同意", all("同意进入许可令草案" not in item.get("允许决策", []) for item in blocked_receipts), blocked_receipts),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "human-confirmation-receipt-state-writeback-draft-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "人工确认回执"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"human-confirmation-receipt-state-writeback-draft-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "human-confirmation-receipt-state-writeback-draft-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
