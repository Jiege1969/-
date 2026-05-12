# -*- coding: utf-8 -*-
"""
名称：生成知识库只读问答入口影子方案.py
作用：生成知识库只读问答入口的影子接入方案、字段映射、验收清单和回滚点。
触发方式：python 生成知识库只读问答入口影子方案.py
安全边界：只读证据卡样板并写方案；不接入正式入口、不启动问答、不调用模型、不入库、不触发n8n、不发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
EVIDENCE_CARD_JSON = OUT_DIR / "知识库证据卡格式标准影子样板_最新.json"
REPORT_JSON = OUT_DIR / "知识库只读问答入口影子方案_最新.json"
REPORT_MD = OUT_DIR / "知识库只读问答入口影子方案_最新.md"


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


def main() -> int:
    evidence_report = load_json(EVIDENCE_CARD_JSON, {})
    cards = evidence_report.get("证据卡样板", [])
    plan = {
        "名称": "知识库只读问答入口影子方案",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if cards else "缺少证据卡样板",
        "入口定位": "影子方案，不接正式入口",
        "依赖产物": {
            "证据卡样板": str(EVIDENCE_CARD_JSON),
            "证据卡数量": len(cards),
        },
        "入口字段映射": {
            "输入字段": {
                "用户问题": "必填；仅作为影子方案字段，不触发真实问答",
                "来源入口": "固定为 shadow_readonly_kb_qa",
                "请求ID": "由入口层生成，用于追踪",
                "人工确认": "默认 false，正式答复前必须人工确认",
            },
            "输出字段": {
                "回答草案": "可选；本方案不生成新回答",
                "证据卡列表": "引用证据卡ID、来源路径、分块序号、内容哈希",
                "安全状态": "必须返回只读、未发送、未入库",
                "下一步": "人工复核或继续影子预演",
            },
        },
        "影子流程": [
            "入口层接收用户问题后只生成请求记录。",
            "读取已有本地问答预演或证据卡样板，不启动批量问答。",
            "返回证据卡列表和只读状态，不作为正式答复发送。",
            "需要正式接入时，必须另走人工确认、灰度方案、回滚点和企业微信入口许可。",
        ],
        "验收清单": [
            "不接入正式企业微信入口。",
            "不调用模型推理。",
            "不生成向量。",
            "不写 Qdrant/PostgreSQL。",
            "输出必须携带证据卡ID、来源路径、分块序号和内容哈希。",
            "默认不可用于正式答复。",
            "回滚方式为删除影子方案产物或忽略影子入口配置，不影响现有股票入口。",
        ],
        "回滚点": [
            "不修改正式入口，因此无需服务回滚。",
            "如后续创建影子入口配置，删除影子配置即可。",
            "如后续接入企业微信，必须另建正式回滚清单。",
        ],
        "安全边界": {
            "接入正式入口": False,
            "启动问答": False,
            "调用模型推理": False,
            "生成向量": False,
            "写正式知识库": False,
            "写Qdrant": False,
            "写PostgreSQL": False,
            "触发n8n": False,
            "发送企业微信": False,
            "联网检索": False,
            "读取旧系统": False,
            "接入税收业务": False,
        },
    }
    lines = [
        "# 知识库只读问答入口影子方案",
        "",
        f"- 生成时间：{plan['生成时间']}",
        f"- 结论：{plan['结论']}",
        f"- 入口定位：{plan['入口定位']}",
        f"- 证据卡数量：{len(cards)}",
        "",
        "## 字段映射",
        "",
        "### 输入字段",
        "",
    ]
    for key, value in plan["入口字段映射"]["输入字段"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "### 输出字段", ""])
    for key, value in plan["入口字段映射"]["输出字段"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 影子流程", ""])
    for index, item in enumerate(plan["影子流程"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 验收清单", ""])
    for item in plan["验收清单"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 回滚点", ""])
    for item in plan["回滚点"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "本轮只生成入口影子方案，不接入正式入口，不启动问答，不调用模型，不生成向量，不写 Qdrant/PostgreSQL，不触发 n8n，不发送企业微信。",
    ])
    write_json(REPORT_JSON, plan)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": plan["结论"], "证据卡数量": len(cards), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if plan["结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
