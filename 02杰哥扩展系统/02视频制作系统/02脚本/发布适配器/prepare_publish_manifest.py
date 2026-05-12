# -*- coding: utf-8 -*-
"""
名称：prepare_publish_manifest.py
作用：从轮次012任务单和草案文件生成发布元数据，并回填视频发布放行清单。
触发方式：python prepare_publish_manifest.py [--task-id VF-YYYYMMDD-001] [--platforms B站,小红书]
依赖：Python 标准库；轮次012任务单、草案输出、视频发布放行清单。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只生成发布元数据并回填清单；不把任务自动改为“放行”，不上传、不发布、不触发n8n或企业微信真实发送。
创建/修改记录：2026-05-08 创建发布清单自动填充工具。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


ROOT = module_root()
ROUND_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层"
TASK_PATH = ROUND_DIR / "视频工厂任务单_最新.json"
SCRIPT_DRAFT_PATH = ROUND_DIR / "草案输出" / "视频脚本草案_最新.md"
STORYBOARD_DRAFT_PATH = ROUND_DIR / "草案输出" / "分镜草案_最新.md"
RELEASE_PATH = ROUND_DIR / "放行清单" / "视频发布放行清单_最新.md"
OUTPUT_DIR = ROUND_DIR / "发布元数据"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
LATEST_JSON = OUTPUT_DIR / "发布元数据_最新.json"
LATEST_MD = OUTPUT_DIR / "发布元数据_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def split_list(value: str) -> list[str]:
    parts = [value.strip()]
    for separator in [",", "，", "、", ";", "；", " "]:
        next_parts: list[str] = []
        for item in parts:
            next_parts.extend(piece.strip() for piece in item.split(separator))
        parts = next_parts
    return [item for item in parts if item]


def clean_title(text: str) -> str:
    text = re.sub(r"[“”\"']", "", text.strip())
    text = re.sub(r"\s+", "", text)
    return text[:30] if text else "视频工厂短视频"


def extract_task_title(task: dict[str, Any]) -> str:
    task_def = task.get("任务定义", {})
    topic = str(task_def.get("主题", ""))
    if "掩耳盗铃" in topic:
        return "掩耳盗铃：听不见问题，不等于问题不存在"
    if "吃亏是福" in topic:
        return "吃亏是福，真正难懂的是边界"
    if "30" in topic and "朋友" in topic:
        return "30岁以后，交朋友为什么变难"
    return clean_title(topic)


def build_desc(task: dict[str, Any], script_text: str) -> str:
    task_def = task.get("任务定义", {})
    topic = task_def.get("主题", "")
    angle = task_def.get("表达角度", "")
    audience = task_def.get("受众人群", "")
    desc = f"这期聊：{topic}。角度：{angle}。适合：{audience}。"
    if "古今结合举例" in read_text(STORYBOARD_DRAFT_PATH):
        desc += " 本期包含古今结合的原创解读。"
    desc += " 内容由AI辅助生成，发布前已人工复核。"
    return desc[:240]


def build_tags(task: dict[str, Any]) -> list[str]:
    task_def = task.get("任务定义", {})
    video_type = str(task_def.get("视频类型", ""))
    tags = ["AI生成", "杰哥视频工厂"]
    if "成语故事" in video_type:
        tags.extend(["成语故事", "传统文化", "人生启发"])
    elif "经典语录" in video_type:
        tags.extend(["经典语录", "生活感悟", "人生哲理"])
    else:
        tags.extend(["生活感悟", "人生哲理"])
    return list(dict.fromkeys(tags))


def find_video_candidate(task_id: str) -> str:
    search_dirs = [
        ROUND_DIR / "成品库",
        ROUND_DIR / "草案输出",
        ROOT / "03数据",
    ]
    suffixes = {".mp4", ".mov", ".mkv", ".avi"}
    candidates: list[Path] = []
    for directory in search_dirs:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in suffixes:
                if task_id in path.name or not candidates:
                    candidates.append(path)
    return str(candidates[0]) if candidates else ""


def parse_table(text: str) -> tuple[list[str], list[dict[str, str]]]:
    lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        return [], []
    headers = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells, strict=True)))
    return headers, rows


def render_release(headers: list[str], rows: list[dict[str, str]]) -> str:
    lines = [
        "# 视频发布放行清单",
        "",
        "> 安全约束：生成放行不等于发布放行。必须人工预览成品后，再在此清单中单独放行发布。",
        "> 所有发布操作均需读取此清单，未放行任务不得发布。",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "-")) or "-" for header in headers) + " |")
    return "\n".join(lines) + "\n"


def upsert_release(metadata: dict[str, Any]) -> None:
    desired = ["任务ID", "生成状态", "发布放行状态", "放行时间", "放行人", "视频文件", "标题", "简介", "标签", "平台", "账号", "B站分区ID", "发布结果"]
    headers, rows = parse_table(read_text(RELEASE_PATH))
    if headers != desired:
        rows = [{header: row.get(header, "-") for header in desired} for row in rows]
        headers = desired
    found = False
    for row in rows:
        if row.get("任务ID") == metadata["任务ID"]:
            found = True
            row["生成状态"] = metadata["生成状态"]
            row["发布放行状态"] = "待确认" if row.get("发布放行状态") != "放行" else row["发布放行状态"]
            row["视频文件"] = metadata["视频文件"] or row.get("视频文件", "-")
            row["标题"] = metadata["标题"]
            row["简介"] = metadata["简介"]
            row["标签"] = "，".join(metadata["标签"])
            row["平台"] = "，".join(metadata["平台"])
            row["账号"] = metadata["账号"]
            row["B站分区ID"] = metadata["B站分区ID"]
    if not found:
        rows.append({
            "任务ID": metadata["任务ID"],
            "生成状态": metadata["生成状态"],
            "发布放行状态": "待确认",
            "放行时间": "-",
            "放行人": "-",
            "视频文件": metadata["视频文件"] or "-",
            "标题": metadata["标题"],
            "简介": metadata["简介"],
            "标签": "，".join(metadata["标签"]),
            "平台": "，".join(metadata["平台"]),
            "账号": metadata["账号"],
            "B站分区ID": metadata["B站分区ID"],
            "发布结果": "-",
        })
    write_text(RELEASE_PATH, render_release(headers, rows))


def build_markdown(metadata: dict[str, Any]) -> str:
    return "\n".join([
        "# 轮次012 发布元数据",
        "",
        f"- 生成时间：{metadata.get('生成时间')}",
        f"- 任务ID：{metadata.get('任务ID')}",
        f"- 视频文件：{metadata.get('视频文件') or '未找到'}",
        f"- 标题：{metadata.get('标题')}",
        f"- 简介：{metadata.get('简介')}",
        f"- 标签：{'，'.join(metadata.get('标签', []))}",
        f"- 平台：{'，'.join(metadata.get('平台', []))}",
        f"- 账号：{metadata.get('账号')}",
        f"- B站分区ID：{metadata.get('B站分区ID')}",
        "",
        "## 安全提示",
        "",
        "- 本工具只填充发布清单，不自动放行发布。",
        "- 未找到视频文件时，发布预检会继续提醒补齐成品路径。",
        "- 发布前仍需人工预览、AI标识确认和企业微信精确确认口令。",
        "",
    ])


def generate_metadata(task_id: str, platforms: list[str], account: str) -> dict[str, Any]:
    task = read_json(TASK_PATH)
    script_text = read_text(SCRIPT_DRAFT_PATH)
    current_id = str(task.get("任务ID", ""))
    resolved_id = task_id or current_id
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": resolved_id,
        "生成状态": "已生成待预览",
        "视频文件": find_video_candidate(resolved_id),
        "标题": extract_task_title(task),
        "简介": build_desc(task, script_text),
        "标签": build_tags(task),
        "平台": platforms or ["B站"],
        "账号": account or "creator",
        "B站分区ID": "249",
    }


def save_metadata(metadata: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(metadata)
    write_json(LATEST_JSON, metadata)
    write_text(LATEST_MD, markdown)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"发布元数据_{metadata['任务ID']}_{timestamp}.json", metadata)
    write_text(ARCHIVE_DIR / f"发布元数据_{metadata['任务ID']}_{timestamp}.md", markdown)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="轮次012发布清单自动填充")
    parser.add_argument("--task-id", default="", help="任务ID；为空则使用最新任务单")
    parser.add_argument("--platforms", default="B站", help="发布平台，多个用逗号分隔")
    parser.add_argument("--account", default="creator", help="发布账号")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metadata = generate_metadata(args.task_id, split_list(args.platforms), args.account)
    save_metadata(metadata)
    upsert_release(metadata)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
