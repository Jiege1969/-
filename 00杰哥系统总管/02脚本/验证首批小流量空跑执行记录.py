# -*- coding: utf-8 -*-
"""
名称：验证首批小流量空跑执行记录.py
作用：生成并验证首批小流量空跑执行记录，确认只空跑、不触发真实动作。
触发方式：python 验证首批小流量空跑执行记录.py
依赖：Python 标准库；生成首批小流量空跑执行记录.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证dry_run空跑记录；不联网；不写库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建首批小流量空跑执行记录验证脚本。
标识：first-batch-dry-run-record-verify
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
    script = manager / "02脚本" / "生成首批小流量空跑执行记录.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "小流量只读执行" / "首批小流量空跑执行记录_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    tasks = report.get("空跑任务", [])
    summary = report.get("汇总", {})
    switches = report.get("默认开关", {})
    report_text = json.dumps(report, ensure_ascii=False)
    checks = [
        check("空跑记录生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("空跑记录文件存在", report_path.exists(), str(report_path)),
        check("执行模式为dry_run", report.get("执行模式") == "dry_run", report.get("执行模式")),
        check("至少空跑三个任务", len(tasks) >= 3, len(tasks)),
        check("全部任务空跑通过", all(item.get("空跑结果") == "通过" for item in tasks), tasks),
        check("真实动作数为零", summary.get("真实动作数") == 0, summary),
        check("n8n触发数为零", summary.get("n8n触发数") == 0, summary),
        check("正式库写入数为零", summary.get("正式库写入数") == 0, summary),
        check("企业微信发送数为零", summary.get("企业微信发送数") == 0, summary),
        check("真实联网关闭", switches.get("允许真实联网") is False, switches),
        check("税收业务关闭", switches.get("允许税收业务") is False and "税收业务系统" not in report_text, switches),
        check("旧系统写入关闭", switches.get("允许旧系统写入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "first-batch-dry-run-record-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "小流量只读执行"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"first-batch-dry-run-record-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
