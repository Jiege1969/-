# -*- coding: utf-8 -*-
"""
名称：生成成熟软件分析逻辑吸收报告.py
作用：把中信证券成熟软件结构抽象为本系统可执行的方法论补强报告。
边界：只读本地配置和中信参考清单；只写本地报告；不调用券商接口；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "01配置"
DATA = ROOT / "03数据"
OUT_DIR = DATA / "015外部成熟软件指标借鉴" / "中信证券"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_layer_matrix(rule: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in rule.get("抽象后的分析方法骨架", []):
        rows.append({
            "顺序": item.get("顺序"),
            "方法层": item.get("方法层"),
            "回答问题": item.get("回答问题"),
            "参考中信场景": item.get("参考中信场景", []),
            "本系统落地": item.get("本系统落地", []),
            "输出": item.get("输出", []),
            "结论权限": item.get("结论权限"),
        })
    return rows


def build_gap_actions(rule: dict[str, Any]) -> list[dict[str, Any]]:
    actions = []
    priority_map = {
        "技术指标较多，但分析场景入口不够清晰。": "P0",
        "个股高分容易掩盖市场/行业/事件/风险的层级差异。": "P0",
        "盘中数据和盘后正式数据容易混用。": "P0",
        "资金、事件、日历类证据不足。": "P1",
        "报告偏静态，持续跟踪机制不足。": "P1"
    }
    for item in rule.get("对当前系统的补强方向", []):
        gap = item.get("缺口", "")
        actions.append({
            "优先级": priority_map.get(gap, "P2"),
            "系统缺口": gap,
            "修正动作": item.get("修正", ""),
            "落地位置": infer_target(gap),
        })
    return actions


def infer_target(gap: str) -> str:
    if "场景入口" in gap:
        return "01配置/股票指标智能选择与方法切换规则 + 282股票指标智能选择引擎"
    if "高分" in gap:
        return "推荐评分/报告结论上限/风险刹车"
    if "盘中" in gap:
        return "数据源注册表/历史日线库/盘中观察库"
    if "资金" in gap or "事件" in gap:
        return "证据补充层/公告财报行业事件核验"
    if "跟踪" in gap:
        return "关注池/观察条件/复盘账本/企业微信前台"
    return "股票分析系统方法层"


def build_markdown(report: dict[str, Any]) -> str:
    rule = report["吸收规则"]
    lines = [
        "# 成熟软件分析逻辑吸收报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 参考对象：{rule['参考对象']}",
        f"- 结论：{report['结论']}",
        "",
        "## 一句话结论",
        "",
        "中信这类成熟软件的价值不在于某一个神奇指标，而在于它把股票分析组织成“场景入口 + 分层判断 + 风险闭环 + 持续跟踪”的工作流。我们要吸收的是这个底层逻辑。",
        "",
        "## 核心提炼",
        "",
    ]
    for item in rule.get("核心提炼", []):
        lines.append(f"- {item['提炼点']}：{item['含义']} 对本系统启发：{item['对本系统启发']}")
    lines.extend(["", "## 六层方法骨架", ""])
    for item in report["六层方法矩阵"]:
        lines.append(
            f"- {item['顺序']}. {item['方法层']}：{item['回答问题']} "
            f"落地：{', '.join(item['本系统落地'])}。权限：{item['结论权限']}"
        )
    lines.extend(["", "## 系统补强动作", ""])
    for item in report["补强动作"]:
        lines.append(f"- {item['优先级']} {item['系统缺口']} -> {item['修正动作']} 落地：{item['落地位置']}")
    lines.extend(["", "## 方法总原则", ""])
    for item in rule.get("方法吸收后的总原则", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 边界", ""])
    for item in rule.get("边界", []):
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    rule_path = CONFIG / "成熟软件分析逻辑吸收规则_v1.0.json"
    citic_scan_path = OUT_DIR / "中信证券指标参考清单_最新.json"
    selector_rule_path = CONFIG / "股票指标智能选择与方法切换规则_v1.0.json"

    rule = read_json(rule_path, {})
    citic_scan = read_json(citic_scan_path, {})
    selector_rule = read_json(selector_rule_path, {})
    report = {
        "名称": "成熟软件分析逻辑吸收报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if rule else "需复核",
        "吸收规则路径": str(rule_path),
        "中信参考清单路径": str(citic_scan_path),
        "现有方法切换规则路径": str(selector_rule_path),
        "中信扫描摘要": {
            "扫描文件数": citic_scan.get("扫描文件数"),
            "分类数": len(citic_scan.get("中信参考分类", {})),
        },
        "现有系统承接点": {
            "已有核心思想数量": len(selector_rule.get("核心思想", [])),
            "已有多层任务线数量": len(selector_rule.get("多层分析任务矩阵", [])),
            "说明": "本次不是推翻现有规则，而是把成熟软件的场景工作流补进方法层，作为现有智能选择机制的上游场景解释。"
        },
        "吸收规则": rule,
        "六层方法矩阵": build_layer_matrix(rule),
        "补强动作": build_gap_actions(rule),
        "安全边界": rule.get("安全边界", {}),
    }
    json_path = OUT_DIR / "成熟软件分析逻辑吸收报告_最新.json"
    md_path = OUT_DIR / "成熟软件分析逻辑吸收报告_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "六层方法数": len(report["六层方法矩阵"]),
        "补强动作数": len(report["补强动作"]),
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if rule else 1


if __name__ == "__main__":
    raise SystemExit(main())
