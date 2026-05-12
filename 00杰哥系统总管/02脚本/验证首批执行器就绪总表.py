# -*- coding: utf-8 -*-
"""
名称：验证首批执行器就绪总表.py
作用：生成并验证首批执行器就绪总表，确认R01/R02/R03均就绪但冻结。
触发方式：python 验证首批执行器就绪总表.py
依赖：Python 标准库；生成首批执行器就绪总表.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证总表；不联网；不写库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建首批执行器就绪总表验证脚本。
标识：first-batch-executor-readiness-table-verify
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
    script = manager / "02脚本" / "生成首批执行器就绪总表.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "小流量只读执行" / "首批执行器就绪总表_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    rows = report.get("执行器", [])
    summary = report.get("汇总", {})
    checks = [
        check("总表生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("总表文件存在", report_path.exists(), str(report_path)),
        check("执行器数量为三个", summary.get("执行器数量") == 3, summary),
        check("三个执行器均就绪但冻结", summary.get("就绪但冻结数量") == 3, rows),
        check("真实动作数量为零", summary.get("真实动作数量") == 0, summary),
        check("R01存在", any(item.get("任务编号") == "R01" for item in rows), rows),
        check("R02存在", any(item.get("任务编号") == "R02" for item in rows), rows),
        check("R03存在", any(item.get("任务编号") == "R03" for item in rows), rows),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "first-batch-executor-readiness-table-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "小流量只读执行"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"first-batch-executor-readiness-table-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "first-batch-executor-readiness-table-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
