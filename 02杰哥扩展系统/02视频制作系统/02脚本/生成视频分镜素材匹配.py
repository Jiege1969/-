"""
名称：生成视频分镜素材匹配.py
作用：读取最新分镜计划和视频素材候选，生成每个镜头的素材匹配预演。
触发方式：python 生成视频分镜素材匹配.py
依赖：Python 标准库；需已有视频分镜计划和视频素材候选。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只生成匹配预演，不复制、不移动、不删除、不转码素材，不调用剪辑软件。
创建/修改记录：2026-04-27 创建视频分镜素材匹配预演脚本。
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


def ensure_candidates(root: Path) -> Path:
    latest = root / "03数据" / "05素材候选" / "视频素材候选_最新.json"
    if latest.exists():
        return latest
    script = root / "02脚本" / "生成视频素材候选.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def ensure_storyboard(root: Path) -> Path:
    latest = root / "03数据" / "03分镜计划" / "视频分镜计划_最新.json"
    if latest.exists():
        return latest
    script = root / "02脚本" / "生成视频制作计划.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    return latest


def preferred_types(requirement: str, rules: dict[str, Any]) -> list[str]:
    for rule in rules.get("匹配规则", []):
        if any(keyword in requirement for keyword in rule.get("镜头需求关键词", [])):
            return rule.get("优先素材类型", [])
    return ["视频", "图片", "文档", "音频"]


def build_matches() -> dict[str, Any]:
    root = module_root()
    rules = load_json(root / "01配置" / "视频素材桥接规则.json")
    storyboard_path = ensure_storyboard(root)
    candidates_path = ensure_candidates(root)
    storyboard = load_json(storyboard_path)
    candidates_data = load_json(candidates_path)
    output_dir = root / "03数据" / "06分镜素材匹配"
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates = candidates_data.get("素材候选", [])
    matches = []
    for shot in storyboard.get("镜头", []):
        requirement = str(shot.get("素材需求", ""))
        pref = preferred_types(requirement, rules)
        ranked = sorted(
            candidates,
            key=lambda item: (
                pref.index(item.get("素材类型")) if item.get("素材类型") in pref else 99,
                not item.get("是否优先素材", False),
                item.get("文件名", ""),
            ),
        )
        selected = ranked[:3]
        matches.append(
            {
                "镜头编号": shot.get("镜头编号"),
                "画面内容": shot.get("画面内容"),
                "素材需求": requirement,
                "优先类型": pref,
                "候选素材": selected,
                "是否需要人工确认": True,
                "是否调用剪辑软件": False,
                "是否复制素材": False,
                "是否转码素材": False,
                "匹配结论": "有候选素材，等待人工确认" if selected else "暂无候选素材",
            }
        )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "分镜来源": str(storyboard_path),
        "素材候选来源": str(candidates_path),
        "匹配数量": len(matches),
        "匹配": matches,
        "是否调用剪辑软件": False,
        "是否复制素材": False,
        "是否移动素材": False,
        "是否删除素材": False,
        "是否转码素材": False,
        "安全说明": "分镜素材匹配只做候选推荐，所有素材授权、主题匹配和剪辑动作均需人工确认。",
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"视频分镜素材匹配_{timestamp}.json"
    latest = output_dir / "视频分镜素材匹配_最新.json"
    text = json.dumps(report, ensure_ascii=False, indent=2)
    output.write_text(text, encoding="utf-8")
    latest.write_text(text, encoding="utf-8")
    print(json.dumps({"match_count": len(matches), "output": str(output)}, ensure_ascii=True))
    return report


def main() -> int:
    build_matches()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
