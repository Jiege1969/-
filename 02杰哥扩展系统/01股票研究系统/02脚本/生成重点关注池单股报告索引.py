# -*- coding: utf-8 -*-
"""
名称：生成重点关注池单股报告索引.py
作用：为重点关注池批量生成单股即时研究报告，并生成可读索引。
触发方式：python 生成重点关注池单股报告索引.py
依赖：Python标准库；重点关注股票池.json；生成单股即时研究报告.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地股票研究数据；只写03数据/23单股即时报告和04日志/单股即时报告；不联网；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建重点关注池单股报告索引脚本。
标识：stock-focus-single-report-index-generate
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(code: str) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz")):
        return text[2:]
    return text.zfill(6) if text.isdigit() else text


def focus_stocks(root: Path) -> list[dict[str, Any]]:
    data = load_json(root / "01配置" / "重点关注股票池.json", {"股票池": []})
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in data.get("股票池", []):
        code = normalize_code(item.get("代码", ""))
        if code and code not in seen:
            seen.add(code)
            result.append(item)
    return result


def report_path_for_latest(root: Path, stock: dict[str, Any]) -> str:
    latest = root / "03数据" / "23单股即时报告" / "单股即时研究报告_最新.md"
    return str(latest) if latest.exists() else ""


def build_markdown(package: dict[str, Any]) -> str:
    lines = [
        "# 重点关注池单股报告索引",
        "",
        f"生成时间：{package['生成时间']}",
        "",
        "声明：本索引只用于研究辅助，不构成投资建议；不连接券商接口，不自动交易。",
        "",
        f"- 重点关注池数量：{package['股票数量']}",
        f"- 成功数量：{package['成功数量']}",
        f"- 失败数量：{package['失败数量']}",
        "",
        "## 单股报告",
        "",
    ]
    for item in package["报告索引"]:
        lines.append(f"- {item['名称']}（{item['代码']}）：{item['状态']}，报告：`{item['报告路径']}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成单股即时研究报告.py"
    stocks = focus_stocks(root)
    rows: list[dict[str, Any]] = []
    for stock in stocks:
        name = str(stock.get("名称", ""))
        result = subprocess.run([sys.executable, str(generator), "--stock", name], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        rows.append({
            "名称": name,
            "代码": stock.get("代码", ""),
            "状态": "成功" if result.returncode == 0 else "失败",
            "报告路径": report_path_for_latest(root, stock),
            "标准输出": result.stdout.strip(),
            "标准错误": result.stderr.strip(),
        })
    success = sum(1 for item in rows if item["状态"] == "成功")
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "股票数量": len(stocks),
        "成功数量": success,
        "失败数量": len(stocks) - success,
        "报告索引": rows,
        "安全边界": {
            "是否联网": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否写旧系统": False,
            "是否写正式库": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    output_dir = root / "03数据" / "23单股即时报告"
    log_dir = root / "04日志" / "单股即时报告"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = output_dir / "重点关注池单股报告索引_最新.json"
    latest_json = output_dir / "重点关注池单股报告索引_最新.json"
    md_path = output_dir / "重点关注池单股报告索引_最新.md"
    latest_md = output_dir / "重点关注池单股报告索引_最新.md"
    log_path = log_dir / "stock-focus-single-report-index-generate-最新.json"
    write_json(json_path, package)
    write_json(latest_json, package)
    markdown = build_markdown(package)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, package)
    print(json.dumps({"股票数量": len(stocks), "成功数量": success, "失败数量": len(stocks) - success, "输出": str(latest_md)}, ensure_ascii=False))
    return 0 if success == len(stocks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
