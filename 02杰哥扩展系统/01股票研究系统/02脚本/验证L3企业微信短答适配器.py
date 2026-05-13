# -*- coding: utf-8 -*-
"""
名称：验证L3企业微信短答适配器.py
作用：运行五样本单股分析，验证L3企业微信短答是否满足前台输出契约。
触发方式：python 验证L3企业微信短答适配器.py
安全边界：只调用本地股票助手函数；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


SAMPLES = [
    ("分析云南锗业", "云南锗业", "sz002428"),
    ("分析天齐锂业", "天齐锂业", "sz002466"),
    ("分析华虹公司", "华虹公司", "sh688347"),
    ("分析浙商中拓", "浙商中拓", "sz000906"),
    ("分析正丹股份", "正丹股份", "sz300641"),
]

FORBIDDEN_WORDS = [
    "买入",
    "卖出",
    "买点",
    "下单",
    "加仓",
    "减仓",
    "满仓",
    "半仓",
    "止盈",
    "目标价",
]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_assistant(root: Path) -> Any:
    script = root / "02脚本" / "股票助手入口.py"
    spec = importlib.util.spec_from_file_location("jiege_stock_assistant_entry_for_l3_verify", script)
    if not spec or not spec.loader:
        raise RuntimeError(f"无法加载股票助手入口：{script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_reply(question: str, expected_name: str, expected_code: str, text: str) -> dict[str, Any]:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    first_line = lines[0] if lines else ""
    why_line = next((line for line in lines if line.startswith("为什么：")), "")
    line_index = {line.split("：", 1)[0]: index for index, line in enumerate(lines) if "：" in line}
    trade_hits = [word for word in FORBIDDEN_WORDS if word in text]
    required_hits = {
        "analysis_object": first_line == f"分析对象：{expected_name}（{expected_code}）",
        "conclusion_second_line": len(lines) > 1 and lines[1].startswith("结论："),
        "has_conclusion": "结论：" in text,
        "has_one_sentence": "一句话：" in text,
        "has_action": "现在怎么处理：" in text,
        "has_watch": "观察条件：" in text,
        "has_risk": "风险线：" in text,
        "has_why": "为什么：" in text,
        "has_missing": "缺口：" in text,
        "has_safety_note": "仅供研究参考" in text and "不作为买卖指令" in text,
        "no_forbidden_trade_words": not trade_hits,
        "has_computed_volume_threshold": (
            ("成交额" not in text and "成交量" not in text)
            or ("当前成交额" in text or "当前成交量" in text)
            and ("1.10倍活跃线" in text or "放量达标线" in text)
        ),
        "no_old_finance_debt_words": all(word not in text for word in ["财报未接入", "基本面暂无", "用户需自行补财报"]),
        "no_null_placeholder": all(word not in text for word in ["null", "未知价格", "--", "——"]),
        "frontend_reply_not_too_long": len(text) <= 650,
        "frontend_line_count_controlled": len(lines) <= 11,
        "why_after_action_and_risk": line_index.get("现在怎么处理", 99) < line_index.get("为什么", -1) and line_index.get("风险线", 99) < line_index.get("为什么", -1),
        "why_line_is_frontend_summary": bool(why_line) and len(why_line) <= 110,
        "why_line_has_no_truncation": bool(why_line) and "…" not in why_line,
        "why_line_not_backend_report": bool(why_line) and all(word not in why_line for word in ["evidence", "missing", "item_scores", "分项", "字段"]),
    }
    blocking = [key for key, ok in required_hits.items() if not ok]
    return {
        "question": question,
        "expected_name": expected_name,
        "expected_code": expected_code,
        "first_line": first_line,
        "reply_length": len(text),
        "line_count": len(lines),
        "why_line_length": len(why_line),
        "trade_hits": trade_hits,
        "required_hits": required_hits,
        "blocking": blocking,
        "passed": not blocking,
        "reply": text,
    }


def build_markdown(report: dict[str, Any]) -> str:
    rows = []
    for item in report["samples"]:
        rows.append(
            "| {question} | {first_line} | {passed} | {reply_length} | {blocking} |".format(
                question=item["question"],
                first_line=item["first_line"],
                passed="通过" if item["passed"] else "失败",
                reply_length=item["reply_length"],
                blocking="无" if not item["blocking"] else "、".join(item["blocking"]),
            )
        )
    sample_blocks: list[str] = []
    for item in report["samples"]:
        sample_blocks.extend([
            f"## {item['question']}",
            "",
            "```text",
            item["reply"],
            "```",
            "",
        ])
    return "\n".join([
        "# L3企业微信短答适配器自动验收",
        "",
        f"生成时间：{report['generated_at']}",
        f"总体结论：{report['overall']['conclusion']}",
        "",
        "| 问题 | 首行 | 结果 | 长度 | 阻断项 |",
        "|---|---|---:|---:|---|",
        *rows,
        "",
        "## 安全边界",
        "",
        "- 不发送企业微信",
        "- 不触发 n8n",
        "- 不调用券商接口",
        "- 不自动交易",
        "",
        *sample_blocks,
    ])


def main() -> int:
    root = module_root()
    assistant = load_assistant(root)
    samples = []
    for question, name, code in SAMPLES:
        result = assistant.build_analysis(question, refresh=False, remember_context=False, entrance_role="助手")
        reply = str(result.get("企业微信回复") or result.get("回复") or "")
        item = validate_reply(question, name, code, reply)
        item["assistant_status"] = result.get("状态")
        item["standard_report_path"] = result.get("标准报告v2路径", "")
        samples.append(item)
    passed_count = sum(1 for item in samples if item["passed"])
    report = {
        "名称": "L3企业微信短答适配器自动验收",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "自动验收报告",
        "status": "passed" if passed_count == len(samples) else "failed",
        "samples": samples,
        "overall": {
            "sample_count": len(samples),
            "passed_count": passed_count,
            "blocking_count": sum(len(item["blocking"]) for item in samples),
            "conclusion": "五样本全部通过" if passed_count == len(samples) else "存在阻断项，需修复",
        },
        "safety_boundary": {
            "not_external_send": True,
            "not_n8n": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
        },
    }
    out_dir = root / "03数据" / "245L3评分基础资产"
    json_path = out_dir / "L3企业微信短答适配器自动验收_20260507.json"
    md_path = out_dir / "L3企业微信短答适配器自动验收_20260507.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({"status": report["status"], "passed_count": passed_count, "json": str(json_path), "md": str(md_path)}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
