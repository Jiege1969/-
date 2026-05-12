# -*- coding: utf-8 -*-
"""
名称：check_human_review_receipt_status.py
作用：只读检查轮次012人工复核回执填写状态。
触发方式：python check_human_review_receipt_status.py
安全边界：只读取本地回执模板并写入本地状态报告；不读取真实素材、不访问平台、不连接账号、不渲染、不发布、不发送企业微信、不连接 n8n。
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
RECEIPT_DIR = DATA_ROOT / "人工复核链" / "人工复核回执"
RECEIPT_JSON = RECEIPT_DIR / "人工复核回执模板_最新.json"
OUTPUT_DIR = RECEIPT_DIR / "状态检查"
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


def contains_pending(value: Any) -> bool:
    text = str(value)
    return any(token in text for token in ["待填写", "待确认", "默认否"])


def build_status(receipt: dict[str, Any]) -> dict[str, Any]:
    review_items = receipt.get("复核项", [])
    gate_items = receipt.get("门禁结论", {})

    pending_review = []
    for item in review_items:
        if contains_pending(item.get("人工结论", "")) or contains_pending(item.get("修改意见", "")):
            pending_review.append(
                {
                    "类别": item.get("类别", ""),
                    "人工结论": item.get("人工结论", ""),
                    "修改意见": item.get("修改意见", ""),
                }
            )

    pending_gates = []
    for key, value in gate_items.items():
        if contains_pending(value):
            pending_gates.append({"门禁项": key, "当前值": value})

    blocking = [
        "回执状态检查只读，不得自动改写任务单、生成清单、渲染配置或发布清单",
        "回执填写完成也不等于生成放行、真实渲染放行或发布放行",
    ]
    if pending_review:
        blocking.append("存在待确认复核项，阻断真实渲染和发布")
    if pending_gates:
        blocking.append("存在待确认门禁项，阻断真实渲染和发布")

    if not receipt:
        status = "未找到回执"
    elif pending_review or pending_gates:
        status = "待人工继续填写"
    else:
        status = "回执字段表面已填完-仍需人工判断"

    return {
        "检查时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": receipt.get("任务ID", "未知任务"),
        "主题": receipt.get("主题", ""),
        "真实系统触发": False,
        "回执状态": status,
        "待处理复核项": pending_review,
        "待处理门禁项": pending_gates,
        "强制阻断": blocking,
        "边界声明": [
            "本状态检查只读本地回执，不是正式放行结论",
            "不读取真实素材、不访问平台、不连接真实账号、不发送企业微信、不接 n8n",
            "生成放行、真实渲染放行、发布放行必须拆开",
        ],
    }


def render_markdown(status: dict[str, Any]) -> str:
    lines = [
        "# 轮次012 人工复核回执状态只读检查",
        "",
        f"- 检查时间：{status['检查时间']}",
        f"- 任务ID：{status['任务ID']}",
        f"- 主题：{status['主题']}",
        "- 真实系统触发：否",
        f"- 回执状态：{status['回执状态']}",
        "",
        "## 待处理复核项",
        "",
    ]
    if status["待处理复核项"]:
        lines.extend(["| 类别 | 人工结论 | 修改意见 |", "|---|---|---|"])
        for item in status["待处理复核项"]:
            lines.append(f"| {item['类别']} | {item['人工结论']} | {item['修改意见']} |")
    else:
        lines.append("- 暂无待处理复核项")

    lines.extend(["", "## 待处理门禁项", ""])
    if status["待处理门禁项"]:
        lines.extend(["| 门禁项 | 当前值 |", "|---|---|"])
        for item in status["待处理门禁项"]:
            lines.append(f"| {item['门禁项']} | {item['当前值']} |")
    else:
        lines.append("- 暂无待处理门禁项")

    lines.extend(["", "## 强制阻断", ""])
    for item in status["强制阻断"]:
        lines.append(f"- [ ] {item}")

    lines.extend(["", "## 边界声明", ""])
    for item in status["边界声明"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    receipt = read_json(RECEIPT_JSON)
    status = build_status(receipt)
    markdown = render_markdown(status)
    task_id = status["任务ID"]

    write_json(OUTPUT_DIR / "人工复核回执状态检查_最新.json", status)
    write_text(OUTPUT_DIR / "人工复核回执状态检查_最新.md", markdown)
    write_json(ARCHIVE_DIR / f"人工复核回执状态检查_{task_id}_{stamp}.json", status)
    write_text(ARCHIVE_DIR / f"人工复核回执状态检查_{task_id}_{stamp}.md", markdown)

    print(f"人工复核回执状态只读检查完成：{status['回执状态']}，未触发真实系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
