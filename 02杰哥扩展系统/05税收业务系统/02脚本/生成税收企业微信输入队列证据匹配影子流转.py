# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信输入队列证据匹配影子流转.py
作用：把企业微信本地输入队列预演结果转换为政策证据匹配影子任务。
安全边界：只读本地预演和配置；不接收真实回调、不联网、不读取凭据、不写正式业务库、不生成正式税务结论。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收企业微信输入队列证据匹配影子流转规则.json"
QUEUE_PREVIEW = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信本地输入队列预演_最新.json"
EVIDENCE_PREVIEW = ROOT / "03数据" / "28政策证据底座字段补齐预演" / "税收政策证据底座字段补齐预演_最新.json"
CONTRACT = ROOT / "01配置" / "涉税业务分析契约.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
SHADOW_DIR = OUT_DIR / "证据匹配影子流转"
OUT_JSON = OUT_DIR / "税收企业微信输入队列证据匹配影子流转_最新.json"
OUT_MD = OUT_DIR / "税收企业微信输入队列证据匹配影子流转_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def has_unmasked_sensitive(text: str) -> bool:
    patterns = [
        r"(?<!\d)1[3-9]\d{9}(?!\d)",
        r"(?<![0-9A-Za-z])\d{17}[\dXx](?![0-9A-Za-z])",
        r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def match_topic(text: str, rule: dict[str, Any]) -> dict[str, Any]:
    matched: list[tuple[int, int, dict[str, Any]]] = []
    for item in as_list(rule.get("主题识别规则")):
        keywords = [word for word in as_list(item.get("关键词")) if word]
        if keywords and any(word in text for word in keywords):
            hits = [word for word in keywords if word in text]
            matched.append((len(hits), max(len(word) for word in hits), item))
    if matched:
        item = sorted(matched, key=lambda row: (row[0], row[1]), reverse=True)[0][2]
        return {
            "业务事项猜测": item.get("主题", "涉税业务分析"),
            "适用税种猜测": as_list(item.get("适用税种猜测")) or ["待识别"],
            "候选证据主题": as_list(item.get("候选证据主题")) or ["待政策证据底座匹配"],
            "依据层级明细": as_list(item.get("依据层级明细")),
            "待复核资料清单": as_list(item.get("待复核资料清单")),
            "待复核说明": item.get("待复核说明", ""),
            "待补充事实": as_list(item.get("待补充事实")) or as_list(rule.get("默认流转", {}).get("待补充事实")),
        }
    default = rule.get("默认流转", {})
    return {
        "业务事项猜测": default.get("业务事项猜测", "涉税业务分析"),
        "适用税种猜测": as_list(default.get("适用税种猜测")) or ["待识别"],
        "候选证据主题": as_list(default.get("候选证据主题")) or ["待政策证据底座匹配"],
        "依据层级明细": as_list(default.get("依据层级明细")),
        "待复核资料清单": as_list(default.get("待复核资料清单")),
        "待复核说明": default.get("待复核说明", ""),
        "待补充事实": as_list(default.get("待补充事实")),
    }


def build_shadow_task(record: dict[str, Any], rule: dict[str, Any], now: str, index: int) -> dict[str, Any]:
    text = record.get("脱敏文本", "")
    topic = match_topic(text, rule)
    status = "blocked_sensitive_unmasked" if has_unmasked_sensitive(text) else "pending_policy_evidence_match"
    if record.get("原输入契约状态") == "normalized" or record.get("输入契约状态") == "normalized":
        status = "pending_fact_completion" if status != "blocked_sensitive_unmasked" else status
    review_items = [
        "核验政策依据层级和有效状态",
        "核验业务事实是否足以进入分析契约",
        "核验地方口径是否仅作为辅助或待复核线索",
    ]
    if status == "blocked_sensitive_unmasked":
        review_items.insert(0, "存在疑似未脱敏敏感信息，禁止继续流转")
    return {
        "流转ID": f"tax-wecom-evidence-shadow-{index:03d}",
        "入队ID": record.get("入队ID"),
        "消息ID": record.get("消息ID"),
        "来源机器人": record.get("机器人名称"),
        "脱敏文本": text,
        "原队列状态": record.get("处理状态"),
        "原输入契约状态": record.get("输入契约状态"),
        "影子流转状态": status,
        "业务事项猜测": topic["业务事项猜测"],
        "适用税种猜测": topic["适用税种猜测"],
        "候选证据主题": topic["候选证据主题"],
        "依据层级要求": rule.get("依据层级要求", []),
        "依据层级明细": topic["依据层级明细"],
        "待复核资料清单": topic["待复核资料清单"],
        "待复核说明": topic["待复核说明"],
        "待补充事实": topic["待补充事实"],
        "待人工复核项": review_items,
        "禁止动作": rule.get("禁止动作", []),
        "下一步建议": "进入政策证据底座候选匹配，形成待复核分析草案输入；不得形成正式税务结论。",
        "是否写正式业务库": False,
        "是否生成正式税务结论": False,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE)
    queue = load_json(QUEUE_PREVIEW)
    evidence = load_json(EVIDENCE_PREVIEW)
    contract = load_json(CONTRACT)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allowed_status = set(rule.get("允许输入状态", []))
    allowed_contract_status = set(rule.get("允许输入契约状态", []))
    records = as_list(queue.get("队列记录"))
    accepted: list[dict[str, Any]] = []
    rejected_trace: list[dict[str, Any]] = []
    for record in records:
        queue_status = record.get("处理状态")
        contract_status = record.get("输入契约状态")
        if queue_status in allowed_status and contract_status in allowed_contract_status:
            accepted.append(build_shadow_task(record, rule, now, len(accepted) + 1))
        else:
            rejected_trace.append({
                "消息ID": record.get("消息ID"),
                "入队ID": record.get("入队ID"),
                "原队列状态": queue_status,
                "原输入契约状态": contract_status,
                "拒绝流转原因": record.get("拒收原因") or "不属于允许进入证据匹配影子流转的输入状态",
                "是否写正式业务库": False,
                "是否生成正式税务结论": False,
            })
    shadow_file = SHADOW_DIR / "税收企业微信输入队列证据匹配影子流转_预演.json"
    shadow_file.write_text(json.dumps(accepted, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "名称": "税收企业微信输入队列证据匹配影子流转",
        "生成时间": now,
        "规则来源": str(RULE),
        "队列来源": str(QUEUE_PREVIEW),
        "影子流转文件": str(shadow_file),
        "流转状态": rule.get("流转状态"),
        "队列记录数量": len(records),
        "影子任务数量": len(accepted),
        "拒绝流转数量": len(rejected_trace),
        "影子任务": accepted,
        "拒绝流转留痕": rejected_trace,
        "证据底座状态摘要": {
            "政策证据字段预演存在": EVIDENCE_PREVIEW.exists(),
            "政策证据字段预演名称": evidence.get("名称", "未读取到"),
            "分析契约存在": CONTRACT.exists(),
            "分析契约名称": contract.get("名称", "未读取到"),
        },
        "安全边界": rule.get("安全边界", {}),
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信输入队列证据匹配影子流转",
        "",
        f"- 生成时间：{now}",
        f"- 流转状态：{report['流转状态']}",
        f"- 队列记录数量：{report['队列记录数量']}",
        f"- 影子任务数量：{report['影子任务数量']}",
        f"- 拒绝流转数量：{report['拒绝流转数量']}",
        "",
        "## 影子任务",
        "",
    ]
    for item in accepted:
        lines.append(f"- {item['流转ID']}：消息={item['消息ID']}，状态={item['影子流转状态']}，事项={item['业务事项猜测']}，税种={','.join(item['适用税种猜测'])}")
    lines.extend(["", "## 拒绝流转留痕", ""])
    for item in rejected_trace:
        lines.append(f"- {item['消息ID']}：{item['拒绝流转原因']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "影子任务数量": len(accepted), "拒绝流转数量": len(rejected_trace), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
