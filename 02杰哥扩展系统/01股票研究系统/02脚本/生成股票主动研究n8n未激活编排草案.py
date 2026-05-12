# -*- coding: utf-8 -*-
"""
名称：生成股票主动研究n8n未激活编排草案.py
作用：生成股票主动研究闭环的n8n未激活编排草案；只生成本地草案，不导入n8n。
触发方式：python 生成股票主动研究n8n未激活编排草案.py
依赖：运行股票主动研究闭环_本地.py；股票企微推送前放行包_最新.json（可选）。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只生成草案文件；不调用n8n API；不导入n8n；不启用工作流；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-active-research-n8n-inactive-draft-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def workflow_draft(root: Path) -> dict[str, Any]:
    script = root / "02脚本" / "运行股票主动研究闭环_本地.py"
    intraday_strategy = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票n8n日内报告闭环与晨报推送策略包_最新.json"
    return {
        "name": "股票主动研究闭环_未激活草案",
        "active": False,
        "draft_only": True,
        "strategy_source": str(intraday_strategy),
        "intraday_report_loop": {
            "轻量随问随答": "全天；不走n8n即时主链路，避免增加延迟。",
            "收市后每日观察": "15:40-18:30；生成分层日报、候选池和第二天候选推荐草案。",
            "半夜宏观规律分析": "00:30-05:30；复盘前日推送、行业轮动和替代候选。",
            "开市前晨报推送": "08:20-08:40；进入本人单条灰度闸口，不群发。",
        },
        "nodes": [
            {
                "name": "Manual Trigger",
                "type": "n8n-nodes-base.manualTrigger",
                "notes": "仅草案；导入后也必须保持active=false。"
            },
            {
                "name": "Run Local Stock Pipeline",
                "type": "n8n-nodes-base.executeCommand",
                "parameters": {
                    "command": f"python \"{script}\" --no-complex"
                },
                "notes": "运行本地闭环脚本，只生成本地文件和推送草案，不真实发送。"
            },
            {
                "name": "Read Push Draft",
                "type": "n8n-nodes-base.readBinaryFile",
                "parameters": {
                    "filePath": str(root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md")
                },
                "notes": "读取推送草案；真实发送节点不放入初版草案。"
            },
            {
                "name": "Read Intraday Strategy",
                "type": "n8n-nodes-base.readBinaryFile",
                "parameters": {
                    "filePath": str(intraday_strategy)
                },
                "notes": "读取260日内报告闭环与晨报推送策略；用于后续收市、半夜、晨报分时调度。"
            }
        ],
        "connections": {
            "Manual Trigger": {
                "main": [[{"node": "Run Local Stock Pipeline", "type": "main", "index": 0}]]
            },
            "Run Local Stock Pipeline": {
                "main": [[{"node": "Read Push Draft", "type": "main", "index": 0}, {"node": "Read Intraday Strategy", "type": "main", "index": 0}]]
            }
        },
        "safety": {
            "no_wecom_send_node": True,
            "no_webhook_public_trigger": True,
            "no_broker_api": True,
            "no_auto_trade": True,
            "must_remain_inactive_after_import": True
        }
    }


def build_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# 股票主动研究n8n未激活编排草案",
        "",
        "## 状态",
        "",
        "- 只生成草案文件。",
        "- 未调用n8n API。",
        "- 未导入n8n。",
        "- 未启用工作流。",
        "- 未发送企业微信。",
        "",
        "## 编排目标",
        "",
        "未来由n8n做流程编排：手动或定时触发本地闭环脚本，读取推送草案，等待人工放行。",
        "",
        "## 初版草案节点",
        "",
        "1. Manual Trigger",
        "2. Run Local Stock Pipeline",
        "3. Read Push Draft",
        "",
        "## 明确不包含",
        "",
        "- 不包含企业微信真实发送节点。",
        "- 不包含公开Webhook触发。",
        "- 不包含券商接口。",
        "- 不包含自动交易。",
        "",
        "## 草案文件",
        "",
        f"- JSON：`{report['输出文件']['JSON时间戳文件']}`",
        f"- 最新JSON：`{report['输出文件']['JSON最新文件']}`",
    ])


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    approval_path = root / "03数据" / "138推送前放行包" / "股票企微推送前放行包_最新.json"
    approval = load_json(approval_path, required=False)
    output_dir = root / "03数据" / "139n8n主动研究编排草案"
    output_json = output_dir / f"股票主动研究n8n未激活编排草案_{stamp}.json"
    output_md = output_dir / f"股票主动研究n8n未激活编排草案_{stamp}.md"
    latest_json = output_dir / "股票主动研究n8n未激活编排草案_最新.json"
    latest_md = output_dir / "股票主动研究n8n未激活编排草案_最新.md"
    log_dir = root / "04日志" / "人工闸口"
    log_path = log_dir / f"股票主动研究n8n未激活编排草案生成日志_{stamp}.json"
    log_latest_path = log_dir / "股票主动研究n8n未激活编排草案生成日志_最新.json"

    report = {
        "名称": "股票主动研究n8n未激活编排草案",
        "版本": "2026-05-01",
        "定位": "为股票主动研究闭环准备n8n编排草案；不导入、不启用、不发送。",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票主动研究n8n未激活编排草案.py",
        "草案状态": "仅本地草案",
        "是否已导入n8n": False,
        "是否已启用n8n": False,
        "是否包含真实发送节点": False,
        "上游放行包": str(approval_path) if approval else "",
        "日内报告闭环策略包": str(root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "股票n8n日内报告闭环与晨报推送策略包_最新.json"),
        "工作流草案": workflow_draft(root),
        "数据健康度": {
            "放行包存在": bool(approval),
            "草案active": False,
            "是否完整": True,
        },
        "安全边界": {
            "是否调用n8n API": False,
            "是否导入n8n": False,
            "是否启用n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
        "实际动作": {
            "生成本地草案": True,
            "写入03数据": True,
            "写入04日志": True,
            "调用n8n API": False,
            "导入n8n": False,
            "启用n8n": False,
            "企业微信真实发送": False,
        },
        "输出文件": {
            "JSON时间戳文件": str(output_json),
            "Markdown时间戳文件": str(output_md),
            "JSON最新文件": str(latest_json),
            "Markdown最新文件": str(latest_md),
        },
    }
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, {
        "名称": "股票主动研究n8n未激活编排草案生成日志",
        "生成时间": report["生成时间"],
        "数据健康度": report["数据健康度"],
        "输出文件": report["输出文件"],
        "安全边界": report["安全边界"],
        "实际动作": report["实际动作"],
    })
    write_json(log_latest_path, load_json(log_path, required=True))
    print(json.dumps({
        "状态": "完成",
        "是否已导入n8n": False,
        "是否已启用n8n": False,
        "Markdown": str(output_md),
        "JSON": str(output_json),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
