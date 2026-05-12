# -*- coding: utf-8 -*-
"""
名称：生成文稿质检样本复盘报告.py
作用：读取文稿质检旁路记录，提炼第一阶段样本复盘结论、风险教训和下一步边界。
触发方式：python 生成文稿质检样本复盘报告.py
依赖：01杰哥智能系统/03数据/文稿质检/review_records.jsonl。
所属系统：01杰哥智能系统/文稿质检
输出：01杰哥智能系统/03数据/文稿质检/样本复盘/文稿质检样本复盘报告_最新.json 与 .md。
安全边界：只读审稿记录并写复盘报告；不调用模型、不触发n8n、不发送企业微信、不替换原文、不固化正式模板、不写股票正式档案、不调用券商接口、不自动交易。
标识：text-reviewer-sample-retrospective
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def smart_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return smart_root() / "03数据" / "文稿质检"


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalized_doc_type(doc_type: str) -> str:
    if doc_type == "stock_daily_recommendation":
        return "stock_daily"
    return doc_type


def issue_counter(records: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for record in records:
        for issue in record.get("review", {}).get("issues", []) or []:
            if isinstance(issue, dict):
                counter[str(issue.get("type") or "unknown")] += 1
    return counter


def pick_examples(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        record_id = str(record.get("id", ""))
        doc_type = normalized_doc_type(str(record.get("doc_type", "")))
        review = record.get("review", {}) if isinstance(record.get("review"), dict) else {}
        source = str(record.get("draft_source", ""))
        item = {
            "id": record_id,
            "文稿类型": doc_type,
            "来源": source,
            "评分": review.get("total_score"),
            "是否通过": review.get("pass"),
            "模型": record.get("model") or "未调用",
            "禁止字段改动数": len(record.get("forbidden_modified") or []),
            "状态": record.get("status", ""),
        }
        if record.get("forbidden_modified"):
            buckets["禁止字段改动样本"].append(item)
        if record.get("model_call", {}).get("status") == "success" and not review.get("pass"):
            buckets["模型失败或被回退样本"].append(item)
        if doc_type == "stock_position_diagnosis" and review.get("pass") is False:
            buckets["手机端排版失败样本"].append(item)
        if doc_type == "stock_position_diagnosis" and review.get("pass") is True:
            buckets["手机端排版修正后样本"].append(item)
        if record.get("status") == "adopted":
            buckets["用户采用样本"].append(item)
    return {key: value[:5] for key, value in buckets.items()}


def build_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    doc_type_counts: Counter[str] = Counter(normalized_doc_type(str(item.get("doc_type", ""))) for item in records)
    status_counts: Counter[str] = Counter(str(item.get("status", "")) for item in records)
    model_records = [item for item in records if item.get("model")]
    stock_records = [
        item for item in records
        if normalized_doc_type(str(item.get("doc_type", ""))).startswith("stock_")
    ]
    forbidden_records = [item for item in records if item.get("forbidden_modified")]
    adopted_records = [item for item in records if item.get("status") == "adopted"]
    passed_records = [item for item in records if item.get("review", {}).get("pass") is True]
    issues = issue_counter(records)
    lessons = [
        {
            "结论": "文稿质检第一阶段应继续旁路运行",
            "依据": "已有模型样本出现禁止字段改动或 JSON 不稳定，尚不能接管正式推送。",
            "落地": "审稿结果只入记录库和复盘报告，不自动替换、不自动发送、不固化正式模板。",
        },
        {
            "结论": "规则质检对手机端排版有稳定价值",
            "依据": "持仓诊断的单段密集文本被规则识别，拆成短段后通过。",
            "落地": "股票报告继续要求判断、策略、风险、后续观察分段；报告链接独立成行。",
        },
        {
            "结论": "模型只能当主编，不能当分析师",
            "依据": "模型建议稿可能改动或删除图片、报告链接等硬字段。",
            "落地": "股票名称、代码、价格、风险线、链接、免责声明等继续由脚本硬比对守门。",
        },
        {
            "结论": "每日推荐、单股查询、持仓诊断三类样本已覆盖",
            "依据": "三类 stock 文稿均已有旁路审稿样本。",
            "落地": "下一阶段不急于接正式链路，应先累计至少 5 次用户明确采用或确认有价值。",
        },
        {
            "结论": "硬件天花板要求默认规则优先",
            "依据": "多数有效观察可由规则完成，模型调用应保持手动或低频旁路。",
            "落地": "不让 7B 模型常态审每条推送；仅在样本观察、人工触发或低峰窗口调用。",
        },
    ]
    return {
        "名称": "文稿质检样本复盘报告",
        "版本": "2026-05-03",
        "生成时间": now,
        "结论": "继续第一阶段旁路观察，不进入正式推送链路",
        "是否允许进入第二阶段": False,
        "统计": {
            "审稿记录总数": len(records),
            "股票类记录数": len(stock_records),
            "调用模型记录数": len(model_records),
            "通过记录数": len(passed_records),
            "采用记录数": len(adopted_records),
            "禁止字段改动记录数": len(forbidden_records),
            "文稿类型分布": dict(doc_type_counts),
            "状态分布": dict(status_counts),
            "问题类型分布": dict(issues),
        },
        "样本例证": pick_examples(records),
        "复盘结论": lessons,
        "下一步": [
            "继续只读/旁路样本观察，优先收集用户明确采用或明确否定的反馈。",
            "保持规则质检默认启用，模型审稿仅手动触发或低峰试验。",
            "若累计 5 次用户确认有价值，再讨论第二阶段；仍不得自动替换原文。",
            "股票正式推送链路继续由现有报告生成和企微入口负责，质检层只提供观察依据。",
        ],
        "安全边界": {
            "调用模型": False,
            "触发n8n": False,
            "发送企业微信": False,
            "替换原文": False,
            "固化正式模板": False,
            "写股票正式档案": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 文稿质检样本复盘报告 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 总结：{report['结论']}",
        f"- 是否允许进入第二阶段：{report['是否允许进入第二阶段']}",
        "",
        "## 二、统计",
        "",
    ]
    for key, value in report["统计"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、样本例证", ""])
    for bucket, items in report["样本例证"].items():
        lines.extend([f"### {bucket}", ""])
        if not items:
            lines.append("- 无。")
        for item in items:
            lines.append(
                f"- {item['id']}｜{item['文稿类型']}｜评分 {item['评分']}｜"
                f"通过 {item['是否通过']}｜模型 {item['模型']}｜禁止字段改动 {item['禁止字段改动数']}"
            )
        lines.append("")
    lines.extend(["## 四、复盘结论", ""])
    for item in report["复盘结论"]:
        lines.append(f"- {item['结论']}：{item['依据']} 落地：{item['落地']}")
    lines.extend(["", "## 五、下一步", ""])
    for item in report["下一步"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 六、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    records_path = data_dir() / "review_records.jsonl"
    records = read_records(records_path)
    report = build_report(records)
    out_dir = data_dir() / "样本复盘"
    latest_json = out_dir / "文稿质检样本复盘报告_最新.json"
    latest_md = out_dir / "文稿质检样本复盘报告_最新.md"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(out_dir / f"文稿质检样本复盘报告_{stamp}.json", report)
    write_text(out_dir / f"文稿质检样本复盘报告_{stamp}.md", build_markdown(report))
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "结论": report["结论"],
        "审稿记录总数": report["统计"]["审稿记录总数"],
        "禁止字段改动记录数": report["统计"]["禁止字段改动记录数"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
