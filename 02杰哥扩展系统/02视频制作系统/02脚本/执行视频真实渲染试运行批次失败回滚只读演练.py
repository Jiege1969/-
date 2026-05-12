# -*- coding: utf-8 -*-
"""
执行视频真实渲染试运行批次失败回滚只读演练。

本脚本只读取第25包失败矩阵、回滚动作清单和证据留存索引，写入只读演练报告。
不删除真实文件，不清理生产目录，不重试真实渲染，不上传发布。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "25真实渲染试运行批次失败回滚与证据留存包"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚与证据留存包_最新.json"
MATRIX_LATEST = DATA_DIR / "视频真实渲染试运行批次失败场景矩阵_最新.json"
ROLLBACK_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚动作清单_最新.json"
EVIDENCE_LATEST = DATA_DIR / "视频真实渲染试运行批次失败证据留存索引_最新.json"
DRILL_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚只读演练报告_最新.json"
DRILL_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚只读演练报告_最新.md"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def guarded_status(generated_at: str, error_count: int) -> dict[str, Any]:
    flags = {
        "batch_allowed": False,
        "whitelist_effective": False,
        "trial_run_allowed": False,
        "can_enter_real_render": False,
        "real_render": False,
        "generate_real_video": False,
        "publish": False,
        "upload_publish": False,
        "call_money_printer_turbo": False,
        "execute_magick": False,
        "execute_magick_version": False,
        "trigger_n8n": False,
        "modify_wecom_public_config": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_pack": False,
        "reload_service": False,
    }
    return {
        "生成时间": generated_at,
        "error_count": error_count,
        "batch_allowed": False,
        "whitelist_effective": False,
        "trial_run_allowed": False,
        "can_enter_real_render": False,
        "real_render": False,
        "publish": False,
        "真实渲染": False,
        "生成真实视频": False,
        "上传发布": False,
        "调用MoneyPrinterTurbo": False,
        "执行magick": False,
        "执行magick_version": False,
        "触发n8n": False,
        "修改企业微信公共配置": False,
        "修改总管面板": False,
        "修改一键接续包": False,
        "重载服务": False,
        "readonly_flags_ascii": flags,
    }


def build_drill_report() -> dict[str, Any]:
    generated_at = now_text()
    package = load_json(PACKAGE_LATEST)
    matrix = load_json(MATRIX_LATEST)
    rollback = load_json(ROLLBACK_LATEST)
    evidence = load_json(EVIDENCE_LATEST)
    checks: list[dict[str, Any]] = []

    for name, path in {
        "总包": PACKAGE_LATEST,
        "失败场景矩阵": MATRIX_LATEST,
        "回滚动作清单": ROLLBACK_LATEST,
        "证据留存索引": EVIDENCE_LATEST,
    }.items():
        add_check(checks, f"{name}存在", path.exists(), str(path))

    actions = rollback.get("回滚动作清单", [])
    add_check(checks, "回滚动作清单非空", bool(actions), len(actions))
    add_check(checks, "全部动作dry_run_only=true", all(item.get("dry_run_only") is True for item in actions), actions)
    add_check(checks, "全部动作不删除真实文件", all(item.get("删除真实文件") is False for item in actions), actions)
    add_check(checks, "全部动作不清理生产目录", all(item.get("清理生产目录") is False for item in actions), actions)
    add_check(checks, "全部动作不重试真实渲染", all(item.get("重试真实渲染") is False for item in actions), actions)
    add_check(checks, "证据索引人工签收unsigned", evidence.get("人工签收状态") == "unsigned", evidence.get("人工签收状态"))
    add_check(checks, "失败矩阵覆盖至少五类场景", matrix.get("失败场景数量", 0) >= 5, matrix.get("失败场景数量"))

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染试运行批次失败回滚只读演练报告",
        "批次ID": package.get("批次ID", evidence.get("批次ID")),
        "任务ID": package.get("任务ID", evidence.get("任务ID")),
        "演练方式": "readonly_dry_run_only",
        "演练结论": "通过；只读演练未触发真实渲染、删除、清理、重试或发布。" if not errors else "不通过；仍保持全部真实动作关闭。",
        "演练步骤": [
            "读取失败场景矩阵。",
            "逐项检查回滚动作 dry_run_only=true。",
            "确认不删除真实文件、不清理生产目录、不重试真实渲染。",
            "确认人工签收状态 unsigned，并保留证据索引。",
        ],
        "检查结果": checks,
        "错误项": errors,
    }
    result.update(guarded_status(generated_at, len(errors)))
    return result


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行批次失败回滚只读演练报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 批次ID：{report['批次ID']}",
        f"- 任务ID：{report['任务ID']}",
        f"- error_count：{report['error_count']}",
        "- batch_allowed：false",
        "- whitelist_effective：false",
        "- trial_run_allowed：false",
        "- can_enter_real_render：false",
        "- real_render：false",
        "- publish：false",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        lines.append(f"- {item['检查项']}：{str(item['通过']).lower()}")
    lines.extend(["", f"结论：{report['演练结论']}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_drill_report()
    stamp = stamp_text()
    write_json(DATA_DIR / f"视频真实渲染试运行批次失败回滚只读演练报告_{stamp}.json", report)
    write_json(DRILL_LATEST, report)
    write_text(DRILL_MD_LATEST, build_markdown(report))
    print(
        json.dumps(
            {
                "readonly_drill": str(DRILL_LATEST),
                "batch_allowed": False,
                "whitelist_effective": False,
                "trial_run_allowed": False,
                "can_enter_real_render": False,
                "real_render": False,
                "publish": False,
                "error_count": report["error_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
