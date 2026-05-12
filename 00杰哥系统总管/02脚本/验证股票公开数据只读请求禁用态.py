"""
名称：验证股票公开数据只读请求禁用态.py
作用：执行并验证股票公开数据只读请求执行器禁用态检查，确认不联网、不抓取、不交易、不写旧系统、不触发n8n、不发送企业微信、不接入税收。
触发方式：python 验证股票公开数据只读请求禁用态.py
依赖：Python 标准库；执行股票公开数据只读请求禁用态检查.py。
所属系统：00杰哥系统总管
安全边界：只执行禁用态检查；不联网；不抓取行情；不调用券商接口；不交易；不写入旧系统；不触发n8n；不发送企业微信；不接入税收。
创建/修改记录：2026-04-27 创建股票公开数据只读请求禁用态验收脚本。
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


def stock_root() -> Path:
    return v3_root() / "02杰哥扩展系统" / "01股票研究系统"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, condition: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if condition else "失败", "详情": detail}


def main() -> int:
    root = stock_root()
    script = root / "02脚本" / "执行股票公开数据只读请求禁用态检查.py"
    result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    report_path = root / "03数据" / "06公开数据探测" / "股票公开数据只读请求禁用态检查_最新.json"
    report = load_json(report_path) if report_path.exists() else {}
    switches = report.get("禁用开关", {})
    checks = [
        check("禁用态检查生成成功", result.returncode == 0, result.stdout.strip() or result.stderr.strip()),
        check("禁用态检查报告存在", report_path.exists(), str(report_path)),
        check("执行器为禁用态", report.get("执行器状态") == "禁用态", report.get("执行器状态")),
        check("未执行联网请求", report.get("是否执行联网请求") is False, report.get("是否执行联网请求")),
        check("联网请求关闭", switches.get("联网请求") is False, switches),
        check("行情抓取关闭", switches.get("行情抓取") is False, switches),
        check("券商接口关闭", switches.get("券商接口") is False, switches),
        check("自动交易关闭", switches.get("自动交易") is False, switches),
        check("旧系统写入关闭", switches.get("旧系统写入") is False, switches),
        check("n8n触发关闭", switches.get("n8n触发") is False, switches),
        check("企业微信发送关闭", switches.get("企业微信发送") is False, switches),
        check("税收接入关闭", switches.get("税收接入") is False, switches),
    ]
    verify = {
        "验证时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stock-readonly-request-disabled-verify",
        "汇总": {
            "通过": sum(1 for item in checks if item["结果"] == "通过"),
            "失败": sum(1 for item in checks if item["结果"] != "通过"),
        },
        "检查结果": checks,
    }
    output_dir = v3_root() / "00杰哥系统总管" / "04日志" / "股票公开数据探测"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"stock-readonly-request-disabled-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-readonly-request-disabled-verify-最新.json"
    output.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(verify, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verify["汇总"], ensure_ascii=False))
    print(str(output))
    return 0 if verify["汇总"]["失败"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
