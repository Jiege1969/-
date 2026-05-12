"""
名称：生成视频制作计划.py
作用：根据视频制作配置和模板生成第一阶段视频制作任务计划。
触发方式：python 生成视频制作计划.py
依赖：Python 标准库。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只读取本模块配置，只写入本模块任务计划、脚本草稿和分镜计划；不处理真实媒体、不上传、不发布。
创建/修改记录：2026-04-26 创建第一阶段视频制作计划脚本。
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
    config = load_json(root / "01配置" / "视频制作配置.json")
    material = load_json(root / "01配置" / "视频素材登记模板.json")
    script_template = load_json(root / "01配置" / "视频脚本模板.json")
    storyboard_template = load_json(root / "01配置" / "视频分镜模板.json")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    plan = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "系统": "02杰哥扩展系统/02视频制作系统",
        "阶段": "第一阶段任务计划",
        "安全边界": config.get("安全边界"),
        "默认流程": config.get("默认流程", []),
        "素材数量": len(material.get("素材", [])),
        "任务列表": [
            "确认视频主题、受众和目标时长",
            "核查素材授权状态",
            "生成口播脚本草稿",
            "生成分镜计划",
            "列出字幕要点和封面标题",
            "等待人工审核后进入剪辑阶段"
        ],
    }
    script_draft = {
        "生成时间": plan["生成时间"],
        "脚本结构": script_template.get("脚本结构", []),
        "默认风格": script_template.get("默认风格"),
        "安全要求": script_template.get("安全要求", []),
        "当前状态": "待填写主题后生成正式口播稿",
    }
    storyboard = {
        "生成时间": plan["生成时间"],
        "镜头字段": storyboard_template.get("镜头字段", []),
        "镜头": storyboard_template.get("默认镜头", []),
        "当前状态": "待人工补充素材后进入剪辑",
    }

    write_json(root / "03数据" / "04任务计划" / f"视频制作计划_{timestamp}.json", plan)
    write_json(root / "03数据" / "04任务计划" / "视频制作计划_最新.json", plan)
    write_json(root / "03数据" / "02脚本草稿" / f"视频脚本草稿_{timestamp}.json", script_draft)
    write_json(root / "03数据" / "02脚本草稿" / "视频脚本草稿_最新.json", script_draft)
    write_json(root / "03数据" / "03分镜计划" / f"视频分镜计划_{timestamp}.json", storyboard)
    write_json(root / "03数据" / "03分镜计划" / "视频分镜计划_最新.json", storyboard)
    print(json.dumps({"素材数量": plan["素材数量"], "输出": "视频制作计划_最新.json"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
