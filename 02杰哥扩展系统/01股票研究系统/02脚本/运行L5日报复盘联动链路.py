# -*- coding: utf-8 -*-
"""
名称：运行L5日报复盘联动链路.py
作用：按顺序运行候选池日报和四本账生成脚本，形成L5日报到复盘闭环的本地链路。
触发方式：python 运行L5日报复盘联动链路.py
依赖：Python标准库；L5日报复盘联动规则.json；生成重点关注池候选池.py；生成L5深度研究报告.py；四本账脚本。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行新股票系统本地脚本；不调用大模型；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建L5日报复盘联动链路脚本。
标识：stock-l5-review-loop-run
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_script(path: Path, timeout: int = 180) -> dict[str, Any]:
    result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {
        "脚本": str(path),
        "返回码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
    }


def main() -> int:
    root = module_root()
    rules = load_json(root / "01配置" / "L5日报复盘联动规则.json")
    switches = rules.get("默认开关", {})
    scripts = []
    if switches.get("允许生成候选池"):
        scripts.append(("生成重点关注池候选池", root / "02脚本" / "生成重点关注池候选池.py", 120))
    if switches.get("允许生成L5日报"):
        scripts.append(("生成L5深度研究报告", root / "02脚本" / "生成L5深度研究报告.py", 120))
    if switches.get("允许生成系统判断账"):
        scripts.append(("记录系统判断账", root / "02脚本" / "记录系统判断账.py", 120))
    if switches.get("允许生成人工决策账模板"):
        scripts.append(("生成人工决策账模板", root / "02脚本" / "生成人工决策账模板.py", 120))
    if switches.get("允许生成结果验证计划"):
        scripts.append(("生成结果验证计划", root / "02脚本" / "生成结果验证计划.py", 120))
    if switches.get("允许生成经验提炼候选账"):
        scripts.append(("生成经验提炼候选账", root / "02脚本" / "生成经验提炼候选账.py", 120))
    results = []
    for name, path, timeout in scripts:
        item = run_script(path, timeout=timeout)
        item["名称"] = name
        results.append(item)
    ok = all(item["返回码"] == 0 for item in results)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(root / "01配置" / "L5日报复盘联动规则.json"),
        "执行数量": len(results),
        "执行结果": results,
        "输出文件": {
            "候选池": str(root / "03数据" / "14候选池" / "重点关注池候选池_最新.json"),
            "L5日报": str(root / "03数据" / "03研究报告" / "L5深度研究候选日报_最新.md"),
            "系统判断账": str(root / "03数据" / "10复盘闭环" / "01系统判断账" / "系统判断账_最新.json"),
            "人工决策账模板": str(root / "03数据" / "10复盘闭环" / "02人工决策账" / "人工决策账模板_最新.json"),
            "结果验证计划": str(root / "03数据" / "10复盘闭环" / "03结果验证账" / "结果验证计划_最新.json"),
            "经验提炼候选账": str(root / "03数据" / "10复盘闭环" / "04经验提炼账" / "经验提炼候选账_最新.json")
        },
        "安全边界": {
            "是否调用大模型": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否调用券商接口": False,
            "是否自动交易": False
        }
    }
    output_dir = root / "04日志" / "L5复盘联动"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_dir / f"stock-l5-review-loop-run-{timestamp}.json"
    latest = output_dir / "stock-l5-review-loop-run-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"执行数量": len(results), "成功": ok, "输出": str(output)}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
