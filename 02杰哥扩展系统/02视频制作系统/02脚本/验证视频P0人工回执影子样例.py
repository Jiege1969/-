# -*- coding: utf-8 -*-
"""
名称：验证视频P0人工回执影子样例.py
作用：只读验收成品预览回执与AI标识人工确认回执两个P0影子样例。
安全边界：只读取影子层样例并写入04日志；不读取真实成品，不连接平台账号，不真实渲染，不真实发布，不触发n8n。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\02视频制作系统")
SHADOW_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层" / "智能体影子层"
LOG_DIR = ROOT / "04日志"
LATEST_LOG = LOG_DIR / "video-p0-human-receipt-shadow-samples-verify-最新.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    preview_path = SHADOW_DIR / "成品预览回执影子样例_最新.json"
    ai_label_path = SHADOW_DIR / "AI标识人工确认回执样例_最新.json"
    checks: list[dict[str, Any]] = []

    add_check(checks, "成品预览回执样例存在", preview_path.exists(), str(preview_path))
    add_check(checks, "AI标识人工确认回执样例存在", ai_label_path.exists(), str(ai_label_path))

    preview = load_json(preview_path) if preview_path.exists() else {}
    ai_label = load_json(ai_label_path) if ai_label_path.exists() else {}

    preview_types = {item.get("回执") for item in preview.get("回执类型", []) if isinstance(item, dict)}
    add_check(checks, "成品预览三类回执齐备", {"预览通过", "需要修改", "驳回"}.issubset(preview_types), sorted(preview_types))
    add_check(checks, "成品预览不得自动发布", any("不得自动变成发布放行" in str(item) for item in preview.get("回执类型", [])), preview.get("回执类型", []))
    add_check(checks, "成品预览阻断提示包含AI标识", any("AI标识" in str(item) for item in preview.get("阻断提示", [])), preview.get("阻断提示", []))
    add_check(checks, "成品预览边界禁止真实动作", all(
        any(word in str(item) for item in preview.get("边界声明", []))
        for word in ["不真实渲染", "不真实发布", "不接 n8n", "不访问平台", "不连接真实账号"]
    ), preview.get("边界声明", []))

    ai_fields = {item.get("字段") for item in ai_label.get("确认字段", []) if isinstance(item, dict)}
    required_ai_fields = {"任务ID", "平台", "AI生成内容标识状态", "确认人", "确认时间", "证据占位", "异常说明"}
    add_check(checks, "AI标识确认字段齐备", required_ai_fields.issubset(ai_fields), sorted(ai_fields))
    add_check(checks, "AI标识逐平台提醒齐备", len(ai_label.get("逐平台提醒", [])) >= 4, ai_label.get("逐平台提醒", []))
    add_check(checks, "AI标识待确认阻断发布放行", any("待确认" in item and "不进入发布放行" in item for item in ai_label.get("阻断规则", [])), ai_label.get("阻断规则", []))
    add_check(checks, "AI标识边界禁止真实动作", all(
        any(word in str(item) for item in ai_label.get("边界声明", []))
        for word in ["不真实渲染", "不真实发布", "不接 n8n", "不访问平台", "不连接真实账号"]
    ), ai_label.get("边界声明", []))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "名称": "视频P0人工回执影子样例验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "安全边界": {
            "读取真实成品": False,
            "连接平台账号": False,
            "真实渲染": False,
            "真实发布": False,
            "触发n8n": False,
            "真实发送企业微信": False,
        },
    }
    write_json(LATEST_LOG, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(LATEST_LOG)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
