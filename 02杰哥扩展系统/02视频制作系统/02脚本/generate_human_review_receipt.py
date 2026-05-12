# -*- coding: utf-8 -*-
"""
名称：generate_human_review_receipt.py
作用：为轮次012视频工厂生成本地人工复核回执模板。
触发方式：python generate_human_review_receipt.py
安全边界：只生成本地待填写回执；不读取真实素材、不访问平台、不连接账号、不渲染、不发布、不发送企业微信、不连接 n8n。
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
REVIEW_ROOT = DATA_ROOT / "人工复核链"
READINESS_PATH = REVIEW_ROOT / "准备度快照" / "人工复核准备度快照_最新.json"
OUTPUT_DIR = REVIEW_ROOT / "人工复核回执"
ARCHIVE_DIR = OUTPUT_DIR / "archive"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def nested_value(data: dict[str, Any], *keys: str, default: Any = "") -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current if current not in (None, "") else default


def build_receipt(task: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    task_id = str(task.get("任务ID", "未知任务"))
    return {
        "模板名称": "人工复核回执模板",
        "模板状态": "待人工填写",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "主题": nested_value(task, "任务定义", "主题", default=""),
        "当前任务状态": task.get("状态", "未知状态"),
        "准备度快照结论": readiness.get("结论", "未读取"),
        "真实系统触发": False,
        "复核人信息": {
            "复核人": "待填写",
            "复核时间": "待填写",
            "复核来源": "待填写：企业微信/本地人工/其他",
        },
        "复核项": [
            {
                "类别": "脚本文案",
                "检查点": "是否有真人生活化细节、是否去AI感、是否避免焦虑贩卖和绝对化表达",
                "人工结论": "待确认",
                "修改意见": "待填写",
            },
            {
                "类别": "分镜可执行性",
                "检查点": "是否完成旁白、画面、字幕安全区、9:16/16:9适配的对应关系",
                "人工结论": "待确认",
                "修改意见": "待填写",
            },
            {
                "类别": "素材授权",
                "检查点": "是否逐镜头补齐素材来源、授权证明、可商用范围、肖像/隐私/商标/水印风险",
                "人工结论": "待确认",
                "修改意见": "待填写",
            },
            {
                "类别": "平台规则",
                "检查点": "是否逐平台补齐官方规则来源、比例/时长/标题/标签/分区要求",
                "人工结论": "待确认",
                "修改意见": "待填写",
            },
            {
                "类别": "AI内容标识",
                "检查点": "是否确认各平台发布时的AI生成内容标识、勾选或声明要求",
                "人工结论": "待确认",
                "修改意见": "待填写",
            },
            {
                "类别": "配音字幕封面",
                "检查点": "是否确认TTS授权、字幕准确性、音乐授权和封面文字合规",
                "人工结论": "待确认",
                "修改意见": "待填写",
            },
        ],
        "门禁结论": {
            "是否允许继续脚本修订": "待确认",
            "是否允许生成放行": "待确认，仅代表进入生成清单，不代表真实渲染",
            "是否允许真实渲染": "默认否，必须另走真实渲染放行",
            "是否允许发布放行": "默认否，必须另走发布放行清单",
            "是否允许自动发布": "默认否",
        },
        "强制阻断项": [
            "素材授权未齐时，阻断真实渲染",
            "平台规则和AI标识未齐时，阻断发布放行",
            "发布放行清单未登记当前任务时，阻断发布",
            "人工复核回执不得自动改写任务状态、生成清单、渲染配置或发布清单",
        ],
        "边界声明": [
            "本回执模板只供人工填写，不是正式放行结论",
            "不读取真实素材、不访问平台、不连接真实账号、不发送企业微信、不接 n8n",
            "生成放行、真实渲染放行、发布放行必须拆开",
        ],
    }


def render_markdown(receipt: dict[str, Any]) -> str:
    lines = [
        "# 轮次012 人工复核回执模板",
        "",
        f"- 生成时间：{receipt['生成时间']}",
        f"- 任务ID：{receipt['任务ID']}",
        f"- 主题：{receipt['主题']}",
        f"- 当前任务状态：{receipt['当前任务状态']}",
        f"- 模板状态：{receipt['模板状态']}",
        f"- 准备度快照结论：{receipt['准备度快照结论']}",
        "- 真实系统触发：否",
        "",
        "## 复核人信息",
        "",
    ]
    for key, value in receipt["复核人信息"].items():
        lines.append(f"- {key}：{value}")

    lines.extend(
        [
            "",
            "## 复核项",
            "",
            "| 类别 | 检查点 | 人工结论 | 修改意见 |",
            "|---|---|---|---|",
        ]
    )
    for item in receipt["复核项"]:
        lines.append(f"| {item['类别']} | {item['检查点']} | {item['人工结论']} | {item['修改意见']} |")

    lines.extend(["", "## 门禁结论", ""])
    for key, value in receipt["门禁结论"].items():
        lines.append(f"- {key}：{value}")

    lines.extend(["", "## 强制阻断项", ""])
    for item in receipt["强制阻断项"]:
        lines.append(f"- [ ] {item}")

    lines.extend(["", "## 边界声明", ""])
    for item in receipt["边界声明"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task = read_json(TASK_PATH)
    readiness = read_json(READINESS_PATH)
    receipt = build_receipt(task, readiness)
    markdown = render_markdown(receipt)
    task_id = receipt["任务ID"]

    write_json(OUTPUT_DIR / "人工复核回执模板_最新.json", receipt)
    write_text(OUTPUT_DIR / "人工复核回执模板_最新.md", markdown)
    write_json(ARCHIVE_DIR / f"人工复核回执模板_{task_id}_{stamp}.json", receipt)
    write_text(ARCHIVE_DIR / f"人工复核回执模板_{task_id}_{stamp}.md", markdown)

    print("人工复核回执模板生成完成，未触发真实系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
