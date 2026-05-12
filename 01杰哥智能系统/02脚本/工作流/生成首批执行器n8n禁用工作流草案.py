# -*- coding: utf-8 -*-
"""
名称：生成首批执行器n8n禁用工作流草案.py
作用：根据首批执行器调度适配表，生成R01/R02/R03的n8n禁用工作流草案。
触发方式：python 生成首批执行器n8n禁用工作流草案.py
依赖：Python 标准库；首批执行器调度适配表_最新.json。
所属系统：01杰哥智能系统/工作流
安全边界：只生成inactive工作流草案；不导入n8n；不触发n8n；不创建系统计划任务；不包含命令执行节点；不联网；不写库；不发送企业微信；不接入税收；不写入旧系统。
创建/修改记录：2026-04-27 创建首批执行器n8n禁用工作流草案脚本。
标识：first-batch-n8n-disabled-workflow-draft
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


def system_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_workflow(adapter: dict[str, Any]) -> dict[str, Any]:
    task_id = adapter.get("任务编号")
    name = adapter.get("未来n8n入口")
    return {
        "name": f"{task_id}_{name}_禁用草案",
        "active": False,
        "nodes": [
            {
                "parameters": {},
                "id": f"{task_id}-manual-disabled",
                "name": "手动触发占位",
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": [0, 0],
                "disabled": True
            },
            {
                "parameters": {
                    "values": {
                        "string": [
                            {"name": "任务编号", "value": str(task_id)},
                            {"name": "执行器", "value": str(adapter.get("执行器"))},
                            {"name": "调度状态", "value": "禁用"},
                            {"name": "说明", "value": "草案只登记元数据，不执行命令。"}
                        ],
                        "boolean": [
                            {"name": "是否触发n8n", "value": False},
                            {"name": "是否执行真实动作", "value": False}
                        ]
                    },
                    "options": {}
                },
                "id": f"{task_id}-metadata-disabled",
                "name": "任务元数据占位",
                "type": "n8n-nodes-base.set",
                "typeVersion": 2,
                "position": [240, 0],
                "disabled": True
            }
        ],
        "connections": {},
        "settings": {},
        "staticData": None,
        "tags": ["杰哥智能化系统", "首批执行器", "禁用草案"],
        "meta": {
            "生成方式": "Codex本地草案生成",
            "安全状态": "inactive_disabled_no_command_node",
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }


def main() -> int:
    root = module_root()
    v3 = system_root()
    adapter_path = v3 / "00杰哥系统总管" / "03数据" / "小流量只读执行" / "首批执行器调度适配表_最新.json"
    adapter_report = load_json(adapter_path) if adapter_path.exists() else {}
    output_dir = root / "03数据" / "工作流草案" / "首批执行器禁用工作流"
    output_dir.mkdir(parents=True, exist_ok=True)
    workflows = []
    for adapter in adapter_report.get("调度适配", []):
        workflow = build_workflow(adapter)
        file_path = output_dir / f"{adapter.get('任务编号')}_n8n禁用工作流草案.json"
        write_json(file_path, workflow)
        workflows.append({"任务编号": adapter.get("任务编号"), "工作流文件": str(file_path), "active": workflow["active"]})
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "首批执行器n8n禁用工作流草案",
        "调度适配表": str(adapter_path),
        "工作流草案": workflows,
        "汇总": {
            "草案数量": len(workflows),
            "激活数量": sum(1 for item in workflows if item.get("active") is True),
        },
        "当前结论": "首批执行器n8n禁用工作流草案已生成；未导入n8n，未触发n8n，未包含命令执行节点。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"首批执行器n8n禁用工作流草案汇总_{timestamp}.json"
    latest = output_dir / "首批执行器n8n禁用工作流草案汇总_最新.json"
    write_json(report_path, report)
    write_json(latest, report)
    print(json.dumps({"草案数量": report["汇总"]["草案数量"], "激活数量": report["汇总"]["激活数量"], "输出": str(report_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
