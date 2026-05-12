# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_DIR = BASE_DIR / "人工复核再校验样例"
SOURCE_REMEDIATION = BASE_DIR / "税收企业微信人工复核校验失败整改清单_最新.json"
SOURCE_RULE = BASE_DIR / "税收企业微信人工复核填写规范与状态机规则_最新.json"
OUT_JSON = BASE_DIR / "税收企业微信人工复核整改后再校验样例模板_最新.json"
OUT_MD = BASE_DIR / "税收企业微信人工复核整改后再校验样例模板_最新.md"
DETAIL_JSON = OUT_DIR / "税收企业微信人工复核整改后再校验样例模板.json"


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


FIELD_SAMPLE_VALUES = {
    "人工复核人": "样例复核人A",
    "人工复核时间": "2026-05-08 12:40:00",
    "政策依据层级与有效状态复核": "pending_evidence_check",
    "业务事实充分性复核": "facts_need_more_info",
    "资料缺口复核": "missing_need_more_info",
    "风险点复核": "risk_need_more_info",
    "是否需要补充资料": "yes",
    "是否进入当前适用依据候选层": "pending_review",
    "是否允许进入后续待复核分析草案": "need_more_info",
    "人工复核意见": "样例意见：证据层级、有效状态、业务事实和资料缺口仍需人工继续复核；本记录仅用于再校验样例，不构成税务意见。",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    remediation = load_json(SOURCE_REMEDIATION)
    rule = load_json(SOURCE_RULE)
    required_fields = [item.get("字段") for item in rule.get("必填人工复核字段", []) if item.get("字段")]
    remediation_items = remediation.get("整改清单", [])

    samples = []
    for item in remediation_items:
        fill_area = {field: FIELD_SAMPLE_VALUES.get(field, "样例待复核值") for field in required_fields}
        samples.append({
            "样例ID": f"tax-wecom-human-review-recheck-sample-{item.get('回执ID', '')}",
            "来源整改ID": item.get("整改ID", ""),
            "来源回执ID": item.get("回执ID", ""),
            "业务事项": item.get("业务事项", ""),
            "样例性质": "template_only_not_real_receipt",
            "人工填写区样例": fill_area,
            "再校验入口": "local_validation_preview_only",
            "预期校验状态": "pending_review",
            "预期阻断说明": "样例默认仍保持待复核，不自动进入evidence_ready或human_reviewed。",
            "是否系统代填真实回执": False,
            "是否真实回写状态": False,
            "是否写正式业务库": False,
            "是否企业微信真实发送": False,
            "是否生成正式税务结论": False,
        })

    result = {
        "名称": "税收企业微信人工复核整改后再校验样例模板",
        "生成时间": now,
        "资产身份": "dry-run人工复核整改后再校验样例模板，不是真实回执，不是真实状态回写，不写正式业务库，不是税务结论。",
        "系统定位": "涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        "整改清单来源": str(SOURCE_REMEDIATION),
        "填写规范来源": str(SOURCE_RULE),
        "运行状态": "sample_template_only_no_status_write",
        "样例数量": len(samples),
        "必填字段数量": len(required_fields),
        "必填字段": required_fields,
        "再校验样例": samples,
        "再校验步骤": [
            "人工复核人根据整改清单补齐真实回执；系统不得代填。",
            "补齐后的回执先进入本地填报校验器预演。",
            "校验通过也只能进入状态预演，不得真实回写草案源文件。",
            "任何样例、校验结果或状态预演均不得解释为正式税务意见。",
        ],
        "下一步低风险队列": [
            "生成税收企业微信待复核分析草案出入口索引反事实校验。",
            "生成税收企业微信人工复核样例敏感信息复扫报告。",
        ],
        "安全边界": SAFETY,
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    OUT_JSON.write_text(text, encoding="utf-8")
    DETAIL_JSON.write_text(text, encoding="utf-8")

    lines = [
        "# 税收企业微信人工复核整改后再校验样例模板",
        "",
        f"- 生成时间：{now}",
        "- 资产身份：dry-run样例模板，不是真实回执，不是真实状态回写，不是税务结论。",
        "- 系统定位：涉税业务分析专家助手的政策证据底座/待复核分析草案链路，不是办税执行系统，不是正式税务意见。",
        f"- 样例数量：{len(samples)}",
        f"- 必填字段数量：{len(required_fields)}",
        "",
        "## 再校验步骤",
        "",
    ]
    for step in result["再校验步骤"]:
        lines.append(f"- {step}")
    lines.extend(["", "## 样例索引", ""])
    for item in samples:
        lines.append(f"- {item['样例ID']}：来源回执={item['来源回执ID']}，业务事项={item['业务事项']}，预期状态={item['预期校验状态']}。")
    lines.extend(["", "## 下一步低风险队列", ""])
    for item in result["下一步低风险队列"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in SAFETY.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": "完成", "报告": str(OUT_MD), "样例数量": len(samples)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
