# -*- coding: utf-8 -*-
"""
名称：验证真实小流量执行许可令.py
作用：生成并验证真实小流量执行许可令，确认全部未签发且不允许真实执行。
触发方式：python 验证真实小流量执行许可令.py
依赖：Python 标准库；生成真实小流量执行许可令.py。
所属系统：00杰哥系统总管
安全边界：只生成和验证未签发许可令；不联网；不写库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建真实小流量执行许可令验证脚本。
标识：real-execution-permit-order-verify
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
    script = manager / "02脚本" / "生成真实小流量执行许可令.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = manager / "03数据" / "小流量只读执行" / "真实小流量执行许可令_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    orders = report.get("许可令", [])
    switches = report.get("默认开关", {})
    report_text = json.dumps(report, ensure_ascii=False)
    checks = [
        check("许可令生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("许可令文件存在", report_path.exists(), str(report_path)),
        check("至少生成三个许可令", len(orders) >= 3, len(orders)),
        check("全部许可令未签发", all(item.get("签发状态") == "未签发" for item in orders), orders),
        check("全部许可令不允许执行", all(item.get("是否允许执行") is False for item in orders), orders),
        check("允许执行数量为零", report.get("汇总", {}).get("允许执行数量") == 0, report.get("汇总", {})),
        check("真实联网关闭", switches.get("允许真实联网") is False, switches),
        check("正式库写入关闭", switches.get("允许正式库写入") is False, switches),
        check("企业微信真实发送关闭", switches.get("允许企业微信真实发送") is False, switches),
        check("n8n真实触发关闭", switches.get("允许n8n真实触发") is False, switches),
        check("税收业务关闭", switches.get("允许税收业务") is False and "税收业务系统" not in report_text, switches),
        check("旧系统写入关闭", switches.get("允许旧系统写入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "real-execution-permit-order-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = manager / "04日志" / "小流量只读执行"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"real-execution-permit-order-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "real-execution-permit-order-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
