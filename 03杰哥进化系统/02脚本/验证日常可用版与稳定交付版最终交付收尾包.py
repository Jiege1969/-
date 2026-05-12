# -*- coding: utf-8 -*-
"""验证日常可用版与稳定交付版最终交付收尾包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "80日常可用版与稳定交付版最终交付收尾包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常可用版与稳定交付版最终交付收尾包验收"

PACKAGE_JSON = DATA_DIR / "日常可用版与稳定交付版最终交付收尾包_最新.json"
PACKAGE_MD = DATA_DIR / "日常可用版与稳定交付版最终交付收尾包_最新.md"
DAILY_MD = DATA_DIR / "日常可用版交付清单_最新.md"
STABLE_MD = DATA_DIR / "稳定交付版交付清单_最新.md"
BOUNDARY_MD = DATA_DIR / "使用边界与红线说明_最新.md"
HANDOFF_MD = DATA_DIR / "使用者接管说明_最新.md"
VERIFY_JSON = LOG_DIR / "daily-stable-final-delivery-closeout-verify-最新.json"
VERIFY_MD = LOG_DIR / "daily-stable-final-delivery-closeout-verify-最新.md"

REQUIRED_FILES = [PACKAGE_JSON, PACKAGE_MD, DAILY_MD, STABLE_MD, BOUNDARY_MD, HANDOFF_MD]
FORBIDDEN_MARKERS = [
    "允许真实发送",
    "允许真实触发",
    "允许接券商",
    "允许交易",
    "允许登录电子税务局",
    "允许接财税软件",
    "允许真实渲染",
    "允许自动发布",
    "允许写正式规则",
    "允许自动转正式规则",
    "允许重载19310",
    "允许重载19302",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check_package() -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"缺少文件：{path}")
    if not PACKAGE_JSON.exists():
        return errors

    package = read_json(PACKAGE_JSON)
    if package.get("状态") != "delivery_closeout_ready":
        errors.append("交付收尾包状态不是 delivery_closeout_ready")
    levels = package.get("交付层级", {})
    if levels.get("日常可用交付版", {}).get("状态") != "可交付使用":
        errors.append("日常可用交付版未声明可交付使用")
    if levels.get("稳定交付版", {}).get("状态") != "稳定候选可交付使用":
        errors.append("稳定交付版未声明稳定候选可交付使用")
    for name, evidence in package.get("验收证据", {}).items():
        if evidence.get("通过") is not True:
            errors.append(f"验收证据未通过：{name}")
    for flag, value in package.get("安全边界", {}).items():
        if value is not False:
            errors.append(f"安全边界必须为 false：{flag}")

    all_text = json.dumps(package, ensure_ascii=False)
    for path in REQUIRED_FILES:
        if path.exists() and path.suffix.lower() == ".md":
            all_text += "\n" + path.read_text(encoding="utf-8-sig")
    hits = [marker for marker in FORBIDDEN_MARKERS if marker in all_text]
    if hits:
        errors.append(f"命中禁止开放措辞：{hits}")
    return errors


def write_report(errors: list[str]) -> dict[str, Any]:
    report = {
        "名称": "日常可用版与稳定交付版最终交付收尾包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": len(errors) == 0,
        "错误": errors,
        "指标": {
            "检查文件数": len(REQUIRED_FILES),
            "错误数": len(errors),
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    VERIFY_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    VERIFY_MD.write_text(
        "\n".join(
            [
                "# 日常可用版与稳定交付版最终交付收尾包验收",
                "",
                f"- 生成时间：{report['生成时间']}",
                f"- 通过：{report['通过']}",
                f"- 错误数：{len(errors)}",
                "",
                "## 错误",
                "",
                "\n".join(f"- {item}" for item in errors) if errors else "- 无",
            ]
        ),
        encoding="utf-8",
    )
    return report


def main() -> int:
    errors = check_package()
    report = write_report(errors)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
