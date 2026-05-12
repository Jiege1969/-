"""
名称：生成稳定中台巡检计划.py
作用：根据稳定中台巡检规则生成只读巡检计划和人工调度建议。
触发方式：python 生成稳定中台巡检计划.py
依赖：Python 标准库；稳定中台巡检规则.json。
所属系统：00杰哥系统总管
安全边界：只生成巡检计划；不创建系统计划任务；不触发n8n；不发送企业微信；不写旧系统。
创建/修改记录：2026-04-27 创建稳定中台巡检计划脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def v3_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_markdown(plan: dict[str, Any], output: Path) -> None:
    lines = [
        "# 稳定中台巡检计划",
        "",
        f"- 生成时间：{plan['生成时间']}",
        "- 类型：只读巡检计划",
        "",
        "## 建议频率",
        "",
    ]
    for name, frequency in plan.get("建议频率", {}).items():
        lines.append(f"- {name}：{frequency}")
    lines.extend([
        "",
        "## 巡检项目",
        "",
        "| 名称 | 类型 | 必检 | 脚本 |",
        "| --- | --- | --- | --- |",
    ])
    for item in plan.get("巡检项目", []):
        lines.append(f"| {item.get('名称')} | {item.get('类型')} | {item.get('必检')} | {item.get('脚本')} |")
    lines.extend([
        "",
        "## 禁止动作",
        "",
    ])
    lines.extend(f"- {value}" for value in plan.get("禁止动作", []))
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    root = v3_root()
    rules_path = root / "00杰哥系统总管" / "01配置" / "稳定中台巡检规则.json"
    rules = load_json(rules_path)
    plan = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查类型": "stable-hub-patrol-plan",
        "规则文件": str(rules_path),
        "建议频率": rules.get("建议频率", {}),
        "巡检项目": rules.get("巡检项目", []),
        "禁止动作": rules.get("禁止动作", []),
        "执行开关": {
            "是否创建计划任务": False,
            "是否重启服务": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否写入旧系统": False,
            "是否恢复税收业务": False
        },
    }
    output_dir = root / "00杰哥系统总管" / "03数据" / "稳定中台"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_output = output_dir / "稳定中台巡检计划_最新.json"
    latest_json = output_dir / "稳定中台巡检计划_最新.json"
    md_output = output_dir / "稳定中台巡检计划_最新.md"
    text = json.dumps(plan, ensure_ascii=False, indent=2)
    json_output.write_text(text, encoding="utf-8")
    latest_json.write_text(text, encoding="utf-8")
    write_markdown(plan, md_output)
    print(json.dumps({"巡检项目数": len(plan["巡检项目"]), "输出": str(json_output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
