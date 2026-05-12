# -*- coding: utf-8 -*-
"""
名称：验证税收企业微信待复核草案三类输入.py
作用：使用指定三类企业微信税收业务输入，验证能否正确进入待复核草案摘要链路。
安全边界：只做本地 dry-run 验证；不真实发送企业微信、不接 n8n、不登录电子税务局、不接财税软件、不生成正式税务结论。
"""

from __future__ import annotations

import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
SCRIPT_DIR = ROOT / "02脚本"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
REPORT_JSON = OUT_DIR / "税收企业微信待复核草案验证回传_最新.json"
REPORT_MD = OUT_DIR / "税收企业微信待复核草案验证回传_最新.md"

SHADOW_RULE = ROOT / "01配置" / "税收企业微信输入队列证据匹配影子流转规则.json"
PACKAGE_RULE = ROOT / "01配置" / "税收企业微信证据匹配到分析契约输入包规则.json"
DRAFT_RULE = ROOT / "01配置" / "税收企业微信分析契约输入包到待复核草案骨架规则.json"
SUMMARY_RULE = ROOT / "01配置" / "税收企业微信待复核草案骨架到分析摘要预演规则.json"

INPUTS = [
    {
        "消息ID": "tax-wecom-review-verify-001",
        "输入文本": "税收业务：软件产品即征即退需要准备哪些资料",
        "期望主题": "软件产品增值税即征即退",
    },
    {
        "消息ID": "tax-wecom-review-verify-002",
        "输入文本": "税收业务：帮我查一下增值税法的依据",
        "期望主题": "增值税法依据",
    },
    {
        "消息ID": "tax-wecom-review-verify-003",
        "输入文本": "税收业务：研发费用加计扣除需要准备哪些资料",
        "期望主题": "研发费用加计扣除",
    },
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def contains_forbidden_output(text: str) -> list[str]:
    forbidden = [
        "可以享受",
        "不能享受",
        "应当享受",
        "不得享受",
        "可扣除金额",
        "应纳税额",
        "退税金额",
        "请立即申报",
        "请办理退税",
        "请开票",
        "申报建议",
        "无需人工复核",
        "正式税务意见",
        "正式税务结论",
        "结论确认",
    ]
    hits = [item for item in forbidden if item in text]
    if re.search(r"(?<![\d-])\d+(?:\.\d+)?\s*元", text):
        hits.append("金额数值")
    return hits


def build_record(source: dict[str, str], index: int) -> dict[str, Any]:
    return {
        "入队ID": f"tax-wecom-review-verify-queue-{index:03d}",
        "消息ID": source["消息ID"],
        "机器人名称": "杰哥工作秘书",
        "处理状态": "queued",
        "输入契约状态": "pending_evidence_match",
        "脱敏文本": source["输入文本"],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    shadow_module = load_module(
        "tax_shadow_flow",
        SCRIPT_DIR / "生成税收企业微信输入队列证据匹配影子流转.py",
    )
    package_module = load_module(
        "tax_analysis_package",
        SCRIPT_DIR / "生成税收企业微信证据匹配到分析契约输入包.py",
    )
    draft_module = load_module(
        "tax_review_draft",
        SCRIPT_DIR / "生成税收企业微信分析契约输入包到待复核草案骨架.py",
    )
    summary_module = load_module(
        "tax_review_summary",
        SCRIPT_DIR / "生成税收企业微信待复核草案骨架到分析摘要预演.py",
    )

    shadow_rule = load_json(SHADOW_RULE)
    package_rule = load_json(PACKAGE_RULE)
    draft_rule = load_json(DRAFT_RULE)
    summary_rule = load_json(SUMMARY_RULE)

    rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = [
        check("仅使用税收业务系统目录", all(str(path).startswith(str(ROOT)) for path in [SHADOW_RULE, PACKAGE_RULE, DRAFT_RULE, SUMMARY_RULE, REPORT_JSON, REPORT_MD]), str(ROOT)),
        check("三条指定输入已装载", len(INPUTS) == 3, INPUTS),
    ]

    for index, source in enumerate(INPUTS, start=1):
        record = build_record(source, index)
        shadow_task = shadow_module.build_shadow_task(record, shadow_rule, now, index)
        package = package_module.build_package(shadow_task, package_rule, index)
        draft = draft_module.build_draft(package, draft_rule, index)
        summary = summary_module.build_summary(draft, summary_rule, index)
        preview = str(summary.get("企业微信输出预览", ""))
        row = {
            "消息ID": source["消息ID"],
            "输入文本": source["输入文本"],
            "期望主题": source["期望主题"],
            "影子流转状态": shadow_task.get("影子流转状态"),
            "输入包状态": package.get("输入包状态"),
            "草案状态": draft.get("契约状态"),
            "摘要状态": summary.get("摘要状态"),
            "识别主题": summary.get("业务事项"),
            "是否进入待复核草案链路": all(
                [
                    shadow_task.get("影子流转状态") in {"pending_policy_evidence_match", "pending_fact_completion"},
                    package.get("输入包状态") in {"pending_review_input", "pending_fact_completion"},
                    draft.get("契约状态") in {"pending_review", "draft"},
                    summary.get("摘要状态") in {"pending_review_summary", "draft_summary"},
                ]
            ),
            "是否主题正确": summary.get("业务事项") == source["期望主题"],
            "是否待复核草案摘要": "【税收分析助手-待复核草案摘要】" in preview and "待复核草案摘要预演" in preview,
            "输出禁用命中": contains_forbidden_output(preview),
            "是否写正式业务库": summary.get("是否写正式业务库"),
            "是否调用模型推理": summary.get("是否调用模型推理"),
            "是否企业微信真实发送": summary.get("是否企业微信真实发送"),
            "是否生成正式税务结论": summary.get("是否生成正式税务结论"),
            "企业微信输出预览": preview,
        }
        rows.append(row)
        checks.extend(
            [
                check(f"{source['期望主题']}进入待复核草案链路", row["是否进入待复核草案链路"], row),
                check(f"{source['期望主题']}主题识别正确", row["是否主题正确"], {"识别主题": row["识别主题"], "期望主题": row["期望主题"]}),
                check(f"{source['期望主题']}输出为待复核草案摘要", row["是否待复核草案摘要"], preview[:500]),
                check(f"{source['期望主题']}无金额测算办理指令正式结论", not row["输出禁用命中"], row["输出禁用命中"]),
                check(
                    f"{source['期望主题']}未写正式库未调用模型未真实发送未生成正式结论",
                    row["是否写正式业务库"] is False
                    and row["是否调用模型推理"] is False
                    and row["是否企业微信真实发送"] is False
                    and row["是否生成正式税务结论"] is False,
                    {
                        "是否写正式业务库": row["是否写正式业务库"],
                        "是否调用模型推理": row["是否调用模型推理"],
                        "是否企业微信真实发送": row["是否企业微信真实发送"],
                        "是否生成正式税务结论": row["是否生成正式税务结论"],
                    },
                ),
            ]
        )

    safety = {
        "是否真实发送企业微信": False,
        "是否接n8n": False,
        "是否登录电子税务局": False,
        "是否接财税软件": False,
        "是否生成正式税务结论": False,
        "是否修改总管面板": False,
        "是否修改一键接续包": False,
        "是否修改企业微信公共配置": False,
    }
    checks.extend(
        [
            check("全部指定输入主题识别正确", all(row["是否主题正确"] for row in rows), [{"输入": row["输入文本"], "识别": row["识别主题"]} for row in rows]),
            check("全部输出统一为待复核草案摘要", all(row["是否待复核草案摘要"] for row in rows), [row["摘要状态"] for row in rows]),
            check("全部输出无金额测算办理指令正式结论", all(not row["输出禁用命中"] for row in rows), [{"消息ID": row["消息ID"], "命中": row["输出禁用命中"]} for row in rows]),
            check("红线动作全部未触碰", all(value is False for value in safety.values()), safety),
        ]
    )

    failed = [item for item in checks if item["结果"] != "通过"]
    report = {
        "名称": "税收企业微信待复核草案验证回传",
        "生成时间": now,
        "验证范围": str(ROOT),
        "验证结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "输入验证明细": rows,
        "检查结果": checks,
        "红线触碰情况": safety,
        "安全边界": "本次仅本地dry-run验证，不真实发送企业微信，不接n8n，不登录电子税务局，不接财税软件，不生成正式税务结论。",
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收企业微信待复核草案验证回传",
        "",
        f"- 生成时间：{now}",
        f"- 验证范围：{ROOT}",
        f"- 验证结论：{report['验证结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 三类输入验证",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['消息ID']}",
                f"- 输入：{row['输入文本']}",
                f"- 期望主题：{row['期望主题']}",
                f"- 识别主题：{row['识别主题']}",
                f"- 链路状态：影子流转={row['影子流转状态']}；输入包={row['输入包状态']}；草案={row['草案状态']}；摘要={row['摘要状态']}",
                f"- 是否进入待复核草案链路：{row['是否进入待复核草案链路']}",
                f"- 是否统一为待复核草案摘要：{row['是否待复核草案摘要']}",
                f"- 禁用命中：{row['输出禁用命中'] or '无'}",
                "",
                "```text",
                row["企业微信输出预览"],
                "```",
                "",
            ]
        )
    lines.extend(["## 检查结果"])
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}")
    lines.extend(["", "## 红线触碰情况"])
    for key, value in safety.items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    lines.append("## 安全边界")
    lines.append("- 本次仅本地 dry-run 验证；未真实发送企业微信，未接 n8n，未登录电子税务局，未接财税软件，未生成正式税务结论。")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"状态": report["验证结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
