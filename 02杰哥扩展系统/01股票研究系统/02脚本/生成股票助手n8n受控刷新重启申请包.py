# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-n8n-controlled-refresh-restart-request-package.py
Purpose: Generate a controlled refresh/restart request package for isolated n8n webhook registration.
Trigger: python 生成股票助手n8n受控刷新重启申请包.py
Dependencies: Python standard library; n8n controlled refresh/restart rule; core refresh/restart config verifier.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Generates request and verification material only; does not restart, enable, trigger, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created controlled refresh/restart request package generator.
Marker: stock-assistant-n8n-controlled-refresh-restart-request-package-generate
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
        "# 股票助手n8n受控刷新重启申请包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、申请结论",
        "",
        f"- 是否具备申请条件：{report['是否具备申请条件']}",
        f"- 是否已执行重启：{report['是否已执行重启']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 二、申请原因",
        "",
    ]
    for item in report["申请原因"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、回滚策略", ""])
    for item in report["回滚策略"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、验收标准", ""])
    for item in report["验收标准"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    v3_root = system_root()
    rule_path = root / "01配置" / "股票助手n8n受控刷新重启申请规则.json"
    rule = load_json(rule_path)
    core_verifier = v3_root / "01杰哥智能系统" / "02脚本" / "验证隔离n8n受控刷新重启配置.py"
    completed = subprocess.run([sys.executable, str(core_verifier)], check=False, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    core_latest = v3_root / "01杰哥智能系统" / "04日志" / "隔离n8n受控刷新重启配置" / "isolated-n8n-controlled-refresh-restart-config-verify-最新.json"
    core_result = load_json(core_latest)
    ready = completed.returncode == 0 and core_result.get("失败", 1) == 0
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "核心侧验证脚本": str(core_verifier),
        "核心侧验证日志": str(core_latest),
        "核心侧验证结果": core_result,
        "申请原因": rule.get("申请原因", []),
        "允许对象": rule.get("允许对象", {}),
        "禁止触碰": rule.get("禁止触碰", []),
        "受控动作边界": rule.get("受控动作边界", {}),
        "回滚策略": rule.get("回滚策略", []),
        "验收标准": rule.get("验收标准", []),
        "是否具备申请条件": ready,
        "是否已执行重启": False,
        "当前结论": "已具备受控刷新/重启申请材料；本包未执行重启，后续只能在明确放行后重启jiege_v3_n8n，不得触碰旧系统。",
        "实际动作": {
            "生成申请包": True,
            "验证受控重启脚本": True,
            "重启n8n": False,
            "启用Webhook": False,
            "触发Webhook": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "76n8n受控刷新重启申请"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手n8n受控刷新重启申请包_{stamp}.json"
    latest_json = output_dir / "股票助手n8n受控刷新重启申请包_最新.json"
    output_md = output_dir / f"股票助手n8n受控刷新重启申请包_{stamp}.md"
    latest_md = output_dir / "股票助手n8n受控刷新重启申请包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备申请条件": ready, "是否已执行重启": False, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
