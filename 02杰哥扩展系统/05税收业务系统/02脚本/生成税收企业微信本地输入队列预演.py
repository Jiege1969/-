# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信本地输入队列预演.py
作用：根据本地输入队列规则，预演“杰哥工作秘书”消息入队、拒收和审计记录。
安全边界：只生成本地队列预演；不接收真实回调、不联网、不读取凭据、不写正式业务库。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收企业微信本地输入队列规则.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
QUEUE_DIR = OUT_DIR / "输入队列"
OUT_JSON = OUT_DIR / "税收企业微信本地输入队列预演_最新.json"
OUT_MD = OUT_DIR / "税收企业微信本地输入队列预演_最新.md"


SAMPLE_MESSAGES = [
    {
        "消息ID": "wecom-input-001",
        "机器人名称": "杰哥工作秘书",
        "提问人标识": "internal_user_masked",
        "消息类型": "text",
        "文本": "我们公司2025年研发费用加计扣除需要准备哪些资料？有立项书和辅助账。",
        "附件元数据": []
    },
    {
        "消息ID": "wecom-input-002",
        "机器人名称": "杰哥工作秘书",
        "提问人标识": "internal_user_masked",
        "消息类型": "text",
        "文本": "请直接登录电子税务局帮我申报并退税。",
        "附件元数据": []
    },
    {
        "消息ID": "wecom-input-003",
        "机器人名称": "其他机器人",
        "提问人标识": "internal_user_masked",
        "消息类型": "text",
        "文本": "研发费用加计扣除能不能享受？",
        "附件元数据": []
    },
    {
        "消息ID": "wecom-input-004",
        "机器人名称": "杰哥工作秘书",
        "提问人标识": "internal_user_masked",
        "消息类型": "mixed",
        "文本": "补充资料：项目立项书、费用辅助账，手机号13812345678请脱敏。",
        "附件元数据": [
            {"附件名称": "项目立项书.docx", "附件类型": "docx", "附件是否已入库": False},
            {"附件名称": "费用辅助账.xlsx", "附件类型": "xlsx", "附件是否已入库": False}
        ]
    },
    {
        "消息ID": "wecom-input-005",
        "机器人名称": "杰哥工作秘书",
        "提问人标识": "internal_user_masked",
        "消息类型": "text",
        "文本": "软件产品即征即退需要哪些增值税依据？",
        "附件元数据": []
    },
    {
        "消息ID": "wecom-input-006",
        "机器人名称": "杰哥工作秘书",
        "提问人标识": "internal_user_masked",
        "消息类型": "text",
        "文本": "增值税法依据现在是什么？请列依据层级、有效状态、待复核说明。",
        "附件元数据": []
    }
]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def mask_sensitive(text: str) -> str:
    patterns = [
        r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[A-Za-z0-9_-]+",
        r"(?<!\d)1[3-9]\d{9}(?!\d)",
        r"(?<![0-9A-Za-z])\d{17}[\dXx](?![0-9A-Za-z])",
        r"(?<!\d)\d{12,19}(?!\d)",
        r"(?<![0-9A-Z])[0-9A-Z]{15,20}(?![0-9A-Z])",
    ]
    masked = text
    for pattern in patterns:
        masked = re.sub(pattern, "[已脱敏]", masked)
    return masked


def classify(message: dict[str, Any], rule: dict[str, Any], now: str, index: int) -> dict[str, Any]:
    text = message.get("文本", "")
    masked = mask_sensitive(text)
    rejected_reason = ""
    if message.get("机器人名称") != rule.get("机器人终端"):
        rejected_reason = "来源机器人不是杰哥工作秘书。"
    else:
        for reject_rule in rule.get("拒收规则", []):
            keywords = reject_rule.get("条件关键词", [])
            if keywords and any(keyword in text for keyword in keywords):
                rejected_reason = reject_rule.get("拒收原因", reject_rule.get("规则", "拒收"))
                break
    if rejected_reason:
        status = "rejected"
        contract_status = "rejected"
        route = "高风险请求"
    elif message.get("附件元数据"):
        status = "queued"
        contract_status = "normalized"
        route = "资料补充"
    else:
        status = "queued"
        contract_status = "pending_evidence_match"
        route = "涉税问题"
    return {
        "入队ID": f"tax-wecom-local-queue-{index:03d}",
        "消息ID": message.get("消息ID"),
        "入队时间": now,
        "机器人名称": message.get("机器人名称"),
        "提问人标识": message.get("提问人标识"),
        "消息类型": message.get("消息类型"),
        "脱敏文本": masked,
        "附件元数据": message.get("附件元数据", []),
        "分流结果": route,
        "处理状态": status,
        "拒收原因": rejected_reason,
        "输入契约状态": contract_status,
        "审计编号": f"tax-wecom-input-audit-{index:03d}",
        "来源通道": "企业微信/杰哥工作秘书" if message.get("机器人名称") == "杰哥工作秘书" else "企业微信/其他来源"
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = [classify(message, rule, now, index + 1) for index, message in enumerate(SAMPLE_MESSAGES)]
    accepted = [item for item in records if item["处理状态"] != "rejected"]
    rejected = [item for item in records if item["处理状态"] == "rejected"]
    queue_file = QUEUE_DIR / "税收企业微信本地输入队列_预演.json"
    queue_file.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "名称": "税收企业微信本地输入队列预演",
        "生成时间": now,
        "规则来源": str(RULE),
        "队列文件": str(queue_file),
        "队列状态": rule.get("队列状态", "dry_run"),
        "记录数量": len(records),
        "入队数量": len(accepted),
        "拒收数量": len(rejected),
        "队列记录": records,
        "安全边界": rule.get("安全边界", {})
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信本地输入队列预演",
        "",
        f"- 生成时间：{now}",
        f"- 队列状态：{report['队列状态']}",
        f"- 记录数量：{report['记录数量']}",
        f"- 入队数量：{report['入队数量']}",
        f"- 拒收数量：{report['拒收数量']}",
        "",
        "## 队列记录",
        "",
    ]
    for item in records:
        lines.append(f"- {item['消息ID']}：处理状态={item['处理状态']}，输入契约状态={item['输入契约状态']}，分流={item['分流结果']}，拒收原因={item['拒收原因'] or '无'}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "记录数量": len(records), "入队数量": len(accepted), "拒收数量": len(rejected), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
