# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-n8n-post-refresh-webhook-gray-acceptance-plan.py
Purpose: Generate the post-refresh Webhook gray acceptance plan for stock assistant isolated n8n.
Trigger: python 生成股票助手n8n刷新后Webhook灰度验收预案.py
Dependencies: Python standard library; controlled refresh/restart request package; pre-execution snapshot package.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Generates acceptance plan only; does not restart, stop, enable, trigger Webhook, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created post-refresh Webhook gray acceptance plan generator.
Marker: stock-assistant-n8n-post-refresh-webhook-gray-acceptance-plan-generate
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
        "# 股票助手n8n刷新后Webhook灰度验收预案",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、当前结论",
        "",
        f"- 是否具备预案完整性：{report['是否具备预案完整性']}",
        f"- 是否已执行重启：{report['实际动作']['重启n8n']}",
        f"- 是否已触发Webhook：{report['实际动作']['触发Webhook']}",
        f"- 是否已发送企业微信：{report['实际动作']['发送企业微信']}",
        "",
        "## 二、前置条件",
        "",
    ]
    for item in report["前置条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、验收顺序", ""])
    for index, item in enumerate(report["验收顺序"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 四、失败止损", ""])
    for item in report["失败止损"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、禁止事项", ""])
    for item in report["禁止事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、关联材料", ""])
    for key, value in report["关联材料"].items():
        lines.append(f"- {key}：`{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票助手n8n刷新后Webhook灰度验收预案规则.json"
    request_package = root / "03数据" / "76n8n受控刷新重启申请" / "股票助手n8n受控刷新重启申请包_最新.json"
    pre_snapshot = root / "03数据" / "77n8n受控刷新重启执行前快照" / "股票助手n8n受控刷新重启执行前快照_最新.json"
    rule = load_json(rule_path)
    request = load_json(request_package)
    snapshot = load_json(pre_snapshot)
    ready = bool(rule.get("前置条件")) and request.get("是否具备申请条件") is True and snapshot.get("是否适合进入受控刷新重启申请复核") is True
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "前置条件": rule.get("前置条件", []),
        "验收顺序": rule.get("验收顺序", []),
        "失败止损": rule.get("失败止损", []),
        "禁止事项": rule.get("禁止事项", []),
        "关联材料": {
            "受控刷新重启申请包": str(request_package),
            "执行前只读快照": str(pre_snapshot),
            "Webhook灰度入口导入件": str(root / "03数据" / "74n8nWebhook灰度入口导入件"),
            "本地执行回环导入件": str(root / "03数据" / "75n8n本地执行回环导入件")
        },
        "是否具备预案完整性": ready,
        "实际动作": {
            "生成预案": True,
            "重启n8n": False,
            "停止容器": False,
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
    output_dir = root / "03数据" / "78n8n刷新后Webhook灰度验收预案"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手n8n刷新后Webhook灰度验收预案_{stamp}.json"
    latest_json = output_dir / "股票助手n8n刷新后Webhook灰度验收预案_最新.json"
    output_md = output_dir / f"股票助手n8n刷新后Webhook灰度验收预案_{stamp}.md"
    latest_md = output_dir / "股票助手n8n刷新后Webhook灰度验收预案_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备预案完整性": ready, "输出": str(output_json)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
