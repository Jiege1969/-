# -*- coding: utf-8 -*-
"""生成阶段性封版候选回归建议拆单。

只读取39封版候选中的回归建议，生成可执行小回归卡候选；不写正式规则、不改运行配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\03杰哥进化系统")
SOURCE_DIR = ROOT / "03数据" / "39阶段性多业务联调通过封版候选"
OUTPUT_DIR = ROOT / "03数据" / "42阶段性封版候选回归建议拆单"
SOURCE_JSON = SOURCE_DIR / "后续回归测试建议_最新.json"
LATEST_JSON = OUTPUT_DIR / "阶段性封版候选回归建议拆单_最新.json"
LATEST_MD = OUTPUT_DIR / "阶段性封版候选回归建议拆单_最新.md"


SCOPE_BY_ID = {
    "MBI-REG-001": "02杰哥扩展系统/00公共组件/企业微信接入设置",
    "MBI-REG-002": "本地端口状态读取",
    "MBI-REG-003": "02杰哥扩展系统/05税收业务系统 + 19310工作秘书入口",
    "MBI-REG-004": "企业微信公共接入层多助手入口",
    "MBI-REG-005": "02杰哥扩展系统/01股票研究系统前台展示产物",
    "MBI-REG-006": "02杰哥扩展系统/02视频制作系统预检与阻断产物",
    "MBI-REG-007": "企业微信公共接入层/health 与n8n禁用态口径",
    "MBI-REG-008": "03杰哥进化系统候选资产",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_cards(source: dict[str, Any]) -> list[dict[str, Any]]:
    cards = []
    for item in source.get("回归建议", []):
        reg_id = item.get("建议ID")
        cards.append(
            {
                "回归ID": reg_id,
                "名称": item.get("名称"),
                "执行范围": SCOPE_BY_ID.get(reg_id, "待补范围"),
                "建议样本": item.get("建议样本", []),
                "通过标准": item.get("通过标准", ""),
                "禁止动作": item.get("禁止动作", []),
                "默认执行方式": "只读检查或读取最新验收产物",
                "越权处理": "登记为需总管确认，不自动执行",
                "状态": "candidate_regression_card",
            }
        )
    return cards


def build_markdown(asset: dict[str, Any]) -> str:
    lines = [
        "# 阶段性封版候选回归建议拆单",
        "",
        f"- 生成时间：{asset['生成时间']}",
        "- 性质：候选拆单，不是正式规则",
        f"- 回归卡数量：{asset['汇总']['回归卡数量']}",
        "",
        "| 回归ID | 名称 | 执行范围 | 默认执行方式 |",
        "| --- | --- | --- | --- |",
    ]
    for card in asset["回归卡"]:
        lines.append(f"| {card['回归ID']} | {card['名称']} | {card['执行范围']} | {card['默认执行方式']} |")
    lines.extend(["", "## 禁止动作汇总", ""])
    for item in asset["禁止动作汇总"]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def main() -> int:
    source = load_json(SOURCE_JSON)
    cards = build_cards(source)
    forbidden = sorted({action for card in cards for action in card.get("禁止动作", [])})
    asset = {
        "名称": "阶段性封版候选回归建议拆单",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "性质": "候选拆单，不是正式规则",
        "来源": str(SOURCE_JSON),
        "回归卡": cards,
        "禁止动作汇总": forbidden,
        "汇总": {"回归卡数量": len(cards), "禁止动作数量": len(forbidden)},
        "安全边界": {
            "写正式规则": False,
            "修改运行配置": False,
            "触发服务重载": False,
            "真实发送企业微信": False,
            "接n8n": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "修改总管面板": False,
            "修改一键接续包": False,
            "推进为正式规则": False,
        },
    }
    write_json(LATEST_JSON, asset)
    write_text(LATEST_MD, build_markdown(asset))
    print(json.dumps({"回归卡数量": len(cards), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
