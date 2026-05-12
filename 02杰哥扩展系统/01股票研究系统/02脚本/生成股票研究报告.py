"""
名称：生成股票研究报告.py
作用：根据本模块股票数据快照生成第一阶段研究报告草稿。
触发方式：python 生成股票研究报告.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本模块本地数据快照，只写入本模块研究报告目录；不联网、不交易、不调用券商接口。
创建/修改记录：2026-04-26 创建第一阶段股票研究报告脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def latest_snapshot() -> Path:
    snapshot_dir = module_root() / "03数据" / "04数据快照"
    candidates = sorted(snapshot_dir.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"no stock snapshot json found in {snapshot_dir}")
    return candidates[0]


def load_report_template() -> dict[str, Any]:
    template_path = module_root() / "01配置" / "股票报告模板.json"
    if template_path.exists():
        return load_json(template_path)
    return {
        "报告标题": "股票研究报告草稿",
        "固定声明": "本报告仅供研究参考，不构成投资建议，不作为买卖指令。",
        "章节": [
            {"标题": "事实"},
            {"标题": "推断"},
            {"标题": "风险"},
            {"标题": "待核实事项"},
        ],
        "禁止表达": [],
    }


def as_text(value: Any) -> str:
    if isinstance(value, list):
        return "；".join(str(item) for item in value if str(item).strip())
    if isinstance(value, dict):
        return "；".join(f"{key}: {val}" for key, val in value.items())
    return str(value or "")


def render_report(snapshot: dict[str, Any]) -> str:
    template = load_report_template()
    lines = [
        f"# {template.get('报告标题', '股票研究报告草稿')}",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 重要声明",
        "",
        template.get("固定声明", "本报告仅供研究参考，不构成投资建议，不作为买卖指令。"),
        "",
    ]
    for item in snapshot.get("股票", []):
        lines.extend(
            [
                f"## {item.get('名称', '未命名')}（{item.get('代码', '无代码')}）",
                "",
                f"- 市场：{item.get('市场', '待填写')}",
                f"- 数据日期：{item.get('数据日期', '待填写')}",
                "",
                "### 事实",
                "",
                f"- 基础信息：{as_text(item.get('基础信息', {}))}",
                f"- 财务摘要：{as_text(item.get('财务摘要', {}))}",
                f"- 估值摘要：{as_text(item.get('估值摘要', {}))}",
                "",
                "### 推断",
                "",
                "- 当前仅基于人工数据快照生成，推断需结合正式数据源和人工复核。",
                "",
                "### 风险",
                "",
                f"- {as_text(item.get('风险因素', [])) or '待补充'}",
                "",
                "### 待核实事项",
                "",
                f"- {as_text(item.get('待核实事项', [])) or '待补充'}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    snapshot_path = latest_snapshot()
    snapshot = load_json(snapshot_path)
    output_dir = module_root() / "03数据" / "03研究报告"
    output_dir.mkdir(parents=True, exist_ok=True)
    report = render_report(snapshot)
    output = output_dir / f"股票研究报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    latest = output_dir / "股票研究报告_最新.md"
    output.write_text(report, encoding="utf-8")
    latest.write_text(report, encoding="utf-8")
    print(json.dumps({"输入": str(snapshot_path), "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
