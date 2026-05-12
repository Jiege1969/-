# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收企业微信待复核草案骨架到分析摘要预演规则.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PREVIEW_JSON = OUT_DIR / "税收企业微信待复核草案骨架到分析摘要预演_最新.json"
PREVIEW_MD = OUT_DIR / "税收企业微信待复核草案骨架到分析摘要预演_最新.md"
REPORT_JSON = OUT_DIR / "税收企业微信待复核草案骨架到分析摘要预演验收_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信待复核草案骨架到分析摘要预演验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def has_unmasked_sensitive(text: str) -> bool:
    patterns = [
        r"(?<!\d)1[3-9]\d{9}(?!\d)",
        r"(?<![0-9A-Za-z])\d{17}[\dXx](?![0-9A-Za-z])",
        r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE)
    preview = load_json(PREVIEW_JSON)
    summaries = preview.get("摘要预演", [])
    safety = preview.get("安全边界", {})
    required = set(rule.get("摘要必填字段", []))
    allowed_status = set(rule.get("摘要状态词", []))
    banned_status = set(rule.get("禁用状态词", []))
    forbidden_phrases = ["可以享受", "不能享受", "应纳税额", "退税金额", "无需人工复核", "正式税务意见"]
    missing_rows = []
    for item in summaries:
        missing = sorted(required - set(item.keys()))
        if missing:
            missing_rows.append({"摘要ID": item.get("摘要ID"), "缺少字段": missing})
    preview_messages = "\n".join(str(item.get("企业微信输出预览", "")) for item in summaries)
    all_text = json.dumps(summaries, ensure_ascii=False)
    status_values = [item.get("摘要状态") for item in summaries]
    checks = [
        check("摘要规则存在", RULE.exists(), str(RULE)),
        check("摘要预演JSON存在", PREVIEW_JSON.exists(), str(PREVIEW_JSON)),
        check("摘要预演Markdown存在", PREVIEW_MD.exists(), str(PREVIEW_MD)),
        check("运行状态为shadow_dry_run", preview.get("运行状态") == "shadow_dry_run", preview.get("运行状态")),
        check("至少生成1条摘要", len(summaries) >= 1, len(summaries)),
        check("摘要字段齐备", not missing_rows, missing_rows),
        check("摘要状态合法且未使用禁用状态", all(status in allowed_status and status not in banned_status for status in status_values), status_values),
        check("政策依据仍为候选待核验", all(item.get("政策依据候选摘要", {}).get("依据状态") == "candidate_only_pending_evidence_review" for item in summaries), summaries),
        check("摘要包含资料缺口风险点和人工复核项", all(item.get("资料缺口摘要") and item.get("风险点摘要") and item.get("人工复核项摘要") for item in summaries), summaries),
        check("企业微信输出预览存在且为待复核摘要", all("待复核" in item.get("企业微信输出预览", "") for item in summaries), preview_messages),
        check("企业微信输出预览不含正式结论短语", not any(phrase in preview_messages for phrase in forbidden_phrases), preview_messages),
        check("摘要不写正式库不调用模型不真实发送不生成正式结论", all(item.get("是否写正式业务库") is False and item.get("是否调用模型推理") is False and item.get("是否企业微信真实发送") is False and item.get("是否生成正式税务结论") is False for item in summaries), summaries),
        check("敏感信息已脱敏", not has_unmasked_sensitive(all_text), all_text[:500]),
        check("未联网未读取凭据未真实发送", safety.get("是否联网") is False and safety.get("是否读取凭据") is False and safety.get("是否企业微信真实发送") is False, safety),
        check("未调用模型未生成正式结论", safety.get("是否调用模型推理") is False and safety.get("是否生成正式税务结论") is False, safety),
        check("未触发n8n未接办税系统", safety.get("是否触发n8n") is False and safety.get("是否接电子税务局") is False and safety.get("是否接财税软件") is False, safety),
    ]
    passed = sum(1 for row in checks if row["结果"] == "通过")
    failed = len(checks) - passed
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "税收企业微信待复核草案骨架到分析摘要预演验收",
        "生成时间": now,
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": safety,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信待复核草案骨架到分析摘要预演验收",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for row in checks:
        lines.append(f"- {row['检查项']}：{row['结果']}。{row['详情']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
