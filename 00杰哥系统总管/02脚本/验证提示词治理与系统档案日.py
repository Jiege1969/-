# -*- coding: utf-8 -*-
"""
名称：验证提示词治理与系统档案日.py
作用：只读核查提示词版本化治理和系统档案日月度注记是否具备可执行、可回滚、可验收入口。
触发方式：python 验证提示词治理与系统档案日.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只读核查并写验收报告；不修改运行源提示词；不触发n8n；不发送企业微信；不调用券商接口；不创建日历或自动化。
创建/修改记录：2026-05-06 创建提示词治理与系统档案日验收入口。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
INTEL = ROOT / "01杰哥智能系统"
EVOLUTION = ROOT / "03杰哥进化系统"

PROMPT_LIBRARY = INTEL / "提示词库"
PROMPT_GOV = EVOLUTION / "02提示词管理"
PROMPT_INDEX_JSON = PROMPT_GOV / "03数据" / "台账" / "提示词版本索引_最新.json"
PROMPT_INDEX_MD = PROMPT_GOV / "03数据" / "台账" / "提示词版本索引_最新.md"
PROMPT_CHANGELOG = PROMPT_GOV / "07文档" / "提示词变更日志.md"
PROMPT_RULE_MD = PROMPT_GOV / "07文档" / "提示词修改规则.md"
PROMPT_RULE_JSON = PROMPT_GOV / "01配置" / "提示词修改规则.json"

ARCHIVE_DIR = EVOLUTION / "月度档案"
ARCHIVE_RULE = EVOLUTION / "03数据" / "34系统档案日" / "系统档案日规则_最新.md"
ARCHIVE_TEMPLATE = ARCHIVE_DIR / "系统档案日月度注记模板_最新.md"
CURRENT_MONTH_NOTE = ARCHIVE_DIR / f"{datetime.now():%Y-%m}系统档案日注记.md"

OUT_DIR = MANAGER / "03数据" / "运行状态"
LOG_DIR = MANAGER / "04日志" / "制度化治理"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def text_contains(path: Path, words: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return all(word in text for word in words)


def validate_prompt_governance() -> dict[str, Any]:
    failures: list[str] = []
    assets: list[dict[str, Any]] = []
    index = read_json(PROMPT_INDEX_JSON) if PROMPT_INDEX_JSON.exists() else {}
    indexed_assets = index.get("assets", [])

    required_files = [
        PROMPT_LIBRARY / "README.md",
        PROMPT_INDEX_JSON,
        PROMPT_INDEX_MD,
        PROMPT_CHANGELOG,
        PROMPT_RULE_MD,
        PROMPT_RULE_JSON,
    ]
    for path in required_files:
        if not path.exists():
            failures.append(f"缺少提示词治理文件：{path}")

    for item in indexed_assets:
        name = str(item.get("名称", "未命名"))
        source = Path(str(item.get("运行源", "")))
        version_file = Path(str(item.get("版本文件", "")))
        version = str(item.get("当前版本", ""))
        registered_sha = str(item.get("SHA256", "")).upper()
        rollback = str(item.get("回滚方式", ""))
        asset_failures: list[str] = []

        if not source.exists():
            asset_failures.append("运行源不存在")
        if not version_file.exists():
            asset_failures.append("版本文件不存在")
        if not re.fullmatch(r"v\d+\.\d+", version):
            asset_failures.append("版本号格式异常")
        if not re.fullmatch(r"[0-9A-F]{64}", registered_sha):
            asset_failures.append("SHA256登记异常")
        if "回滚" not in rollback and "恢复" not in rollback:
            asset_failures.append("缺少回滚口径")
        actual_sha = sha256(version_file) if version_file.exists() else ""
        if actual_sha and registered_sha and actual_sha != registered_sha:
            asset_failures.append("版本文件SHA256与索引不一致")

        if asset_failures:
            failures.append(f"{name}：" + "；".join(asset_failures))
        assets.append({
            "名称": name,
            "类型": item.get("类型", ""),
            "优先级": item.get("优先级", ""),
            "当前版本": version,
            "运行源存在": source.exists(),
            "版本文件存在": version_file.exists(),
            "SHA256一致": bool(actual_sha and registered_sha and actual_sha == registered_sha),
            "问题": asset_failures,
        })

    if not indexed_assets:
        failures.append("提示词版本索引没有资产条目")

    rule_ok = text_contains(PROMPT_RULE_MD, ["提示词是软代码", "变更日志", "回滚"])
    changelog_ok = text_contains(PROMPT_CHANGELOG, ["v1.0", "回滚"])
    library_ok = text_contains(PROMPT_LIBRARY / "README.md", ["当前版本索引", "清债规则"])
    if not rule_ok:
        failures.append("提示词修改规则缺少软代码/变更日志/回滚要点")
    if not changelog_ok:
        failures.append("提示词变更日志缺少基线版本或回滚说明")
    if not library_ok:
        failures.append("提示词库README缺少索引或清债规则")

    return {
        "名称": "提示词版本化治理验收",
        "资产数量": len(indexed_assets),
        "通过资产数量": sum(1 for item in assets if not item["问题"]),
        "失败资产数量": sum(1 for item in assets if item["问题"]),
        "规则文件通过": rule_ok,
        "变更日志通过": changelog_ok,
        "提示词库入口通过": library_ok,
        "资产明细": assets,
        "失败": failures,
    }


def validate_archive_day() -> dict[str, Any]:
    failures: list[str] = []
    required = {
        "系统档案日规则": ARCHIVE_RULE,
        "月度注记模板": ARCHIVE_TEMPLATE,
        "当月注记": CURRENT_MONTH_NOTE,
    }
    for name, path in required.items():
        if not path.exists():
            failures.append(f"缺少{name}：{path}")

    rule_ok = text_contains(ARCHIVE_RULE, ["每月一次", "最多 1 小时", "不创建日历事件"])
    template_ok = text_contains(ARCHIVE_TEMPLATE, ["结论摘要", "下月方向"])
    note_ok = text_contains(CURRENT_MONTH_NOTE, ["结论摘要", "本月规则沉淀", "下月方向"])
    note_text = CURRENT_MONTH_NOTE.read_text(encoding="utf-8", errors="replace") if CURRENT_MONTH_NOTE.exists() else ""
    directions = re.findall(r"^\d+\.\s+", note_text, flags=re.M)

    if not rule_ok:
        failures.append("系统档案日规则缺少频率、时长或不创建自动化边界")
    if not template_ok:
        failures.append("月度注记模板缺少结论摘要或下月方向")
    if not note_ok:
        failures.append("当月注记缺少结论摘要、本月规则沉淀或下月方向")
    if len(directions) > 3:
        failures.append("当月注记下月方向超过3条")

    return {
        "名称": "系统档案日验收",
        "规则存在": ARCHIVE_RULE.exists(),
        "模板存在": ARCHIVE_TEMPLATE.exists(),
        "当月注记存在": CURRENT_MONTH_NOTE.exists(),
        "规则通过": rule_ok,
        "模板通过": template_ok,
        "当月注记通过": note_ok,
        "下月方向数量": len(directions),
        "失败": failures,
    }


def write_reports(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    json_latest = OUT_DIR / "提示词治理与系统档案日验收_最新.json"
    md_latest = OUT_DIR / "提示词治理与系统档案日验收_最新.md"
    log_latest = LOG_DIR / "prompt-governance-archive-day-verify-最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    json_latest.write_text(text, encoding="utf-8")
    log_latest.write_text(text, encoding="utf-8")

    prompt = report["提示词治理"]
    archive = report["系统档案日"]
    lines = [
        "# 提示词治理与系统档案日验收",
        "",
        f"- 验收时间：{report['验收时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 提示词资产：{prompt['通过资产数量']}/{prompt['资产数量']} 通过",
        f"- 系统档案日：{'通过' if not archive['失败'] else '未通过'}",
        "",
        "## 提示词治理",
        f"- 版本索引：`{PROMPT_INDEX_JSON}`",
        f"- 变更日志：`{PROMPT_CHANGELOG}`",
        f"- 修改规则：`{PROMPT_RULE_MD}`",
        f"- 失败资产数量：{prompt['失败资产数量']}",
        "",
        "## 系统档案日",
        f"- 规则：`{ARCHIVE_RULE}`",
        f"- 模板：`{ARCHIVE_TEMPLATE}`",
        f"- 当月注记：`{CURRENT_MONTH_NOTE}`",
        f"- 下月方向数量：{archive['下月方向数量']}",
        "",
        "## 失败项",
    ]
    failures = prompt["失败"] + archive["失败"]
    if failures:
        lines.extend([f"- {item}" for item in failures])
    else:
        lines.append("- 无。")
    lines.extend([
        "",
        "## 安全边界",
        "- 未修改运行源提示词；未触发 n8n；未发送企业微信；未调用券商接口；未自动交易；未创建日历或自动化。",
    ])
    md_latest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    prompt = validate_prompt_governance()
    archive = validate_archive_day()
    failures = prompt["失败"] + archive["失败"]
    report = {
        "名称": "提示词治理与系统档案日验收",
        "验收时间": now_text(),
        "提示词治理": prompt,
        "系统档案日": archive,
        "当前结论": "通过" if not failures else "未通过",
        "失败数量": len(failures),
        "安全边界": {
            "未修改运行源提示词": True,
            "未触发n8n": True,
            "未发送企业微信": True,
            "未调用券商接口": True,
            "未自动交易": True,
            "未创建日历或自动化": True,
        },
    }
    write_reports(report)
    print(json.dumps({
        "状态": report["当前结论"],
        "提示词资产": f"{prompt['通过资产数量']}/{prompt['资产数量']}",
        "系统档案日": "通过" if not archive["失败"] else "未通过",
        "失败数量": report["失败数量"],
        "输出": str(OUT_DIR / "提示词治理与系统档案日验收_最新.md"),
    }, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
