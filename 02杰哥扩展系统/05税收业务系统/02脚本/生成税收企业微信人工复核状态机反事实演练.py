# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = BASE_DIR / "人工复核状态机反事实演练"
SOURCE_RULE = BASE_DIR / "税收企业微信人工复核填写规范与状态机规则_最新.json"
SOURCE_VALIDATOR = BASE_DIR / "税收企业微信人工复核回执填报校验器预演_最新.json"
OUT_JSON = BASE_DIR / "税收企业微信人工复核状态机反事实演练_最新.json"
OUT_MD = BASE_DIR / "税收企业微信人工复核状态机反事实演练_最新.md"
DETAIL_JSON = OUT_DIR / "税收企业微信人工复核状态机反事实演练.json"


SAFETY = {
    "是否接收真实企业微信回调": False,
    "是否联网": False,
    "是否读取凭据": False,
    "是否企业微信真实发送": False,
    "是否修改公共企业微信接入配置": False,
    "是否修改19310": False,
    "是否触发n8n": False,
    "是否写正式业务库": False,
    "是否写草案源文件": False,
    "是否真实回写状态": False,
    "是否调用模型推理": False,
    "是否接电子税务局": False,
    "是否接财税软件": False,
    "是否生成正式税务结论": False,
    "是否形成正式复核结论": False,
    "是否覆盖历史资料": False,
    "是否删除历史审计记录": False,
}


