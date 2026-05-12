# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信报告反馈改版候选.py
作用：把企业微信中关于股票报告内容和展示方式的反馈，转为进化候选。
边界：只写入进化系统候选层；不写正式规则、不触发n8n、不发送企业微信、不接券商、不交易。
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def workspace_root() -> Path:
    return root_dir().parent


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def classify_feedback(record: dict[str, Any]) -> tuple[str, str, str]:
    feedback_type = str(record.get("反馈类型") or record.get("类型") or "").strip()
    reason = str(record.get("理由") or record.get("原始命令") or "").strip()
    text = f"{feedback_type} {reason}"
    if any(word in text for word in ("股票名称需要可点击详情", "可以点击", "点击", "具体分析报告", "详情链接", "报告链接")):
        return (
            "stock_report_clickable_detail_link",
            "股票名称需要可点击详情",
            "股票报告中的股票名称应使用企业微信可点击链接，点击后进入该股票的具体分析入口。",
        )
    if any(word in text for word in ("太空泛", "空泛", "太笼统")):
        return (
            "stock_report_less_generic",
            "报告不能太空泛",
            "股票报告应减少后台分析过程堆砌，增加为什么看、当前判断、下一步观察条件。",
        )
    if any(word in text for word in ("风险没讲清", "风险不清", "风险")):
        return (
            "stock_report_clear_risk",
            "风险解释需要更清楚",
            "股票报告应把风险/缺口写成用户能判断的具体事项，避免只给抽象风险词。",
        )
    if any(word in text for word in ("少了财务", "财务依据", "缺财务", "财务")):
        return (
            "stock_report_financial_evidence",
            "需要补财务依据",
            "股票报告在条件允许时应增加财务依据或明确财务数据缺口。",
        )
    if any(word in text for word in ("行业逻辑不够", "行业逻辑", "行业")):
        return (
            "stock_report_industry_logic",
            "需要补行业逻辑",
            "股票报告应说明行业背景、位置和驱动因素，而不是只列单股技术信息。",
        )
    if any(word in text for word in ("说到位", "口径保留", "保留")):
        return (
            "stock_report_keep_good_style",
            "有效口径保留",
            "用户明确认可的报告表达应进入保留候选，后续用于稳定输出风格。",
        )
    return (
        "stock_report_general_feedback",
        feedback_type or "一般报告反馈",
        "把用户对股票报告的自然语言反馈保留为候选样本，等待复盘归纳。",
    )


