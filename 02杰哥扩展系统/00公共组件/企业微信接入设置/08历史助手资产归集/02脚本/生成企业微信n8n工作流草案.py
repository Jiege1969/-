"""
名称：生成企业微信n8n工作流草案.py
作用：根据企业微信n8n联动规则生成n8n工作流草案和导入前风险提示。
触发方式：python 生成企业微信n8n工作流草案.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/06企业微信助手系统
安全边界：只生成本地草案，不导入n8n，不启用Webhook，不连接企业微信，不真实发送。
创建/修改记录：2026-04-27 创建企业微信n8n工作流草案脚本。
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


def build_workflow_draft() -> dict[str, Any]:
    root = module_root()
    rules = load_json(root / "01配置" / "企业微信n8n联动规则.json")
    output_dir = root / "03数据" / "03工作流草案"
    output_dir.mkdir(parents=True, exist_ok=True)
    switches = rules.get("开关", {})
    if switches.get("允许导入n8n") or switches.get("允许启用Webhook") or switches.get("允许真实发送"):
        raise RuntimeError("草案阶段禁止导入n8n、启用Webhook或真实发送")

    nodes = []
    for index, node in enumerate(rules.get("n8n草案节点", []), start=1):
        nodes.append(
            {
                "id": f"wework-draft-{index:02d}",
                "name": node.get("节点名"),
                "type": node.get("节点类型"),
                "position": [index * 260, 160],
                "parameters": {
                    "职责": node.get("职责"),
                    "真实启用": False,
                    "说明": "草案节点，不导入n8n。",
                },
            }
        )

    connections = {}
    for index in range(len(nodes) - 1):
        connections[nodes[index]["name"]] = {
            "main": [
                [
                    {
                        "node": nodes[index + 1]["name"],
                        "type": "main",
                        "index": 0,
                    }
                ]
            ]
        }

    draft = {
        "name": "企业微信助手本地预演工作流草案",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active": False,
        "nodes": nodes,
        "connections": connections,
        "settings": {
            "executionOrder": "v1",
            "真实导入": False,
            "启用Webhook": False,
        },
        "field_mapping": rules.get("字段映射", {}),
        "risk_notice": rules.get("禁止事项", []),
    }
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则来源": str(root / "01配置" / "企业微信n8n联动规则.json"),
        "工作流草案": draft,
        "节点数量": len(nodes),
        "是否导入n8n": False,
        "是否启用Webhook": False,
        "是否连接企业微信": False,
        "是否真实发送": False,
        "安全说明": "该文件是n8n草案结构，不会自动导入或启用。",
    }
    latest = output_dir / "企业微信n8n工作流草案_最新.json"
    output = latest
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"node_count": len(nodes), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_workflow_draft()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
