"""
名称：生成n8n工作流草案.py
作用：根据 v3 工作流注册表和 n8n 接口契约生成可审阅的 n8n 工作流草案清单。
触发方式：python 生成n8n工作流草案.py
依赖：Python 标准库。
所属系统：01杰哥智能系统
安全边界：只读取 v3 配置，只写入本地工作流草案；不调用 n8n API，不创建 webhook，不触发外部动作。
创建/修改记录：2026-04-26 创建 n8n 工作流草案生成脚本。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[3]


def config_dir() -> Path:
    return v3_root() / "01杰哥智能系统" / "01配置"


def output_dir() -> Path:
    target = v3_root() / "01杰哥智能系统" / "03数据" / "工作流草案"
    target.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(text: str) -> str:
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[\\/:*?\"<>|]", "", text)
    return text or "workflow"


def build_workflow_draft(workflow: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    name = workflow.get("工作流名", "未命名工作流")
    webhook_path = contract.get("入口契约", {}).get("路径前缀", "/webhook/jiege-v3/") + slugify(name)
    return {
        "名称": name,
        "状态": "草案",
        "归属系统": workflow.get("归属系统"),
        "适用任务": workflow.get("适用任务", []),
        "触发方式": workflow.get("触发方式"),
        "是否允许自动触发": False,
        "安全边界": "草案仅用于审阅，不导入 n8n，不触发外部动作。",
        "Webhook草案": {
            "方法": contract.get("入口契约", {}).get("方法", "POST"),
            "路径": webhook_path,
            "是否启用": False,
        },
        "输入字段": contract.get("入口契约", {}).get("请求字段", []),
        "输出字段": contract.get("出口契约", {}).get("响应字段", []),
        "节点草案": [
            {
                "节点名": "接收请求",
                "类型": "Webhook",
                "说明": "接收智能体大脑传来的结构化任务请求，草案阶段不启用。",
            },
            {
                "节点名": "校验字段",
                "类型": "Function",
                "说明": "检查请求ID、任务类型、风险等级和人工确认状态。",
            },
            {
                "节点名": "调用本地能力",
                "类型": "HTTP Request",
                "说明": "后续按任务类型调用 v3 本地只读能力或生成计划；当前不配置真实地址。",
            },
            {
                "节点名": "返回结果",
                "类型": "Respond to Webhook",
                "说明": "按出口契约返回执行摘要、结果数据和风险提示。",
            },
        ],
    }


def build_drafts() -> dict[str, Any]:
    registry = load_json(config_dir() / "工作流注册表.json")
    contract = load_json(config_dir() / "n8n接口契约.json")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    drafts = []
    for workflow in registry.get("工作流", []):
        draft = build_workflow_draft(workflow, contract)
        file_name = f"n8n工作流草案_{slugify(draft['名称'])}_{timestamp}.json"
        target = output_dir() / file_name
        target.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
        draft["草案文件"] = str(target)
        drafts.append(draft)

    manifest = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "契约状态": contract.get("状态"),
        "接管状态": contract.get("n8n基础信息", {}).get("接管状态"),
        "工作流数量": len(drafts),
        "是否调用n8n": False,
        "工作流草案": drafts,
    }
    output = output_dir() / f"n8n工作流草案清单_{timestamp}.json"
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = output_dir() / "n8n工作流草案清单_最新.json"
    latest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"工作流数量": len(drafts), "输出": str(output)}, ensure_ascii=False))
    return manifest


def main() -> int:
    build_drafts()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
