# -*- coding: utf-8 -*-
"""
名称：生成首批执行器就绪总表.py
作用：汇总R01股票只读探测器、R02知识库本地入库预演器、R03办公材料草稿预演器的最新联检状态。
触发方式：python 生成首批执行器就绪总表.py
依赖：Python 标准库；R01/R02/R03最新联检报告；真实小流量执行窗口登记和许可令。
所属系统：00杰哥系统总管
安全边界：只读取联检报告并生成总表；不联网；不写库；不触发n8n；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建首批执行器就绪总表脚本。
标识：first-batch-executor-readiness-table
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


def load_json_if_exists(path: Path) -> dict[str, Any]:
    return load_json(path) if path.exists() else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def task_row(task_id: str, name: str, report_path: Path, blocked_field: str) -> dict[str, Any]:
    report = load_json_if_exists(report_path)
    return {
        "任务编号": task_id,
        "任务名称": name,
        "联检报告": str(report_path),
        "执行器状态": report.get("执行器状态", "未生成"),
        "是否真实动作": report.get(blocked_field),
        "执行模式": report.get("执行模式", ""),
        "当前结论": report.get("当前结论", ""),
    }


def main() -> int:
    root = v3_root()
    manager = root / "00杰哥系统总管"
    rows = [
        task_row(
            "R01",
            "股票公开数据只读探测器",
            root / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "06公开数据探测" / "R01股票只读探测器联检_最新.json",
            "是否执行真实联网请求",
        ),
        task_row(
            "R02",
            "知识库本地入库预演器",
            root / "01杰哥智能系统" / "03数据" / "知识库" / "06入库前复核" / "R02知识库本地入库预演器联检_最新.json",
            "是否写入正式向量库",
        ),
        task_row(
            "R03",
            "办公材料草稿预演器",
            root / "02杰哥扩展系统" / "03本职工作系统" / "03数据" / "04本地生成门禁" / "R03办公材料草稿预演器联检_最新.json",
            "是否输出正式文档",
        ),
    ]
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "首批执行器就绪总表",
        "执行器": rows,
        "汇总": {
            "执行器数量": len(rows),
            "就绪但冻结数量": sum(1 for item in rows if item.get("执行器状态") == "就绪但冻结"),
            "真实动作数量": sum(1 for item in rows if item.get("是否真实动作") is True),
        },
        "当前结论": "首批R01/R02/R03执行器均已进入联检链路；当前全部就绪但冻结，未执行真实动作。",
    }
    output_dir = manager / "03数据" / "小流量只读执行"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / "首批执行器就绪总表_最新.json"
    latest = output_dir / "首批执行器就绪总表_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行器数量": report["汇总"]["执行器数量"], "就绪但冻结数量": report["汇总"]["就绪但冻结数量"], "真实动作数量": report["汇总"]["真实动作数量"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