SCENARIOS = [
    {
        "场景ID": "tax-review-counterfactual-001",
        "场景": "只填写人工复核人，其他字段空白",
        "证据状态": "pending_review",
        "事实状态": "facts_need_more_info",
        "资料缺口状态": "missing_need_more_info",
        "风险状态": "risk_need_more_info",
        "允许进入草案": "need_more_info",
        "含禁止短语": False,
        "含敏感信息": False,
        "缺失字段数": 9,
    },
    {
        "场景ID": "tax-review-counterfactual-002",
        "场景": "证据为evidence_ready但业务事实不足",
        "证据状态": "evidence_ready",
        "事实状态": "facts_need_more_info",
        "资料缺口状态": "missing_clear",
        "风险状态": "risk_reviewed",
        "允许进入草案": "allow_draft_preview",
        "含禁止短语": False,
        "含敏感信息": False,
        "缺失字段数": 0,
    },
    {
        "场景ID": "tax-review-counterfactual-003",
        "场景": "业务事实充分但证据仍待核验",
        "证据状态": "pending_evidence_check",
        "事实状态": "facts_sufficient_for_draft",
        "资料缺口状态": "missing_clear",
        "风险状态": "risk_reviewed",
        "允许进入草案": "allow_draft_preview",
        "含禁止短语": False,
        "含敏感信息": False,
        "缺失字段数": 0,
    },
    {
        "场景ID": "tax-review-counterfactual-004",
        "场景": "允许进入草案但风险点未复核",
        "证据状态": "evidence_ready",
        "事实状态": "facts_sufficient_for_draft",
        "资料缺口状态": "missing_clear",
        "风险状态": "risk_need_more_info",
        "允许进入草案": "allow_draft_preview",
        "含禁止短语": False,
        "含敏感信息": False,
        "缺失字段数": 0,
    },
    {
        "场景ID": "tax-review-counterfactual-005",
        "场景": "全部字段完整但人工意见含正式结论类禁止短语",
        "证据状态": "evidence_ready",
        "事实状态": "facts_sufficient_for_draft",
        "资料缺口状态": "missing_clear",
        "风险状态": "risk_reviewed",
        "允许进入草案": "allow_draft_preview",
        "含禁止短语": True,
        "含敏感信息": False,
        "缺失字段数": 0,
    },
    {
        "场景ID": "tax-review-counterfactual-006",
        "场景": "全部字段完整但包含敏感信息提示词",
        "证据状态": "evidence_ready",
        "事实状态": "facts_sufficient_for_draft",
        "资料缺口状态": "missing_clear",
        "风险状态": "risk_reviewed",
        "允许进入草案": "allow_draft_preview",
        "含禁止短语": False,
        "含敏感信息": True,
        "缺失字段数": 0,
    },
    {
        "场景ID": "tax-review-counterfactual-007",
        "场景": "全部门禁满足，仅允许进入证据可用预演",
        "证据状态": "evidence_ready",
        "事实状态": "facts_sufficient_for_draft",
        "资料缺口状态": "missing_clear",
        "风险状态": "risk_reviewed",
        "允许进入草案": "allow_draft_preview",
        "含禁止短语": False,
        "含敏感信息": False,
        "缺失字段数": 0,
    },
]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def decide(scenario: dict) -> dict:
    blockers = []
    if scenario["缺失字段数"] > 0:
        blockers.append("人工复核必填字段未填满")
    if scenario["证据状态"] != "evidence_ready":
        blockers.append("政策依据层级或有效状态未达到evidence_ready")
    if scenario["事实状态"] != "facts_sufficient_for_draft":
        blockers.append("业务事实不足")
    if scenario["资料缺口状态"] != "missing_clear":
        blockers.append("资料缺口未复核清楚")
    if scenario["风险状态"] != "risk_reviewed":
        blockers.append("风险点未完成复核")
    if scenario["允许进入草案"] != "allow_draft_preview":
        blockers.append("未允许进入后续待复核分析草案")
    if scenario["含禁止短语"]:
        blockers.append("命中禁止短语")
    if scenario["含敏感信息"]:
        blockers.append("命中敏感信息提示词")

    if scenario["含禁止短语"] or scenario["含敏感信息"]:
        target_status = "blocked"
    elif blockers:
        target_status = "pending_review"
    else:
        target_status = "evidence_ready"

    return {
        **scenario,
        "阻断原因": blockers,
        "目标状态预演": target_status,
        "是否误升级为evidence_ready": target_status == "evidence_ready" and bool(blockers),
        "是否误升级为human_reviewed": False,
        "动作": "counterfactual_preview_only_no_status_write",
        "是否真实回写状态": False,
        "是否写正式业务库": False,
        "是否企业微信真实发送": False,
        "是否生成正式税务结论": False,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rule_data = load_json(SOURCE_RULE)
    validator_data = load_json(SOURCE_VALIDATOR)
    results = [decide(item) for item in SCENARIOS]
    mis_upgrade = [item for item in results if item["是否误升级为evidence_ready"] or item["是否误升级为human_reviewed"]]
    target_counts = {}
    for item in results:
        target_counts[item["目标状态预演"]] = target_counts.get(item["目标状态预演"], 0) + 1

    result = {
        "名称": "税收企业微信人工复核状态机反事实演练",
        "生成时间": now,
        "资产身份": "dry-run状态机反事实演练，不是真实状态回写，不写正式业务库，不是人工复核结论，不是税务结论。",
        "状态机规则来源": str(SOURCE_RULE),
        "回执校验器来源": str(SOURCE_VALIDATOR),
        "状态机规则数量": len(rule_data.get("状态机规则", [])),
        "校验器阻断数量": validator_data.get("阻断数量", 0),
        "演练场景数量": len(results),
        "误升级数量": len(mis_upgrade),
        "目标状态统计": target_counts,
        "演练结果": results,
        "结论": "通过" if not mis_upgrade else "失败",
        "下一步低风险队列": [
            "生成税收企业微信人工复核校验失败整改清单。",
            "生成税收企业微信待复核分析草案出入口状态索引。"
        ],
        "安全边界": SAFETY,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text, encoding="utf-8")
    DETAIL_JSON.write_text(text, encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核状态机反事实演练",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run反事实演练，不是真实状态回写，不是人工复核结论，不是税务结论。",
        f"- 演练场景数量：{len(results)}",
        f"- 误升级数量：{len(mis_upgrade)}",
        f"- 结论：{result['结论']}",
        "",
        "## 演练结果",
        "",
    ]
    for item in results:
        lines.append(f"- {item['场景ID']}：{item['场景']} -> {item['目标状态预演']}，误升evidence_ready={item['是否误升级为evidence_ready']}，误升human_reviewed={item['是否误升级为human_reviewed']}。")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in result["下一步低风险队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in SAFETY.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": result["结论"], "报告": str(OUT_MD), "误升级数量": len(mis_upgrade)}, ensure_ascii=False))
    return 0 if not mis_upgrade else 1


if __name__ == "__main__":
    raise SystemExit(main())
