# -*- coding: utf-8 -*-
"""
名称：验证视频真实渲染环境只读识别增强包.py
作用：验收只读识别增强包和核对结果，确认错误数为 0 且所有真实动作均为 False。
安全边界：只读读取数据包并写入验收日志；不执行 magick；不调用 MoneyPrinterTurbo；不渲染；不发布；不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\02视频制作系统")
DATA_DIR = ROOT / "03数据" / "19真实渲染环境只读识别增强包"
LOG_DIR = ROOT / "04日志" / "真实渲染环境只读识别增强包验收"
PACKAGE_JSON = DATA_DIR / "视频真实渲染环境只读识别增强包_最新.json"
CHECK_JSON = DATA_DIR / "视频真实渲染环境只读识别增强核对_最新.json"
LATEST_LOG = LOG_DIR / "video-render-env-readonly-detect-enhanced-verify-最新.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def all_false(mapping: dict[str, Any]) -> bool:
    return bool(mapping) and all(value is False for value in mapping.values())


def main() -> int:
    package = load_json(PACKAGE_JSON)
    result = load_json(CHECK_JSON)
    checks: list[dict[str, Any]] = []

    add_check(checks, "识别增强包存在", PACKAGE_JSON.exists(), str(PACKAGE_JSON))
    add_check(checks, "核对结果存在", CHECK_JSON.exists(), str(CHECK_JSON))
    add_check(checks, "识别增强包声明未执行 magick", package.get("当前真实动作", {}).get("执行magick") is False, package.get("当前真实动作", {}))
    add_check(checks, "识别增强包声明未执行 magick -version", package.get("当前真实动作", {}).get("执行magick_version") is False, package.get("当前真实动作", {}))
    add_check(checks, "识别增强包所有真实动作均为 false", all_false(package.get("当前真实动作", {})), package.get("当前真实动作", {}))
    add_check(checks, "核对结果不可进入真实渲染", result.get("可进入真实渲染") is False, result.get("可进入真实渲染"))
    add_check(checks, "核对结果包含 blocked 原因", len(result.get("blocked原因列表", [])) > 0, result.get("blocked原因列表", []))
    add_check(checks, "核对结果包含人工安装配置建议", len(result.get("下一步人工安装配置建议", [])) > 0, result.get("下一步人工安装配置建议", []))
    add_check(checks, "核对结果所有真实动作均为 false", all_false(result.get("当前真实动作", {})), result.get("当前真实动作", {}))

    errors = [item for item in checks if not item["通过"]]
    report = {
        "名称": "视频真实渲染环境只读识别增强包验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "错误数": len(errors),
        "通过数": len(checks) - len(errors),
        "检查项": checks,
        "所有真实动作": {
            "执行magick": False,
            "执行magick_version": False,
            "调用MoneyPrinterTurbo": False,
            "真实渲染": False,
            "生成真实视频": False,
            "上传发布": False,
            "触发n8n": False,
            "修改企业微信公共配置": False,
            "修改总管面板": False,
            "修改一键接续包": False,
            "重载服务": False,
        },
        "结论": "通过" if not errors else "未通过",
    }
    write_json(LATEST_LOG, report)
    print(json.dumps({"错误数": report["错误数"], "通过数": report["通过数"], "输出": str(LATEST_LOG)}, ensure_ascii=False))
    return 0 if report["错误数"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
