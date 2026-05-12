# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
REWRITE_DIR = DATA_DIR / "复核回执状态回写预演"
RECEIPT_JSON = DATA_DIR / "税收企业微信人工复核回执空白模板批量预演_最新.json"
READING_PACKET_JSON = DATA_DIR / "税收企业微信人工复核阅读包批量预演_最新.json"
DRAFT_SKELETON_JSON = DATA_DIR / "税收企业微信待复核草案骨架批量预演_最新.json"
OUT_REWRITE_JSON = REWRITE_DIR / "税收企业微信复核回执到草案状态回写预演.json"
OUT_JSON = DATA_DIR / "税收企业微信复核回执到草案状态回写预演_最新.json"
OUT_MD = DATA_DIR / "税收企业微信复核回执到草案状态回写预演_最新.md"


BOUNDARIES = {
    "是否接收真实企业微信回调": False,
    "是否联网": False,
    "是否读取凭据": False,
    "是否企业微信真实发送": False,
    "是否修改公共企业微信接入配置": False,
    "是否修改19310": False,
    "是否触发n8n": False,
    "是否写正式业务库": False,
    "是否写草案源文件": False,
    "是否调用模型推理": False,
    "是否接电子税务局": False,
    "是否接财税软件": False,
    "是否生成正式税务结论": False,
    "是否覆盖历史资料": False,
    "是否删除历史审计记录": False,
}


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def find_draft_state(draft_source: dict[str, Any], draft_id: str) -> str:
    for key in ("草案骨架", "草案骨架预演", "待复核草案骨架"):
        rows = draft_source.get(key)
        if isinstance(rows, list):
            for item in rows:
                if str(item.get("草案ID", item.get("来源草案ID", ""))) == draft_id:
                    return str(item.get("草案状态", item.get("状态", "unknown")))
    return "unknown"


def all_fill_blank(fill_zone: dict[str, Any]) -> bool:
    return bool(fill_zone) and all(value == "待人工填写" for value in fill_zone.values())


def build_transition(receipt: dict[str, Any], packet_map: dict[str, dict[str, Any]], draft_source: dict[str, Any]) -> dict[str, Any]:
    fill_zone = receipt.get("人工填写区", {})
    source_draft_id = str(receipt.get("来源草案ID", ""))
    packet = packet_map.get(str(receipt.get("阅读包ID", "")), {})
    blank = all_fill_blank(fill_zone)
    current_packet_state = str(packet.get("复核状态", receipt.get("承接复核状态", "unknown")))
    current_draft_state = find_draft_state(draft_source, source_draft_id)
    return {
        "回写预演ID": str(receipt.get("回执ID", "")).replace("receipt-blank", "status-rewrite"),
        "回执ID": receipt.get("回执ID", ""),
        "阅读包ID": receipt.get("阅读包ID", ""),
        "摘要ID": receipt.get("摘要ID", ""),
        "来源草案ID": source_draft_id,
        "消息ID": receipt.get("消息ID", ""),
        "业务事项": receipt.get("业务事项", ""),
        "回执状态": receipt.get("回执状态", ""),
        "当前阅读包状态": current_packet_state,
        "当前草案状态": current_draft_state,
        "目标阅读包状态": current_packet_state,
        "目标草案状态": current_draft_state,
        "是否具备回写条件": False,
        "阻断原因": "人工复核回执仍为空白待填写，不能自动改变阅读包、摘要或草案状态。",
        "需要人工填写字段": [key for key, value in fill_zone.items() if value == "待人工填写"],
        "回写动作": "no_op_shadow_preview",
        "回写限制": [
            "空白回执不得触发状态变化。",
            "状态回写只做本地预演，不写草案源文件或正式业务库。",
            "后续即使人工填写，也只能进入待复核链路，不自动生成正式税务结论。",
        ],
        "是否回写草案源文件": False,
        "是否写正式业务库": False,
        "是否调用模型推理": False,
        "是否企业微信真实发送": False,
        "是否生成正式税务结论": False,
        "是否形成正式复核结论": False,
        "是否自动升级为human_reviewed": False,
        "是否空白回执": blank,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 税收企业微信复核回执到草案状态回写预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 资产身份：{report['资产身份']}",
        f"- 回写预演数量：{report['回写预演数量']}",
        f"- 可回写数量：{report['可回写数量']}",
        f"- 阻断数量：{report['阻断数量']}",
        "- 说明：这是本地 no-op 状态回写预演，不写草案源文件，不写正式库，不生成正式税务结论。",
        "",
        "## 回写预演清单",
    ]
    for item in report["回写预演"]:
        lines.extend([
            f"### {item['回写预演ID']}",
            f"- 回执ID：{item['回执ID']}",
            f"- 阅读包ID：{item['阅读包ID']}",
            f"- 来源草案ID：{item['来源草案ID']}",
            f"- 业务事项：{item['业务事项']}",
            f"- 是否具备回写条件：{item['是否具备回写条件']}",
            f"- 回写动作：{item['回写动作']}",
            f"- 阻断原因：{item['阻断原因']}",
            "",
        ])
    lines.extend(["## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    REWRITE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    receipt_source = load(RECEIPT_JSON)
    packet_source = load(READING_PACKET_JSON)
    draft_source = load(DRAFT_SKELETON_JSON)
    receipts = as_list(receipt_source.get("回执模板"))
    packets = as_list(packet_source.get("阅读包"))
    packet_map = {str(item.get("阅读包ID", "")): item for item in packets}
    transitions = [build_transition(item, packet_map, draft_source) for item in receipts]
    writable = [item for item in transitions if item["是否具备回写条件"] is True]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信复核回执到草案状态回写预演",
        "生成时间": now,
        "资产身份": "dry-run复核回执到草案状态回写预演，不是真实状态回写，不写正式业务库，不是正式复核结果，不是税务结论。",
        "回执来源": str(RECEIPT_JSON),
        "阅读包来源": str(READING_PACKET_JSON),
        "草案骨架来源": str(DRAFT_SKELETON_JSON),
        "回写预演保存路径": str(OUT_REWRITE_JSON),
        "运行状态": "shadow_dry_run_no_op_status_rewrite",
        "回写预演数量": len(transitions),
        "可回写数量": len(writable),
        "阻断数量": len(transitions) - len(writable),
        "回写预演": transitions,
        "安全边界": BOUNDARIES,
    }
    OUT_REWRITE_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({"状态": "通过", "回写预演数量": len(transitions), "可回写数量": len(writable), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
