# -*- coding: utf-8 -*-
"""
名称：生成施工接续卡片.py
作用：汇总当前施工面板、一键接续施工包和最新验收报告，生成给下一轮Codex施工使用的接续卡片。
触发方式：python 生成施工接续卡片.py
依赖：Python标准库；当前施工面板；一键接续施工包；最新验收报告。
所属系统：00杰哥系统总管
安全边界：只写00总管03数据/施工接续的最新卡片；不写时间戳流水；不删除文件；不写旧系统；不重启服务；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易。
标识：construction-handoff-card-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path, limit: int = 4000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")[-limit:]


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


def bool_from_acceptance(acceptance: dict[str, Any]) -> bool:
    if not acceptance:
        return False
    if acceptance.get("总体结论") in {"通过", "可继续施工", "已通过"}:
        return True
    if acceptance.get("结论") in {"通过", "可继续施工", "已通过"}:
        return True
    checks = acceptance.get("检查项")
    if isinstance(checks, list) and checks:
        return all(bool(item.get("通过")) for item in checks if isinstance(item, dict))
    return False


def build_card(root: Path) -> dict[str, Any]:
    manager = root / "00杰哥系统总管"
    panel_path = manager / "07文档" / "当前施工面板.md"
    package_path = manager / "03数据" / "开工上下文" / "一键接续施工包_最新.md"
    package_json_path = manager / "03数据" / "开工上下文" / "一键接续施工包_最新.json"
    context_path = manager / "03数据" / "开工上下文" / "开工上下文摘要_最新.md"
    acceptance_path = manager / "03数据" / "验收报告" / "验收报告_最新.md"
    acceptance_json_path = manager / "03数据" / "验收报告" / "验收报告_最新.json"
    round32_path = manager / "03数据" / "运行状态" / "摸清家底找差距第三十二轮开工上下文流水清债收口_最新.md"
    round33_path = manager / "03数据" / "运行状态" / "摸清家底找差距第三十三轮施工接续卡片流水清债收口_最新.md"
    debt_rule_path = manager / "03数据" / "运行状态" / "摸清家底找差距清债原则_最新.md"

    package_json = load_json(package_json_path)
    acceptance_json = load_json(acceptance_json_path)
    required_files = [
        panel_path,
        package_path,
        package_json_path,
        context_path,
        acceptance_path,
        acceptance_json_path,
    ]
    missing = [str(path) for path in required_files if not path.exists()]

    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "是否适合继续施工": not missing and bool_from_acceptance(acceptance_json),
        "当前所在步骤": "摸清家底找差距第33轮：施工接续卡片与施工接续校验日志清债收口",
        "统一口径": {
            "当前主线": "摸清家底找差距清债持续推进；能证实无当前依赖的旧项直接收口。",
            "样本原则": "股票分析系统作为底基和母样本，只吸收灰度门禁、交付验收、统一出口、回滚预案等有效逻辑，不继承时间戳流水和旧壳债务。",
            "接续规则": "下一轮先读当前施工面板、一键接续施工包、开工上下文摘要、最新验收报告和本卡片；历史工作日志只作追溯，不作当前入口。",
        },
        "下一步建议": [
            "继续复扫05备份和真实归档中的旧包旧壳，区分不可再生资产、可再生资产、中间产物。",
            "对已证实无依赖的旧时间戳流水和旧入口直接删除；需要保留的只保留当前索引、规则和母样本。",
            "把本轮形成的清债规则同步进总管面板、开工上下文和后续系统施工原则。",
        ],
        "安全边界": {
            "触发n8n": False,
            "企业微信真实发送": False,
            "写正式库": False,
            "券商接口": False,
            "自动交易": False,
            "删除未证实依赖项": False,
            "覆盖旧系统": False,
            "重启正式服务": False,
        },
        "关键文件": {
            "当前施工面板": str(panel_path),
            "一键接续施工包": str(package_path),
            "开工上下文摘要": str(context_path),
            "最新验收报告": str(acceptance_path),
            "第32轮开工上下文流水清债报告": str(round32_path),
            "第33轮施工接续卡片流水清债报告": str(round33_path),
            "清债原则": str(debt_rule_path),
            "施工接续卡片": str(manager / "03数据" / "施工接续" / "施工接续卡片_最新.md"),
        },
        "依赖状态": {
            "缺失必读文件": missing,
            "一键接续包检查项": package_json.get("检查项") or package_json.get("必读文件") or [],
            "最新验收结论": acceptance_json.get("总体结论") or acceptance_json.get("结论") or "",
        },
        "当前施工面板尾部": read_text(panel_path, 2500),
    }


def build_markdown(card: dict[str, Any]) -> str:
    lines = [
        "# 施工接续卡片",
        "",
        f"生成时间：{card['生成时间']}",
        "",
        "## 一、当前结论",
        "",
        f"- 是否适合继续施工：{card['是否适合继续施工']}",
        f"- 当前所在步骤：{card['当前所在步骤']}",
        "",
        "## 二、统一口径",
        "",
    ]
    for key, value in card["统一口径"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、下一步建议", ""])
    for item in card["下一步建议"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、必须保持关闭", ""])
    for key, value in card["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、关键文件", ""])
    for name, path in card["关键文件"].items():
        lines.append(f"- {name}：`{path}`")
    missing = card["依赖状态"]["缺失必读文件"]
    lines.extend(["", "## 六、依赖状态", ""])
    lines.append(f"- 缺失必读文件：{len(missing)}")
    for path in missing:
        lines.append(f"- 缺失：`{path}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    manager = root / "00杰哥系统总管"
    output_dir = manager / "03数据" / "施工接续"
    json_latest = output_dir / "施工接续卡片_最新.json"
    md_latest = output_dir / "施工接续卡片_最新.md"
    card = build_card(root)
    write_json(json_latest, card)
    write_text(md_latest, build_markdown(card))
    print(json.dumps({"是否适合继续施工": card["是否适合继续施工"], "输出": str(json_latest), "卡片": str(md_latest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
