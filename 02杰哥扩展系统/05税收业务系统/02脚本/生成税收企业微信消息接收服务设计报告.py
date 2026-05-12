# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信消息接收服务设计报告.py
作用：生成“杰哥工作秘书”企业微信消息接收服务设计报告和本地入队样例。
安全边界：只生成本地设计报告；不启动服务、不新增端口、不接收真实回调、不读取凭据。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DESIGN = ROOT / "01配置" / "税收企业微信消息接收服务设计.json"
INPUT_CONTRACT = ROOT / "01配置" / "税收企业微信输入消息契约.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信消息接收服务设计报告_最新.json"
OUT_MD = OUT_DIR / "税收企业微信消息接收服务设计报告_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    design = load_json(DESIGN)
    input_contract = load_json(INPUT_CONTRACT)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    queue_sample = {
        "入队ID": "tax-wecom-queue-sample-001",
        "消息ID": "wecom-tax-input-sample-001",
        "接收时间": now,
        "机器人名称": "杰哥工作秘书",
        "提问人标识": "internal_user_masked",
        "消息类型": "text",
        "原始文本脱敏版": "咨询2025年研发费用加计扣除政策分析条件，已提供立项书和部分费用辅助账。",
        "附件元数据": [
            {"附件名称": "立项书", "附件类型": "docx", "附件是否已入库": False},
            {"附件名称": "费用辅助账", "附件类型": "xlsx", "附件是否已入库": False}
        ],
        "输入契约状态": "pending_evidence_match",
        "处理状态": "queued",
        "来源通道": "企业微信/杰哥工作秘书",
        "审计编号": "tax-wecom-input-audit-sample-001"
    }
    report = {
        "名称": "税收企业微信消息接收服务设计报告",
        "生成时间": now,
        "设计来源": str(DESIGN),
        "输入契约来源": str(INPUT_CONTRACT),
        "机器人终端": design.get("机器人终端", ""),
        "服务状态": design.get("服务状态", "missing"),
        "默认端口策略": design.get("默认端口策略", {}),
        "回调验签字段": design.get("回调验签字段", []),
        "消息入队字段": design.get("消息入队字段", []),
        "处理状态词": design.get("处理状态词", []),
        "拒收条件": design.get("拒收条件", []),
        "允许附件类型": design.get("允许附件类型", []),
        "审计要求": design.get("审计要求", []),
        "下游输入契约": input_contract.get("名称", ""),
        "入队样例": queue_sample,
        "当前部署状态": {
            "是否已启动服务": False,
            "是否已开放端口": False,
            "是否已配置企业微信真实回调": False,
            "是否已读取企业微信回调凭据": False
        },
        "安全边界": design.get("安全边界", {})
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信消息接收服务设计报告",
        "",
        f"- 生成时间：{now}",
        f"- 机器人终端：{report['机器人终端']}",
        f"- 服务状态：{report['服务状态']}",
        f"- 下游输入契约：{report['下游输入契约']}",
        f"- 是否已启动服务：{report['当前部署状态']['是否已启动服务']}",
        f"- 是否已开放端口：{report['当前部署状态']['是否已开放端口']}",
        f"- 是否已配置企业微信真实回调：{report['当前部署状态']['是否已配置企业微信真实回调']}",
        "",
        "## 回调验签字段",
        "",
    ]
    for field in report["回调验签字段"]:
        lines.append(f"- {field}")
    lines.extend(["", "## 消息入队字段", ""])
    for field in report["消息入队字段"]:
        lines.append(f"- {field}")
    lines.extend(["", "## 拒收条件", ""])
    for item in report["拒收条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "服务状态": report["服务状态"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
