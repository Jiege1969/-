# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "29涉税业务分析契约影子样例"
GENERAL_JSON = OUT_DIR / "涉税业务分析契约影子样例_最新.json"
RD_JSON = OUT_DIR / "研发费用涉税业务分析契约影子样例_最新.json"
OUT_JSON = OUT_DIR / "涉税业务分析契约影子样例复核_最新.json"
OUT_MD = OUT_DIR / "涉税业务分析契约影子样例复核_最新.md"

REQUIRED_FIELDS = [
    "问题ID",
    "契约状态",
    "业务事实",
    "政策依据",
    "依据层级",
    "适用条件",
    "资料缺口",
    "风险点",
    "置信度",
    "人工复核项",
    "输出边界",
]
FORBIDDEN_PHRASES = [
    "该业务一定适用",
    "应纳税额",
    "退税金额",
    "无需人工复核",
    "confirmed_conclusion",
    "confirmed_tax_opinion",
    "auto_applicable",
]
SAFETY_FALSE_KEYS = [
    "是否联网",
    "是否下载",
    "是否调用模型推理",
    "是否写正式业务库",
    "是否生成正式税务结论",
    "是否接电子税务局",
    "是否接财税软件",
    "是否触发n8n",
    "是否企业微信真实发送",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def text_blob(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def review_one(name: str, path: Path, data: dict[str, Any]) -> dict[str, Any]:
    sample = data.get("影子样例", {})
    blob = text_blob(data)
    missing = [field for field in REQUIRED_FIELDS if is_empty(sample.get(field))]
    forbidden = [phrase for phrase in FORBIDDEN_PHRASES if phrase in blob]
    safety = data.get("安全边界", {})
    safety_risks = [
        {"字段": key, "当前值": safety.get(key), "期望值": False}
        for key in SAFETY_FALSE_KEYS
        if key in safety and safety.get(key) is not False
    ]
    contract_status = sample.get("契约状态")
    evidence = sample.get("政策依据", [])
    review_items = sample.get("人工复核项", [])
    boundary = text_blob(sample.get("输出边界", ""))

    risks = []
    if contract_status not in {"pending_review", "draft", "evidence_ready"}:
        risks.append(f"契约状态不在税务白名单：{contract_status}")
    if missing:
        risks.append(f"必备字段缺失：{missing}")
    if forbidden:
        risks.append(f"命中禁止结论短语：{forbidden}")
    if safety_risks:
        risks.append(f"安全边界未关闭：{safety_risks}")
    if not evidence:
        risks.append("缺少政策依据候选，不能形成分析草案。")
    if not review_items:
        risks.append("缺少人工复核项。")
    if "正式税务结论" not in boundary and "正式税务意见" not in boundary:
        risks.append("输出边界未明确不得生成正式税务结论或正式税务意见。")

    return {
        "样例名称": name,
        "来源文件": str(path),
        "契约状态": contract_status,
        "政策依据数量": len(evidence) if isinstance(evidence, list) else 0,
        "人工复核项数量": len(review_items) if isinstance(review_items, list) else 0,
        "缺失字段": missing,
        "禁止短语命中": forbidden,
        "安全边界风险": safety_risks,
        "风险项": risks,
        "复核结论": "通过" if not risks else "待纠偏",
        "是否生成正式税务结论": False,
    }


def write_md(report: dict[str, Any]) -> None:
    lines = [
        "# 涉税业务分析契约影子样例复核",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 样例数量：{report['样例数量']}",
        f"- 风险数量：{report['风险数量']}",
        "",
        "## 样例复核",
        "",
    ]
    for item in report["样例复核结果"]:
        lines.extend([
            f"### {item['样例名称']}",
            f"- 契约状态：{item['契约状态']}",
            f"- 政策依据数量：{item['政策依据数量']}",
            f"- 人工复核项数量：{item['人工复核项数量']}",
            f"- 复核结论：{item['复核结论']}",
            f"- 风险项：{item['风险项'] or '无'}",
            "",
        ])
    lines.extend(["## 下一步自动队列", ""])
    for item in report["下一步自动队列"]:
        lines.append(f"- {item['优先级']} {item['事项']}：{item['边界']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    samples = [
        ("通用涉税业务分析契约影子样例", GENERAL_JSON, load_json(GENERAL_JSON)),
        ("研发费用涉税业务分析契约影子样例", RD_JSON, load_json(RD_JSON)),
    ]
    results = [review_one(name, path, data) for name, path, data in samples]
    risks = [risk for item in results for risk in item["风险项"]]
    report = {
        "名称": "涉税业务分析契约影子样例复核",
        "生成时间": now,
        "资产身份": "涉税业务分析契约影子样例复核，不是正式税务结论库。",
        "样例数量": len(results),
        "风险数量": len(risks),
        "结论": "通过，影子样例保持待复核分析边界" if not risks else "待纠偏",
        "样例复核结果": results,
        "下一步自动队列": [
            {
                "优先级": "L2",
                "事项": "税收企业微信正式入口dry-run链路复检",
                "原因": "分析契约影子样例已复核，企业微信入口仍需保持dry-run门禁和消息合规。",
                "是否可自动推进": True,
                "边界": "只运行本地dry-run和验收脚本，不读取凭据，不启动服务，不真实发送，不生成正式税务结论。",
            }
        ],
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否调用模型推理": False,
            "是否写正式业务库": False,
            "是否生成正式税务结论": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(report)
    print(json.dumps({"状态": "完成", "风险数量": len(risks), "输出": str(OUT_JSON)}, ensure_ascii=False))
    return 0 if not risks else 1


if __name__ == "__main__":
    raise SystemExit(main())
