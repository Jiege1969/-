# -*- coding: utf-8 -*-
"""
名称：执行重点关注池历史K线东方财富增强受控刷新.py
作用：备份当前历史K线最新快照后，运行改造后的历史K线生成脚本，生成东方财富增强正式成交额快照。
安全边界：只备份并刷新股票模块03数据/11历史行情；不发送企业微信、不触发 n8n、不写正式库、不调用券商接口、不自动交易。
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "233历史K线东方财富增强受控刷新"
HISTORY_SCRIPT = ROOT / "02脚本" / "生成重点关注池历史K线快照.py"
LATEST_HISTORY = ROOT / "03数据" / "11历史行情" / "重点关注池历史K线快照_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_amount_sources(data: dict[str, Any]) -> dict[str, Any]:
    items = data.get("历史K线", []) or []
    eastmoney = 0
    tencent = 0
    with_amount = 0
    for item in items:
        source = str(item.get("数据源", ""))
        rows = item.get("K线", []) or []
        if "东方财富" in source:
            eastmoney += 1
        if "腾讯" in source:
            tencent += 1
        if any((row.get("成交额") or 0) for row in rows):
            with_amount += 1
    return {
        "股票数量": len(items),
        "东方财富数量": eastmoney,
        "腾讯数量": tencent,
        "含正式成交额数量": with_amount,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 重点关注池历史K线东方财富增强受控刷新执行报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 备份文件：`{report['备份文件']}`",
        "",
        "## 一、刷新前后",
        "",
    ]
    for key, value in report["刷新前统计"].items():
        lines.append(f"- 刷新前{key}：{value}")
    for key, value in report["刷新后统计"].items():
        lines.append(f"- 刷新后{key}：{value}")
    lines.extend(["", "## 二、执行输出", ""])
    lines.append(f"- returncode：{report['执行结果']['returncode']}")
    lines.append(f"- stdout：{report['执行结果']['stdout']}")
    lines.append(f"- stderr：{report['执行结果']['stderr']}")
    lines.extend(["", "## 三、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    backup_dir = OUT_DIR / "备份" / stamp
    backup_path = backup_dir / "重点关注池历史K线快照_最新_刷新前备份.json"
    before = load_json(LATEST_HISTORY)
    before_hash = sha256(LATEST_HISTORY)
    backup_dir.mkdir(parents=True, exist_ok=True)
    if LATEST_HISTORY.exists():
        shutil.copy2(LATEST_HISTORY, backup_path)
    completed = subprocess.run(
        [sys.executable, str(HISTORY_SCRIPT)],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=180,
        check=False,
    )
    after = load_json(LATEST_HISTORY)
    after_hash = sha256(LATEST_HISTORY)
    before_stats = count_amount_sources(before)
    after_stats = count_amount_sources(after)
    ok = (
        completed.returncode == 0
        and after_stats["股票数量"] > 0
        and after_stats["东方财富数量"] == after_stats["股票数量"]
        and after_stats["含正式成交额数量"] == after_stats["股票数量"]
    )
    report = {
        "名称": "重点关注池历史K线东方财富增强受控刷新执行报告",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "完成" if ok else "失败",
        "执行脚本": str(HISTORY_SCRIPT),
        "最新快照": str(LATEST_HISTORY),
        "备份文件": str(backup_path),
        "刷新前sha256": before_hash,
        "刷新后sha256": after_hash,
        "刷新前统计": before_stats,
        "刷新后统计": after_stats,
        "执行结果": {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        },
        "回滚方式": f"如需回滚，将备份文件复制回 {LATEST_HISTORY}",
        "安全边界": {
            "已备份刷新前最新快照": bool(backup_path.exists()),
            "运行历史K线刷新": True,
            "覆盖历史K线最新快照": True,
            "修改220口径": False,
            "修改221短文": False,
            "修改222影子分支": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "重点关注池历史K线东方财富增强受控刷新执行报告_最新.json"
    latest_md = OUT_DIR / "重点关注池历史K线东方财富增强受控刷新执行报告_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "刷新后统计": after_stats,
        "备份": str(backup_path),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
