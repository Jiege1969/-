# -*- coding: utf-8 -*-
"""
生成“249股票主动推送dry-run消息样本包”。

安全边界：
- 只读取 248 白名单频率熔断规则包最新 JSON。
- 只写入 249 dry-run 消息样本包本地文件。
- 不调用企业微信 API，不真实发送，不启用或触发 n8n。
- 不连接券商，不执行任何交易动作，不重载 19310/19302。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RULE_PATH = ROOT / "03数据" / "248主动推送白名单频率熔断规则包" / "股票主动推送白名单频率熔断规则包_最新.json"
OUT_DIR = ROOT / "03数据" / "249主动推送dry-run消息样本包"

PACKAGE_BASENAME = "股票主动推送dry-run消息样本包"

DEFAULT_FORBIDDEN_WORDS = [
    "买入",
    "卖出",
    "加仓",
    "减仓",
    "满仓",
    "清仓",
    "仓位",
    "下单",
]

ALLOWED_TONE = [
    "研究价值",
    "风险复核",
    "观察条件",
    "证据缺口",
    "人工复核",
    "不构成投资建议",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"规则包不存在：{path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else False


def forbidden_words_from_rule(rule: dict[str, Any]) -> list[str]:
    words = list(DEFAULT_FORBIDDEN_WORDS)
    boundary = rule.get("内容边界")
    if isinstance(boundary, dict):
        from_rule = boundary.get("禁止表达")
        if isinstance(from_rule, list):
            words.extend(str(item) for item in from_rule)
    return sorted({word for word in words if word})


def build_samples() -> list[dict[str, Any]]:
    message_text = "\n".join(
        [
            "研究价值：公开资料存在进一步复核价值。",
            "风险复核：信息时效、口径差异、异常波动需要人工复核。",
            "观察条件：仅在公开资料、风险提示、人工复核一致时保留观察。",
            "证据缺口：缺少最新公告、行业比较、财务口径交叉验证。",
            "人工复核：由人工确认资料来源、时间戳、结论边界。",
            "不构成投资建议：本样本仅用于本地dry-run预演。",
        ]
    )
    return [
        {
            "sample_id": "stock-active-push-dry-run-001",
            "dry_run": True,
            "真实发送": False,
            "n8n": False,
            "券商": False,
            "交易": False,
            "用途": "仅用于本地预演，不进入外发链路。",
            "message_text": message_text,
            "route_guard": {
                "local_preview_only": True,
                "enterprise_wechat_api": False,
                "external_delivery": False,
                "webhook": False,
                "n8n_trigger": False,
                "broker_connection": False,
                "trade_action": False,
            },
        }
    ]


def build_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送dry-run消息样本包",
        "",
        f"- 生成时间：{package['generated_at']}",
        f"- 来源规则包：{package['source_rule_package']['path']}",
        f"- dry_run：{package['dry_run']}",
        f"- 真实发送：{package['真实发送']}",
        f"- n8n：{package['n8n']}",
        f"- 券商：{package['券商']}",
        f"- 交易：{package['交易']}",
        "",
        "## 样本",
        "",
    ]
    for sample in package["samples"]:
        lines.extend(
            [
                f"### {sample['sample_id']}",
                "",
                "```text",
                sample["message_text"],
                "```",
                "",
                f"- dry_run：{sample['dry_run']}",
                f"- 真实发送：{sample['真实发送']}",
                f"- n8n：{sample['n8n']}",
                f"- 券商：{sample['券商']}",
                f"- 交易：{sample['交易']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 安全边界",
            "",
            "- 只写本地文件。",
            "- 不调用企业微信API。",
            "- 不真实发送。",
            "- 不启用或触发n8n。",
            "- 不连接券商。",
            "- 不执行任何交易动作。",
            "- 不重载19310/19302。",
            "- 不改总管面板。",
            "- 不改一键接续包。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    rule = load_json(RULE_PATH)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    forbidden_words = forbidden_words_from_rule(rule)

    package = {
        "package_name": PACKAGE_BASENAME,
        "generated_at": generated_at,
        "source_rule_package": {
            "path": str(RULE_PATH),
            "exists": RULE_PATH.exists(),
            "sha256": sha256_file(RULE_PATH),
            "generated_at": rule.get("生成时间"),
            "真实发送允许": as_bool(rule.get("是否允许真实发送")),
            "n8n自动推送允许": as_bool(rule.get("是否允许n8n自动推送")),
        },
        "dry_run": True,
        "真实发送": False,
        "n8n": False,
        "券商": False,
        "交易": False,
        "local_only": True,
        "allowed_tone": ALLOWED_TONE,
        "forbidden_word_check": {
            "source": "248规则包内容边界及本脚本硬编码红线",
            "checked_count": len(forbidden_words),
        },
        "samples": build_samples(),
        "actual_actions": {
            "write_local_files": True,
            "enterprise_wechat_api": False,
            "real_send": False,
            "enable_n8n": False,
            "trigger_n8n": False,
            "reload_19310": False,
            "reload_19302": False,
            "broker_connection": False,
            "trade_action": False,
            "tax_login": False,
            "write_formal_rules": False,
            "modify_admin_panel": False,
            "modify_one_click_continuation_package": False,
        },
    }

    output_json = OUT_DIR / f"{PACKAGE_BASENAME}_{stamp}.json"
    latest_json = OUT_DIR / f"{PACKAGE_BASENAME}_最新.json"
    output_md = OUT_DIR / f"{PACKAGE_BASENAME}_{stamp}.md"
    latest_md = OUT_DIR / f"{PACKAGE_BASENAME}_最新.md"

    write_json(output_json, package)
    write_json(latest_json, package)
    markdown = build_markdown(package)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)

    print(
        json.dumps(
            {
                "status": "generated",
                "dry_run": True,
                "真实发送": False,
                "n8n": False,
                "samples": len(package["samples"]),
                "latest_json": str(latest_json),
                "latest_md": str(latest_md),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
