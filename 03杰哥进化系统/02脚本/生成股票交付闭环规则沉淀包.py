# -*- coding: utf-8 -*-
"""
名称：生成股票交付闭环规则沉淀包.py
作用：读取股票系统237/241/242交付闭环证据，生成03进化系统可复用的交付闭环规则沉淀包。
触发方式：python 生成股票交付闭环规则沉淀包.py
依赖：Python标准库；股票交付闭环规则沉淀规则.json；股票系统237/241/242最新验收证据。
所属系统：03杰哥进化系统
安全边界：只读股票系统验收结果，只写03进化系统本地规则沉淀包；不修改股票系统核心脚本，不修改总管进度口径，不修改知识库问答代码，不发送企业微信，不触发n8n，不调用外部正式发送接口，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建股票交付闭环规则沉淀生成脚本。
标识：evolution-stock-delivery-loop-rule-deposit-generate
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


def path_from_config(raw_path: str) -> Path:
    return Path(raw_path.replace("/", "\\"))


def passed_count(report: dict[str, Any]) -> int:
    for key in ("通过数量", "通过"):
        value = report.get(key)
        if isinstance(value, int):
            return value
    summary = report.get("汇总", {})
    if isinstance(summary, dict) and isinstance(summary.get("通过"), int):
        return summary["通过"]
    return 0


def failed_count(report: dict[str, Any]) -> int:
    for key in ("失败数量", "失败"):
        value = report.get(key)
        if isinstance(value, int):
            return value
    summary = report.get("汇总", {})
    if isinstance(summary, dict) and isinstance(summary.get("失败"), int):
        return summary["失败"]
    return 0


def conclusion(report: dict[str, Any]) -> str:
    return str(report.get("总结论") or report.get("结论") or "")


def build_evidence_summary(evidence: dict[str, dict[str, Any]]) -> dict[str, Any]:
    report_237 = evidence.get("237交付闭环报告", {})
    verify_237 = evidence.get("237交付闭环验收", {})
    report_241 = evidence.get("241灰度发送报告", {})
    verify_241 = evidence.get("241灰度发送验收", {})
    report_242 = evidence.get("242最终收口报告", {})
    verify_242 = evidence.get("242最终收口验收", {})
    return {
        "237交付闭环": {
            "总结论": conclusion(report_237),
            "验收结论": conclusion(verify_237),
            "验收通过": passed_count(verify_237),
            "验收失败": failed_count(verify_237),
            "引用验收数量": len(report_237.get("验收结果", [])),
            "回滚证据数量": len(report_237.get("回滚证据", [])),
            "本轮备份文件数": report_237.get("安全边界", {}).get("本轮备份文件数", 0),
        },
        "241白名单灰度": {
            "总结论": conclusion(report_241),
            "验收结论": conclusion(verify_241),
            "验收通过": passed_count(verify_241),
            "验收失败": failed_count(verify_241),
            "真实发送成功": report_241.get("真实发送成功"),
            "目标用户": report_241.get("目标用户"),
            "当天计数": report_241.get("当天计数"),
            "确认令有效": report_241.get("关键证据", {}).get("确认令有效"),
            "目标用户本人白名单": report_241.get("关键证据", {}).get("目标用户本人白名单"),
            "计数未超限": report_241.get("关键证据", {}).get("计数未超限"),
        },
        "242最终收口": {
            "总结论": conclusion(report_242),
            "验收结论": conclusion(verify_242),
            "验收通过": passed_count(verify_242),
            "验收失败": failed_count(verify_242),
            "关键验收包数量": len(report_242.get("验收结果", [])),
            "回滚证据数量": len(report_242.get("回滚证据", [])),
            "是否还有阻塞": report_242.get("是否还有阻塞", ""),
            "股票系统剩余有效工时估算": report_242.get("股票系统剩余有效工时估算", ""),
        },
    }


def build_check_item(rule: dict[str, Any]) -> dict[str, Any]:
    rule_id = str(rule.get("规则ID", ""))
    hard_boundary = bool(rule.get("硬边界保留"))
    auto = bool(rule.get("自动执行"))
    if hard_boundary:
        default_action = "仅生成检查结果、阻断原因和补证据建议；不得自动执行真实覆盖、外发、n8n、券商或交易动作"
    elif auto:
        default_action = "作为03本地规则检查自动固化；失败时只生成补证据或待收口提示"
    else:
        default_action = "进入人工复核队列；低风险本地材料可继续补齐"
    return {
        "检查项ID": rule_id.replace("DLV-", "DLV-LRC-"),
        "来源规则ID": rule_id,
        "检查项名称": rule.get("规则名称", ""),
        "检查类型": rule.get("检查类型", ""),
        "检查目标": rule.get("下次施工约束", ""),
        "默认动作": default_action,
        "自动执行": auto,
        "硬边界保留": hard_boundary,
        "失败处理": "记录到03进化系统规则沉淀验收；不反向覆盖任何业务系统输出。",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票交付闭环规则沉淀包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 规则数量：{report['规则数量']}",
        f"- 自动固化数量：{report['自动固化数量']}",
        f"- 人工确认或硬边界数量：{report['人工确认或硬边界数量']}",
        f"- 小样本验收：{report['小样本规则沉淀验收']['判定']}",
        "",
        "## 证据摘要",
        "",
    ]
    for name, summary in report["证据摘要"].items():
        lines.append(f"### {name}")
        for key, value in summary.items():
            lines.append(f"- {key}：{value}")
        lines.append("")
    lines.extend(["## 规则闭环", ""])
    for rule in report["规则清单"]:
        lines.extend(
            [
                f"### {rule['规则ID']} {rule['规则名称']}",
                f"- 问题：{rule['问题']}",
                f"- 复盘：{rule['复盘']}",
                f"- 规则：{rule['规则']}",
                f"- 下次施工约束：{rule['下次施工约束']}",
                f"- 自动执行：{rule['自动执行']}",
                f"- 硬边界保留：{rule['硬边界保留']}",
                "",
            ]
        )
    lines.extend(["## 自动固化边界", ""])
    lines.append("- 可自动固化：" + "；".join(report["自动固化建议"]["可自动固化"]))
    lines.append("- 仍需人工确认或硬边界保留：" + "；".join(report["自动固化建议"]["仍需人工确认或硬边界保留"]))
    lines.append("")
    lines.extend(["## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    config_path = root / "01配置" / "股票交付闭环规则沉淀规则.json"
    config = load_json(config_path, {})
    evidence_paths = config.get("证据源", {})
    evidence = {name: load_json(path_from_config(raw_path), {}) for name, raw_path in evidence_paths.items()}
    missing_evidence = [name for name, data in evidence.items() if not data]
    rules = config.get("核心规则", [])
    check_items = [build_check_item(rule) for rule in rules]
    evidence_summary = build_evidence_summary(evidence)
    auto_rules = [rule["规则名称"] for rule in rules if rule.get("自动执行") and not rule.get("硬边界保留")]
    manual_rules = [rule["规则名称"] for rule in rules if rule.get("硬边界保留") or not rule.get("自动执行")]
    sample = {
        "证据源全部存在": not missing_evidence,
        "237交付闭环验收通过": evidence_summary["237交付闭环"]["验收失败"] == 0 and evidence_summary["237交付闭环"]["验收通过"] >= 15,
        "241白名单灰度验收通过": evidence_summary["241白名单灰度"]["验收失败"] == 0 and evidence_summary["241白名单灰度"]["真实发送成功"] is True,
        "242最终收口验收通过": evidence_summary["242最终收口"]["验收失败"] == 0 and evidence_summary["242最终收口"]["验收通过"] >= 20,
        "规则数量等于6": len(rules) == 6,
        "规则格式完整": all(all(key in rule and rule[key] for key in ("问题", "复盘", "规则", "下次施工约束")) for rule in rules),
        "包含备份规则": any("备份" in rule.get("规则名称", "") for rule in rules),
        "包含最新回滚证据规则": any("_最新" in rule.get("规则名称", "") and "回滚证据" in rule.get("规则名称", "") for rule in rules),
        "包含影子验证规则": any("影子验证" in rule.get("规则名称", "") for rule in rules),
        "包含白名单灰度规则": any("白名单灰度" in rule.get("规则名称", "") for rule in rules),
        "包含分级隔离规则": any("分级隔离" in rule.get("规则名称", "") for rule in rules),
        "包含最终收口验收规则": any("最终收口验收" in rule.get("规则名称", "") for rule in rules),
    }
    sample["判定"] = "通过" if all(sample.values()) else "需补充"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-stock-delivery-loop-rule-deposit",
        "所属系统": "03杰哥进化系统",
        "来源": config.get("规则来源", ""),
        "配置路径": str(config_path),
        "证据源路径": evidence_paths,
        "缺失证据": missing_evidence,
        "盘点结果": {
            "现有复盘目录": [
                "03数据/01问题卡片",
                "03数据/02成功经验",
                "03数据/03失败教训",
                "03数据/04通用方法",
                "03数据/08规则沉淀",
                "03数据/10自动评审",
                "03数据/11本地检查项候选",
                "03数据/16用户明确规则沉淀",
            ],
            "现有规则固化配置": [
                "验收报告规则沉淀规则.json",
                "规则自动评审与去重评分规则.json",
                "股票系统正式化分级隔离规则.json",
                "股票交付闭环规则沉淀规则.json",
            ],
        },
        "证据摘要": evidence_summary,
        "规则数量": len(rules),
        "自动固化数量": len(auto_rules),
        "人工确认或硬边界数量": len(manual_rules),
        "规则清单": rules,
        "本地检查项候选": check_items,
        "自动固化建议": {
            "可自动固化": auto_rules,
            "仍需人工确认或硬边界保留": manual_rules,
            "说明": "自动固化只落在03本地规则检查、证据完整性检查和收口验收检查；涉及真实覆盖、真实外发、n8n、券商接口、自动交易时仍保留人工确认或硬边界。",
        },
        "小样本规则沉淀验收": sample,
        "安全边界": config.get("安全边界", {}),
        "进化系统当前完成度": "20%-30%；本轮规则沉淀后，规则固化能力继续增强，但真实复盘反馈经验卡片仍等待股票复盘结果回填。",
        "剩余有效工时估算": "约16-26小时；较接续包18-30小时减少约2-4小时，剩余在统一检查入口、跨系统模板化、反馈回填后经验卡片和定期复验。",
        "阻塞项": [
            "股票复盘反馈仍待T5/T20/T60/T120或人工评价回填，不能硬提炼投资经验结论。",
            "跨系统自动执行只能先做本地检查和报告生成，真实覆盖、真实外发、n8n、券商接口、自动交易仍需人工确认或保持关闭。",
            "规则与现有LRC检查项仍需后续合并去重，形成统一施工前检查入口。",
        ],
    }
    out_dir = root / "03数据" / "17股票交付闭环规则沉淀"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"股票交付闭环规则沉淀包_{timestamp}.json"
    latest_json = out_dir / "股票交付闭环规则沉淀包_最新.json"
    output_md = out_dir / f"股票交付闭环规则沉淀包_{timestamp}.md"
    latest_md = out_dir / "股票交付闭环规则沉淀包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"规则数量": len(rules), "自动固化数量": len(auto_rules), "输出": str(output_json), "判定": sample["判定"]}, ensure_ascii=True))
    return 0 if sample["判定"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
