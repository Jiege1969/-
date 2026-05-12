# -*- coding: utf-8 -*-
"""
名称：生成经验提炼候选账.py
作用：生成经验提炼候选账模板，为后续把系统判断、人工决策和结果验证汇总成可复用经验做准备。
触发方式：python 生成经验提炼候选账.py
依赖：Python标准库；复盘账本运行规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新系统股票模块03数据/10复盘闭环；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建经验提炼候选账生成脚本。
标识：stock-experience-extraction-candidate-ledger
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
    review_rules = load_json(root / "01配置" / "研究决策复盘闭环规则.json")
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "候选状态": "待结果验证完成后提炼",
        "归因矩阵": review_rules.get("归因矩阵", []),
        "提炼标准": review_rules.get("提炼标准", {}),
        "候选经验": [],
        "说明": "只有满足样本量、结果验证和归因说明后，才允许进入规则优化候选。",
        "安全边界": {
            "是否联网": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    ledger_dir = root / rules.get("账本路径", {}).get("经验提炼账", "03数据/10复盘闭环/04经验提炼账")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = ledger_dir / f"经验提炼候选账_{timestamp}.json"
    latest = ledger_dir / "经验提炼候选账_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"候选经验": 0, "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
