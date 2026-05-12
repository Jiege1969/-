# -*- coding: utf-8 -*-
"""
名称：generate_generation_release_advice.py
作用：基于一致性检查结果生成轮次012视频工厂生成放行建议单。
触发方式：python generate_generation_release_advice.py
安全边界：只生成本地人工参考建议；不修改放行清单、不读取真实素材、不访问平台、不连接账号、不渲染、不发布、不发送企业微信、不连接 n8n。
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
CONSISTENCY_PATH = REVIEW_ROOT / "一致性检查" / "复核结果与放行清单一致性检查_最新.json"
OUTPUT_DIR = REVIEW_ROOT / "放行建议"
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


def build_advice(task: dict[str, Any], consistency: dict[str, Any]) -> dict[str, Any]:
    task_id = str(task.get("任务ID", consistency.get("任务ID", "未知任务")))
    generation_status = str(consistency.get("生成放行状态", "未知"))
    publish_status = str(consistency.get("发布放行状态", "未知"))
    allow_render = bool(nested_value(task, "生成控制", "允许真实渲染", default=False))
    allow_publish = bool(nested_value(task, "生成控制", "允许自动发布", default=False))

    advice_result = "仅建议维持人工复核链，不进入真实渲染"
    if generation_status == "生成放行已登记" and not allow_render:
        advice_result = "生成放行已有登记，但真实渲染仍阻断"
    elif generation_status != "生成放行已登记":
        advice_result = "不建议生成执行；需人工先核对生成放行清单"

    return {
        "建议单名称": "生成放行建议单",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "当前任务状态": task.get("状态", "未知状态"),
        "主题": nested_value(task, "任务定义", "主题", default=""),
        "真实系统触发": False,
        "生成放行清单状态": generation_status,
        "发布放行清单状态": publish_status,
        "任务单允许真实渲染": allow_render,
        "任务单允许自动发布": allow_publish,
        "建议结论": advice_result,
        "建议给人工确认的事项": [
            "确认当前生成放行仅代表可以进入生成放行讨论或队列登记，不代表真实渲染。",
            "确认素材授权、平台规则、AI标识、配音字幕封面授权仍需逐项复核。",
            "确认真实渲染必须另走真实渲染放行，不得由生成放行自动继承。",
            "确认发布必须另走发布放行清单，不得由生成放行自动继承。",
        ],
        "不得自动执行的事项": [
            "不得自动修改视频生成放行清单。",
            "不得自动修改视频发布放行清单。",
            "不得调用 MoneyPrinterTurbo、Pixelle-Video 或任何渲染适配器。",
            "不得调用 PostBot、MoneyPrinterPlus 或任何发布适配器。",
            "不得通过企业微信真实发送执行结果或发布命令。",
            "不得连接 n8n、真实账号、平台后台或素材库。",
        ],
        "下一步建议": [
            "若人工只想继续完善草案：返回脚本、分镜、素材授权和平台规则复核链。",
            "若人工想推进真实渲染：交回总管判断真实渲染放行条件，本业务线只登记阻断项。",
            "若人工想推进发布：先补发布放行前问题卡，确认AI标识、平台规则、账号状态和成品预览。",
        ],
        "边界声明": [
            "本建议单只供人工参考，不是生成放行、真实渲染放行或发布放行凭证。",
            "本建议单不修改任何清单、任务单、配置或适配器。",
            "不读取真实素材、不访问平台、不连接真实账号。",
            "不发送企业微信。",
            "不接 n8n。",
            "生成放行、真实渲染放行、发布放行必须拆开。",
        ],
    }


def render_markdown(advice: dict[str, Any]) -> str:
    lines = [
        "# 轮次012 生成放行建议单",
        "",
        f"- 生成时间：{advice['生成时间']}",
        f"- 任务ID：{advice['任务ID']}",
        f"- 当前任务状态：{advice['当前任务状态']}",
        f"- 主题：{advice['主题']}",
        "- 真实系统触发：否",
        f"- 生成放行清单状态：{advice['生成放行清单状态']}",
        f"- 发布放行清单状态：{advice['发布放行清单状态']}",
        f"- 任务单允许真实渲染：{advice['任务单允许真实渲染']}",
        f"- 任务单允许自动发布：{advice['任务单允许自动发布']}",
        f"- 建议结论：{advice['建议结论']}",
        "",
        "## 建议给人工确认的事项",
        "",
    ]
    for item in advice["建议给人工确认的事项"]:
        lines.append(f"- [ ] {item}")

    lines.extend(["", "## 不得自动执行的事项", ""])
    for item in advice["不得自动执行的事项"]:
        lines.append(f"- [ ] {item}")

    lines.extend(["", "## 下一步建议", ""])
    for item in advice["下一步建议"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 边界声明", ""])
    for item in advice["边界声明"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task = read_json(TASK_PATH)
    consistency = read_json(CONSISTENCY_PATH)
    advice = build_advice(task, consistency)
    markdown = render_markdown(advice)
    task_id = advice["任务ID"]

    write_json(OUTPUT_DIR / "生成放行建议单_最新.json", advice)
    write_text(OUTPUT_DIR / "生成放行建议单_最新.md", markdown)
    write_json(ARCHIVE_DIR / f"生成放行建议单_{task_id}_{stamp}.json", advice)
    write_text(ARCHIVE_DIR / f"生成放行建议单_{task_id}_{stamp}.md", markdown)

    print("生成放行建议单生成完成，未触发真实系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
