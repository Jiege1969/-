# -*- coding: utf-8 -*-
"""
名称：生成后续低风险队列补充与状态观察.py
作用：根据计划工作模式开工包、日常调度状态、任务队列调度和无干扰规则，生成下一批低风险候选与状态观察报告。
触发方式：python 生成后续低风险队列补充与状态观察.py
所属系统：00杰哥系统总管
安全边界：只读当前状态和脚本存在性；只写00总管运行状态报告；不触发执行器；不触发n8n；
不发送企业微信；不写正式库；不重启19300/19302；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
INTELLIGENCE = ROOT / "01杰哥智能系统"
EXTENSION = ROOT / "02杰哥扩展系统"
EVOLUTION = ROOT / "03杰哥进化系统"
OUT_DIR = MANAGER / "03数据" / "运行状态"
RULE_PATH = MANAGER / "01配置" / "无干扰自动施工模式规则.json"
PLAN_PACKAGE = OUT_DIR / "计划工作模式开工包_最新.json"
SCHEDULE_STATE = OUT_DIR / "个人智能母系统日常调度状态_最新.json"
TASK_QUEUE = OUT_DIR / "个人智能母系统任务队列调度_最新.json"
CURRENT_QUEUE = OUT_DIR / "无干扰自动施工队列_最新.json"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def script_status(path: Path) -> dict[str, Any]:
    return {"路径": str(path), "存在": path.exists()}


def build_candidate(code: str, name: str, system: str, action: str, scripts: list[Path], level: str, reason: str) -> dict[str, Any]:
    return {
        "编号": code,
        "任务": name,
        "所属系统": system,
        "执行方式": action,
        "自动级别": level,
        "判定原因": reason,
        "脚本检查": [script_status(path) for path in scripts],
        "脚本齐备": all(path.exists() for path in scripts),
        "安全边界": {
            "触发执行器": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "重启19300": False,
            "重启19302": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 后续低风险队列补充与状态观察",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前调度状态：{report['当前调度状态']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 候选任务",
        "",
    ]
    for item in report["候选任务"]:
        lines.append(f"- {item['编号']} {item['任务']}：{item['自动级别']}；脚本齐备={item['脚本齐备']}；{item['判定原因']}")
    lines.extend(["", "## 阻断项", ""])
    for item in report["阻断项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 本轮建议", ""])
    for item in report["本轮建议"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    rule = load_json(RULE_PATH)
    plan = load_json(PLAN_PACKAGE)
    schedule = load_json(SCHEDULE_STATE)
    task_queue = load_json(TASK_QUEUE)
    current_queue = load_json(CURRENT_QUEUE)
    current_state = schedule.get("当前状态", "未知")
    heavy_load = "重负载" in current_state or "避让" in current_state

    candidates = [
        build_candidate(
            "LR001",
            "企业微信助手统一路由状态基线",
            "02扩展/企业微信助手",
            "只读运行状态摘要、统一指令路由预演和速查卡验收，不真实发送企业微信。",
            [
                EXTENSION / "06企业微信助手系统" / "02脚本" / "生成企业微信助手系统状态摘要.py",
                EXTENSION / "06企业微信助手系统" / "02脚本" / "验证企业微信助手系统状态摘要.py",
                EXTENSION / "06企业微信助手系统" / "02脚本" / "验证企业微信统一指令路由预演.py",
                EXTENSION / "06企业微信助手系统" / "02脚本" / "验证企业微信统一指令使用速查卡.py",
            ],
            "允许自动",
            "当前只做状态基线和本地预演，不触发真实发送。",
        ),
        build_candidate(
            "LR002",
            "知识库可追溯问答只读基线",
            "01智能/知识库",
            "刷新知识库状态摘要、检索增强链路和本地问答预演验收；不写正式库。",
            [
                INTELLIGENCE / "02脚本" / "生成知识库系统状态摘要.py",
                INTELLIGENCE / "02脚本" / "验证知识库系统状态摘要.py",
                INTELLIGENCE / "02脚本" / "验证知识库本地问答预演.py",
                INTELLIGENCE / "02脚本" / "验证知识库检索增强链路.py",
            ],
            "允许自动" if not heavy_load else "允许只读观察",
            "用户重负载时只允许轻量状态观察，避免模型重任务。",
        ),
        build_candidate(
            "LR003",
            "总管小流量执行器只读门禁复核",
            "00总管",
            "验证首批执行器就绪总表和小流量只读方案，不触发执行器。",
            [
                MANAGER / "02脚本" / "验证首批执行器就绪总表.py",
                MANAGER / "02脚本" / "验证小流量只读执行方案.py",
                MANAGER / "02脚本" / "验证小流量只读执行前快照.py",
                MANAGER / "02脚本" / "验证小流量只读执行后观测模板.py",
            ],
            "允许自动",
            "只验证门禁和模板，不执行任务。",
        ),
        build_candidate(
            "LR004",
            "进化系统复盘材料状态基线",
            "03进化",
            "刷新进化系统状态摘要、复盘报告和经验卡片候选模板。",
            [
                EVOLUTION / "02脚本" / "生成进化系统状态摘要.py",
                EVOLUTION / "02脚本" / "验证进化系统状态摘要.py",
                EVOLUTION / "02脚本" / "生成进化复盘报告.py",
                EVOLUTION / "02脚本" / "生成巡检结果经验卡片候选模板.py",
                EVOLUTION / "02脚本" / "验证巡检结果经验卡片候选模板.py",
            ],
            "允许自动",
            "只生成复盘材料和候选模板，不把临时经验直接写成总纲规则。",
        ),
        build_candidate(
            "BLOCK001",
            "正式微信短文生成器替换运行入口",
            "02股票扩展/00总管",
            "涉及正式入口替换，必须停下报告。",
            [],
            "必须停下报告",
            "会影响企业微信股票回复正式链路。",
        ),
    ]

    allowed = [item for item in candidates if item["自动级别"] in ("允许自动", "允许只读观察") and item["脚本齐备"]]
    missing = [item for item in candidates if item["自动级别"] in ("允许自动", "允许只读观察") and not item["脚本齐备"]]
    blockers = [item["任务"] for item in candidates if item["自动级别"] == "必须停下报告"]
    if missing:
        blockers.extend([f"{item['任务']} 脚本未齐备，仅登记缺口。" for item in missing])

    report = {
        "名称": "后续低风险队列补充与状态观察",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前调度状态": current_state,
        "当前结论": "后续低风险候选清单已生成；当前优先选择脚本齐备、只读或本地预演任务，正式入口替换继续阻断。",
        "依据": {
            "无干扰规则": str(RULE_PATH),
            "计划工作模式开工包": str(PLAN_PACKAGE),
            "日常调度状态": str(SCHEDULE_STATE),
            "任务队列调度": str(TASK_QUEUE),
            "无干扰队列": str(CURRENT_QUEUE),
        },
        "规则摘要": {
            "允许自动执行": rule.get("允许自动执行", []),
            "必须停下报告": rule.get("必须停下报告", []),
        },
        "计划主线": plan.get("下阶段主线") or plan.get("下阶段主线列表") or [],
        "任务队列摘要": task_queue,
        "当前无干扰建议": current_queue.get("本轮建议执行", {}),
        "候选任务": candidates,
        "可自动候选数量": len(allowed),
        "脚本缺口候选数量": len(missing),
        "阻断项": blockers,
        "本轮建议": [
            "优先执行 LR001 企业微信助手统一路由状态基线，因为它只做本地状态和路由预演，不运行模型重任务。",
            "用户重负载避让期间，LR002 知识库只做状态观察，不启动批量问答或入库。",
            "LR003 仅验证小流量只读门禁，不触发执行器。",
            "LR004 可生成进化复盘材料，但不得把临时经验直接写成总纲规则。",
            "BLOCK001 正式微信短文生成器替换运行入口继续必须停下报告。",
        ],
        "安全边界": {
            "触发执行器": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "重启19300": False,
            "重启19302": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    latest_json = OUT_DIR / "后续低风险队列补充与状态观察_最新.json"
    latest_md = OUT_DIR / "后续低风险队列补充与状态观察_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "当前结论": report["当前结论"],
        "可自动候选数量": report["可自动候选数量"],
        "脚本缺口候选数量": report["脚本缺口候选数量"],
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
