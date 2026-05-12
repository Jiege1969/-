# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-wework-controlled-send-gate-package.py
Purpose: Generate a stock assistant package that records the controlled WeWork send gate state.
Trigger: python 生成股票助手企业微信受控发送闸口包.py
Dependencies: Python standard library; 00公共组件/02脚本/企业微信受控发送闸口.py.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Runs check-only send gate and writes stock package reports only; does not call WeWork APIs, send messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created stock assistant controlled WeWork send gate package generator.
Marker: stock-assistant-wework-controlled-send-gate-package-generate
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


def system_root() -> Path:
    return module_root().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手企业微信受控发送闸口包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        f"- 是否允许真实发送：{report['是否允许真实发送']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 闸口检查",
        "",
    ]
    for item in report["闸口结果"].get("检查结果", []):
        lines.append(f"- {item['检查项']}：{item['通过']}，{item['说明']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    v3_root = system_root()
    gate = v3_root / "02杰哥扩展系统" / "00公共组件" / "02脚本" / "企业微信受控发送闸口.py"
    completed = subprocess.run([sys.executable, str(gate), "--check-only"], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    gate_latest = v3_root / "02杰哥扩展系统" / "00公共组件" / "04日志" / "企业微信受控发送闸口" / "wework-controlled-send-gate-最新.json"
    gate_result = load_json(gate_latest)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "闸口脚本": str(gate),
        "闸口日志": str(gate_latest),
        "返回码": completed.returncode,
        "标准输出": completed.stdout.strip(),
        "标准错误": completed.stderr.strip(),
        "闸口结果": gate_result,
        "是否允许真实发送": gate_result.get("是否允许真实发送") is True,
        "当前结论": "真实企业微信发送仍未放行；股票助手只能继续本地灰度和受控准备。",
        "实际动作": {
            "运行受控发送闸口检查": True,
            "调用企业微信API": False,
            "发送企业微信": False,
            "启用n8n": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        },
    }
    output_dir = root / "03数据" / "73企业微信受控发送闸口"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手企业微信受控发送闸口包_{stamp}.json"
    latest_json = output_dir / "股票助手企业微信受控发送闸口包_最新.json"
    output_md = output_dir / f"股票助手企业微信受控发送闸口包_{stamp}.md"
    latest_md = output_dir / "股票助手企业微信受控发送闸口包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否允许真实发送": report["是否允许真实发送"], "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
