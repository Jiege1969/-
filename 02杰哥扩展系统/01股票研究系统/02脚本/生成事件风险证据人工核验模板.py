# -*- coding: utf-8 -*-
"""
名称：生成事件风险证据人工核验模板.py
作用：基于事件风险证据补全底稿，生成可人工填写的核验模板。
安全边界：只读本地底稿；只写 03数据/175事件风险证据人工核验模板；不写正式库、不抓正文、不触发 n8n、不发送企业微信、不调用券商接口、不自动交易。
"""

from __future__ import annotations

import json
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


def build_template_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "代码": item.get("代码"),
        "名称": item.get("名称"),
        "行业": item.get("行业"),
        "优先级": item.get("优先级"),
        "可信度": item.get("可信度"),
        "证据缺口": item.get("证据缺口", []),
        "建议核验入口": item.get("建议核验入口", []),
        "待核验问题": item.get("待核验问题", []),
        "人工填写": {
            "核验状态": "待核验",
            "材料标题": "",
            "材料发布日期": "",
            "材料来源名称": "",
            "材料来源URL": "",
            "事件类型": "",
            "风险等级": "",
            "是否发现新增重大风险": "",
            "是否支持当前前台结论": "",
            "建议前台处理": "",
            "核验摘要": "",
        },
        "核验人": "",
        "核验日期": "",
        "备注": "",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 事件与风险证据人工核验模板 - {report['生成时间']}",
        "",
        "## 一、填写规则",
        "",
        "1. 只在人工打开官方或可信入口后填写，不允许把未核验线索写成事实。",
        "2. `核验状态` 只有写成 `已核验`，并补齐材料标题、日期、来源、核验摘要、核验人、核验日期后，才进入预览层。",
        "3. `建议前台处理` 只允许写：维持结论、增加风险提示、降低关注、暂缓推荐、阻断推荐。",
        "4. 本模板不会写入公司品质档案、推送草案或正式库。",
        "",
        "## 二、待核验股票",
        "",
        "| 优先级 | 代码 | 名称 | 行业 | 证据缺口 | 核验状态 |",
        "|---:|---|---|---|---|---|",
    ]
    for item in report["核验模板"]:
        gaps = "、".join(item.get("证据缺口", []))
        lines.append(f"| {item.get('优先级')} | {item.get('代码')} | {item.get('名称')} | {item.get('行业')} | {gaps} | {item['人工填写']['核验状态']} |")
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 只生成模板，不自动判断风险。",
        "- 不写正式库，不改推荐，不发企业微信。",
        "- 不触发 n8n，不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    source_path = root / "03数据" / "174事件风险证据补全底稿" / "事件风险证据补全底稿_最新.json"
    source = load_json(source_path, {})
    stocks = source.get("股票", []) if isinstance(source, dict) else []
    template = [build_template_item(item) for item in stocks]

    report = {
        "名称": "事件与风险证据人工核验模板",
        "版本": "2026-05-02",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成事件风险证据人工核验模板.py",
        "输入底稿": str(source_path),
        "股票数量": len(template),
        "核验模板": template,
        "安全边界": {
            "是否写正式库": False,
            "是否修改推荐": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "175事件风险证据人工核验模板"
    latest_json = output_dir / "事件风险证据人工核验模板_最新.json"
    latest_md = output_dir / "事件风险证据人工核验模板_最新.md"
    markdown = build_markdown(report)
    write_json(output_dir / f"事件风险证据人工核验模板_{stamp}.json", report)
    write_json(latest_json, report)
    write_text(output_dir / f"事件风险证据人工核验模板_{stamp}.md", markdown)
    write_text(latest_md, markdown)

    print(json.dumps({"状态": "完成", "股票数量": len(template), "模板": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
