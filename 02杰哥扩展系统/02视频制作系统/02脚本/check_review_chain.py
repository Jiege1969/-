# -*- coding: utf-8 -*-
"""
名称：check_review_chain.py
作用：只读检查轮次012人工复核链模板、样例和阻断声明是否齐备。
触发方式：python check_review_chain.py
安全边界：只读取本地文件并写入本地检查报告；不访问网络、不读取真实素材、不渲染、不发布、不发送企业微信、不连接 n8n。
所属系统：02杰哥扩展系统/02视频制作系统
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
DATA_ROOT = ROOT / "03数据" / "18轮次012视频工厂总控层"
REVIEW_ROOT = DATA_ROOT / "人工复核链"
TEMPLATE_DIR = REVIEW_ROOT / "复核模板"
EXAMPLE_DIR = REVIEW_ROOT / "占位填写样例"
OUTPUT_DIR = REVIEW_ROOT / "本地自检报告"
ARCHIVE_DIR = OUTPUT_DIR / "archive"


CHECK_FILES = [
    TEMPLATE_DIR / "素材授权字段模板_最新.md",
    TEMPLATE_DIR / "平台规则待确认模板_最新.md",
    EXAMPLE_DIR / "素材授权占位填写样例_最新.md",
    EXAMPLE_DIR / "平台规则占位填写样例_最新.md",
    REVIEW_ROOT / "人工复核回执" / "人工复核回执模板_最新.md",
    REVIEW_ROOT / "人工复核回执" / "人工复核回执填写说明_最新.md",
    REVIEW_ROOT / "人工复核回执" / "状态检查" / "人工复核回执状态检查_最新.md",
    REVIEW_ROOT / "人工复核回执" / "接收卡" / "人工复核回执填写后接收卡_最新.md",
    REVIEW_ROOT / "一致性检查" / "复核结果与放行清单一致性检查_最新.md",
    REVIEW_ROOT / "放行建议" / "生成放行建议单_最新.md",
]

REQUIRED_PATTERNS = [
    "真实系统触发：否",
    "阻断",
    "不读取真实素材",
    "不发送企业微信",
    "不接 n8n",
]

FORBIDDEN_PATTERNS = [
    "sub" + "process" + ".run(",
    "req" + "uests" + ".",
    "url" + "lib",
    "http" + ".client",
    "selen" + "ium",
    "play" + "wright",
    "post" + "bot",
    "Money" + "PrinterTurbo 命令已执行",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def inspect_file(path: Path) -> dict[str, Any]:
    text = read_text(path)
    missing = [pattern for pattern in REQUIRED_PATTERNS if pattern not in text]
    forbidden_hits = [pattern for pattern in FORBIDDEN_PATTERNS if pattern in text]
    return {
        "文件": str(path),
        "存在": path.exists(),
        "缺失必备声明": missing,
        "命中禁止模式": forbidden_hits,
        "通过": path.exists() and not missing and not forbidden_hits,
    }


def inspect_script(path: Path) -> dict[str, Any]:
    text = read_text(path)
    forbidden_hits = [pattern for pattern in FORBIDDEN_PATTERNS if pattern in text]
    return {
        "脚本": str(path),
        "存在": path.exists(),
        "命中禁止模式": forbidden_hits,
        "通过": path.exists() and not forbidden_hits,
    }


def build_report() -> dict[str, Any]:
    file_results = [inspect_file(path) for path in CHECK_FILES]
    script_results = [
        inspect_script(ROOT / "02脚本" / "generate_review_templates.py"),
        inspect_script(ROOT / "02脚本" / "generate_review_examples.py"),
        inspect_script(ROOT / "02脚本" / "generate_human_review_receipt.py"),
        inspect_script(ROOT / "02脚本" / "generate_human_review_receipt_guide.py"),
        inspect_script(ROOT / "02脚本" / "check_human_review_receipt_status.py"),
        inspect_script(ROOT / "02脚本" / "generate_human_review_receipt_intake_card.py"),
        inspect_script(ROOT / "02脚本" / "check_review_release_consistency.py"),
        inspect_script(ROOT / "02脚本" / "generate_generation_release_advice.py"),
        inspect_script(ROOT / "02脚本" / "check_review_chain.py"),
    ]
    all_results = file_results + script_results
    passed = all(item["通过"] for item in all_results)
    return {
        "检查时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查范围": "轮次012人工复核链模板与占位样例",
        "真实系统触发": False,
        "结论": "通过" if passed else "需人工处理",
        "文件检查": file_results,
        "脚本检查": script_results,
        "阻断登记": [
            "若任一模板缺失边界声明或阻断项，不得进入真实渲染",
            "若任一样例缺失AI标识、平台规则或素材授权待确认，不得进入发布放行",
            "若脚本命中网络、浏览器、发布或外部执行调用，必须暂停并交回总管判断",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 轮次012 人工复核链本地自检报告",
        "",
        f"- 检查时间：{report['检查时间']}",
        f"- 检查范围：{report['检查范围']}",
        f"- 真实系统触发：{report['真实系统触发']}",
        f"- 结论：{report['结论']}",
        "",
        "## 文件检查",
        "",
        "| 文件 | 存在 | 缺失必备声明 | 命中禁止模式 | 通过 |",
        "|---|---|---|---|---|",
    ]
    for item in report["文件检查"]:
        missing = "；".join(item["缺失必备声明"]) if item["缺失必备声明"] else "-"
        forbidden = "；".join(item["命中禁止模式"]) if item["命中禁止模式"] else "-"
        lines.append(f"| {item['文件']} | {item['存在']} | {missing} | {forbidden} | {item['通过']} |")
    lines.extend(
        [
            "",
            "## 脚本检查",
            "",
            "| 脚本 | 存在 | 命中禁止模式 | 通过 |",
            "|---|---|---|---|",
        ]
    )
    for item in report["脚本检查"]:
        forbidden = "；".join(item["命中禁止模式"]) if item["命中禁止模式"] else "-"
        lines.append(f"| {item['脚本']} | {item['存在']} | {forbidden} | {item['通过']} |")
    lines.extend(["", "## 阻断登记", ""])
    for item in report["阻断登记"]:
        lines.append(f"- [ ] {item}")
    lines.extend(
        [
            "",
            "## 边界声明",
            "",
            "- 本检查器只读本地影子文件并写本地报告。",
            "- 不读取真实素材、不访问平台、不连接真实账号、不发送企业微信、不接 n8n。",
            "- 检查通过不等于生成放行、渲染放行或发布放行。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = build_report()
    markdown = render_markdown(report)

    write_json(OUTPUT_DIR / "人工复核链本地自检报告_最新.json", report)
    write_text(OUTPUT_DIR / "人工复核链本地自检报告_最新.md", markdown)
    write_json(ARCHIVE_DIR / f"人工复核链本地自检报告_{stamp}.json", report)
    write_text(ARCHIVE_DIR / f"人工复核链本地自检报告_{stamp}.md", markdown)

    print(f"人工复核链本地自检完成：{report['结论']}，未触发真实系统")
    return 0 if report["结论"] == "通过" else 2


if __name__ == "__main__":
    raise SystemExit(main())
