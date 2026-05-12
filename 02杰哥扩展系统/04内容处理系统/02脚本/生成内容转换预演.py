"""
名称：生成内容转换预演.py
作用：根据内容批处理计划生成转换预演报告，说明每个素材建议如何处理、复用到哪个系统。
触发方式：python 生成内容转换预演.py
依赖：Python 标准库；需先生成内容批处理计划。
所属系统：02杰哥扩展系统/04内容处理系统
安全边界：只读取批处理计划，只写入转换预演目录；不改写、不删除、不移动素材，不执行真实转码。
创建/修改记录：2026-04-27 创建内容转换预演脚本。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_plan(root: Path) -> Path:
    latest = root / "03数据" / "03批处理计划" / "内容批处理计划_最新.json"
    if latest.exists():
        return latest
    script = root / "02脚本" / "生成内容批处理计划.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def target_system_for(asset_type: str) -> list[str]:
    mapping = {
        "文档": ["03本职工作系统", "01杰哥智能系统/知识库"],
        "表格": ["03本职工作系统", "01杰哥智能系统/知识库"],
        "图片": ["02视频制作系统", "04内容处理系统"],
        "音频": ["02视频制作系统", "04内容处理系统"],
        "视频": ["02视频制作系统", "04内容处理系统"],
    }
    return mapping.get(asset_type, ["人工确认"])


def build_preview() -> dict[str, Any]:
    root = module_root()
    plan_path = ensure_plan(root)
    plan = load_json(plan_path)
    output_dir = root / "03数据" / "04转换预演"
    output_dir.mkdir(parents=True, exist_ok=True)

    previews = []
    for task in plan.get("任务", []):
        asset_type = task.get("素材类型", "未知")
        previews.append(
            {
                "文件名": task.get("文件名"),
                "路径": task.get("路径"),
                "素材类型": asset_type,
                "任务类型": task.get("任务类型"),
                "建议动作": task.get("预演动作", []),
                "建议复用系统": target_system_for(asset_type),
                "是否需要人工确认": True,
                "是否执行真实转换": False,
                "是否改写原文件": False,
                "是否删除原文件": False,
                "是否移动原文件": False,
                "预演结论": "可进入人工确认队列" if not task.get("是否阻断") else "仅登记，暂不处理",
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "计划来源": str(plan_path),
        "预演数量": len(previews),
        "预演": previews,
        "是否执行真实转换": False,
        "是否改写原文件": False,
        "是否删除原文件": False,
        "是否移动原文件": False,
        "安全说明": "转换预演只输出建议动作和复用方向，不执行真实转换，不改变任何原始素材。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"内容转换预演_{timestamp}.json"
    latest = output_dir / "内容转换预演_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"preview_count": len(previews), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_preview()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
