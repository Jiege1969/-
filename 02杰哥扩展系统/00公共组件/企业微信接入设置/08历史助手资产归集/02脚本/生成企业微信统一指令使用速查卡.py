# -*- coding: utf-8 -*-
"""
名称：生成企业微信统一指令使用速查卡.py
作用：根据企业微信统一指令路由规则和本地调用预演结果，生成用户可读的企业微信指令速查卡。
触发方式：python 生成企业微信统一指令使用速查卡.py
依赖：Python标准库；生成企业微信统一指令本地调用预演.py；企业微信统一指令路由预演规则.json；wecom-unified-command-local-call-preview-最新.json。
所属系统：02杰哥扩展系统/06企业微信助手系统
安全边界：只读取本系统配置和预演结果，只写入本系统03数据与07文档；不真实发送企业微信；不触发Webhook；不触发n8n；不写旧系统；不接入税收真实业务；不接入交易。
创建/修改记录：2026-04-29 创建企业微信统一指令使用速查卡生成脚本；2026-04-29 生成前刷新统一指令本地调用预演，避免速查卡读取旧状态。
标识：wecom-unified-command-quick-card-generate
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


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def first_preview_for_route(local_preview: dict[str, Any], route_name: str) -> str:
    for item in local_preview.get("调用结果", []):
        if item.get("路由") == route_name:
            preview = str(item.get("回复预演", "")).strip()
            return preview[:260] + "..." if len(preview) > 260 else preview
    return ""


def build_card(route_config: dict[str, Any], local_preview: dict[str, Any]) -> dict[str, Any]:
    route_rules = sorted(route_config.get("路由规则", []), key=lambda item: int(item.get("优先级", 100)))
    items: list[dict[str, Any]] = []
    for rule in route_rules:
        route_name = str(rule.get("路由", ""))
        keywords = [str(item) for item in rule.get("关键词", [])]
        example = keywords[0] if keywords else route_name
        if route_name == "股票研究":
            example = "新易盛"
        elif route_name == "系统状态":
            example = "系统现在进度多少"
        elif route_name == "知识库问答":
            example = "帮我查一下这个资料依据"
        elif route_name == "内容办公处理":
            example = "帮我整理一份工作汇报提纲"
        elif route_name == "视频制作":
            example = "把这段素材做成视频脚本"
        elif route_name == "税收业务暂停":
            example = "增值税政策怎么处理"
        items.append(
            {
                "路由": route_name,
                "目标系统": rule.get("目标系统", ""),
                "能力状态": rule.get("能力状态", ""),
                "推荐说法": example,
                "关键词": keywords[:8],
                "当前返回预演": first_preview_for_route(local_preview, route_name),
                "真实动作": False,
            }
        )
    fallback = route_config.get("兜底路由", {})
    items.append(
        {
            "路由": fallback.get("路由", "澄清一次"),
            "目标系统": fallback.get("目标系统", "06企业微信助手系统"),
            "能力状态": fallback.get("能力状态", "可用"),
            "推荐说法": "这个事情你怎么看",
            "关键词": ["无法确定意图时追问一次"],
            "当前返回预演": first_preview_for_route(local_preview, str(fallback.get("路由", "澄清一次"))),
            "真实动作": False,
        }
    )
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-unified-command-quick-card",
        "所属系统": "02杰哥扩展系统/06企业微信助手系统",
        "总体状态": "healthy" if items else "degraded",
        "指令数量": len(items),
        "指令": items,
        "使用原则": [
            "股票可以直接发股票名或代码，系统只做研究分析，不做交易。",
            "状态类问题直接问进度、健康、自检、总览。",
            "知识库、内容办公、视频制作当前处于本地预演和草稿阶段。",
            "税收业务按当前约定暂停真实搭建和真实接入。",
            "系统无法判断意图时只追问一次，确认后再进入学习归档。",
        ],
        "安全边界": {
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "写旧系统": False,
            "写正式库": False,
            "接入税收真实业务": False,
            "交易接口": False,
        },
    }


def build_markdown(card: dict[str, Any]) -> str:
    lines = [
        "# 企业微信统一指令使用速查卡",
        "",
        f"- 生成时间：{card['生成时间']}",
        f"- 总体状态：{card['总体状态']}",
        f"- 指令数量：{card['指令数量']}",
        "",
        "## 常用说法",
        "",
        "| 能力 | 推荐说法 | 当前状态 | 说明 |",
        "| --- | --- | --- | --- |",
    ]
    for item in card.get("指令", []):
        preview = str(item.get("当前返回预演", "")).replace("\r", " ").replace("\n", " / ")
        preview = preview[:120] + "..." if len(preview) > 120 else preview
        lines.append(f"| {item.get('路由')} | `{item.get('推荐说法')}` | {item.get('能力状态')} | {preview} |")
    lines.extend(["", "## 使用原则", ""])
    lines.extend(f"- {item}" for item in card.get("使用原则", []))
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 这张速查卡只说明当前可用的指令和边界。",
            "- 不真实发送企业微信，不触发Webhook，不触发n8n。",
            "- 不写旧系统，不写正式库，不接入交易接口。",
        ]
    )
    return "\n".join(lines) + "\n"


def refresh_local_preview(root: Path) -> dict[str, Any]:
    """刷新统一指令本地调用预演；该脚本只做低风险本地预演。"""
    generator = root / "02脚本" / "生成企业微信统一指令本地调用预演.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    return {
        "脚本": str(generator),
        "退出码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
    }


def main() -> int:
    root = module_root()
    refresh_result = refresh_local_preview(root)
    route_config = load_json(root / "01配置" / "企业微信统一指令路由预演规则.json", {})
    local_preview = load_json(root / "03数据" / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json", {})
    card = build_card(route_config, local_preview)
    card["本地调用预演刷新"] = refresh_result
    if refresh_result.get("退出码") != 0:
        card["总体状态"] = "degraded"
    output_dir = root / "03数据" / "11统一指令使用速查卡"
    latest_json = output_dir / "wecom-unified-command-quick-card-最新.json"
    output_json = latest_json
    latest_md = output_dir / "企业微信统一指令使用速查卡_最新.md"
    output_md = latest_md
    doc_md = root / "07文档" / "企业微信统一指令使用速查卡.md"
    markdown = build_markdown(card)
    write_json(output_json, card)
    write_json(latest_json, card)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_text(doc_md, markdown)
    print(json.dumps({"状态": card["总体状态"], "指令数量": card["指令数量"], "输出": str(output_json), "文档": str(doc_md)}, ensure_ascii=False))
    return 0 if card["总体状态"] == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
