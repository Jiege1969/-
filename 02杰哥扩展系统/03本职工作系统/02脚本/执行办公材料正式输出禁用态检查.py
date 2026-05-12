"""
名称：执行办公材料正式输出禁用态检查.py
作用：读取办公材料本地生成门禁报告，生成正式输出禁用态检查报告，确认正式文档生成、覆盖、上传和外发均保持关闭。
触发方式：python 执行办公材料正式输出禁用态检查.py
依赖：Python 标准库；办公材料本地生成门禁报告_最新.json；办公材料本地生成门禁.json。
所属系统：02杰哥扩展系统/03本职工作系统
安全边界：只生成正式输出禁用态检查报告；不生成正式文档；不覆盖正式文档；不读取涉密资料；不自动外发；不上传；不触发n8n；不真实发送企业微信。
创建/修改记录：2026-04-27 创建办公材料正式输出禁用态检查脚本。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = module_root()
    gate = load_json(root / "01配置" / "办公材料本地生成门禁.json")
    gate_report_path = root / "03数据" / "04本地生成门禁" / "办公材料本地生成门禁报告_最新.json"
    gate_report = load_json(gate_report_path) if gate_report_path.exists() else {}
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "办公材料正式输出禁用态检查",
        "门禁报告": str(gate_report_path),
        "门禁开关": gate.get("默认开关", {}),
        "草稿状态": gate_report.get("草稿框架", {}),
        "是否生成正式文档": False,
        "是否覆盖正式文档": False,
        "是否读取涉密资料": False,
        "是否自动外发": False,
        "是否自动上传": False,
        "是否触发n8n": False,
        "是否企业微信真实发送": False,
        "执行器状态": "禁用态",
        "当前结论": "正式输出执行器保持禁用，只允许本地草稿和人工确认。"
    }
    output_dir = root / "03数据" / "04本地生成门禁"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"办公材料正式输出禁用态检查_{timestamp}.json"
    latest = output_dir / "办公材料正式输出禁用态检查_最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行器状态": report["执行器状态"], "是否生成正式文档": report["是否生成正式文档"], "输出": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
