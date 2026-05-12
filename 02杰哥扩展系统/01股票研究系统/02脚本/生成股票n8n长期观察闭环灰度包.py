# -*- coding: utf-8 -*-
"""
名称：生成股票n8n长期观察闭环灰度包.py
作用：把股票主动研究、单人推送、用户反馈和进化候选串成n8n长期观察闭环灰度方案。
触发方式：python 生成股票n8n长期观察闭环灰度包.py
依赖：Python标准库；既有股票主动研究闭环、反馈记录与进化候选脚本。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写本地258灰度包；不导入n8n；不启用n8n工作流；不真实发送企业微信；不群发；不调用券商接口；不自动交易；不重载服务。
标识：stock-n8n-long-observation-loop-gray-package-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return module_root().parents[1]


def evolution_root() -> Path:
    return project_root() / "03杰哥进化系统"


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


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
    }


def workflow_blueprint(root: Path, evo: Path) -> dict[str, Any]:
    local_pipeline = root / "02脚本" / "运行股票主动研究闭环_本地.py"
    feedback_script = root / "02脚本" / "记录股票AI反馈.py"
    evo_candidate_script = evo / "02脚本" / "生成股票复盘反馈样本接入候选包.py"
    return {
        "name": "股票长期观察闭环_灰度草案",
        "active": False,
        "draft_only": True,
        "intended_mode": "n8n参与长期分析和反馈闭环；真实发送另走单人灰度闸口。",
        "nodes": [
            {
                "name": "Schedule Trigger",
                "type": "n8n-nodes-base.scheduleTrigger",
                "active_requirement": "导入后初始保持active=false；灰度启用时只允许工作日低频触发。",
                "purpose": "每天固定时间让股票系统主动参与分析。",
            },
            {
                "name": "Run Local Stock Observation",
                "type": "n8n-nodes-base.executeCommand",
                "parameters": {
                    "command": f"python \"{local_pipeline}\" --no-complex"
                },
                "purpose": "生成本地股票研究报告、企业微信推送草案和发送前检查。",
            },
            {
                "name": "Read Push Draft",
                "type": "n8n-nodes-base.readBinaryFile",
                "parameters": {
                    "filePath": str(root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md")
                },
                "purpose": "读取准备推给使用者观察的报告草案。",
            },
            {
                "name": "Single User Send Gate",
                "type": "manual_or_controlled_gate",
                "parameters": {
                    "allowed_receivers": ["ChenXiaoJie"],
                    "max_messages_per_run": 1,
                    "group_send": False,
                    "broker_api": False,
                    "trade": False,
                },
                "purpose": "只允许本人、单条、低频；真实发送必须另有确认令。",
            },
            {
                "name": "Feedback Intake",
                "type": "n8n-nodes-base.executeCommand",
                "parameters": {
                    "command_template": f"python \"{feedback_script}\" --command \"{{{{feedback_text}}}}\""
                },
                "purpose": "把使用者对报告的反馈写入股票系统本地反馈日志。",
            },
            {
                "name": "Evolution Candidate Sync",
                "type": "n8n-nodes-base.executeCommand",
                "parameters": {
                    "command": f"python \"{evo_candidate_script}\""
                },
                "purpose": "把复盘和反馈整理为进化候选，不自动转正式规则。",
            },
        ],
        "connections": {
            "Schedule Trigger": ["Run Local Stock Observation"],
            "Run Local Stock Observation": ["Read Push Draft"],
            "Read Push Draft": ["Single User Send Gate"],
            "Feedback Intake": ["Evolution Candidate Sync"],
        },
        "activation_stages": [
            {
                "阶段": "A",
                "名称": "本地长期分析dry-run",
                "n8n可参与": True,
                "真实发送": False,
                "说明": "n8n可定时或手动触发本地分析，只写本地报告和日志。",
            },
            {
                "阶段": "B",
                "名称": "单人推送灰度",
                "n8n可参与": True,
                "真实发送": "仅本人单条且受控确认",
                "说明": "只允许ChenXiaoJie，且每次最多一条。",
            },
            {
                "阶段": "C",
                "名称": "反馈进化候选闭环",
                "n8n可参与": True,
                "真实发送": "沿用单人灰度限制",
                "说明": "把使用者反馈和复盘结果转为进化候选，不自动生效为正式规则。",
            },
        ],
        "hard_guards": {
            "group_send": False,
            "broker_api": False,
            "trade": False,
            "auto_formal_rule": False,
            "service_reload": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票n8n长期观察闭环灰度包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- n8n定位：{report['n8n定位']}",
        f"- 是否真实发送企业微信：{report['安全边界']['真实发送企业微信']}",
        f"- 是否接券商/交易：{report['安全边界']['调用券商接口']} / {report['安全边界']['自动交易']}",
        "",
        "## 为什么要启用n8n参与",
        "",
    ]
    for item in report["使用者目标吸收"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 闭环链路", ""])
    for idx, item in enumerate(report["闭环链路"], 1):
        lines.append(f"{idx}. {item}")
    lines.extend(["", "## 启用阶段", ""])
    for item in report["工作流草案"]["activation_stages"]:
        lines.append(f"- {item['阶段']} {item['名称']}：{item['说明']}")
    lines.extend(["", "## 当前仍未执行的动作", ""])
    for item in report["当前未执行动作"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    evo = evolution_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    out_dir = root / "03数据" / "258股票n8n长期观察闭环灰度包"
    log_dir = root / "04日志" / "股票n8n长期观察闭环灰度包"

    source_files = {
        "本地主动研究闭环": root / "02脚本" / "运行股票主动研究闭环_本地.py",
        "n8n未激活编排草案": root / "02脚本" / "生成股票主动研究n8n未激活编排草案.py",
        "股票AI反馈记录": root / "02脚本" / "记录股票AI反馈.py",
        "进化反馈样本候选": evo / "02脚本" / "生成股票复盘反馈样本接入候选包.py",
        "主动推送灰度巡检": root / "02脚本" / "执行股票主动推送灰度链路一键只读巡检.py",
    }

    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "包名": "股票n8n长期观察闭环灰度包",
        "当前结论": "方向修正为启用n8n参与长期分析和反馈闭环；真实发送仍走单人灰度闸口。",
        "n8n定位": "调度器和闭环编排器，不是券商、不负责交易决策。",
        "使用者目标吸收": [
            "股票分析是长期过程，系统必须主动参与观察，不能只在被询问时响应。",
            "n8n应负责定时触发分析、生成报告、推送给本人观察、收集反馈。",
            "使用者近期主要工作是看分析内容是否全面、结果是否说到位。",
            "进化系统负责把反馈沉淀为候选经验，但不自动转正式规则。",
        ],
        "闭环链路": [
            "n8n定时或人工触发本地股票主动研究闭环。",
            "股票系统生成研究报告、推送草案、发送前检查和日志。",
            "企业微信灰度阶段只允许本人单条接收，禁止群发。",
            "使用者回复反馈，例如：说到位、太空泛、少了财务、风险没讲清、这个口径保留。",
            "股票反馈脚本把反馈写入本地日志。",
            "进化系统把反馈和复盘结果整理成候选，不自动改正式规则。",
        ],
        "源入口状态": {name: file_state(path) for name, path in source_files.items()},
        "工作流草案": workflow_blueprint(root, evo),
        "当前放行判断": {
            "允许n8n参与本地长期分析dry-run": True,
            "允许n8n真实触发外部Webhook": False,
            "允许企业微信单人真实灰度发送": "需要单独受控确认令和最终发送闸口",
            "允许群发": False,
            "允许券商接口": False,
            "允许自动交易": False,
            "允许自动转正式规则": False,
        },
        "当前未执行动作": [
            "未导入n8n工作流。",
            "未启用n8n active=true。",
            "未调用n8n API。",
            "未真实发送企业微信。",
            "未修改19310/19302服务。",
            "未写进化正式规则。",
        ],
        "安全边界": {
            "导入n8n": False,
            "启用n8n工作流": False,
            "触发n8n": False,
            "真实发送企业微信": False,
            "群发": False,
            "调用券商接口": False,
            "自动交易": False,
            "自动转正式规则": False,
            "重载19310": False,
            "重载19302": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
        "实际动作": {
            "写本地258灰度包": True,
            "读取既有入口状态": True,
            "导入n8n": False,
            "启用n8n工作流": False,
            "触发n8n": False,
            "真实发送企业微信": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    output_json = out_dir / f"股票n8n长期观察闭环灰度包_{stamp}.json"
    latest_json = out_dir / "股票n8n长期观察闭环灰度包_最新.json"
    output_md = out_dir / f"股票n8n长期观察闭环灰度包_{stamp}.md"
    latest_md = out_dir / "股票n8n长期观察闭环灰度包_最新.md"
    log_json = log_dir / f"stock-n8n-long-observation-loop-gray-package-{stamp}.json"
    log_latest = log_dir / "stock-n8n-long-observation-loop-gray-package-最新.json"

    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_json(log_json, {
        "生成时间": report["生成时间"],
        "输出": str(latest_json),
        "安全边界": report["安全边界"],
        "实际动作": report["实际动作"],
    })
    write_json(log_latest, load_json(log_json, {}))
    print(json.dumps({
        "状态": "完成",
        "允许n8n参与本地长期分析dry_run": True,
        "真实发送企业微信": False,
        "输出": str(latest_json),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
