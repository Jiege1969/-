# -*- coding: utf-8 -*-
"""
名称：验证单股即时研究报告.py
作用：验证单股即时研究报告可生成，并确认报告包含数据健康度、行情事实、技术指标、分层、风险和安全边界。
触发方式：python 验证单股即时研究报告.py
依赖：Python标准库；生成单股即时研究报告.py；本地股票研究数据。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地报告验收；不联网；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建单股即时研究报告验收脚本。
标识：stock-single-instant-report-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成单股即时研究报告.py"
    samples = ["新易盛", "浙商中拓", "海光信息"]
    runs = [
        subprocess.run([sys.executable, str(generator), "--stock", stock], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        for stock in samples
    ]
    latest_json = root / "03数据" / "23单股即时报告" / "单股即时研究报告_最新.json"
    latest_md = root / "03数据" / "23单股即时报告" / "单股即时研究报告_最新.md"
    report = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    safety = report.get("安全边界", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "样例报告全部生成成功", all(run.returncode == 0 for run in runs), [{"stdout": run.stdout.strip(), "stderr": run.stderr.strip()} for run in runs])
    add_check(checks, "最新JSON存在", latest_json.exists() and bool(report.get("股票")), str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "单股即时研究报告" in text, str(latest_md))
    add_check(checks, "包含数据健康度", "数据健康度" in text and bool(report.get("数据健康度")), report.get("数据健康度", {}))
    add_check(checks, "包含行情事实", "行情事实" in text and bool(report.get("行情")), report.get("行情", {}))
    add_check(checks, "包含技术指标", "技术指标" in text and bool(report.get("技术指标")), report.get("技术指标", {}))
    add_check(checks, "包含系统分层", "系统分层" in text and bool(report.get("研判", {}).get("层级")), report.get("研判", {}))
    add_check(checks, "包含风险", "风险" in text, text[:500])
    add_check(checks, "高风险动作关闭", all(value is False for value in safety.values()), safety)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    output = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "单股即时研究报告可生成并可复用到企业微信查询。" if failed == 0 else "单股即时研究报告存在失败项。",
    }
    output_dir = root / "04日志" / "单股即时报告"
    output_path = output_dir / f"stock-single-instant-report-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-single-instant-report-verify-最新.json"
    write_json(output_path, output)
    write_json(latest, output)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output_path)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
