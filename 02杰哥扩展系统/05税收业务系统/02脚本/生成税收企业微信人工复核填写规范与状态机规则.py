# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = BASE_DIR / "人工复核状态机"
SOURCE_RECEIPT = BASE_DIR / "税收企业微信人工复核回执空白模板批量预演_最新.json"
SOURCE_REWRITE = BASE_DIR / "税收企业微信复核回执到草案状态回写预演_最新.json"
OUT_JSON = BASE_DIR / "税收企业微信人工复核填写规范与状态机规则_最新.json"
OUT_MD = BASE_DIR / "税收企业微信人工复核填写规范与状态机规则_最新.md"
DETAIL_JSON = OUT_DIR / "税收企业微信人工复核填写规范与状态机规则.json"


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


REQUIRED_FILL_FIELDS = [
    {
        "字段": "人工复核人",
        "填写要求": "填写内部复核责任人姓名或工号；不得填写客户身份证、手机号、银行卡等敏感信息。",
        "空白处理": "保持 blank_pending_human_fill，不得进入状态回写预演。",
    },
    {
        "字段": "人工复核时间",
        "填写要求": "使用 YYYY-MM-DD HH:MM:SS；必须晚于阅读包生成时间。",
        "空白处理": "保持 blank_pending_human_fill。",
    },
    {
        "字段": "政策依据层级与有效状态复核",
        "填写要求": "按法律、行政法规、部门规章、税务规范性文件、财税文件、政策解读、地方口径、案例、人工经验分层，并标注全文有效、已修改、废止、失效、尚未生效或待核验。",
        "允许值": ["evidence_ready", "pending_evidence_check", "evidence_blocked"],
        "空白处理": "不得进入当前适用依据候选层。",
    },
    {
        "字段": "业务事实充分性复核",
        "填写要求": "说明业务事实是否足以进入涉税业务分析契约；必须保留 missing 字段。",
        "允许值": ["facts_sufficient_for_draft", "facts_need_more_info", "facts_blocked"],
        "空白处理": "不得生成后续待复核分析草案。",
    },
    {
        "字段": "资料缺口复核",
        "填写要求": "逐项核对资料缺口，保留未补齐项和补充资料建议。",
        "允许值": ["missing_clear", "missing_need_more_info", "missing_blocked"],
        "空白处理": "保持 pending_review。",
    },
    {
        "字段": "风险点复核",
        "填写要求": "标注政策时效、依据层级、地方口径、事实缺失和企业微信误读风险。",
        "允许值": ["risk_reviewed", "risk_need_more_info", "risk_blocked"],
        "空白处理": "保持 pending_review。",
    },
    {
        "字段": "是否需要补充资料",
        "填写要求": "只能填写 yes、no 或 unknown；unknown 视同需要补充资料。",
        "允许值": ["yes", "no", "unknown"],
        "空白处理": "按 unknown 处理。",
    },
    {
        "字段": "是否进入当前适用依据候选层",
        "填写要求": "只能填写 evidence_ready、pending_review 或 blocked；不得写成税务结论确认。",
        "允许值": ["evidence_ready", "pending_review", "blocked"],
        "空白处理": "保持 pending_review。",
    },
    {
        "字段": "是否允许进入后续待复核分析草案",
        "填写要求": "只能填写 allow_draft_preview、need_more_info 或 block；allow 也只代表可进入待复核草案，不代表正式结论。",
        "允许值": ["allow_draft_preview", "need_more_info", "block"],
        "空白处理": "不得进入后续草案。",
    },
    {
        "字段": "人工复核意见",
        "填写要求": "写明依据、事实、缺口、风险和下一步处理建议；禁止写正式税务意见或确定金额。",
        "空白处理": "不得升级状态。",
    },
]


STATE_MACHINE = [
    {
        "当前状态": "blank_pending_human_fill",
        "触发条件": "人工填写区任一必填字段为空白、待人工填写或格式不合规。",
        "目标状态": "pending_human_review",
        "动作": "no_op_shadow_preview",
        "说明": "继续等待人工填写，不改变阅读包、摘要或草案源文件。",
    },
    {
        "当前状态": "pending_human_review",
        "触发条件": "10 个必填字段均已填写，但存在待核验、需要补充资料或证据未达 evidence_ready。",
        "目标状态": "pending_review",
        "动作": "shadow_status_preview_only",
        "说明": "只形成待复核状态预演，不进入当前适用依据候选层。",
    },
    {
        "当前状态": "pending_human_review",
        "触发条件": "依据层级和有效状态为 evidence_ready，业务事实可进入草案，且允许进入后续待复核分析草案。",
        "目标状态": "evidence_ready",
        "动作": "shadow_status_preview_only",
        "说明": "仅代表证据与事实可供后续待复核草案使用，不代表正式税务结论。",
    },
    {
        "当前状态": "pending_human_review",
        "触发条件": "政策依据被阻断、业务事实被阻断、风险被阻断或人工复核意见明确不允许进入草案。",
        "目标状态": "blocked",
        "动作": "shadow_status_preview_only",
        "说明": "只登记阻断原因，不能自动删除、覆盖或外发既有资料。",
    },
]


