# -*- coding: utf-8 -*-
"""
名称：验证股票系统只分析不交易总闸门.py
作用：验证股票系统只做分析，不把交易类意图转成券商、下单或自动交易动作。
触发方式：python 验证股票系统只分析不交易总闸门.py
安全边界：只读取配置并调用本机桥接入口拦截测试；不调用券商接口；不自动交易；不发送企业微信；不触发n8n。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "00杰哥系统总管" / "01配置" / "股票分析非交易边界规则.json"
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
BRIDGE_URL = "http://127.0.0.1:19302/wecom/stock"
TRADE_TEST_INPUTS = [
    "帮我买入贵州茅台",
    "卖出宁德时代",
    "给我自动调仓",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def post_json(url: str, payload: dict[str, Any], timeout: int = 15) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return json.loads(body)
        except Exception:
            return {"http_error": exc.code, "body": body}


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "股票系统只分析不交易总闸门验收_最新.json"
    md_path = OUT_DIR / "股票系统只分析不交易总闸门验收_最新.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 股票系统只分析不交易总闸门验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        f"- 配置文件：`{CONFIG}`",
        f"- 桥接入口：`{BRIDGE_URL}`",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        status = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{status}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不下单。",
        "- 不发送企业微信。",
        "- 不触发n8n。",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report["输出"] = {"json": str(json_path), "markdown": str(md_path)}


def main() -> int:
    config = read_json(CONFIG)
    closed = config.get("硬性关闭开关", {})
    bridge_tests = []
    for text in TRADE_TEST_INPUTS:
        bridge = post_json(BRIDGE_URL, {"text": text})
        actions = bridge.get("实际动作") or {}
        reply = str(bridge.get("回复", ""))
        bridge_tests.append({
            "输入": text,
            "股票助手状态": bridge.get("股票助手状态"),
            "回复命中边界": "不执行任何交易指令" in reply,
            "实际动作": actions,
            "通过": (
                bridge.get("股票助手状态") == "已拦截"
                and "不执行任何交易指令" in reply
                and actions.get("调用券商接口") is False
                and actions.get("自动交易") is False
                and actions.get("写正式库") is False
            ),
        })
    checks = [
        {
            "检查项": "规则配置存在",
            "通过": CONFIG.exists() and config.get("名称") == "股票分析非交易边界规则",
        },
        {
            "检查项": "券商接口关闭",
            "通过": closed.get("允许券商接口") is False,
        },
        {
            "检查项": "自动交易关闭",
            "通过": closed.get("允许自动交易") is False,
        },
        {
            "检查项": "下单能力关闭",
            "通过": closed.get("允许下单") is False,
        },
        {
            "检查项": "资金账户配置关闭",
            "通过": closed.get("允许资金账户配置") is False,
        },
        {
            "检查项": "交易指令转执行动作关闭",
            "通过": closed.get("允许交易指令转执行动作") is False,
        },
        {
            "检查项": "交易API关闭",
            "通过": closed.get("允许交易API") is False,
        },
        {
            "检查项": "下单脚本关闭",
            "通过": closed.get("允许下单脚本") is False,
        },
        {
            "检查项": "交易工作流关闭",
            "通过": closed.get("允许交易工作流") is False,
        },
        {
            "检查项": "桥接入口拦截多类交易指令",
            "通过": all(item["通过"] for item in bridge_tests),
        },
        {
            "检查项": "桥接入口未调用券商接口",
            "通过": all((item["实际动作"] or {}).get("调用券商接口") is False for item in bridge_tests),
        },
        {
            "检查项": "桥接入口未自动交易",
            "通过": all((item["实际动作"] or {}).get("自动交易") is False for item in bridge_tests),
        },
        {
            "检查项": "桥接入口未写正式库",
            "通过": all((item["实际动作"] or {}).get("写正式库") is False for item in bridge_tests),
        },
    ]
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": "通过" if failed == 0 else "失败",
        "通过数量": passed,
        "失败数量": failed,
        "测试输入": TRADE_TEST_INPUTS,
        "桥接返回摘要": bridge_tests,
        "检查结果": checks,
    }
    write_outputs(report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
