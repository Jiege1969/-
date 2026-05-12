# -*- coding: utf-8 -*-
"""
名称：税收企业微信工作秘书入口适配器.py
作用：按单条企业微信税收输入，动态走待复核草案摘要链路，返回工作秘书可读的 dry-run 摘要。
安全边界：只调用税收业务系统内部构建函数；不真实发送企业微信、不接n8n、不登录电子税务局、不接财税软件、不写正式业务库、不生成正式税务结论。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
SCRIPT_DIR = ROOT / "02脚本"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信工作秘书入口适配器_最新.json"
OUT_MD = OUT_DIR / "税收企业微信工作秘书入口适配器_最新.md"

SHADOW_RULE = ROOT / "01配置" / "税收企业微信输入队列证据匹配影子流转规则.json"
PACKAGE_RULE = ROOT / "01配置" / "税收企业微信证据匹配到分析契约输入包规则.json"
DRAFT_RULE = ROOT / "01配置" / "税收企业微信分析契约输入包到待复核草案骨架规则.json"
SUMMARY_RULE = ROOT / "01配置" / "税收企业微信待复核草案骨架到分析摘要预演规则.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载税收内部脚本：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_record(message: str, message_id: str) -> dict[str, Any]:
    return {
        "入队ID": f"{message_id}-queue",
        "消息ID": message_id,
        "机器人名称": "杰哥工作秘书",
        "处理状态": "queued",
        "输入契约状态": "pending_evidence_match",
        "脱敏文本": message,
    }


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 税收企业微信工作秘书入口适配器",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 输入：{result['输入']}",
        f"- 识别主题：{result['识别主题']}",
        f"- 适配状态：{result['状态']}",
        f"- 真实发送企业微信：{result['安全边界']['真实发送企业微信']}",
        f"- 触发n8n：{result['安全边界']['触发n8n']}",
        "",
        "## 回复预览",
        "",
        "```text",
        result["reply_text"],
        "```",
        "",
    ]
    return "\n".join(lines)


def adapt_message(message: str, message_id: str = "tax-wecom-work-secretary-single") -> dict[str, Any]:
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

    record = build_record(message, message_id)
    shadow_task = shadow_module.build_shadow_task(record, load_json(SHADOW_RULE), now, 1)
    package = package_module.build_package(shadow_task, load_json(PACKAGE_RULE), 1)
    draft = draft_module.build_draft(package, load_json(DRAFT_RULE), 1)
    summary = summary_module.build_summary(draft, load_json(SUMMARY_RULE), 1)
    reply_text = str(summary.get("企业微信输出预览") or "").strip()
    if not reply_text:
        reply_text = "【税收分析助手-待复核草案摘要】\n当前输入未生成可读摘要，请补充业务事项、所属期间、主体和资料线索。"

    result = {
        "生成时间": now,
        "名称": "税收企业微信工作秘书入口适配器",
        "状态": "完成",
        "输入": message,
        "消息ID": message_id,
        "路由": "税收业务待复核草案摘要",
        "识别主题": summary.get("业务事项"),
        "影子流转状态": shadow_task.get("影子流转状态"),
        "输入包状态": package.get("输入包状态"),
        "草案状态": draft.get("契约状态"),
        "摘要状态": summary.get("摘要状态"),
        "回复": reply_text,
        "reply_text": reply_text,
        "summary": summary,
        "安全边界": {
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "写正式业务库": False,
            "调用模型推理": False,
            "生成正式税务结论": False,
        },
        "公共接入层接入状态": {
            "是否已修改企业微信公共配置": False,
            "接入建议": "需总管确认后，将工作秘书税收本地调用从静态摘要首条读取改为调用本适配器。",
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(build_markdown(result), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="税收企业微信工作秘书入口适配器")
    parser.add_argument("message", nargs="*", help="税收业务输入文本")
    parser.add_argument("--message-id", default="tax-wecom-work-secretary-single")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    message = " ".join(args.message).strip()
    if not message:
        message = "税收业务：请补充要分析的涉税事项、所属期间和已有资料。"
    result = adapt_message(message, args.message_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
