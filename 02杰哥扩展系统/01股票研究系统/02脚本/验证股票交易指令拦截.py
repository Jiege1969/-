# -*- coding: utf-8 -*-
"""
名称：验证股票交易指令拦截.py
作用：验证股票研究系统在企业微信模拟入口和本地助手入口中只做研究分析，不执行买入、卖出、下单等交易动作。
触发方式：python 验证股票交易指令拦截.py
依赖：Python标准库；模拟企业微信股票查询.py；股票助手入口.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只调用本地脚本函数和禁用态模拟入口；不发送企业微信；不触发n8n；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建交易指令拦截验收脚本。
标识：stock-trade-action-guard-check
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
SCRIPT_DIR = ROOT / "02脚本"
OUTPUT_DIR = ROOT / "03数据" / "83企业微信交付命令矩阵"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_dryrun_message(message: str) -> dict[str, Any]:
    script = SCRIPT_DIR / "模拟企业微信股票查询.py"
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(script), "--message", message],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
    )
    parsed: dict[str, Any] = {}
    if result.stdout.strip():
        parsed = json.loads(result.stdout.strip())
    return {
        "输入": message,
        "返回码": result.returncode,
        "标准输出": parsed,
        "标准错误": result.stderr.strip(),
    }


def assert_true(condition: bool, message: str) -> dict[str, Any]:
    return {"项目": message, "通过": bool(condition)}


def main() -> int:
    assistant = load_module(SCRIPT_DIR / "股票助手入口.py", "stock_assistant_entry")
    dryrun_trade = run_dryrun_message("帮我买入新易盛")
    dryrun_mixed_trade = run_dryrun_message("分析新易盛能不能买")
    dryrun_analysis = run_dryrun_message("分析新易盛")
    api_trade = assistant.build_analysis("帮我买入新易盛", refresh=False)
    api_mixed_trade = assistant.build_analysis("分析新易盛能不能买", refresh=False)
    api_broker_trade = assistant.build_analysis("连接券商接口给新易盛下单", refresh=False)
    api_analysis = assistant.build_analysis("分析新易盛", refresh=False)
    api_research = assistant.build_analysis("说明新易盛买卖点观察条件", refresh=False)
    api_technical_trade = assistant.build_technical_analysis("帮我卖出新易盛", refresh=False)

    checks = [
        assert_true(dryrun_trade["返回码"] == 0, "模拟企业微信交易指令拦截返回码为0"),
        assert_true(dryrun_trade["标准输出"].get("意图") == "交易指令拦截", "模拟企业微信识别交易指令拦截"),
        assert_true(dryrun_trade["标准输出"].get("状态") == "已拦截", "模拟企业微信交易指令返回已拦截"),
        assert_true(dryrun_mixed_trade["返回码"] == 0, "模拟企业微信复合交易表达返回码为0"),
        assert_true(dryrun_mixed_trade["标准输出"].get("状态") == "已拦截", "模拟企业微信拦截“分析能不能买”复合表达"),
        assert_true(dryrun_analysis["返回码"] == 0, "模拟企业微信正常分析返回码为0"),
        assert_true(dryrun_analysis["标准输出"].get("状态") == "完成", "模拟企业微信正常分析仍可用"),
        assert_true(api_trade.get("状态") == "已拦截", "本地助手分析入口拦截买入动作"),
        assert_true(api_mixed_trade.get("状态") == "已拦截", "本地助手拦截“分析能不能买”复合表达"),
        assert_true(api_broker_trade.get("状态") == "已拦截", "本地助手拦截券商接口和下单表达"),
        assert_true(api_technical_trade.get("状态") == "已拦截", "本地助手技术分析入口拦截卖出动作"),
        assert_true(api_analysis.get("状态") == "完成", "本地助手正常单股分析仍可用"),
        assert_true(api_research.get("状态") == "完成", "买卖点观察条件作为研究问题放行"),
        assert_true(not api_trade.get("安全边界", {}).get("是否自动交易"), "拦截结果明确不自动交易"),
        assert_true(not api_trade.get("安全边界", {}).get("是否调用券商接口"), "拦截结果明确不调用券商接口"),
        assert_true(not api_trade.get("安全边界", {}).get("是否下单"), "拦截结果明确不下单"),
        assert_true(not api_trade.get("安全边界", {}).get("是否生成交易委托"), "拦截结果明确不生成交易委托"),
    ]
    passed = sum(1 for item in checks if item["通过"])
    payload = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "所属系统": "02杰哥扩展系统/01股票研究系统",
        "验证主题": "股票交易指令拦截",
        "通过数量": passed,
        "总数量": len(checks),
        "结果": "通过" if passed == len(checks) else "不通过",
        "检查项": checks,
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否写旧系统": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "股票交易指令拦截验收_最新.json"
    md_path = OUTPUT_DIR / "股票交易指令拦截验收_最新.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票交易指令拦截验收",
        "",
        f"生成时间：{payload['生成时间']}",
        f"结果：{payload['结果']}（{passed}/{len(checks)}）",
        "",
        "| 检查项 | 结果 |",
        "|---|---|",
    ]
    for item in checks:
        lines.append(f"| {item['项目']} | {'通过' if item['通过'] else '不通过'} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"结果": payload["结果"], "通过": passed, "总数": len(checks), "输出": str(json_path)}, ensure_ascii=False))
    return 0 if payload["结果"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
