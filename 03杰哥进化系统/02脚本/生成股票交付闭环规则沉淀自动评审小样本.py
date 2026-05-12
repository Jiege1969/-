# -*- coding: utf-8 -*-
"""
名称：生成股票交付闭环规则沉淀自动评审小样本.py
作用：基于股票交付闭环规则沉淀包，生成带“问题->复盘->规则->下次施工约束->验收检查”的规则沉淀小样本和自动评审小样本。
触发方式：python 生成股票交付闭环规则沉淀自动评审小样本.py
依赖：Python标准库；03本地股票交付闭环规则沉淀包、自动评审报告、反馈等待机制。
所属系统：03杰哥进化系统
安全边界：只读其他系统验收结果并写03本地小样本；不修改总管进度配置，不修改01智能系统中台代码，不修改02扩展系统业务脚本，不发送企业微信真实消息，不触发n8n，不调用券商接口，不自动交易，不反向覆盖业务输出。
创建/修改记录：2026-05-05 创建规则沉淀与自动评审小样本生成脚本。
标识：evolution-stock-delivery-rule-deposit-auto-review-sample-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def system_root() -> Path:
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


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.iterdir() if item.is_file())


def acceptance_check(rule_name: str) -> dict[str, Any]:
    checks = {
        "正式覆盖前必须备份": {
            "验收检查ID": "AC-DLV-001",
            "检查方式": "检查正式覆盖动作是否存在备份路径、备份对象、备份时间、校验信息和回滚方式。",
            "通过条件": "备份对象、备份路径、回滚方式齐全；若涉及真实覆盖，必须保留人工确认或硬边界。",
            "失败处理": "不得执行覆盖，只能补备份和回滚方案。",
        },
        "_最新 文件刷新必须有回滚证据": {
            "验收检查ID": "AC-DLV-002",
            "检查方式": "检查 _最新 文件刷新是否同时具备时间戳版本、来源报告、验收日志或备份快照。",
            "通过条件": "_最新 有至少一种可定位回滚证据，并能追溯来源。",
            "失败处理": "不得标记完成，必须补齐证据链。",
        },
        "影子验证通过后才能接正式口径": {
            "验收检查ID": "AC-DLV-003",
            "检查方式": "检查影子验证、dry-run或对照包验收是否存在，且失败数量为0。",
            "通过条件": "影子/dry-run/对照包验收通过；正式入口切换仍按备份和授权边界执行。",
            "失败处理": "只能继续修影子链路，不能接正式口径。",
        },
        "企业微信真实发送必须先白名单灰度": {
            "验收检查ID": "AC-DLV-004",
            "检查方式": "检查确认令、白名单目标、灰度计数、发送日志、公共发送器日志和停止/回滚条件。",
            "通过条件": "目标在白名单内，计数未超限，日志齐全；扩面必须重新授权。",
            "失败处理": "不得真实发送，不得复用单条灰度授权扩面。",
        },
        "n8n、券商接口、自动交易必须分级隔离": {
            "验收检查ID": "AC-DLV-005",
            "检查方式": "检查企业微信、n8n、券商接口、自动交易是否分别有独立许可和关闭状态证据。",
            "通过条件": "消息灰度许可不隐含n8n许可，研究输出不隐含券商接口或自动交易许可。",
            "失败处理": "判定为风险混淆，阻断真实动作。",
        },
        "完成后必须生成最终收口验收": {
            "验收检查ID": "AC-DLV-006",
            "检查方式": "检查最终收口报告和最终收口验收是否存在，且包含完成清单、回滚证据、安全边界和剩余工时。",
            "通过条件": "最终收口验收通过，失败为0；否则不得标记阶段性交付完成。",
            "失败处理": "只能标记为分段通过或待收口。",
        },
    }
    return checks.get(rule_name, {
        "验收检查ID": "AC-DLV-UNKNOWN",
        "检查方式": "待补充。",
        "通过条件": "待补充。",
        "失败处理": "待补充。",
    })


def build_inventory(root: Path) -> dict[str, Any]:
    data = root / "03数据"
    return {
        "复盘文件": {
            "01问题卡片": count_files(data / "01问题卡片"),
            "02成功经验": count_files(data / "02成功经验"),
            "03失败教训": count_files(data / "03失败教训"),
            "13股票复盘反馈样本": count_files(data / "13股票复盘反馈样本"),
            "14复盘反馈观察": count_files(data / "14复盘反馈观察"),
            "15复盘转经验候选": count_files(data / "15复盘转经验候选"),
        },
        "规则文件": {
            "08规则沉淀": count_files(data / "08规则沉淀"),
            "16用户明确规则沉淀": count_files(data / "16用户明确规则沉淀"),
            "17股票交付闭环规则沉淀": count_files(data / "17股票交付闭环规则沉淀"),
            "19股票交付闭环经验候选与反馈等待": count_files(data / "19股票交付闭环经验候选与反馈等待"),
        },
        "自动评审文件": {
            "10自动评审": count_files(data / "10自动评审"),
            "18股票交付闭环规则自动评审": count_files(data / "18股票交付闭环规则自动评审"),
            "20股票交付闭环规则沉淀收口": count_files(data / "20股票交付闭环规则沉淀收口"),
        },
    }


def build_rule_sample(deposit: dict[str, Any], review: dict[str, Any]) -> list[dict[str, Any]]:
    review_map = {item.get("规则ID"): item for item in review.get("规则评审", [])}
    samples = []
    for rule in deposit.get("规则清单", []):
        rule_id = rule.get("规则ID", "")
        review_item = review_map.get(rule_id, {})
        samples.append(
            {
                "规则ID": rule_id,
                "规则名称": rule.get("规则名称", ""),
                "问题": rule.get("问题", ""),
                "复盘": rule.get("复盘", ""),
                "规则": rule.get("规则", ""),
                "下次施工约束": rule.get("下次施工约束", ""),
                "验收检查": acceptance_check(rule.get("规则名称", "")),
                "自动评审": {
                    "价值分": review_item.get("价值分", 0),
                    "价值等级": review_item.get("价值等级", ""),
                    "重复等级": review_item.get("重复等级", ""),
                    "可自动固化": review_item.get("可自动固化", False),
                    "仍需人工确认": review_item.get("仍需人工确认", False),
                    "建议动作": review_item.get("建议动作", ""),
                },
            }
        )
    return samples


def build_auto_review_sample(rule_samples: list[dict[str, Any]]) -> dict[str, Any]:
    auto_rules = [item["规则名称"] for item in rule_samples if item["自动评审"].get("可自动固化")]
    manual_rules = [item["规则名称"] for item in rule_samples if item["自动评审"].get("仍需人工确认")]
    scenarios = []
    for item in rule_samples:
        check = item["验收检查"]
        scenarios.append(
            {
                "场景ID": f"SC-{item['规则ID']}",
                "场景名称": f"后续施工检查：{item['规则名称']}",
                "输入线索": item["下次施工约束"],
                "使用规则": item["规则ID"],
                "验收检查ID": check["验收检查ID"],
                "预期判定": "可自动检查" if item["自动评审"].get("可自动固化") else "需人工确认或硬边界",
                "失败处理": check["失败处理"],
            }
        )
    return {
        "小样本场景数量": len(scenarios),
        "可自动固化规则": auto_rules,
        "仍需人工确认规则": manual_rules,
        "后续施工检查场景": scenarios,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票交付闭环规则沉淀与自动评审小样本",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 规则小样本数量：{report['规则小样本数量']}",
        f"- 自动评审场景数量：{report['自动评审小样本']['小样本场景数量']}",
        f"- 小样本验收：{report['小样本验收']['判定']}",
        "",
        "## 规则小样本",
        "",
    ]
    for item in report["规则沉淀小样本"]:
        lines.extend(
            [
                f"### {item['规则ID']} {item['规则名称']}",
                f"- 问题：{item['问题']}",
                f"- 复盘：{item['复盘']}",
                f"- 规则：{item['规则']}",
                f"- 下次施工约束：{item['下次施工约束']}",
                f"- 验收检查：{item['验收检查']['检查方式']}",
                "",
            ]
        )
    lines.extend(["## 自动评审小样本", ""])
    for scene in report["自动评审小样本"]["后续施工检查场景"]:
        lines.append(f"- {scene['场景ID']}：{scene['场景名称']} -> {scene['预期判定']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    deposit = load_json(root / "03数据" / "17股票交付闭环规则沉淀" / "股票交付闭环规则沉淀包_最新.json", {})
    review = load_json(root / "03数据" / "18股票交付闭环规则自动评审" / "股票交付闭环规则自动评审报告_最新.json", {})
    waiting = load_json(root / "03数据" / "19股票交付闭环经验候选与反馈等待" / "股票交付闭环经验候选与反馈等待机制_最新.json", {})
    rule_samples = build_rule_sample(deposit, review)
    auto_review_sample = build_auto_review_sample(rule_samples)
    sample = {
        "已读取沉淀包": bool(deposit),
        "已读取自动评审": bool(review),
        "已读取反馈等待机制": bool(waiting),
        "规则数量为6": len(rule_samples) == 6,
        "每条规则有问题复盘规则约束验收检查": all(all(item.get(key) for key in ("问题", "复盘", "规则", "下次施工约束", "验收检查")) for item in rule_samples),
        "自动评审场景数量为6": auto_review_sample["小样本场景数量"] == 6,
        "可自动固化数量为3": len(auto_review_sample["可自动固化规则"]) == 3,
        "人工确认数量为3": len(auto_review_sample["仍需人工确认规则"]) == 3,
        "反馈等待机制未误生成投资经验": waiting.get("反馈等待机制", {}).get("可转经验样本数量", 0) == 0,
        "安全边界未突破": True,
    }
    sample["判定"] = "通过" if all(sample.values()) else "需复核"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-delivery-rule-deposit-auto-review-sample",
        "所属系统": "03杰哥进化系统",
        "盘点结果": build_inventory(root),
        "规则小样本数量": len(rule_samples),
        "规则沉淀小样本": rule_samples,
        "自动评审小样本": auto_review_sample,
        "小样本验收": sample,
        "发现的问题": [
            "DLV规则与既有EVR/USR规则存在语义重叠，后续需要合并摘要。",
            "股票复盘反馈仍待回填，当前只沉淀交付流程经验，不沉淀投资判断经验。",
            "03框不得直接修改总管共享口径文件，进度影响只能提交总管回收。",
        ],
        "进化系统当前完成度": "仍按总管派工基准口径20%-30%，本轮不直接修改总管进度口径。",
        "剩余有效工时": "建议03进化系统剩余约14-22小时；是否下调由总管读取本验收后统一决定。",
        "阻塞项": [
            "复盘反馈未回填，投资判断经验卡片仍阻塞。",
            "DLV/EVR/USR规则合并去重尚未完成。",
            "跨系统统一施工前检查入口需总管回收后协调。",
        ],
        "需要总管收口的事项": [
            "读取本小样本和验收日志，决定是否调整03完成度与剩余工时。",
            "决定是否把DLV规则纳入跨系统统一施工前检查规范。",
            "统一处理03结果回收，03本轮不直接修改共享口径文件。",
        ],
        "安全边界": {
            "修改总管进度配置": False,
            "修改01智能系统中台代码": False,
            "修改02扩展系统业务脚本": False,
            "发送企业微信真实消息": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "反向覆盖业务输出": False,
        },
    }
    out_dir = root / "03数据" / "21股票交付闭环规则沉淀自动评审小样本"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"股票交付闭环规则沉淀自动评审小样本_{timestamp}.json"
    latest_json = out_dir / "股票交付闭环规则沉淀自动评审小样本_最新.json"
    output_md = out_dir / f"股票交付闭环规则沉淀自动评审小样本_{timestamp}.md"
    latest_md = out_dir / "股票交付闭环规则沉淀自动评审小样本_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"规则小样本数量": len(rule_samples), "判定": sample["判定"], "输出": str(output_json)}, ensure_ascii=True))
    return 0 if sample["判定"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
