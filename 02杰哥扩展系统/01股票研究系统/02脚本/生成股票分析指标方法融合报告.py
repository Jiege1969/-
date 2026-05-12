# -*- coding: utf-8 -*-
"""
名称：生成股票分析指标方法融合报告.py
作用：把数据底座、指标扩展、成熟软件方法吸收和现有智能选择规则汇总为可执行方法报告。
边界：只读本地配置和报告；只写本地报告；不联网；不交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "01配置"
DATA = ROOT / "03数据"
OUT_DIR = DATA / "018股票分析指标方法融合"


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


def layer_summary(rule: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for layer in rule.get("分析方法层", []):
        rows.append({
            "层级": layer.get("层级"),
            "名称": layer.get("名称"),
            "主导指标数量": len(layer.get("主导指标", [])),
            "辅助指标数量": len(layer.get("辅助指标", [])),
            "有否决指标": bool(layer.get("否决指标")),
            "权限": layer.get("权限"),
            "输出": layer.get("输出", []),
        })
    return rows


def build_markdown(report: dict[str, Any]) -> str:
    rule = report["融合规则"]
    lines = [
        "# 股票分析指标方法融合报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 数据底座状态：{report['数据底座状态'].get('结论', '缺失')}",
        f"- 方法层数量：{len(rule.get('分析方法层', []))}",
        f"- 场景映射数量：{len(rule.get('场景到方法映射', []))}",
        "",
        "## 核心原则",
        "",
    ]
    for item in rule.get("上位原则", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 方法层与指标权限", ""])
    for item in report["方法层摘要"]:
        veto = "有" if item["有否决指标"] else "无"
        lines.append(
            f"- {item['层级']} {item['名称']}：主导{item['主导指标数量']}项，"
            f"辅助{item['辅助指标数量']}项，否决{veto}。权限：{item['权限']}"
        )
    lines.extend(["", "## 场景到方法", ""])
    for item in rule.get("场景到方法映射", []):
        main = "、".join(item.get("主导层", []))
        lines.append(f"- {item['场景']}：主导层={main}；输出={item.get('输出', item.get('排序逻辑', ''))}")
    lines.extend(["", "## 结论生成", ""])
    for level, desc in rule.get("结论生成规则", {}).items():
        lines.append(f"- {level}：{desc}")
    lines.extend(["", "## 当前验收", ""])
    for item in report["验收项"]:
        lines.append(f"- {item['项目']}：{item['状态']}。{item['说明']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    fusion_rule_path = CONFIG / "股票分析指标方法融合规则_v1.0.json"
    db_index_path = DATA / "016全A基础数据库索引" / "全A基础数据库统一索引_最新.json"
    mature_method_path = DATA / "015外部成熟软件指标借鉴" / "中信证券" / "成熟软件分析逻辑吸收报告_最新.json"
    indicator_validation_path = DATA / "015外部成熟软件指标借鉴" / "中信证券" / "中信借鉴指标扩展验证_最新.json"
    selector_rule_path = CONFIG / "股票指标智能选择与方法切换规则_v1.0.json"

    rule = read_json(fusion_rule_path, {})
    db_index = read_json(db_index_path, {})
    mature_method = read_json(mature_method_path, {})
    indicator_validation = read_json(indicator_validation_path, {})
    selector_rule = read_json(selector_rule_path, {})

    checks = [
        {
            "项目": "全A基础数据库",
            "状态": "通过" if db_index.get("结论") == "通过" else "需复核",
            "说明": f"全A{db_index.get('全A股票池', {}).get('股票数量', 0)}只，中信原始日线{db_index.get('中信本机原始日线', {}).get('文件覆盖', {}).get('总数', 0)}只。"
        },
        {
            "项目": "成熟软件方法吸收",
            "状态": "通过" if mature_method.get("结论") == "通过" else "需复核",
            "说明": f"六层方法{len(mature_method.get('六层方法矩阵', []))}层，补强动作{len(mature_method.get('补强动作', []))}项。"
        },
        {
            "项目": "新增指标计算",
            "状态": "通过" if indicator_validation.get("结论") == "通过" else "需复核",
            "说明": f"新增字段验证{indicator_validation.get('新增字段数量', 0)}项。"
        },
        {
            "项目": "现有智能选择规则",
            "状态": "通过" if selector_rule.get("核心思想") else "需复核",
            "说明": f"已有任务矩阵{len(selector_rule.get('多层分析任务矩阵', []))}条。"
        }
    ]
    issues = [item for item in checks if item["状态"] != "通过"]
    report = {
        "名称": "股票分析指标方法融合报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not issues and rule else "需复核",
        "融合规则路径": str(fusion_rule_path),
        "融合规则": rule,
        "数据底座状态": {"结论": db_index.get("结论"), "摘要": db_index.get("全A股票池", {})},
        "方法吸收状态": {"结论": mature_method.get("结论"), "六层方法数": len(mature_method.get("六层方法矩阵", []))},
        "指标验证状态": {"结论": indicator_validation.get("结论"), "新增字段数量": indicator_validation.get("新增字段数量")},
        "方法层摘要": layer_summary(rule),
        "验收项": checks,
        "安全边界": rule.get("安全边界", {}),
    }
    json_path = OUT_DIR / "股票分析指标方法融合报告_最新.json"
    md_path = OUT_DIR / "股票分析指标方法融合报告_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "方法层数量": len(rule.get("分析方法层", [])),
        "场景映射数量": len(rule.get("场景到方法映射", [])),
        "验收问题": len(issues),
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if report["结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
