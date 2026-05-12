# -*- coding: utf-8 -*-
"""
名称：生成知识库问答灰度样本清单影子模板.py
作用：生成知识库问答入口灰度样本清单影子模板，默认不填真实样本、不放行灰度。
触发方式：python 生成知识库问答灰度样本清单影子模板.py
安全边界：只读人工确认单模板并写样本清单模板；不放行灰度、不接正式入口、不调用企业微信、不触发Webhook/n8n、不启动问答、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
CONFIRM_TEMPLATE = OUT_DIR / "知识库问答入口人工确认单模板_最新.json"
REPORT_JSON = OUT_DIR / "知识库问答灰度样本清单影子模板_最新.json"
REPORT_MD = OUT_DIR / "知识库问答灰度样本清单影子模板_最新.md"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    confirm = load_json(CONFIRM_TEMPLATE)
    confirm_ok = confirm.get("结论") == "通过" and confirm.get("默认状态") == "未确认，禁止灰度"
    sample_fields = {
        "样本ID": "",
        "用户问题": "",
        "期望路由": "知识库问答",
        "证据卡ID": "",
        "来源路径": "",
        "分块序号": "",
        "内容哈希": "",
        "人工复核人": "",
        "人工复核结论": "未复核",
        "是否允许进入灰度": False,
        "是否允许企业微信显示": False,
        "是否允许真实发送": False,
        "阻断原因": "模板默认阻断，未填写真实样本",
    }
    report = {
        "名称": "知识库问答灰度样本清单影子模板",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if confirm_ok else "人工确认单模板不足",
        "来源人工确认单模板": str(CONFIRM_TEMPLATE),
        "样本上限": 3,
        "当前真实样本数量": 0,
        "模板默认状态": "空样本，禁止灰度",
        "样本字段": sample_fields,
        "样本清单": [],
        "填写规则": [
            "只能填写已经具备证据卡ID的样本。",
            "每个样本必须有来源路径、分块序号和内容哈希。",
            "人工复核结论未通过时禁止灰度。",
            "样本数量不得超过3条。",
            "是否允许真实发送必须保持 false。",
        ],
        "安全边界": {
            "填入真实样本": False,
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
        "# 知识库问答灰度样本清单影子模板",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 样本上限：{report['样本上限']}",
        f"- 当前真实样本数量：{report['当前真实样本数量']}",
        f"- 模板默认状态：{report['模板默认状态']}",
        "",
        "## 样本字段",
        "",
    ]
    for key, value in sample_fields.items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 填写规则", ""])
    for item in report["填写规则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只生成空样本影子模板，不填真实样本，不放行灰度，不接入正式入口，不调用企业微信接口，不触发 Webhook/n8n，不启动问答，不写库。")
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "当前真实样本数量": 0, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if confirm_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
