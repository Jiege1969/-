# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


TAX_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
DATA_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
SOURCE_JSON = DATA_DIR / "税收企业微信待复核草案骨架批量预演_最新.json"
RULE_PATH = TAX_ROOT / "01配置" / "税收企业微信待复核草案骨架到分析摘要预演规则.json"
SUMMARY_JSON = DATA_DIR / "待复核分析摘要" / "税收企业微信待复核分析摘要批量预演.json"
OUT_JSON = DATA_DIR / "税收企业微信待复核分析摘要批量预演_最新.json"
OUT_MD = DATA_DIR / "税收企业微信待复核分析摘要批量预演_最新.md"


FORBIDDEN_PREVIEW_PHRASES = [
    "可以享受",
    "不能享受",
    "应纳税额",
    "退税金额",
    "无需人工复核",
    "正式税务意见",
]


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def unique_short(items: list[Any], limit: int) -> list[str]:
    rows: list[str] = []
    for item in items:
        text = str(item).strip()
        if text and text not in rows:
            rows.append(text)
        if len(rows) >= limit:
            break
    return rows


def summarize_basis_details(items: list[Any], limit: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        row = {
            "依据名称": str(item.get("依据名称", "")).strip(),
            "依据层级": str(item.get("依据层级", "")).strip(),
            "有效状态": str(item.get("有效状态", "")).strip(),
            "待复核说明": str(item.get("待复核说明", "")).strip(),
        }
        key = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if row["依据名称"] and key not in seen:
            rows.append(row)
            seen.add(key)
        if len(rows) >= limit:
            break
    return rows


def mask_sensitive(text: str) -> str:
    patterns = [
        (r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[A-Za-z0-9_-]+", "[企业微信Webhook已脱敏]"),
        (r"(?<![0-9A-Za-z])\d{17}[\dXx](?![0-9A-Za-z])", "[身份证号已脱敏]"),
        (r"(?<!\d)1[3-9]\d{9}(?!\d)", "[手机号已脱敏]"),
        (r"(?<![0-9A-Za-z])\d{12,19}(?![0-9A-Za-z])", "[长编号已脱敏]"),
    ]
    masked = text
    for pattern, replacement in patterns:
        masked = re.sub(pattern, replacement, masked)
    return masked


def normalize_preview_terms(text: str) -> str:
    replacements = {
        "可以享受": "作出享受判断",
        "不能享受": "作出不适用判断",
        "应纳税额": "税额测算",
        "退税金额": "退税测算",
        "无需人工复核": "跳过人工复核",
        "正式税务意见": "对外税务意见",
    }
    normalized = text
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


def summary_status(skeleton_status: str) -> str:
    if skeleton_status == "pending_review":
        return "pending_review_summary"
    return "draft_summary"


def build_preview(summary: dict[str, Any], max_len: int) -> str:
    lines = [
        "【税收分析助手-待复核草案摘要】",
        f"事项：{summary['业务事项']}",
        f"状态：{summary['摘要状态']}",
        f"置信度：{summary['置信度']}",
        f"事实：{summary['事实摘要']}",
        "政策依据候选：",
    ]
    lines.extend(f"- {item}" for item in summary["政策依据候选摘要"].get("候选主题", []))
    lines.append("依据层级明细：")
    for item in summary["依据层级明细摘要"]:
        lines.append(f"- {item['依据名称']}｜层级：{item['依据层级']}｜有效状态：{item['有效状态']}｜待复核：{item['待复核说明']}")
    lines.append("待复核资料清单：")
    lines.extend(f"- {item}" for item in summary["待复核资料清单摘要"])
    lines.append("资料缺口：")
    lines.extend(f"- {item}" for item in summary["资料缺口摘要"])
    lines.append("风险点：")
    lines.extend(f"- {item}" for item in summary["风险点摘要"])
    lines.append("人工复核：")
    lines.extend(f"- {item}" for item in summary["人工复核项摘要"])
    if summary["待复核说明摘要"]:
        lines.append(f"待复核说明：{summary['待复核说明摘要']}")
    lines.append("边界：待复核草案摘要预演，不作为申报、退税、开票或办税执行依据。")
    preview = normalize_preview_terms(mask_sensitive("\n".join(lines)))
    if len(preview) > max_len:
        preview = preview[: max_len - 16].rstrip() + "\n...[已截断]"
    return preview


def build_summary(skeleton: dict[str, Any], rule: dict[str, Any], index: int) -> dict[str, Any]:
    limits = rule.get("摘要规则", {})
    policy = skeleton.get("政策依据", {})
    fact = skeleton.get("业务事实", {})
    summary = {
        "摘要ID": f"tax-wecom-review-summary-batch-{index:03d}",
        "来源草案ID": skeleton.get("草案ID"),
        "消息ID": skeleton.get("消息ID"),
        "摘要状态": summary_status(str(skeleton.get("契约状态", "draft"))),
        "业务事项": skeleton.get("业务事项", "涉税业务分析"),
        "事实摘要": mask_sensitive(str(fact.get("摘要", ""))),
        "政策依据候选摘要": {
            "依据状态": policy.get("依据状态"),
            "候选主题": unique_short(
                as_list(policy.get("候选主题")),
                int(limits.get("最大候选政策主题数", 4)),
            ),
            "说明": policy.get("说明"),
        },
        "依据层级摘要": unique_short(
            as_list(skeleton.get("依据层级")),
            int(limits.get("最大依据层级数", 8)),
        ),
        "依据层级明细摘要": summarize_basis_details(
            as_list(skeleton.get("依据层级明细")),
            int(limits.get("最大依据层级数", 8)),
        ),
        "适用条件摘要": unique_short(
            as_list(skeleton.get("适用条件")),
            int(limits.get("最大资料缺口数", 6)),
        ),
        "待复核资料清单摘要": unique_short(
            as_list(skeleton.get("待复核资料清单")),
            int(limits.get("最大资料缺口数", 6)),
        ),
        "待复核说明摘要": mask_sensitive(str(skeleton.get("待复核说明", ""))),
        "资料缺口摘要": unique_short(
            as_list(skeleton.get("资料缺口")),
            int(limits.get("最大资料缺口数", 6)),
        ),
        "风险点摘要": unique_short(
            as_list(skeleton.get("风险点")),
            int(limits.get("最大风险点数", 5)),
        ),
        "置信度": skeleton.get("置信度", "low"),
        "人工复核项摘要": unique_short(
            as_list(skeleton.get("人工复核项")),
            int(limits.get("最大人工复核项数", 6)),
        ),
        "企业微信输出预览": "",
        "输出边界": rule.get("输出边界", []),
        "禁止动作": rule.get("禁止动作", []),
        "是否写正式业务库": False,
        "是否调用模型推理": False,
        "是否企业微信真实发送": False,
        "是否生成正式税务结论": False,
    }
    summary["企业微信输出预览"] = build_preview(
        summary,
        int(limits.get("企业微信预览最大字符数", 1600)),
    )
    return summary


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 税收企业微信待复核分析摘要批量预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        "- 资产身份：dry-run批量摘要预演，不是真实企业微信消息，不是真实发送记录，不是正式业务库，不是税务结论。",
        f"- 草案骨架数量：{report['草案骨架数量']}",
        f"- 摘要数量：{report['摘要数量']}",
        f"- 阻断数量：{report['阻断数量']}",
        "",
        "## 摘要清单",
    ]
    for item in report["摘要预演"]:
        lines.extend(
            [
                f"### {item['摘要ID']} {item['业务事项']}",
                f"- 来源草案：{item['来源草案ID']}",
                f"- 消息ID：{item['消息ID']}",
                f"- 摘要状态：{item['摘要状态']}",
                f"- 置信度：{item['置信度']}",
                "",
                "```text",
                item["企业微信输出预览"],
                "```",
                "",
            ]
        )
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
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    source = load(SOURCE_JSON)
    rule = load(RULE_PATH)
    skeletons = as_list(source.get("草案骨架"))
    blocked = as_list(source.get("阻断留痕"))
    allowed_status = set(rule.get("允许草案状态", []))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summaries = [
        build_summary(skeleton, rule, index)
        for index, skeleton in enumerate(skeletons, start=1)
        if skeleton.get("契约状态") in allowed_status
    ]
    status_blocked = [
        {
            "草案ID": skeleton.get("草案ID"),
            "消息ID": skeleton.get("消息ID"),
            "契约状态": skeleton.get("契约状态"),
            "阻断原因": "草案状态不允许进入待复核分析摘要批量预演",
            "是否写正式业务库": False,
            "是否企业微信真实发送": False,
            "是否生成正式税务结论": False,
        }
        for skeleton in skeletons
        if skeleton.get("契约状态") not in allowed_status
    ]
    all_blocked = blocked + status_blocked
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
    summary_file = {
        "名称": "税收企业微信待复核分析摘要批量预演文件",
        "生成时间": now,
        "规则来源": str(RULE_PATH),
        "来源草案骨架": str(SOURCE_JSON),
        "运行状态": "shadow_dry_run",
        "摘要数量": len(summaries),
        "阻断数量": len(all_blocked),
        "摘要预演": summaries,
        "阻断留痕": all_blocked,
        "安全边界": boundaries,
    }
    report = {
        "名称": "税收企业微信待复核分析摘要批量预演",
        "生成时间": now,
        "资产身份": "dry-run批量摘要预演，不是真实企业微信消息，不是真实发送记录，不是正式业务库，不是税务结论。",
        "规则来源": str(RULE_PATH),
        "草案骨架来源": str(SOURCE_JSON),
        "摘要预演文件": str(SUMMARY_JSON),
        "运行状态": "shadow_dry_run",
        "草案骨架数量": len(skeletons),
        "摘要数量": len(summaries),
        "阻断数量": len(all_blocked),
        "摘要状态统计": {
            "pending_review_summary": sum(1 for item in summaries if item["摘要状态"] == "pending_review_summary"),
            "draft_summary": sum(1 for item in summaries if item["摘要状态"] == "draft_summary"),
        },
        "摘要预演": summaries,
        "阻断留痕": all_blocked,
        "安全边界": boundaries,
    }
    SUMMARY_JSON.write_text(json.dumps(summary_file, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({"状态": "完成", "摘要数量": len(summaries), "阻断数量": len(all_blocked), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
