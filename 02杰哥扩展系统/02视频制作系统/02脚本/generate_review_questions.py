# -*- coding: utf-8 -*-
"""
名称：generate_review_questions.py
作用：为轮次012视频制作影子工厂生成“待复核问题清单”。
触发方式：python generate_review_questions.py
安全边界：只做本地文件读取和复核清单写入；不读取真实素材、不渲染、不发布、不发送企业微信、不连接 n8n。
所属系统：02杰哥扩展系统/02视频制作系统
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
DATA_ROOT = ROOT / "03数据" / "18轮次012视频工厂总控层"
TASK_PATH = DATA_ROOT / "视频工厂任务单_最新.json"
DRAFT_DIR = DATA_ROOT / "草案输出"
SCRIPT_DRAFT_PATH = DRAFT_DIR / "视频脚本草案_最新.md"
STORYBOARD_DRAFT_PATH = DRAFT_DIR / "分镜草案_最新.md"
RELEASE_DIR = DATA_ROOT / "放行清单"
GENERATION_RELEASE_PATH = RELEASE_DIR / "视频生成放行清单_最新.md"
PUBLISH_RELEASE_PATH = RELEASE_DIR / "视频发布放行清单_最新.md"
OUTPUT_DIR = DATA_ROOT / "人工复核链"
ARCHIVE_DIR = OUTPUT_DIR / "archive"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_nested(data: dict[str, Any], *keys: str, default: Any = "") -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current


def release_line_for_task(text: str, task_id: str) -> str:
    for line in text.splitlines():
        if task_id and task_id in line and line.strip().startswith("|"):
            return line.strip()
    return ""


def release_state(text: str, task_id: str, state_name: str) -> str:
    line = release_line_for_task(text, task_id)
    if not line:
        return "未找到任务行"
    if state_name in line:
        return state_name
    if "待确认" in line:
        return "待确认"
    if "待生成" in line:
        return "待生成"
    return "需人工核对"


def has_creator_checklist(text: str) -> bool:
    required_items = [
        "是否有具体的生活场景或真人细节",
        "是否记得在发布平台勾选",
        "是否无意中贩卖焦虑",
    ]
    return all(item in text for item in required_items)


def build_review_payload() -> dict[str, Any]:
    task = read_json(TASK_PATH)
    script_draft = read_text(SCRIPT_DRAFT_PATH)
    storyboard_draft = read_text(STORYBOARD_DRAFT_PATH)
    generation_release = read_text(GENERATION_RELEASE_PATH)
    publish_release = read_text(PUBLISH_RELEASE_PATH)

    task_id = str(task.get("任务ID", "未知任务"))
    task_definition = task.get("任务定义", {})
    generation_control = task.get("生成控制", {})
    status = str(task.get("状态", "未知状态"))
    video_type = str(task_definition.get("视频类型", ""))
    allow_real_render = bool(generation_control.get("允许真实渲染", False))
    allow_auto_publish = bool(generation_control.get("允许自动发布", False))
    generation_state = release_state(generation_release, task_id, "放行")
    publish_state = release_state(publish_release, task_id, "发布放行")

    # 安全规则来源：用户要求生成放行、渲染放行、发布放行必须拆开；缺少素材授权和人工确认时只能输出待复核问题。
    gate_summary = {
        "任务ID": task_id,
        "当前任务状态": status,
        "生成放行清单状态": generation_state,
        "渲染放行状态": "未放行" if not allow_real_render else "配置已放行-仍需适配器二次确认",
        "发布放行清单状态": publish_state,
        "自动发布状态": "未放行" if not allow_auto_publish else "配置已放行-仍需人工二次确认",
        "真实系统触发": False,
        "结论属性": "影子复核草案，不是正式结论",
    }

    questions = [
        {
            "类别": "素材授权",
            "复核问题": "每一个分镜画面是否已明确素材来源、授权类型、可商用范围、是否含人物肖像或平台水印？",
            "未满足时处理": "不得进入真实渲染，只能继续补充素材候选和授权说明。",
        },
        {
            "类别": "素材授权",
            "复核问题": "若使用 Pexels 或本地素材，是否已记录素材链接/文件名/授权说明，并能追溯到任务ID？",
            "未满足时处理": "输出待补充素材清单，不读取真实素材文件。",
        },
        {
            "类别": "平台规则",
            "复核问题": "目标平台是否已分别确认视频比例、时长、标题限制、标签规则、AI生成内容标识要求？",
            "未满足时处理": "不得进入发布放行；由总管或人工补齐平台规则。",
        },
        {
            "类别": "内容合规",
            "复核问题": "标题和脚本是否含点击诱饵、绝对化医疗、封建迷信、焦虑贩卖或对立煽动表述？",
            "未满足时处理": "退回脚本草案修改，并重新跑合规检查。",
        },
        {
            "类别": "去AI感",
            "复核问题": "脚本中是否保留至少一个具体生活场景、真人细节或可感知动作，而不是抽象道理堆叠？",
            "未满足时处理": "补写真人化细节后再进入分镜复核。",
        },
        {
            "类别": "分镜可执行性",
            "复核问题": "分镜是否做到旁白句子、画面需求、字幕安全区、9:16/16:9适配的逐项对应？",
            "未满足时处理": "不得交给渲染适配器，先补齐镜头-素材-字幕映射。",
        },
        {
            "类别": "配音字幕封面",
            "复核问题": "TTS声音授权、字幕准确性、背景音乐授权、封面文字合规性是否已人工确认？",
            "未满足时处理": "只保留草案，不生成真实成品。",
        },
        {
            "类别": "门禁拆分",
            "复核问题": "是否明确：生成放行不等于渲染放行，渲染放行不等于发布放行，发布还需单独人工确认？",
            "未满足时处理": "暂停执行，退回门禁说明补齐。",
        },
    ]

    checks = {
        "脚本草案存在": bool(script_draft),
        "分镜草案存在": bool(storyboard_draft),
        "脚本含创作者自查清单": has_creator_checklist(script_draft),
        "分镜含创作者自查清单": has_creator_checklist(storyboard_draft),
        "任务允许真实渲染": allow_real_render,
        "任务允许自动发布": allow_auto_publish,
        "生成放行清单任务行": release_line_for_task(generation_release, task_id),
        "发布放行清单任务行": release_line_for_task(publish_release, task_id),
        "视频类型": video_type,
    }

    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务摘要": {
            "任务ID": task_id,
            "主题": get_nested(task, "任务定义", "主题", default=""),
            "视频类型": video_type,
            "当前状态": status,
        },
        "门禁摘要": gate_summary,
        "基础检查": checks,
        "待复核问题": questions,
        "安全声明": "本文件只服务视频制作影子工厂和人工复核链，未触发真实素材读取、真实渲染、真实发布或企业微信真实外发。",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["任务摘要"]
    gates = payload["门禁摘要"]
    checks = payload["基础检查"]
    questions = payload["待复核问题"]

    lines = [
        "# 轮次012 视频待复核问题清单",
        "",
        f"- 生成时间：{payload['生成时间']}",
        f"- 任务ID：{summary['任务ID']}",
        f"- 主题：{summary['主题']}",
        f"- 视频类型：{summary['视频类型']}",
        f"- 当前状态：{summary['当前状态']}",
        "- 文件属性：影子复核草案，不是正式结论",
        "- 真实系统触发：否",
        "",
        "## 门禁摘要",
        "",
    ]
    for key, value in gates.items():
        lines.append(f"- {key}：{value}")

    lines.extend(["", "## 基础检查", ""])
    for key, value in checks.items():
        shown = value if value not in ("", None) else "未记录"
        lines.append(f"- {key}：{shown}")

    lines.extend(["", "## 待人工复核问题", ""])
    for index, item in enumerate(questions, start=1):
        lines.append(f"### {index}. {item['类别']}")
        lines.append("")
        lines.append(f"- 复核问题：{item['复核问题']}")
        lines.append(f"- 未满足时处理：{item['未满足时处理']}")
        lines.append("")

    lines.extend(
        [
            "## 执行边界",
            "",
            "- 本轮只生成本地待复核清单。",
            "- 不接 n8n，不发送企业微信，不重启服务，不修改 19310。",
            "- 不读取真实素材，不接真实账号，不触发真实渲染或真实发布。",
            "- 素材授权、平台规则、人工确认任一不齐，只能停留在待复核状态。",
            "",
            f"> {payload['安全声明']}",
            "",
        ]
    )
    return "\n".join(lines)


def archive_outputs(task_id: str, stamp: str, payload: dict[str, Any], markdown: str) -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_base = f"视频待复核问题清单_{task_id}_{stamp}"
    write_json(ARCHIVE_DIR / f"{archive_base}.json", payload)
    write_text(ARCHIVE_DIR / f"{archive_base}.md", markdown)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = build_review_payload()
    markdown = render_markdown(payload)
    task_id = payload["任务摘要"]["任务ID"]

    write_json(OUTPUT_DIR / "视频待复核问题清单_最新.json", payload)
    write_text(OUTPUT_DIR / "视频待复核问题清单_最新.md", markdown)
    archive_outputs(task_id, stamp, payload, markdown)

    print("待复核问题清单生成完成，未触发真实系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
