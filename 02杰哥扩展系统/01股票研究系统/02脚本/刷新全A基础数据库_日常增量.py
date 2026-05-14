# -*- coding: utf-8 -*-
"""
名称：刷新全A基础数据库_日常增量.py
作用：日常维护全A基础数据库底座，串联本机日线增量、覆盖校验、盘中清理、多源比对和统一索引。
边界：只读中信证券本机文件；只写股票系统03数据；不登录券商；不调用券商接口；不交易；不发送企业微信。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "02脚本"
DATA = ROOT / "03数据"
OUT_DIR = DATA / "017全A基础数据库日常增量"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def default_end_date() -> str:
    now = datetime.now()
    after_close = now.weekday() < 5 and (now.hour, now.minute) >= (15, 35)
    target = now if after_close else now - timedelta(days=1)
    return target.strftime("%Y%m%d")


def run_step(name: str, args: list[str], timeout: int = 600) -> dict[str, Any]:
    started = datetime.now()
    completed = subprocess.run(
        [sys.executable, *args],
        cwd=str(SCRIPT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return {
        "步骤": name,
        "命令": [sys.executable, *args],
        "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
        "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "返回码": completed.returncode,
        "通过": completed.returncode == 0,
        "stdout": completed.stdout[-3000:],
        "stderr": completed.stderr[-3000:],
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 全A基础数据库日常增量刷新报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 结束日期：{report['结束日期']}",
        "",
        "## 步骤结果",
        "",
    ]
    for step in report["步骤"]:
        status = "通过" if step["通过"] else "失败"
        lines.append(f"- {step['步骤']}：{status}，返回码 {step['返回码']}")
    lines.extend(["", "## 边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    end = default_end_date()
    steps = [
        (
            "中信本机原始日线全A增量归档",
            ["采集全A历史日线_中信本机只读.py", "--market", "all", "--offset", "0", "--limit", "5515", "--start", "20240101", "--end", end],
            900,
        ),
        (
            "中信本机原始日线覆盖验证",
            ["验证中信证券本机日线覆盖.py"],
            180,
        ),
        (
            "正式历史库盘中未完结日清理",
            ["清理全A历史日线_剔除盘中未完结日.py"],
            180,
        ),
        (
            "正式历史库补库进度验证",
            ["验证全A历史日线补库进度.py"],
            180,
        ),
        (
            "正式库与中信本机库多源比对",
            ["比对全A历史日线_正式库_vs_中信本机.py"],
            180,
        ),
        (
            "全A基础数据库统一索引刷新",
            ["生成全A基础数据库统一索引.py"],
            180,
        ),
    ]
    results = []
    for name, args, timeout in steps:
        results.append(run_step(name, args, timeout))

    failed = [step for step in results if not step["通过"]]
    report = {
        "名称": "全A基础数据库日常增量刷新报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结束日期": end,
        "结论": "通过" if not failed else "需复核",
        "失败数量": len(failed),
        "步骤": results,
        "安全边界": {
            "是否联网": False,
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否修改中信目录": False,
            "是否交易": False,
            "是否发送企业微信": False,
        },
    }
    json_path = OUT_DIR / "全A基础数据库日常增量刷新_最新.json"
    md_path = OUT_DIR / "全A基础数据库日常增量刷新_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "结束日期": end,
        "步骤数量": len(results),
        "失败数量": len(failed),
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
