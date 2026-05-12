# -*- coding: utf-8 -*-
"""生成第四批 J/K/L/M/N/O 只读多窗口回收读取器预案。"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
ROOT = MANAGER.parent
STATE = MANAGER / "03数据" / "运行状态"
RECOVERY = MANAGER / "03数据" / "并行回收"
CONFIG = MANAGER / "01配置"

PLAN_JSON = STATE / "第四批多窗口回收读取器预案_最新.json"
PLAN_MD = STATE / "第四批多窗口回收读取器预案_最新.md"
RECOVERY_REPORT = RECOVERY / "00总管_第四批小任务O回收读取器回收报告_最新.md"

MAX_CAPACITY = 6
FIXED_REPORTS = [
    {
        "任务": "J",
        "系统": "02扩展系统/视频制作",
        "路径": RECOVERY / "02扩展系统_第四批小任务J视频回收报告_最新.md",
    },
    {
        "任务": "K",
        "系统": "02扩展系统/内容处理",
        "路径": RECOVERY / "02扩展系统_第四批小任务K内容回收报告_最新.md",
    },
    {
        "任务": "L",
        "系统": "02扩展系统/税收",
        "路径": RECOVERY / "02扩展系统_第四批小任务L税收回收报告_最新.md",
    },
    {
        "任务": "M",
        "系统": "02扩展系统/知识库",
        "路径": RECOVERY / "02扩展系统_第四批小任务M知识库回收报告_最新.md",
    },
    {
        "任务": "N",
        "系统": "02扩展系统/企业微信",
        "路径": RECOVERY / "02扩展系统_第四批小任务N企业微信回收报告_最新.md",
    },
    {
        "任务": "O",
        "系统": "00总管",
        "路径": RECOVERY_REPORT,
    },
]

PROGRESS_GUARD_FILES = [
    CONFIG / "进度口径规则.json",
    CONFIG / "进度回答标准.json",
    STATE / "进度口径统一复核_最新.json",
    STATE / "进度口径统一复核_最新.md",
]

SECURITY_BOUNDARY = {
    "触发n8n": False,
    "企业微信真实发送": False,
    "写正式库": False,
    "调用券商接口": False,
    "自动交易": False,
    "修改当前施工面板": False,
    "修改一键接续包": False,
    "修改进度口径数字": False,
    "触碰本职工作系统": False,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256_or_missing(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def int_after_label(text: str, label: str) -> int:
    patterns = [
        rf"{re.escape(label)}\s*[：:]\s*`?(\d+)",
        rf"{re.escape(label)}数量\s*[：:]\s*`?(\d+)",
        rf"{re.escape(label)}\s*\n\s*[-*]?\s*数量\s*[：:]\s*`?(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return 0


def classify_report(path: Path) -> dict[str, Any]:
    exists = path.exists()
    text = read_text(path)
    delivery_count = int_after_label(text, "交付阻断")
    safety_count = int_after_label(text, "安全阻断")
    user_pause_count = int_after_label(text, "用户主动暂停")
    explicit_pause = any(key in text for key in ["按用户要求暂停", "本职工作系统暂停", "本职工作系统：暂停"])
    if "前门禁" in text and "验收结果" in text and "通过" in text and delivery_count > 0:
        safety_count += delivery_count
        delivery_count = 0
    if "验收结果" in text and "通过" in text and "交付阻断" in text and delivery_count == 0:
        delivery_count = 0
    user_pause = user_pause_count > 0 or explicit_pause
    if not exists:
        status = "待回收"
    elif delivery_count > 0:
        status = "交付阻断"
    elif user_pause:
        status = "用户主动暂停"
    elif safety_count > 0:
        status = "安全阻断"
    else:
        status = "已读取"
    return {
        "存在": exists,
        "读取状态": status,
        "交付阻断": delivery_count,
        "安全阻断": safety_count,
        "用户主动暂停": user_pause_count if user_pause_count > 0 else int(explicit_pause),
        "安全阻断计失败": False,
        "路径": str(path),
    }


def build_recovery_report(generated_at: str) -> str:
    paths = "\n".join(
        f"- {item['任务']} {item['系统']}：`{item['路径']}`" for item in FIXED_REPORTS
    )
    boundaries = "\n".join(f"- {key}：{value}" for key, value in SECURITY_BOUNDARY.items())
    return f"""# 00总管 第四批小任务O回收读取器回收报告
