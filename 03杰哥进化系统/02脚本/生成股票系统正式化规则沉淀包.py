# -*- coding: utf-8 -*-
"""
名称：生成股票系统正式化规则沉淀包.py
作用：把用户明确提出的股票系统正式化规则沉淀为03进化系统本地规则包和检查项候选。
触发方式：python 生成股票系统正式化规则沉淀包.py
依赖：Python标准库；股票系统正式化分级隔离规则.json。
所属系统：03杰哥进化系统
安全边界：只读取03配置和03已有候选结果，只写03进化系统本地沉淀包；不修改股票系统业务脚本，不修改总管进度口径，不发送企业微信，不触发n8n，不调用券商接口，不自动交易。
创建/修改记录：2026-05-05 创建用户明确规则沉淀生成脚本。
标识：evolution-user-stock-formalization-rules-generate
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


def build_check_item(rule: dict[str, Any]) -> dict[str, Any]:
    rule_id = str(rule.get("规则ID", ""))
    check_suffix = rule_id.replace("USR-STOCK-", "")
    hard_boundary = bool(rule.get("硬边界保留"))
    auto = bool(rule.get("自动执行"))
    if hard_boundary:
        default_action = "保留硬边界；只能生成备份、灰度、隔离和验收证据，不自动执行真实动作"
    elif auto:
        default_action = "作为03本地施工前检查自动执行；失败时补证据或继续影子验证"
    else:
        default_action = "进入风险分级复核；低风险本地工作继续，高风险真实动作不放行"
    return {
        "检查项ID": f"USR-LRC-{check_suffix}",
        "来源规则ID": rule_id,
        "检查项名称": rule.get("规则名称", ""),
        "检查类型": rule.get("检查类型", ""),
        "检查目标": rule.get("下次施工约束", ""),
        "默认动作": default_action,
        "自动执行": auto,
        "硬边界保留": hard_boundary,
        "失败处理": "生成阻断或纠偏记录；只允许在03进化系统补规则、补证据、补验收，不反向覆盖业务输出。",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票系统正式化规则沉淀包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 规则数量：{report['规则数量']}",
        f"- 自动检查数量：{report['自动检查数量']}",
        f"- 硬边界数量：{report['硬边界数量']}",
        f"- 小样本验收：{report['小样本验收']['判定']}",
        "",
        "## 规则清单",
        "",
    ]
    for rule in report["规则清单"]:
        lines.extend(
            [
                f"### {rule['规则ID']} {rule['规则名称']}",
                f"- 问题：{rule['问题']}",
                f"- 规则：{rule['规则']}",
                f"- 下次施工约束：{rule['下次施工约束']}",
                f"- 检查类型：{rule['检查类型']}",
                f"- 自动执行：{rule['自动执行']}",
                f"- 硬边界保留：{rule['硬边界保留']}",
                "",
            ]
        )
    lines.extend(["## 本地检查项候选", ""])
    for item in report["本地检查项候选"]:
        lines.extend(
            [
                f"### {item['检查项ID']} {item['检查项名称']}",
                f"- 类型：{item['检查类型']}",
                f"- 目标：{item['检查目标']}",
                f"- 默认动作：{item['默认动作']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 自动固化边界",
            "",
            "- 可自动固化：影子验证通过后才能切正式口径、_最新 文件必须有回滚证据。",
            "- 仍需人工确认或硬边界保留：正式覆盖前必须备份、正式发送前必须白名单灰度、企业微信/n8n/券商接口/自动交易分级隔离。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    root = system_root()
    config_path = root / "01配置" / "股票系统正式化分级隔离规则.json"
    existing_candidate_path = root / "03数据" / "11本地检查项候选" / "规则本地检查项候选_最新.json"
    config = load_json(config_path, {})
    rules = config.get("核心规则", [])
    candidates = [build_check_item(rule) for rule in rules]
    existing_candidates = load_json(existing_candidate_path, {})
    sample = {
        "配置存在": bool(config),
        "规则数量等于5": len(rules) == 5,
        "包含备份规则": any("备份" in item.get("规则名称", "") for item in rules),
        "包含白名单灰度规则": any("白名单灰度" in item.get("规则名称", "") for item in rules),
        "包含影子验证规则": any("影子验证" in item.get("规则名称", "") for item in rules),
        "包含最新回滚证据规则": any("_最新" in item.get("规则名称", "") and "回滚证据" in item.get("规则名称", "") for item in rules),
        "包含分级隔离规则": any("分级隔离" in item.get("规则名称", "") for item in rules),
        "已有本地检查项可衔接": bool(existing_candidates.get("检查项候选")),
    }
    sample["判定"] = "通过" if all(sample.values()) else "需补充"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "evolution-user-stock-formalization-rules",
        "所属系统": "03杰哥进化系统",
        "来源": config.get("规则来源", "用户明确规则沉淀"),
        "配置路径": str(config_path),
        "衔接已有检查项路径": str(existing_candidate_path),
        "规则数量": len(rules),
        "自动检查数量": sum(1 for item in candidates if item["自动执行"]),
        "硬边界数量": sum(1 for item in candidates if item["硬边界保留"]),
        "规则清单": rules,
        "本地检查项候选": candidates,
        "自动固化建议": {
            "可自动固化": [
                "影子验证通过后才能切正式口径",
                "_最新 文件必须有回滚证据",
            ],
            "仍需人工确认或硬边界保留": [
                "正式覆盖前必须备份",
                "正式发送前必须白名单灰度",
                "企业微信、n8n、券商接口、自动交易必须分级隔离",
            ],
            "说明": "自动固化仅限03进化系统本地检查和验收证据；涉及真实覆盖、外发、工作流、券商接口或交易动作时只生成约束，不执行真实动作。",
        },
        "小样本验收": sample,
        "安全边界": config.get("安全边界", {}),
    }
    out_dir = root / "03数据" / "16用户明确规则沉淀"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_json = out_dir / f"股票系统正式化规则沉淀包_{timestamp}.json"
    latest_json = out_dir / "股票系统正式化规则沉淀包_最新.json"
    output_md = out_dir / f"股票系统正式化规则沉淀包_{timestamp}.md"
    latest_md = out_dir / "股票系统正式化规则沉淀包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"规则数量": len(rules), "输出": str(output_json), "判定": sample["判定"]}, ensure_ascii=True))
    return 0 if sample["判定"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
