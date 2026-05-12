# -*- coding: utf-8 -*-
"""
名称：生成一键接续施工包自动刷新.py
作用：兼容旧入口；调用当前一键接续施工包生成脚本刷新接续包，不再创建05备份快照，不再向施工面板写入旧进度摘要。
触发方式：python 生成一键接续施工包自动刷新.py
所属系统：00杰哥系统总管
安全边界：只调用当前接续包生成链并写最新刷新报告；不备份、不写时间戳目录、不触发n8n、不发送企业微信、不调用券商接口。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
GENERATOR = MANAGER / "02脚本" / "生成一键接续施工包.py"
PACKAGE = MANAGER / "03数据" / "开工上下文" / "一键接续施工包_最新.md"
PANEL = MANAGER / "07文档" / "当前施工面板.md"
REPORT_JSON = OUT_DIR / "一键接续施工包自动刷新报告_最新.json"
REPORT_MD = OUT_DIR / "一键接续施工包自动刷新报告_最新.md"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_card(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    passed = result.returncode == 0 and PACKAGE.exists() and PANEL.exists()
    report = {
        "名称": "一键接续施工包自动刷新报告",
        "生成时间": now,
        "结论": "通过" if passed else "失败",
        "模式": "兼容旧入口；当前只调用生成一键接续施工包.py，不再创建05备份快照，不再改写施工面板旧摘要。",
        "调用脚本": str(GENERATOR),
        "返回码": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "当前产物": {
            "一键接续施工包": file_card(PACKAGE),
            "当前施工面板": file_card(PANEL),
        },
        "备份": {},
        "安全边界": {
            "写05备份": False,
            "写时间戳目录": False,
            "改写旧进度摘要": False,
            "触发n8n": False,
            "发送企业微信": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    lines = [
        "# 一键接续施工包自动刷新报告",
        "",
        f"- 生成时间：{now}",
        f"- 结论：{report['结论']}",
        "- 模式：兼容旧入口；只调用当前接续包生成链。",
        f"- 当前接续包：{PACKAGE}",
        f"- 当前施工面板：{PANEL}",
        "",
        "## 安全边界",
        "",
        "未写05备份，未写时间戳目录，未触发 n8n，未发送企业微信，未调用券商接口，未自动交易。",
    ]
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines))
    print(json.dumps({"状态": report["结论"], "输出": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
