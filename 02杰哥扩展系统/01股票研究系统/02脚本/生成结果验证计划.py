# -*- coding: utf-8 -*-
"""
名称：生成结果验证计划.py
作用：根据系统判断账生成T+1、T+3、T+5、T+20结果验证计划，为后续复盘归因提供任务清单。
触发方式：python 生成结果验证计划.py
依赖：Python标准库；复盘账本运行规则.json；系统判断账_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新系统股票模块03数据/10复盘闭环；不联网；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建结果验证计划生成脚本。
标识：stock-result-verification-plan-generate
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
    judgment = load_json(judgment_path)
    tasks = []
    for item in judgment.get("系统判断账", []):
        for cycle in rules.get("验证周期", []):
            tasks.append({
                "创建时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "验证周期": cycle,
                "股票代码": item.get("股票代码"),
                "股票名称": item.get("股票名称"),
                "原始推荐层级": item.get("推荐层级"),
                "原始系统评分": item.get("系统评分"),
                "待验证字段": ["区间涨跌幅", "最大上涨", "最大回撤", "是否触发风险", "是否符合原始判断"],
                "验证状态": "待到期执行",
                "说明": "当前只生成计划，不联网抓取，不触发真实调度。"
            })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源系统判断账": str(judgment_path),
        "任务数量": len(tasks),
        "结果验证计划": tasks,
        "安全边界": {
            "是否联网": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    ledger_dir = root / rules.get("账本路径", {}).get("结果验证账", "03数据/10复盘闭环/03结果验证账")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = ledger_dir / f"结果验证计划_{timestamp}.json"
    latest = ledger_dir / "结果验证计划_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"任务数量": len(tasks), "输出": str(output)}, ensure_ascii=False))
    return 0 if tasks else 1


if __name__ == "__main__":
    raise SystemExit(main())
