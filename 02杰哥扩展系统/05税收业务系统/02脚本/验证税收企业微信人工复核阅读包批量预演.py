# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
PACKET_DIR = DATA_DIR / "人工复核阅读包"
SOURCE_JSON = DATA_DIR / "税收企业微信人工复核阅读包批量预演_最新.json"
SOURCE_MD = DATA_DIR / "税收企业微信人工复核阅读包批量预演_最新.md"
PACKET_JSON = PACKET_DIR / "税收企业微信人工复核阅读包批量预演.json"
OUT_JSON = DATA_DIR / "税收企业微信人工复核阅读包批量预演验收_最新.json"
OUT_MD = DATA_DIR / "税收企业微信人工复核阅读包批量预演验收_最新.md"

REQUIRED_PACKET_FIELDS = [
    "阅读包ID",
    "摘要ID",
    "来源草案ID",
    "消息ID",
    "业务事项",
    "复核状态",
    "合规结论",
    "政策依据候选摘要",
    "依据层级摘要",
    "适用条件摘要",
    "资料缺口摘要",
    "风险点摘要",
    "人工复核项摘要",
    "复核结论占位",
]

PROHIBITED_PHRASES = [
    "可以享受",
    "不能享受",
    "应纳税额",
    "退税金额",
    "请立即申报",
    "请办理退税",
    "请开票",
    "无需人工复核",
    "本阅读包为正式税务意见",
    "正式复核结果：通过",
]


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def has_required_fields(packet: dict[str, Any]) -> bool:
    return all(field in packet and packet.get(field) not in ("", None, []) for field in REQUIRED_PACKET_FIELDS)


def evidence_state(packet: dict[str, Any]) -> str:
    evidence = packet.get("政策依据候选摘要", {})
    if isinstance(evidence, dict):
        return str(evidence.get("依据状态", ""))
    return ""


def main() -> int:
    source = load(SOURCE_JSON)
    packet_copy = load(PACKET_JSON)
    text = SOURCE_MD.read_text(encoding="utf-8", errors="ignore") if SOURCE_MD.exists() else ""
    packets = source.get("阅读包", [])
    boundaries = source.get("安全边界", {})
    json_text = json.dumps(source, ensure_ascii=False)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checks = [
        check("阅读包JSON存在", SOURCE_JSON.exists(), str(SOURCE_JSON)),
        check("阅读包Markdown存在", SOURCE_MD.exists(), str(SOURCE_MD)),
        check("阅读包归档副本存在", PACKET_JSON.exists(), str(PACKET_JSON)),
        check("归档副本与最新文件数量一致", len(packet_copy.get("阅读包", [])) == len(packets), len(packet_copy.get("阅读包", []))),
        check("阅读包数量为5", source.get("阅读包数量") == 5 and len(packets) == 5, {"阅读包数量": source.get("阅读包数量"), "明细": len(packets)}),
        check("红线阻断留痕数量为1", source.get("红线阻断留痕数量") == 1, source.get("红线阻断留痕数量")),
        check("全部阅读包字段完整", all(has_required_fields(item) for item in packets), packets),
        check("全部保持待人工复核状态", all(item.get("复核状态") == "pending_human_review" for item in packets), [item.get("复核状态") for item in packets]),
        check("全部合规审查已通过", all(item.get("合规结论") == "通过" for item in packets), [item.get("合规结论") for item in packets]),
        check("全部依据仍为候选待核验", all(evidence_state(item) == "candidate_only_pending_evidence_review" for item in packets), [evidence_state(item) for item in packets]),
        check("全部包含资料缺口风险点人工复核项", all(item.get("资料缺口摘要") and item.get("风险点摘要") and item.get("人工复核项摘要") for item in packets), packets),
        check("复核结论仍为空白占位", all("待人工填写" in json.dumps(item.get("复核结论占位", {}), ensure_ascii=False) for item in packets), packets),
        check("全部未真实发送未写库未调用模型未生成结论", all(item.get("是否企业微信真实发送") is False and item.get("是否写正式业务库") is False and item.get("是否调用模型推理") is False and item.get("是否生成正式税务结论") is False for item in packets), packets),
        check("安全边界全部为False", all(value is False for value in boundaries.values()), boundaries),
        check("未命中正式结论或办税执行短语", not any(phrase in json_text for phrase in PROHIBITED_PHRASES), PROHIBITED_PHRASES),
        check("Markdown声明不是正式复核结果不是正式入口放行不是税务结论", "不是正式复核结果" in text and "不是正式入口放行" in text and "不是税务结论" in text, "资产身份声明"),
    ]
    failed = [item for item in checks if item["结果"] != "通过"]
    report = {
        "名称": "税收企业微信人工复核阅读包批量预演验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": boundaries,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信人工复核阅读包批量预演验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}；{item['详情']}")
    lines.extend(["", "## 安全边界"])
    for key, value in boundaries.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
