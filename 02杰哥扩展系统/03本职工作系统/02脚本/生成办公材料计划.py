"""
名称：生成办公材料计划.py
作用：根据本职工作配置和办公材料模板生成第一阶段办公材料任务计划。
触发方式：python 生成办公材料计划.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/03本职工作系统
安全边界：只读取本模块配置，只写入本模块任务计划和草稿框架；不读取真实涉密资料、不自动发送。
创建/修改记录：2026-04-26 创建第一阶段办公材料计划脚本。
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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = module_root()
    config = load_json(root / "01配置" / "本职工作配置.json")
    templates = load_json(root / "01配置" / "办公材料模板.json")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    plan = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "系统": "02杰哥扩展系统/03本职工作系统",
        "阶段": "第一阶段任务计划",
        "安全边界": config.get("安全边界"),
        "材料类型": config.get("材料类型", []),
        "任务列表": [
            "确认材料类型和使用场景",
            "补充真实事实依据",
            "选择对应模板",
            "生成草稿框架",
            "人工复核后再进入正式文稿"
        ],
    }
    drafts = {
        "生成时间": plan["生成时间"],
        "默认风格": config.get("输出规则", {}).get("默认风格"),
        "草稿模板": [
            {
                "材料类型": item.get("材料类型"),
                "章节": item.get("章节", []),
                "当前状态": "待补充事实依据后生成正式草稿"
            }
            for item in templates.get("模板", [])
        ],
    }

    write_json(root / "03数据" / "02任务计划" / f"办公材料计划_{timestamp}.json", plan)
    write_json(root / "03数据" / "02任务计划" / "办公材料计划_最新.json", plan)
    write_json(root / "03数据" / "03输出草稿" / f"办公材料草稿框架_{timestamp}.json", drafts)
    write_json(root / "03数据" / "03输出草稿" / "办公材料草稿框架_最新.json", drafts)
    print(json.dumps({"材料类型数量": len(plan["材料类型"]), "输出": "办公材料计划_最新.json"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
