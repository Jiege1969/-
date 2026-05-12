# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = BASE_DIR / "人工复核整改清单"
SOURCE_VALIDATOR = BASE_DIR / "税收企业微信人工复核回执填报校验器预演_最新.json"
SOURCE_RULE = BASE_DIR / "税收企业微信人工复核填写规范与状态机规则_最新.json"
OUT_JSON = BASE_DIR / "税收企业微信人工复核校验失败整改清单_最新.json"
OUT_MD = BASE_DIR / "税收企业微信人工复核校验失败整改清单_最新.md"
DETAIL_JSON = OUT_DIR / "税收企业微信人工复核校验失败整改清单.json"


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


def build_field_guidance(rule_data: dict) -> dict[str, dict]:
    guidance = {}
    for item in rule_data.get("必填人工复核字段", []):
        field = item.get("字段", "")
        if field:
            guidance[field] = {
                "填写要求": item.get("填写要求", ""),
                "允许值": item.get("允许值", []),
                "空白处理": item.get("空白处理", ""),
            }
    return guidance


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    validator_data = load_json(SOURCE_VALIDATOR)
    rule_data = load_json(SOURCE_RULE)
    field_guidance = build_field_guidance(rule_data)
    records = validator_data.get("校验记录", [])
    failed_records = [item for item in records if not item.get("是否通过填报校验")]

    remediation_items = []
    for item in failed_records:
        missing_fields = item.get("缺失字段", [])
        remediation_items.append({
            "整改ID": f"tax-wecom-human-review-remediation-{item.get('回执ID', '')}",
            "回执ID": item.get("回执ID", ""),
            "业务事项": item.get("业务事项", ""),
            "当前状态": item.get("目标状态预演", "pending_human_review"),
            "整改类型": "fill_required_human_review_fields",
            "缺失字段数量": len(missing_fields),
            "缺失字段": [
                {
                    "字段": field,
                    "填写要求": field_guidance.get(field, {}).get("填写要求", ""),
                    "允许值": field_guidance.get(field, {}).get("允许值", []),
                    "空白处理": field_guidance.get(field, {}).get("空白处理", ""),
                    "整改动作": "由人工复核人补齐，不得由系统代填。",
                }
                for field in missing_fields
            ],
            "敏感信息整改": item.get("敏感信息命中字段", []),
            "禁止短语整改": item.get("禁止短语命中字段", []),
            "重新提交条件": [
                "10 个人工复核必填字段全部非空。",
                "字段值符合允许值或填写要求。",
                "人工复核意见不得包含正式税务意见、确定金额、一定适用等禁止短语。",
                "人工填写区不得包含凭据、Webhook、Token、身份证、银行卡、手机号等敏感信息。",
                "重新提交后仍只能进入本地校验预演，不得真实回写状态。",
            ],
            "是否允许系统代填": False,
            "是否真实回写状态": False,
            "是否写正式业务库": False,
            "是否企业微信真实发送": False,
            "是否生成正式税务结论": False,
        })

    result = {
        "名称": "税收企业微信人工复核校验失败整改清单",
        "生成时间": now,
        "资产身份": "dry-run人工复核整改清单，不是真实状态回写，不写正式业务库，不是人工复核结论，不是税务结论。",
        "校验器来源": str(SOURCE_VALIDATOR),
        "填写规范来源": str(SOURCE_RULE),
        "运行状态": "remediation_list_only_no_status_write",
        "校验记录数量": len(records),
        "失败记录数量": len(failed_records),
        "整改清单数量": len(remediation_items),
        "整改清单": remediation_items,
        "统一整改护栏": [
            "系统只能列出缺失字段和整改要求，不能代替人工填写。",
            "整改完成后也只允许重新进入本地校验预演。",
            "不得因整改清单生成而改变阅读包、摘要或草案状态。",
            "不得把整改清单、待复核分析草案或证据可用状态解释为正式税务意见。",
        ],
        "下一步低风险队列": [
            "生成税收企业微信待复核分析草案出入口状态索引。",
            "生成税收企业微信人工复核整改后再校验样例模板。",
        ],
        "安全边界": SAFETY,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text, encoding="utf-8")
    DETAIL_JSON.write_text(text, encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核校验失败整改清单",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run整改清单，不是真实状态回写，不是人工复核结论，不是税务结论。",
        f"- 校验记录数量：{len(records)}",
        f"- 失败记录数量：{len(failed_records)}",
        f"- 整改清单数量：{len(remediation_items)}",
        "",
        "## 整改清单",
        "",
    ]
    for item in remediation_items:
        lines.append(f"- {item['回执ID']}：{item['业务事项']}，缺失字段数量={item['缺失字段数量']}，整改类型={item['整改类型']}。")
    lines.extend(["", "## 统一整改护栏", ""])
    for item in result["统一整改护栏"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in result["下一步低风险队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in SAFETY.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "报告": str(OUT_MD), "整改清单数量": len(remediation_items)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
