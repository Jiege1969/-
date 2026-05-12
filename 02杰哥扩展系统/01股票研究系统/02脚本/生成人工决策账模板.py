# -*- coding: utf-8 -*-
"""
名称：生成人工决策账模板.py
作用：生成可由用户填写或后续消息入口解析的人工决策账模板。
触发方式：python 生成人工决策账模板.py
依赖：Python标准库；复盘账本运行规则.json；系统判断账_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新系统股票模块03数据/10复盘闭环；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建人工决策账模板生成脚本。
标识：stock-human-decision-ledger-template
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


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "复盘账本运行规则.json")
    judgment_path = root / rules.get("账本路径", {}).get("系统判断账", "03数据/10复盘闭环/01系统判断账") / "系统判断账_最新.json"
    judgment = load_json(judgment_path) if judgment_path.exists() else {"系统判断账": []}
    candidates = []
    for item in judgment.get("系统判断账", [])[:20]:
        candidates.append({
            "股票代码": item.get("股票代码"),
            "股票名称": item.get("股票名称"),
            "系统推荐层级": item.get("推荐层级"),
            "系统评分": item.get("系统评分"),
            "用户反馈": "待填写",
            "确认层级": "待填写",
            "人工理由": "待填写",
            "是否进入L4及以上": False,
            "记录状态": "待用户确认"
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "反馈模板": rules.get("反馈模板", []),
        "候选决策记录": candidates,
        "填写说明": "可填写确认L4、继续观察、暂不关注、无价值、系统看错、我判断错了等反馈；L4及以上必须人工确认。",
        "安全边界": {
            "是否联网": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    ledger_dir = root / rules.get("账本路径", {}).get("人工决策账", "03数据/10复盘闭环/02人工决策账")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = ledger_dir / f"人工决策账模板_{timestamp}.json"
    latest = ledger_dir / "人工决策账模板_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"候选数量": len(candidates), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
