# -*- coding: utf-8 -*-
"""
名称：模拟企业微信股票查询.py
作用：在禁用态模拟企业微信股票查询消息，生成股票研究助手回复草稿。
触发方式：python 模拟企业微信股票查询.py --message "分析新易盛"
依赖：Python标准库；企业微信股票查询禁用态规则.json；重点关注股票池.json；行情快照；技术指标；候选池；日常使用包；生成单股即时研究报告.py；生成企业微信单股短回复.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读新股票研究系统本地数据；只写03数据/18企业微信股票查询禁用态；不真实发送企业微信；不触发n8n；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信股票查询禁用态模拟脚本；2026-04-28 单股查询复用单股即时研究报告；2026-04-28 单股查询改用企业微信短回复。
标识：stock-wework-query-dryrun
"""

from __future__ import annotations

import argparse
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


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8-sig")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(code: str) -> str:
    code = str(code or "").strip().lower()
    if code.startswith(("sh", "sz")):
        return code[2:]
    return code.zfill(6) if code.isdigit() else code


def code_with_market(code: str) -> str:
    code = str(code or "").strip().lower()
    if code.startswith(("sh", "sz")):
        return code
    if code.startswith(("6", "9")):
        return "sh" + code
    return "sz" + code


TRADE_ACTION_PATTERNS = (
    "\u5e2e\u6211\u4e70",
    "\u5e2e\u6211\u5356",
    "\u4e70\u5165",
    "\u5356\u51fa",
    "\u4e0b\u5355",
    "\u6302\u5355",
    "\u64a4\u5355",
    "\u5efa\u4ed3",
    "\u6e05\u4ed3",
    "\u52a0\u4ed3",
    "\u51cf\u4ed3",
    "\u6ee1\u4ed3",
    "\u534a\u4ed3",
    "\u5238\u5546",
    "\u6210\u4ea4",
    "\u4ea4\u6613",
)

TRADE_RESEARCH_EXCEPTIONS = (
    "\u4e70\u5356\u70b9",
    "\u4e70\u70b9",
    "\u5356\u70b9",
    "\u4e70\u5356\u5efa\u8bae",
    "\u6295\u7814",
    "\u7814\u7a76",
    "\u5206\u6790",
)


def contains_trade_action(message: str) -> bool:
    text = str(message or "").replace(" ", "")
    if any(pattern in text for pattern in TRADE_RESEARCH_EXCEPTIONS):
        return False
    return any(pattern in text for pattern in TRADE_ACTION_PATTERNS)


def build_trade_action_refusal(message: str) -> dict[str, Any]:
    return {
        "\u72b6\u6001": "\u5df2\u62e6\u622a",
        "trade_guard": True,
        "\u539f\u59cb\u6d88\u606f": message,
        "\u56de\u590d": (
            "\u5df2\u8bc6\u522b\u5230\u4e70\u5165\u3001\u5356\u51fa\u3001\u4e0b\u5355\u6216\u5176\u4ed6\u4ea4\u6613\u52a8\u4f5c\u610f\u56fe\uff0c"
            "\u80a1\u7968\u7814\u7a76\u7cfb\u7edf\u4e0d\u6267\u884c\u4efb\u4f55\u4ea4\u6613\u6307\u4ee4\u3002\n"
            "\u53ef\u4ee5\u6539\u6210\uff1a\u5206\u6790\u65b0\u6613\u76db\u3001\u6280\u672f\u5206\u6790\u65b0\u6613\u76db\u3001"
            "\u67e5\u770bL5\u5019\u9009\u3001\u8bf4\u660e\u4e70\u5356\u70b9\u89c2\u5bdf\u6761\u4ef6\u3002\n"
            "\u58f0\u660e\uff1a\u4ec5\u4f5c\u7814\u7a76\u8f85\u52a9\uff0c\u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae\uff1b"
            "\u4e0d\u8fde\u63a5\u5238\u5546\u63a5\u53e3\uff0c\u4e0d\u81ea\u52a8\u4ea4\u6613\u3002"
        ),
    }


def find_stock(message: str, stocks: list[dict[str, Any]]) -> dict[str, Any] | None:
    text = str(message or "").strip()
    for item in stocks:
        code = str(item.get("代码") or item.get("code") or "")
        name = str(item.get("名称") or item.get("name") or "")
        if name and name in text:
            return item
        if code and (code in text or normalize_code(code) in text):
            return item
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) >= 6:
        guess = digits[:6]
        return {"代码": code_with_market(guess), "名称": guess, "关注原因": "用户输入代码"}
    return None


