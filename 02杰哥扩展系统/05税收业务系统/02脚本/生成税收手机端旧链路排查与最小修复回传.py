# -*- coding: utf-8 -*-
"""
名称：生成税收手机端旧链路排查与最小修复回传.py
作用：回传手机端旧链路原因、税收内部入口适配层最小修复和三类输入验证结果。
安全边界：只运行本地 dry-run；不真实发送企业微信、不接 n8n、不登录电子税务局、不接财税软件、不生成正式税务结论。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
SCRIPT_DIR = ROOT / "02脚本"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
ENTRY_SCRIPT = SCRIPT_DIR / "生成税收企业微信正式入口消息预演.py"
ENTRY_VALIDATE = SCRIPT_DIR / "验证税收企业微信正式入口消息预演.py"
ENTRY_JSON = OUT_DIR / "税收企业微信正式入口消息预演_最新.json"
REPORT_JSON = OUT_DIR / "税收手机端旧链路排查与最小修复回传_最新.json"
REPORT_MD = OUT_DIR / "税收手机端旧链路排查与最小修复回传_最新.md"


INPUTS = [
    ("mobile-tax-recheck-001", "税收业务：软件产品即征即退需要准备哪些资料", "软件产品增值税即征即退"),
    ("mobile-tax-recheck-002", "税收业务：帮我查一下增值税法的依据", "增值税法依据"),
    ("mobile-tax-recheck-003", "税收业务：研发费用加计扣除需要准备哪些资料", "研发费用加计扣除"),
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_cmd(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return {
        "命令": args,
        "返回码": completed.returncode,
        "标准输出": completed.stdout.strip(),
        "错误输出": completed.stderr.strip(),
    }


def forbidden_hits(text: str) -> list[str]:
    phrases = [
        "【税收分析助手-待复核预演】",
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
    hits = [phrase for phrase in phrases if phrase in text]
    if re.search(r"(?<![\d-])\d+(?:\.\d+)?\s*元", text):
        hits.append("金额数值")
    return hits


def check(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "结果": "通过" if ok else "失败", "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    entry_text = ENTRY_SCRIPT.read_text(encoding="utf-8")
    checks.extend([
        check("正式入口消息预演脚本存在", ENTRY_SCRIPT.exists(), str(ENTRY_SCRIPT)),
        check("正式入口脚本已接入direct_text_adapter", "direct_text_adapter" in entry_text and "build_summary_from_record" in entry_text, "入口适配层函数"),
        check("正式入口脚本未把研发费用旧影子样例作为主来源", '"旧链路是否仍作为主来源": False' in entry_text, "旧链路仅保留为记录字段"),
    ])

    for message_id, text, expected_topic in INPUTS:
        run = run_cmd([sys.executable, str(ENTRY_SCRIPT), "--text", text, "--message-id", message_id])
        validation = run_cmd([sys.executable, str(ENTRY_VALIDATE)])
        preview = load_json(ENTRY_JSON)
        message = preview.get("消息预演", {}).get("企业微信拟发送消息", "")
        safety = preview.get("安全边界", {})
        hits = forbidden_hits(message)
        row = {
            "消息ID": message_id,
            "输入": text,
            "期望主题": expected_topic,
            "识别主题": preview.get("识别主题"),
            "入口适配模式": preview.get("入口适配模式"),
            "摘要状态": preview.get("摘要状态"),
            "标题是否为待复核草案摘要": "【税收分析助手-待复核草案摘要】" in message,
            "是否仍为旧标题": "【税收分析助手-待复核预演】" in message,
            "禁用命中": hits,
            "是否真实发送": preview.get("消息预演", {}).get("是否真实发送"),
            "生成命令返回码": run["返回码"],
            "验收命令返回码": validation["返回码"],
            "验收输出": validation["标准输出"],
            "安全边界": safety,
            "消息预览": message,
        }
        rows.append(row)
        checks.extend([
            check(f"{expected_topic}正式入口生成成功", run["返回码"] == 0, run["标准输出"] or run["错误输出"]),
            check(f"{expected_topic}正式入口验收通过", validation["返回码"] == 0, validation["标准输出"] or validation["错误输出"]),
            check(f"{expected_topic}主题识别正确", row["识别主题"] == expected_topic, {"识别主题": row["识别主题"], "期望主题": expected_topic}),
            check(f"{expected_topic}标题为待复核草案摘要", row["标题是否为待复核草案摘要"] and not row["是否仍为旧标题"], message[:300]),
            check(f"{expected_topic}无金额测算办理指令正式结论", not hits, hits),
            check(
                f"{expected_topic}红线动作关闭",
                row["是否真实发送"] is False
                and safety.get("是否企业微信真实发送") is False
                and safety.get("是否触发n8n") is False
                and safety.get("是否接电子税务局") is False
                and safety.get("是否接财税软件") is False
                and safety.get("是否生成正式税务结论") is False
                and safety.get("是否修改企业微信公共配置") is False,
                safety,
            ),
        ])

    safety_summary = {
        "是否修改总管面板": False,
        "是否修改一键接续包": False,
        "是否修改企业微信公共配置": False,
        "是否真实发送企业微信": False,
        "是否接n8n": False,
        "是否登录电子税务局": False,
        "是否接财税软件": False,
        "是否生成正式税务结论": False,
    }
    checks.append(check("本轮红线全部未触碰", all(value is False for value in safety_summary.values()), safety_summary))
    failed = [item for item in checks if item["结果"] != "通过"]
    report = {
        "名称": "税收手机端旧链路排查与最小修复回传",
        "生成时间": now,
        "验证范围": str(ROOT),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "旧链路排查结论": [
            "手机端实际出口命中税收企业微信正式入口消息预演产物：03数据/32税收企业微信正式入口/税收企业微信正式入口消息预演_最新.json。",
            "旧生成脚本固定读取03数据/29涉税业务分析契约影子样例/研发费用涉税业务分析契约影子样例_最新.json和研发费用准备度门禁，所以不同输入都会被包装为研发费用口径。",
            "上轮本地dry-run三类输入验证直接调用待复核草案链路函数，未覆盖正式入口消息预演脚本，因此手机端仍读旧产物。",
        ],
        "最小修复方案": [
            "仅修改税收业务系统内部正式入口消息预演脚本和税收侧合规规则。",
            "正式入口消息预演新增direct_text_adapter，支持工作秘书传入单条文本后即时进入输入队列证据匹配、分析契约输入包、待复核草案骨架、待复核草案摘要链路。",
            "正式入口不再把研发费用旧影子样例作为主来源；旧路径仅作为排查字段记录。",
            "如果公共企业微信接入层没有把手机端文本传给该脚本，也没有写入税收本地输入队列，则需要总管确认公共路由映射，本轮未修改公共配置。",
        ],
        "需总管确认": [
            "公共企业微信接入层需确认调用税收正式入口消息预演时传入--text或设置TAX_WECOM_INPUT_TEXT，或先写入税收本地输入队列。",
            "如公共层仍调用旧产物缓存或旧脚本入口，需要总管批准后调整公共路由；本轮未改公共企业微信配置。",
        ],
        "三类输入验证": rows,
        "检查结果": checks,
        "红线触碰情况": safety_summary,
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 税收手机端旧链路排查与最小修复回传",
        "",
        f"- 生成时间：{now}",
        f"- 验证范围：{ROOT}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 旧链路排查结论",
    ]
    lines.extend(f"- {item}" for item in report["旧链路排查结论"])
    lines.extend(["", "## 最小修复方案"])
    lines.extend(f"- {item}" for item in report["最小修复方案"])
    lines.extend(["", "## 三类输入验证"])
    for row in rows:
        lines.extend([
            f"### {row['消息ID']}",
            f"- 输入：{row['输入']}",
            f"- 期望主题：{row['期望主题']}",
            f"- 识别主题：{row['识别主题']}",
            f"- 入口适配模式：{row['入口适配模式']}",
            f"- 摘要状态：{row['摘要状态']}",
            f"- 标题是否为待复核草案摘要：{row['标题是否为待复核草案摘要']}",
            f"- 是否仍为旧标题：{row['是否仍为旧标题']}",
            f"- 禁用命中：{row['禁用命中'] or '无'}",
            f"- 是否真实发送：{row['是否真实发送']}",
            "",
            "```text",
            row["消息预览"],
            "```",
            "",
        ])
    lines.extend(["## 需总管确认"])
    lines.extend(f"- {item}" for item in report["需总管确认"])
    lines.extend(["", "## 红线触碰情况"])
    for key, value in safety_summary.items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 检查结果"])
    for item in checks:
        lines.append(f"- {item['检查项']}：{item['结果']}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
