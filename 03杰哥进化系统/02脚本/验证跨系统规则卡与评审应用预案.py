# -*- coding: utf-8 -*-
"""
名称：验证跨系统规则卡与评审应用预案.py
作用：重新生成并验证本轮小任务 D 的规则卡、评审样本、阻断项和真实动作禁用边界。
安全边界：只运行 03 本地生成与验证；不触发 n8n、不发送企业微信、不调用券商接口、不自动交易、不写正式库。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PACKAGE_NAME = "跨系统规则卡与评审应用预案"


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return system_root().parents[0]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def build_verify_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 跨系统规则卡与评审应用预案验收报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 验收结论：{report['验收结论']}",
        f"- 通过项：{report['汇总']['通过']}",
        f"- 失败项：{report['汇总']['失败']}",
        f"- 阻断项数量：{report['阻断项数量']}",
        "",
        "## 检查项",
        "",
    ]
    for check in report["检查项"]:
        mark = "通过" if check["通过"] else "失败"
        lines.append(f"- {mark}：{check['名称']}")
    lines.extend(
        [
            "",
            "## 安全边界",
            "",
            "- 自动交易禁用。",
            "- 券商接口未调用。",
            "- n8n 未触发。",
            "- 企业微信真实发送未触发。",
            "- 正式库未写入。",
            "- 外部发布未执行。",
            "",
        ]
    )
    return "\n".join(lines)


def refresh_recovery_report(recovery_path: Path, verify_report: dict[str, Any]) -> None:
    text = recovery_path.read_text(encoding="utf-8-sig") if recovery_path.exists() else "# 03进化系统_本轮小任务D回收报告_最新\n"
    marker = "## 验证脚本结果"
    base = text.split(marker)[0].rstrip()
    lines = [
        base,
        "",
        marker,
        "",
        f"- 验证时间：{verify_report['生成时间']}",
        f"- 验收结论：{verify_report['验收结论']}",
        f"- 通过项：{verify_report['汇总']['通过']}",
        f"- 失败项：{verify_report['汇总']['失败']}",
        f"- 阻断项数量：{verify_report['阻断项数量']}",
        f"- 验收 JSON：{verify_report['验收JSON']}",
        f"- 验收 Markdown：{verify_report['验收Markdown']}",
        "",
    ]
    write_text(recovery_path, "\n".join(lines))


def main() -> int:
    root = system_root()
    generator = root / "02脚本" / "生成跨系统规则卡与评审应用预案.py"
    data_dir = root / "03数据" / "23跨系统规则卡与评审应用预案"
    latest_json = data_dir / f"{PACKAGE_NAME}_最新.json"
    latest_md = data_dir / f"{PACKAGE_NAME}_最新.md"
    doc_path = root / "07文档" / "跨系统规则卡正式接入口径_最新.md"
    recovery_path = repo_root() / "00杰哥系统总管" / "03数据" / "并行回收" / "03进化系统_本轮小任务D回收报告_最新.md"

    result = subprocess.run(
        [sys.executable, str(generator)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )

    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码为 0", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "规则卡 JSON 存在", latest_json.exists(), str(latest_json))
    add_check(checks, "规则卡 Markdown 存在", latest_md.exists(), str(latest_md))
    add_check(checks, "正式接入口径文档存在", doc_path.exists(), str(doc_path))
    add_check(checks, "固定回收报告存在", recovery_path.exists(), str(recovery_path))

    payload = load_json(latest_json) if latest_json.exists() else {}
    cards = payload.get("规则卡", [])
    samples = payload.get("跨系统评审小样本", [])
    blockers = [item for sample in samples for item in sample.get("阻断项", [])]
    safety = payload.get("安全边界", {})
    card_names = [card.get("规则名", "") for card in cards]
    systems = {sample.get("系统") for sample in samples}
    high_risk_cards = [card for card in cards if card.get("风险等级") in {"高", "极高"}]

    add_check(checks, "规则卡数量不少于 4", len(cards) >= 4, len(cards))
    add_check(checks, "评审样本数量为 3-5 个", 3 <= len(samples) <= 5, len(samples))
    add_check(checks, "覆盖 5 类跨系统样本", {"股票", "企业微信助手", "知识库", "内容处理/视频", "总管派工"}.issubset(systems), sorted(systems))
    add_check(checks, "包含股票交付闭环规则", any("股票交付闭环" in name for name in card_names), card_names)
    add_check(checks, "包含股票自动交易硬闸门规则", any("股票自动交易硬闸门" in name for name in card_names), card_names)
    add_check(checks, "包含并行施工容量规则", any("并行施工容量" in name for name in card_names), card_names)
    add_check(checks, "包含影子灰度真实动作边界规则", any("影子" in name and "真实动作" in name for name in card_names), card_names)
    add_check(checks, "高风险规则均有阻断条件", all(card.get("阻断条件") for card in high_risk_cards), high_risk_cards)
    add_check(checks, "阻断项数量不少于 5", len(blockers) >= 5, blockers)
    add_check(checks, "高风险样本存在阻断", any(sample.get("评审结果") == "阻断" and sample.get("阻断项") for sample in samples), samples)
    add_check(checks, "自动交易禁用", safety.get("自动交易启用") is False, safety)
    add_check(checks, "券商接口未调用", safety.get("券商接口调用") is False, safety)
    add_check(checks, "n8n 未触发", safety.get("n8n触发") is False, safety)
    add_check(checks, "企业微信真实发送未触发", safety.get("企业微信真实发送") is False, safety)
    add_check(checks, "正式库未写入", safety.get("正式库写入") is False, safety)
    add_check(checks, "外部发布未执行", safety.get("外部发布") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report: dict[str, Any] = {
        "生成时间": now_text(),
        "任务": "03杰哥进化系统规则固化与跨系统评审应用预案验收",
        "验收结论": "通过" if failed == 0 else "失败",
        "汇总": {"通过": passed, "失败": failed},
        "规则卡数量": len(cards),
        "评审样本数量": len(samples),
        "阻断项数量": len(blockers),
        "检查项": checks,
        "验收对象": str(latest_json),
        "安全边界": safety,
    }

    tag = stamp()
    version_json = data_dir / f"{PACKAGE_NAME}_验收_{tag}.json"
    version_md = data_dir / f"{PACKAGE_NAME}_验收_{tag}.md"
    latest_verify_json = data_dir / f"{PACKAGE_NAME}_验收_最新.json"
    latest_verify_md = data_dir / f"{PACKAGE_NAME}_验收_最新.md"
    verify_report["验收JSON"] = str(latest_verify_json)
    verify_report["验收Markdown"] = str(latest_verify_md)

    write_json(version_json, verify_report)
    write_json(latest_verify_json, verify_report)
    markdown = build_verify_markdown(verify_report)
    write_text(version_md, markdown)
    write_text(latest_verify_md, markdown)
    refresh_recovery_report(recovery_path, verify_report)

    print(json.dumps({"验收结论": verify_report["验收结论"], "通过": passed, "失败": failed, "阻断项数量": len(blockers)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