def build_candidate(category: str, label: str, proposal: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    evidence = []
    for item in records:
        source_text = str(item.get("原始命令") or item.get("理由") or "")
        evidence.append(
            {
                "时间": item.get("时间", ""),
                "反馈类型": item.get("反馈类型", ""),
                "股票代码": item.get("代码", ""),
                "股票名称": item.get("名称", ""),
                "原始命令": source_text,
                "去重键": sha256_text(f"{category}|{source_text}|{item.get('时间', '')}")[:16],
            }
        )
    return {
        "候选ID": f"{category}-{sha256_text(category + label)[:10]}",
        "候选类型": category,
        "用户表达": label,
        "证据数量": len(records),
        "证据样本": evidence[:8],
        "建议改版": proposal,
        "目标层级": "股票企业微信报告展示层/用户阅读稿",
        "建议验收": [
            "企业微信端今日观察报告不展示后台技术过程",
            "股票名称可点击进入单股详情入口",
            "报告包含为什么看、当前判断、风险/缺口、下一步观察",
            "反馈只进入候选层，不自动改正式规则",
        ],
        "当前处理": "候选层沉淀，等待影子验收和人工确认后再考虑正式化",
        "是否自动转正式规则": False,
        "是否写正式规则库": False,
        "是否触发n8n": False,
        "是否真实发送企业微信": False,
        "是否接券商": False,
        "是否交易": False,
    }


def main() -> int:
    now = datetime.now()
    root = root_dir()
    base = workspace_root()
    stock_root = base / "02杰哥扩展系统" / "01股票研究系统"
    feedback_log = stock_root / "04日志" / "用户反馈" / "反馈日志.json"
    sample_dir = root / "03数据" / "13股票复盘反馈样本"
    candidate_dir = root / "03数据" / "15复盘转经验候选"

    feedback_data = read_json(feedback_log, {})
    records = feedback_data.get("反馈记录", []) if isinstance(feedback_data, dict) else []
    valid_records = [item for item in records if isinstance(item, dict) and item.get("是否有效", True) is not False]

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    labels: dict[str, str] = {}
    proposals: dict[str, str] = {}
    for record in valid_records:
        category, label, proposal = classify_feedback(record)
        grouped[category].append(record)
        labels[category] = label
        proposals[category] = proposal

    candidates = [
        build_candidate(category, labels[category], proposals[category], items)
        for category, items in sorted(grouped.items())
    ]

    safety = {
        "写正式规则库": False,
        "自动转正式规则": False,
        "触发n8n": False,
        "企业微信真实发送": False,
        "调用券商接口": False,
        "自动交易": False,
        "修改总管面板": False,
        "修改一键接续包": False,
        "重载19310": False,
        "重载19302": False,
    }
    sample_report = {
        "名称": "股票企业微信报告反馈样本",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "来源": str(feedback_log),
        "反馈总数": len(records),
        "有效反馈数": len(valid_records),
        "样本": valid_records,
        "安全边界": safety,
    }
    candidate_report = {
        "名称": "股票企业微信报告反馈改版候选",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "来源反馈日志": str(feedback_log),
        "候选数量": len(candidates),
        "候选": candidates,
        "结论": "已把企业微信报告反馈转为改版候选；只进入候选层，不自动写正式规则。",
        "安全边界": safety,
    }

    stamp = now.strftime("%Y%m%d-%H%M%S")
    sample_json = sample_dir / f"股票企业微信报告反馈样本_{stamp}.json"
    sample_md = sample_dir / f"股票企业微信报告反馈样本_{stamp}.md"
    candidate_json = candidate_dir / f"股票企业微信报告反馈改版候选_{stamp}.json"
    candidate_md = candidate_dir / f"股票企业微信报告反馈改版候选_{stamp}.md"
    write_json(sample_json, sample_report)
    write_json(sample_dir / "股票企业微信报告反馈样本_最新.json", sample_report)
    write_json(candidate_json, candidate_report)
    write_json(candidate_dir / "股票企业微信报告反馈改版候选_最新.json", candidate_report)

    sample_text = "\n".join(
        [
            "# 股票企业微信报告反馈样本",
            "",
            f"- 生成时间：{sample_report['生成时间']}",
            f"- 反馈总数：{len(records)}",
            f"- 有效反馈数：{len(valid_records)}",
            f"- 来源：{feedback_log}",
            "- 边界：只作为反馈样本，不写正式规则，不触发n8n，不发送企业微信，不交易。",
        ]
    )
    candidate_lines = [
        "# 股票企业微信报告反馈改版候选",
        "",
        f"- 生成时间：{candidate_report['生成时间']}",
        f"- 候选数量：{len(candidates)}",
        "- 结论：企业微信中的报告内容和展示需求已进入进化候选层。",
        "",
        "## 候选清单",
    ]
    for item in candidates:
        candidate_lines.extend(
            [
                "",
                f"### {item['用户表达']}",
                f"- 候选ID：{item['候选ID']}",
                f"- 证据数量：{item['证据数量']}",
                f"- 建议改版：{item['建议改版']}",
                "- 当前处理：候选层沉淀，不自动转正式规则。",
            ]
        )
    candidate_lines.extend(["", "## 红线", "- 未写正式规则库；未触发n8n；未真实发送企业微信；未接券商；未交易。"])
    write_text(sample_md, sample_text)
    write_text(sample_dir / "股票企业微信报告反馈样本_最新.md", sample_text)
    write_text(candidate_md, "\n".join(candidate_lines))
    write_text(candidate_dir / "股票企业微信报告反馈改版候选_最新.md", "\n".join(candidate_lines))

    print(json.dumps({"候选数量": len(candidates), "输出": str(candidate_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