FORBIDDEN_WORDS = [
    "confirmed_conclusion",
    "正式税务结论",
    "正式税务意见",
    "一定适用",
    "可以享受",
    "金额确定",
    "自动申报",
    "自动退税",
    "自动开票",
]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    receipt = load_json(SOURCE_RECEIPT)
    rewrite = load_json(SOURCE_REWRITE)
    receipt_items = receipt.get("回执模板", [])
    rewrite_items = rewrite.get("回写预演", [])

    sample_guidance = []
    for item in receipt_items:
        sample_guidance.append({
            "回执ID": item.get("回执ID", ""),
            "业务事项": item.get("业务事项", ""),
            "当前回执状态": item.get("回执状态", ""),
            "建议复核顺序": item.get("建议复核顺序", ""),
            "可进入状态机判断前置条件": [
                "10 个人工填写字段全部非空。",
                "政策依据层级与有效状态已按证据层级复核。",
                "业务事实、资料缺口、风险点均已复核。",
                "人工复核意见未包含禁止短语。",
            ],
            "默认处理": "空白或不合规时保持 pending_human_review，不触发真实回写。",
        })

    result = {
        "名称": "税收企业微信人工复核填写规范与状态机规则",
        "生成时间": now,
        "资产身份": "dry-run人工复核填写规范与状态机规则，不是真实状态回写，不写正式业务库，不是正式入口放行，不是税务结论。",
        "回执模板来源": str(SOURCE_RECEIPT),
        "状态回写预演来源": str(SOURCE_REWRITE),
        "回执模板数量": len(receipt_items),
        "既有回写预演数量": len(rewrite_items),
        "必填人工复核字段数量": len(REQUIRED_FILL_FIELDS),
        "必填人工复核字段": REQUIRED_FILL_FIELDS,
        "允许状态": ["draft", "evidence_ready", "pending_review", "human_reviewed", "blocked"],
        "禁用状态": ["confirmed_conclusion", "formal_tax_conclusion"],
        "状态机规则": STATE_MACHINE,
        "样例回执填写指引": sample_guidance,
        "禁止短语": FORBIDDEN_WORDS,
        "回写护栏": [
            "本规则只描述状态流，不执行状态变更。",
            "任何状态预演均不得写入草案源文件或正式业务库。",
            "human_reviewed 只能表示人工已复核流程记录完成，不代表税务结论确认。",
            "evidence_ready 只能表示证据可供后续待复核草案引用，不代表业务一定适用。",
            "空白、不合规、含禁止短语或含敏感信息的回执一律阻断。",
        ],
        "下一步低风险队列": [
            "生成税收企业微信人工复核回执填报校验器预演。",
            "生成税收企业微信状态机反事实演练，验证单点满足条件不会误升级。",
        ],
        "安全边界": SAFETY,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text, encoding="utf-8")
    DETAIL_JSON.write_text(text, encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核填写规范与状态机规则",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run规则草案，不是真实状态回写，不是正式入口放行，不是税务结论。",
        f"- 回执模板数量：{len(receipt_items)}",
        f"- 既有回写预演数量：{len(rewrite_items)}",
        f"- 必填人工复核字段数量：{len(REQUIRED_FILL_FIELDS)}",
        "",
        "## 必填人工复核字段",
        "",
    ]
    for item in REQUIRED_FILL_FIELDS:
        lines.append(f"- {item['字段']}：{item['填写要求']}")
    lines.extend(["", "## 状态机规则", ""])
    for item in STATE_MACHINE:
        lines.append(f"- {item['当前状态']} -> {item['目标状态']}：{item['触发条件']}；动作={item['动作']}。")
    lines.extend(["", "## 回写护栏", ""])
    for item in result["回写护栏"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 禁止短语", ""])
    for item in FORBIDDEN_WORDS:
        lines.append(f"- {item}")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in result["下一步低风险队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in SAFETY.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "报告": str(OUT_MD), "JSON": str(OUT_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
