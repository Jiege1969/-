"""
名称：生成股票研究计划.py
作用：根据股票研究配置和股票池模板生成第一阶段只读研究计划。
触发方式：python 生成股票研究计划.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本模块配置，只写入本模块研究计划目录；不抓行情、不调用券商、不执行交易。
创建/修改记录：2026-04-26 创建第一阶段股票研究计划脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    root = module_root()
    config = load_json(root / "01配置" / "股票研究配置.json")
    pool = load_json(root / "01配置" / "股票池模板.json")
    output_dir = root / "03数据" / "02研究计划"
    output_dir.mkdir(parents=True, exist_ok=True)

    stocks = pool.get("股票池", [])
    plan = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "系统": "02杰哥扩展系统/01股票研究系统",
        "阶段": "第一阶段只读研究计划",
        "安全边界": config.get("安全边界"),
        "股票数量": len(stocks),
        "研究维度": config.get("默认研究维度", []),
        "输出规则": config.get("输出规则", {}),
        "任务列表": [
            {
                "代码": item.get("代码", ""),
                "名称": item.get("名称", ""),
                "市场": item.get("市场", ""),
                "优先级": item.get("优先级", "中"),
                "任务": [
                    "补充基础资料",
                    "核实最近财报",
                    "整理估值区间",
                    "列出主要风险",
                    "生成研究摘要"
                ],
                "当前状态": "待人工补充数据源"
            }
            for item in stocks
        ],
    }

    output = output_dir / f"股票研究计划_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    latest = output_dir / "股票研究计划_最新.json"
    text = json.dumps(plan, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"股票数量": len(stocks), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
