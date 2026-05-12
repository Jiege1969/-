# -*- coding: utf-8 -*-
"""
名称：生成股票n8n长期观察模型与时段调度策略包.py
作用：把股票三线模型路由、收市后分析窗口、夜间长期观察窗口固化为n8n灰度调度策略。
触发方式：python 生成股票n8n长期观察模型与时段调度策略包.py
依赖：Python标准库；股票三线分析与模型路由配置；L5AI分析报告规则；盘后批处理资源预算规则；个人智能母系统日常调度规则。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写本地259策略包；不修改正式模型路由；不导入n8n；不启用n8n；不真实发送企业微信；不调用券商接口；不自动交易；不重载服务。
标识：stock-n8n-long-observation-model-schedule-package-generate
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


def manager_root() -> Path:
    return project_root() / "00杰哥系统总管"


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
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def build_model_schedule(routes: dict[str, Any], l5_rule: dict[str, Any], resource_rule: dict[str, Any]) -> list[dict[str, Any]]:
    lines = routes.get("分析线", {})
    l5_models = l5_rule.get("模型路由", {})
    resource_models = resource_rule.get("模型调用策略", {})
    return [
        {
            "阶段": "收市后轻扫描",
            "建议时间": "15:40-17:30",
            "主要任务": "行情快照、技术指标、分层评分、候选提取。",
            "模型策略": "全样本池不调用大模型；只做结构化指标和规则评分。",
            "依据": resource_models.get("全样本池", ""),
            "n8n角色": "可定时触发本地脚本，但初始保持未激活或手动执行。",
            "推送": "不推送，产出候选和本地报告。",
        },
        {
            "阶段": "收市后报告生成",
            "建议时间": "18:00-21:30",
            "主要任务": "对少量L5深度研究池和重点关注池生成结构化分析报告。",
            "模型策略": {
                "默认分析模型": l5_models.get("默认分析模型", "qwen3:14b"),
                "复杂风险模型": l5_models.get("复杂推理模型", "deepseek-r1:32b"),
                "快速兜底模型": l5_models.get("快速兜底模型", "qwen2.5:7b"),
                "触发条件": l5_models.get("复杂触发条件", {}),
            },
            "n8n角色": "触发本地研究闭环，生成推送草案和发送前检查。",
            "推送": "只进入本人单条灰度闸口，不群发。",
        },
        {
            "阶段": "夜间长期观察",
            "建议时间": "00:30-05:30",
            "主要任务": "复盘样本、报告质量观察、用户反馈归纳、长期跟踪样本更新。",
            "模型策略": {
                "专家线主模型候选": lines.get("专家线", {}).get("模型路由", {}).get("主模型候选", ["deepseek-r1:32b", "qwen3:30b"]),
                "专家线兜底模型": lines.get("专家线", {}).get("模型路由", {}).get("兜底模型", "qwen3:14b"),
                "金融复核主模型": lines.get("金融复核线", {}).get("模型路由", {}).get("主模型", "mychen76/Fin-R1:Q5"),
                "金融交叉对照模型": lines.get("金融复核线", {}).get("模型路由", {}).get("交叉对照模型", "martain7r/finance-llama-8b:q4_k_m"),
                "归纳模型": lines.get("金融复核线", {}).get("模型路由", {}).get("归纳模型", "qwen3:14b"),
            },
            "n8n角色": "适合做长任务编排和低峰资源调度，结果写入本地观察账和进化候选。",
            "推送": "默认不夜间推送；仅写本地，次日汇总给使用者看。",
        },
        {
            "阶段": "用户即时问答",
            "建议时间": "全天，但交易保护窗口轻量优先",
            "主要任务": "用户临时问某只股票或系统状态。",
            "模型策略": lines.get("助手线", {}).get("模型路由", {}),
            "n8n角色": "不参与即时问答主链路，避免增加延迟。",
            "推送": "被动回复或单条灰度，不扩面。",
        },
    ]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票n8n长期观察模型与时段调度策略包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 调度策略",
        "",
    ]
    for item in report["模型与时段策略"]:
        lines.append(f"### {item['阶段']}")
        lines.append(f"- 建议时间：{item['建议时间']}")
        lines.append(f"- 主要任务：{item['主要任务']}")
        lines.append(f"- n8n角色：{item['n8n角色']}")
        lines.append(f"- 推送：{item['推送']}")
        lines.append("")
    lines.extend([
        "## 关键原则",
        "",
        "- 收市后生成股票报告，避免盘中重模型压正式入口。",
        "- 半夜跑长期观察、复盘归纳和金融专业模型复核。",
        "- 专业金融模型用于证据解释和公司质量复核，不直接给交易指令。",
        "- n8n是调度器，不是判断核心；模型路由仍由股票系统配置决定。",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    manager = manager_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    paths = {
        "股票三线模型路由": root / "01配置" / "股票三线分析与模型路由配置.json",
        "L5AI分析报告规则": root / "01配置" / "L5AI分析报告规则.json",
        "盘后批处理资源预算规则": root / "01配置" / "盘后批处理资源预算规则.json",
        "个人智能母系统日常调度规则": manager / "01配置" / "个人智能母系统日常调度规则.json",
        "模型资源池登记": manager / "03数据" / "模型资源池" / "模型资源池登记_最新.json",
        "股票模型健康检查": root / "03数据" / "148模型健康检查" / "股票系统模型健康检查_最新.json",
    }
    routes = load_json(paths["股票三线模型路由"], {})
    l5_rule = load_json(paths["L5AI分析报告规则"], {})
    resource_rule = load_json(paths["盘后批处理资源预算规则"], {})
    daily_rule = load_json(paths["个人智能母系统日常调度规则"], {})
    model_pool = load_json(paths["模型资源池登记"], {})
    model_health = load_json(paths["股票模型健康检查"], {})

    report = {
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "包名": "股票n8n长期观察模型与时段调度策略包",
        "当前结论": "股票n8n长期观察应按收市后报告、夜间长期观察、即时问答轻量化三类任务分时调用不同模型；n8n是调度器，不是判断核心。",
        "使用者要求吸收": [
            "股票分析应在收市后进行。",
            "长期观察应放在半夜，利用用户休息时的空闲算力。",
            "股票分析应优先使用专业模型和既有模型路由。",
            "系统已具备按任务调用不同模型的基础，本包把该能力纳入n8n调度策略。",
        ],
        "来源文件状态": {name: file_state(path) for name, path in paths.items()},
        "模型与时段策略": build_model_schedule(routes, l5_rule, resource_rule),
        "n8n灰度调度建议": {
            "工作流初始状态": "active=false",
            "建议触发窗口": [
                {"名称": "收市轻扫描", "时间": "15:40", "动作": "只做结构化扫描，不调用全量大模型"},
                {"名称": "收市报告生成", "时间": "18:30", "动作": "少量候选调用qwen3/deepseek生成报告草案"},
                {"名称": "夜间长期观察", "时间": "00:30", "动作": "调用金融专业模型和复盘归纳，写本地候选"},
                {"名称": "次日摘要准备", "时间": "06:30", "动作": "整理给使用者看的观察摘要，不夜间打扰"},
            ],
            "真实发送要求": "另走本人单条灰度发送确认令；n8n调度策略本身不放行真实发送。",
        },
        "专业模型使用原则": [
            "金融专业模型只做证据解释、公司质量复核和风险复核，不直接给交易指令。",
            "复杂推理模型优先放在收市后或夜间，不在开市保护窗口抢占正式入口资源。",
            "轻量问答使用助手线主模型或兜底模型，避免把所有问题都交给重模型。",
        ],
        "模型资源摘要": {
            "模型资源池文件存在": paths["模型资源池登记"].exists(),
            "股票模型健康文件存在": paths["股票模型健康检查"].exists(),
            "模型资源池类型": type(model_pool).__name__,
            "模型健康类型": type(model_health).__name__,
        },
        "资源避让继承": {
            "来源": str(paths["个人智能母系统日常调度规则"]),
            "交易保护窗口": "09:00-15:30只允许轻量待命，禁止重模型批量分析。",
            "收市股票分析": "15:30-18:30优先股票数据采集、分层日报、推荐报告和质检旁路。",
            "夜间维护进化": "22:00-06:00适合复盘学习、影子试验和低风险维护。",
            "资源阈值": daily_rule.get("资源避让阈值", {}),
        },
        "安全边界": {
            "修改正式模型路由": False,
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
            "读取现有模型路由配置": True,
            "读取现有调度规则": True,
            "写本地259策略包": True,
            "修改正式模型路由": False,
            "导入n8n": False,
            "启用n8n工作流": False,
            "触发n8n": False,
            "真实发送企业微信": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    out_dir = root / "03数据" / "259股票n8n长期观察模型与时段调度策略包"
    log_dir = root / "04日志" / "股票n8n长期观察模型与时段调度策略包"
    output_json = out_dir / f"股票n8n长期观察模型与时段调度策略包_{stamp}.json"
    latest_json = out_dir / "股票n8n长期观察模型与时段调度策略包_最新.json"
    output_md = out_dir / f"股票n8n长期观察模型与时段调度策略包_{stamp}.md"
    latest_md = out_dir / "股票n8n长期观察模型与时段调度策略包_最新.md"
    log_json = log_dir / f"stock-n8n-long-observation-model-schedule-package-{stamp}.json"
    log_latest = log_dir / "stock-n8n-long-observation-model-schedule-package-最新.json"

    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_json(log_json, {"生成时间": report["生成时间"], "输出": str(latest_json), "安全边界": report["安全边界"]})
    write_json(log_latest, load_json(log_json, {}))
    print(json.dumps({"状态": "完成", "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
