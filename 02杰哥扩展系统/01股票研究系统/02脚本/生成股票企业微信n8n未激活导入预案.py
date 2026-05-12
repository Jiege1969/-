# -*- coding: utf-8 -*-
"""
名称：生成股票企业微信n8n未激活导入预案.py
作用：生成股票企业微信n8n适配器工作流人工确认后的未激活导入预案，不执行导入。
触发方式：python 生成股票企业微信n8n未激活导入预案.py
依赖：Python标准库；股票企业微信n8n灰度导入许可令_最新.json；股票企业微信n8n适配器工作流草案_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成本地导入预案；不调用n8n API；不导入n8n；不启用Webhook；不触发工作流；不调用OpenClaw；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信n8n未激活导入预案脚本。
标识：stock-wework-n8n-inactive-import-plan-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(plan: dict[str, Any]) -> str:
    steps = "\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(plan["人工确认后步骤"]))
    checks = "\n".join(f"- {item}" for item in plan["导入后只读检查"])
    rollback = "\n".join(f"- {item}" for item in plan["回滚保持未激活"])
    return f"""# 股票企业微信n8n未激活导入预案

生成时间：{plan['生成时间']}

结论：{plan['结论']}

## 一、人工确认后步骤

{steps}

## 二、导入后只读检查

{checks}

## 三、回滚保持未激活

{rollback}

## 四、当前实际动作

- 调用n8n API：false
- 导入n8n：false
- 启用Webhook：false
- 触发n8n：false
- 发送企业微信：false
"""


def main() -> int:
    root = module_root()
    permit = load_json(root / "03数据" / "29n8n灰度导入许可" / "股票企业微信n8n灰度导入许可令_最新.json", {})
    workflow_path = root / "03数据" / "28n8n适配器工作流草案" / "股票企业微信n8n适配器工作流草案_最新.json"
    workflow = load_json(workflow_path, {})
    plan = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "inactive_import_plan_only",
        "许可令结论": permit.get("结论", ""),
        "工作流草案": str(workflow_path),
        "工作流名称": workflow.get("name", ""),
        "工作流active": workflow.get("active"),
        "人工确认后步骤": [
            "先执行n8n当前状态只读备份，保存导入前工作流清单。",
            "人工确认后导入工作流JSON，但必须保持active=false。",
            "导入后立即检查工作流active状态、节点数量、是否存在凭据、是否存在Webhook启用。",
            "不执行手动触发，不接OpenClaw，不接企业微信真实发送。",
            "生成导入后只读验收报告和回滚保持未激活预案。"
        ],
        "导入后只读检查": [
            "工作流存在且名称匹配。",
            "active=false。",
            "无credentials字段。",
            "无真实企业微信发送节点。",
            "无交易接口节点。",
            "最近执行记录为空或未执行。"
        ],
        "回滚保持未激活": [
            "若导入后active=true，立即设置active=false。",
            "若发现凭据或真实发送节点，停止灰度接入并提交诊断报告。",
            "回滚只保持未激活，不删除工作流，避免破坏性操作。"
        ],
        "实际动作": {
            "调用n8nAPI": False,
            "导入n8n": False,
            "启用Webhook": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "结论": "已生成未激活导入预案，等待人工确认后才能进入导入动作。" if permit.get("失败") == 0 and workflow.get("active") is False else "导入预案证据不足，暂不建议进入人工确认。",
    }
    output_dir = root / "03数据" / "30n8n未激活导入预案"
    log_dir = root / "04日志" / "n8n未激活导入预案"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / "股票企业微信n8n未激活导入预案_最新.json"
    latest_json = output_dir / "股票企业微信n8n未激活导入预案_最新.json"
    md_path = output_dir / "股票企业微信n8n未激活导入预案_最新.md"
    latest_md = output_dir / "股票企业微信n8n未激活导入预案_最新.md"
    log_path = log_dir / "stock-wework-n8n-inactive-import-plan-generate-最新.json"
    write_json(json_path, plan)
    write_json(latest_json, plan)
    write_text(md_path, build_markdown(plan))
    write_text(latest_md, build_markdown(plan))
    write_json(log_path, plan)
    print(json.dumps({"结论": plan["结论"], "输出": str(latest_md)}, ensure_ascii=False))
    return 0 if workflow.get("active") is False else 1


if __name__ == "__main__":
    raise SystemExit(main())
