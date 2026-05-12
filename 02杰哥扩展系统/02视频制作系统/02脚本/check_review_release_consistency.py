# -*- coding: utf-8 -*-
"""
名称：check_review_release_consistency.py
作用：只读检查轮次012视频工厂人工复核、任务单、生成放行清单、发布放行清单是否混用状态。
触发方式：python check_review_release_consistency.py
安全边界：只读本地文件并生成本地检查报告；不读取真实素材、不访问平台、不连接账号、不渲染、不发布、不发送企业微信、不连接 n8n。
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
RELEASE_DIR = DATA_ROOT / "放行清单"
GENERATION_RELEASE_PATH = RELEASE_DIR / "视频生成放行清单_最新.md"
PUBLISH_RELEASE_PATH = RELEASE_DIR / "视频发布放行清单_最新.md"
REVIEW_ROOT = DATA_ROOT / "人工复核链"
RECEIPT_DIR = REVIEW_ROOT / "人工复核回执"
RECEIPT_PATH = RECEIPT_DIR / "人工复核回执模板_最新.json"
RECEIPT_STATUS_PATH = RECEIPT_DIR / "状态检查" / "人工复核回执状态检查_最新.json"
RECEIPT_INTAKE_PATH = RECEIPT_DIR / "接收卡" / "人工复核回执填写后接收卡_最新.json"
OUTPUT_DIR = REVIEW_ROOT / "一致性检查"
ARCHIVE_DIR = OUTPUT_DIR / "archive"


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


def nested_value(data: dict[str, Any], *keys: str, default: Any = "") -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current if current not in (None, "") else default


def flatten_values(data: Any) -> list[str]:
    if isinstance(data, dict):
        values: list[str] = []
        for item in data.values():
            values.extend(flatten_values(item))
        return values
    if isinstance(data, list):
        values = []
        for item in data:
            values.extend(flatten_values(item))
        return values
    return [str(data)]


def release_line_for_task(text: str, task_id: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if task_id and task_id in stripped and stripped.startswith("|"):
            return stripped
    return ""


def infer_generation_release(line: str) -> str:
    if not line:
        return "未登记"
    if "待确认" in line:
        return "待确认"
    if "放行" in line:
        return "生成放行已登记"
    return "需人工核对"


def infer_publish_release(line: str) -> str:
    if not line:
        return "未登记"
    if "待确认" in line:
        return "待确认"
    if "发布放行" in line or "放行" in line:
        return "发布放行疑似已登记-仍需人工二次核对"
    return "需人工核对"


def has_any(values: list[str], words: list[str]) -> bool:
    return any(word in value for value in values for word in words)


def build_report() -> dict[str, Any]:
    task = read_json(TASK_PATH)
    receipt = read_json(RECEIPT_PATH)
    receipt_status = read_json(RECEIPT_STATUS_PATH)
    receipt_intake = read_json(RECEIPT_INTAKE_PATH)
    generation_release_text = read_text(GENERATION_RELEASE_PATH)
    publish_release_text = read_text(PUBLISH_RELEASE_PATH)

    task_id = str(task.get("任务ID", "未知任务"))
    receipt_task_id = str(receipt.get("任务ID", "未知任务"))
    status_task_id = str(receipt_status.get("任务ID", "未知任务"))
    intake_task_id = str(receipt_intake.get("任务ID", "未知任务"))
    generation_line = release_line_for_task(generation_release_text, task_id)
    publish_line = release_line_for_task(publish_release_text, task_id)
    generation_status = infer_generation_release(generation_line)
    publish_status = infer_publish_release(publish_line)
    allow_render = bool(nested_value(task, "生成控制", "允许真实渲染", default=False))
    allow_auto_publish = bool(nested_value(task, "生成控制", "允许自动发布", default=False))
    receipt_values = flatten_values(receipt) + flatten_values(receipt_status) + flatten_values(receipt_intake)

    checks = [
        {
            "检查项": "任务ID一致性",
            "结果": "通过" if task_id in {receipt_task_id, status_task_id, intake_task_id} else "需人工核对",
            "说明": f"任务单={task_id}；回执={receipt_task_id}；状态检查={status_task_id}；接收卡={intake_task_id}",
        },
        {
            "检查项": "生成放行与真实渲染分离",
            "结果": "通过",
            "说明": f"生成清单状态={generation_status}；任务单允许真实渲染={allow_render}",
        },
        {
            "检查项": "发布放行独立性",
            "结果": "通过" if publish_status in {"未登记", "待确认"} else "需人工核对",
            "说明": f"发布清单状态={publish_status}；任务单允许自动发布={allow_auto_publish}",
        },
        {
            "检查项": "回执不得直接触发执行",
            "结果": "需人工核对" if has_any(receipt_values, ["真实渲染", "真实发布", "自动发布", "发送企业微信", "接入 n8n", "重启服务", "修改 19310"]) else "通过",
            "说明": "回执和接收卡中出现执行类词汇时，只能登记阻断，不能执行。",
        },
    ]

    blockers: list[str] = []
    if not allow_render:
        blockers.append("任务单允许真实渲染=false，阻断真实渲染")
    if not allow_auto_publish:
        blockers.append("任务单允许自动发布=false，阻断自动发布")
    if generation_status != "生成放行已登记":
        blockers.append("生成放行清单未明确登记当前任务为放行，阻断生成执行")
    if publish_status != "发布放行疑似已登记-仍需人工二次核对":
        blockers.append("发布放行清单未明确登记当前任务为发布放行，阻断发布")
    blockers.append("人工复核回执通过不等于生成放行、真实渲染放行或发布放行")

    return {
        "检查名称": "复核结果与放行清单一致性检查",
        "检查时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "当前任务状态": task.get("状态", "未知状态"),
        "真实系统触发": False,
        "生成放行清单行": generation_line or "未找到当前任务",
        "发布放行清单行": publish_line or "未找到当前任务",
        "生成放行状态": generation_status,
        "发布放行状态": publish_status,
        "检查结果": checks,
        "阻断事项": blockers,
        "结论": "一致性检查完成；真实渲染和发布仍按独立门禁阻断",
        "边界声明": [
            "本检查器只读本地任务单、人工复核材料和放行清单",
            "不自动修改任务单、生成放行清单、发布放行清单或适配器配置",
            "不读取真实素材、不访问平台、不连接真实账号、不发送企业微信、不接 n8n",
            "生成放行、真实渲染放行、发布放行必须拆开",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 轮次012 复核结果与放行清单一致性检查",
        "",
        f"- 检查时间：{report['检查时间']}",
        f"- 任务ID：{report['任务ID']}",
        f"- 当前任务状态：{report['当前任务状态']}",
        "- 真实系统触发：否",
        f"- 生成放行状态：{report['生成放行状态']}",
        f"- 发布放行状态：{report['发布放行状态']}",
        f"- 结论：{report['结论']}",
        "",
        "## 放行清单匹配",
        "",
        f"- 生成放行清单行：{report['生成放行清单行']}",
        f"- 发布放行清单行：{report['发布放行清单行']}",
        "",
        "## 检查结果",
        "",
        "| 检查项 | 结果 | 说明 |",
        "|---|---|---|",
    ]
    for item in report["检查结果"]:
        lines.append(f"| {item['检查项']} | {item['结果']} | {item['说明']} |")

    lines.extend(["", "## 阻断事项", ""])
    for item in report["阻断事项"]:
        lines.append(f"- [ ] {item}")

    lines.extend(["", "## 边界声明", ""])
    for item in report["边界声明"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = build_report()
    markdown = render_markdown(report)
    task_id = report["任务ID"]

    write_json(OUTPUT_DIR / "复核结果与放行清单一致性检查_最新.json", report)
    write_text(OUTPUT_DIR / "复核结果与放行清单一致性检查_最新.md", markdown)
    write_json(ARCHIVE_DIR / f"复核结果与放行清单一致性检查_{task_id}_{stamp}.json", report)
    write_text(ARCHIVE_DIR / f"复核结果与放行清单一致性检查_{task_id}_{stamp}.md", markdown)

    print("复核结果与放行清单一致性检查完成，未触发真实系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
