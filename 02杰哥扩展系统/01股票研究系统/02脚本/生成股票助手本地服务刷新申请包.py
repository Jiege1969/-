# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-local-service-refresh-request-package.py
Purpose: Generate a controlled local stock assistant service refresh request package.
Trigger: python 生成股票助手本地服务刷新申请包.py
Dependencies: Python standard library; local delivery functional acceptance package.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Generates request material only; does not restart service, enable or trigger Webhook, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created local stock assistant service refresh request package generator.
Marker: stock-assistant-local-service-refresh-request-package-generate
"""

from __future__ import annotations

import json
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手本地服务刷新申请包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、申请结论",
        "",
        f"- 是否具备刷新申请条件：{report['是否具备刷新申请条件']}",
        f"- 是否已执行服务刷新：{report['实际动作']['刷新本地股票助手服务']}",
        "",
        "## 二、申请原因",
        "",
    ]
    for item in report["申请原因"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、刷新后验收", ""])
    for item in report["刷新后验收"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、禁止事项", ""])
    for item in report["禁止事项"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手本地服务刷新申请规则.json"
    local_acceptance = root / "03数据" / "81股票助手本地交付功能验收包" / "股票助手本地交付功能验收包_最新.json"
    rule = load_json(rule_path)
    acceptance = load_json(local_acceptance)
    ready = acceptance.get("核心本地查询能力是否可用") is True and acceptance.get("是否达到本地交付功能要求") is False
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "本地功能验收包": str(local_acceptance),
        "申请原因": rule.get("申请原因", []),
        "允许对象": rule.get("允许对象", []),
        "禁止事项": rule.get("禁止事项", []),
        "刷新后验收": rule.get("刷新后验收", []),
        "当前未通过项": acceptance.get("未通过项", []),
        "是否具备刷新申请条件": ready,
        "实际动作": {
            "生成申请包": True,
            "刷新本地股票助手服务": False,
            "重启n8n": False,
            "启用Webhook": False,
            "触发Webhook": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }
    output_dir = root / "03数据" / "82股票助手本地服务刷新申请包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手本地服务刷新申请包_{stamp}.json"
    latest_json = output_dir / "股票助手本地服务刷新申请包_最新.json"
    output_md = output_dir / f"股票助手本地服务刷新申请包_{stamp}.md"
    latest_md = output_dir / "股票助手本地服务刷新申请包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备刷新申请条件": ready, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
