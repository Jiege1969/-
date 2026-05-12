# -*- coding: utf-8 -*-
"""
执行视频真实渲染启用前总闸口只读核对。

只读取第21包生成结果和第20包来源摘要，不调用 MoneyPrinterTurbo，不执行 magick，
不真实渲染，不生成真实视频，不上传发布。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "21真实渲染启用前总闸口与人工放行申请包"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染启用前总闸口与人工放行申请包_最新.json"
CHECK_LATEST = DATA_DIR / "视频真实渲染启用前总闸口只读核对_最新.json"
CHECK_MD_LATEST = DATA_DIR / "视频真实渲染启用前总闸口只读核对_最新.md"


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


def all_false(values: dict[str, Any], keys: list[str]) -> bool:
    return all(values.get(key) is False for key in keys)


def build_check(package: dict[str, Any]) -> dict[str, Any]:
    cn_keys = ["真实渲染", "生成真实视频", "上传发布", "调用MoneyPrinterTurbo", "执行magick", "执行magick_version"]
    ascii_keys = [
        "real_render",
        "generate_real_video",
        "upload_publish",
        "call_money_printer_turbo",
        "execute_magick",
        "execute_magick_version",
    ]
    gate = package.get("总闸口核对结果", {})
    approval = package.get("人工放行申请草案", {})
    manual_items = [item.get("确认项") for item in approval.get("需人工确认项", [])]
    required_manual_items = ["MoneyPrinterTurbo入口", "ImageMagick可用性", "测试素材", "输出目录", "生成放行清单", "发布阻断保持"]

    checks = [
        {
            "检查项": "总闸口保持 blocked",
            "通过": package.get("总闸口") == "blocked" and gate.get("总闸口") == "blocked" and approval.get("总闸口") == "blocked",
        },
        {
            "检查项": "可进入真实渲染为 false",
            "通过": package.get("可进入真实渲染") is False and gate.get("可进入真实渲染") is False and approval.get("可进入真实渲染") is False,
        },
        {
            "检查项": "真实渲染/生成真实视频/上传发布均为 false",
            "通过": all(package.get(key) is False for key in ["真实渲染", "生成真实视频", "上传发布"]),
        },
        {
            "检查项": "未调用 MoneyPrinterTurbo，未执行 magick 或 magick_version",
            "通过": all(package.get(key) is False for key in ["调用MoneyPrinterTurbo", "执行magick", "执行magick_version"]),
        },
        {
            "检查项": "中文只读红线标志均为 false",
            "通过": all_false(package.get("readonly_flags", {}), cn_keys),
        },
        {
            "检查项": "英文只读红线标志均为 false",
            "通过": all_false(package.get("readonly_flags_ascii", {}), ascii_keys),
        },
        {
            "检查项": "人工放行申请草案保持 blocked",
            "通过": approval.get("申请状态") == "blocked",
        },
        {
            "检查项": "需人工确认项齐全",
            "通过": all(item in manual_items for item in required_manual_items),
        },
    ]
    errors = [item for item in checks if not item["通过"]]

    return {
        "名称": "视频真实渲染启用前总闸口只读核对",
        "生成时间": now_text(),
        "来源包": str(PACKAGE_LATEST),
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
        "readonly_flags": package.get("readonly_flags", {}),
        "readonly_flags_ascii": package.get("readonly_flags_ascii", {}),
        "检查结果": checks,
        "错误项": errors,
        "需人工确认项": approval.get("需人工确认项", []),
        "核对结论": "总闸口只读核对通过；真实渲染仍保持 blocked。" if not errors else "总闸口只读核对未通过；真实渲染仍保持 blocked。",
    }


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染启用前总闸口只读核对",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- error_count：{result['error_count']}",
        f"- 总闸口：{result['总闸口']}",
        f"- 可进入真实渲染：{result['可进入真实渲染']}",
        f"- 真实渲染：{result['真实渲染']}",
        f"- 生成真实视频：{result['生成真实视频']}",
        f"- 上传发布：{result['上传发布']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in result["检查结果"]:
        lines.append(f"- {item['检查项']}：{item['通过']}")
    lines.extend(["", "## 需人工确认项", ""])
    for item in result["需人工确认项"]:
        lines.append(f"- {item['确认项']}：{item['当前状态']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    package = load_json(PACKAGE_LATEST)
    result = build_check(package)
    stamped = DATA_DIR / f"视频真实渲染启用前总闸口只读核对_{stamp_text()}.json"

    write_json(stamped, result)
    write_json(CHECK_LATEST, result)
    write_text(CHECK_MD_LATEST, build_markdown(result))

    print(
        json.dumps(
            {
                "readonly_check": str(CHECK_LATEST),
                "总闸口": "blocked",
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
