# -*- coding: utf-8 -*-
"""
名称：验证研发费用加计扣除政策链补齐预演.py
作用：验收研发费用加计扣除政策链补齐预演的分层、缺口和安全边界。
安全边界：只读检查本地预演报告；不联网、不下载、不生成正式税务结论。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
OUT_DIR = ROOT / "03数据" / "22研发费用企业所得税证据链补齐预案"
PREVIEW = OUT_DIR / "研发费用加计扣除政策链补齐预演_最新.json"
REPORT_JSON = OUT_DIR / "研发费用加计扣除政策链补齐预演验收_最新.json"
REPORT_MD = OUT_DIR / "研发费用加计扣除政策链补齐预演验收_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "说明": detail}


def main() -> int:
    preview = load_json(PREVIEW)
    cards = preview.get("证据卡片", [])
    query_cards = preview.get("官方查询候选", [])
    safety = preview.get("安全边界", {})
    current_cards = [card for card in cards if card.get("是否当前适用依据候选")]
    core_119 = [card for card in cards if "完善研究开发费用税前加计扣除政策" in card.get("标题", "")]
    checks = [
        check("预演报告存在", PREVIEW.exists(), str(PREVIEW)),
        check("定位为政策证据底座", "政策证据底座" in str(preview.get("资产身份", "")), preview.get("资产身份", "")),
        check("只读本地预演模式", preview.get("模式") == "local_only_policy_chain_preview", preview.get("模式")),
        check("包含研发费用相关证据卡片", len(cards) >= 3, len(cards)),
        check("记录官方查询候选", len(query_cards) >= 1, query_cards),
        check("证据卡片具备来源和本地路径", all(card.get("来源链接") and card.get("本地原文路径") for card in cards), cards),
        check("案例不进入当前适用依据候选", all(card.get("是否当前适用依据候选") is False for card in cards if card.get("依据层级") == "案例"), cards),
        check("案例不继承被引用正式文件文号", all(not card.get("文号") for card in cards if card.get("依据层级") == "案例"), cards),
        check("指引不进入当前适用依据候选", all(card.get("是否当前适用依据候选") is False for card in cards if card.get("依据层级") == "政策解读"), cards),
        check("正式依据候选至少包含上位法或财税税务文件", any(card.get("依据层级") in {"法律", "财税文件", "税务规范性文件"} for card in cards), cards),
        check("财税119号本地元数据线索已提取", any(card.get("文号") == "财税〔2015〕119号" and card.get("施行日期") == "2016-01-01" for card in core_119), core_119),
        check("非牵头制定页面提示已保留", any("非由国家税务总局牵头制定" in card.get("页面提示", "") for card in core_119), core_119),
        check("缺口清单明确仍需复核", len(preview.get("政策链缺口", [])) >= 1, preview.get("政策链缺口", [])),
        check("链条状态未升级为正式结论", preview.get("链条状态") in {"pending_review", "evidence_ready"} and "正式税务结论" not in preview.get("链条状态", ""), preview.get("链条状态")),
        check("未生成正式税务结论", preview.get("安全边界", {}).get("是否生成正式税务结论") is False, safety),
        check("高风险动作全部关闭", all(value is False for value in safety.values()), safety),
        check("当前适用依据候选不直接形成结论", len(current_cards) < len(cards) and "不输出能否享受" in preview.get("输出边界", ""), preview.get("输出边界", "")),
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "名称": "研发费用加计扣除政策链补齐预演验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "检查结果": checks,
        "安全边界": "只读检查；不联网、不下载、不生成正式税务结论。",
    }
    write_json(REPORT_JSON, report)
    lines = [
        "# 研发费用加计扣除政策链补齐预演验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['检查项']}：{'通过' if item['通过'] else '失败'}。{item['说明']}")
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
