# -*- coding: utf-8 -*-
"""
名称：生成股票系统交付验收清单.py
作用：根据股票系统交付验收清单规则和现有产物，生成本地可用、企业微信禁用态可用、n8n禁用态可用、真实灰度可用、交付可用的分层验收清单。
触发方式：python 生成股票系统交付验收清单.py
依赖：Python标准库；股票系统交付验收清单规则.json；股票系统状态摘要；股票统一消息出口禁用态回复包；OpenClaw桥接契约；n8n未激活导入预案。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地报告并写入股票模块03数据目录；不重启服务；不导入n8n；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票系统交付验收清单脚本。
标识：stock-delivery-acceptance-checklist-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def evaluate(root: Path, rule: dict[str, Any]) -> list[dict[str, Any]]:
    files = {
        "状态摘要": root / "03数据" / "16状态摘要" / "股票研究系统状态摘要_最新.json",
        "单股报告": root / "03数据" / "23单股即时报告" / "单股即时研究报告_最新.json",
        "报告索引": root / "03数据" / "23单股即时报告" / "重点关注池单股报告索引_最新.md",
        "L5报告": root / "03数据" / "15深度研究" / "L5深度研究报告_最新.md",
        "日常包": root / "03数据" / "17日常使用包" / "股票研究日常使用包_最新.md",
        "短回复": root / "03数据" / "24企业微信短回复" / "企业微信单股短回复_最新.json",
        "语音追问": root / "03数据" / "24企业微信短回复" / "企业微信语音追问短回复_最新.json",
        "语音确认": root / "03数据" / "24企业微信短回复" / "企业微信语音确认学习回复_最新.json",
        "统一路由": root / "03数据" / "25企业微信统一路由" / "企业微信股票消息统一路由禁用态_最新.json",
        "统一出口": root / "03数据" / "34统一消息出口禁用态" / "股票统一消息出口禁用态回复包_最新.json",
        "n8n契约": root / "03数据" / "26n8n路由契约" / "股票企业微信n8n路由契约_最新.md",
        "n8n适配器": root / "03数据" / "27n8n适配器禁用态" / "股票企业微信n8n适配器禁用态_最新.md",
        "n8n草案": root / "03数据" / "28n8n适配器工作流草案" / "股票企业微信n8n适配器工作流草案包_最新.json",
        "n8n许可": root / "03数据" / "29n8n灰度导入许可" / "股票企业微信n8n灰度导入许可令_最新.md",
        "n8n预案": root / "03数据" / "30n8n未激活导入预案" / "股票企业微信n8n未激活导入预案_最新.md",
        "OpenClaw契约": root / "03数据" / "33OpenClaw桥接契约" / "OpenClaw股票消息桥接禁用态契约_最新.md",
    }
    status = load_json(files["状态摘要"])
    data_health = status.get("数据健康度", {})
    layer_checks = {
        "A本地可用": [
            data_health.get("健康等级") in {"优秀", "可用"},
            exists(files["单股报告"]),
            exists(files["报告索引"]),
            exists(files["L5报告"]),
            exists(files["日常包"]),
        ],
        "B企业微信禁用态可用": [
            exists(files["短回复"]),
            exists(files["语音追问"]),
            exists(files["语音确认"]),
            exists(files["统一路由"]),
            exists(files["统一出口"]),
        ],
        "Cn8n禁用态可用": [
            exists(files["n8n契约"]),
            exists(files["n8n适配器"]),
            exists(files["n8n草案"]),
            exists(files["n8n许可"]),
            exists(files["n8n预案"]),
        ],
        "D真实灰度可用": [
            False,
            False,
            exists(files["OpenClaw契约"]),
            False,
            False,
            False,
        ],
        "E交付可用": [
            False,
            False,
            False,
            False,
            True,
            False,
        ],
    }
    evaluated = []
    for layer in rule.get("验收层级", []):
        name = layer.get("层级", "")
        checks = layer_checks.get(name, [])
        passed = sum(1 for item in checks if item)
        total = len(checks)
        evaluated.append({
            **layer,
            "检查通过": passed,
            "检查总数": total,
            "完成度": round((passed / total * 100), 2) if total else 0,
            "判定": "通过" if total and passed == total else "未通过",
        })
    return evaluated


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票系统交付验收清单",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 当前结论：{report['当前结论']}",
        f"- 可交付层级：{report['当前可交付层级']}",
        "",
        "## 二、分层验收",
        "",
    ]
    for layer in report["验收层级"]:
        lines.append(f"### {layer['层级']}")
        lines.append(f"- 定义：{layer['定义']}")
        lines.append(f"- 当前状态：{layer['当前状态']}")
        lines.append(f"- 检查：{layer['检查通过']}/{layer['检查总数']}，完成度：{layer['完成度']}%，判定：{layer['判定']}")
        lines.append("- 必须满足：")
        for item in layer.get("必须满足", []):
            lines.append(f"  - {item}")
        lines.append("")
    lines.extend(["## 三、禁止误判", ""])
    for item in report["禁止误判"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "股票系统交付验收清单规则.json"
    rule = load_json(rule_path)
    layers = evaluate(root, rule)
    passed_layers = [item["层级"] for item in layers if item["判定"] == "通过"]
    current_layer = passed_layers[-1] if passed_layers else "尚未通过本地可用"
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "验收层级": layers,
        "禁止误判": rule.get("禁止误判", []),
        "安全边界": rule.get("安全边界", {}),
        "当前可交付层级": current_layer,
        "当前结论": "股票系统已达到本地可用、企业微信禁用态可用、n8n禁用态可用；真实灰度和最终交付仍未放行。" if current_layer == "Cn8n禁用态可用" else "股票系统仍处于分层建设中。",
        "实际动作": {
            "重启服务": False,
            "导入n8n": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写正式库": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "35交付验收清单"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票系统交付验收清单_{stamp}.json"
    latest_json = output_dir / "股票系统交付验收清单_最新.json"
    output_md = output_dir / f"股票系统交付验收清单_{stamp}.md"
    latest_md = output_dir / "股票系统交付验收清单_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"当前可交付层级": current_layer, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
