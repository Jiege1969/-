# -*- coding: utf-8 -*-
"""生成三日巡检第2天待执行链路与防伪检查包。

本脚本只读取 59 包与 69 包，生成第2天待执行链路说明和防伪检查清单。
它不生成第2/3自然日样本，不触发任何外部系统，不修改服务或正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
DATA_ROOT = EVOLUTION_ROOT / "03数据"

PACKAGE_59_DIR = DATA_ROOT / "59稳定候选补强与三日巡检启动包"
PACKAGE_59_LEDGER = PACKAGE_59_DIR / "三日只读巡检样本台账_最新.json"

PACKAGE_69_DIR = DATA_ROOT / "69三日巡检样本防伪与次日待执行卡包"
PACKAGE_69_JSON = PACKAGE_69_DIR / "三日巡检样本防伪与次日待执行卡包_最新.json"
PACKAGE_69_CARD_JSON = PACKAGE_69_DIR / "次日待执行卡_最新.json"
PACKAGE_69_RULES_JSON = PACKAGE_69_DIR / "样本防伪规则_最新.json"
PACKAGE_69_READONLY_JSON = PACKAGE_69_DIR / "只读核对结果_最新.json"

OUTPUT_DIR = DATA_ROOT / "73三日巡检第2天待执行链路与防伪检查包"
PACKAGE_JSON = OUTPUT_DIR / "三日巡检第2天待执行链路与防伪检查包_最新.json"
PACKAGE_MD = OUTPUT_DIR / "三日巡检第2天待执行链路与防伪检查包_最新.md"
CHAIN_JSON = OUTPUT_DIR / "第2天待执行链路说明_最新.json"
CHAIN_MD = OUTPUT_DIR / "第2天待执行链路说明_最新.md"
CHECKLIST_JSON = OUTPUT_DIR / "第2天防伪检查清单_最新.json"
CHECKLIST_MD = OUTPUT_DIR / "第2天防伪检查清单_最新.md"

EXPECTED_FIRST_DAY = "2026-05-08"
EXPECTED_DAY2_LOWER_BOUND = "2026-05-09"


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "触发n8n": False,
    "接券商或交易": False,
    "登录税局或接财税软件": False,
    "真实渲染或发布视频": False,
    "转正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "修改生成日常可用版自主巡检快照.py": False,
    "修改服务配置": False,
    "重载19310": False,
    "重载19302": False,
    "预生成第2自然日样本": False,
    "预生成第3自然日样本": False,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sample_dates_from_ledger(ledger: dict[str, Any]) -> list[str]:
    samples = ledger.get("自然日样本", [])
    return sorted({item.get("样本日期") for item in samples if item.get("样本日期")})


def assert_source_state(
    ledger_59: dict[str, Any],
    package_69: dict[str, Any],
    card_69: dict[str, Any],
    rules_69: dict[str, Any],
    readonly_69: dict[str, Any],
) -> None:
    errors: list[str] = []
    dates = sample_dates_from_ledger(ledger_59)
    source_69 = package_69.get("来源确认", {})

    if dates != [EXPECTED_FIRST_DAY]:
        errors.append(f"59包台账必须仅有首日样本 {EXPECTED_FIRST_DAY}，当前={dates}")
    if ledger_59.get("三日达标") is not False:
        errors.append("59包台账三日达标必须为 false")
    if source_69.get("自然日样本日期") != [EXPECTED_FIRST_DAY]:
        errors.append("69包来源确认必须仅有首日样本 2026-05-08")
    if source_69.get("三日达标") is not False:
        errors.append("69包来源确认三日达标必须为 false")
    if package_69.get("当前允许三日达标") is not False:
        errors.append("69包当前允许三日达标必须为 false")
    if card_69.get("待执行日期下限") != EXPECTED_DAY2_LOWER_BOUND:
        errors.append("69包次日待执行日期下限必须为 2026-05-09")
    if card_69.get("来源首日样本日期") != EXPECTED_FIRST_DAY:
        errors.append("69包次日卡来源首日样本日期必须为 2026-05-08")
    if card_69.get("样本生成状态") != "未生成，仅待执行":
        errors.append("69包次日卡必须保持未生成样本状态")
    if readonly_69.get("通过") is not True or readonly_69.get("错误数") != 0:
        errors.append("69包只读核对结果必须通过且错误数为 0")
    if not any("不能提前生成占位样本" in item for item in rules_69.get("规则", [])):
        errors.append("69包防伪规则必须声明不能提前生成第2/3自然日占位样本")

    if errors:
        raise SystemExit("拒绝生成：\n" + "\n".join(f"- {item}" for item in errors))


def build_chain(generated_at: str) -> dict[str, Any]:
    return {
        "名称": "三日巡检第2天待执行链路说明",
        "生成时间": generated_at,
        "链路状态": "pending-only",
        "来源首日样本日期": EXPECTED_FIRST_DAY,
        "待执行自然日序号": 2,
        "待执行日期下限": EXPECTED_DAY2_LOWER_BOUND,
        "链路步骤": [
            "到达真实自然日后，先只读读取 59 包台账与 69 包防伪规则。",
            "确认 59 包仍只有 2026-05-08 一个自然日样本，且三日达标=false。",
            "确认执行日期必须大于首日样本日期，且不早于 2026-05-09。",
            "确认目标目录中不存在第2/3自然日未来样本文件。",
            "只读核对通过后，才允许后续真实执行流程在真实日期写入第2自然日样本。",
        ],
        "本包输出性质": "只生成待执行链路说明与防伪检查清单，不生成第2天样本。",
        "不得执行": list(SAFETY_BOUNDARY.keys()),
    }


def build_checklist(generated_at: str, dates: list[str]) -> dict[str, Any]:
    return {
        "名称": "三日巡检第2天防伪检查清单",
        "生成时间": generated_at,
        "检查项": [
            {
                "项目": "当前只有首日样本",
                "要求": [EXPECTED_FIRST_DAY],
                "当前": dates,
                "通过": dates == [EXPECTED_FIRST_DAY],
            },
            {
                "项目": "三日达标保持false",
                "要求": False,
                "说明": "只有1个自然日样本时不得置为true。",
            },
            {
                "项目": "次日待执行日期下限",
                "要求": EXPECTED_DAY2_LOWER_BOUND,
                "说明": "第2天真实样本日期必须大于首日样本日期。",
            },
            {
                "项目": "同日重复运行不得增加自然日计数",
                "要求": "同日只能覆盖同日样本，不能新增自然日计数。",
            },
            {
                "项目": "未来样本禁生成",
                "要求": "本包不得出现第2/3自然日真实样本记录文件。",
            },
            {
                "项目": "外部系统与服务禁触发",
                "要求": "不发企业微信、不触发n8n、不接交易/税务/视频发布、不重载服务。",
            },
        ],
        "安全边界": SAFETY_BOUNDARY,
    }


def build_package_md(package: dict[str, Any]) -> str:
    outputs = [f"- {name}: {path}" for name, path in package["输出文件"].items()]
    return "\n".join(
        [
            "# 三日巡检第2天待执行链路与防伪检查包",
            "",
            f"- 生成时间: {package['生成时间']}",
            f"- 状态: {package['状态']}",
            f"- 首日样本日期: {package['来源确认']['首日样本日期']}",
            f"- 自然日样本日期: {', '.join(package['来源确认']['自然日样本日期'])}",
            f"- 三日达标: {package['来源确认']['三日达标']}",
            f"- 第2天待执行日期下限: {package['第2天待执行链路说明']['待执行日期下限']}",
            f"- 第2天样本生成状态: {package['样本生成声明']['第2自然日样本']}",
            "",
            "## 链路步骤",
            "",
            *[f"- {item}" for item in package["第2天待执行链路说明"]["链路步骤"]],
            "",
            "## 输出文件",
            "",
            *outputs,
        ]
    )


def build_chain_md(chain: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 三日巡检第2天待执行链路说明",
            "",
            f"- 来源首日样本日期: {chain['来源首日样本日期']}",
            f"- 待执行自然日序号: {chain['待执行自然日序号']}",
            f"- 待执行日期下限: {chain['待执行日期下限']}",
            f"- 本包输出性质: {chain['本包输出性质']}",
            "",
            "## 链路步骤",
            "",
            *[f"- {item}" for item in chain["链路步骤"]],
        ]
    )


def build_checklist_md(checklist: dict[str, Any]) -> str:
    lines = ["# 三日巡检第2天防伪检查清单", ""]
    for item in checklist["检查项"]:
        lines.append(f"- {item['项目']}: {item.get('要求', item.get('说明', ''))}")
    return "\n".join(lines)


def main() -> int:
    ledger_59 = read_json(PACKAGE_59_LEDGER)
    package_69 = read_json(PACKAGE_69_JSON)
    card_69 = read_json(PACKAGE_69_CARD_JSON)
    rules_69 = read_json(PACKAGE_69_RULES_JSON)
    readonly_69 = read_json(PACKAGE_69_READONLY_JSON)

    assert_source_state(ledger_59, package_69, card_69, rules_69, readonly_69)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dates = sample_dates_from_ledger(ledger_59)
    chain = build_chain(generated_at)
    checklist = build_checklist(generated_at, dates)
    package = {
        "名称": "三日巡检第2天待执行链路与防伪检查包",
        "生成时间": generated_at,
        "状态": "ready",
        "来源文件": {
            "59包台账": str(PACKAGE_59_LEDGER),
            "69总包": str(PACKAGE_69_JSON),
            "69次日待执行卡": str(PACKAGE_69_CARD_JSON),
            "69防伪规则": str(PACKAGE_69_RULES_JSON),
            "69只读核对结果": str(PACKAGE_69_READONLY_JSON),
        },
        "来源确认": {
            "自然日样本数": len(dates),
            "自然日样本日期": dates,
            "首日样本日期": EXPECTED_FIRST_DAY,
            "三日达标": False,
            "69包只读核对错误数": readonly_69.get("错误数"),
            "确认当前只有首日样本": dates == [EXPECTED_FIRST_DAY],
            "确认次日待执行日期下限": card_69.get("待执行日期下限"),
        },
        "第2天待执行链路说明": chain,
        "第2天防伪检查清单": checklist,
        "安全边界": SAFETY_BOUNDARY,
        "样本生成声明": {
            "第2自然日样本": "未生成，仅待真实日期到达后由后续真实执行流程处理",
            "第3自然日样本": "未生成",
        },
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "链路说明JSON": str(CHAIN_JSON),
            "链路说明Markdown": str(CHAIN_MD),
            "防伪检查清单JSON": str(CHECKLIST_JSON),
            "防伪检查清单Markdown": str(CHECKLIST_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_package_md(package))
    write_json(CHAIN_JSON, chain)
    write_text(CHAIN_MD, build_chain_md(chain))
    write_json(CHECKLIST_JSON, checklist)
    write_text(CHECKLIST_MD, build_checklist_md(checklist))

    print(json.dumps({"通过": True, "错误数": 0, "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
