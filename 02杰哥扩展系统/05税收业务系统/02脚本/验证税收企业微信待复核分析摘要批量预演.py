# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
RULE_PATH = TAX_ROOT / "01配置" / "税收企业微信待复核草案骨架到分析摘要预演规则.json"
SRC_JSON = DATA_DIR / "税收企业微信待复核分析摘要批量预演_最新.json"
SRC_MD = DATA_DIR / "税收企业微信待复核分析摘要批量预演_最新.md"
SUMMARY_JSON = DATA_DIR / "待复核分析摘要" / "税收企业微信待复核分析摘要批量预演.json"
OUT_JSON = DATA_DIR / "税收企业微信待复核分析摘要批量预演验收_最新.json"
OUT_MD = DATA_DIR / "税收企业微信待复核分析摘要批量预演验收_最新.md"


REQUIRED_FIELDS = [
    "摘要ID",
    "来源草案ID",
    "消息ID",
    "摘要状态",
    "业务事项",
    "事实摘要",
    "政策依据候选摘要",
    "依据层级摘要",
    "依据层级明细摘要",
    "适用条件摘要",
    "待复核资料清单摘要",
    "待复核说明摘要",
    "资料缺口摘要",
    "风险点摘要",
    "置信度",
    "人工复核项摘要",
    "企业微信输出预览",
    "输出边界",
    "禁止动作",
    "是否写正式业务库",
    "是否调用模型推理",
    "是否企业微信真实发送",
    "是否生成正式税务结论",
]
ALLOWED_STATUSES = {"draft_summary", "pending_review_summary"}
FORBIDDEN_STATUSES = {"confirmed_conclusion", "confirmed_tax_opinion", "final_conclusion"}
FORBIDDEN_PREVIEW_PHRASES = ["可以享受", "不能享受", "应纳税额", "退税金额", "无需人工复核", "正式税务意见"]


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if passed else "失败", "详情": detail}


def has_unmasked_sensitive(text: str) -> bool:
    patterns = [
        r"(?<!\d)1[3-9]\d{9}(?!\d)",
        r"(?<![0-9A-Za-z])\d{17}[\dXx](?![0-9A-Za-z])",
        r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def main() -> int:
    data = load(SRC_JSON)
    summary_file = load(SUMMARY_JSON)
    text = SRC_MD.read_text(encoding="utf-8", errors="ignore") if SRC_MD.exists() else ""
    summaries = data.get("摘要预演", [])
    blocked = data.get("阻断留痕", [])
    boundaries = data.get("安全边界", {})
    status_values = [item.get("摘要状态") for item in summaries]
    missing_rows = [
        {"摘要ID": item.get("摘要ID"), "缺少字段": sorted(set(REQUIRED_FIELDS) - set(item.keys()))}
        for item in summaries
        if sorted(set(REQUIRED_FIELDS) - set(item.keys()))
    ]
    preview_messages = "\n".join(str(item.get("企业微信输出预览", "")) for item in summaries)
    all_text = json.dumps(summaries, ensure_ascii=False)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    checks = [
        check("主JSON存在", SRC_JSON.exists(), str(SRC_JSON)),
        check("主Markdown存在", SRC_MD.exists(), str(SRC_MD)),
        check("摘要预演文件存在", SUMMARY_JSON.exists(), str(SUMMARY_JSON)),
        check("规则文件存在", RULE_PATH.exists(), str(RULE_PATH)),
        check("主JSON可解析", bool(data), data.get("名称", "未解析")),
        check("摘要预演文件可解析", bool(summary_file), summary_file.get("名称", "未解析")),
        check("运行状态为shadow_dry_run", data.get("运行状态") == "shadow_dry_run", data.get("运行状态")),
        check("草案骨架数量为5", data.get("草案骨架数量") == 5, data.get("草案骨架数量")),
        check("摘要数量为5", len(summaries) == 5 and data.get("摘要数量") == 5, len(summaries)),
        check("阻断数量为1", len(blocked) == 1 and data.get("阻断数量") == 1, len(blocked)),
        check("摘要字段齐备", not missing_rows, missing_rows),
        check("摘要状态合法", all(status in ALLOWED_STATUSES for status in status_values), status_values),
        check("摘要状态未使用禁用状态", not any(status in FORBIDDEN_STATUSES for status in status_values), status_values),
        check("包含draft_summary和pending_review_summary", {"draft_summary", "pending_review_summary"}.issubset(set(status_values)), status_values),
        check("政策依据仍为候选待核验", all(item.get("政策依据候选摘要", {}).get("依据状态") == "candidate_only_pending_evidence_review" for item in summaries), [item.get("摘要ID") for item in summaries]),
        check("全部摘要有依据层级和适用条件", all(item.get("依据层级摘要") and item.get("适用条件摘要") for item in summaries), [item.get("摘要ID") for item in summaries]),
        check("全部摘要有资料缺口风险点和人工复核项", all(item.get("资料缺口摘要") and item.get("风险点摘要") and item.get("人工复核项摘要") for item in summaries), [item.get("摘要ID") for item in summaries]),
        check("企业微信输出预览存在且保持待复核", all("待复核" in item.get("企业微信输出预览", "") for item in summaries), "待复核摘要预览"),
        check("企业微信输出预览不含正式结论短语", not any(phrase in preview_messages for phrase in FORBIDDEN_PREVIEW_PHRASES), preview_messages[:500]),
        check("敏感信息已脱敏", not has_unmasked_sensitive(all_text), all_text[:500]),
        check("全部摘要不写正式库不调用模型不真实发送不生成正式结论", all(item.get("是否写正式业务库") is False and item.get("是否调用模型推理") is False and item.get("是否企业微信真实发送") is False and item.get("是否生成正式税务结论") is False for item in summaries), "四项输出门禁=False"),
        check("硬边界全部为False", all(value is False for value in boundaries.values()), boundaries),
        check("Markdown声明不是正式业务库和税务结论", "不是正式业务库" in text and "不是税务结论" in text, "资产身份声明"),
    ]
    failed = [item for item in checks if item["结果"] != "通过"]
    result = {
        "名称": "税收企业微信待复核分析摘要批量预演验收",
        "生成时间": now,
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "安全边界": boundaries,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信待复核分析摘要批量预演验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{result['结论']}",
        f"- 通过数量：{result['通过数量']}",
        f"- 失败数量：{result['失败数量']}",
        "",
        "## 检查结果",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}；{item['详情']}")
    lines.extend(["", "## 安全边界"])
    for key, value in boundaries.items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": result["结论"], "通过数量": result["通过数量"], "失败数量": result["失败数量"], "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
