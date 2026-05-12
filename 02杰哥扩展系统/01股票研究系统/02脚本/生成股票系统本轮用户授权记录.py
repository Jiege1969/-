# -*- coding: utf-8 -*-
"""
名称：生成股票系统本轮用户授权记录.py
作用：把本轮用户“全权完成工作、纠正过时闸口”的授权写成本地可审计记录。
安全边界：只写股票系统本地授权记录；不发送企业微信、不触发 n8n、不调用券商接口、不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "239股票系统本轮用户授权"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "股票系统本轮用户授权记录",
        "生成时间": now,
        "授权来源": "用户在当前施工线程明确表示：继续，不停下来等我确认，授权你全权完成工作；闸口规定过时就要根据工作需要纠正，不要成为搭建工作的拦路虎。",
        "授权结论": "允许纠正过时等待确认闸口，并推进股票系统受控单人真实灰度闭环。",
        "允许事项": {
            "纠正过时人工确认闸口": True,
            "允许单人白名单企业微信真实灰度": True,
            "允许最多一条股票短回复真实灰度消息": True,
            "允许使用公共受控发送器": True,
            "允许生成发送日志和验收包": True
        },
        "仍保持关闭": {
            "群发": True,
            "外部客户发送": True,
            "n8n导入或启用": True,
            "调用券商接口": True,
            "自动交易": True,
            "下单": True,
            "写正式库": True,
            "重启正式服务": True
        },
        "灰度边界": {
            "接收人": "本人白名单",
            "消息数量": 1,
            "消息来源": "24企业微信短回复 v21_template_dry_run 正式成交额口径草稿",
            "发送器": "00公共组件/02脚本/企业微信受控发送器.py"
        }
    }
    write_json(OUT_DIR / "股票系统本轮用户授权记录_最新.json", report)
    lines = [
        "# 股票系统本轮用户授权记录",
        "",
        f"- 生成时间：{now}",
        f"- 授权结论：{report['授权结论']}",
        "",
        "## 允许事项",
        ""
    ]
    for key, value in report["允许事项"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 仍保持关闭", ""])
    for key, value in report["仍保持关闭"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    write_text(OUT_DIR / "股票系统本轮用户授权记录_最新.md", "\n".join(lines))
    print(json.dumps({"状态": "完成", "输出": str(OUT_DIR / "股票系统本轮用户授权记录_最新.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
