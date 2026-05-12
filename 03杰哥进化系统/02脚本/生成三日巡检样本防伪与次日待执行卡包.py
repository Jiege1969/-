# -*- coding: utf-8 -*-
"""生成三日巡检样本防伪与次日待执行卡包。

本脚本只读取 59 包三日只读巡检样本台账，生成防伪规则与次日待执行卡。
它不会预生成第 2/3 自然日样本，也不会触发任何外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SOURCE_DIR = EVOLUTION_ROOT / "03数据" / "59稳定候选补强与三日巡检启动包"
SOURCE_LEDGER = SOURCE_DIR / "三日只读巡检样本台账_最新.json"

OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "69三日巡检样本防伪与次日待执行卡包"
PACKAGE_JSON = OUTPUT_DIR / "三日巡检样本防伪与次日待执行卡包_最新.json"
PACKAGE_MD = OUTPUT_DIR / "三日巡检样本防伪与次日待执行卡包_最新.md"
NEXTDAY_CARD_JSON = OUTPUT_DIR / "次日待执行卡_最新.json"
NEXTDAY_CARD_MD = OUTPUT_DIR / "次日待执行卡_最新.md"
ANTI_FAKE_RULES_JSON = OUTPUT_DIR / "样本防伪规则_最新.json"
ANTI_FAKE_RULES_MD = OUTPUT_DIR / "样本防伪规则_最新.md"

EXPECTED_FIRST_DAY = "2026-05-08"


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "触发n8n": False,
    "接券商或交易": False,
    "登录税局或接财税软件": False,
    "真实渲染或发布视频": False,
    "转正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "修改服务配置": False,
    "重载19310": False,
    "重载19302": False,
    "预生成第2自然日样本": False,
    "预生成第3自然日样本": False,
}


ANTI_FAKE_RULES = [
    "自然日计数只按样本日期去重，同一天重复运行只能覆盖当日样本，不增加自然日计数。",
    "当前首日样本日期为 2026-05-08；第2自然日样本日期必须大于当前首日日期。",
    "第2/3自然日必须在真实日期到达后由只读核对结果写入，不能提前生成占位样本。",
    "三日达标只能在 3 个不同自然日样本均为 pass 后置为 true；当前只有首日样本时必须保持 false。",
    "任一安全边界项出现 true、任一巡检源失败、或出现服务重载/外部触发痕迹时，三日达标保持 false。",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_day(day_text: str) -> datetime:
    return datetime.strptime(day_text, "%Y-%m-%d")


def source_status(ledger: dict[str, Any]) -> dict[str, Any]:
    samples = ledger.get("自然日样本", [])
    dates = sorted({item.get("样本日期") for item in samples if item.get("样本日期")})
    return {
        "来源台账": str(SOURCE_LEDGER),
        "来源台账存在": SOURCE_LEDGER.exists(),
        "自然日样本数": len(dates),
        "自然日样本日期": dates,
        "首日样本日期": dates[0] if dates else None,
        "三日达标": ledger.get("三日达标"),
        "确认当前仅首日样本": dates == [EXPECTED_FIRST_DAY],
        "确认三日达标为false": ledger.get("三日达标") is False,
    }


def build_nextday_card(status: dict[str, Any], generated_at: str) -> dict[str, Any]:
    first_day = status["首日样本日期"]
    next_day = (parse_day(first_day) + timedelta(days=1)).strftime("%Y-%m-%d")
    return {
        "名称": "次日待执行卡",
        "生成时间": generated_at,
        "来源首日样本日期": first_day,
        "待执行自然日序号": 2,
        "待执行日期下限": next_day,
        "必须满足": [
            f"实际执行日期必须大于首日样本日期 {first_day}",
            "执行时重新读取 59 包台账，若仍是同一天，只允许覆盖当日样本，不增加自然日计数",
            "只读核对通过后才允许由后续真实执行流程写入第2自然日样本",
            "本卡不是样本，不计入三日达标",
        ],
        "禁止事项": [
            "不得预生成第2自然日样本",
            "不得预生成第3自然日样本",
            "不得修改总管面板、一键接续包、服务配置或正式规则",
            "不得触发企业微信、n8n、券商、税局、财税软件、视频渲染或发布",
        ],
        "建议输出名": {
            "第2自然日真实样本JSON": "三日巡检第2自然日样本记录_yyyy-mm-dd_真实执行.json",
            "第2自然日真实样本Markdown": "三日巡检第2自然日样本记录_yyyy-mm-dd_真实执行.md",
        },
        "样本生成状态": "未生成，仅待执行",
    }


def build_rules_doc(rules: list[str]) -> dict[str, Any]:
    return {
        "名称": "样本防伪规则",
        "规则": rules,
        "判定口径": {
            "重复运行": "按样本日期去重，同一天只能覆盖同日样本",
            "第2天日期": "必须大于当前首日日期",
            "未来样本": "包内不得出现第2/3自然日真实样本记录",
            "当前达标": "当前仅 2026-05-08 一个自然日样本，三日达标必须为 false",
        },
    }


def build_md(package: dict[str, Any]) -> str:
    outputs = [f"- {name}: {path}" for name, path in package["输出文件"].items()]
    return "\n".join(
        [
            "# 三日巡检样本防伪与次日待执行卡包",
            "",
            f"- 生成时间: {package['生成时间']}",
            f"- 来源自然日样本数: {package['来源确认']['自然日样本数']}",
            f"- 来源自然日样本日期: {', '.join(package['来源确认']['自然日样本日期'])}",
            f"- 来源三日达标: {package['来源确认']['三日达标']}",
            f"- 当前允许三日达标: {package['当前允许三日达标']}",
            "",
            "## 防伪规则",
            "",
            *[f"- {item}" for item in package["样本防伪规则"]["规则"]],
            "",
            "## 次日卡",
            "",
            f"- 待执行自然日序号: {package['次日待执行卡']['待执行自然日序号']}",
            f"- 待执行日期下限: {package['次日待执行卡']['待执行日期下限']}",
            f"- 样本生成状态: {package['次日待执行卡']['样本生成状态']}",
            "",
            "## 输出文件",
            "",
            *outputs,
        ]
    )


def build_card_md(card: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 次日待执行卡",
            "",
            f"- 来源首日样本日期: {card['来源首日样本日期']}",
            f"- 待执行自然日序号: {card['待执行自然日序号']}",
            f"- 待执行日期下限: {card['待执行日期下限']}",
            f"- 样本生成状态: {card['样本生成状态']}",
            "",
            "## 必须满足",
            "",
            *[f"- {item}" for item in card["必须满足"]],
            "",
            "## 禁止事项",
            "",
            *[f"- {item}" for item in card["禁止事项"]],
        ]
    )


def build_rules_md(rules_doc: dict[str, Any]) -> str:
    return "\n".join(["# 样本防伪规则", "", *[f"- {item}" for item in rules_doc["规则"]]])


def main() -> int:
    ledger = read_json(SOURCE_LEDGER)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = source_status(ledger)
    if not (status["确认当前仅首日样本"] and status["确认三日达标为false"]):
        raise SystemExit("59包台账不是仅 2026-05-08 一个自然日样本且三日达标=false，拒绝生成。")

    card = build_nextday_card(status, generated_at)
    rules_doc = build_rules_doc(ANTI_FAKE_RULES)
    package = {
        "名称": "三日巡检样本防伪与次日待执行卡包",
        "生成时间": generated_at,
        "状态": "ready",
        "来源确认": status,
        "当前允许三日达标": False,
        "样本防伪规则": rules_doc,
        "次日待执行卡": card,
        "安全边界": SAFETY_BOUNDARY,
        "未生成样本声明": {
            "第2自然日样本": "未生成",
            "第3自然日样本": "未生成",
        },
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "次日待执行卡JSON": str(NEXTDAY_CARD_JSON),
            "次日待执行卡Markdown": str(NEXTDAY_CARD_MD),
            "样本防伪规则JSON": str(ANTI_FAKE_RULES_JSON),
            "样本防伪规则Markdown": str(ANTI_FAKE_RULES_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_md(package))
    write_json(NEXTDAY_CARD_JSON, card)
    write_text(NEXTDAY_CARD_MD, build_card_md(card))
    write_json(ANTI_FAKE_RULES_JSON, rules_doc)
    write_text(ANTI_FAKE_RULES_MD, build_rules_md(rules_doc))

    print(json.dumps({"状态": "ready", "自然日样本数": 1, "三日达标": False, "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
