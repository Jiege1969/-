# -*- coding: utf-8 -*-
"""
名称：记录系统判断账.py
作用：从最新重点关注池公开行情快照生成系统判断账，记录系统为什么推荐或过滤股票。
触发方式：python 记录系统判断账.py
依赖：Python标准库；复盘账本运行规则.json；重点关注池公开行情快照_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读新系统股票模块数据；只写新系统股票模块03数据/10复盘闭环；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建系统判断账记录脚本。
标识：stock-system-judgment-ledger-record
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def choose_layer(score: int, rules: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rules, key=lambda item: int(item.get("最低分", 0)), reverse=True)
    for item in ordered:
        if score >= int(item.get("最低分", 0)):
            return item
    return {"层级": "L7系统过滤", "权限": "系统可自动过滤"}


def score_quote(row: dict[str, Any], score_rules: dict[str, int]) -> dict[str, Any]:
    score = int(score_rules.get("基础分", 50))
    basis: list[str] = []
    risks: list[str] = []
    pct = to_float(row.get("涨跌幅"))
    volume_ratio = to_float(row.get("量比"))
    turnover = to_float(row.get("换手率"))
    pe = to_float(row.get("市盈率"))

    if pct is not None:
        if 0 <= pct <= 4:
            score += int(score_rules.get("涨跌幅0到4", 0))
            basis.append(f"涨跌幅{pct}%，处于温和强势区间。")
        elif pct > 7:
            score += int(score_rules.get("涨跌幅大于7", 0))
            risks.append(f"涨跌幅{pct}%，追高和回落风险上升。")
        elif pct < -5:
            score += int(score_rules.get("涨跌幅小于-5", 0))
            risks.append(f"涨跌幅{pct}%，需核实趋势破位或利空。")
        else:
            basis.append(f"涨跌幅{pct}%，需结合趋势位置判断。")
    if volume_ratio is not None:
        if 1.1 <= volume_ratio <= 2.5:
            score += int(score_rules.get("量比1点1到2点5", 0))
            basis.append(f"量比{volume_ratio}，活跃度改善。")
        elif volume_ratio > 4:
            score += int(score_rules.get("量比大于4", 0))
            risks.append(f"量比{volume_ratio}，异动过强需防冲高回落。")
    if turnover is not None:
        if 1 <= turnover <= 8:
            score += int(score_rules.get("换手率1到8", 0))
            basis.append(f"换手率{turnover}%，流动性可观察。")
        elif turnover > 15:
            score += int(score_rules.get("换手率大于15", 0))
            risks.append(f"换手率{turnover}%，筹码波动偏大。")
    if pe is not None and pe > 90:
        score += int(score_rules.get("市盈率大于90", 0))
        risks.append(f"市盈率{pe}，估值和业绩兑现压力需复核。")

    return {
        "评分": max(0, min(100, score)),
        "依据": basis or ["公开行情未触发明显正向条件。"],
        "风险": risks or ["单日行情未暴露突出风险，但仍需结合公告、财务和趋势。"]
    }


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "复盘账本运行规则.json")
    snapshot_path = root / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json"
    snapshot = load_json(snapshot_path)
    rows = snapshot.get("行情", [])
    entries = []
    for row in rows:
        score = score_quote(row, rules.get("评分规则", {}))
        layer = choose_layer(score["评分"], rules.get("分层规则", []))
        entries.append({
            "记录时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "股票代码": row.get("代码"),
            "股票名称": row.get("名称"),
            "推荐层级": layer.get("层级"),
            "权限边界": layer.get("权限"),
            "系统评分": score["评分"],
            "触发依据": score["依据"],
            "风险提示": score["风险"],
            "指标快照": row,
            "数据来源": snapshot.get("数据源"),
            "数据生成时间": snapshot.get("生成时间"),
            "固定声明": "研究辅助，不构成投资建议，不自动交易。"
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(root / "01配置" / "复盘账本运行规则.json"),
        "行情快照": str(snapshot_path),
        "记录数量": len(entries),
        "系统判断账": entries,
        "安全边界": {
            "是否联网": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    ledger_dir = root / rules.get("账本路径", {}).get("系统判断账", "03数据/10复盘闭环/01系统判断账")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = ledger_dir / f"系统判断账_{timestamp}.json"
    latest = ledger_dir / "系统判断账_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"记录数量": len(entries), "输出": str(output)}, ensure_ascii=False))
    return 0 if entries else 1


if __name__ == "__main__":
    raise SystemExit(main())
