# -*- coding: utf-8 -*-
"""
名称：验证智能决策样例推演.py
作用：生成并验证智能决策样例推演报告，确认低风险任务可进入只读/临时链路，高风险、税收和真实发送被阻断。
触发方式：python 验证智能决策样例推演.py
依赖：Python 标准库；生成智能决策样例推演报告.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证样例推演报告；不调用模型；不触发n8n；不发送企业微信；不接入税收；不写入旧系统；不删除文件。
创建/修改记录：2026-04-27 创建智能决策样例推演验证脚本。
标识：decision-sample-simulation-verify
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
    script = manager / "02脚本" / "生成智能决策样例推演报告.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "智能决策内核" / "智能决策样例推演报告_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    rows = report.get("样例推演", [])
    summary = report.get("汇总", {})
    switches = report.get("默认开关", {})
    checks = [
        check("样例推演报告生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("样例推演报告文件存在", report_path.exists(), str(report_path)),
        check("样例数量不少于六个", summary.get("样例数量", 0) >= 6, summary),
        check("真实动作数量为零", summary.get("真实动作数量") == 0, summary),
        check("所有样例符合预期", summary.get("符合预期数量") == summary.get("样例数量"), summary),
        check("税收业务被阻断", any(item.get("任务类型") == "税收业务" and item.get("是否阻断") is True for item in rows), rows),
        check("企业微信真实发送被阻断", any(item.get("任务类型") == "企业微信助手" and item.get("是否阻断") is True for item in rows), rows),
        check("旧系统删除类动作被阻断", any("删除旧系统" in item.get("输入", "") and item.get("是否阻断") is True for item in rows), rows),
        check("税收业务开关关闭", switches.get("允许税收业务") is False, switches),
        check("旧系统写入开关关闭", switches.get("允许旧系统写入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "decision-sample-simulation-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "智能决策内核"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"decision-sample-simulation-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
