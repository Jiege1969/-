# -*- coding: utf-8 -*-
"""生成用户视角报告读感验收样例。

仅生成股票线W1影子验收样例，用于检查前台输出是否符合使用者视角。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "用户视角报告读感验收样例_最新.json"
MD_OUT = DATA_DIR / "用户视角报告读感验收样例_最新.md"


CHECKLIST = [
    {"id": "READ-001", "name": "对象明确", "requirement": "第一行必须写股票名称和代码。"},
    {"id": "READ-002", "name": "结论先行", "requirement": "第二行必须给结论词，不先堆指标。"},
    {"id": "READ-003", "name": "主因压缩", "requirement": "主因只写1句，不展开分析过程。"},
    {"id": "READ-004", "name": "缺口清楚", "requirement": "关键缺口必须可执行、可补证。"},
    {"id": "READ-005", "name": "边界清楚", "requirement": "不得出现交易、下单或确定性收益表达。"},
]


SAMPLES = [
    {
        "stock": {"name": "云南锗业", "code": "002428"},
        "readability_result": "pass",
        "user_view_comment": "结论清楚，知道为什么只能观察，也知道下一步要补锗价、政策暴露度和财报。",
        "fix_needed": [],
    },
    {
        "stock": {"name": "天齐锂业", "code": "002466"},
        "readability_result": "pass",
        "user_view_comment": "短答没有堆技术指标，缺口集中在锂价和盈利修复，容易理解。",
        "fix_needed": [],
    },
    {
        "stock": {"name": "华虹公司", "code": "688347"},
        "readability_result": "pass_with_minor_gap",
        "user_view_comment": "结论可读，但半导体景气指标需要后续补成更具体的数据项。",
        "fix_needed": ["把半导体景气指标拆成可观测字段"],
    },
    {
        "stock": {"name": "浙商中拓", "code": "000906"},
        "readability_result": "pass",
        "user_view_comment": "暂不建议强结论的原因明确，现金流、负债和商品周期是关键。",
        "fix_needed": [],
    },
    {
        "stock": {"name": "正丹股份", "code": "300641"},
        "readability_result": "pass_with_minor_gap",
        "user_view_comment": "方向清楚，但产品价格、价差和利润弹性之间还可以再压缩成固定句式。",
        "fix_needed": ["补化工股产品价格到利润弹性的固定话术"],
    },
]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    asset = {
        "name": "用户视角报告读感验收样例",
        "version": "v1.0",
        "generated_at": generated_at,
        "asset_identity": "W1用户视角报告读感验收样例",
        "status": "shadow_readability_acceptance",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "checklist": CHECKLIST,
        "samples": SAMPLES,
        "summary": {
            "check_count": len(CHECKLIST),
            "sample_count": len(SAMPLES),
            "pass_count": len([item for item in SAMPLES if item["readability_result"] == "pass"]),
            "minor_gap_count": len([item for item in SAMPLES if item["readability_result"] == "pass_with_minor_gap"]),
            "real_wecom_send_allowed": False,
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
        "# 用户视角报告读感验收样例",
        "",
        f"- 生成时间：{generated_at}",
        "- 资产身份：W1用户视角报告读感验收样例",
        "- 状态：shadow_readability_acceptance",
        "",
    ]
    for item in SAMPLES:
        lines.append(f"- {item['stock']['name']}（{item['stock']['code']}）：{item['readability_result']}；{item['user_view_comment']}")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "ok", "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
