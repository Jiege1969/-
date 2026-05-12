# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
PACKET_DIR = DATA_DIR / "人工复核阅读包"
SUMMARY_JSON = DATA_DIR / "税收企业微信待复核分析摘要批量预演_最新.json"
COMPLIANCE_JSON = DATA_DIR / "税收企业微信待复核摘要批量消息合规审查_最新.json"
OUT_PACKET_JSON = PACKET_DIR / "税收企业微信人工复核阅读包批量预演.json"
OUT_JSON = DATA_DIR / "税收企业微信人工复核阅读包批量预演_最新.json"
OUT_MD = DATA_DIR / "税收企业微信人工复核阅读包批量预演_最新.md"


BOUNDARIES = {
    "是否接收真实企业微信回调": False,
    "是否联网": False,
    "是否读取凭据": False,
    "是否企业微信真实发送": False,
    "是否修改公共企业微信接入配置": False,
    "是否修改19310": False,
    "是否触发n8n": False,
    "是否写正式业务库": False,
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


def review_order(confidence: str, missing_count: int, risk_count: int) -> str:
    if confidence == "low" or missing_count >= 6 or risk_count >= 4:
        return "P1_high_manual_review"
    if confidence == "medium" or missing_count >= 3:
        return "P2_normal_manual_review"
    return "P3_light_manual_review"


def build_packet(index: int, summary: dict[str, Any], compliance_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    summary_id = str(summary.get("摘要ID", ""))
    compliance = compliance_map.get(summary_id, {})
    missing = as_list(summary.get("资料缺口摘要"))
    risks = as_list(summary.get("风险点摘要"))
    confidence = str(summary.get("置信度", "medium"))
    return {
        "阅读包ID": f"tax-wecom-human-review-packet-batch-{index:03d}",
        "摘要ID": summary_id,
        "来源草案ID": summary.get("来源草案ID", ""),
        "消息ID": summary.get("消息ID", ""),
        "业务事项": summary.get("业务事项", ""),
        "摘要状态": summary.get("摘要状态", ""),
        "复核状态": "pending_human_review",
        "合规结论": compliance.get("审查结论", "未找到合规记录"),
        "置信度": confidence,
        "建议复核顺序": review_order(confidence, len(missing), len(risks)),
        "事实摘要": summary.get("事实摘要", ""),
        "政策依据候选摘要": summary.get("政策依据候选摘要", {}),
        "依据层级摘要": as_list(summary.get("依据层级摘要")),
        "适用条件摘要": as_list(summary.get("适用条件摘要")),
        "资料缺口摘要": missing,
        "风险点摘要": risks,
        "人工复核项摘要": as_list(summary.get("人工复核项摘要")),
        "企业微信输出预览": summary.get("企业微信输出预览", ""),
        "输出边界": as_list(summary.get("输出边界")),
        "禁止动作": as_list(summary.get("禁止动作")),
        "复核结论占位": {
            "人工复核人": "待人工填写",
            "人工复核时间": "待人工填写",
            "复核意见": "待人工填写",
            "是否可进入证据候选层": "待人工填写",
            "是否需要补充资料": "待人工填写",
        },
        "是否写正式业务库": False,
        "是否调用模型推理": False,
        "是否企业微信真实发送": False,
        "是否生成正式税务结论": False,
        "是否形成正式复核结论": False,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 税收企业微信人工复核阅读包批量预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 资产身份：{report['资产身份']}",
        f"- 阅读包数量：{report['阅读包数量']}",
        f"- 红线阻断留痕数量：{report['红线阻断留痕数量']}",
        "- 说明：这是给人工复核人看的本地阅读包，不是正式复核结果，不是正式入口放行，不是税务结论。",
        "- 是否真实发送：False",
        "",
        "## 阅读包清单",
    ]
    for item in report["阅读包"]:
        lines.extend([
            f"### {item['阅读包ID']}",
            f"- 摘要ID：{item['摘要ID']}",
            f"- 消息ID：{item['消息ID']}",
            f"- 业务事项：{item['业务事项']}",
            f"- 复核状态：{item['复核状态']}",
            f"- 合规结论：{item['合规结论']}",
            f"- 置信度：{item['置信度']}",
            f"- 建议复核顺序：{item['建议复核顺序']}",
            f"- 资料缺口：{'; '.join(item['资料缺口摘要'])}",
            f"- 风险点：{'; '.join(item['风险点摘要'])}",
            f"- 人工复核项：{'; '.join(item['人工复核项摘要'])}",
            "",
        ])
    if report["红线阻断留痕"]:
        lines.extend(["## 红线阻断留痕", ""])
        for item in report["红线阻断留痕"]:
            lines.append(f"- 消息ID：{item.get('消息ID')}；原因：{item.get('拒绝流转原因') or item.get('阻断原因')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    summary_source = load(SUMMARY_JSON)
    compliance_source = load(COMPLIANCE_JSON)
    summaries = as_list(summary_source.get("摘要预演"))
    compliance_rows = as_list(compliance_source.get("单条审查结果"))
    compliance_map = {str(item.get("摘要ID", "")): item for item in compliance_rows}
    packets = [build_packet(index, item, compliance_map) for index, item in enumerate(summaries, start=1)]
    blocked = as_list(compliance_source.get("阻断留痕")) or as_list(summary_source.get("阻断留痕"))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信人工复核阅读包批量预演",
        "生成时间": now,
        "资产身份": "dry-run人工复核阅读包预演，不是真实企业微信消息，不是真实发送记录，不是正式复核结果，不是正式入口放行，不是税务结论。",
        "摘要来源": str(SUMMARY_JSON),
        "合规来源": str(COMPLIANCE_JSON),
        "阅读包保存路径": str(OUT_PACKET_JSON),
        "运行状态": "shadow_dry_run_pending_human_review",
        "阅读包数量": len(packets),
        "红线阻断留痕数量": len(blocked),
        "阅读包": packets,
        "红线阻断留痕": blocked,
        "安全边界": BOUNDARIES,
    }
    OUT_PACKET_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({"状态": "通过", "阅读包数量": len(packets), "阻断留痕数量": len(blocked), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
