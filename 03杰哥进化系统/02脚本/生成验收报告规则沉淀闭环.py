# -*- coding: utf-8 -*-
"""
名称：生成验收报告规则沉淀闭环.py
作用：只读股票系统和总管系统验收报告，提取可沉淀规则，并生成“问题 -> 复盘 -> 规则 -> 下次施工约束”闭环包。
触发方式：python 生成验收报告规则沉淀闭环.py
依赖：Python标准库；验收报告规则沉淀规则.json。
所属系统：03杰哥进化系统
安全边界：只读取其他系统验收结果；只写入03杰哥进化系统数据目录；不修改股票系统业务脚本，不修改总管进度口径，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建验收报告规则沉淀闭环生成脚本。
标识：evolution-acceptance-rule-loop-generate
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return system_root().parents[0]


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


def output_dir() -> Path:
    return system_root() / "03数据" / "08规则沉淀"


def is_backup_path(path: Path) -> bool:
    text = str(path)
    return "\\备份\\" in text or "/备份/" in text or "\\05备份\\" in text or "/05备份/" in text


def source_report_paths() -> list[Path]:
    root = project_root()
    stock_data = root / "02杰哥扩展系统" / "01股票研究系统" / "03数据"
    manager_state = root / "00杰哥系统总管" / "03数据" / "运行状态"
    paths: list[Path] = []
    if stock_data.exists():
        paths.extend(path for path in stock_data.rglob("*验收_最新.json") if not is_backup_path(path))
    if manager_state.exists():
        paths.extend(path for path in manager_state.glob("*验收_最新.json") if not is_backup_path(path))
    return sorted(paths, key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)


def report_status(report: dict[str, Any]) -> tuple[bool, int, int]:
    failed = int(report.get("失败数量", report.get("汇总", {}).get("失败", 0)) or 0)
    passed = int(report.get("通过数量", report.get("汇总", {}).get("通过", 0)) or 0)
    conclusion = str(report.get("结论", report.get("判定", "")))
    ok = failed == 0 and (conclusion in {"通过", "healthy", ""} or passed > 0)
    return ok, passed, failed


def text_of(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def match_categories(report: dict[str, Any], rules: dict[str, Any]) -> list[str]:
    text = text_of(report)
    categories = []
    for item in rules.get("规则分类关键词", []):
        if any(keyword in text for keyword in item.get("关键词", [])):
            categories.append(item.get("分类", "未分类"))
    return categories


def inventory_evolution_assets() -> dict[str, Any]:
    root = system_root()
    all_files = [item for item in root.rglob("*") if item.is_file() and "__pycache__" not in str(item)]
    keyword_files = []
    for item in all_files:
        name = item.name
        if any(keyword in name for keyword in ["复盘", "评审", "规则", "固化", "经验", "验收", "闭环"]):
            keyword_files.append(str(item))
    return {
        "配置文件数": len(list((root / "01配置").glob("*.json"))),
        "脚本数": len(list((root / "02脚本").glob("*.py"))),
        "文档数": len(list((root / "07文档").rglob("*.md"))),
        "经验卡片数": len(list((root / "03数据").rglob("*经验*.md"))) + len(list((root / "03数据").rglob("*经验*.json"))),
        "验收日志数": len(list((root / "04日志").rglob("*.json"))),
        "复盘评审规则固化相关文件数": len(keyword_files),
        "复盘评审规则固化相关文件样例": keyword_files[:30],
    }


RULE_LIBRARY: dict[str, dict[str, str]] = {
    "高风险动作默认关闭": {
        "问题": "真实发送、n8n、写库、券商接口、自动交易和服务重启容易在联调或验收口径中被误认为可直接执行。",
        "复盘": "股票与总管验收报告反复把这些动作写入安全边界，并要求默认全部为False或保持关闭。",
        "规则": "所有高风险动作默认关闭；进化系统只能把它们固化为检查项、禁止项和人工确认提示，不能代替业务系统放行。",
        "下次施工约束": "下次施工前先读取安全边界字段；若出现真实发送、触发n8n、写库、券商接口、自动交易或服务重启，必须停下等待人工确认。",
        "固化级别": "可自动固化为进化系统检查项",
    },
    "影子与dry-run先行": {
        "问题": "正式模板、正式口径或发送链路若直接切换，会把未验证输出带入业务入口。",
        "复盘": "股票验收报告采用shadow、dry-run、预演和草稿对照，证明结果可用但不改变默认正式行为。",
        "规则": "涉及正式入口、模板、口径或发送链路的变化，必须先走影子或dry-run，并保留旧输出用于对照。",
        "下次施工约束": "只要报告出现影子、dry-run、预演或草稿，下一步只能进入小样本验收或准入方案，不能直接切默认正式入口。",
        "固化级别": "可自动固化为进化系统检查项",
    },
    "上游验收闸口": {
        "问题": "单点验收通过容易掩盖上游证据不足、链路断点或前置任务未完成。",
        "复盘": "发送准入和阶段收口报告都要求读取上游验收，并检查失败数量为0。",
        "规则": "下游准入必须显式列出上游验收、存在性、结论、通过数量和失败数量。",
        "下次施工约束": "任何准入包缺少上游验收清单，或任一上游失败数量不为0，均不得进入下一阶段。",
        "固化级别": "可自动固化为进化系统检查项",
    },
    "人工确认闸口": {
        "问题": "系统能生成方案不等于用户已经同意真实执行。",
        "复盘": "早期人工确认闸口用于避免系统不完善时误动真实业务；现在应纠偏为风险分级，不能卡住低风险本地施工。",
        "规则": "人工确认只约束真实发送、P4真实清理、入口替换、默认模板切换或生产权限扩大；03本地规则沉淀、验收脚本、报告生成和文档同步自动继续。",
        "下次施工约束": "缺少用户明确确认记录时，仍可继续只读复核、灰度方案、回滚演练、小样本验收和03本地规则固化；不得执行高风险真实动作。",
        "固化级别": "风险分级后固化",
    },
    "回滚与停止开关": {
        "问题": "没有停止开关和回滚路径的方案，失败后无法及时收束影响。",
        "复盘": "回滚与停止开关应服务持续推进，而不是把所有后续动作一刀切拦住。",
        "规则": "任何可能改变正式输出或真实动作的方案，必须同时给出停止开关、回滚对象、日志证据和恢复边界；本地方案、检查和演练可自动推进。",
        "下次施工约束": "没有回滚或停止开关的方案，不得进入真实执行或默认切换；但可以继续补齐回滚方案、停止开关和验收脚本。",
        "固化级别": "风险分级后固化",
    },
    "证据来源与降级边界": {
        "问题": "报告内容若混用估算、影子数据和正式依据，会让用户误判可信度。",
        "复盘": "股票短回复验收要求正式成交额阈值、公开数据来源、不含估算降级，并保留不自动交易声明。",
        "规则": "报告必须区分正式依据、影子口径、估算降级和仍缺依据字段；高风险结论必须保留来源说明。",
        "下次施工约束": "若来源字段缺失或出现估算降级，下一步只能标记为观察、补证据或人工复核，不得提升推荐等级。",
        "固化级别": "可自动固化为进化系统检查项",
    },
    "分阶段治理": {
        "问题": "清理、归档、合并、入口替换若一步到位，容易误动业务资产。",
        "复盘": "总管验收把治理拆为P1影子删除、P2影子归档、P3合并预演和P4受控真实动作。",
        "规则": "治理类动作必须先候选清单、引用检查、影子包、备份回滚和验收，再讨论受控真实动作。",
        "下次施工约束": "P1-P3报告不得被解释为P4授权；P4必须单独有人工确认、备份、回滚和运行窗口。",
        "固化级别": "可自动固化为进化系统检查项",
    },
    "只读沉淀不反向覆盖": {
        "问题": "进化系统读取其他系统结果时，容易越界修改业务输出或进度口径。",
        "复盘": "现有进化系统总则规定只生成建议和草案；本轮任务也要求进化系统只能读取其他系统结果并沉淀规则。",
        "规则": "进化系统对外部系统只读；产物只写入03进化系统，不反向覆盖股票、总管或智能系统业务输出。",
        "下次施工约束": "任何规则沉淀只能落在03目录；需要修改业务脚本、总管进度口径或生产提示词时，必须作为阻断点报告。",
        "固化级别": "可自动固化为进化系统检查项",
    },
}


def build_rule_items(source_summaries: list[dict[str, Any]], category_counter: Counter[str]) -> list[dict[str, Any]]:
    items = []
    for category, template in RULE_LIBRARY.items():
        source_hits = [
            {
                "报告名称": item["报告名称"],
                "路径": item["路径"],
                "结论": item["结论"],
                "通过数量": item["通过数量"],
                "失败数量": item["失败数量"],
            }
            for item in source_summaries
            if category in item["命中分类"]
        ]
        if category == "只读沉淀不反向覆盖" and not source_hits:
            source_hits = []
        if source_hits or category == "只读沉淀不反向覆盖":
            solidify = template["固化级别"]
            items.append(
                {
                    "规则ID": f"EVR-{len(items) + 1:03d}",
                    "规则分类": category,
                    "问题": template["问题"],
                    "复盘": template["复盘"],
                    "规则": template["规则"],
                    "下次施工约束": template["下次施工约束"],
                    "固化级别": solidify,
                    "可自动固化": solidify.startswith("可自动") or solidify.startswith("风险分级"),
                    "仍需人工确认": solidify.startswith("需人工") or solidify.startswith("风险分级"),
                    "来源报告数量": len(source_hits),
                    "来源报告": source_hits[:8],
                    "命中强度": int(category_counter.get(category, 0)),
                }
            )
    return items


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 验收报告规则沉淀闭环",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 来源报告数量：{report['来源报告数量']}",
        f"- 通过报告数量：{report['通过报告数量']}",
        f"- 提取规则数量：{report['提取规则数量']}",
        f"- 自动固化候选：{len(report['自动固化规则'])}",
        f"- 需人工确认：{len(report['人工确认规则'])}",
        "",
        "## 已提取规则",
        "",
    ]
    for item in report["提取规则"]:
        lines.extend(
            [
                f"### {item['规则ID']} {item['规则分类']}",
                f"- 问题：{item['问题']}",
                f"- 复盘：{item['复盘']}",
                f"- 规则：{item['规则']}",
                f"- 下次施工约束：{item['下次施工约束']}",
                f"- 固化级别：{item['固化级别']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 安全边界",
            "",
            "- 不修改股票系统业务脚本。",
            "- 不修改总管进度口径。",
            "- 不发送企业微信、不触发n8n、不调用券商接口、不自动交易。",
            "- 进化系统只读其他系统验收结果并沉淀规则，不反向覆盖业务输出。",
            "",
        ]
    )
    return "\n".join(lines)


def build_report() -> dict[str, Any]:
    root = system_root()
    rules = load_json(root / "01配置" / "验收报告规则沉淀规则.json", {})
    source_paths = source_report_paths()
    source_summaries = []
    category_counter: Counter[str] = Counter()
    for path in source_paths:
        report = load_json(path, {})
        ok, passed, failed = report_status(report)
        categories = match_categories(report, rules)
        category_counter.update(categories)
        source_summaries.append(
            {
                "报告名称": report.get("名称", path.stem),
                "路径": str(path),
                "结论": report.get("结论", report.get("判定", "")),
                "通过": ok,
                "通过数量": passed,
                "失败数量": failed,
                "命中分类": categories,
                "安全边界": report.get("安全边界", {}),
            }
        )

    rule_items = build_rule_items(source_summaries, category_counter)
    auto_rules = [item for item in rule_items if item["可自动固化"]]
    manual_rules = [item for item in rule_items if item["仍需人工确认"]]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "生成时间": now,
        "类型": "evolution-acceptance-rule-loop",
        "所属系统": "03杰哥进化系统",
        "输入边界": "只读股票系统和总管系统验收报告",
        "输出边界": "只写入03杰哥进化系统/03数据/08规则沉淀和04日志",
        "现有资产盘点": inventory_evolution_assets(),
        "来源报告数量": len(source_summaries),
        "通过报告数量": sum(1 for item in source_summaries if item["通过"]),
        "失败报告数量": sum(1 for item in source_summaries if not item["通过"]),
        "分类命中统计": dict(category_counter),
        "来源报告样本": source_summaries[:20],
        "提取规则数量": len(rule_items),
        "提取规则": rule_items,
        "自动固化规则": auto_rules,
        "人工确认规则": manual_rules,
        "小样本验收": {
            "样本来源": "最新股票验收报告和总管运行状态验收报告",
            "样本规则数量": len(rule_items),
            "闭环字段完整": all(all(key in item for key in ["问题", "复盘", "规则", "下次施工约束"]) for item in rule_items),
            "跨系统覆盖": {
                "股票系统报告": any("02杰哥扩展系统" in item["路径"] for item in source_summaries),
                "总管系统报告": any("00杰哥系统总管" in item["路径"] for item in source_summaries),
            },
            "判定": "通过" if len(rule_items) >= 6 else "需补样本",
        },
        "剩余有效工时估算": {
            "原基线": "18-30小时",
            "本轮后估算": "14-24小时",
            "减少原因": "已补齐验收报告规则抽取、规则分级、闭环报告和小样本验收底座。",
        },
        "交付阻塞": [
            "真实业务复盘样本仍需继续积累，尤其是股票复盘T+1/T+3/T+5反馈。",
            "自动规则固化只能落在进化系统本地检查项；涉及真实发送、P4真实动作、入口替换和总管进度口径仍需人工确认。",
            "规则命中目前以验收报告结构化字段和关键词为主，后续可补更细的语义标签和去重评分。",
        ],
        "安全边界": {
            "修改股票系统业务脚本": False,
            "修改总管进度口径": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "反向覆盖业务输出": False,
        },
    }

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = output_dir()
    output_json = out_dir / f"验收报告规则沉淀闭环_{timestamp}.json"
    latest_json = out_dir / "验收报告规则沉淀闭环_最新.json"
    output_md = out_dir / f"验收报告规则沉淀闭环_{timestamp}.md"
    latest_md = out_dir / "验收报告规则沉淀闭环_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"提取规则数量": len(rule_items), "输出": str(output_json), "摘要": str(output_md)}, ensure_ascii=True))
    return report


def main() -> int:
    report = build_report()
    return 0 if report["小样本验收"]["判定"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
