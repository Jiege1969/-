# -*- coding: utf-8 -*-
"""
名称：生成动态样本池设计报告.py
作用：根据动态样本池规则和重点关注池，生成股票样本池分层、评分、更新频率和算力边界报告。
触发方式：python 生成动态样本池设计报告.py
依赖：Python标准库；动态样本池规则.json；重点关注股票池.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取股票模块配置并写入股票模块03数据目录；不联网；不调用券商接口；不自动交易；不写旧系统；不触发n8n；不发送企业微信。
创建/修改记录：2026-04-28 创建动态样本池设计报告脚本；2026-04-30 适配2000只标准大股票池字段。
标识：stock-dynamic-sample-pool-design-report
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
    rule_path = root / "01配置" / "动态样本池规则.json"
    focus_path = root / "01配置" / "重点关注股票池.json"
    rules = load_json(rule_path)
    focus = load_json(focus_path)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "重点关注池文件": str(focus_path),
        "重点关注池数量": len(focus.get("股票池", [])),
        "目标规模": rules.get("目标规模", {}),
        "定位原则": rules.get("定位原则", {}),
        "样本来源": rules.get("样本来源", []),
        "评分权重": rules.get("评分权重", {}),
        "分层规则": rules.get("分层规则", []),
        "更新频率": rules.get("更新频率", {}),
        "算力边界": rules.get("算力边界", {}),
        "当前实施口径": {
            "第一阶段": "重点关注池19只先独立可用",
            "第二阶段": "试运行池扩展到300只",
            "第三阶段": "核心样本池扩展到800-1000只",
            "第四阶段": "标准大股票池扩展到2000只轻扫描",
            "大模型使用": "只用于重点关注池、候选研究池和深度分析池"
        },
        "安全边界": {
            "是否联网": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否写旧系统": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False
        },
        "当前结论": "动态样本池设计已固化；2000只标准大股票池是规律学习与候选筛选底座，不等于推荐池。"
    }
    output_dir = root / "03数据" / "07样本池"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"动态样本池设计报告_{timestamp}.json"
    latest = output_dir / "动态样本池设计报告_最新.json"
    write_json(output, report)
    write_json(latest, report)
    targets = rules.get("目标规模", {})
    large_pool_size = targets.get("标准大股票池", targets.get("盘后代表样本池"))
    print(json.dumps({"重点关注池数量": report["重点关注池数量"], "标准大股票池": large_pool_size, "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
