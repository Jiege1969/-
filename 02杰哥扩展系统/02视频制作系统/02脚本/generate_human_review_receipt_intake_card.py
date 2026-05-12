# -*- coding: utf-8 -*-
"""
名称：generate_human_review_receipt_intake_card.py
作用：生成轮次012视频工厂人工复核回执填写后的只读接收卡。
触发方式：python generate_human_review_receipt_intake_card.py
安全边界：只生成本地接收口径文件；不读取真实素材、不访问平台、不连接账号、不渲染、不发布、不发送企业微信、不连接 n8n。
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
RECEIPT_DIR = REVIEW_ROOT / "人工复核回执"
RECEIPT_PATH = RECEIPT_DIR / "人工复核回执模板_最新.json"
STATUS_PATH = RECEIPT_DIR / "状态检查" / "人工复核回执状态检查_最新.json"
OUTPUT_DIR = RECEIPT_DIR / "接收卡"
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


def build_intake_card(task: dict[str, Any], receipt: dict[str, Any], status_check: dict[str, Any]) -> dict[str, Any]:
    task_id = str(task.get("任务ID", receipt.get("任务ID", "未知任务")))
    receipt_task_id = str(receipt.get("任务ID", "未知任务"))
    status_task_id = str(status_check.get("任务ID", "未知任务"))
    task_id_consistent = task_id == receipt_task_id or receipt_task_id == "未知任务"

    return {
        "接收卡名称": "人工复核回执填写后只读接收卡",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "回执任务ID": receipt_task_id,
        "状态检查任务ID": status_task_id,
        "任务ID一致性": "待人工核对" if not task_id_consistent else "表面一致或回执未填写",
        "当前任务状态": task.get("状态", "未知状态"),
        "真实系统触发": False,
        "接收定位": "只读登记人工回执填写结果，不自动修改任务单、放行清单、渲染配置或发布配置",
        "允许接收的人工信息": [
            "复核人、复核时间、复核来源",
            "脚本文案、分镜可执行性、素材授权、平台规则、AI内容标识、配音字幕封面的人工结论",
            "具体修改意见、待补资料、驳回建议和复核备注",
        ],
        "禁止接收为执行指令的内容": [
            "真实渲染、真实发布、自动发布、批量发布、发送企业微信、接入 n8n、重启服务、修改 19310",
            "真实账号、Cookie、登录凭证、素材密钥、平台后台权限信息",
            "把生成放行、真实渲染放行和发布放行混写为同一个结论",
        ],
        "接收后只读检查步骤": [
            "核对任务ID是否与最新任务单一致",
            "核对是否仍存在待确认、待填写、待补资料或驳回建议",
            "核对是否出现真实系统触发类指令；若出现，登记阻断并交回总管判断",
            "核对素材授权、平台规则、AI标识是否齐全；任一缺口未齐，不得进入真实渲染或发布",
            "仅生成接收状态，不自动改写任务单状态或任何放行清单",
        ],
        "默认阻断结论": [
            "素材授权未齐时，阻断真实渲染",
            "平台规则和AI标识未齐时，阻断发布放行",
            "人工复核回执未闭合时，阻断真实渲染和发布",
            "当前接收卡不是生成放行、真实渲染放行或发布放行凭证",
        ],
        "边界声明": [
            "本接收卡只服务人工复核链的本地影子登记",
            "不读取真实素材、不访问平台、不连接真实账号、不发送企业微信、不接 n8n",
            "生成放行、真实渲染放行、发布放行必须拆开",
        ],
    }


def render_markdown(card: dict[str, Any]) -> str:
    lines = [
        "# 轮次012 人工复核回执填写后只读接收卡",
        "",
        f"- 生成时间：{card['生成时间']}",
        f"- 任务ID：{card['任务ID']}",
        f"- 回执任务ID：{card['回执任务ID']}",
        f"- 状态检查任务ID：{card['状态检查任务ID']}",
        f"- 任务ID一致性：{card['任务ID一致性']}",
        f"- 当前任务状态：{card['当前任务状态']}",
        "- 真实系统触发：否",
        f"- 接收定位：{card['接收定位']}",
        "",
        "## 允许接收的人工信息",
        "",
    ]
    for item in card["允许接收的人工信息"]:
        lines.append(f"- {item}")

    lines.extend(["", "## 禁止接收为执行指令的内容", ""])
    for item in card["禁止接收为执行指令的内容"]:
        lines.append(f"- [ ] {item}")

    lines.extend(["", "## 接收后只读检查步骤", ""])
    for index, item in enumerate(card["接收后只读检查步骤"], start=1):
        lines.append(f"{index}. {item}")

    lines.extend(["", "## 默认阻断结论", ""])
    for item in card["默认阻断结论"]:
        lines.append(f"- [ ] {item}")

    lines.extend(["", "## 边界声明", ""])
    for item in card["边界声明"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task = read_json(TASK_PATH)
    receipt = read_json(RECEIPT_PATH)
    status_check = read_json(STATUS_PATH)
    card = build_intake_card(task, receipt, status_check)
    markdown = render_markdown(card)
    task_id = card["任务ID"]

    write_json(OUTPUT_DIR / "人工复核回执填写后接收卡_最新.json", card)
    write_text(OUTPUT_DIR / "人工复核回执填写后接收卡_最新.md", markdown)
    write_json(ARCHIVE_DIR / f"人工复核回执填写后接收卡_{task_id}_{stamp}.json", card)
    write_text(ARCHIVE_DIR / f"人工复核回执填写后接收卡_{task_id}_{stamp}.md", markdown)

    print("人工复核回执填写后接收卡生成完成，未触发真实系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
