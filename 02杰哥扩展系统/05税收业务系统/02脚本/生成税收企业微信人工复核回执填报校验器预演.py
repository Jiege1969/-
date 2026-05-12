# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = BASE_DIR / "人工复核回执校验器"
SOURCE_RECEIPT = BASE_DIR / "税收企业微信人工复核回执空白模板批量预演_最新.json"
SOURCE_RULE = BASE_DIR / "税收企业微信人工复核填写规范与状态机规则_最新.json"
OUT_JSON = BASE_DIR / "税收企业微信人工复核回执填报校验器预演_最新.json"
OUT_MD = BASE_DIR / "税收企业微信人工复核回执填报校验器预演_最新.md"
DETAIL_JSON = OUT_DIR / "税收企业微信人工复核回执填报校验器预演.json"


BLANK_VALUES = {"", "待人工填写", "待填写", "unknown_blank"}
SENSITIVE_PATTERNS = ["身份证", "银行卡", "手机号", "密码", "token", "secret", "webhook", "key="]

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


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def is_blank(value: object) -> bool:
    return str(value).strip() in BLANK_VALUES


def contains_sensitive(value: object) -> bool:
    text = str(value).lower()
    return any(pattern.lower() in text for pattern in SENSITIVE_PATTERNS)


def validate_receipt(receipt: dict, required_fields: list[dict], forbidden_words: list[str]) -> dict:
    fill_area = receipt.get("人工填写区", {})
    missing_fields = []
    sensitive_hits = []
    forbidden_hits = []

    for field in required_fields:
        name = field.get("字段", "")
        value = fill_area.get(name, "")
        if is_blank(value):
            missing_fields.append(name)
        if contains_sensitive(value):
            sensitive_hits.append(name)
        if any(word in str(value) for word in forbidden_words):
            forbidden_hits.append(name)

    allowed_to_preview = not missing_fields and not sensitive_hits and not forbidden_hits
    if allowed_to_preview:
        target_status = "pending_review"
        block_reason = ""
    else:
        target_status = "pending_human_review"
        block_reason = "人工复核回执未满足字段完整性、敏感信息或禁止短语校验，不得进入状态预演。"

    return {
        "校验ID": f"tax-wecom-human-review-receipt-check-{receipt.get('回执ID', '')}",
        "回执ID": receipt.get("回执ID", ""),
        "业务事项": receipt.get("业务事项", ""),
        "来源回执状态": receipt.get("回执状态", ""),
        "必填字段数量": len(required_fields),
        "缺失字段": missing_fields,
        "敏感信息命中字段": sensitive_hits,
        "禁止短语命中字段": forbidden_hits,
        "是否通过填报校验": allowed_to_preview,
        "目标状态预演": target_status,
        "阻断原因": block_reason,
        "动作": "validation_only_no_status_write",
        "是否真实回写状态": False,
        "是否写正式业务库": False,
        "是否企业微信真实发送": False,
        "是否生成正式税务结论": False,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    receipt_data = load_json(SOURCE_RECEIPT)
    rule_data = load_json(SOURCE_RULE)
    receipts = receipt_data.get("回执模板", [])
    required_fields = rule_data.get("必填人工复核字段", [])
    forbidden_words = rule_data.get("禁止短语", [])
    validations = [validate_receipt(item, required_fields, forbidden_words) for item in receipts]
    passed_count = sum(1 for item in validations if item["是否通过填报校验"])
    blocked_count = len(validations) - passed_count

    result = {
        "名称": "税收企业微信人工复核回执填报校验器预演",
        "生成时间": now,
        "资产身份": "dry-run人工复核回执填报校验器预演，不是真实状态回写，不写正式业务库，不是人工复核结论，不是税务结论。",
        "回执模板来源": str(SOURCE_RECEIPT),
        "填写规范来源": str(SOURCE_RULE),
        "运行状态": "validation_only_no_status_write",
        "回执数量": len(receipts),
        "校验记录数量": len(validations),
        "通过填报校验数量": passed_count,
        "阻断数量": blocked_count,
        "校验规则": [
            "10 个人工复核必填字段均不得为空白或待人工填写。",
            "人工填写区不得包含敏感信息提示词或凭据类关键词。",
            "人工填写区不得包含正式税务意见、确定金额、一定适用等禁止短语。",
            "通过校验也只允许进入状态预演，不允许真实回写。",
            "空白回执全部保持 pending_human_review。",
        ],
        "校验记录": validations,
        "下一步低风险队列": [
            "生成税收企业微信人工复核状态机反事实演练。",
            "生成税收企业微信人工复核校验失败整改清单。"
        ],
        "安全边界": SAFETY,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text, encoding="utf-8")
    DETAIL_JSON.write_text(text, encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核回执填报校验器预演",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run校验器预演，不是真实状态回写，不是人工复核结论，不是税务结论。",
        f"- 回执数量：{len(receipts)}",
        f"- 校验记录数量：{len(validations)}",
        f"- 通过填报校验数量：{passed_count}",
        f"- 阻断数量：{blocked_count}",
        "",
        "## 校验规则",
        "",
    ]
    for item in result["校验规则"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 校验记录", ""])
    for item in validations:
        lines.append(f"- {item['回执ID']}：通过={item['是否通过填报校验']}，目标状态预演={item['目标状态预演']}，缺失字段={len(item['缺失字段'])}，动作={item['动作']}。")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in result["下一步低风险队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in SAFETY.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "报告": str(OUT_MD), "通过填报校验数量": passed_count, "阻断数量": blocked_count}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