def quote_map(root: Path) -> dict[str, dict[str, Any]]:
    data = load_json(root / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json", {"行情": []})
    return {normalize_code(item.get("代码", "")): item for item in data.get("行情", [])}


def indicator_map(root: Path) -> dict[str, dict[str, Any]]:
    data = load_json(root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json", {"技术指标": []})
    return {normalize_code(item.get("代码", "")): item for item in data.get("技术指标", [])}


def candidate_map(root: Path) -> dict[str, dict[str, Any]]:
    data = load_json(root / "03数据" / "14候选池" / "重点关注池候选池_最新.json", {"候选池": {}})
    result: dict[str, dict[str, Any]] = {}
    for layer, items in data.get("候选池", {}).items():
        for item in items:
            result[normalize_code(item.get("代码", ""))] = {**item, "候选层级": layer}
    return result


def load_stocks(root: Path) -> list[dict[str, Any]]:
    focus = load_json(root / "01配置" / "重点关注股票池.json", {"股票池": []})
    merged = load_json(root / "01配置" / "股票池模板.json", {"股票池": []})
    return merged.get("股票池") or focus.get("股票池", [])


def data_health(root: Path) -> dict[str, Any]:
    status = load_json(root / "03数据" / "16状态摘要" / "股票研究系统状态摘要_最新.json", {})
    health = status.get("数据健康度")
    if health:
        return health
    rows = load_json(root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json", {"技术指标": []}).get("技术指标", [])
    total = len(rows)
    success = sum(1 for item in rows if item.get("状态") == "成功" or item.get("计算状态") == "成功")
    rate = round(success / total * 100, 2) if total else 0
    level = "优秀" if rate >= 95 else "可用" if rate >= 85 else "降级" if rate > 0 else "暂停"
    return {"股票数量": total, "指标成功数量": success, "成功率": rate, "健康等级": level}


def build_stock_reply(root: Path, message: str) -> dict[str, Any]:
    stocks = load_stocks(root)
    stock = find_stock(message, stocks)
    health = data_health(root)
    if not stock:
        return {
            "状态": "未识别",
            "回复": "未识别到股票名称或代码。可输入：分析新易盛、分析300502、查看L5候选、今日股票日常包。\n声明：本回复为禁用态模拟，不真实发送企业微信。",
            "数据健康度": health,
        }
    brief_reply = run_brief_reply(root, stock)
    code = normalize_code(stock.get("代码") or stock.get("code") or "")
    name = stock.get("名称") or stock.get("name") or code
    quote = quote_map(root).get(code, {})
    indicator = indicator_map(root).get(code, {})
    candidate = candidate_map(root).get(code, {})
    basis = "；".join(candidate.get("依据", [])[:3]) or "暂无候选池依据，需结合行情和后续报告。"
    risks = "；".join(candidate.get("风险", [])[:3]) or "未发现候选池突出风险，仍需人工复核。"
    layer = candidate.get("候选层级") or candidate.get("层级") or "未进入候选池"
    ma = indicator.get("均线", {})
    if brief_reply.get("状态") == "完成" and brief_reply.get("短回复"):
        return {
            "状态": "完成",
            "股票": stock,
            "行情": quote,
            "技术指标": indicator,
            "候选信息": candidate,
            "企业微信短回复": brief_reply,
            "数据健康度": health,
            "回复": brief_reply["短回复"],
        }
    reply_lines = [
        f"{name}（{stock.get('代码') or stock.get('code')}）股票研究助手",
        f"数据健康度：{health.get('健康等级')}，指标成功{health.get('指标成功数量')}/{health.get('股票数量')}，成功率{health.get('成功率')}%。",
        f"行情：最新价{quote.get('最新价', '无')}，涨跌幅{quote.get('涨跌幅', '无')}%，行业{quote.get('行业', '无')}。",
        f"技术：状态{indicator.get('状态', '无')}，K线{indicator.get('K线数量', 0)}条，最新日期{indicator.get('最新日期', '无')}，MA5={ma.get('MA5')}，MA20={ma.get('MA20')}，RSI14={indicator.get('RSI14')}。",
        f"分层：{layer}，系统评分{candidate.get('系统评分', '无')}。",
        f"即时报告：{brief_reply.get('完整报告', '未生成')}",
        f"依据：{basis}",
        f"风险：{risks}",
        "反馈格式：继续观察：股票名称，原因；暂不关注：股票名称，原因；无价值：股票名称，原因；确认L4：股票名称，原因。",
        "声明：本回复为企业微信禁用态模拟草稿，只用于研究辅助，不构成投资建议，不连接券商接口，不自动交易。",
    ]
    return {
        "状态": "完成",
        "股票": stock,
        "行情": quote,
        "技术指标": indicator,
        "候选信息": candidate,
        "企业微信短回复": brief_reply,
        "数据健康度": health,
        "回复": "\n".join(reply_lines),
    }


def run_brief_reply(root: Path, stock: dict[str, Any]) -> dict[str, Any]:
    script = root / "02脚本" / "生成企业微信单股短回复.py"
    name = str(stock.get("名称") or stock.get("代码") or "")
    if not script.exists() or not name:
        return {"状态": "未生成", "原因": "企业微信短回复脚本或股票名称缺失"}
    result = subprocess.run([sys.executable, str(script), "--stock", name], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "24企业微信短回复" / "企业微信单股短回复_最新.json"
    payload = load_json(latest_json, {})
    return {
        "状态": "完成" if result.returncode == 0 and payload.get("短回复") else "失败",
        "返回码": result.returncode,
        "短回复": payload.get("短回复", ""),
        "短回复Markdown": str(root / "03数据" / "24企业微信短回复" / "企业微信单股短回复_最新.md"),
        "完整报告": payload.get("单股报告", {}).get("Markdown", ""),
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
    }


def run_single_report(root: Path, stock: dict[str, Any]) -> dict[str, Any]:
    script = root / "02脚本" / "生成单股即时研究报告.py"
    name = str(stock.get("名称") or stock.get("代码") or "")
    if not script.exists() or not name:
        return {"状态": "未生成", "原因": "单股即时报告脚本或股票名称缺失"}
    result = subprocess.run([sys.executable, str(script), "--stock", name], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest = root / "03数据" / "23单股即时报告" / "单股即时研究报告_最新.md"
    return {
        "状态": "完成" if result.returncode == 0 and latest.exists() else "失败",
        "返回码": result.returncode,
        "最新Markdown": str(latest) if latest.exists() else "",
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
    }


def build_l5_reply(root: Path) -> dict[str, Any]:
    health = data_health(root)
    data = load_json(root / "03数据" / "14候选池" / "重点关注池候选池_最新.json", {"候选池": {}})
    items = data.get("候选池", {}).get("L5深度研究", [])
    lines = [
        "L5深度研究候选",
        f"数据健康度：{health.get('健康等级')}，指标成功{health.get('指标成功数量')}/{health.get('股票数量')}。",
    ]
    for item in items[:8]:
        lines.append(f"- {item.get('名称')}（{item.get('代码')}）：评分{item.get('系统评分')}，风险：{'；'.join(item.get('风险', [])[:2]) or '待复核'}")
    lines.append("声明：禁用态模拟草稿，不真实发送企业微信，不构成投资建议。")
    return {"状态": "完成", "数据健康度": health, "回复": "\n".join(lines), "L5数量": len(items)}


def build_daily_package_reply(root: Path) -> dict[str, Any]:
    health = data_health(root)
    text = read_text(root / "03数据" / "17日常使用包" / "股票研究日常使用包_最新.md", "")
    lines = [line for line in text.splitlines() if line.strip()]
    excerpt = "\n".join(lines[:18])
    reply = f"{excerpt}\n\n声明：禁用态模拟草稿，不真实发送企业微信，不构成投资建议。"
    return {"状态": "完成", "数据健康度": health, "回复": reply}


def classify(message: str) -> str:
    text = str(message or "")
    if "日常包" in text or "今日股票" in text or "股票日报" in text:
        return "日常包"
    if "L5" in text.upper() or "候选" in text:
        return "L5候选"
    if "数据健康" in text or "健康度" in text:
        return "数据健康度"
    return "单股分析"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", default="分析新易盛")
    parser.add_argument("--sender", default="dry-run-user")
    args = parser.parse_args()
    root = module_root()
    rules = load_json(root / "01配置" / "企业微信股票查询禁用态规则.json", {})
    intent = classify(args.message)
    if contains_trade_action(args.message):
        intent = "交易指令拦截"
        result = build_trade_action_refusal(args.message)
    elif intent == "日常包":
        result = build_daily_package_reply(root)
    elif intent == "L5候选":
        result = build_l5_reply(root)
    elif intent == "数据健康度":
        health = data_health(root)
        result = {"状态": "完成", "数据健康度": health, "回复": f"数据健康度：{health.get('健康等级')}，指标成功{health.get('指标成功数量')}/{health.get('股票数量')}，成功率{health.get('成功率')}%。\n声明：禁用态模拟草稿，不真实发送企业微信。"}
    else:
        result = build_stock_reply(root, args.message)
    payload = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": rules.get("模式", "dry_run_only"),
        "发送人": args.sender,
        "原始消息": args.message,
        "识别意图": intent,
        "结果": result,
        "企业微信真实发送": False,
        "触发n8n": False,
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否写旧系统": False,
            "是否写正式库": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = root / "03数据" / "18企业微信股票查询禁用态"
    json_output = output_dir / f"企业微信股票查询禁用态_{stamp}.json"
    json_latest = output_dir / "企业微信股票查询禁用态_最新.json"
    md_output = output_dir / f"企业微信股票查询禁用态_{stamp}.md"
    md_latest = output_dir / "企业微信股票查询禁用态_最新.md"
    markdown = "# 企业微信股票查询禁用态回复草稿\n\n" + result.get("回复", "")
    write_json(json_output, payload)
    write_json(json_latest, payload)
    write_text(md_output, markdown)
    write_text(md_latest, markdown)
    print(json.dumps({"意图": intent, "状态": result.get("状态"), "输出": str(json_output)}, ensure_ascii=False))
    return 0 if result.get("状态") in {"完成", "已拦截"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
