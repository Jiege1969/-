# -*- coding: utf-8 -*-
"""
名称：生成一键接续施工包.py
作用：按当前一键接续施工包规则生成唯一最新接续入口。
安全边界：只读输入依据并写入00总管开工上下文，不触发n8n、不发送企业微信、不写正式库、不调用券商接口。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path("D:/杰哥智能化系统/00杰哥系统总管")
RULE_PATH = ROOT / "01配置" / "一键接续施工包规则.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path, limit: int = 1800) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8-sig", errors="replace").replace("\x00", "")
    return text[:limit]


def summarize_json(path: Path) -> str:
    try:
        data = load_json(path)
    except Exception as exc:
        return f"JSON读取失败: {exc}"
    summary: dict[str, Any] = {}
    for key in ("生成时间", "轮次", "主题", "范围", "结论", "删除总数", "删除数量", "数据目录删除数", "日志目录删除数", "通过", "失败"):
        if key in data:
            summary[key] = data[key]
    if "删除清单" in data:
        summary["删除清单"] = "已登记，当前接续包不展开旧路径明细"
    if "删除项" in data:
        summary["删除项"] = "已登记，当前接续包不展开旧路径明细"
    if not summary:
        summary = {"类型": "JSON状态文件", "说明": "当前接续包不展开明细"}
    return json.dumps(summary, ensure_ascii=False)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_status(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    exists = path.exists()
    suffix = path.suffix.lower()
    return {
        "路径": path_text,
        "存在": exists,
        "大小": path.stat().st_size if exists else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if exists else "",
        "摘要": summarize_json(path) if exists and suffix == ".json" else (read_text(path, 1200) if exists and suffix in {".md", ".txt"} else ""),
    }


def build_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# 一键接续施工包 最新",
        "",
        f"- 更新时间：{package['生成时间']}",
        "- 接续指令：继续摸清家底找差距；按清债防复发规则执行，证实无当前依赖的旧项直接收口。",
        f"- 权威面板：{ROOT / '07文档' / '当前施工面板.md'}",
        f"- 当前验收入口：{ROOT / '03数据' / '验收报告' / '验收报告_最新.md'}",
        "",
        "## 当前规则",
        "",
    ]
    for item in package["生成原则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 输入依据"])
    for item in package["输入依据状态"]:
        status = "存在" if item["存在"] else "缺失"
        lines.append(f"- {status}：{item['路径']}")
    lines.extend(["", "## 安全边界"])
    for key, value in package["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 下一步动作", ""])
    next_actions = package.get("下一步动作") or ["继续按当前施工面板推进。"]
    for index, item in enumerate(next_actions, start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 当前摘要", "", package.get("当前施工面板摘要", ""), ""])
    return "\n".join(lines)


def main() -> int:
    rule = load_json(RULE_PATH)
    outputs = rule["当前权威输出"]
    input_paths = rule.get("输入依据", [])
    statuses = [file_status(path) for path in input_paths]
    missing = [item for item in statuses if not item["存在"]]

    panel = ROOT / "07文档" / "当前施工面板.md"
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(RULE_PATH),
        "当前权威输出": outputs,
        "输入依据状态": statuses,
        "缺失文件数量": len(missing),
        "生成原则": rule.get("生成原则", []),
        "下一步动作": rule.get("下一步动作", []),
        "安全边界": rule.get("安全边界", {}),
        "验收标准": rule.get("验收标准", []),
        "当前施工面板摘要": read_text(panel, 2400),
        "实际动作": {
            "删除不可再生数据": False,
            "覆盖业务数据": False,
            "重启正式服务": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "下单": False,
        },
    }

    latest_json = Path(outputs["JSON"])
    latest_md = Path(outputs["Markdown"])
    latest_log = ROOT / "04日志" / "开工上下文" / "one-click-resume-package-最新.json"
    markdown = build_markdown(package)
    write_json(latest_json, package)
    write_json(latest_log, package)
    write_text(latest_md, markdown)
    print(json.dumps({"输入依据": len(statuses), "缺失": len(missing), "输出": str(latest_md)}, ensure_ascii=False))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
