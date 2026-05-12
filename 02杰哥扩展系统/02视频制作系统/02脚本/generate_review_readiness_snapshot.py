# -*- coding: utf-8 -*-
"""
名称：generate_review_readiness_snapshot.py
作用：汇总轮次012视频工厂人工复核链准备度，输出本地快照。
触发方式：python generate_review_readiness_snapshot.py
安全边界：只读本地任务、模板、样例、自检报告和放行清单；只写本地快照；不渲染、不发布、不发送企业微信、不连接 n8n。
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
CHECK_REPORT_PATH = REVIEW_ROOT / "本地自检报告" / "人工复核链本地自检报告_最新.json"
OUTPUT_DIR = REVIEW_ROOT / "准备度快照"
ARCHIVE_DIR = OUTPUT_DIR / "archive"


REQUIRED_FILES = {
    "待复核问题清单": REVIEW_ROOT / "视频待复核问题清单_最新.md",
    "素材授权字段模板": REVIEW_ROOT / "复核模板" / "素材授权字段模板_最新.md",
    "平台规则待确认模板": REVIEW_ROOT / "复核模板" / "平台规则待确认模板_最新.md",
    "素材授权占位填写样例": REVIEW_ROOT / "占位填写样例" / "素材授权占位填写样例_最新.md",
    "平台规则占位填写样例": REVIEW_ROOT / "占位填写样例" / "平台规则占位填写样例_最新.md",
    "人工复核回执模板": REVIEW_ROOT / "人工复核回执" / "人工复核回执模板_最新.md",
    "人工复核回执填写说明": REVIEW_ROOT / "人工复核回执" / "人工复核回执填写说明_最新.md",
    "人工复核回执状态检查": REVIEW_ROOT / "人工复核回执" / "状态检查" / "人工复核回执状态检查_最新.md",
    "人工复核回执填写后接收卡": REVIEW_ROOT / "人工复核回执" / "接收卡" / "人工复核回执填写后接收卡_最新.md",
    "复核结果与放行清单一致性检查": REVIEW_ROOT / "一致性检查" / "复核结果与放行清单一致性检查_最新.md",
    "生成放行建议单": REVIEW_ROOT / "放行建议" / "生成放行建议单_最新.md",
    "人工复核链本地自检报告": REVIEW_ROOT / "本地自检报告" / "人工复核链本地自检报告_最新.md",
}


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


def release_line_for_task(text: str, task_id: str) -> str:
    for line in text.splitlines():
        if task_id and task_id in line and line.strip().startswith("|"):
            return line.strip()
    return ""


def infer_generation_release(text: str, task_id: str) -> str:
    line = release_line_for_task(text, task_id)
    if not line:
        return "未登记"
    if "放行" in line:
        return "生成放行已登记"
    if "待确认" in line:
        return "待确认"
    return "需人工核对"


def infer_publish_release(text: str, task_id: str) -> str:
    line = release_line_for_task(text, task_id)
    if not line:
        return "未登记"
    if "发布放行" in line or "放行" in line:
        return "发布放行疑似登记-需人工二次核对"
    if "待确认" in line:
        return "待确认"
    return "需人工核对"


def build_snapshot() -> dict[str, Any]:
    task = read_json(TASK_PATH)
    check_report = read_json(CHECK_REPORT_PATH)
    generation_release = read_text(GENERATION_RELEASE_PATH)
    publish_release = read_text(PUBLISH_RELEASE_PATH)

    task_id = str(task.get("任务ID", "未知任务"))
    allow_render = bool(nested_value(task, "生成控制", "允许真实渲染", default=False))
    allow_publish = bool(nested_value(task, "生成控制", "允许自动发布", default=False))
    check_passed = check_report.get("结论") == "通过"

    file_items = [
        {
            "名称": name,
            "路径": str(path),
            "存在": path.exists(),
        }
        for name, path in REQUIRED_FILES.items()
    ]
    all_files_ready = all(item["存在"] for item in file_items)

    readiness = {
        "影子复核材料准备度": "可进入人工复核" if all_files_ready and check_passed else "需补齐材料",
        "生成放行准备度": "仅生成清单层面已登记" if infer_generation_release(generation_release, task_id) == "生成放行已登记" else "未具备",
        "真实渲染准备度": "阻断" if not allow_render else "配置显示放行-仍需适配器和人工二次确认",
        "发布准备度": "阻断" if not allow_publish else "配置显示放行-仍需发布清单和人工二次确认",
    }

    blocking_items = []
    if not all_files_ready:
        blocking_items.append("人工复核链材料未齐，阻断后续动作")
    if not check_passed:
        blocking_items.append("本地自检未通过，阻断后续动作")
    if not allow_render:
        blocking_items.append("任务单允许真实渲染=false，阻断真实渲染")
    if not allow_publish:
        blocking_items.append("任务单允许自动发布=false，阻断发布")
    if infer_publish_release(publish_release, task_id) == "未登记":
        blocking_items.append("发布放行清单未登记当前任务，阻断发布")

    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "任务ID": task_id,
        "主题": nested_value(task, "任务定义", "主题", default=""),
        "当前任务状态": task.get("状态", "未知状态"),
        "真实系统触发": False,
        "文件清单": file_items,
        "本地自检结论": check_report.get("结论", "未生成"),
        "生成放行清单状态": infer_generation_release(generation_release, task_id),
        "发布放行清单状态": infer_publish_release(publish_release, task_id),
        "准备度": readiness,
        "阻断事项": blocking_items,
        "结论": "人工复核准备材料基本齐备，但真实渲染和发布仍阻断",
    }


def render_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        "# 轮次012 人工复核准备度快照",
        "",
        f"- 生成时间：{snapshot['生成时间']}",
        f"- 任务ID：{snapshot['任务ID']}",
        f"- 主题：{snapshot['主题']}",
        f"- 当前任务状态：{snapshot['当前任务状态']}",
        f"- 真实系统触发：{snapshot['真实系统触发']}",
        f"- 结论：{snapshot['结论']}",
        "",
        "## 文件清单",
        "",
        "| 名称 | 存在 | 路径 |",
        "|---|---|---|",
    ]
    for item in snapshot["文件清单"]:
        lines.append(f"| {item['名称']} | {item['存在']} | {item['路径']} |")

    lines.extend(["", "## 准备度", ""])
    for key, value in snapshot["准备度"].items():
        lines.append(f"- {key}：{value}")

    lines.extend(
        [
            "",
            "## 门禁状态",
            "",
            f"- 本地自检结论：{snapshot['本地自检结论']}",
            f"- 生成放行清单状态：{snapshot['生成放行清单状态']}",
            f"- 发布放行清单状态：{snapshot['发布放行清单状态']}",
            "",
            "## 阻断事项",
            "",
        ]
    )
    if snapshot["阻断事项"]:
        for item in snapshot["阻断事项"]:
            lines.append(f"- [ ] {item}")
    else:
        lines.append("- [ ] 无新增阻断项，但仍需人工复核后另行判断")

    lines.extend(
        [
            "",
            "## 边界声明",
            "",
            "- 本快照只汇总人工复核准备度，不生成真实渲染或发布放行结论。",
            "- 生成放行、真实渲染放行、发布放行必须拆开。",
            "- 不读取真实素材、不访问平台、不连接真实账号、不发送企业微信、不接 n8n。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot = build_snapshot()
    markdown = render_markdown(snapshot)
    task_id = snapshot["任务ID"]

    write_json(OUTPUT_DIR / "人工复核准备度快照_最新.json", snapshot)
    write_text(OUTPUT_DIR / "人工复核准备度快照_最新.md", markdown)
    write_json(ARCHIVE_DIR / f"人工复核准备度快照_{task_id}_{stamp}.json", snapshot)
    write_text(ARCHIVE_DIR / f"人工复核准备度快照_{task_id}_{stamp}.md", markdown)

    print("人工复核准备度快照生成完成，未触发真实系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
