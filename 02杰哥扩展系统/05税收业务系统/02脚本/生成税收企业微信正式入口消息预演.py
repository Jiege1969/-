# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信正式入口消息预演.py
作用：把杰哥工作秘书税收输入适配到待复核草案摘要链路，生成企业微信入口消息预演。
安全边界：只生成本地预演消息；不读取凭据、不联网、不真实发送、不生成正式税务结论。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
SCRIPT_DIR = ROOT / "02脚本"
CONFIG = ROOT / "01配置" / "税收企业微信正式入口配置.json"
SHADOW_RULE = ROOT / "01配置" / "税收企业微信输入队列证据匹配影子流转规则.json"
PACKAGE_RULE = ROOT / "01配置" / "税收企业微信证据匹配到分析契约输入包规则.json"
DRAFT_RULE = ROOT / "01配置" / "税收企业微信分析契约输入包到待复核草案骨架规则.json"
SUMMARY_RULE = ROOT / "01配置" / "税收企业微信待复核草案骨架到分析摘要预演规则.json"
QUEUE_PREVIEW = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信本地输入队列预演_最新.json"
SUMMARY_PREVIEW = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信待复核草案骨架到分析摘要预演_最新.json"
LEGACY_SHADOW = ROOT / "03数据" / "29涉税业务分析契约影子样例" / "研发费用涉税业务分析契约影子样例_最新.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
ADAPTER_DIR = OUT_DIR / "工作秘书入口适配"
OUT_JSON = OUT_DIR / "税收企业微信正式入口消息预演_最新.json"
OUT_MD = OUT_DIR / "税收企业微信正式入口消息预演_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载税收内部脚本：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mask_sensitive(text: str) -> str:
    patterns = [
        (r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=[A-Za-z0-9_-]+", "[企业微信Webhook已脱敏]"),
        (r"\b[0-9A-Z]{15,20}\b", "[纳税人识别号或编号已脱敏]"),
        (r"\b1[3-9]\d{9}\b", "[手机号已脱敏]"),
        (r"\b\d{17}[\dXx]\b", "[身份证号已脱敏]"),
        (r"\b\d{12,19}\b", "[银行账号或长编号已脱敏]"),
    ]
    masked = text
    for pattern, repl in patterns:
        masked = re.sub(pattern, repl, masked)
    return masked


def newest_queued_record(queue: dict[str, Any]) -> dict[str, Any]:
    rows = [
        row for row in queue.get("队列记录", [])
        if row.get("处理状态") == "queued" and row.get("输入契约状态") in {"pending_evidence_match", "normalized"}
    ]
    return rows[-1] if rows else {}


def record_from_text(text: str, message_id: str, now: str) -> dict[str, Any]:
    return {
        "入队ID": f"tax-wecom-entry-adapter-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "消息ID": message_id,
        "入队时间": now,
        "机器人名称": "杰哥工作秘书",
        "提问人标识": "work_secretary_user_masked",
        "消息类型": "text",
        "脱敏文本": mask_sensitive(text),
        "附件元数据": [],
        "分流结果": "涉税问题",
        "处理状态": "queued",
        "拒收原因": "",
        "输入契约状态": "pending_evidence_match",
        "审计编号": f"tax-wecom-entry-adapter-audit-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "来源通道": "企业微信/杰哥工作秘书/税收内部入口适配层",
    }


def incoming_record(args: argparse.Namespace, now: str) -> tuple[dict[str, Any], str, list[str]]:
    notes: list[str] = []
    text = (args.text or os.environ.get("TAX_WECOM_INPUT_TEXT", "")).strip()
    if text:
        notes.append("命令行或环境变量提供了工作秘书输入文本，已直接进入税收内部待复核草案摘要链路。")
        return record_from_text(text, args.message_id, now), "direct_text_adapter", notes

    queue = load_json(QUEUE_PREVIEW, {})
    record = newest_queued_record(queue)
    if record:
        notes.append("未收到直接文本，改读税收本地输入队列最新 queued 记录。")
        return record, "local_queue_latest", notes

    notes.append("未发现直接文本或本地输入队列记录，需总管确认公共接入层是否把手机端输入写入税收本地队列。")
    return {}, "missing_input", notes


def build_summary_from_record(record: dict[str, Any], now: str) -> dict[str, Any]:
    shadow_module = load_module("tax_shadow_flow", SCRIPT_DIR / "生成税收企业微信输入队列证据匹配影子流转.py")
    package_module = load_module("tax_analysis_package", SCRIPT_DIR / "生成税收企业微信证据匹配到分析契约输入包.py")
    draft_module = load_module("tax_review_draft", SCRIPT_DIR / "生成税收企业微信分析契约输入包到待复核草案骨架.py")
    summary_module = load_module("tax_review_summary", SCRIPT_DIR / "生成税收企业微信待复核草案骨架到分析摘要预演.py")

    shadow = shadow_module.build_shadow_task(record, load_json(SHADOW_RULE), now, 1)
    package = package_module.build_package(shadow, load_json(PACKAGE_RULE), 1)
    draft = draft_module.build_draft(package, load_json(DRAFT_RULE), 1)
    summary = summary_module.build_summary(draft, load_json(SUMMARY_RULE), 1)
    return {
        "影子任务": shadow,
        "输入包": package,
        "草案骨架": draft,
        "摘要": summary,
    }


def fallback_summary() -> tuple[dict[str, Any], str]:
    latest = load_json(SUMMARY_PREVIEW, {})
    rows = latest.get("摘要预演", [])
    if rows:
        return rows[-1], "latest_review_summary_artifact"
    return {}, "missing_review_summary"


def build_message(config: dict[str, Any], summary: dict[str, Any], source_mode: str) -> dict[str, Any]:
    max_len = int(config.get("消息格式", {}).get("最大字符数", 1800))
    message = str(summary.get("企业微信输出预览", "")).strip()
    if not message:
        message = "【税收分析助手-待复核草案摘要】\n事项：待识别\n状态：missing_input\n边界：待复核草案摘要预演，不作为申报、退税、开票或办税执行依据。"
    message = mask_sensitive(message)
    if len(message) > max_len:
        message = message[: max_len - 18].rstrip() + "\n...[已截断]"
    return {
        "消息类型": config.get("消息格式", {}).get("默认类型", "markdown"),
        "企业微信拟发送消息": message,
        "字符数": len(message),
        "是否脱敏处理": True,
        "是否真实发送": False,
        "发送模式": "dry_run",
        "入口适配模式": source_mode,
        "真实发送阻断原因": [
            "配置入口状态不是real_send_enabled。",
            "真实发送放行不是true。",
            "当前未读取或校验企业微信凭据。",
        ],
    }


def build_markdown(report: dict[str, Any]) -> str:
    message = report["消息预演"]["企业微信拟发送消息"]
    lines = [
        "# 税收企业微信正式入口消息预演",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 入口状态：{report['入口状态']}",
        f"- 入口适配模式：{report['入口适配模式']}",
        f"- 识别主题：{report.get('识别主题', '')}",
        f"- 发送模式：{report['消息预演']['发送模式']}",
        f"- 是否真实发送：{report['消息预演']['是否真实发送']}",
        "",
        "## 拟发送消息",
        "",
        "```text",
        message,
        "```",
        "",
        "## 适配说明",
        "",
    ]
    for note in report.get("适配说明", []):
        lines.append(f"- {note}")
    lines.extend(["", "## 真实发送阻断原因", ""])
    for reason in report["消息预演"].get("真实发送阻断原因", []):
        lines.append(f"- {reason}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="税收企业微信正式入口消息预演")
    parser.add_argument("--text", default="", help="杰哥工作秘书转入税收系统的单条输入文本")
    parser.add_argument("--message-id", default="tax-wecom-entry-adapter-input", help="输入消息ID")
    return parser.parse_args()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
    args = parse_args()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    config = load_json(CONFIG)
    record, source_mode, notes = incoming_record(args, now)
    chain: dict[str, Any] = {}
    summary: dict[str, Any] = {}
    artifact_source = ""

    if record:
        chain = build_summary_from_record(record, now)
        summary = chain.get("摘要", {})
        artifact_source = "税收内部入口适配层即时生成"
        write_json(ADAPTER_DIR / "税收企业微信工作秘书入口适配链路_最新.json", {
            "名称": "税收企业微信工作秘书入口适配链路",
            "生成时间": now,
            "输入记录": record,
            **chain,
            "安全边界": {
                "是否真实发送企业微信": False,
                "是否接n8n": False,
                "是否登录电子税务局": False,
                "是否接财税软件": False,
                "是否生成正式税务结论": False,
            },
        })
    else:
        summary, source_mode = fallback_summary()
        artifact_source = str(SUMMARY_PREVIEW if summary else LEGACY_SHADOW)
        if summary:
            notes.append("已降级读取最新待复核草案摘要产物；未使用研发费用旧影子样例。")

    message = build_message(config, summary, source_mode)
    report = {
        "名称": "税收企业微信正式入口消息预演",
        "生成时间": now,
        "配置来源": str(CONFIG),
        "分析草案来源": artifact_source,
        "旧链路来源": str(LEGACY_SHADOW),
        "旧链路是否仍作为主来源": False,
        "入口适配模式": source_mode,
        "适配说明": notes,
        "输入记录": record,
        "识别主题": summary.get("业务事项", ""),
        "摘要状态": summary.get("摘要状态", ""),
        "入口状态": config.get("入口状态", "dry_run_only"),
        "真实发送放行": config.get("真实发送放行", False),
        "消息预演": message,
        "安全边界": {
            "是否联网": False,
            "是否下载": False,
            "是否读取凭据": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
            "是否触发n8n": False,
            "是否写向量库": False,
            "是否企业微信真实发送": False,
            "是否生成正式税务结论": False,
            "是否修改总管面板": False,
            "是否修改一键接续包": False,
            "是否修改企业微信公共配置": False,
        },
    }
    write_json(OUT_JSON, report)
    write_text(OUT_MD, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "入口适配模式": source_mode,
        "识别主题": report["识别主题"],
        "发送模式": message["发送模式"],
        "是否真实发送": message["是否真实发送"],
        "输出": str(OUT_MD),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
