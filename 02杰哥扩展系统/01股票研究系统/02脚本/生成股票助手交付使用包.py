# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-delivery-usage-package.py
Purpose: Generate the stock assistant delivery usage package for user-facing handoff.
Trigger: python 生成股票助手交付使用包.py
Dependencies: Python standard library; stock assistant status materials.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Generates local delivery package only; does not restart, enable, trigger Webhook, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created stock assistant delivery usage package generator.
Marker: stock-assistant-delivery-usage-package-generate
"""

from __future__ import annotations

import json
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
        "# 股票助手交付使用包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、交付结论",
        "",
        f"- 当前交付状态：{report['当前交付状态']}",
        f"- 股票研究系统进度：{report['进度口径']['股票研究系统']}",
        f"- 剩余有效工作时间：{report['进度口径']['剩余有效工作时间']}",
        "",
        "## 二、当前可用能力",
        "",
    ]
    for item in report["当前可用能力"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、交付前最后待办", ""])
    for item in report["交付前最后待办"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、用户使用入口", ""])
    for key, value in report["用户使用入口"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、安全边界", ""])
    for item in report["禁止事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、关键验收结果", ""])
    for key, value in report["关键验收结果"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    v3_root = system_root()
    rule_path = root / "01配置" / "股票助手交付使用包规则.json"
    rule = load_json(rule_path)
    progress_log = v3_root / "00杰哥系统总管" / "04日志" / "acceptance"
    latest_acceptance = sorted(progress_log.glob("v3-acceptance-*.json"))[-1] if progress_log.exists() and list(progress_log.glob("v3-acceptance-*.json")) else None
    latest_acceptance_data = load_json(latest_acceptance) if latest_acceptance else {}
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "当前交付状态": "接近交付，需完成隔离n8n受控刷新/重启后的Webhook灰度联通和企业微信白名单小范围测试",
        "进度口径": {
            "股票研究系统": "约96%-98%",
            "剩余有效工作时间": "约2-4小时",
            "整体杰哥智能化系统": "约33%-37%"
        },
        "交付目标": rule.get("交付目标", []),
        "当前可用能力": rule.get("当前可用能力", []),
        "交付前最后待办": rule.get("交付前最后待办", []),
        "禁止事项": rule.get("禁止事项", []),
        "用户使用入口": {
            "本地股票助手": "http://127.0.0.1:19300/",
            "隔离n8n": "http://127.0.0.1:28679/",
            "Webhook灰度路径": "/webhook/jiege-stock-wework-gray",
            "旧系统保护": "D:\\杰哥智能体操作系统 保持可用，不写入不删除"
        },
        "关键验收结果": {
            "最新v3总体验收": f"{latest_acceptance_data.get('summary', {}).get('passed', '未知')}/{latest_acceptance_data.get('summary', {}).get('total', '未知')}",
            "脚本规范": "以最新规范检查结果为准",
            "交易接口": "禁用",
            "企业微信真实发送": "未放行",
            "旧系统写入": "禁止"
        },
        "实际动作": {
            "生成交付使用包": True,
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
    output_dir = root / "03数据" / "79股票助手交付使用包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手交付使用包_{stamp}.json"
    latest_json = output_dir / "股票助手交付使用包_最新.json"
    output_md = output_dir / f"股票助手交付使用包_{stamp}.md"
    latest_md = output_dir / "股票助手交付使用包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否生成交付使用包": True, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
