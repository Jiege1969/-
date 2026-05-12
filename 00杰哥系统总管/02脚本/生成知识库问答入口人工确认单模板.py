# -*- coding: utf-8 -*-
"""
名称：生成知识库问答入口人工确认单模板.py
作用：生成知识库问答入口灰度前人工确认单模板，明确用户签核项和默认阻断状态。
触发方式：python 生成知识库问答入口人工确认单模板.py
安全边界：只读灰度门禁草案并写模板；不放行灰度、不接正式入口、不调用企业微信、不触发Webhook/n8n、不启动问答、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
GATE_JSON = OUT_DIR / "知识库问答入口灰度门禁草案_最新.json"
REPORT_JSON = OUT_DIR / "知识库问答入口人工确认单模板_最新.json"
REPORT_MD = OUT_DIR / "知识库问答入口人工确认单模板_最新.md"


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


def main() -> int:
    gate = load_json(GATE_JSON)
    gate_ok = gate.get("结论") == "通过"
    template = {
        "名称": "知识库问答入口人工确认单模板",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if gate_ok else "灰度门禁不足",
        "来源门禁草案": str(GATE_JSON),
        "默认状态": "未确认，禁止灰度",
        "确认单字段": {
            "确认单ID": "由后续填写脚本生成",
            "确认人": "",
            "确认时间": "",
            "是否允许创建影子入口配置": False,
            "是否允许新增灰度样本清单": False,
            "是否允许企业微信助手显示知识库问答预演结果": False,
            "是否保持真实发送关闭": True,
            "是否保持n8n关闭": True,
            "是否保持写库关闭": True,
            "首批灰度样本上限": 0,
            "备注": "",
        },
        "必须人工勾选项": [
            "我确认这是影子/灰度前准备，不代表正式入口接入。",
            "我确认真实发送企业微信继续关闭。",
            "我确认 n8n/Webhook 继续关闭。",
            "我确认知识库写库、Qdrant、PostgreSQL 继续关闭。",
            "我确认每条预演回答必须带证据卡并人工复核。",
        ],
        "自动阻断默认值": {
            "未填写确认人": True,
            "未确认真实发送关闭": True,
            "首批灰度样本上限大于3": True,
            "试图接入正式入口": True,
            "试图触发n8n": True,
            "试图写库": True,
        },
        "安全边界": {
            "放行灰度": False,
            "接入正式入口": False,
            "调用企业微信接口": False,
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "启动问答": False,
            "调用模型推理": False,
            "写正式知识库": False,
            "写Qdrant": False,
            "写PostgreSQL": False,
            "自动放行": False,
        },
    }
    lines = [
        "# 知识库问答入口人工确认单模板",
        "",
        f"- 生成时间：{template['生成时间']}",
        f"- 结论：{template['结论']}",
        f"- 默认状态：{template['默认状态']}",
        f"- 来源门禁草案：`{GATE_JSON}`",
        "",
        "## 确认单字段",
        "",
    ]
    for key, value in template["确认单字段"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 必须人工勾选项", ""])
    for item in template["必须人工勾选项"]:
        lines.append(f"- [ ] {item}")
    lines.extend(["", "## 自动阻断默认值", ""])
    for key, value in template["自动阻断默认值"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只生成确认单模板，不放行灰度，不接入正式入口，不调用企业微信接口，不触发 Webhook/n8n，不启动问答，不写库。")
    write_json(REPORT_JSON, template)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": template["结论"], "默认状态": template["默认状态"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if gate_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
