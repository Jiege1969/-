# -*- coding: utf-8 -*-
"""
名称：生成股票盘后批处理资源预算计划.py
作用：根据动态样本池规则、盘后批处理资源预算规则和模型资源池，生成股票样本池扩展到2000只时的资源预算与禁用态执行计划。
触发方式：python 生成股票盘后批处理资源预算计划.py
依赖：Python标准库；动态样本池规则.json；盘后批处理资源预算规则.json；股票池模板.json；00总管模型资源池登记_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置并写入股票模块03数据目录；不联网；不抓取真实行情；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票盘后批处理资源预算计划脚本；2026-04-30 适配2000只标准大股票池定位。
标识：stock-after-hours-batch-resource-plan-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return module_root().parents[1]


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


def visible_models(model_pool: dict[str, Any]) -> list[str]:
    items = model_pool.get("模型资源池", [])
    return [item.get("名称", "") for item in items if item.get("当前状态") == "已可见"]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票盘后批处理资源预算计划",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 当前结论：{report['当前结论']}",
        f"- 推荐施工状态：{report['推荐施工状态']}",
        "- 2000只标准大股票池是规律学习和候选筛选底座，只做盘后日线级轻扫描，不做盘中全量扫描。",
        "- 大模型只处理候选研究池、深度分析池和重点关注池，不逐只分析2000只。",
        "",
        "## 二、资源边界",
        "",
    ]
    for key, value in report["硬件边界"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、样本池阶段", ""])
    for item in report["样本池阶段"]:
        lines.append(f"- {item['阶段']}：{item['规模']}只；用途：{item['用途']}")
    lines.extend(["", "## 四、批处理策略", ""])
    for key, value in report["批处理分段"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、模型调用策略", ""])
    for key, value in report["模型调用策略"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 六、存储预算", ""])
    for key, value in report["资源预算估算"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 七、禁用态安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 八、下一步", ""])
    for item in report["下一步"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    sys_root = system_root()
    rule_path = root / "01配置" / "盘后批处理资源预算规则.json"
    dynamic_rule_path = root / "01配置" / "动态样本池规则.json"
    stock_pool_path = root / "01配置" / "股票池模板.json"
    model_pool_path = sys_root / "00杰哥系统总管" / "03数据" / "模型资源池" / "模型资源池登记_最新.json"

    rule = load_json(rule_path)
    dynamic_rule = load_json(dynamic_rule_path)
    stock_pool = load_json(stock_pool_path)
    model_pool = load_json(model_pool_path)
    models = visible_models(model_pool)

    target_size = rule.get("样本池阶段", [{}])[-1].get("规模", 2000)
    batch_size = int(rule.get("批处理分段", {}).get("每批股票数", 100))
    batch_count = (int(target_size) + batch_size - 1) // batch_size
    budget = rule.get("资源预算估算", {})
    daily_mb = budget.get("2000只标准大股票池单日产物MB", budget.get("2000只单日产物MB", 160))
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "动态样本池规则": str(dynamic_rule_path),
        "股票池模板": str(stock_pool_path),
        "模型资源池": str(model_pool_path),
        "当前股票池数量": len(stock_pool.get("股票池", [])),
        "动态样本池目标规模": dynamic_rule.get("目标规模", {}),
        "硬件边界": rule.get("硬件边界", {}),
        "样本池阶段": rule.get("样本池阶段", []),
        "批处理分段": rule.get("批处理分段", {}),
        "批次数估算": batch_count,
        "模型调用策略": rule.get("模型调用策略", {}),
        "日常执行目标": rule.get("日常执行目标", {}),
        "当前可见模型": models,
        "资源预算估算": rule.get("资源预算估算", {}),
        "日新增产物MB估算": daily_mb,
        "实际动作": {
            "真实联网": False,
            "真实抓取行情": False,
            "触发n8n": False,
            "企业微信真实发送": False,
            "写正式库": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启服务": False
        },
        "推荐施工状态": "先以禁用态计划和资源预算固化；真实盘后只读轻扫描需另走公开数据只读许可令。",
        "当前结论": "本机可承载2000只盘后日线级轻扫描设计，但不适合对2000只逐只调用大模型深度分析。",
        "下一步": [
            "先做300只试运行池的名单生成和禁用态批处理计划。",
            "再做只读公开数据许可令，明确数据源、频率、失败降级和缓存策略。",
            "最后由n8n纳入未激活工作流草案，人工确认后再灰度启用。"
        ],
    }
    output_dir = root / "03数据" / "32盘后批处理计划"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票盘后批处理资源预算计划_{stamp}.json"
    latest_json = output_dir / "股票盘后批处理资源预算计划_最新.json"
    output_md = output_dir / f"股票盘后批处理资源预算计划_{stamp}.md"
    latest_md = output_dir / "股票盘后批处理资源预算计划_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"目标规模": target_size, "批次数估算": batch_count, "日新增MB估算": daily_mb, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
