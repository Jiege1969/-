# -*- coding: utf-8 -*-
"""
名称：生成真实小流量执行许可令.py
作用：根据真实小流量执行许可令规则，生成首批任务的未签发许可令清单。
触发方式：python 生成真实小流量执行许可令.py
依赖：Python 标准库；真实小流量执行许可令规则.json；真实小流量执行窗口登记_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成未签发许可令；不联网；不写库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建真实小流量执行许可令生成脚本。
标识：real-execution-permit-order
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_order(template: dict[str, Any], window_map: dict[str, dict[str, Any]], default_status: str) -> dict[str, Any]:
    task_id = template.get("任务编号")
    window = window_map.get(task_id, {})
    return {
        "任务编号": task_id,
        "任务名称": template.get("任务名称"),
        "窗口状态": window.get("窗口状态", "未登记"),
        "动作边界": template.get("动作边界"),
        "输入范围": template.get("输入范围"),
        "输出范围": template.get("输出范围"),
        "回滚方式": template.get("回滚方式"),
        "观测指标": template.get("观测指标", []),
        "签发状态": default_status,
        "签发人": "",
        "签发时间": "",
        "是否允许执行": False,
        "阻断原因": "许可令未签发，窗口未开放。",
    }


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rule_path = manager / "01配置" / "真实小流量执行许可令规则.json"
    window_path = manager / "03数据" / "小流量只读执行" / "真实小流量执行窗口登记_最新.json"
    rules = load_json(rule_path)
    window_report = load_json(window_path) if window_path.exists() else {}
    window_map = {item.get("任务编号"): item for item in window_report.get("执行窗口", [])}
    orders = [build_order(item, window_map, rules.get("默认签发状态", "未签发")) for item in rules.get("任务模板", [])]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "窗口登记文件": str(window_path),
        "默认开关": rules.get("默认开关", {}),
        "许可令": orders,
        "汇总": {
            "许可令数量": len(orders),
            "已签发数量": sum(1 for item in orders if item.get("签发状态") == "已签发"),
            "允许执行数量": sum(1 for item in orders if item.get("是否允许执行") is True),
        },
        "当前结论": "首批小流量执行许可令已生成；全部为未签发状态，不允许真实执行。",
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "真实小流量执行许可令_最新.json"
    latest = output_dir / "真实小流量执行许可令_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"许可令数量": report["汇总"]["许可令数量"], "允许执行数量": report["汇总"]["允许执行数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
