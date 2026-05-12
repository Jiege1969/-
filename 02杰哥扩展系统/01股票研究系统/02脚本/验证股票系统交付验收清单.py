# -*- coding: utf-8 -*-
"""
名称：验证股票系统交付验收清单.py
作用：验证股票系统交付验收清单已生成，并明确本地可用、企业微信禁用态可用、n8n禁用态可用、真实灰度可用和最终交付可用的边界。
触发方式：python 验证股票系统交付验收清单.py
依赖：Python标准库；生成股票系统交付验收清单.py；股票系统交付验收清单规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地交付验收清单验收；不重启服务；不导入n8n；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票系统交付验收清单验收脚本。
标识：stock-delivery-acceptance-checklist-verify
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
    generator = root / "02脚本" / "生成股票系统交付验收清单.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "35交付验收清单" / "股票系统交付验收清单_最新.json"
    latest_md = root / "03数据" / "35交付验收清单" / "股票系统交付验收清单_最新.md"
    report = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    layers = [item.get("层级") for item in report.get("验收层级", [])]
    actions = report.get("实际动作", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "生成脚本执行成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists() and len(report.get("验收层级", [])) == 5, str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "股票系统交付验收清单" in text, str(latest_md))
    add_check(checks, "验收层级完整", all(name in layers for name in ["A本地可用", "B企业微信禁用态可用", "Cn8n禁用态可用", "D真实灰度可用", "E交付可用"]), layers)
    add_check(checks, "明确禁止误判", "本地脚本验收通过不等于企业微信真实可用" in text and "n8n工作流草案生成不等于已经导入n8n" in text, "禁止误判")
    add_check(checks, "真实灰度未误判为交付", report.get("当前可交付层级") != "E交付可用", report.get("当前可交付层级"))
    add_check(checks, "高风险动作未执行", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票系统交付验收清单可用。" if failed == 0 else "股票系统交付验收清单存在失败项。",
    }
    output_dir = root / "04日志" / "交付验收清单"
    output = output_dir / f"stock-delivery-acceptance-checklist-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-delivery-acceptance-checklist-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
