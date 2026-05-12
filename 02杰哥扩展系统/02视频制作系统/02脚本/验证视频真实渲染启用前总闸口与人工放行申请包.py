# -*- coding: utf-8 -*-
"""
验证视频真实渲染启用前总闸口与人工放行申请包。

验证只检查产物结构与红线状态，并写入固定验收日志：
video-render-enable-gate-approval-draft-verify-最新.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "21真实渲染启用前总闸口与人工放行申请包"
LOG_DIR = ROOT / "04日志" / "真实渲染启用前总闸口与人工放行申请包验收"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染启用前总闸口与人工放行申请包_最新.json"
GATE_LATEST = DATA_DIR / "视频真实渲染启用前总闸口核对结果_最新.json"
APPROVAL_LATEST = DATA_DIR / "视频真实渲染人工放行申请草案_最新.json"
CHECK_LATEST = DATA_DIR / "视频真实渲染启用前总闸口只读核对_最新.json"
VERIFY_LATEST = LOG_DIR / "video-render-enable-gate-approval-draft-verify-最新.json"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def all_required_false(doc: dict[str, Any]) -> bool:
    required = ["真实渲染", "生成真实视频", "上传发布", "调用MoneyPrinterTurbo", "执行magick", "执行magick_version"]
    return all(doc.get(key) is False for key in required)


def ascii_required_false(doc: dict[str, Any]) -> bool:
    flags = doc.get("readonly_flags_ascii", {})
    required = [
        "real_render",
        "generate_real_video",
        "upload_publish",
        "call_money_printer_turbo",
        "execute_magick",
        "execute_magick_version",
    ]
    return all(flags.get(key) is False for key in required)


def validate() -> dict[str, Any]:
    package = load_json(PACKAGE_LATEST)
    gate = load_json(GATE_LATEST)
    approval = load_json(APPROVAL_LATEST)
    check = load_json(CHECK_LATEST)
    checks: list[dict[str, Any]] = []

    add_check(checks, "总包存在", PACKAGE_LATEST.exists(), str(PACKAGE_LATEST))
    add_check(checks, "总闸口核对结果存在", GATE_LATEST.exists(), str(GATE_LATEST))
    add_check(checks, "人工放行申请草案存在", APPROVAL_LATEST.exists(), str(APPROVAL_LATEST))
    add_check(checks, "只读核对结果存在", CHECK_LATEST.exists(), str(CHECK_LATEST))

    docs = {"package": package, "gate": gate, "approval": approval, "check": check}
    for name, doc in docs.items():
        add_check(checks, f"{name}: 总闸口=blocked", doc.get("总闸口") == "blocked", doc.get("总闸口"))
        add_check(checks, f"{name}: 可进入真实渲染=false", doc.get("可进入真实渲染") is False, doc.get("可进入真实渲染"))
        add_check(checks, f"{name}: 真实渲染/生成真实视频/上传发布/调用/执行均为 false", all_required_false(doc), {key: doc.get(key) for key in ["真实渲染", "生成真实视频", "上传发布", "调用MoneyPrinterTurbo", "执行magick", "执行magick_version"]})
        add_check(checks, f"{name}: 英文红线字段均为 false", ascii_required_false(doc), doc.get("readonly_flags_ascii", {}))
        add_check(checks, f"{name}: error_count=0", doc.get("error_count", 0) == 0, doc.get("error_count", 0))

    required_manual_items = ["MoneyPrinterTurbo入口", "ImageMagick可用性", "测试素材", "输出目录", "生成放行清单", "发布阻断保持"]
    manual_items = [item.get("确认项") for item in approval.get("需人工确认项", [])]
    add_check(checks, "人工放行申请草案保持 blocked", approval.get("申请状态") == "blocked", approval.get("申请状态"))
    add_check(checks, "人工确认项齐全", all(item in manual_items for item in required_manual_items), manual_items)
    add_check(checks, "发布阻断保持", approval.get("上传发布") is False and "发布阻断保持" in manual_items, {"上传发布": approval.get("上传发布"), "确认项": manual_items})

    errors = [item for item in checks if not item["通过"]]
    return {
        "名称": "视频真实渲染启用前总闸口与人工放行申请包验收",
        "生成时间": now_text(),
        "error_count": len(errors),
        "总闸口": "blocked",
        "可进入真实渲染": False,
        "can_enter_real_render": False,
        "真实渲染": False,
        "生成真实视频": False,
        "上传发布": False,
        "调用MoneyPrinterTurbo": False,
        "执行magick": False,
        "执行magick_version": False,
        "检查结果": checks,
        "错误项": errors,
        "产物路径": {
            "总包": str(PACKAGE_LATEST),
            "总闸口核对结果": str(GATE_LATEST),
            "人工放行申请草案": str(APPROVAL_LATEST),
            "只读核对结果": str(CHECK_LATEST),
            "验收日志": str(VERIFY_LATEST),
        },
        "红线确认": {
            "不真实渲染": True,
            "不发布": True,
            "不接n8n": True,
            "不改企业微信公共配置": True,
            "不改总管面板": True,
            "不改一键接续包": True,
            "不重载服务": True,
        },
        "验收结论": "通过" if not errors else "不通过",
    }


def main() -> int:
    result = validate()
    write_json(VERIFY_LATEST, result)
    print(
        json.dumps(
            {
                "verify_log": str(VERIFY_LATEST),
                "总闸口": "blocked",
                "可进入真实渲染": False,
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "调用MoneyPrinterTurbo": False,
                "执行magick": False,
                "执行magick_version": False,
                "error_count": result["error_count"],
                "验收结论": result["验收结论"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
