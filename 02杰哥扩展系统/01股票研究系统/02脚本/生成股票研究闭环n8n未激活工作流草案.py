# -*- coding: utf-8 -*-
"""
名称：生成股票研究闭环n8n未激活工作流草案.py
作用：生成股票研究分析-观察-验证-提炼-优化建议闭环的n8n未激活工作流草案，供后续人工审查后导入。
触发方式：python 生成股票研究闭环n8n未激活工作流草案.py
依赖：Python标准库；股票研究最小闭环演练规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写新系统股票模块03数据和07文档；不导入n8n；不激活工作流；不发送企业微信；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-30 创建股票研究闭环n8n未激活工作流草案生成脚本。
标识：stock-review-loop-n8n-inactive-draft-generate
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_workflow(root: Path, rules: dict[str, Any]) -> dict[str, Any]:
    base = "/mnt/d/杰哥智能化系统/02杰哥扩展系统/01股票研究系统/02脚本"
    commands = [
        ("生成闭环蓝图", f"python '{base}/生成研究决策复盘闭环蓝图.py'"),
        ("运行日常研究", f"python '{base}/运行股票日常研究链路.py'"),
        ("计算技术指标", f"python '{base}/验证技术指标计算链路.py'"),
        ("生成候选池", f"python '{base}/生成重点关注池候选池.py'"),
        ("运行L5复盘联动", f"python '{base}/运行L5日报复盘联动链路.py'"),
        ("验证四本账", f"python '{base}/验证复盘账本可运行.py'"),
    ]
    nodes: list[dict[str, Any]] = [
        {
            "parameters": {},
            "id": "manual-trigger",
            "name": "人工触发闭环演练",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [0, 300],
        }
    ]
    connections: dict[str, dict[str, list[list[dict[str, str]]]]] = {}
    previous = "人工触发闭环演练"
    for index, (name, command) in enumerate(commands, start=1):
        node = {
            "parameters": {
                "command": command,
            },
            "id": f"execute-{index}",
            "name": name,
            "type": "n8n-nodes-base.executeCommand",
            "typeVersion": 1,
            "position": [index * 260, 300],
            "notes": "未激活草案节点。正式导入前需人工核对容器路径、Python环境和执行权限。",
        }
        nodes.append(node)
        connections[previous] = {"main": [[{"node": name, "type": "main", "index": 0}]]}
        previous = name
    workflow = {
        "name": "股票研究分析观察验证提炼闭环_未激活草案",
        "active": False,
        "nodes": nodes,
        "connections": connections,
        "settings": {
            "executionOrder": "v1",
            "saveManualExecutions": True,
        },
        "tags": ["股票研究", "闭环演练", "未激活", "人工确认"],
        "meta": {
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "规则文件": str(root / "01配置" / "股票研究最小闭环演练规则.json"),
            "安全边界": rules.get("安全边界", {}),
            "说明": "本文件仅为n8n未激活工作流草案，不自动导入、不自动启用。",
        },
    }
    return workflow


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票研究闭环 n8n 未激活工作流草案",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、定位",
        "",
        "n8n 只负责调度，不负责复杂分析。复杂分析仍由股票研究系统本地脚本完成。",
        "",
        "## 二、工作流状态",
        "",
        "- 状态：未激活",
        "- 导入：未执行",
        "- 真实发送：未执行",
        "- 自动交易：禁止",
        "",
        "## 三、节点顺序",
        "",
    ]
    for item in report["节点顺序"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 四、后续启用条件",
        "",
        "1. 本地最小闭环演练通过。",
        "2. 用户确认允许导入 n8n。",
        "3. 导入后保持未激活，先做手工执行测试。",
        "4. 不接交易接口，不自动下单。",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "股票研究最小闭环演练规则.json")
    workflow = build_workflow(root, rules)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = root / "03数据" / "30n8n闭环草案"
    output = output_dir / f"股票研究闭环n8n未激活工作流草案_{timestamp}.json"
    latest = output_dir / "股票研究闭环n8n未激活工作流草案_最新.json"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "工作流文件": str(output),
        "最新工作流文件": str(latest),
        "节点顺序": [node["name"] for node in workflow["nodes"]],
        "安全边界": rules.get("安全边界", {}),
        "状态": "未激活草案已生成",
    }
    doc_path = root / "07文档" / "股票研究闭环n8n未激活工作流草案.md"
    write_json(output, workflow)
    write_json(latest, workflow)
    write_text(doc_path, build_markdown(report))
    print(json.dumps({"状态": "完成", "输出": str(output), "文档": str(doc_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
