# -*- coding: utf-8 -*-
"""
名称：generate_human_review_receipt_guide.py
作用：生成轮次012视频工厂人工复核回执填写说明。
触发方式：python generate_human_review_receipt_guide.py
安全边界：只生成本地说明文档；不读取真实素材、不访问平台、不连接账号、不渲染、不发布、不发送企业微信、不连接 n8n。
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
OUTPUT_DIR = DATA_ROOT / "人工复核链" / "人工复核回执"
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


def build_guide(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "说明名称": "人工复核回执填写说明",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": str(task.get("任务ID", "未知任务")),
        "主题": nested_value(task, "任务定义", "主题", default=""),
        "真实系统触发": False,
        "填写原则": [
            "只填写人工判断，不自动改写任务单或放行清单",
            "无法确认的项目保持待确认，不得为了推进而填通过",
            "素材、平台、AI标识任一缺口未补齐时，必须保持阻断",
            "回执通过不等于生成放行、真实渲染放行或发布放行",
        ],
        "字段说明": [
            {
                "字段": "复核人/复核时间/复核来源",
                "填写要求": "填写真实人工复核信息；如来自企业微信，只记录来源，不触发真实发送。",
            },
            {
                "字段": "人工结论",
                "填写要求": "可填：通过、需修改、待确认、驳回建议。禁止填自动发布、自动渲染等执行性指令。",
            },
            {
                "字段": "修改意见",
                "填写要求": "写清具体问题和建议修改方向，不写真实账号、Cookie、素材密钥或平台登录信息。",
            },
            {
                "字段": "是否允许生成放行",
                "填写要求": "仅代表是否允许进入生成放行清单讨论，不代表真实渲染。",
            },
            {
                "字段": "是否允许真实渲染",
                "填写要求": "默认否；如要改为是，必须另走真实渲染放行流程，当前业务线不得自行实施。",
            },
            {
                "字段": "是否允许发布放行/自动发布",
                "填写要求": "默认否；发布必须另走发布放行清单和人工确认，当前业务线不得自行实施。",
            },
        ],
        "强制阻断": [
            "素材授权未齐：阻断真实渲染",
            "平台规则未齐：阻断发布放行",
            "AI生成内容标识未确认：阻断发布放行",
            "发布放行清单未登记当前任务：阻断发布",
            "回执出现真实账号、Cookie、外发、n8n、服务重启或自动发布要求：暂停并交回总管判断",
        ],
        "边界声明": [
            "本说明只服务人工复核填写，不是正式结论",
            "不读取真实素材、不访问平台、不连接真实账号、不发送企业微信、不接 n8n",
            "生成放行、真实渲染放行、发布放行必须拆开",
        ],
    }


def render_markdown(guide: dict[str, Any]) -> str:
    lines = [
        "# 轮次012 人工复核回执填写说明",
        "",
        f"- 生成时间：{guide['生成时间']}",
        f"- 任务ID：{guide['任务ID']}",
        f"- 主题：{guide['主题']}",
        "- 真实系统触发：否",
        "",
        "## 填写原则",
        "",
    ]
    for item in guide["填写原则"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 字段说明",
            "",
            "| 字段 | 填写要求 |",
            "|---|---|",
        ]
    )
    for item in guide["字段说明"]:
        lines.append(f"| {item['字段']} | {item['填写要求']} |")

    lines.extend(["", "## 强制阻断", ""])
    for item in guide["强制阻断"]:
        lines.append(f"- [ ] {item}")

    lines.extend(["", "## 边界声明", ""])
    for item in guide["边界声明"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    task = read_json(TASK_PATH)
    guide = build_guide(task)
    markdown = render_markdown(guide)
    task_id = guide["任务ID"]

    write_json(OUTPUT_DIR / "人工复核回执填写说明_最新.json", guide)
    write_text(OUTPUT_DIR / "人工复核回执填写说明_最新.md", markdown)
    write_json(ARCHIVE_DIR / f"人工复核回执填写说明_{task_id}_{stamp}.json", guide)
    write_text(ARCHIVE_DIR / f"人工复核回执填写说明_{task_id}_{stamp}.md", markdown)

    print("人工复核回执填写说明生成完成，未触发真实系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
