# -*- coding: utf-8 -*-
"""
名称：生成OpenClaw股票消息桥接禁用态契约.py
作用：根据OpenClaw股票消息桥接禁用态契约配置，生成股票企业微信到n8n桥接的禁用态契约报告。
触发方式：python 生成OpenClaw股票消息桥接禁用态契约.py
依赖：Python标准库；OpenClaw股票消息桥接禁用态契约.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置并写入股票模块03数据目录；不调用OpenClaw；不触发n8n；不启用Webhook；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-28 创建OpenClaw股票消息桥接禁用态契约生成脚本。
标识：stock-openclaw-message-bridge-contract-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenClaw股票消息桥接禁用态契约",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 当前结论：{report['当前结论']}",
        "- OpenClaw只做南北向消息代理，不写业务判断。",
        "- n8n是唯一逻辑编排中心。",
        "- 当前只生成禁用态契约，不调用真实OpenClaw、不启用Webhook、不发送企业微信。",
        "",
        "## 二、角色定位",
        "",
    ]
    for key, value in report["定位"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、禁止事项", ""])
    for item in report["禁止事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、入站字段", ""])
    for key, value in report["入站消息字段"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、OpenClaw转发n8n字段", ""])
    for key, value in report["OpenClaw转发到n8n字段"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 六、n8n返回OpenClaw字段", ""])
    for key, value in report["n8n返回OpenClaw字段"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 七、实际动作", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "OpenClaw股票消息桥接禁用态契约.json"
    rule = load_json(rule_path)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "定位": rule.get("定位", {}),
        "禁止事项": rule.get("禁止事项", []),
        "入站消息字段": rule.get("入站消息字段", {}),
        "OpenClaw转发到n8n字段": rule.get("OpenClaw转发到n8n字段", {}),
        "n8n返回OpenClaw字段": rule.get("n8n返回OpenClaw字段", {}),
        "禁用态验收标准": rule.get("禁用态验收标准", []),
        "实际动作": {
            "调用OpenClaw": False,
            "触发n8n": False,
            "启用Webhook": False,
            "企业微信真实发送": False,
            "写正式库": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启服务": False
        },
        "当前结论": "OpenClaw桥接契约已固化为禁用态；后续真实接入必须先经过人工确认、未激活导入和小流量灰度。",
    }
    output_dir = root / "03数据" / "33OpenClaw桥接契约"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"OpenClaw股票消息桥接禁用态契约_{stamp}.json"
    latest_json = output_dir / "OpenClaw股票消息桥接禁用态契约_最新.json"
    output_md = output_dir / f"OpenClaw股票消息桥接禁用态契约_{stamp}.md"
    latest_md = output_dir / "OpenClaw股票消息桥接禁用态契约_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"输出": str(output_json), "契约": str(output_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
