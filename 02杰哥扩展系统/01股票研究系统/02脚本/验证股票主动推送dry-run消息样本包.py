# -*- coding: utf-8 -*-
"""
验证“249股票主动推送dry-run消息样本包”。

本脚本会先运行生成脚本，再检查本地样本包的安全边界。
不会调用企业微信 API，不会真实发送，不会启用或触发 n8n，
不会连接券商，不会执行任何交易动作。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "02脚本"
RULE_PATH = ROOT / "03数据" / "248主动推送白名单频率熔断规则包" / "股票主动推送白名单频率熔断规则包_最新.json"
PACKAGE_DIR = ROOT / "03数据" / "249主动推送dry-run消息样本包"
LOG_DIR = ROOT / "04日志" / "主动推送dry-run消息样本包"
GENERATOR = SCRIPT_DIR / "生成股票主动推送dry-run消息样本包.py"
LATEST_JSON = PACKAGE_DIR / "股票主动推送dry-run消息样本包_最新.json"
LATEST_MD = PACKAGE_DIR / "股票主动推送dry-run消息样本包_最新.md"

FORBIDDEN_WORDS = [
    "买入",
    "卖出",
    "加仓",
    "减仓",
    "满仓",
    "清仓",
    "仓位",
    "下单",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any = "") -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail}


def forbidden_words_from_rule(rule: dict[str, Any]) -> list[str]:
    words = list(FORBIDDEN_WORDS)
    boundary = rule.get("内容边界")
    if isinstance(boundary, dict):
        from_rule = boundary.get("禁止表达")
        if isinstance(from_rule, list):
            words.extend(str(item) for item in from_rule)
    return sorted({word for word in words if word})


def collect_message_texts(package: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    samples = package.get("samples", [])
    if not isinstance(samples, list):
        return texts
    for sample in samples:
        if isinstance(sample, dict):
            text = sample.get("message_text")
            if isinstance(text, str):
                texts.append(text)
    return texts


def all_false(package: dict[str, Any], key: str) -> bool:
    if package.get(key) is not False:
        return False
    samples = package.get("samples", [])
    if not isinstance(samples, list):
        return False
    return all(isinstance(sample, dict) and sample.get(key) is False for sample in samples)


def all_true(package: dict[str, Any], key: str) -> bool:
    if package.get(key) is not True:
        return False
    samples = package.get("samples", [])
    if not isinstance(samples, list):
        return False
    return all(isinstance(sample, dict) and sample.get(key) is True for sample in samples)


def dangerous_actions_closed(package: dict[str, Any]) -> tuple[bool, list[str]]:
    actions = package.get("actual_actions", {})
    if not isinstance(actions, dict):
        return False, ["actual_actions缺失"]
    dangerous_keys = [
        "enterprise_wechat_api",
        "real_send",
        "enable_n8n",
        "trigger_n8n",
        "reload_19310",
        "reload_19302",
        "broker_connection",
        "trade_action",
        "tax_login",
        "write_formal_rules",
        "modify_admin_panel",
        "modify_one_click_continuation_package",
    ]
    open_items = [key for key in dangerous_keys if actions.get(key) is not False]
    return not open_items, open_items


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送dry-run消息样本包验收",
        "",
        f"- 验收时间：{result['verified_at']}",
        f"- 总体状态：{result['status']}",
        f"- 通过：{result['passed']}",
        f"- 失败：{result['failed']}",
        f"- 样本数量：{result['sample_count']}",
        f"- 最新JSON：{result['latest_json']}",
        f"- 最新Markdown：{result['latest_md']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in result["checks"]:
        lines.append(f"- {item['check']}：{item['passed']}；{item['detail']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    completed = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    rule = load_json(RULE_PATH)
    package = load_json(LATEST_JSON)
    samples = package.get("samples", [])
    sample_count = len(samples) if isinstance(samples, list) else 0
    message_texts = collect_message_texts(package)
    forbidden_words = forbidden_words_from_rule(rule)
    hits = sorted(
        {
            word
            for word in forbidden_words
            for text in message_texts
            if word and word in text
        }
    )
    actions_closed, open_actions = dangerous_actions_closed(package)

    checks = [
        check(
            "生成脚本成功运行",
            completed.returncode == 0,
            {"returncode": completed.returncode, "stderr": completed.stderr.strip()},
        ),
        check("规则包存在", RULE_PATH.exists(), str(RULE_PATH)),
        check("输出JSON最新文件存在", LATEST_JSON.exists(), str(LATEST_JSON)),
        check("输出Markdown最新文件存在", LATEST_MD.exists(), str(LATEST_MD)),
        check("dry_run=true", all_true(package, "dry_run"), package.get("dry_run")),
        check("真实发送=false", all_false(package, "真实发送"), package.get("真实发送")),
        check("n8n=false", all_false(package, "n8n"), package.get("n8n")),
        check("券商=false", all_false(package, "券商"), package.get("券商")),
        check("交易=false", all_false(package, "交易"), package.get("交易")),
        check("禁止词未命中", not hits, hits),
        check("样本数量>=1", sample_count >= 1, sample_count),
        check("危险动作全部关闭", actions_closed, open_actions),
    ]
    failed_checks = [item for item in checks if not item["passed"]]

    result = {
        "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pass" if not failed_checks else "blocked",
        "passed": len(checks) - len(failed_checks),
        "failed": len(failed_checks),
        "sample_count": sample_count,
        "latest_json": str(LATEST_JSON),
        "latest_md": str(LATEST_MD),
        "generator_stdout": completed.stdout.strip(),
        "checks": checks,
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

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = LOG_DIR / f"股票主动推送dry-run消息样本包验收_{stamp}.json"
    latest_log_json = LOG_DIR / "股票主动推送dry-run消息样本包验收_最新.json"
    output_md = LOG_DIR / f"股票主动推送dry-run消息样本包验收_{stamp}.md"
    latest_log_md = LOG_DIR / "股票主动推送dry-run消息样本包验收_最新.md"

    write_json(output_json, result)
    write_json(latest_log_json, result)
    markdown = build_markdown(result)
    write_text(output_md, markdown)
    write_text(latest_log_md, markdown)

    print(
        json.dumps(
            {
                "status": result["status"],
                "passed": result["passed"],
                "failed": result["failed"],
                "sample_count": sample_count,
                "latest_log_json": str(latest_log_json),
            },
            ensure_ascii=False,
        )
    )
    return 0 if not failed_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
