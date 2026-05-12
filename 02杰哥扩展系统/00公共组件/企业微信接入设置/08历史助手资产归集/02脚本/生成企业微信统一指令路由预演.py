# -*- coding: utf-8 -*-
"""
名称：生成企业微信统一指令路由预演.py
作用：根据企业微信统一指令路由预演规则，对样例消息进行只读路由判断，形成统一入口分流预演报告。
触发方式：python 生成企业微信统一指令路由预演.py
依赖：Python标准库；企业微信统一指令路由预演规则.json。
所属系统：02杰哥扩展系统/06企业微信助手系统
安全边界：只读取本系统配置并写入本系统03数据；不真实发送企业微信；不触发Webhook；不触发n8n；不写正式库；不写旧系统；不接入税收真实业务；不接入交易。
创建/修改记录：2026-04-29 创建企业微信统一指令路由预演脚本。
标识：wecom-unified-command-router-preview-generate
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


def route_message(message: str, config: dict[str, Any]) -> dict[str, Any]:
    normalized = message.strip().lower()
    rules = sorted(config.get("路由规则", []), key=lambda item: int(item.get("优先级", 100)))
    for rule in rules:
        keywords = [str(item).lower() for item in rule.get("关键词", [])]
        if any(keyword and keyword in normalized for keyword in keywords):
            return {
                "输入": message,
                "命中路由": rule.get("路由"),
                "目标系统": rule.get("目标系统"),
                "能力状态": rule.get("能力状态"),
                "执行方式": rule.get("执行方式"),
                "真实动作": bool(rule.get("真实动作")),
            }
    fallback = config.get("兜底路由", {})
    return {
        "输入": message,
        "命中路由": fallback.get("路由", "澄清一次"),
        "目标系统": fallback.get("目标系统", "06企业微信助手系统"),
        "能力状态": fallback.get("能力状态", "可用"),
        "执行方式": fallback.get("执行方式", "无法确定意图时只追问一次。"),
        "真实动作": bool(fallback.get("真实动作")),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 企业微信统一指令路由预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['汇总']['状态']}",
        f"- 样例数量：{report['汇总']['样例数量']}",
        f"- 命中期望数量：{report['汇总']['命中期望数量']}",
        f"- 真实动作数量：{report['汇总']['真实动作数量']}",
        "",
        "## 路由样例",
        "",
        "| 输入 | 命中路由 | 目标系统 | 能力状态 |",
        "| --- | --- | --- | --- |",
    ]
    for item in report.get("样例结果", []):
        lines.append(f"| {item['输入']} | {item['命中路由']} | {item['目标系统']} | {item['能力状态']} |")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 当前仅做路由预演，不真实发送企业微信。",
        "- 不触发Webhook、不触发n8n、不写正式库、不写旧系统。",
        "- 税收业务命中后返回暂停说明，不进入真实业务搭建。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    config_path = root / "01配置" / "企业微信统一指令路由预演规则.json"
    config = load_json(config_path)
    samples = config.get("预演样例", [])
    results: list[dict[str, Any]] = []
    for sample in samples:
        routed = route_message(str(sample.get("输入", "")), config)
        routed["期望路由"] = sample.get("期望路由")
        routed["是否命中期望"] = routed["命中路由"] == sample.get("期望路由")
        results.append(routed)

    real_actions = [item for item in results if item.get("真实动作") is True]
    matched = [item for item in results if item.get("是否命中期望") is True]
    safety = config.get("安全边界", {})
    safety_ok = all(value is False for value in safety.values())
    status = "healthy" if len(matched) == len(results) and not real_actions and safety_ok else "degraded"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-unified-command-router-preview",
        "所属系统": "02杰哥扩展系统/06企业微信助手系统",
        "配置": str(config_path),
        "汇总": {
            "状态": status,
            "样例数量": len(results),
            "命中期望数量": len(matched),
            "真实动作数量": len(real_actions),
            "模式": config.get("默认模式", "preview_only"),
        },
        "样例结果": results,
        "安全边界": safety,
    }
    output_dir = root / "03数据" / "08统一指令路由预演"
    latest_json = output_dir / "wecom-unified-command-router-preview-最新.json"
    output_json = latest_json
    latest_md = output_dir / "企业微信统一指令路由预演_最新.md"
    output_md = latest_md
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"状态": status, "样例数量": len(results), "命中期望数量": len(matched), "输出": str(output_json)}, ensure_ascii=False))
    return 0 if status == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
