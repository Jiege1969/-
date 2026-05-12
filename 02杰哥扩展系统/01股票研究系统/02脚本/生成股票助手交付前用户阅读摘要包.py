# -*- coding: utf-8 -*-
"""
名称：生成股票助手交付前用户阅读摘要包.py
作用：生成面向用户阅读的股票助手交付前摘要，说明当前已具备能力、未放行边界、下一步确认事项和进度口径。
触发方式：python 生成股票助手交付前用户阅读摘要包.py
依赖：Python标准库；股票助手交付前用户阅读摘要规则.json；股票助手交付材料索引包_最新.json；股票助手交付前剩余动作清单包_最新.json；股票助手交付前只读总状态面板_最新.json；进度回答标准.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地配置和本地产物并写入股票模块03数据目录；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手交付前用户阅读摘要包脚本。
标识：stock-assistant-delivery-user-summary-package-generate
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


def stock_progress(answer_standard: dict[str, Any]) -> dict[str, Any]:
    for item in answer_standard.get("重点子系统", []):
        if item.get("子系统") == "股票分析系统":
            return item
    return {}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手交付前用户阅读摘要",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、当前结论",
        "",
        f"- 是否具备用户阅读摘要条件：{report['是否具备用户阅读摘要条件']}",
        f"- 当前股票系统进度：{report['股票系统进度'].get('当前进度', '')}",
        f"- 可交付使用还需有效工作时间：{report['股票系统进度'].get('可交付使用还需有效工作时间', '')}",
        f"- 当前说明：{report['当前说明']}",
        "",
        "## 二、当前已具备能力",
        "",
    ]
    for item in report["当前已具备能力"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 三、仍未放行边界", ""])
    for item in report["仍未放行边界"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 四、下一步需要用户确认", ""])
    for item in report["需要用户确认事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 五、核心入口", ""])
    for item in report["核心入口"]:
        lines.append(f"- {item['名称']}：`{item['路径']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    sys_root = system_root()
    manager = sys_root / "00杰哥系统总管"
    rule_path = root / "01配置" / "股票助手交付前用户阅读摘要规则.json"
    index_path = root / "03数据" / "49交付材料索引" / "股票助手交付材料索引包_最新.json"
    remaining_path = root / "03数据" / "50交付前剩余动作清单" / "股票助手交付前剩余动作清单包_最新.json"
    dashboard_path = root / "03数据" / "48交付前只读总状态面板" / "股票助手交付前只读总状态面板_最新.json"
    usage_doc_path = root / "07文档" / "股票助手独立使用说明.md"
    progress_standard_path = manager / "01配置" / "进度回答标准.json"

    rule = load_json(rule_path)
    index = load_json(index_path)
    remaining = load_json(remaining_path)
    dashboard = load_json(dashboard_path)
    progress_standard = load_json(progress_standard_path)
    prerequisites = {
        "交付材料索引包存在": index_path.exists(),
        "交付材料索引具备": index.get("是否具备交付材料索引条件") is True,
        "剩余动作清单存在": remaining_path.exists(),
        "剩余动作清单具备": remaining.get("是否具备剩余动作清单条件") is True,
        "只读总状态面板存在": dashboard_path.exists(),
        "只读总状态面板具备": dashboard.get("是否适合继续低风险施工") is True,
        "股票助手独立使用说明存在": usage_doc_path.exists(),
        "进度回答标准存在": progress_standard_path.exists(),
    }
    passed = all(prerequisites.values())
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "前置条件": prerequisites,
        "摘要原则": rule.get("摘要原则", []),
        "股票系统进度": stock_progress(progress_standard),
        "当前已具备能力": rule.get("当前已具备能力", []),
        "仍未放行边界": rule.get("仍未放行边界", []),
        "需要用户确认事项": rule.get("需要用户确认事项", []),
        "核心入口": [
            {"名称": "股票助手独立使用说明", "路径": str(usage_doc_path)},
            {"名称": "交付材料索引包", "路径": str(index_path)},
            {"名称": "交付前只读总状态面板", "路径": str(dashboard_path)},
            {"名称": "交付前剩余动作清单", "路径": str(remaining_path)},
        ],
        "是否具备用户阅读摘要条件": passed,
        "当前说明": "股票助手材料侧已接近交付，但企业微信真实发送、n8n启用、OpenClaw真实桥接、服务刷新和交易接口仍未放行。" if passed else "股票助手用户阅读摘要前置材料不完整，不能作为交付前摘要。",
        "实际动作": rule.get("安全边界", {}),
    }
    output_dir = root / "03数据" / "51交付前用户阅读摘要"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手交付前用户阅读摘要包_{stamp}.json"
    latest_json = output_dir / "股票助手交付前用户阅读摘要包_最新.json"
    output_md = output_dir / f"股票助手交付前用户阅读摘要包_{stamp}.md"
    latest_md = output_dir / "股票助手交付前用户阅读摘要包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"是否具备用户阅读摘要条件": passed, "输出": str(output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
