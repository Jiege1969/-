# -*- coding: utf-8 -*-
"""
名称：执行视频真实渲染环境只读识别增强核对.py
作用：读取只读识别增强包，输出真实渲染阻断结论与人工安装/配置建议。
安全边界：只读核对；不执行 magick；不调用 MoneyPrinterTurbo；不渲染；不生成真实视频；不发布；不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\02视频制作系统")
DATA_DIR = ROOT / "03数据" / "19真实渲染环境只读识别增强包"
LATEST_PACKAGE = DATA_DIR / "视频真实渲染环境只读识别增强包_最新.json"
LATEST_RESULT = DATA_DIR / "视频真实渲染环境只读识别增强核对_最新.json"
LATEST_MD = DATA_DIR / "视频真实渲染环境只读识别增强核对_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def any_money_entry(package: dict[str, Any]) -> bool:
    return any(
        bool(item.get("含任一入口文件"))
        for item in package.get("MoneyPrinterTurbo候选目录识别", [])
        if isinstance(item, dict)
    )


def build_result(package: dict[str, Any]) -> dict[str, Any]:
    magick = package.get("ImageMagick命令名识别", {})
    real_actions = package.get("当前真实动作", {})
    blockers = [
        "本轮目标是只读识别增强，不包含真实渲染放行授权",
        "未执行 magick -version，无法确认 ImageMagick 真实可用版本",
        "未调用 MoneyPrinterTurbo 入口，无法确认真实工程运行状态",
        "未进行素材、任务单、人工复核、发布放行链的真实渲染前总验收",
    ]
    if not magick.get("PATH命令名可找到"):
        blockers.append("PATH 中未识别到 magick 命令名，需人工安装 ImageMagick 或配置 PATH")
    if not any_money_entry(package):
        blockers.append("候选目录未识别到 MoneyPrinterTurbo 入口文件，需人工确认安装目录")

    return {
        "名称": "视频真实渲染环境只读识别增强核对",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源包": str(LATEST_PACKAGE),
        "可进入真实渲染": False,
        "blocked原因列表": blockers,
        "下一步人工安装配置建议": [
            "人工安装或确认 ImageMagick，并由负责人在安全窗口手工执行版本核验",
            "人工确认 MoneyPrinterTurbo 安装目录及 start.bat、app/main.py、webui/Main.py 所属入口",
            "人工补齐渲染前任务单、素材授权、人工复核、发布放行链验收记录",
            "确认需要真实渲染时，由总管另行下发明确放行任务；本脚本不得替代放行",
        ],
        "识别摘录": {
            "magick_PATH命令名可找到": bool(magick.get("PATH命令名可找到")),
            "magick_解析到的命令路径": magick.get("解析到的命令路径", ""),
            "MoneyPrinterTurbo_候选目录数": len(package.get("MoneyPrinterTurbo候选目录识别", [])),
            "MoneyPrinterTurbo_识别到入口": any_money_entry(package),
        },
        "当前真实动作": {
            **{key: bool(value) for key, value in real_actions.items()},
            "真实渲染核对放行": False,
        },
    }


def build_markdown(result: dict[str, Any]) -> str:
    blockers = [f"- {item}" for item in result["blocked原因列表"]]
    suggestions = [f"- {item}" for item in result["下一步人工安装配置建议"]]
    return "\n".join(
        [
            "# 视频真实渲染环境只读识别增强核对",
            "",
            f"- 生成时间：{result['生成时间']}",
            f"- 可进入真实渲染：{result['可进入真实渲染']}",
            "",
            "## blocked 原因列表",
            "",
            *blockers,
            "",
            "## 下一步人工安装/配置建议",
            "",
            *suggestions,
            "",
            "## 真实动作",
            "",
            *[f"- {key}：{value}" for key, value in result["当前真实动作"].items()],
        ]
    )


def main() -> int:
    package = load_json(LATEST_PACKAGE)
    result = build_result(package)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stamped_result = DATA_DIR / f"视频真实渲染环境只读识别增强核对_{timestamp}.json"
    write_json(stamped_result, result)
    write_json(LATEST_RESULT, result)
    write_text(LATEST_MD, build_markdown(result))
    print(json.dumps({"可进入真实渲染": False, "blocked原因数": len(result["blocked原因列表"]), "输出": str(LATEST_RESULT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