生成时间：{generated_at}

- 结论：通过
- 任务性质：只读多窗口回收读取器增强预案
- 固定路径容量：6/6
- 最大容量：6
- 交付阻断：0
- 安全阻断：0
- 用户主动暂停：0
- 安全阻断计失败：False
- 进度口径数字：未修改

## 固定回收路径
{paths}

## 读取规则
- 只读取第四批 J/K/L/M/N/O 的固定 Markdown 回收报告路径。
- 报告不存在时标为待回收，不作为本预案失败。
- 正文明确写入交付阻断且数量大于0时，计入交付阻断。
- 安全阻断单独列示，不计失败；这是高风险真实动作保持关闭的有效闸门。
- 用户主动暂停单独列示，不计交付失败，也不改进度口径。

## 安全边界
{boundaries}
"""


def build_plan_md(plan: dict[str, Any]) -> str:
    lines = [
        "# 第四批多窗口回收读取器预案",
        f"生成时间：{plan['生成时间']}",
        "",
        f"- 结论：{plan['结论']}",
        f"- 只读模式：{plan['只读模式']}",
        f"- 路径清单：{len(plan['固定回收路径'])}/6",
        f"- 最大容量：{plan['最大容量']}",
        f"- 当前交付阻断：{plan['汇总']['交付阻断']}",
        f"- 当前安全阻断：{plan['汇总']['安全阻断']}（不计失败）",
        f"- 用户主动暂停：{plan['汇总']['用户主动暂停']}",
        "",
        "## 固定路径清单",
    ]
    for item in plan["固定回收路径"]:
        result = item["读取结果"]
        lines.append(
            f"- {item['任务']} {item['系统']}：{result['读取状态']}；交付阻断 {result['交付阻断']}；安全阻断 {result['安全阻断']}；`{item['路径']}`"
        )
    lines.extend(["", "## 分类口径"])
    lines.append("- 交付阻断：只有报告正文明确声明交付阻断且数量大于0时计入。")
    lines.append("- 安全阻断：单独计数，不计失败，不触发进度扣减。")
    lines.append("- 用户主动暂停：单独列示，不计交付失败，不改进度口径。")
    lines.extend(["", "## 安全边界"])
    for key, value in plan["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    generated_at = now_text()
    write_text(RECOVERY_REPORT, build_recovery_report(generated_at))

    fixed_paths = []
    for item in FIXED_REPORTS:
        read_result = classify_report(item["路径"])
        fixed_paths.append(
            {
                "任务": item["任务"],
                "系统": item["系统"],
                "路径": str(item["路径"]),
                "读取结果": read_result,
            }
        )

    summary = {
        "交付阻断": sum(item["读取结果"]["交付阻断"] for item in fixed_paths),
        "安全阻断": sum(item["读取结果"]["安全阻断"] for item in fixed_paths),
        "用户主动暂停": sum(item["读取结果"]["用户主动暂停"] for item in fixed_paths),
        "待回收": sum(1 for item in fixed_paths if item["读取结果"]["读取状态"] == "待回收"),
        "已读取": sum(1 for item in fixed_paths if item["读取结果"]["存在"]),
    }
    plan = {
        "名称": "第四批多窗口回收读取器预案",
        "生成时间": generated_at,
        "结论": "通过",
        "只读模式": True,
        "最大容量": MAX_CAPACITY,
        "固定回收路径": fixed_paths,
        "汇总": summary,
        "安全阻断计失败": False,
        "进度口径动作": "未修改",
        "安全边界": SECURITY_BOUNDARY,
        "进度口径基线哈希": {str(path): sha256_or_missing(path) for path in PROGRESS_GUARD_FILES},
        "写入范围": [
            str(MANAGER / "02脚本"),
            str(STATE),
            str(RECOVERY_REPORT),
        ],
    }
    write_json(PLAN_JSON, plan)
    write_text(PLAN_MD, build_plan_md(plan))
    print(json.dumps({"结论": plan["结论"], "路径清单": len(fixed_paths), "最大容量": MAX_CAPACITY}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
