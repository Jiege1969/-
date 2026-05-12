# -*- coding: utf-8 -*-
"""
名称：生成首批执行器调度适配表.py
作用：根据首批执行器调度适配规则，生成R01/R02/R03到未来n8n入口的禁用态映射表。
触发方式：python 生成首批执行器调度适配表.py
依赖：Python 标准库；首批执行器调度适配规则.json；首批执行器就绪总表。
所属系统：00杰哥系统总管
安全边界：只生成禁用态调度适配表；不触发n8n；不创建系统计划任务；不重启服务；不联网；不写库；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建首批执行器调度适配表脚本。
标识：first-batch-scheduler-adapter-table
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


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rule_path = manager / "01配置" / "首批执行器调度适配规则.json"
    readiness_path = manager / "03数据" / "小流量只读执行" / "首批执行器就绪总表_最新.json"
    rules = load_json(rule_path)
    readiness = load_json(readiness_path) if readiness_path.exists() else {}
    adapters = []
    for item in rules.get("调度适配", []):
        executor_path = Path(item.get("执行器", ""))
        adapters.append({
            "任务编号": item.get("任务编号"),
            "执行器": str(executor_path),
            "执行器文件存在": executor_path.exists(),
            "未来n8n入口": item.get("未来n8n入口"),
            "调度状态": item.get("调度状态", "禁用"),
            "触发方式": item.get("触发方式"),
            "是否触发n8n": False,
            "是否创建系统计划任务": False,
        })
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": rules.get("阶段"),
        "规则文件": str(rule_path),
        "就绪总表": str(readiness_path),
        "就绪总表摘要": readiness.get("汇总", {}),
        "默认开关": rules.get("默认开关", {}),
        "调度适配": adapters,
        "汇总": {
            "适配数量": len(adapters),
            "禁用数量": sum(1 for item in adapters if item.get("调度状态") == "禁用"),
            "n8n触发数量": sum(1 for item in adapters if item.get("是否触发n8n") is True),
            "系统计划任务创建数量": sum(1 for item in adapters if item.get("是否创建系统计划任务") is True),
        },
        "当前结论": "首批执行器调度适配表已生成；全部禁用，未触发n8n，未创建系统计划任务。",
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "首批执行器调度适配表_最新.json"
    latest = output_dir / "首批执行器调度适配表_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"适配数量": report["汇总"]["适配数量"], "禁用数量": report["汇总"]["禁用数量"], "n8n触发数量": report["汇总"]["n8n触发数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
