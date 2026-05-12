"""
名称：生成视频主题化预演.py
作用：基于视频脚本草稿、分镜计划和主题化生成规则，生成主题方案、字幕要点和封面标题预演。
触发方式：python 生成视频主题化预演.py
依赖：Python 标准库；需已有视频制作计划、脚本草稿和分镜计划。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只生成本地预演文件；不处理真实媒体、不调用剪辑软件、不上传、不发布。
创建/修改记录：2026-04-27 创建视频主题化预演脚本。
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


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_plan() -> None:
    root = module_root()
    required = [
        root / "03数据" / "02脚本草稿" / "视频脚本草稿_最新.json",
        root / "03数据" / "03分镜计划" / "视频分镜计划_最新.json",
    ]
    if all(path.exists() for path in required):
        return
    script = root / "02脚本" / "生成视频制作计划.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)


def main() -> int:
    ensure_plan()
    root = module_root()
    rules = load_json(root / "01配置" / "视频主题化生成规则.json")
    script_draft = load_json(root / "03数据" / "02脚本草稿" / "视频脚本草稿_最新.json")
    storyboard = load_json(root / "03数据" / "03分镜计划" / "视频分镜计划_最新.json")
    directions = rules.get("主题方向", [])
    shots = storyboard.get("镜头", [])
    theme = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "阶段": "视频主题化预演",
        "脚本来源状态": script_draft.get("当前状态"),
        "分镜来源状态": storyboard.get("当前状态"),
        "主题方案": [
            {
                "方向": direction,
                "主题": f"{direction}：围绕一个核心问题展开",
                "受众": "待人工确认",
                "表达风格": script_draft.get("默认风格"),
            }
            for direction in directions
        ],
        "字幕要点": [
            {
                "镜头编号": shot.get("镜头编号"),
                "画面内容": shot.get("画面内容"),
                "字幕": f"{shot.get('字幕要点', '要点')}：保留人工复核",
                "时长秒": shot.get("时长秒"),
            }
            for shot in shots
        ],
        "封面标题预演": [
            "一个核心问题，讲清楚",
            "从现象到判断的清晰路径",
            "先看结论，再看依据",
        ][: rules.get("封面标题规则", {}).get("数量", 3)],
        "发布前检查": [
            "主题已人工确认",
            "事实依据已人工确认",
            "素材授权已人工确认",
            "字幕和封面标题已人工确认",
        ],
        "安全边界": rules.get("安全边界", {}),
        "是否调用剪辑软件": False,
        "是否生成真实媒体": False,
        "是否上传发布": False,
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = root / "03数据" / "07主题化预演" / f"视频主题化预演_{timestamp}.json"
    latest = root / "03数据" / "07主题化预演" / "视频主题化预演_最新.json"
    write_json(output, theme)
    write_json(latest, theme)
    print(json.dumps({"主题方案数量": len(theme["主题方案"]), "字幕要点数量": len(theme["字幕要点"]), "输出": str(output)}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
