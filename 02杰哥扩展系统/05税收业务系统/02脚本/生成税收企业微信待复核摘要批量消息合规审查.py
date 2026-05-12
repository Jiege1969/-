# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
RULE_PATH = TAX_ROOT / "01配置" / "税收企业微信消息合规审查规则.json"
SOURCE_JSON = DATA_DIR / "税收企业微信待复核分析摘要批量预演_最新.json"
OUT_JSON = DATA_DIR / "税收企业微信待复核摘要批量消息合规审查_最新.json"
OUT_MD = DATA_DIR / "税收企业微信待复核摘要批量消息合规审查_最新.md"


SUMMARY_REQUIRED = [
    "【税收分析助手-待复核草案摘要】",
    "状态：",
    "置信度：",
    "政策依据候选：",
    "依据层级明细：",
    "待复核资料清单：",
    "资料缺口：",
    "风险点：",
    "人工复核：",
    "边界：待复核草案摘要预演",
]


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_message(message_id: str, summary_id: str, message: str, rule: dict[str, Any]) -> dict[str, Any]:
    max_len = int(rule.get("长度限制", {}).get("最大字符数", 1800))
    missing_required = [item for item in SUMMARY_REQUIRED if item not in message]
    prohibited = [item for item in rule.get("禁止短语", []) if item in message]
    sensitive_hits = []
    for item in rule.get("敏感信息模式", []):
        pattern = item.get("正则", "")
        if pattern and re.search(pattern, message):
            sensitive_hits.append(item.get("名称", pattern))
    passed = not missing_required and not prohibited and not sensitive_hits and len(message) <= max_len
    return {
        "摘要ID": summary_id,
        "消息ID": message_id,
        "审查结论": "通过" if passed else "失败",
        "消息字符数": len(message),
        "最大字符数": max_len,
        "缺失必须包含": missing_required,
        "命中禁止短语": prohibited,
        "命中敏感信息模式": sensitive_hits,
        "是否真实发送": False,
        "是否读取凭据": False,
        "是否生成正式税务结论": False,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 税收企业微信待复核摘要批量消息合规审查",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 审查结论：{report['审查结论']}",
        f"- 摘要数量：{report['摘要数量']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        f"- 阻断留痕数量：{report['阻断留痕数量']}",
        "- 资产身份：dry-run批量消息合规审查，不是真实发送记录，不是正式入口放行，不是税务结论。",
        "- 是否真实发送：False",
        "",
        "## 单条审查结果",
    ]
    for item in report["单条审查结果"]:
        lines.extend([
            f"### {item['摘要ID']}",
            f"- 消息ID：{item['消息ID']}",
            f"- 审查结论：{item['审查结论']}",
            f"- 消息字符数：{item['消息字符数']}/{item['最大字符数']}",
            f"- 缺失必须包含：{item['缺失必须包含'] or '无'}",
            f"- 命中禁止短语：{item['命中禁止短语'] or '无'}",
            f"- 命中敏感信息模式：{item['命中敏感信息模式'] or '无'}",
            "",
        ])
    if report["阻断留痕"]:
        lines.extend(["## 阻断留痕", ""])
        for item in report["阻断留痕"]:
            lines.append(f"- 消息ID：{item.get('消息ID')}；原因：{item.get('拒绝流转原因') or item.get('阻断原因')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rule = load(RULE_PATH)
    source = load(SOURCE_JSON)
    summaries = source.get("摘要预演", [])
    blocked = source.get("阻断留痕", [])
    results = [
        check_message(
            str(item.get("消息ID", "")),
            str(item.get("摘要ID", "")),
            str(item.get("企业微信输出预览", "")),
            rule,
        )
        for item in summaries
    ]
    failed = [item for item in results if item["审查结论"] != "通过"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    boundaries = {
        "是否接收真实企业微信回调": False,
        "是否联网": False,
        "是否读取凭据": False,
        "是否企业微信真实发送": False,
        "是否修改公共企业微信接入配置": False,
        "是否修改19310": False,
        "是否触发n8n": False,
        "是否写正式业务库": False,
        "是否调用模型推理": False,
        "是否接电子税务局": False,
        "是否接财税软件": False,
        "是否生成正式税务结论": False,
    }
    report = {
        "名称": "税收企业微信待复核摘要批量消息合规审查",
        "生成时间": now,
        "资产身份": "dry-run批量消息合规审查，不是真实发送记录，不是正式入口放行，不是税务结论。",
        "规则来源": str(RULE_PATH),
        "摘要来源": str(SOURCE_JSON),
        "摘要必须包含": SUMMARY_REQUIRED,
        "审查结论": "通过" if not failed else "失败",
        "摘要数量": len(summaries),
        "通过数量": len(results) - len(failed),
        "失败数量": len(failed),
        "阻断留痕数量": len(blocked),
        "单条审查结果": results,
        "阻断留痕": blocked,
        "是否真实发送": False,
        "安全边界": boundaries,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({"状态": report["审查结论"], "摘要数量": len(summaries), "失败数量": len(failed), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
