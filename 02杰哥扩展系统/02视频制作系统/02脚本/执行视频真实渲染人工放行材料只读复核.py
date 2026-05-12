# -*- coding: utf-8 -*-
"""
执行视频真实渲染人工放行材料只读复核。

只读取第22包和第21包人工放行申请草案，不调用 MoneyPrinterTurbo，
不执行 magick，不真实渲染，不生成真实视频，不上传发布。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
SOURCE21_DIR = ROOT / "03数据" / "21真实渲染启用前总闸口与人工放行申请包"
DATA_DIR = ROOT / "03数据" / "22真实渲染人工放行材料完整性复核与试运行禁入包"

SOURCE21_APPROVAL = SOURCE21_DIR / "视频真实渲染人工放行申请草案_最新.json"
PACKAGE_LATEST = DATA_DIR / "视频真实渲染人工放行材料完整性复核与试运行禁入包_最新.json"
MATERIAL_REVIEW_LATEST = DATA_DIR / "视频真实渲染人工放行材料完整性复核_最新.json"
TRIAL_BAN_LATEST = DATA_DIR / "视频真实渲染试运行禁入清单_最新.json"
CHECK_LATEST = DATA_DIR / "视频真实渲染人工放行材料只读复核_最新.json"
CHECK_MD_LATEST = DATA_DIR / "视频真实渲染人工放行材料只读复核_最新.md"


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


def required_false(doc: dict[str, Any]) -> bool:
    keys = ["可进入真实渲染", "真实渲染", "生成真实视频", "上传发布", "调用MoneyPrinterTurbo", "执行magick", "执行magick_version"]
    return all(doc.get(key) is False for key in keys)


def required_ascii_false(doc: dict[str, Any]) -> bool:
    flags = doc.get("readonly_flags_ascii", {})
    keys = [
        "can_enter_real_render",
        "real_render",
        "generate_real_video",
        "upload_publish",
        "call_money_printer_turbo",
        "execute_magick",
        "execute_magick_version",
    ]
    return all(flags.get(key) is False for key in keys)


def build_check() -> dict[str, Any]:
    package = load_json(PACKAGE_LATEST)
    material_review = load_json(MATERIAL_REVIEW_LATEST)
    trial_ban = load_json(TRIAL_BAN_LATEST)
    approval = load_json(SOURCE21_APPROVAL)
    checks: list[dict[str, Any]] = []

    add_check(checks, "第21包人工放行申请草案存在", SOURCE21_APPROVAL.exists(), str(SOURCE21_APPROVAL))
    add_check(checks, "第22包总包存在", PACKAGE_LATEST.exists(), str(PACKAGE_LATEST))
    add_check(checks, "材料完整性复核存在", MATERIAL_REVIEW_LATEST.exists(), str(MATERIAL_REVIEW_LATEST))
    add_check(checks, "试运行禁入清单存在", TRIAL_BAN_LATEST.exists(), str(TRIAL_BAN_LATEST))

    docs = {"package": package, "material_review": material_review, "trial_ban": trial_ban}
    for name, doc in docs.items():
        add_check(checks, f"{name}: 试运行禁入=true", doc.get("试运行禁入") is True, doc.get("试运行禁入"))
        add_check(checks, f"{name}: 可进入真实渲染/真实动作均为 false", required_false(doc), {key: doc.get(key) for key in ["可进入真实渲染", "真实渲染", "生成真实视频", "上传发布", "调用MoneyPrinterTurbo", "执行magick", "执行magick_version"]})
        add_check(checks, f"{name}: 英文红线动作均为 false", required_ascii_false(doc), doc.get("readonly_flags_ascii", {}))
        add_check(checks, f"{name}: error_count=0", doc.get("error_count") == 0, doc.get("error_count"))

    required_materials = ["MoneyPrinterTurbo入口", "ImageMagick可用性", "测试素材", "输出目录", "生成放行清单", "发布阻断保持", "回滚方案", "人工确认签收"]
    material_names = [item.get("材料项") for item in material_review.get("材料复核项", [])]
    add_check(checks, "材料完整性复核项齐全", all(item in material_names for item in required_materials), material_names)
    add_check(checks, "第21申请草案保持 blocked", approval.get("申请状态") == "blocked", approval.get("申请状态"))
    add_check(checks, "第21申请草案未放行真实渲染", required_false(approval), {key: approval.get(key) for key in ["可进入真实渲染", "真实渲染", "生成真实视频", "上传发布", "调用MoneyPrinterTurbo", "执行magick", "执行magick_version"]})

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染人工放行材料只读复核",
        "生成时间": now_text(),
        "来源": {
            "第21人工放行申请草案": str(SOURCE21_APPROVAL),
            "第22总包": str(PACKAGE_LATEST),
            "材料完整性复核": str(MATERIAL_REVIEW_LATEST),
            "试运行禁入清单": str(TRIAL_BAN_LATEST),
        },
        "error_count": len(errors),
        "试运行禁入": True,
        "trial_run_forbidden": True,
        "可进入真实渲染": False,
        "can_enter_real_render": False,
        "真实渲染": False,
        "生成真实视频": False,
        "上传发布": False,
        "调用MoneyPrinterTurbo": False,
        "执行magick": False,
        "执行magick_version": False,
        "readonly_flags": package.get("readonly_flags", {}),
        "readonly_flags_ascii": package.get("readonly_flags_ascii", {}),
        "检查结果": checks,
        "错误项": errors,
        "复核结论": "只读复核通过；材料仍待人工补齐，试运行禁入保持 true。" if not errors else "只读复核未通过；试运行禁入保持 true。",
    }
    return result


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染人工放行材料只读复核",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- error_count：{result['error_count']}",
        f"- 试运行禁入：{result['试运行禁入']}",
        f"- 可进入真实渲染：{result['可进入真实渲染']}",
        f"- 真实渲染：{result['真实渲染']}",
        f"- 生成真实视频：{result['生成真实视频']}",
        f"- 上传发布：{result['上传发布']}",
        f"- 调用MoneyPrinterTurbo：{result['调用MoneyPrinterTurbo']}",
        f"- 执行magick：{result['执行magick']}",
        f"- 执行magick_version：{result['执行magick_version']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in result["检查结果"]:
        lines.append(f"- {item['检查项']}：{item['通过']}")
    lines.extend(["", f"结论：{result['复核结论']}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    result = build_check()
    write_json(DATA_DIR / f"视频真实渲染人工放行材料只读复核_{stamp_text()}.json", result)
    write_json(CHECK_LATEST, result)
    write_text(CHECK_MD_LATEST, build_markdown(result))
    print(
        json.dumps(
            {
                "readonly_check": str(CHECK_LATEST),
                "试运行禁入": True,
                "可进入真实渲染": False,
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "调用MoneyPrinterTurbo": False,
                "执行magick": False,
                "执行magick_version": False,
                "error_count": result["error_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
