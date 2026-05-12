# -*- coding: utf-8 -*-
"""
名称：生成首批小流量空跑执行记录.py
作用：根据空跑执行规则、窗口登记和许可令，生成首批小流量任务的空跑执行记录。
触发方式：python 生成首批小流量空跑执行记录.py
依赖：Python 标准库；首批小流量空跑执行规则.json；真实小流量执行窗口登记_最新.json；真实小流量执行许可令_最新.json。
所属系统：00杰哥系统总管
安全边界：只生成dry_run空跑记录；不联网；不写库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建首批小流量空跑执行记录脚本。
标识：first-batch-dry-run-record
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


def build_task(rule: dict[str, Any], window_map: dict[str, dict[str, Any]], permit_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    task_id = rule.get("任务编号")
    window = window_map.get(task_id, {})
    permit = permit_map.get(task_id, {})
    blocked = window.get("允许真实动作") is not True or permit.get("是否允许执行") is not True
    return {
        "任务编号": task_id,
        "任务名称": rule.get("任务名称"),
        "执行模式": "dry_run",
        "空跑动作": rule.get("空跑动作"),
        "窗口状态": window.get("窗口状态", "未登记"),
        "许可令状态": permit.get("签发状态", "未生成"),
        "是否执行真实动作": False,
        "是否触发n8n": False,
        "是否写入正式库": False,
        "是否发送企业微信": False,
        "空跑结果": "通过" if blocked else "需复核",
        "结论": "真实动作被窗口和许可令阻断，仅完成空跑记录。",
    }


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    data_dir = manager / "03数据" / "小流量只读执行"
    rule_path = manager / "01配置" / "首批小流量空跑执行规则.json"
    window_path = data_dir / "真实小流量执行窗口登记_最新.json"
    permit_path = data_dir / "真实小流量执行许可令_最新.json"
    rules = load_json(rule_path)
    window_report = load_json(window_path) if window_path.exists() else {}
    permit_report = load_json(permit_path) if permit_path.exists() else {}
    window_map = {item.get("任务编号"): item for item in window_report.get("执行窗口", [])}
    permit_map = {item.get("任务编号"): item for item in permit_report.get("许可令", [])}
    tasks = [build_task(item, window_map, permit_map) for item in rules.get("空跑任务", [])]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "执行模式": rules.get("执行模式"),
        "规则文件": str(rule_path),
        "窗口登记文件": str(window_path),
        "许可令文件": str(permit_path),
        "默认开关": rules.get("默认开关", {}),
        "空跑任务": tasks,
        "汇总": {
            "任务数": len(tasks),
            "空跑通过数": sum(1 for item in tasks if item.get("空跑结果") == "通过"),
            "真实动作数": sum(1 for item in tasks if item.get("是否执行真实动作") is True),
            "n8n触发数": sum(1 for item in tasks if item.get("是否触发n8n") is True),
            "正式库写入数": sum(1 for item in tasks if item.get("是否写入正式库") is True),
            "企业微信发送数": sum(1 for item in tasks if item.get("是否发送企业微信") is True),
        },
        "当前结论": "首批小流量任务已完成空跑记录；未执行真实联网、写库、n8n触发或企业微信发送。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = data_dir / f"首批小流量空跑执行记录_{timestamp}.json"
    latest = data_dir / "首批小流量空跑执行记录_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"任务数": report["汇总"]["任务数"], "空跑通过数": report["汇总"]["空跑通过数"], "真实动作数": report["汇总"]["真实动作数"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
