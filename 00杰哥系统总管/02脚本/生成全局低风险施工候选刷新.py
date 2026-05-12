# -*- coding: utf-8 -*-
"""
名称：生成全局低风险施工候选刷新.py
作用：在旧路径口径巡检通过后，刷新下一批可自动推进的低风险施工候选。
触发方式：python 生成全局低风险施工候选刷新.py
安全边界：只读队列和验收报告并写候选清单；不改入口、不发送企业微信、不触发n8n、不写库、不调用券商接口、不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "全局低风险施工候选刷新_最新.json"
REPORT_MD = OUT_DIR / "全局低风险施工候选刷新_最新.md"
QUEUE_VALIDATION = OUT_DIR / "无干扰自动施工队列验收_最新.json"
OLD_PATH_VALIDATION = OUT_DIR / "旧路径口径全局巡检验收_最新.json"
NON_TRADE_VALIDATION = OUT_DIR / "股票系统只分析不交易总闸门验收_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    queue_validation = load_json(QUEUE_VALIDATION)
    old_path_validation = load_json(OLD_PATH_VALIDATION)
    non_trade_validation = load_json(NON_TRADE_VALIDATION)
    preconditions = {
        "无干扰队列通过": queue_validation.get("结论") == "通过",
        "旧路径口径巡检通过": old_path_validation.get("结论") == "通过",
        "股票非交易总闸门通过": non_trade_validation.get("当前结论") == "通过",
    }
    candidates = [
        {
            "编号": "LR-20260505-001",
            "任务": "文档索引当前路径口径复核",
            "所属系统": "00总管/01智能",
            "执行方式": "只读复核设计纲领、施工面板、文档总索引和总架构说明当前路径口径",
            "禁止动作": "不删除文件，不修改入口，不触发服务",
            "推荐顺序": 1,
        },
        {
            "编号": "LR-20260505-002",
            "任务": "知识库问答灰度终态索引定期复核",
            "所属系统": "01智能/02扩展",
            "执行方式": "只读复核终态索引、阻断报告和许可预检仍为禁止灰度",
            "禁止动作": "不填写许可，不放行灰度，不接企业微信",
            "推荐顺序": 2,
        },
        {
            "编号": "LR-20260505-003",
            "任务": "企业微信助手禁用态入口复查",
            "所属系统": "02扩展/06企业微信助手",
            "执行方式": "只读复查知识库问答入口仍处于禁用态桥接",
            "禁止动作": "不真实发送企业微信，不触发 Webhook/n8n",
            "推荐顺序": 3,
        },
        {
            "编号": "LR-20260505-004",
            "任务": "全盘架构实施进度章节一致性检查",
            "所属系统": "00总管",
            "执行方式": "只读检查总架构说明、工作日志和施工面板章节是否同步",
            "禁止动作": "不改业务入口，不写正式库",
            "推荐顺序": 4,
        },
    ]
    blockers = [
        "正式微信短文生成器替换运行入口仍必须停下报告。",
        "知识库问答灰度仍禁止自动放行。",
        "企业微信真实发送、Webhook、n8n触发、写库、券商接口和自动交易仍关闭。",
    ]
    safety = {
        "修改入口": False,
        "发送企业微信": False,
        "触发Webhook": False,
        "触发n8n": False,
        "写正式库": False,
        "调用模型推理": False,
        "调用券商接口": False,
        "自动交易": False,
    }
    report = {
        "名称": "全局低风险施工候选刷新",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if all(preconditions.values()) else "前置缺口",
        "前置条件": preconditions,
        "候选数量": len(candidates),
        "低风险候选": candidates,
        "必须阻断项": blockers,
        "下一步建议": candidates[0]["任务"],
        "安全边界": safety,
    }
    lines = [
        "# 全局低风险施工候选刷新",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 候选数量：{report['候选数量']}",
        f"- 下一步建议：{report['下一步建议']}",
        "",
        "## 低风险候选",
        "",
    ]
    for item in candidates:
        lines.append(f"- {item['编号']} {item['任务']}：{item['执行方式']}；{item['禁止动作']}")
    lines.extend(["", "## 必须阻断项", ""])
    for item in blockers:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    lines.append("本轮只刷新候选清单，不修改入口，不发送企业微信，不触发 Webhook/n8n，不写库，不调用券商接口，不自动交易。")
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "候选数量": len(candidates), "下一步建议": report["下一步建议"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if report["结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
