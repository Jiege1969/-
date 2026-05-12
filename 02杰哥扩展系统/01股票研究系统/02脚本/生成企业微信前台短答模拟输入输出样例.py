# -*- coding: utf-8 -*-
"""生成企业微信前台短答影子输入输出样例。

本脚本只写入股票线本地影子样例，不接企业微信真实发送、不改入口、不改正式配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "企业微信前台短答模拟输入输出样例_最新.json"
MD_OUT = DATA_DIR / "企业微信前台短答模拟输入输出样例_最新.md"


SAMPLES = [
    {
        "input_text": "云南锗业现在怎么样",
        "name": "云南锗业",
        "code": "002428",
        "conclusion": "可纳入观察",
        "reason": "锗相关政策与资源品主题具备催化，但财报、资金和连续价格证据仍需补齐。",
        "gap": "缺少最新财报结构化摘要、锗价连续观测和资金/机构证据的自动入账结果。",
        "confidence": "medium",
        "focus": "复核锗价、成交额、板块热度与公告变化。",
    },
    {
        "input_text": "天齐锂业能看吗",
        "name": "天齐锂业",
        "code": "002466",
        "conclusion": "可纳入观察",
        "reason": "锂资源属性明确，行业价格若企稳会改善研究价值，但当前行业景气和盈利修复证据不足。",
        "gap": "缺少锂价连续观测、最新财报拆解和资金趋势的结构化证据。",
        "confidence": "medium",
        "focus": "复核锂价、库存、盈利弹性和板块相对强弱。",
    },
    {
        "input_text": "华虹公司现在怎么样",
        "name": "华虹公司",
        "code": "688347",
        "conclusion": "可纳入观察",
        "reason": "半导体国产化方向具备中长期研究价值，但当前仍要看景气、产能利用率和估值消化。",
        "gap": "缺少半导体景气指标、最新财报质量和机构资金变化的结构化证据。",
        "confidence": "medium",
        "focus": "复核晶圆代工景气、政策证据和财报毛利率趋势。",
    },
    {
        "input_text": "浙商中拓怎么样",
        "name": "浙商中拓",
        "code": "000906",
        "conclusion": "暂不建议强结论",
        "reason": "供应链业务受商品周期和经营现金流影响较大，缺少足够行业与资金证据前不应给强判断。",
        "gap": "缺少最新财报经营现金流、商品价格联动和资金/机构证据。",
        "confidence": "low",
        "focus": "复核经营现金流、负债结构、商品周期和公告事项。",
    },
    {
        "input_text": "正丹股份现在怎么看",
        "name": "正丹股份",
        "code": "300641",
        "conclusion": "可纳入观察",
        "reason": "化工品价格与景气弹性较强，若价格连续观测确认改善，研究价值会提升。",
        "gap": "缺少核心产品价格连续观测、最新财报利润弹性和资金承接证据。",
        "confidence": "medium",
        "focus": "复核TMA等产品价格、订单景气和资金承接变化。",
    },
]


def build_front_answer(item: dict) -> str:
    return "\n".join(
        [
            f"{item['name']}（{item['code']}）",
            f"结论：{item['conclusion']}。",
            f"主要原因：{item['reason']}",
            f"关键缺口：{item['gap']}",
            f"置信度：{item['confidence']}；下一次重点复核：{item['focus']}",
        ]
    )


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = []
    for item in SAMPLES:
        records.append(
            {
                "input_channel": "wecom_shadow",
                "input_text": item["input_text"],
                "real_wecom_send_allowed": False,
                "formal_entry_allowed": False,
                "resolved_stock": {"name": item["name"], "code": item["code"]},
                "simulated_front_answer": build_front_answer(item),
                "backend_trace_required": {
                    "evidence": ["对象已识别", "前台输出按结论型短答格式生成"],
                    "missing": [item["gap"]],
                    "confidence_reason": "影子样例仅验证输出契约，真实分数必须读取结构化证据后生成。",
                    "next_review_focus": item["focus"],
                    "gate_decisions": {
                        "object_first": True,
                        "evidence_before_judgment": True,
                        "missing_explicit": True,
                        "real_wecom_send": False,
                        "formal_entry_write": False,
                    },
                    "source_assets": [
                        "L3评分契约",
                        "股票对象识别验收",
                        "前台结论型短答统一验收记录",
                    ],
                },
            }
        )
    asset = {
        "name": "企业微信前台短答模拟输入输出样例",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1企业微信前台短答影子输入输出样例",
        "status": "shadow_io_sample",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_service_change": True,
        "records": records,
        "summary": {
            "sample_count": len(records),
            "object_clear_count": len(records),
            "shadow_output_count": len(records),
            "real_wecom_send_allowed": False,
            "formal_entry_allowed": False,
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_formal_config": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 企业微信前台短答模拟输入输出样例",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1企业微信前台短答影子输入输出样例",
        "- 状态：shadow_io_sample",
        "- 边界：仅本地影子样例，不发送企业微信，不改正式入口。",
        "",
    ]
    for record in records:
        lines.extend(
            [
                f"## {record['resolved_stock']['name']}（{record['resolved_stock']['code']}）",
                "",
                "```text",
                record["simulated_front_answer"],
                "```",
                "",
            ]
        )
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
