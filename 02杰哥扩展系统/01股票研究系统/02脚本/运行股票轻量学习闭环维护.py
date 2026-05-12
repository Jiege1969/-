# -*- coding: utf-8 -*-
"""
名称：运行股票轻量学习闭环维护.py
作用：顺序运行股票轻量学习闭环维护脚本，刷新档案、账本、预览和摘要。
触发方式：python 运行股票轻量学习闭环维护.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地维护脚本；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不自动修改正式规则；可按晋级候选账自动更新重点关注池并保留备份与回滚日志。
标识：stock-light-learning-maintenance-runner
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_script(root: Path, name: str) -> dict[str, Any]:
    script = root / "02脚本" / name
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, "-B", str(script)],
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=180,
    )
    return {
        "脚本": str(script),
        "返回码": completed.returncode,
        "标准输出": completed.stdout.strip(),
        "标准错误": completed.stderr.strip(),
        "是否通过": completed.returncode == 0,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票轻量学习闭环维护运行记录 - {report['生成时间']}",
        "",
        f"- 结论：{report['结论']}",
        f"- 通过：{report['通过数量']} / {report['脚本数量']}",
        "",
        "## 明细",
        "",
    ]
    for item in report["运行结果"]:
        lines.append(f"- {'通过' if item['是否通过'] else '失败'}：`{Path(item['脚本']).name}`")
        if item.get("标准输出"):
            lines.append(f"  - 输出：{item['标准输出'][:500]}")
        if item.get("标准错误"):
            lines.append(f"  - 错误：{item['标准错误'][:500]}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 不触发 n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不自动修改正式规则。",
        "- 重点关注池自动入池只基于晋级候选账执行，写入前备份，写入后记录日志，可回滚。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    scripts = [
        "生成股票轻量学习闭环账本骨架.py",
        "更新公司品质档案_从现有数据.py",
        "更新指数样本学习账_从L8数据.py",
        "同步L5AI报告到判断复盘账.py",
        "生成股票验证建议预览.py",
        "生成股票判断复盘到期提醒与人工填写清单.py",
        "生成股票经验候选账.py",
        "生成股票轻量学习周复盘摘要.py",
        "执行重点观察池自动入池.py",
    ]
    results = [run_script(root, script) for script in scripts]
    passed = sum(1 for item in results if item["是否通过"])
    report = {
        "名称": "股票轻量学习闭环维护运行记录",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "脚本数量": len(results),
        "通过数量": passed,
        "失败数量": len(results) - passed,
        "结论": "通过" if passed == len(results) else "存在失败",
        "运行结果": results,
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否自动修改正式规则": False,
            "是否自动更新重点关注池": True,
        },
    }
    out_dir = root / "04日志" / "复盘"
    latest_json = out_dir / "股票轻量学习闭环维护运行记录_最新.json"
    stamp_json = out_dir / f"股票轻量学习闭环维护运行记录_{stamp}.json"
    latest_md = out_dir / "股票轻量学习闭环维护运行记录_最新.md"
    stamp_md = out_dir / f"股票轻量学习闭环维护运行记录_{stamp}.md"
    write_json(latest_json, report)
    write_json(stamp_json, report)
    markdown = build_markdown(report)
    write_text(latest_md, markdown)
    write_text(stamp_md, markdown)
    print(json.dumps({
        "状态": "完成" if passed == len(results) else "存在失败",
        "通过数量": passed,
        "失败数量": len(results) - passed,
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
