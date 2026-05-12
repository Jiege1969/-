# -*- coding: utf-8 -*-
"""
名称：股票助手入口.py
作用：提供新股票研究系统的独立本地网页和API入口，对标旧系统股票分析服务的使用体验。
触发方式：python 股票助手入口.py
依赖：Python标准库；股票助手体验配置.json；重点关注股票池.json；运行股票日常研究链路.py；生成重点关注池公开行情快照.py。
所属系统：02杰哥扩展系统/01股票研究系统
输出：本地 HTTP 服务 127.0.0.1:19300；命令行问答文本；单股标准报告v2；判断复盘账。
安全边界：仅绑定127.0.0.1；只写新系统股票模块目录；不调用券商接口；不自动交易；不写旧系统；不触发n8n；不发送企业微信；不占用旧系统18300端口。
创建/修改记录：2026-04-28 创建股票助手独立体验入口。
标识：stock-assistant-experience-service
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import html
import textwrap
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
PUBLIC_ENTRY_CONFIG_PATH = ROOT / "01配置" / "股票公网入口配置.json"
CONFIG_PATH = ROOT / "01配置" / "股票助手体验配置.json"
FRONT_OUTPUT_STANDARD_PATH = ROOT / "01配置" / "股票前台输出标准_v2.json"
BAILLIE_GROWTH_FRAMEWORK_PATH = ROOT / "01配置" / "柏基长期成长分析框架_v1.json"
FOCUS_POOL_PATH = ROOT / "01配置" / "重点关注股票池.json"
MERGED_POOL_PATH = ROOT / "01配置" / "股票池模板.json"
QUOTE_LATEST_PATH = ROOT / "03数据" / "04数据快照" / "重点关注池公开行情快照_最新.json"
REPORT_LATEST_PATH = ROOT / "03数据" / "03研究报告" / "股票研究报告_最新.md"
CANDIDATE_REPORT_LATEST_PATH = ROOT / "03数据" / "03研究报告" / "重点关注池候选池报告_最新.md"
CANDIDATE_POOL_LATEST_PATH = ROOT / "03数据" / "14候选池" / "重点关注池候选池_最新.json"
L5_RESEARCH_REPORT_LATEST_PATH = ROOT / "03数据" / "03研究报告" / "L5深度研究候选日报_最新.md"
L5_RESEARCH_JSON_LATEST_PATH = ROOT / "03数据" / "15深度研究" / "L5深度研究报告_最新.json"
INDICATOR_LATEST_PATH = ROOT / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json"
HISTORY_KLINE_LATEST_PATH = ROOT / "03数据" / "11历史行情" / "重点关注池历史K线快照_最新.json"
STATUS_SUMMARY_JSON_LATEST_PATH = ROOT / "03数据" / "16状态摘要" / "股票研究系统状态摘要_最新.json"
STATUS_SUMMARY_MD_LATEST_PATH = ROOT / "03数据" / "16状态摘要" / "股票研究系统状态摘要_最新.md"
DAILY_PACKAGE_JSON_LATEST_PATH = ROOT / "03数据" / "17日常使用包" / "股票研究日常使用包_最新.json"
DAILY_PACKAGE_MD_LATEST_PATH = ROOT / "03数据" / "17日常使用包" / "股票研究日常使用包_最新.md"
HISTORY_DIR = ROOT / "04日志" / "助手入口"
def load_public_entry_config() -> dict[str, Any]:
    if not PUBLIC_ENTRY_CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(PUBLIC_ENTRY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


PUBLIC_ENTRY_CONFIG = load_public_entry_config()
PUBLIC_BASE_URL = str(os.getenv("JIEGE_STOCK_PUBLIC_BASE_URL") or PUBLIC_ENTRY_CONFIG.get("公网基址") or "").rstrip("/")
PUBLIC_BOT_MESSAGE_PATH = str(PUBLIC_ENTRY_CONFIG.get("智能机器人路径") or "/wecom-bot/message")


def public_stock_url(query: str) -> str:
    path = query if query.startswith("/") else f"/{query}"
    return f"{PUBLIC_BASE_URL}{path}"


def public_single_stock_report_url(name: Any) -> str:
    """企业微信前台单股详情直达入口，不能指向推荐总览页。"""
    stock_name = str(name or "").strip()
    return public_stock_url(f"{PUBLIC_BOT_MESSAGE_PATH}?ask=分析{stock_name}")


CARD_DIR = ROOT / "03数据" / "86图形报告"
CARD_LATEST_SVG_PATH = CARD_DIR / "股票图形报告_最新.svg"
CARD_LATEST_JSON_PATH = CARD_DIR / "股票图形报告_最新.json"
CARD_LATEST_PNG_PATH = CARD_DIR / "股票图形报告_最新.png"
CARD_LATEST_ICON_PATH = CARD_DIR / "股票星级图标_最新.png"
PNG_RENDERER_PATH = ROOT / "02脚本" / "生成股票图形报告PNG.ps1"
LOCAL_CARD_URL = "http://127.0.0.1:19300/card/latest.svg"
LOCAL_CARD_PNG_URL = "http://127.0.0.1:19300/card/latest.png"
LOCAL_SIGNAL_ICON_URL = "http://127.0.0.1:19300/card/signal-icon.png"
PUBLIC_CARD_URL = public_stock_url(f"{PUBLIC_BOT_MESSAGE_PATH}?card=latest")
PUBLIC_CARD_PNG_URL = public_stock_url(f"{PUBLIC_BOT_MESSAGE_PATH}?card=latest_png")
PUBLIC_SIGNAL_ICON_URL = public_stock_url(f"{PUBLIC_BOT_MESSAGE_PATH}?card=signal_icon")
SYSTEM_JUDGMENT_LEDGER_PATH = ROOT / "03数据" / "10复盘闭环" / "01系统判断账" / "系统判断账_最新.json"
HUMAN_DECISION_LEDGER_PATH = ROOT / "03数据" / "10复盘闭环" / "02人工决策账" / "人工决策账模板_最新.json"
RESULT_VERIFICATION_LEDGER_PATH = ROOT / "03数据" / "10复盘闭环" / "03结果验证账" / "结果验证计划_最新.json"
EXPERIENCE_CANDIDATE_LEDGER_PATH = ROOT / "03数据" / "10复盘闭环" / "04经验提炼账" / "经验提炼候选账_最新.json"
COMPANY_SNAPSHOT_LATEST_PATH = ROOT / "03数据" / "166公司经营快照" / "公司经营快照_最新.json"
INDUSTRY_PROSPERITY_LATEST_PATH = ROOT / "03数据" / "167行业景气结论" / "行业景气结论_最新.json"
STANDARD_REPORT_V2_DIR = ROOT / "03数据" / "135分层日报"
AI_DAILY_REPORT_JSON_PATH = STANDARD_REPORT_V2_DIR / "AI分析报告_最新.json"
JUDGMENT_REPLAY_LEDGER_LATEST_PATH = ROOT / "04日志" / "复盘" / "判断复盘账_最新.json"
WECHAT_PUSH_DRAFT_LATEST_PATH = ROOT / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"
EXPERT_OVERVIEW_DIR = ROOT / "03数据" / "185专家市场总览"
EXPERT_OVERVIEW_JSON_LATEST_PATH = EXPERT_OVERVIEW_DIR / "股票专家市场总览_最新.json"
EXPERT_OVERVIEW_MD_LATEST_PATH = EXPERT_OVERVIEW_DIR / "股票专家市场总览_最新.md"
REPORT_CREDIBILITY_LATEST_PATH = ROOT / "03数据" / "170报告可信度面板" / "股票报告可信度与数据缺口面板_最新.json"
EVIDENCE_OVERVIEW_LATEST_PATH = ROOT / "03数据" / "180证据核验总览面板" / "股票证据核验总览面板_最新.json"
FINANCE_REVIEW_LATEST_PATH = ROOT / "03数据" / "149金融专项复核" / "股票金融专项复核_最新.json"
FINANCE_REVIEW_INDEX_LATEST_PATH = ROOT / "03数据" / "149金融专项复核索引" / "股票金融专项复核索引_最新.json"
MODEL_HEALTH_LATEST_PATH = ROOT / "03数据" / "148模型健康检查" / "股票系统模型健康检查_最新.md"
FINAL_ACCEPTANCE_LATEST_PATH = ROOT / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md"
RISK_OBSERVATION_PANEL_LATEST_PATH = ROOT / "03数据" / "184风险失效条件观察面板" / "股票风险失效条件观察面板_最新.json"
PUBLIC_CALLBACK_STATUS_SCRIPT = ROOT / "02脚本" / "查看股票公网回调状态.ps1"


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


def load_front_output_standard() -> dict[str, Any]:
    value = load_json(FRONT_OUTPUT_STANDARD_PATH, {}) or {}
    return value if isinstance(value, dict) else {}


def single_stock_template_config() -> dict[str, Any]:
    standard = load_front_output_standard()
    value = standard.get("单股短答模板", {}) if isinstance(standard, dict) else {}
    return value if isinstance(value, dict) else {}


def load_baillie_growth_framework() -> dict[str, Any]:
    value = load_json(BAILLIE_GROWTH_FRAMEWORK_PATH, {}) or {}
    return value if isinstance(value, dict) else {}


def text_response(body: str, status: int = 200, content_type: str = "text/plain; charset=utf-8") -> tuple[int, bytes, str]:
    return status, body.encode("utf-8"), content_type


def json_response(data: dict[str, Any], status: int = 200) -> tuple[int, bytes, str]:
    return status, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"), "application/json; charset=utf-8"


def load_config() -> dict[str, Any]:
    return load_json(CONFIG_PATH, {}) or {}


def focus_stocks() -> list[dict[str, Any]]:
    data = load_json(FOCUS_POOL_PATH, {"股票池": []})
    return data.get("股票池", [])


def merged_stocks() -> list[dict[str, Any]]:
    data = load_json(MERGED_POOL_PATH, {"股票池": []})
    stocks = data.get("股票池", [])
    if stocks:
        return stocks
    return focus_stocks()


def daily_ai_report_stocks() -> list[dict[str, Any]]:
    data = load_json(AI_DAILY_REPORT_JSON_PATH, {"分析结果": []}) or {"分析结果": []}
    stocks: list[dict[str, Any]] = []
    for row in data.get("分析结果", []):
        if not isinstance(row, dict):
            continue
        code = str(row.get("代码") or row.get("code") or "").strip()
        name = str(row.get("名称") or row.get("name") or "").strip()
        if not code and not name:
            continue
        item = dict(row)
        item.setdefault("关注原因", "最新AI日报推荐/观察股票")
        item.setdefault("来源", str(AI_DAILY_REPORT_JSON_PATH))
        stocks.append(item)
    return stocks


def all_recognizable_stocks() -> list[dict[str, Any]]:
    stocks: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for source in (merged_stocks(), daily_ai_report_stocks()):
        for item in source:
            code = normalize_full_code(item.get("代码") or item.get("code") or "")
            name = str(item.get("名称") or item.get("name") or "")
            key = (code, name)
            if key in seen:
                continue
            seen.add(key)
            stocks.append(item)
    return stocks


def normalize_code(code: str) -> str:
    code = str(code or "").strip().lower()
    if code.startswith(("sh", "sz")):
        return code[2:]
    return code


def code_with_market(code: str) -> str:
    code = str(code or "").strip().lower()
    if code.startswith(("sh", "sz")):
        return code
    if code.startswith(("6", "9")):
        return "sh" + code
    return "sz" + code


def normalize_full_code(code: str) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.lower()
        if suffix == "sh":
            return "sh" + num
        if suffix == "sz":
            return "sz" + num
        if suffix == "bj":
            return "bj" + num
    if text.startswith(("6", "9")):
        return "sh" + text.zfill(6)
    if text.startswith(("4", "8")):
        return "bj" + text.zfill(6)
    return "sz" + text.zfill(6) if text.isdigit() else text


def find_company_snapshot(stock: dict[str, Any]) -> dict[str, Any]:
    data = load_json(COMPANY_SNAPSHOT_LATEST_PATH, {"股票快照": []}) or {"股票快照": []}
    target = normalize_full_code(stock.get("代码") or stock.get("code") or "")
    name = str(stock.get("名称") or stock.get("name") or "")
    for item in data.get("股票快照", []):
        if normalize_full_code(item.get("代码")) == target or (name and item.get("名称") == name):
            return item
    return {}


def find_industry_prosperity(industry: str) -> dict[str, Any]:
    data = load_json(INDUSTRY_PROSPERITY_LATEST_PATH, {"行业景气结论": []}) or {"行业景气结论": []}
    for item in data.get("行业景气结论", []):
        if item.get("行业") == industry:
            return item
    return {}


TRADE_ACTION_PATTERNS = (
    "\u5e2e\u6211\u4e70",
    "\u5e2e\u6211\u5356",
    "\u4e70\u5165",
    "\u5356\u51fa",
    "能不能买",
    "可以买",
    "要不要买",
    "能买",
    "买不买",
    "\u4e0b\u5355",
    "\u6302\u5355",
    "\u64a4\u5355",
    "\u8c03\u4ed3",
    "\u5efa\u4ed3",
    "\u6e05\u4ed3",
    "\u52a0\u4ed3",
    "\u51cf\u4ed3",
    "\u6ee1\u4ed3",
    "\u534a\u4ed3",
    "\u5238\u5546",
    "\u6210\u4ea4",
    "\u4ea4\u6613",
    "\u4ea4\u6613API",
    "\u4ea4\u6613api",
    "\u4ea4\u6613\u63a5\u53e3",
    "\u8d44\u91d1\u8d26\u6237",
    "\u59d4\u6258",
    "\u4ed3\u4f4d\u5efa\u8bae",
    "\u76ee\u6807\u4ef7",
)

TRADE_RESEARCH_EXCEPTIONS = (
    "\u4e70\u5356\u70b9",
    "\u4e70\u70b9",
    "\u5356\u70b9",
    "\u89c2\u5bdf\u6761\u4ef6",
    "\u98ce\u9669\u89c2\u5bdf\u7ebf",
    "\u8f6c\u5f3a\u6761\u4ef6",
    "\u5931\u6548\u6761\u4ef6",
)


def contains_trade_action(message: str) -> bool:
    text = str(message or "").replace(" ", "")
    if any(pattern in text for pattern in TRADE_RESEARCH_EXCEPTIONS) and not any(
        pattern in text for pattern in (
            "\u4e70\u5165",
            "\u5356\u51fa",
            "\u4e0b\u5355",
            "\u6302\u5355",
            "\u64a4\u5355",
            "\u5238\u5546",
            "\u4ea4\u6613API",
            "\u4ea4\u6613api",
            "\u8d44\u91d1\u8d26\u6237",
            "\u81ea\u52a8\u4ea4\u6613",
            "\u59d4\u6258",
        )
    ):
        return False
    return any(pattern in text for pattern in TRADE_ACTION_PATTERNS)


RECENT_STOCK_CONTEXT: list[dict[str, Any]] = []
RECENT_STOCK_CONTEXT_TTL_SECONDS = 5 * 60
RECENT_STOCK_CONTEXT_LIMIT = 5


def build_trade_action_refusal(message: str) -> dict[str, Any]:
    stock = find_stock(message)
    if stock:
        target = stock_display_name(stock)
        research_hint = (
            f"我不能执行买卖指令，也不直接给下单建议；不执行任何交易指令。\n"
            f"可以把它转成研究问题：分析{target}，看当前判断、参考位置、风险观察线和持仓处理建议。"
        )
    else:
        research_hint = (
            "我不能执行买卖指令，也不直接给下单建议；不执行任何交易指令。\n"
            "可以改成研究问题：分析某只股票、看今日推荐、或问某只持仓还能不能拿。"
        )
    return {
        "\u72b6\u6001": "\u5df2\u62e6\u622a",
        "\u8f93\u5165": message,
        "trade_guard": True,
        "\u56de\u590d": (
            "\u5df2\u8bc6\u522b\u5230\u4e70\u5165\u3001\u5356\u51fa\u3001\u4e0b\u5355\u6216\u5176\u4ed6\u4ea4\u6613\u52a8\u4f5c\u610f\u56fe\u3002\n"
            f"{research_hint}\n"
            "\u58f0\u660e\uff1a\u672c\u7cfb\u7edf\u4e25\u683c\u6309\u5206\u6790\u7cfb\u7edf\u6807\u51c6\u8fd0\u884c\uff0c\u4ec5\u4f5c\u7814\u7a76\u8f85\u52a9\uff0c\u4e0d\u6784\u6210\u6295\u8d44\u5efa\u8bae\uff1b"
            "\u4e0d\u8fde\u63a5\u5238\u5546\u63a5\u53e3\uff0c\u4e0d\u4e0b\u5355\uff0c\u4e0d\u751f\u6210\u4ea4\u6613\u59d4\u6258\uff0c\u4e0d\u81ea\u52a8\u4ea4\u6613\u3002"
        ),
        "\u5b89\u5168\u8fb9\u754c": {
            "\u662f\u5426\u8c03\u7528\u5238\u5546\u63a5\u53e3": False,
            "\u662f\u5426\u81ea\u52a8\u4ea4\u6613": False,
            "\u662f\u5426\u53d1\u9001\u4f01\u4e1a\u5fae\u4fe1": False,
            "\u662f\u5426\u4e0b\u5355": False,
            "\u662f\u5426\u751f\u6210\u4ea4\u6613\u59d4\u6258": False,
        },
    }


def stock_display_name(stock: dict[str, Any]) -> str:
    name = stock.get("名称") or stock.get("name") or stock.get("代码") or stock.get("code") or "这只股票"
    code = stock.get("代码") or stock.get("code") or ""
    return f"{name}({code})" if code and str(code) not in str(name) else str(name)


def remember_recent_stock(stock: dict[str, Any] | None) -> None:
    if not stock:
        return
    code = str(stock.get("代码") or stock.get("code") or "").lower()
    name = str(stock.get("名称") or stock.get("name") or code or "").strip()
    if not code and not name:
        return
    now = datetime.now().timestamp()
    fresh = []
    for item in RECENT_STOCK_CONTEXT:
        if now - float(item.get("time", 0)) <= RECENT_STOCK_CONTEXT_TTL_SECONDS:
            existing = item.get("code") or item.get("name")
            current = code or name
            if existing != current:
                fresh.append(item)
    fresh.insert(0, {"time": now, "code": code, "name": name, "stock": stock})
    del RECENT_STOCK_CONTEXT[:]
    RECENT_STOCK_CONTEXT.extend(fresh[:RECENT_STOCK_CONTEXT_LIMIT])


def recent_context_stocks() -> list[dict[str, Any]]:
    now = datetime.now().timestamp()
    fresh = [
        item for item in RECENT_STOCK_CONTEXT
        if now - float(item.get("time", 0)) <= RECENT_STOCK_CONTEXT_TTL_SECONDS
    ]
    del RECENT_STOCK_CONTEXT[:]
    RECENT_STOCK_CONTEXT.extend(fresh[:RECENT_STOCK_CONTEXT_LIMIT])
    return [item["stock"] for item in RECENT_STOCK_CONTEXT if isinstance(item.get("stock"), dict)]


def find_stock(question: str) -> dict[str, Any] | None:
    text = str(question or "").strip()
    if not text:
        return None
    stocks = all_recognizable_stocks()
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


def run_script(script_name: str, timeout: int = 180) -> dict[str, Any]:
    script = ROOT / "02脚本" / script_name
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=timeout,
    )
    return {
        "脚本": str(script),
        "返回码": result.returncode,
        "标准输出": result.stdout.strip(),
        "标准错误": result.stderr.strip(),
    }


def update_quote_snapshot() -> dict[str, Any]:
    run = run_script("生成重点关注池公开行情快照.py", timeout=60)
    snapshot = load_json(QUOTE_LATEST_PATH, {}) or {}
    snapshot["刷新结果"] = run
    return snapshot


def latest_quote_snapshot(refresh: bool = False) -> dict[str, Any]:
    if refresh or not QUOTE_LATEST_PATH.exists():
        return update_quote_snapshot()
    return load_json(QUOTE_LATEST_PATH, {}) or {}


def latest_ledgers() -> dict[str, Any]:
    return {
        "系统判断账": load_json(SYSTEM_JUDGMENT_LEDGER_PATH, {}) or {},
        "人工决策账模板": load_json(HUMAN_DECISION_LEDGER_PATH, {}) or {},
        "结果验证计划": load_json(RESULT_VERIFICATION_LEDGER_PATH, {}) or {},
        "经验提炼候选账": load_json(EXPERIENCE_CANDIDATE_LEDGER_PATH, {}) or {},
        "路径": {
            "系统判断账": str(SYSTEM_JUDGMENT_LEDGER_PATH),
            "人工决策账模板": str(HUMAN_DECISION_LEDGER_PATH),
            "结果验证计划": str(RESULT_VERIFICATION_LEDGER_PATH),
            "经验提炼候选账": str(EXPERIENCE_CANDIDATE_LEDGER_PATH),
        }
    }


def latest_data_health() -> dict[str, Any]:
    l5_report = load_json(L5_RESEARCH_JSON_LATEST_PATH, {}) or {}
    if l5_report.get("数据健康度"):
        return {
            "状态": "完成",
            "来源": str(L5_RESEARCH_JSON_LATEST_PATH),
            "数据健康度": l5_report.get("数据健康度"),
        }
    indicators = load_json(INDICATOR_LATEST_PATH, {}) or {}
    history = load_json(HISTORY_KLINE_LATEST_PATH, {}) or {}
    rows = indicators.get("技术指标", [])
    total = len(rows)
    success = sum(1 for item in rows if item.get("状态") == "成功" or item.get("计算状态") == "成功")
    rate = round(success / total * 100, 2) if total else 0
    if rate >= 95:
        level = "优秀"
    elif rate >= 85:
        level = "可用"
    elif rate > 0:
        level = "降级"
    else:
        level = "暂停"
    return {
        "状态": "完成",
        "来源": str(INDICATOR_LATEST_PATH),
        "数据健康度": {
            "股票数量": total,
            "指标成功数量": success,
            "成功率": rate,
            "健康等级": level,
            "历史行情降级说明": history.get("降级说明", ""),
        },
    }


def find_quote(stock: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any] | None:
    target = normalize_code(str(stock.get("代码") or stock.get("code") or ""))
    for row in snapshot.get("行情", []):
        if normalize_code(str(row.get("代码") or "")) == target:
            return row
    return None


def find_indicator(stock: dict[str, Any]) -> dict[str, Any] | None:
    target = normalize_code(str(stock.get("代码") or stock.get("code") or ""))
    indicators = load_json(INDICATOR_LATEST_PATH, {}) or {}
    for row in indicators.get("技术指标", []):
        if normalize_code(str(row.get("代码") or "")) == target:
            return row
    return None


def find_candidate(stock: dict[str, Any]) -> dict[str, Any] | None:
    target = normalize_code(str(stock.get("代码") or stock.get("code") or ""))
    data = load_json(CANDIDATE_POOL_LATEST_PATH, {}) or {}
    for layer, items in data.get("候选池", {}).items():
        for row in items:
            if normalize_code(str(row.get("代码") or "")) == target:
                return {**row, "候选层级": layer}
    for row in daily_ai_report_stocks():
        if normalize_code(str(row.get("代码") or "")) == target:
            score = to_float(row.get("调整分"))
            mapped_score = round(score * 20, 2) if score is not None and score <= 5 else score
            return {
                **row,
                "候选层级": "AI日报推荐/观察",
                "系统评分": mapped_score,
                "依据": [str(row.get("analysis_text") or "最新AI日报推荐/观察股票")[:300]],
                "风险": ["AI日报候选仍需结合公告、财报、行业和行情数据继续核验"],
            }
    return None


def find_risk_observation_row(stock: dict[str, Any]) -> dict[str, Any] | None:
    target = normalize_code(str(stock.get("代码") or stock.get("code") or ""))
    data = load_json(RISK_OBSERVATION_PANEL_LATEST_PATH, {}) or {}
    for row in data.get("逐股结果", []):
        if normalize_code(str(row.get("代码") or "")) != target:
            continue
        lines = row.get("观察线") if isinstance(row.get("观察线"), dict) else {}
        return {
            **row,
            "最新价": lines.get("现价"),
            "收盘价": lines.get("现价"),
            "观察承接": lines.get("承接观察线"),
            "风险观察线": lines.get("风险观察线"),
            "强度确认位": lines.get("强度确认线"),
            "行业": row.get("行业"),
            "来源": str(RISK_OBSERVATION_PANEL_LATEST_PATH),
        }
    return None


def build_recognition(text: str) -> dict[str, Any]:
    stock = find_stock(text)
    return {
        "状态": "完成" if stock else "未识别",
        "输入": text,
        "识别结果": stock,
        "重点关注池数量": len(focus_stocks()),
        "合并股票池数量": len(merged_stocks()),
        "说明": "用于企业微信文字或语音转文字后的股票名称确认。",
    }


HELP_KEYWORDS = ("帮助", "怎么用", "使用说明", "能问什么", "你会什么", "股票帮助", "指令", "菜单")
DAILY_RECOMMENDATION_KEYWORDS = (
    "今日推荐",
    "今天推荐",
    "每日推荐",
    "今天有什么值得看",
    "今天看什么",
    "有什么值得看",
    "今日观察",
    "推荐股票",
    "股票推荐",
    "推荐的股票",
    "有什么推荐的股票",
    "你有什么推荐的股票",
    "有没有推荐的股票",
    "有推荐的股票吗",
    "有什么股票推荐",
    "推荐一下股票",
    "推荐几只股票",
    "今天有什么推荐",
    "今天有什么推荐股票",
    "现在有什么推荐",
    "查看推荐",
    "今日报告",
)
SYSTEM_STATUS_KEYWORDS = ("股票系统状态", "系统状态", "交付状态", "验收状态", "现在能不能用")
MODEL_HEALTH_KEYWORDS = ("模型健康", "模型状态", "ollama状态", "Ollama状态")
PUBLIC_CALLBACK_KEYWORDS = ("公网状态", "公网回调", "回调状态", "隧道状态", "手机外网")
SINGLE_STOCK_ANALYSIS_KEYWORDS = (
    "分析",
    "看看",
    "看一下",
    "怎么样",
    "走势",
    "风险",
    "位置",
    "参考位置",
    "买点",
    "卖点",
    "压力位",
    "支撑位",
)
CONTEXT_PRONOUN_KEYWORDS = ("这个", "这只", "它", "该股", "这票", "这支", "刚才那只")


def is_help_question(question: str) -> bool:
    text = str(question or "").strip()
    return bool(text) and any(keyword in text for keyword in HELP_KEYWORDS)


def is_daily_recommendation_question(question: str) -> bool:
    text = str(question or "").replace(" ", "").strip()
    return bool(text) and any(keyword in text for keyword in DAILY_RECOMMENDATION_KEYWORDS)


def is_system_status_question(question: str) -> bool:
    text = str(question or "").strip()
    return bool(text) and any(keyword in text for keyword in SYSTEM_STATUS_KEYWORDS)


def is_model_health_question(question: str) -> bool:
    text = str(question or "").strip()
    return bool(text) and any(keyword in text for keyword in MODEL_HEALTH_KEYWORDS)


def is_public_callback_question(question: str) -> bool:
    text = str(question or "").strip()
    return bool(text) and any(keyword in text for keyword in PUBLIC_CALLBACK_KEYWORDS)


def is_single_stock_analysis_question(question: str) -> bool:
    text = str(question or "").replace(" ", "").strip()
    return bool(text) and any(keyword in text for keyword in SINGLE_STOCK_ANALYSIS_KEYWORDS)


def uses_recent_context_pronoun(question: str) -> bool:
    text = str(question or "").replace(" ", "").strip()
    return bool(text) and any(keyword in text for keyword in CONTEXT_PRONOUN_KEYWORDS)


def build_usage_help() -> dict[str, Any]:
    reply = "\n".join([
        "杰哥，股票研究助手可以这样用：",
        "",
        "1. 看单只股票：",
        "分析天齐锂业 / 分析300750 / 天齐锂业怎么样",
        "",
        "2. 看持仓诊断：",
        "我持仓天齐锂业还能不能拿 / 天齐锂业要不要离场观望",
        "",
        "3. 看今日结果：",
        "今日推荐 / 今天有什么值得看 / 今日观察",
        "",
        "4. 看系统状态：",
        "股票系统状态 / 模型健康 / 公网状态",
        "",
        "前台只给结论、策略、位置、风险和下一步；后台报告会保留详细分析。",
        "安全边界：只做研究参考，不连接券商接口，不自动交易。",
    ])
    return {
        "状态": "完成",
        "类型": "使用帮助",
        "回复": reply,
        "企业微信回复": reply,
        "安全边界": load_config().get("安全边界", {}),
    }


def build_daily_recommendation_reply() -> dict[str, Any]:
    if not WECHAT_PUSH_DRAFT_LATEST_PATH.exists():
        reply = "\n".join([
            "杰哥，今日推荐草案还没有生成。",
            "可以先运行股票系统日常一键流程，生成L5、AI报告和企微推送草案后再查看。",
            f"预期位置：{WECHAT_PUSH_DRAFT_LATEST_PATH}",
            "说明：本消息仅为研究辅助，不构成投资建议，不作为买卖指令。",
        ])
        return {
            "状态": "未生成",
            "类型": "今日推荐",
            "回复": reply,
            "企业微信回复": reply,
            "推送草案": str(WECHAT_PUSH_DRAFT_LATEST_PATH),
        }
    text = WECHAT_PUSH_DRAFT_LATEST_PATH.read_text(encoding="utf-8-sig", errors="replace").strip()
    # 企业微信长文本可读性优先，超过长度时保留头部摘要和完整文件路径。
    limit = 3200
    if len(text) > limit:
        text = text[:limit].rstrip() + "\n\n（内容较长，已截取前半部分。完整报告见下方文件。）"
    if "完整报告" not in text:
        text += f"\n\n完整报告：\n{STANDARD_REPORT_V2_DIR / 'AI分析报告_最新.md'}"
    return {
        "状态": "完成",
        "类型": "今日推荐",
        "回复": text,
        "企业微信回复": text,
        "推送草案": str(WECHAT_PUSH_DRAFT_LATEST_PATH),
        "安全边界": load_config().get("安全边界", {}),
    }


def parse_daily_push_sections(text: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    normalized = strip_markdown_for_plain_text(text)
    parts = normalized.split("可观察股票：", 1)
    recommend_text = parts[0]
    observe_text = parts[1] if len(parts) > 1 else ""
    pattern = re.compile(r"(?m)^\d+\.\s*([^：\n]+)：([^\n]+)")

    def collect(section: str) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for match in pattern.finditer(section):
            label = match.group(1).strip()
            level = match.group(2).strip()
            name_match = re.match(r"(.+?)\(([^)]+)\)", label)
            if name_match:
                name = name_match.group(1).strip()
                code = name_match.group(2).strip()
            else:
                name = label
                code = ""
            rows.append({"名称": name, "代码": code, "等级": level})
        return rows

    return collect(recommend_text), collect(observe_text)


def parse_daily_stock_blocks(text: str) -> dict[str, dict[str, str]]:
    """从企微推送草案抽取前台可读的策略、参考位和风险，供专家入口复用，避免退化成空泛总览。"""
    normalized = str(text or "")
    pattern = re.compile(
        r"(?ms)^\d+\.\s*(?:\[)?(.+?)\(([^)]+)\)(?:\]\([^)]+\))?：([^\n]+)"
        r".*?【建议策略】：\s*(.*?)\n\s*\n【参考价位】：\s*(.*?)\n\s*\n【主要风险】：\s*(.*?)(?=\n\s*\d+\.\s*(?:\[)?.+?\([^)]+\)(?:\]\([^)]+\))?：|\n\s*可观察股票：|\n\s*完整报告：|\Z)"
    )
    blocks: dict[str, dict[str, str]] = {}
    for match in pattern.finditer(normalized):
        name = match.group(1).strip()
        blocks[name] = {
            "名称": name,
            "代码": match.group(2).strip(),
            "等级": match.group(3).strip(),
            "建议策略": re.sub(r"\s+", " ", match.group(4)).strip(" 。；，,"),
            "参考价位": re.sub(r"\s+", " ", match.group(5)).strip(" 。；，,"),
            "主要风险": re.sub(r"\s+", " ", match.group(6)).strip(" 。；，,"),
        }
    return blocks


def strip_markdown_for_plain_text(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", str(text or ""))


def stock_link_label(name: str, code: str) -> str:
    label = f"{name}({code})" if code else name
    ask = urllib.parse.quote(f"分析{name}", safe="")
    base_url = PUBLIC_BASE_URL or "http://43.167.210.211"
    return f"[{label}]({base_url}{PUBLIC_BOT_MESSAGE_PATH}?ask={ask})"


def stars_from_level_text(level: str) -> str:
    text = str(level or "")
    star_match = re.search(r"(⭐+)", text)
    if star_match:
        return star_match.group(1)
    if "重点" in text:
        return "⭐⭐⭐⭐⭐"
    if "常规" in text:
        return "⭐⭐⭐⭐"
    if "观察" in text:
        return "⭐⭐⭐"
    return ""


def linked_stock_lines(rows: list[dict[str, str]], limit: int = 6) -> list[str]:
    lines: list[str] = []
    for index, item in enumerate(rows[:limit], start=1):
        label = stock_link_label(item.get("名称", ""), item.get("代码", ""))
        stars = stars_from_level_text(item.get("等级", ""))
        level = re.sub(r"⭐+", "", str(item.get("等级", ""))).strip(" 。；，,")
        suffix = f"{level}{stars}" if level or stars else ""
        lines.append(f"{index}. {label}：{suffix}".rstrip("："))
    return lines


def plain_stock_lines(rows: list[dict[str, str]], limit: int = 6) -> list[str]:
    """企业微信手机端优先的纯文本股票列表，避免 Markdown 链接原文污染气泡。"""
    lines: list[str] = []
    for index, item in enumerate(rows[:limit], start=1):
        name = str(item.get("名称", "")).strip()
        code = str(item.get("代码", "")).strip()
        label = f"{name}({code})" if code else name
        stars = stars_from_level_text(item.get("等级", ""))
        level = re.sub(r"⭐+", "", str(item.get("等级", ""))).strip(" 。；，,")
        suffix = f"{level}{stars}" if level or stars else ""
        lines.append(f"{index}. {label}：{suffix}".rstrip("："))
    return lines


def short_sentence(text: str, limit: int = 46) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip(" 。；，,")
    replacements = {
        "技术面及资金放量率": "走势结构和成交活跃度",
        "技术面分稳健": "走势结构较稳",
        "技术结构得分突出": "走势结构较强",
        "技术结构较强": "走势结构较强",
        "技术结构": "走势结构",
        "技术面": "走势结构",
        "指标": "信号",
        "调整分": "系统得分",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit - 1].rstrip(" ，,。；") + "…"


def ai_row_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("名称") or "").strip(): item for item in rows if str(item.get("名称") or "").strip()}


def format_front_summary_line(index: int, item: dict[str, str], ai_by_name: dict[str, dict[str, Any]], blocks: dict[str, dict[str, str]]) -> list[str]:
    """生成专家线手机摘要：看方向和逻辑，不逐只展开助手线价位细节。"""
    name = str(item.get("名称") or "").strip()
    code = str(item.get("代码") or "").strip()
    level = str(item.get("等级") or "").strip()
    ai_item = ai_by_name.get(name, {})
    block = blocks.get(name, {})
    industry = str(ai_item.get("行业") or "待核验").strip()
    score_value = ai_item.get("调整分")
    try:
        score = f"{float(score_value):.2f}"
    except Exception:
        score = "-"
    strategy = short_sentence(block.get("建议策略") or ai_item.get("研究小结") or ai_item.get("analysis_text") or "系统给出阶段性研究关注信号，需继续跟踪验证。", 58)
    return [f"{index}、{name}({code})：{level}；{industry}；得分{score}；逻辑：{strategy}。"]


def compact_finance_review_text(text: str) -> str:
    cleaned = re.sub(r"\*\*", "", str(text or "")).strip()
    cleaned = re.sub(r"\n\s*-\s*", " ", cleaned)
    match = re.search(r"6[\.\、]\s*复核结论\s*(.+)", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(1).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace("建议结合更多基本面分析谨慎决策", "需结合更多基本面材料人工复核")
    cleaned = cleaned.replace("建议持续跟踪并谨慎决策", "需持续跟踪并继续人工复核")
    cleaned = cleaned.replace("需谨慎对待", "需人工核验")
    cleaned = cleaned.replace("谨慎对待", "人工核验")
    cleaned = cleaned.replace("谨慎决策", "人工复核")
    cleaned = cleaned.replace("做出决策", "作为人工复核依据")
    cleaned = cleaned.replace("作出决策", "作为人工复核依据")
    cleaned = cleaned.replace("建议持续跟踪", "后续需持续跟踪")
    cleaned = cleaned.replace("投资价值", "研究关注价值").replace("买卖建议", "交易动作建议")
    cleaned = cleaned.replace("目标价预测", "价格预测")
    if not cleaned:
        return "暂无可读复核结论，等待下一次金融专项复核。"
    return cleaned[:180] + ("..." if len(cleaned) > 180 else "")


def build_finance_review_summary() -> tuple[str, dict[str, Any]]:
    index = load_json(FINANCE_REVIEW_INDEX_LATEST_PATH, {}) or {}
    latest = load_json(FINANCE_REVIEW_LATEST_PATH, {}) or {}
    summary = index.get("摘要", {}) if isinstance(index.get("摘要"), dict) else {}
    stock = latest.get("股票", {}) if isinstance(latest.get("股票"), dict) else {}
    main_result = latest.get("主模型结果", {}) if isinstance(latest.get("主模型结果"), dict) else {}
    report_count = summary.get("有效报告数", 0) or 0
    stock_count = summary.get("覆盖股票数", 0) or 0
    success_count = summary.get("主模型成功数", 0) or 0
    latest_name = stock.get("名称") or "暂无"
    latest_code = stock.get("展示代码") or stock.get("代码") or "-"
    latest_time = latest.get("生成时间") or index.get("生成时间") or "未生成"
    conclusion = compact_finance_review_text(main_result.get("text", ""))
    if not latest and not index:
        text = "金融专项复核：尚未形成可引用复核结果；当前专家结论只解释行情、分层和证据缺口，不提高推荐强度。"
    else:
        text = (
            f"金融专项复核：已有{report_count}份有效复核，覆盖{stock_count}只股票，"
            f"主模型成功{success_count}次；最近复核为{latest_name}({latest_code})，时间{latest_time}。"
            f"复核提醒：{conclusion}"
        )
    return text, {
        "索引摘要": summary,
        "最近复核股票": stock,
        "最近复核时间": latest_time,
        "最近复核结论摘要": conclusion,
    }


def build_expert_overview_reply(question: str = "") -> dict[str, Any]:
    now = datetime.now()
    ai_report = load_json(AI_DAILY_REPORT_JSON_PATH, {}) or {}
    industry_report = load_json(INDUSTRY_PROSPERITY_LATEST_PATH, {}) or {}
    credibility = load_json(REPORT_CREDIBILITY_LATEST_PATH, {}) or {}
    evidence = load_json(EVIDENCE_OVERVIEW_LATEST_PATH, {}) or {}
    finance_review_text, finance_review_record = build_finance_review_summary()
    daily_text = WECHAT_PUSH_DRAFT_LATEST_PATH.read_text(encoding="utf-8-sig", errors="replace") if WECHAT_PUSH_DRAFT_LATEST_PATH.exists() else ""
    recommended, observed = parse_daily_push_sections(daily_text)
    daily_blocks = parse_daily_stock_blocks(daily_text)
    ai_rows = ai_report.get("分析结果", []) if isinstance(ai_report.get("分析结果"), list) else []
    ai_by_name = ai_row_map(ai_rows)
    top_industries = industry_report.get("行业景气结论", []) if isinstance(industry_report.get("行业景气结论"), list) else []
    top_industries = top_industries[:5]
    industry_names = "、".join(str(item.get("行业") or "-") for item in top_industries[:3]) or "待补充"
    summary_rows = (recommended[:4] + observed[:1]) if recommended else observed[:5]
    summary_lines: list[str] = []
    for index, item in enumerate(summary_rows, start=1):
        summary_lines.extend(format_front_summary_line(index, item, ai_by_name, daily_blocks))
    if not summary_lines:
        summary_lines.append("暂无达标推荐；先观察行业方向和风险线变化。")
    obs_names = "\n".join(plain_stock_lines(observed[:5])) or "暂无观察名单"
    rec_industries: dict[str, int] = {}
    for item in ai_rows:
        name = str(item.get("名称") or "")
        if any(row.get("名称") == name for row in recommended):
            industry = str(item.get("行业") or "待补充")
            rec_industries[industry] = rec_industries.get(industry, 0) + 1
    main_focus = sorted(rec_industries.items(), key=lambda pair: pair[1], reverse=True)
    focus_text = "、".join(f"{name}{count}只" for name, count in main_focus[:3]) or f"{industry_names}等方向"
    market_state = "积极研究、谨慎验证"
    if not recommended and not observed:
        market_state = "等待为主"
    elif len(recommended) <= 2:
        market_state = "谨慎观察、少量研究"
    elif len(recommended) >= 4:
        market_state = "结构性积极研究"
    credibility_avg = credibility.get("平均可信度分", "-")
    gap_items = credibility.get("缺口优先级", []) if isinstance(credibility.get("缺口优先级"), list) else []
    gap_text = "；".join(
        f"{item.get('缺口')}影响{item.get('影响股票数')}只，{item.get('建议')}"
        for item in gap_items[:3]
    ) or "公司概况、事件风险和行业景气仍需继续人工核验。"
    chain_summary = evidence.get("链路汇总", {}) if isinstance(evidence.get("链路汇总"), dict) else {}
    chain_text = "；".join(
        f"{name}{value.get('状态', '待核验')}({value.get('未通过数量', 0)}项未通过)"
        for name, value in chain_summary.items()
        if isinstance(value, dict)
    ) or "证据核验链路等待人工补证。"
    industry_lines = []
    for item in top_industries[:3]:
        industry_lines.append(f"- {item.get('行业', '-')}：{item.get('景气状态', '待核验')}")
    if not industry_lines:
        industry_lines.append("- 行业景气结论未生成，需先刷新L6行业主题观察池。")
    data_date = str(ai_report.get("数据日期") or "未知")
    if re.match(r"^\d{4}-\d{2}-\d{2}$", data_date):
        title_date = data_date.replace("-", "年", 1).replace("-", "月", 1) + "日"
    else:
        title_date = data_date
    base_url = PUBLIC_BASE_URL or "http://43.167.210.211"
    detail_url = public_stock_url(f"{PUBLIC_BOT_MESSAGE_PATH}?view=stock-reco")
    reply = "\n".join([
        f"【{title_date}股票分析报告】",
        "",
        "完整图文报告：",
        detail_url,
        "",
        "说明：进入图文报告后可点股票名称查看单股详情；也可直接回复“分析 摩尔线程”。",
        "",
        "今日摘要：",
        *summary_lines,
        "",
        f"整体结论：重点关注{len(recommended)}只，观察{len(observed)}只；{market_state}。",
        "",
        "观察股票：",
        obs_names,
        "",
        "主要方向：",
        *industry_lines,
        "",
        "下一步：先看重点关注股能否守住各自风险线，再看成交量是否继续活跃；观察股只有转强后才提高研究优先级。",
        "",
        "说明：本消息为研究摘要，仅供人工查看，不构成投资建议，不作为买卖指令。",
    ])
    record = {
        "名称": "股票专家市场总览",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "问题": question,
        "数据日期": ai_report.get("数据日期"),
        "市场状态": market_state,
        "推荐数量": len(recommended),
        "观察数量": len(observed),
        "强势方向": top_industries[:5],
        "重点关注名单": recommended,
        "可观察股票": observed,
        "报告平均可信度": credibility_avg,
        "证据缺口": gap_items[:5],
        "金融专项复核": finance_review_record,
        "回复": reply,
        "安全边界": load_config().get("安全边界", {}),
    }
    stamp = now.strftime("%Y%m%d_%H%M%S")
    write_json(EXPERT_OVERVIEW_DIR / f"股票专家市场总览_{stamp}.json", record)
    write_json(EXPERT_OVERVIEW_JSON_LATEST_PATH, record)
    write_text(EXPERT_OVERVIEW_DIR / f"股票专家市场总览_{stamp}.md", reply)
    write_text(EXPERT_OVERVIEW_MD_LATEST_PATH, reply)
    return {
        "状态": "完成",
        "类型": "专家市场总览",
        "问题": question,
        "回复": reply,
        "企业微信回复": reply,
        "专家总览": str(EXPERT_OVERVIEW_MD_LATEST_PATH),
        "安全边界": load_config().get("安全边界", {}),
    }


def path_time(path: Path) -> str:
    if not path.exists():
        return "未生成"
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def build_system_status_reply() -> dict[str, Any]:
    result = run_script("验证股票系统完全交付最终验收.py", timeout=120)
    ok = result.get("返回码") == 0 and "完全交付通过" in str(result.get("标准输出"))
    reply = "\n".join([
        "杰哥，股票分析系统当前状态：",
        "",
        f"总体结论：{'可完整使用，最终验收通过' if ok else '需要查看验收日志，可能存在异常'}。",
        "可用能力：单股查询、持仓诊断、今日推荐、L8X-L7-L6-L5分层、AI报告、企微桥接。",
        "安全边界：不连接券商接口，不自动交易。",
        "",
        f"最终验收报告：{FINAL_ACCEPTANCE_LATEST_PATH}",
        f"报告更新时间：{path_time(FINAL_ACCEPTANCE_LATEST_PATH)}",
    ])
    return {
        "状态": "完成" if ok else "需检查",
        "类型": "股票系统状态",
        "回复": reply,
        "企业微信回复": reply,
        "验收结果": result,
        "安全边界": load_config().get("安全边界", {}),
    }


def build_model_health_reply() -> dict[str, Any]:
    result = run_script("生成股票系统模型健康检查.py", timeout=120)
    ok = result.get("返回码") == 0
    reply = "\n".join([
        "杰哥，股票系统模型健康检查完成：",
        "",
        f"总体结论：{'主流程模型可用' if ok else '模型健康检查异常，需要查看日志'}。",
        "主流程模型：qwen3:14b、deepseek-r1:32b、qwen2.5:7b。",
        "专业模型：金融复核、向量检索、交叉评审模型作为后续增强能力，不影响当前日常使用。",
        "",
        f"模型健康报告：{MODEL_HEALTH_LATEST_PATH}",
        f"报告更新时间：{path_time(MODEL_HEALTH_LATEST_PATH)}",
    ])
    return {
        "状态": "完成" if ok else "需检查",
        "类型": "模型健康",
        "回复": reply,
        "企业微信回复": reply,
        "检查结果": result,
        "安全边界": load_config().get("安全边界", {}),
    }


def build_public_callback_reply() -> dict[str, Any]:
    if not PUBLIC_CALLBACK_STATUS_SCRIPT.exists():
        reply = f"杰哥，公网回调状态脚本不存在：{PUBLIC_CALLBACK_STATUS_SCRIPT}"
        return {"状态": "未生成", "类型": "公网状态", "回复": reply, "企业微信回复": reply}
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PUBLIC_CALLBACK_STATUS_SCRIPT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    stdout = result.stdout.strip()
    ok = result.returncode == 0 and '"status":  "ready"' in stdout and '"public_callback_ok":  true' in stdout
    reply = "\n".join([
        "杰哥，股票系统公网回调状态：",
        "",
        f"总体结论：{'ready，公网回调可用' if ok else '需要检查公网隧道或本地桥接'}。",
        "本地桥接：检查127.0.0.1:19302。",
        "公网回调：检查云端转发到本机桥接。",
        "",
        "说明：这是状态检查，不会发送企业微信消息，不会触发交易。",
    ])
    return {
        "状态": "完成" if ok else "需检查",
        "类型": "公网状态",
        "回复": reply,
        "企业微信回复": reply,
        "检查输出": stdout,
        "返回码": result.returncode,
        "安全边界": load_config().get("安全边界", {}),
    }


def build_technical_analysis(text: str, refresh: bool = False) -> dict[str, Any]:
    if contains_trade_action(text):
        return build_trade_action_refusal(text)
    stock = find_stock(text)
    if not stock:
        return {
            "状态": "未识别",
            "输入": text,
            "回复": "没有识别到股票名称或代码，无法生成技术分析。",
        }
    snapshot = latest_quote_snapshot(refresh=refresh)
    quote = find_quote(stock, snapshot)
    indicator = find_indicator(stock)
    decision = score_quote(quote)
    return {
        "状态": "完成",
        "输入": text,
        "股票": stock,
        "行情": quote,
        "技术指标": indicator,
        "规则判断": decision,
        "数据健康度": latest_data_health().get("数据健康度", {}),
        "定位声明": "这是研究助手技术分析结果，不是交易指令，不自动下单。",
    }


def score_quote(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        score = 50
        layer = "L6轻度关注"
        return {"评分": score, "分层": layer, "研究信号": build_research_signal(score, layer, ["需要核实代码和数据源返回。"]), "依据": ["暂无公开行情，保持观察。"], "风险": ["需要核实代码和数据源返回。"]}
    score = 50
    basis: list[str] = []
    risks: list[str] = []
    pct = to_float(row.get("涨跌幅"))
    turnover = to_float(row.get("换手率"))
    volume_ratio = to_float(row.get("量比"))
    pe = to_float(row.get("市盈率"))

    if pct is not None:
        if 0 <= pct <= 4:
            score += 8
            basis.append(f"涨跌幅{pct}%，处于可观察强度。")
        elif pct > 7:
            score -= 6
            risks.append(f"涨跌幅{pct}%，短线追高风险升高。")
        elif pct < -5:
            score -= 8
            risks.append(f"涨跌幅{pct}%，需确认是否有利空或趋势破位。")
        else:
            basis.append(f"涨跌幅{pct}%，需结合K线位置判断。")
    if volume_ratio is not None:
        if 1.1 <= volume_ratio <= 2.5:
            score += 6
            basis.append(f"量比{volume_ratio}，活跃度改善。")
        elif volume_ratio > 4:
            score -= 4
            risks.append(f"量比{volume_ratio}，异动较强，需防冲高回落。")
    if turnover is not None:
        if 1 <= turnover <= 8:
            score += 4
            basis.append(f"换手率{turnover}%，交易活跃度适中。")
        elif turnover > 15:
            score -= 4
            risks.append(f"换手率{turnover}%，筹码波动较大。")
    if pe is not None and pe > 90:
        score -= 4
        risks.append(f"市盈率{pe}，估值弹性和回撤风险都要单独核实。")

    if score >= 75:
        layer = "L4观察仓候选"
    elif score >= 62:
        layer = "L5深度研究"
    elif score >= 45:
        layer = "L6轻度关注"
    else:
        layer = "L7系统过滤"
    score = max(0, min(100, score))
    risks = risks or ["未发现单日行情层面的突出风险，但仍需结合公告、财务和K线。"]
    return {"评分": score, "分层": layer, "研究信号": build_research_signal(score, layer, risks), "依据": basis or ["公开行情未出现明显强弱信号。"], "风险": risks}


def merge_candidate_decision(decision: dict[str, Any], candidate: dict[str, Any] | None) -> dict[str, Any]:
    if not candidate:
        return decision
    candidate_score = to_float(candidate.get("系统评分"))
    candidate_layer = candidate.get("候选层级") or candidate.get("层级")
    if candidate_score is None or not candidate_layer:
        return decision
    basis = candidate.get("依据") or decision.get("依据", [])
    risks = candidate.get("风险") or decision.get("风险", [])
    return {
        "评分": candidate_score,
        "分层": candidate_layer,
        "研究信号": build_research_signal(candidate_score, str(candidate_layer), risks),
        "依据": basis,
        "风险": risks,
        "单日行情判断": decision,
    }


def build_research_signal(score: float, layer: str, risks: list[str]) -> dict[str, Any]:
    layer_text = str(layer or "")
    risk_text = "；".join(str(item) for item in risks)
    major_risk_words = ["数据缺失", "K线不足", "破位", "利空", "追高", "回撤", "动能偏弱", "无法", "失败"]
    has_major_risk = any(word in risk_text for word in major_risk_words)
    if score >= 95 and not has_major_risk:
        strength = 5.0
        marker = "⭐⭐⭐⭐⭐+S"
        direction = "买入研究信号"
        note = "顶级机会研究信号，极致条件罕见，一旦满足必须高亮复核；仍需人工确认，不构成买入指令。"
        color_name = "金色"
        color_value = "#FFD700"
        wecom_color = "warning"
        level_name = "S级顶级机会"
    elif score >= 90:
        strength = 5.0
        marker = "⭐⭐⭐⭐⭐"
        direction = "买入研究信号"
        note = "极强机会研究信号，可列入最高优先级复核；仍需人工确认，不构成买入指令。"
        color_name = "金色"
        color_value = "#FFD700"
        wecom_color = "warning"
        level_name = "极强机会"
    elif score >= 85:
        strength = 4.5
        marker = "⭐⭐⭐⭐⭐"
        direction = "买入研究信号"
        note = "强机会研究信号，接近五星，适合重点研究确认条件；仍需人工确认，不构成买入指令。"
        color_name = "金色"
        color_value = "#FFD700"
        wecom_color = "warning"
        level_name = "强机会"
    elif score >= 80:
        strength = 4.0
        marker = "⭐⭐⭐⭐"
        direction = "买入研究信号"
        note = "较强机会研究信号，可作为重点研究对象；仍需人工确认，不构成买入指令。"
        color_name = "金色"
        color_value = "#FFD700"
        wecom_color = "warning"
        level_name = "较强机会"
    elif score >= 70 or layer_text.startswith("L4"):
        strength = 3.0
        marker = "⭐⭐⭐"
        direction = "买入研究信号"
        note = "中等机会研究信号，适合继续跟踪关键确认条件；不构成买入指令。"
        color_name = "金色"
        color_value = "#FFD700"
        wecom_color = "warning"
        level_name = "中等机会"
    elif score >= 62 or layer_text.startswith("L5"):
        strength = 2.0
        marker = "⭐⭐"
        direction = "买入研究信号"
        note = "初步机会研究信号，具备继续深度研究价值；不构成买入指令。"
        color_name = "金色"
        color_value = "#FFD700"
        wecom_color = "warning"
        level_name = "初步机会"
    elif score >= 55:
        strength = 1.0
        marker = "⭐"
        direction = "机会观察信号"
        note = "轻微信号，仅提示观察，不构成买入指令。"
        color_name = "金色"
        color_value = "#FFD700"
        wecom_color = "warning"
        level_name = "轻微机会"
    elif score <= 5:
        strength = 5.0
        marker = "⭐⭐⭐⭐⭐+S"
        direction = "卖出/退出研究信号"
        note = "顶级风险退出研究信号，极致风险条件罕见，一旦满足必须高亮复核；不构成卖出指令。"
        color_name = "绿色"
        color_value = "#2E7D32"
        wecom_color = "info"
        level_name = "S级顶级风险"
    elif score <= 15 or layer_text.startswith("L7"):
        strength = 5.0
        marker = "⭐⭐⭐⭐⭐"
        direction = "卖出/退出研究信号"
        note = "强风险退出研究信号，适合最高优先级复核是否退出观察；不构成卖出指令。"
        color_name = "绿色"
        color_value = "#2E7D32"
        wecom_color = "info"
        level_name = "强风险"
    elif score <= 25:
        strength = 4.0
        marker = "⭐⭐⭐⭐"
        direction = "卖出/退出研究信号"
        note = "较强风险退出研究信号，需重点复核弱势或风险来源；不构成卖出指令。"
        color_name = "绿色"
        color_value = "#2E7D32"
        wecom_color = "info"
        level_name = "较强风险"
    elif score <= 35:
        strength = 3.0
        marker = "⭐⭐⭐"
        direction = "卖出/退出研究信号"
        note = "中等风险观察信号，需要复核趋势、公告和数据源；不构成卖出指令。"
        color_name = "绿色"
        color_value = "#2E7D32"
        wecom_color = "info"
        level_name = "中等风险"
    elif score <= 44 or any(word in risk_text for word in ["破位", "利空", "追高", "回撤"]):
        strength = 2.0
        marker = "⭐⭐"
        direction = "卖出/退出研究信号"
        note = "存在需要重点核实的风险点；不构成卖出指令。"
        color_name = "绿色"
        color_value = "#2E7D32"
        wecom_color = "info"
        level_name = "初步风险"
    elif score <= 49:
        strength = 1.0
        marker = "⭐"
        direction = "风险观察信号"
        note = "轻微风险信号，仅提示复核，不构成卖出指令。"
        color_name = "绿色"
        color_value = "#2E7D32"
        wecom_color = "info"
        level_name = "轻微风险"
    else:
        strength = 0.0
        marker = "观察"
        direction = "中性观察"
        note = "当前未形成明确买入或卖出研究信号，只保留观察。"
        color_name = "不标色"
        color_value = "#374151"
        wecom_color = "comment"
        level_name = "中性观察"
    is_s_level = str(marker).endswith("+S")
    if marker == "观察":
        display_marker = marker
        wecom_marker = marker
    elif color_name in {"金色", "红色", "绿色"}:
        star_count = max(1, min(5, int(math.ceil(float(strength)))))
        display_marker = "⭐" * star_count
        if is_s_level:
            display_marker += "+S"
        wecom_marker = display_marker
    else:
        display_marker = marker
        wecom_marker = display_marker
    return {
        "星级": strength,
        "标记": display_marker,
        "企业微信标记": wecom_marker,
        "企业微信彩色标记_停用": f'<font color="{wecom_color}">{display_marker}</font>' if color_name in {"金色", "红色", "绿色"} else display_marker,
        "企业微信文本标记": ("🟡 " if color_name in {"金色", "红色"} else "🟢 " if color_name == "绿色" else "") + display_marker,
        "方向": direction,
        "说明": note,
        "强度": f"{strength:g}/5",
        "级别": level_name,
        "颜色": color_name,
        "色值": color_value,
        "企业微信颜色": wecom_color,
        "是否S级": is_s_level,
        "是否半星": strength % 1 != 0,
        "显示星数": 0 if marker == "观察" else max(1, min(5, int(math.ceil(float(strength))))),
    }


def svg_text(text: Any) -> str:
    return html.escape(str(text if text is not None else ""), quote=True)


def svg_wrapped_lines(text: str, width: int = 30, max_lines: int = 3) -> list[str]:
    clean = str(text or "").replace("\n", " ").strip()
    if not clean:
        return ["暂无"]
    wrapped = textwrap.wrap(clean, width=width, break_long_words=True, replace_whitespace=False)
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] = wrapped[-1].rstrip("，。；、 ") + "..."
    return wrapped


def svg_star_bar(signal: dict[str, Any], x: int, y: int) -> str:
    strength = float(signal.get("显示星数") or signal.get("星级") or 0)
    direction = str(signal.get("方向") or "")
    is_risk = "卖出" in direction or "风险" in direction
    active_color = "#2E7D32" if is_risk else "#FFD700"
    inactive_color = "#334155"
    symbol = "⭐"
    parts: list[str] = []
    size = 38
    gap = 42
    for index in range(5):
        sx = x + index * gap
        star_id = f"half-star-{index}"
        if strength >= index + 1:
            parts.append(f'<text x="{sx}" y="{y}" font-size="{size}" fill="{active_color}" font-family="Microsoft YaHei, Arial">{symbol}</text>')
        elif strength > index:
            parts.append(f'<text x="{sx}" y="{y}" font-size="{size}" fill="{inactive_color}" font-family="Microsoft YaHei, Arial">{symbol}</text>')
            parts.append(f'<clipPath id="{star_id}"><rect x="{sx}" y="{y - 34}" width="19" height="42"/></clipPath>')
            parts.append(f'<text x="{sx}" y="{y}" font-size="{size}" fill="{active_color}" font-family="Microsoft YaHei, Arial" clip-path="url(#{star_id})">{symbol}</text>')
        else:
            parts.append(f'<text x="{sx}" y="{y}" font-size="{size}" fill="{inactive_color}" font-family="Microsoft YaHei, Arial">{symbol}</text>')
    if signal.get("是否S级"):
        parts.append(f'<text x="{x + 218}" y="{y - 2}" font-size="24" fill="#FFD700" font-weight="800" font-family="Microsoft YaHei, Arial">+S</text>')
    return "\n".join(parts)


def build_stock_card_svg(stock: dict[str, Any], quote: dict[str, Any] | None, decision: dict[str, Any]) -> str:
    signal = decision.get("研究信号", {})
    name = stock.get("名称") or stock.get("name") or stock.get("代码") or stock.get("code")
    code = stock.get("代码") or stock.get("code")
    quote = quote or {}
    price = format_price(quote_latest_price(quote))
    pct = quote.get("涨跌幅", "-")
    amount = quote.get("成交额", "-")
    industry = quote.get("行业", "-")
    layer = decision.get("分层", "-")
    score = decision.get("评分", "-")
    color = signal.get("色值", "#FFD700")
    direction = signal.get("方向", "中性观察")
    level = signal.get("级别", "")
    basis = "；".join(str(item) for item in decision.get("依据", [])[:3])
    risks = "；".join(str(item) for item in decision.get("风险", [])[:2])
    basis_lines = svg_wrapped_lines(basis, width=34, max_lines=3)
    risk_lines = svg_wrapped_lines(risks, width=34, max_lines=2)
    card_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    basis_svg = "\n".join(
        f'<text x="48" y="{332 + i * 28}" font-size="20" fill="#f8fafc" font-weight="700" font-family="Microsoft YaHei, Arial">{svg_text(line)}</text>'
        for i, line in enumerate(basis_lines)
    )
    risk_svg = "\n".join(
        f'<text x="48" y="{464 + i * 26}" font-size="18" fill="#cbd5e1" font-family="Microsoft YaHei, Arial">{svg_text(line)}</text>'
        for i, line in enumerate(risk_lines)
    )
    star_svg = svg_star_bar(signal, 508, 170)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="720" viewBox="0 0 1080 720">
  <rect width="1080" height="720" fill="#070b13"/>
  <rect x="24" y="24" width="1032" height="672" rx="18" fill="#0b111d" stroke="#164e63"/>
  <text x="48" y="86" font-size="42" fill="#f8fafc" font-weight="800" font-family="Microsoft YaHei, Arial">{svg_text(name)}</text>
  <text x="48" y="128" font-size="20" fill="#22d3ee" font-family="Microsoft YaHei, Arial">{svg_text(code)}</text>
  <text x="170" y="128" font-size="20" fill="#94a3b8" font-family="Microsoft YaHei, Arial">{svg_text(card_time)}</text>
  <text x="48" y="180" font-size="42" fill="{color}" font-weight="800" font-family="Microsoft YaHei, Arial">{svg_text(price)}</text>
  <text x="210" y="180" font-size="26" fill="{color}" font-weight="800" font-family="Microsoft YaHei, Arial">{svg_text(pct)}%</text>

  <rect x="48" y="218" width="428" height="132" rx="12" fill="#111827" stroke="#243247"/>
  <text x="70" y="258" font-size="18" fill="#22d3ee" font-family="Microsoft YaHei, Arial">BASIC INFO</text>
  <text x="70" y="294" font-size="18" fill="#cbd5e1" font-family="Microsoft YaHei, Arial">分层：{svg_text(layer)}</text>
  <text x="70" y="326" font-size="18" fill="#cbd5e1" font-family="Microsoft YaHei, Arial">行业：{svg_text(industry)}</text>
  <text x="260" y="294" font-size="18" fill="#cbd5e1" font-family="Microsoft YaHei, Arial">评分：{svg_text(score)}</text>
  <text x="260" y="326" font-size="18" fill="#cbd5e1" font-family="Microsoft YaHei, Arial">成交额：{svg_text(amount)}</text>

  <rect x="500" y="96" width="508" height="254" rx="14" fill="#101827" stroke="#243247"/>
  <text x="528" y="138" font-size="24" fill="#f8fafc" font-weight="800" font-family="Microsoft YaHei, Arial">Research Signal</text>
  {star_svg}
  <text x="528" y="248" font-size="28" fill="{color}" font-weight="800" font-family="Microsoft YaHei, Arial">{svg_text(level)}</text>
  <text x="528" y="288" font-size="20" fill="#dbeafe" font-family="Microsoft YaHei, Arial">{svg_text(direction)} · 强度 {svg_text(signal.get("强度", ""))}</text>
  <text x="528" y="322" font-size="16" fill="#94a3b8" font-family="Microsoft YaHei, Arial">研究助手信号，不构成交易指令</text>

  <rect x="48" y="386" width="960" height="138" rx="14" fill="#0f172a" stroke="#243247"/>
  <text x="48" y="372" font-size="20" fill="#22d3ee" font-family="Microsoft YaHei, Arial">KEY INSIGHTS</text>
  {basis_svg}

  <rect x="48" y="558" width="960" height="94" rx="14" fill="#111827" stroke="#243247"/>
  <text x="70" y="594" font-size="20" fill="#fb7185" font-family="Microsoft YaHei, Arial">RISK NOTES</text>
  {risk_svg}
</svg>"""


def generate_stock_card(stock: dict[str, Any], quote: dict[str, Any] | None, decision: dict[str, Any]) -> dict[str, Any]:
    CARD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    code = str(stock.get("代码") or stock.get("code") or "stock").lower()
    svg_path = CARD_DIR / f"{code}_{stamp}.svg"
    png_path = CARD_DIR / f"{code}_{stamp}.png"
    icon_path = CARD_DIR / f"{code}_{stamp}_signal_icon.png"
    render_json_path = CARD_DIR / f"{code}_{stamp}_png参数.json"
    svg = build_stock_card_svg(stock, quote, decision)
    svg_path.write_text(svg, encoding="utf-8")
    CARD_LATEST_SVG_PATH.write_text(svg, encoding="utf-8")
    signal = decision.get("研究信号", {})
    quote = quote or {}
    latest_price = quote_latest_price(quote)
    confirm_price = round(latest_price * 1.03, 2) if latest_price is not None else "-"
    risk_price = round(latest_price * 0.94, 2) if latest_price is not None else "-"
    pressure_price = round(latest_price * 1.08, 2) if latest_price is not None else "-"
    trend_text = "重点复核" if "强" in str(signal.get("级别", "")) else str(decision.get("分层", "继续观察"))
    render_payload = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "名称": stock.get("名称") or stock.get("name") or stock.get("代码") or stock.get("code"),
        "代码": stock.get("代码") or stock.get("code"),
        "市场": stock.get("市场") or ("上交所" if str(stock.get("代码") or stock.get("code") or "").lower().startswith("sh") else "深交所"),
        "数据源": quote.get("数据源", "公开行情"),
        "最新价": format_price(latest_price),
        "涨跌幅": quote.get("涨跌幅", 0),
        "涨跌额": quote.get("涨跌额", "-"),
        "成交量": quote.get("成交量", "-"),
        "成交额": quote.get("成交额", "-"),
        "最高": format_price(quote_number(quote, "最高", "最高价", "high")),
        "最低": format_price(quote_number(quote, "最低", "最低价", "low")),
        "今开": quote.get("今开", "-"),
        "昨收": quote.get("昨收", "-"),
        "行业": quote.get("行业", "-"),
        "分层": decision.get("分层", "-"),
        "评分": decision.get("评分", "-"),
        "星级": signal.get("显示星数", signal.get("星级", 0)),
        "方向": signal.get("方向", ""),
        "级别": signal.get("级别", ""),
        "强度": signal.get("强度", ""),
        "色值": signal.get("色值", "#FFD700"),
        "是否S级": signal.get("是否S级", False),
        "趋势预测": trend_text,
        "核心洞察": f"{signal.get('级别', '')}，评分{decision.get('评分', '-')}，按研究助手规则进入{decision.get('分层', '观察')}。",
        "主要依据1": str((decision.get("依据") or ["暂无"])[0]),
        "主要依据2": str((decision.get("依据") or ["", "暂无"])[1] if len(decision.get("依据") or []) > 1 else ""),
        "风险提示": "；".join(str(item) for item in decision.get("风险", [])[:2]),
        "观察价": latest_price if latest_price is not None else "-",
        "确认价": confirm_price,
        "风险价": risk_price,
        "压力价": pressure_price,
    }
    write_json(render_json_path, render_payload)
    png_result: dict[str, Any] = {"状态": "未执行", "原因": "PNG渲染脚本不存在"}
    if PNG_RENDERER_PATH.exists():
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(PNG_RENDERER_PATH),
                "-InputJson",
                str(render_json_path),
                "-OutputPng",
                str(png_path),
                "-OutputIcon",
                str(icon_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        png_result = {
            "状态": "完成" if completed.returncode == 0 and png_path.exists() else "失败",
            "返回码": completed.returncode,
            "标准输出": completed.stdout.strip(),
            "标准错误": completed.stderr.strip(),
        }
        if png_path.exists():
            CARD_LATEST_PNG_PATH.write_bytes(png_path.read_bytes())
        if icon_path.exists():
            CARD_LATEST_ICON_PATH.write_bytes(icon_path.read_bytes())
    quoted_png_name = urllib.parse.quote(png_path.name)
    unique_local_png_url = f"http://127.0.0.1:19300/card/report.png?name={quoted_png_name}&v={stamp}"
    unique_public_png_url = public_stock_url(f"{PUBLIC_BOT_MESSAGE_PATH}?card=report_png&name={quoted_png_name}&v={stamp}")
    payload = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "股票": stock,
        "SVG": str(svg_path),
        "PNG": str(png_path),
        "星级图标": str(icon_path),
        "最新SVG": str(CARD_LATEST_SVG_PATH),
        "最新PNG": str(CARD_LATEST_PNG_PATH),
        "最新星级图标": str(CARD_LATEST_ICON_PATH),
        "本地URL": LOCAL_CARD_URL,
        "本地PNGURL": unique_local_png_url,
        "本地星级图标URL": LOCAL_SIGNAL_ICON_URL,
        "公网URL": PUBLIC_CARD_URL,
        "公网PNGURL": unique_public_png_url,
        "公网星级图标URL": PUBLIC_SIGNAL_ICON_URL,
        "PNG渲染": png_result,
        "旧系统写入": False,
        "交易接口": False,
    }
    write_json(CARD_DIR / f"{code}_{stamp}.json", payload)
    write_json(CARD_LATEST_JSON_PATH, payload)
    return payload


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def format_decimal(value: Any, digits: int = 2, suffix: str = "") -> str:
    number = to_float(value)
    if number is None:
        return "-"
    return f"{number:.{digits}f}{suffix}"


def format_price(value: Any) -> str:
    number = to_float(value)
    if number is None:
        return "-"
    return f"{number:.2f}元"


def parse_price_text(value: Any) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", str(value or ""))
    return to_float(match.group(0)) if match else None


def format_percent(value: Any) -> str:
    text = str(value if value is not None else "").strip()
    if text.endswith("%"):
        return text
    return format_decimal(value, 2, "%")


def format_volume_ratio(value: Any) -> str:
    number = to_float(value)
    if number is None:
        return "-"
    return f"{number:.2f}"


def strip_html_tags(value: Any) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", str(value or ""))).strip()


def front_stars_by_score(score: Any) -> str:
    number = to_float(score) or 0.0
    if number >= 90:
        count = 5
    elif number >= 75:
        count = 4
    elif number >= 60:
        count = 3
    elif number >= 45:
        count = 2
    else:
        count = 1
    return "⭐" * count


def ma_map(indicator: dict[str, Any] | None) -> dict[str, Any]:
    if not indicator:
        return {}
    value = indicator.get("均线")
    return value if isinstance(value, dict) else {}


def macd_map(indicator: dict[str, Any] | None) -> dict[str, Any]:
    if not indicator:
        return {}
    value = indicator.get("MACD")
    return value if isinstance(value, dict) else {}


def quote_number(quote: dict[str, Any] | None, *keys: str) -> float | None:
    """兼容公开行情快照和L5/L6分层数据中的不同字段名。"""
    data = quote or {}
    for key in keys:
        value = to_float(data.get(key))
        if value is not None:
            return value
    return None


def quote_latest_price(quote: dict[str, Any] | None) -> float | None:
    return quote_number(quote, "最新价", "现价", "收盘价", "收盘", "close")


def build_reference_points(row: dict[str, Any] | None, indicator: dict[str, Any] | None) -> dict[str, str]:
    quote = row or {}
    ma = ma_map(indicator)
    latest = quote_latest_price(quote)
    ideal = quote_number(quote, "观察承接", "承接观察线") or to_float(ma.get("MA5")) or (latest * 0.98 if latest is not None else None)
    secondary = quote_number(quote, "次级承接") or to_float(ma.get("MA10")) or (latest * 0.96 if latest is not None else None)
    defense = quote_number(quote, "风险观察线", "防守位") or to_float(ma.get("MA60")) or (latest * 0.94 if latest is not None else None)
    high = quote_number(quote, "最高", "最高价", "high")
    target = quote_number(quote, "强度确认位", "强度确认线", "目标压力位") or max([value for value in [high, latest * 1.08 if latest is not None else None] if value is not None], default=None)
    return {
        "理想买点": format_price(ideal),
        "次优买点": format_price(secondary),
        "防守位": format_price(defense),
        "目标压力位": format_price(target),
    }


def build_signal_sentence(signal: dict[str, Any], score: Any) -> str:
    direction = str(signal.get("方向") or "")
    level = str(signal.get("级别") or "")
    score_text = format_decimal(score, 2, "分")
    marker = signal.get("企业微信文本标记") or signal.get("标记") or signal.get("企业微信标记") or ""
    marker = strip_html_tags(marker)
    if "卖出" in direction or "风险" in direction:
        return f"（系统评分：{score_text}）{marker} {level}，属于风险复核信号，需优先复核风险来源。"
    if "买入" in direction or "机会" in direction:
        return f"（系统评分：{score_text}）{marker} {level}，属于机会研究信号，可优先研究或继续观察。"
    return f"（系统评分：{score_text}）{marker} 当前为中性观察，暂不形成明确机会或风险研究信号。"


def build_analysis_explanation(row: dict[str, Any] | None, indicator: dict[str, Any] | None, decision: dict[str, Any]) -> str:
    quote = row or {}
    ma = ma_map(indicator)
    macd = macd_map(indicator)
    latest = to_float(quote.get("最新价"))
    ma5 = to_float(ma.get("MA5"))
    ma20 = to_float(ma.get("MA20"))
    rsi14 = to_float((indicator or {}).get("RSI14"))
    volume_ratio = to_float((indicator or {}).get("量比5日") or (indicator or {}).get("量比"))
    basis_items = [str(item).strip("。；;，, ") for item in decision.get("依据", [])[:2] if str(item).strip()]
    basis = "；".join(basis_items) or "趋势、量能和分层结果综合给出当前研究信号"
    notes: list[str] = [f"{basis}。"]
    if latest is not None and ma5:
        notes.append(f"现价相对MA5乖离约{((latest - ma5) / ma5 * 100):.2f}%，可判断短线是否存在追高或回踩确认需求。")
    if latest is not None and ma20:
        notes.append(f"现价相对MA20乖离约{((latest - ma20) / ma20 * 100):.2f}%，用于观察趋势强度与均值回归风险。")
    if rsi14 is not None:
        if rsi14 >= 70:
            notes.append(f"RSI14为{rsi14:.2f}，短线偏热，强势中也要防止追高。")
        elif rsi14 <= 30:
            notes.append(f"RSI14为{rsi14:.2f}，短线偏弱，需观察止跌确认。")
        else:
            notes.append(f"RSI14为{rsi14:.2f}，情绪未到极端区间。")
    if macd:
        dif = to_float(macd.get("DIF"))
        dea = to_float(macd.get("DEA"))
        bar = to_float(macd.get("MACD") or macd.get("柱"))
        if dif is not None and dea is not None and bar is not None:
            notes.append(f"MACD当前DIF {dif:.2f}、DEA {dea:.2f}、柱 {bar:.2f}，用于验证趋势动能是否延续。")
    if volume_ratio is not None:
        notes.append(f"量比约{volume_ratio:.2f}，可辅助判断资金参与度；若量能过度放大且乖离较高，需要警惕回调。")
    return "\n".join(notes)


def build_operation_checklist(row: dict[str, Any] | None, indicator: dict[str, Any] | None) -> list[str]:
    quote = row or {}
    ma = ma_map(indicator)
    macd = macd_map(indicator)
    latest = to_float(quote.get("最新价"))
    ma5 = to_float(ma.get("MA5"))
    ma10 = to_float(ma.get("MA10"))
    ma20 = to_float(ma.get("MA20"))
    ma60 = to_float(ma.get("MA60"))
    rsi14 = to_float((indicator or {}).get("RSI14"))
    volume_ratio = to_float((indicator or {}).get("量比5日") or (indicator or {}).get("量比"))
    lines: list[str] = []
    if all(value is not None for value in [ma5, ma10, ma20]):
        lines.append(("通过" if ma5 > ma10 > ma20 else "观察") + "：多头排列 MA5>MA10>MA20")
    else:
        lines.append("观察：均线数据不完整，需等待下一轮技术指标刷新")
    if latest is not None and ma60 is not None:
        lines.append(("通过" if latest >= ma60 else "警戒") + "：价格站上MA60")
    if rsi14 is not None:
        lines.append(("警戒" if rsi14 >= 70 else "通过") + f"：RSI14 {rsi14:.2f}")
    if macd:
        dif = to_float(macd.get("DIF"))
        dea = to_float(macd.get("DEA"))
        bar = to_float(macd.get("MACD") or macd.get("柱"))
        ok = dif is not None and dea is not None and bar is not None and dif >= dea and bar >= 0
        lines.append(("通过" if ok else "观察") + "：MACD动能验证")
    if volume_ratio is not None:
        lines.append(("通过" if volume_ratio >= 1.2 else "观察") + f"：量能量比 {volume_ratio:.2f}")
    lines.append("警戒：当前版本未接入实时新闻和财务数据，不能据此下最终结论")
    return lines


def is_holding_diagnosis_question(question: str) -> bool:
    text = str(question or "")
    keywords = ["持仓", "还能不能拿", "还能拿", "能拿吗", "拿吗", "拿着", "要不要走", "离场", "卖出", "减仓", "止盈", "止损"]
    return any(word in text for word in keywords)


def frontend_level(decision: dict[str, Any], industry_state: dict[str, Any], snapshot: dict[str, Any], holding_mode: bool = False) -> str:
    score = to_float(decision.get("评分")) or 0.0
    layer = str(decision.get("分层") or "")
    signal = decision.get("研究信号", {})
    direction = str(signal.get("方向") or "")
    industry_status = str(industry_state.get("景气状态") or "")
    quality = str(snapshot.get("公司品质档位") or snapshot.get("品质档位") or "待核验")
    if "风险" in direction or score < 40:
        return "离场观望" if holding_mode else "风险复核"
    if holding_mode:
        if score >= 58 and industry_status != "下行":
            return "继续持仓观察"
        if score >= 48:
            return "降低关注"
        return "离场观望"
    if "AI日报" in layer:
        if score >= 90:
            return "重点推荐"
        if score >= 70:
            return "常规推荐"
        if score >= 55:
            return "观察等待"
    if "L5" in layer and score >= 70 and industry_status == "上行" and quality not in {"低", "承压", "差"}:
        return "重点推荐"
    if "L5" in layer and score >= 55 and industry_status != "下行":
        return "常规推荐"
    if score >= 45:
        return "观察等待"
    return "风险复核"


def build_frontend_strategy_sentence(level: str, decision: dict[str, Any], industry_state: dict[str, Any], row: dict[str, Any] | None, indicator: dict[str, Any] | None) -> str:
    quote = row or {}
    score = to_float(decision.get("评分")) or 0.0
    industry_status = str(industry_state.get("景气状态") or "待核验")
    ma = ma_map(indicator)
    latest = quote_latest_price(quote)
    ma20 = to_float(ma.get("MA20"))
    ma60 = to_float(ma.get("MA60"))
    volume_ratio = to_float((indicator or {}).get("量比5日") or (indicator or {}).get("量比") or quote.get("量比"))
    trend_text = "中期趋势仍需确认"
    if latest is not None and ma20 is not None and ma60 is not None:
        if latest >= ma20 >= ma60:
            trend_text = "短中期趋势配合较好"
        elif latest >= ma20:
            trend_text = "短线有所修复，但中期趋势仍需确认"
        elif latest < ma60:
            trend_text = "价格仍在中期参考线下方，趋势偏弱"
    elif score >= 60:
        trend_text = "系统评分处于可观察区间，但均线数据仍需补齐"
    volume_text = "资金活跃度待确认"
    if volume_ratio is not None:
        if volume_ratio >= 1.5:
            volume_text = "资金活跃度明显提升"
        elif volume_ratio >= 1.1:
            volume_text = "资金活跃度有所改善"
        else:
            volume_text = "资金活跃度尚未明显放大"
    if level == "重点推荐":
        return f"{trend_text}，行业景气{industry_status}，{volume_text}，可列为高优先级研究对象。"
    if level == "常规推荐":
        return f"{trend_text}，行业景气{industry_status}，{volume_text}，可作为常规研究对象。"
    if level == "观察等待":
        return f"{trend_text}，{volume_text}，当前更适合观察等待，不宜急于追高。"
    if level == "继续持仓观察":
        return f"{trend_text}，{volume_text}，暂按量化价格线观察。"
    if level == "降低关注":
        return f"{trend_text}，行业或资金信号不够配合，建议降低关注并等待更明确信号。"
    if level == "离场观望":
        return f"{trend_text}，风险信号需要优先复核，建议转为离场观望。"
    return f"{trend_text}，{volume_text}，当前进入风险复核状态。"


def build_user_research_plan(level: str, row: dict[str, Any] | None, indicator: dict[str, Any] | None, points: dict[str, str]) -> dict[str, str]:
    quote = row or {}
    latest = quote_latest_price(quote)
    high = quote_number(quote, "最高", "最高价", "high")
    low = quote_number(quote, "最低", "最低价", "low")
    volume_ratio = to_float((indicator or {}).get("量比5日") or (indicator or {}).get("量比") or quote.get("量比"))
    current_price = format_price(latest)
    low_line = format_price(low if low is not None else latest)
    first_watch = points.get("目标压力位") or "-"
    support_watch = points.get("理想买点") or "-"
    trend_repair = points.get("防守位") or first_watch
    volume_condition = "成交量明显放大" if volume_ratio is not None and volume_ratio >= 1.1 else "成交量回到活跃状态"

    if level in {"风险复核", "离场观望"}:
        return {
            "是否关注": "暂不作为重点关注对象。",
            "当前动作": "先回避，等修复信号出现。",
            "关注条件": f"重新站回{first_watch}附近，并且{volume_condition}。",
            "转强条件": f"进一步站稳{trend_repair}附近，再考虑提高研究优先级。",
            "风险提醒": f"若继续弱于{low_line}附近，维持回避观察。",
            "价格状态": f"现价{current_price}，当前不急于找买点。",
            "第一观察线": first_watch,
            "修复线": trend_repair,
            "弱势线": low_line,
        }
    if level == "观察等待":
        return {
            "是否关注": "可以放入观察池，但不追高。",
            "当前动作": "不追高；等待承接区按标准成立，或转强线与量比同时达标。",
            "关注条件": f"回落到{support_watch}附近能稳住，或站回{first_watch}附近并放量。",
            "转强条件": f"站稳{first_watch}附近，且资金活跃度继续改善。",
            "风险提醒": f"若跌破{points.get('防守位', '-')}，降低关注。",
            "价格状态": f"现价{current_price}，等待更清楚的位置。",
            "观察区": support_watch,
            "转强线": first_watch,
            "风险线": points.get("防守位", "-"),
        }
    return {
        "是否关注": "值得继续关注。",
        "当前动作": "不追高；只看承接区或转强线是否达标。",
        "关注条件": f"回落到{support_watch}附近并按量化承接标准成立，可提高关注。",
        "转强条件": f"当天收盘价或当前实时价高于{first_watch}附近，且近5日成交活跃度达到平时的1.10倍以上。",
        "风险提醒": f"若跌破{points.get('防守位', '-')}，转为谨慎观察。",
        "价格状态": f"现价{current_price}，只等承接成立或转强确认。",
        "观察区": support_watch,
        "转强线": first_watch,
        "风险线": points.get("防守位", "-"),
    }


def build_numeric_watch_rules(row: dict[str, Any] | None, indicator: dict[str, Any] | None, points: dict[str, str], level: str = "") -> dict[str, str]:
    """把承接、转强、成交活跃全部量化，避免前台出现无法执行的模糊话。"""
    template = single_stock_template_config()
    numeric_rules = template.get("量化标准", {}) if isinstance(template.get("量化标准"), dict) else {}
    quote = row or {}
    latest = quote_latest_price(quote)
    support = parse_price_text(points.get("理想买点"))
    strong = parse_price_text(points.get("目标压力位"))
    risk = parse_price_text(points.get("防守位"))
    low_price = to_float(quote.get("最低") or quote.get("最低价") or quote.get("low"))
    volume_ratio = to_float((indicator or {}).get("量比5日") or (indicator or {}).get("量比") or quote.get("量比5日") or quote.get("量比"))
    active_line = to_float(numeric_rules.get("成交活跃量比5日")) or 1.10
    strong_line = to_float(numeric_rules.get("成交明显活跃量比5日")) or 1.30
    support_upper_ratio = to_float(numeric_rules.get("承接区上沿比例")) or 1.01
    support_upper = support * support_upper_ratio if support is not None else None
    support_zone = f"{format_price(support)}-{format_price(support_upper)}" if support is not None and support_upper is not None else points.get("理想买点", "-")
    risk_line = format_price(risk) if risk is not None else points.get("防守位", "-")
    strong_line_price = format_price(strong) if strong is not None else points.get("目标压力位", "-")
    active_plain = f"近5日成交活跃度达到平时的{active_line:.2f}倍以上"
    strong_plain = f"近5日成交活跃度达到平时的{strong_line:.2f}倍以上"
    volume_current = f"当前只有{volume_ratio:.2f}倍" if volume_ratio is not None and volume_ratio < active_line else f"当前{volume_ratio:.2f}倍" if volume_ratio is not None else "当前成交活跃度未刷新"
    volume_result = "达到活跃标准" if volume_ratio is not None and volume_ratio >= active_line else "没有达到活跃标准" if volume_ratio is not None else "等待系统刷新"
    if volume_ratio is not None and volume_ratio >= strong_line:
        volume_result = "明显活跃"
    below_main_line = latest is not None and (
        (risk is not None and latest < risk)
        or (support is not None and latest < support and level in {"风险复核", "离场观望"})
    )
    if below_main_line:
        weak_line = format_price(low_price) if low_price is not None else format_price(latest)
        return {
            "现价": format_price(latest),
            "承接区": support_zone,
            "承接标准": f"当前{format_price(latest)}低于承接区{support_zone}，先不作为重点关注；重新站回{format_price(support)}上方并且不再跌回{weak_line}下方，才算止跌修复。",
            "转强标准": f"当天收盘价或当前实时价高于{strong_line_price}；更稳妥看连续2个交易日收盘价都高于{strong_line_price}，同时{active_plain}。",
            "成交标准": f"成交活跃就是{active_plain}；明显活跃就是{strong_plain}。{volume_current}，{volume_result}。",
            "风险标准": f"当前已低于{risk_line}风险线，维持风险复核；只要没有重新站回{risk_line}上方，就继续回避；若继续跌破{weak_line}，风险加重。",
            "下一步": f"先等两个修复信号：一是重新站回{format_price(support)}上方并稳住；二是站上{strong_line_price}且成交活跃度达标。未出现前不列为重点关注。",
        }
    return {
        "现价": format_price(latest),
        "承接区": support_zone,
        "承接标准": f"价格回到{support_zone}后不跌破{risk_line}；当天收盘价或当前实时价重新站上{format_price(support)}，视为承接成立。",
        "转强标准": f"当天收盘价或当前实时价高于{strong_line_price}；更稳妥看连续2个交易日收盘价都高于{strong_line_price}，同时{active_plain}。",
        "成交标准": f"成交活跃就是{active_plain}；明显活跃就是{strong_plain}。{volume_current}，{volume_result}。",
        "风险标准": f"跌破{risk_line}，或跌回{format_price(support)}下方且近5日成交活跃度低于平时的{active_line:.2f}倍，转为谨慎观察。",
        "下一步": f"只等两个信号：一是承接区{support_zone}按标准成立；二是站上{strong_line_price}且成交活跃度达标。",
    }


def user_risk_summary(level: str, decision: dict[str, Any], row: dict[str, Any] | None, indicator: dict[str, Any] | None) -> str:
    risks_text = "；".join(str(item) for item in decision.get("风险", []) if str(item).strip())
    if level in {"风险复核", "离场观望"}:
        return "系统后台继续核验公告、财报和行业信息；但当前价格位置和成交活跃度已经不支持重点关注，先等修复信号。"
    if "过热" in risks_text:
        return "短线偏热，避免追高；等待价格回到承接区并按标准成立。"
    if risks_text and not any(token in risks_text for token in ["候选", "核验", "公告", "财报", "行业"]):
        return "存在风险提醒，需等价格和成交量继续确认。"
    if risks_text:
        return "系统会继续核验公告、财报和行业信息；当前前台先按价格和成交量条件执行观察。"
    return "暂无突出的前台风险，但仍需跟踪公告、财报和市场环境。"


def baillie_keyword_hits(text: str, keywords: list[str]) -> list[str]:
    compact = str(text or "").lower()
    hits: list[str] = []
    for keyword in keywords:
        word = str(keyword or "").strip()
        if word and word.lower() in compact and word not in hits:
            hits.append(word)
    return hits


def build_baillie_growth_assessment(
    stock: dict[str, Any],
    quote: dict[str, Any] | None,
    snapshot: dict[str, Any],
    industry_line: str,
    finance_status: str,
    risk_items: list[str],
) -> dict[str, Any]:
    """把柏基长期成长框架转成报告里的定性雷达，不改变系统评分。"""
    framework = load_baillie_growth_framework()
    text_parts = [
        stock.get("名称"),
        stock.get("name"),
        stock.get("行业"),
        stock.get("细分领域"),
        stock.get("板块"),
        (quote or {}).get("行业"),
        snapshot.get("申万一级行业"),
        snapshot.get("细分行业"),
        industry_line,
        snapshot.get("公司简介"),
        snapshot.get("主营业务"),
    ]
    source_text = " ".join(str(item or "") for item in text_parts)
    law_rules = framework.get("加速回报定律关键词", {}) if isinstance(framework.get("加速回报定律关键词"), dict) else {}
    theme_rules = framework.get("长期主题关键词", {}) if isinstance(framework.get("长期主题关键词"), dict) else {}
    law_hits: list[str] = []
    for law_name, keywords in law_rules.items():
        if isinstance(keywords, list) and baillie_keyword_hits(source_text, [str(item) for item in keywords]):
            law_hits.append(str(law_name))
    theme_hits: list[str] = []
    for theme_name, keywords in theme_rules.items():
        if isinstance(keywords, list) and baillie_keyword_hits(source_text, [str(item) for item in keywords]):
            theme_hits.append(str(theme_name))

    positive_count = len(law_hits) + min(len(theme_hits), 3)
    if positive_count >= 4 and finance_status == "已接入":
        radar = "长期成长高优先级复核"
    elif positive_count >= 2:
        radar = "长期成长观察"
    elif positive_count == 1:
        radar = "单主题待核验"
    else:
        radar = "暂未识别长期成长主线"

    if finance_status != "已接入" and radar in {"长期成长高优先级复核", "长期成长观察"}:
        radar = "长期成长观察（证据不足）"

    if law_hits:
        law_line = "可能相关：" + "、".join(law_hits[:3])
    else:
        law_line = "未识别成本下降或性能提升的明确证据，需补充技术成熟度曲线。"
    if len(theme_hits) >= 2:
        theme_line = "主题重叠：" + "、".join(theme_hits[:4])
    elif theme_hits:
        theme_line = "单一主题：" + "、".join(theme_hits[:2])
    else:
        theme_line = "未进入多主题重叠区，不能按平台型成长逻辑加分。"

    diligence_lines = [
        "TAM/终局市场：待补充未来5-10年市场空间证据。",
        "管理层长期主义：待补充创始人/管理层公开信、访谈和研发投入连续性。",
        "社会贡献/护城河：待核验产品是否成为客户基础设施或生态共生节点。",
    ]
    if finance_status == "已接入":
        diligence_lines.append("财务纪律：财报关键指标已接入，可继续核验研发、现金流和资本开支方向。")
    else:
        diligence_lines.append("财务纪律：财报关键指标未完整接入，不能据此提高长期评级。")

    devil_risks = [item for item in risk_items if item][:3]
    if not devil_risks:
        devil_risks = ["技术路线被替代", "估值提前透支长期成长", "行业景气或政策环境逆转"]
    while len(devil_risks) < 3:
        fallback = ["关键客户或供应链变化", "竞争格局恶化", "管理层长期投入不及预期"][len(devil_risks) - 1]
        devil_risks.append(fallback)

    return {
        "雷达结论": radar,
        "加速回报定律": law_line,
        "欧拉图主题": theme_line,
        "主题数量": len(theme_hits),
        "尽调十问摘要": diligence_lines,
        "魔鬼代言人风险": devil_risks[:5],
        "使用边界": "本框架只用于长期成长质量复核，不改变系统评分，不构成买卖建议。",
    }


def baillie_growth_report_lines(assessment: dict[str, Any]) -> list[str]:
    lines = [
        f"- 雷达结论：{assessment.get('雷达结论', '待核验')}",
        f"- 技术成熟度：{assessment.get('加速回报定律', '待核验')}",
        f"- 欧拉图主题：{assessment.get('欧拉图主题', '待核验')}",
    ]
    for item in assessment.get("尽调十问摘要", [])[:4]:
        lines.append(f"- {item}")
    risks = assessment.get("魔鬼代言人风险", [])
    if risks:
        lines.append("- 反证清单：" + "；".join(str(item) for item in risks[:3]))
    lines.append(f"- 边界：{assessment.get('使用边界')}")
    return lines


def split_front_rule(text: str) -> list[str]:
    """把前台观察条件拆成手机端短句，避免一行塞进多个判断。"""
    raw = str(text or "").strip()
    if not raw:
        return []
    parts = re.split(r"[；。]", raw)
    lines: list[str] = []
    for part in parts:
        item = part.strip("，,；。 ")
        if not item:
            continue
        if "，同时" in item:
            lines.extend(sub.strip("，, ") for sub in item.split("，同时") if sub.strip("，, "))
        elif "，或" in item:
            lines.extend(sub.strip("，, ") for sub in item.split("，或") if sub.strip("，, "))
        elif "且" in item:
            lines.extend(sub.strip("，, ") for sub in item.split("且") if sub.strip("，, "))
        else:
            lines.append(item)
    return [line for line in lines if line]


def front_block(label: str, text: str) -> str:
    lines = split_front_rule(text)
    if not lines:
        return f"{label}：-"
    return "\n".join([f"{label}：", *[f"- {line}" for line in lines]])


def front_action_text(level: str, watch_rules: dict[str, str], points: dict[str, str]) -> str:
    """把操作策略写成用户能直接理解的答案，避免只说“看观察线”。"""
    if level in {"风险复核", "离场观望"}:
        return "先回避。只有修复区重新站稳、转强线有效突破、成交活跃度达标，才重新纳入观察。"
    strong_line = points.get("目标压力位", "-")
    return f"{level}，但现价不追。低位看{watch_rules.get('承接区', '-')}能否稳住；上攻看{strong_line}能否站上。两者都不满足就继续观察。"


def build_frontend_stock_reply(
    stock: dict[str, Any],
    row: dict[str, Any] | None,
    indicator: dict[str, Any] | None,
    decision: dict[str, Any],
    report_path: str,
    holding_mode: bool = False,
) -> str:
    name = stock.get("名称") or stock.get("name") or stock.get("代码") or stock.get("code")
    code = str(stock.get("代码") or stock.get("code") or "").lower()
    snapshot = find_company_snapshot(stock)
    industry = (
        snapshot.get("申万一级行业")
        or (row or {}).get("行业")
        or stock.get("行业")
        or stock.get("细分领域")
        or stock.get("板块")
        or "-"
    )
    industry_state = find_industry_prosperity(industry)
    level = frontend_level(decision, industry_state, snapshot, holding_mode=holding_mode)
    points = build_reference_points(row, indicator)
    plan = build_user_research_plan(level, row, indicator, points)
    watch_rules = build_numeric_watch_rules(row, indicator, points, level)
    action_text = front_action_text(level, watch_rules, points)
    risk_summary = user_risk_summary(level, decision, row, indicator)
    signal = decision.get("研究信号", {}) if isinstance(decision.get("研究信号"), dict) else {}
    stars = front_stars_by_score(decision.get("评分"))
    strength = str(signal.get("强度") or "-")
    if strength != "-" and not strength.endswith("/5"):
        strength = f"{strength}/5"
    if holding_mode:
        title = f"{name}({code}) 持仓诊断"
        current_label = level
        return "\n".join([
            title,
            f"当前判断：{current_label} {stars}",
            f"强度：{strength}",
            "",
            f"核心答案：{risk_summary}",
            "",
            front_block("操作策略", action_text),
            "",
            front_block("后续条件", watch_rules["承接标准"]),
            "",
            front_block("转强条件", watch_rules["转强标准"]),
            "",
            front_block("成交标准", watch_rules["成交标准"]),
            "",
            front_block("风险线", watch_rules["风险标准"]),
            "",
            f"结论：{current_label}。{plan['是否关注']}",
            "",
            f"图文详情：{public_single_stock_report_url(name)}",
        ])
    return "\n".join([
        f"{name}({code})",
        f"当前判断：{level} {stars}；强度：{strength}",
        f"现价：{watch_rules['现价']}",
        "",
        front_block("操作策略", action_text),
        "",
        front_block("关注条件", watch_rules["承接标准"]),
        "",
        front_block("转强条件", watch_rules["转强标准"]),
        "",
        front_block("成交标准", watch_rules["成交标准"]),
        "",
        front_block("风险线", watch_rules["风险标准"]),
        "",
        f"结论：{watch_rules['下一步']}",
        "",
        f"补充核验：{risk_summary}",
        "",
        f"图文详情：{public_single_stock_report_url(name)}",
    ])


def replay_main_reason(decision: dict[str, Any], industry_state: dict[str, Any]) -> tuple[str, list[str]]:
    signal = decision.get("研究信号", {})
    direction = str(signal.get("方向") or "")
    basis_text = "；".join(str(item) for item in decision.get("依据", []))
    reasons: list[str] = []
    if "风险" in direction:
        main = "风险复核"
    elif industry_state.get("景气状态") == "上行" or "行业" in basis_text:
        main = "行业景气"
    else:
        main = "技术/资金信号"
    if main != "技术/资金信号":
        reasons.append("技术/资金信号")
    if main != "行业景气" and industry_state:
        reasons.append("行业景气")
    return main, reasons


def verification_periods(main_reason: str) -> list[str]:
    if main_reason == "技术/资金信号":
        return ["T5", "T20"]
    if main_reason == "行业景气":
        return ["T20", "T60"]
    if main_reason == "公司品质":
        return ["T60", "T120"]
    if main_reason == "风险复核":
        return ["T5", "T20"]
    return ["T20", "T60"]


def append_judgment_replay_record(record: dict[str, Any]) -> None:
    ledger = load_json(JUDGMENT_REPLAY_LEDGER_LATEST_PATH, []) or []
    if not isinstance(ledger, list):
        ledger = []
    key = (
        record.get("股票代码"),
        record.get("报告日期"),
        record.get("系统评分"),
        record.get("分层状态"),
        record.get("报告类型"),
    )
    for item in ledger:
        if (
            item.get("股票代码"),
            item.get("报告日期"),
            item.get("系统评分"),
            item.get("分层状态"),
            item.get("报告类型"),
        ) == key:
            for field in ("基准价格", "基准涨跌幅", "原始报告路径", "记录时间"):
                if record.get(field) not in (None, "") and item.get(field) in (None, ""):
                    item[field] = record.get(field)
            write_json(JUDGMENT_REPLAY_LEDGER_LATEST_PATH, ledger)
            return
    ledger.append(record)
    write_json(JUDGMENT_REPLAY_LEDGER_LATEST_PATH, ledger)


def persist_standard_report_v2(
    stock: dict[str, Any],
    quote: dict[str, Any] | None,
    decision: dict[str, Any],
    report_text: str,
    industry_state: dict[str, Any],
    snapshot: dict[str, Any],
    trigger: str,
) -> str:
    now = datetime.now()
    day = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y%m%d_%H%M%S")
    code = normalize_full_code(stock.get("代码") or stock.get("code") or "")
    name = stock.get("名称") or stock.get("name") or code
    safe_name = "".join(ch for ch in str(name) if ch not in '\\/:*?"<>|') or code
    report_path = STANDARD_REPORT_V2_DIR / f"单股标准报告v2_{safe_name}_{code}_{stamp}.md"
    latest_path = STANDARD_REPORT_V2_DIR / "单股标准报告v2_最新.md"
    write_text(report_path, report_text)
    write_text(latest_path, report_text)

    signal = decision.get("研究信号", {})
    attention_level = "风险复核对象" if "风险" in str(signal.get("方向")) else "常规跟踪对象"
    main_reason, sub_reasons = replay_main_reason(decision, industry_state)
    quality_level = snapshot.get("公司品质档位") or snapshot.get("品质档位") or "待核验"
    record = {
        "股票代码": code,
        "股票名称": name,
        "报告日期": day,
        "报告类型": "单股标准报告v2",
        "报告触发原因": trigger,
        "判断主因": main_reason,
        "辅因": sub_reasons,
        "关注等级": attention_level,
        "系统评分": decision.get("评分"),
        "分层状态": decision.get("分层"),
        "基准价格": (quote or {}).get("最新价"),
        "基准涨跌幅": (quote or {}).get("涨跌幅"),
        "证据完整度": "中",
        "公司品质档位": quality_level,
        "原始报告路径": str(report_path),
        "应验证周期": verification_periods(main_reason),
        "验证结果_T5": None,
        "验证结果_T20": None,
        "验证结果_T60": None,
        "验证结果_T120": None,
        "人工评价": None,
        "备注": "由股票助手入口生成标准报告v2时自动写入；不自动修改规则。",
        "记录时间": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
    append_judgment_replay_record(record)
    return str(report_path)


def build_wecom_stock_report(
    stock: dict[str, Any],
    row: dict[str, Any] | None,
    indicator: dict[str, Any] | None,
    decision: dict[str, Any],
    card: dict[str, Any],
) -> str:
    name = stock.get("名称") or stock.get("name") or stock.get("代码") or stock.get("code")
    code = str(stock.get("代码") or stock.get("code") or "").lower()
    quote = row or {}
    snapshot = find_company_snapshot(stock)
    snapshot_industry = snapshot.get("申万一级行业")
    snapshot_sub_industry = snapshot.get("细分行业")
    industry = snapshot_industry or quote.get("行业") or stock.get("行业") or stock.get("细分领域") or stock.get("板块") or "-"
    sub_industry = snapshot_sub_industry or quote.get("行业") or stock.get("细分领域") or "-"
    unknown_tokens = {"", "-", "待补充", "待接入", "待映射", "None", "none", "null"}

    def is_unknown_text(value: Any) -> bool:
        return str(value or "").strip() in unknown_tokens

    industry = next(
        (
            str(value).strip()
            for value in [snapshot_industry, quote.get("行业"), stock.get("行业"), stock.get("细分领域"), stock.get("板块")]
            if not is_unknown_text(value)
        ),
        "-",
    )
    sub_industry = next(
        (
            str(value).strip()
            for value in [snapshot_sub_industry, quote.get("细分行业"), quote.get("行业"), stock.get("细分领域")]
            if not is_unknown_text(value)
        ),
        "-",
    )
    display_industry = "行业待核验" if is_unknown_text(industry) else str(industry).strip()
    display_sub_industry = "" if is_unknown_text(sub_industry) or str(sub_industry).strip() == display_industry else str(sub_industry).strip()
    industry_display_line = f"{display_industry} / {display_sub_industry}" if display_sub_industry else display_industry
    industry_state_subject = f"{display_industry}行业景气状态" if not is_unknown_text(industry) else "行业景气状态"
    industry_state = find_industry_prosperity(industry)
    signal = decision.get("研究信号", {})
    checklist = build_operation_checklist(row, indicator)
    volume_ratio = format_volume_ratio((indicator or {}).get("量比5日") or (indicator or {}).get("量比") or quote.get("量比"))
    basis_items = [str(item).strip("。；; ") for item in decision.get("依据", [])[:3] if str(item).strip()]
    risk_items = [str(item).strip("。；; ") for item in decision.get("风险", [])[:2] if str(item).strip()]
    risk_level = "高" if "风险" in str(signal.get("方向")) else "中"
    market_line = (
        f"现价{format_price(quote_latest_price(quote))}，涨跌幅{format_percent(quote.get('涨跌幅'))}，"
        f"最高/最低{format_price(quote_number(quote, '最高', '最高价', 'high'))}/{format_price(quote_number(quote, '最低', '最低价', 'low'))}"
    )
    front_level = frontend_level(decision, industry_state, snapshot, holding_mode=False)
    strategy = build_frontend_strategy_sentence(front_level, decision, industry_state, row, indicator)
    key_reason = "；".join(basis_items[:2]) or "趋势、量价和分层状态综合显示仍需继续观察"
    if "\n" in key_reason or "基本信息" in key_reason or "万亿元" in key_reason:
        key_reason = "行业强度、资金活跃度和分层状态共同触发关注；公司经营和公告证据仍需继续核验"
    if len(key_reason) > 130:
        key_reason = key_reason[:129] + "…"
    key_risk = "；".join(risk_items) or "暂无额外风险提示；仍需结合新闻、财务和大盘环境复核"
    key_risk = re.sub(
        r"(RSI14为)(\d+\.\d{3,})",
        lambda match: f"{match.group(1)}{float(match.group(2)):.2f}",
        key_risk,
    )
    points = build_reference_points(row, indicator)
    plan = build_user_research_plan(front_level, row, indicator, points)
    watch_rules = build_numeric_watch_rules(row, indicator, points, front_level)
    action_text = front_action_text(front_level, watch_rules, points)
    risk_summary = user_risk_summary(front_level, decision, row, indicator)
    volume_number = to_float((indicator or {}).get("量比5日") or (indicator or {}).get("量比") or quote.get("量比"))
    if volume_number is None:
        volume_state = "待确认"
    elif volume_number >= 1.2:
        volume_state = "活跃"
    elif volume_number >= 0.8:
        volume_state = "一般"
    else:
        volume_state = "偏弱"
    if "卖出" in str(signal.get("方向")) or "风险" in str(signal.get("方向")):
        signal_type = "风险复核信号"
    elif "买入" in str(signal.get("方向")) or "机会" in str(signal.get("方向")):
        signal_type = "机会研究信号"
    else:
        signal_type = "中性观察研究信号"
    signal_marker = front_stars_by_score(decision.get("评分"))
    strength_text = str(signal.get("强度", "-"))
    if strength_text and strength_text != "-" and not strength_text.endswith("/5"):
        strength_text = f"{strength_text}/5"
    finance = snapshot.get("财报快照", {}) if snapshot else {}
    finance_status = snapshot.get("证据状态", {}).get("财报指标", "待接入") if snapshot else "待接入"
    if finance_status == "已接入":
        finance_line = (
            f"最新报告期{finance.get('最新报告期', '-')}，营业收入{format_decimal(finance.get('营业收入_亿元'), 2)}亿元，"
            f"归母净利润{format_decimal(finance.get('归母净利润_亿元'), 2)}亿元，扣非净利润{format_decimal(finance.get('扣非净利润_亿元'), 2)}亿元；"
            f"毛利率{format_percent(finance.get('毛利率'))}，ROE{format_percent(finance.get('ROE'))}。"
        )
        evidence_text = "行情、分层、财报关键指标已接入；公告和行业价格仍待核验。"
    else:
        finance_line = "财报关键指标尚未接入，需补充营业收入、利润、毛利率、ROE、现金流等字段。"
        evidence_text = "行情和分层已接入；财报、公告和行业价格仍待核验。"
    company_status = snapshot.get("证据状态", {}).get("公司概况", "待接入") if snapshot else "待接入"
    industry_line = industry_state.get("前台结论") or "行业景气结论暂未生成，需等待L6行业强度刷新。"
    if is_unknown_text(industry):
        industry_line = "行业景气结论暂未生成；行业映射和L6行业强度仍需补齐后复核。"
    conclusion = (
        f"按当前行情、技术结构和分层结果，系统给出{front_level}；"
        f"{industry_state_subject}为{industry_state.get('景气状态', '待核验')}。"
    )
    strategy_note = strategy
    if finance_status != "已接入" or is_unknown_text(industry):
        strategy_note = f"{strategy} 由于行业、财报或公告证据仍未完全接入，本条只作为常规研究对象继续跟踪。"
    if len(strategy_note) > 150:
        strategy_note = strategy_note[:149] + "…"
    checklist_text = "\n".join(f"- {item}" for item in checklist[:4])
    def compact_mobile_sentence(value: Any, limit: int = 42) -> str:
        text = re.sub(r"^\s*\d+[.、]\s*", "", str(value or "").strip("。；; \n"))
        return text if len(text) <= limit else text[: limit - 1] + "…"

    reason_text = "\n".join(f"- {compact_mobile_sentence(item)}" for item in basis_items[:2]) or "- 趋势、量价和分层状态仍需继续观察"
    evidence_short = "行情/分层已接入"
    evidence_gap = "财报/公告/行业价格待核验"
    if finance_status == "已接入":
        evidence_short = "行情/分层/财报已接入"
        evidence_gap = "公告/行业价格待核验"
    if is_unknown_text(industry):
        company_line = "结构化公司画像暂未接入。"
    else:
        company_line = f"已识别行业：{industry_display_line}；公司画像：{company_status}。"
    industry_mobile_line = str(industry_state.get("景气状态") or "待生成")
    finance_mobile_line = "关键指标待接入。"
    if finance_status == "已接入":
        finance_mobile_line = (
            f"{finance.get('最新报告期', '-')}；营收{format_decimal(finance.get('营业收入_亿元'), 2)}亿元；"
            f"净利{format_decimal(finance.get('归母净利润_亿元'), 2)}亿元。"
        )
    if front_level in {"风险复核", "离场观望"}:
        price_watch_lines = [
            f"- 当前价：{watch_rules['现价']}",
            f"- 修复区：{watch_rules['承接区']}",
            f"- 转强线：{points.get('目标压力位', '-')}",
            f"- 风险线：{points.get('防守位', '-')}",
        ]
    else:
        price_watch_lines = [
            f"- 当前价：{watch_rules['现价']}",
            f"- 承接区：{watch_rules['承接区']}",
            f"- 转强线：{points.get('目标压力位', '-')}",
            f"- 风险线：{points.get('防守位', '-')}",
        ]
    if front_level in {"重点推荐", "常规推荐"}:
        answer_line = f"{front_level}，值得纳入研究清单。"
    elif front_level == "观察等待":
        answer_line = "观察等待，可以放入观察池，但暂不提高优先级。"
    else:
        answer_line = f"{front_level}，当前先不作为重点关注对象。"
    volume_user_line = {
        "活跃": "成交量已经较活跃，后续重点看能否持续。",
        "一般": "成交量暂时一般，后续要看是否重新放大。",
        "偏弱": "成交量偏弱，暂时不支持直接提高关注。",
        "待确认": "成交量状态待确认，等待下一轮数据刷新。",
    }.get(volume_state, "成交量状态待确认。")
    evidence_lines = [
        f"- 行业：{industry_display_line}；景气：{industry_mobile_line}。",
        f"- 财报：{finance_mobile_line}",
        f"- 证据缺口：{evidence_gap}。",
    ]
    if is_unknown_text(industry):
        evidence_lines[0] = "- 行业：仍待核验，暂不把行业结论作为强支撑。"
    baillie_assessment = build_baillie_growth_assessment(
        stock=stock,
        quote=quote,
        snapshot=snapshot,
        industry_line=industry_display_line,
        finance_status=finance_status,
        risk_items=risk_items,
    )
    baillie_lines = baillie_growth_report_lines(baillie_assessment)
    focus_lines = [f"- {line}" for line in split_front_rule(watch_rules["承接标准"])]
    focus_lines.extend(f"- {line}" for line in split_front_rule(watch_rules["转强标准"]))
    focus_lines.extend(f"- {line}" for line in split_front_rule(watch_rules["成交标准"]))
    risk_front_lines = [f"- {line}" for line in split_front_rule(watch_rules["风险标准"])]
    action_lines = [f"- {line}" for line in split_front_rule(action_text)]
    return "\n".join([
        f"![股票图形报告]({card['公网PNGURL']})",
        "",
        f"{name}({code})",
        f"生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "【结论】",
        f"{answer_line} {signal_marker}",
        f"强度：{strength_text}",
        "",
        "【操作策略】",
        *action_lines,
        "",
        "一、关注条件",
        *focus_lines,
        "",
        "二、价格观察",
        *price_watch_lines,
        "",
        "三、为什么这样判断",
        f"- {plan['价格状态']}",
        f"- {volume_user_line}",
        f"- {risk_summary}",
        "",
        "四、风险提醒",
        *risk_front_lines,
        "- 待核验：公告、行业价格、解禁减持、财报正文。",
        "",
        "五、证据补充",
        *evidence_lines,
        "",
        "六、长期成长质量框架",
        *baillie_lines,
        "",
        "七、后续跟踪重点",
        "- 是否守住风险线。",
        "- 成交量是否持续改善。",
        "- 是否重新进入重点研究层。",
        "- 财报、公告和行业证据是否补齐。",
        "",
        "说明：本页为研究报告，不自动交易。",
    ])


def build_clarification_reply(question: str) -> dict[str, Any]:
    reply = "\n".join([
        "杰哥，我还没对齐你的意思，先不乱猜。",
        "",
        "你是想看“今日推荐”，还是想分析某只股票？",
        "如果是单股，直接发股票名或代码，比如“天齐锂业”或“300750”。",
    ])
    return {
        "状态": "需要澄清",
        "类型": "意图澄清",
        "问题": question,
        "回复": reply,
        "企业微信回复": reply,
        "澄清选项": ["今日推荐", "分析某只股票", "持仓诊断", "系统状态"],
        "重点关注池数量": len(focus_stocks()),
        "安全边界": load_config().get("安全边界", {}),
    }


def build_missing_stock_reply(question: str, intent: str = "单股分析") -> dict[str, Any]:
    if intent == "持仓诊断":
        lead = "你想诊断哪只持仓股票？"
        example = "比如：持仓 天齐锂业，或 天齐锂业还能不能拿。"
    else:
        lead = "请告诉我股票名称或代码。"
        example = "比如：分析 天齐锂业，或直接输入 300750。"
    reply = "\n".join([
        f"杰哥，{lead}",
        example,
        "我拿到股票对象后，直接给你当前判断、操作策略、关注条件、风险线和结论。",
    ])
    return {
        "状态": "需要补充股票",
        "类型": intent,
        "问题": question,
        "回复": reply,
        "企业微信回复": reply,
        "重点关注池数量": len(focus_stocks()),
        "安全边界": load_config().get("安全边界", {}),
    }


def build_context_choice_reply(question: str, stocks: list[dict[str, Any]]) -> dict[str, Any]:
    names = "、".join(stock_display_name(stock) for stock in stocks[:3])
    reply = "\n".join([
        "杰哥，刚才提到过不止一只股票，我不确定你说的是哪只。",
        f"你是指：{names}？",
        "请直接回复股票名或代码，我再接着分析。",
    ])
    return {
        "状态": "需要选择股票",
        "类型": "上下文澄清",
        "问题": question,
        "回复": reply,
        "企业微信回复": reply,
        "候选股票": [stock_display_name(stock) for stock in stocks[:3]],
        "安全边界": load_config().get("安全边界", {}),
    }


def build_analysis(question: str, refresh: bool = True, remember_context: bool = True, entrance_role: str = "助手") -> dict[str, Any]:
    if is_help_question(question):
        return build_usage_help()
    if contains_trade_action(question):
        return build_trade_action_refusal(question)
    role_text = str(entrance_role or "")
    if "专家" in role_text:
        if not find_stock(question) or is_daily_recommendation_question(question):
            return build_expert_overview_reply(question)
    if is_daily_recommendation_question(question):
        return build_daily_recommendation_reply()
    if is_system_status_question(question):
        return build_system_status_reply()
    if is_model_health_question(question):
        return build_model_health_reply()
    if is_public_callback_question(question):
        return build_public_callback_reply()
    stock = find_stock(question)
    holding_mode = is_holding_diagnosis_question(question)
    single_stock_intent = is_single_stock_analysis_question(question)
    context_pronoun = uses_recent_context_pronoun(question)
    if not stock and (holding_mode or single_stock_intent or context_pronoun):
        recent_stocks = recent_context_stocks()
        if len(recent_stocks) == 1 and (context_pronoun or holding_mode):
            stock = recent_stocks[0]
        elif len(recent_stocks) > 1 and (context_pronoun or holding_mode):
            return build_context_choice_reply(question, recent_stocks)
    if not stock:
        if holding_mode:
            return build_missing_stock_reply(question, intent="持仓诊断")
        if single_stock_intent:
            return build_missing_stock_reply(question, intent="单股分析")
        return build_clarification_reply(question)
    if remember_context:
        remember_recent_stock(stock)
    snapshot = latest_quote_snapshot(refresh=refresh)
    row = find_quote(stock, snapshot)
    indicator = find_indicator(stock)
    candidate = find_candidate(stock)
    risk_row = find_risk_observation_row(stock)
    if row and risk_row:
        row = {**risk_row, **row}
    elif candidate and risk_row:
        row = {**candidate, **risk_row}
    elif not row and candidate:
        # AI日报/L5/L6中的扩展股票可能不在旧公开行情快照内，使用分层候选数据兜底行情字段。
        row = candidate
    elif not row and risk_row:
        row = risk_row
    decision = merge_candidate_decision(score_quote(row), candidate)
    card = generate_stock_card(stock, row, decision)
    name = stock.get("名称") or stock.get("name") or stock.get("代码") or stock.get("code")
    code = stock.get("代码") or stock.get("code")
    snapshot_for_report = find_company_snapshot(stock)
    industry_for_report = (
        snapshot_for_report.get("申万一级行业")
        or (row or {}).get("行业")
        or stock.get("行业")
        or stock.get("细分领域")
        or stock.get("板块")
        or "-"
    )
    industry_state_for_report = find_industry_prosperity(industry_for_report)
    reply = [
        f"{name}（{code}）研究助手快评",
        f"观察分层：{decision['分层']}，体验版评分：{decision['评分']}。",
        f"研究信号：{decision['研究信号']['标记']} {decision['研究信号']['方向']}（强度{decision['研究信号']['强度']}）。{decision['研究信号']['说明']}",
        f"图形报告PNG：{card['本地PNGURL']}",
    ]
    standard_report_v2 = build_wecom_stock_report(stock, row, indicator, decision, card)
    standard_report_path = persist_standard_report_v2(
        stock,
        row,
        decision,
        standard_report_v2,
        industry_state_for_report,
        snapshot_for_report,
        trigger="用户点击/企业微信查询",
    )
    frontend_reply = build_frontend_stock_reply(
        stock,
        row,
        indicator,
        decision,
        standard_report_path,
        holding_mode=holding_mode,
    )
    # 企业微信聊天气泡只给“答案型简报”；展开详情由链接页读取标准报告v2。
    wecom_reply = [frontend_reply]
    if row:
        market_line = f"公开行情：最新价{row.get('最新价')}，涨跌幅{row.get('涨跌幅')}%，成交额{row.get('成交额')}，行业{row.get('行业')}。"
        reply.append(market_line)
    for line in [
        "主要依据：" + "；".join(decision["依据"]),
        "风险提示：" + "；".join(decision["风险"]),
        "定位声明：这是研究助手输出，不是交易指令，不自动下单。",
    ]:
        reply.append(line)
    record_history(question, stock, row, decision)
    return {
        "状态": "完成",
        "问题": question,
        "股票": stock,
        "行情": row,
        "技术指标": indicator,
        "规则判断": decision,
        "图形报告": card,
        "回复": frontend_reply,
        "后台详细回复": "\n".join(reply),
        "企业微信回复": "\n".join(wecom_reply),
        "标准报告v2路径": standard_report_path,
        "判断复盘账": str(JUDGMENT_REPLAY_LEDGER_LATEST_PATH),
        "最新报告": str(REPORT_LATEST_PATH),
        "安全边界": load_config().get("安全边界", {}),
    }


def record_history(question: str, stock: dict[str, Any], quote: dict[str, Any] | None, decision: dict[str, Any]) -> None:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    payload = {
        "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "问题": question,
        "股票": stock,
        "行情": quote,
        "规则判断": decision,
    }
    write_json(HISTORY_DIR / f"stock-assistant-query-{stamp}.json", payload)
    write_json(HISTORY_DIR / "stock-assistant-query-最新.json", payload)


def render_home() -> str:
    focus = focus_stocks()
    report_state = "已生成" if REPORT_LATEST_PATH.exists() else "未生成"
    candidate_state = "已生成" if CANDIDATE_POOL_LATEST_PATH.exists() else "未生成"
    ledger_state = "已生成" if SYSTEM_JUDGMENT_LEDGER_PATH.exists() and RESULT_VERIFICATION_LEDGER_PATH.exists() else "未生成"
    rows = "\n".join(
        f"<tr><td>{item.get('名称')}</td><td>{item.get('代码')}</td><td>{item.get('优先级','')}</td><td>{item.get('状态','')}</td></tr>"
        for item in focus
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>杰哥股票研究助手</title>
  <style>
    body {{ font-family: "Microsoft YaHei", Arial, sans-serif; margin: 0; background: #f6f7f9; color: #17202a; }}
    header {{ background: #15324b; color: white; padding: 22px 28px; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 22px; }}
    section {{ background: white; border: 1px solid #dce1e7; border-radius: 8px; padding: 18px; margin-bottom: 16px; }}
    textarea {{ width: 100%; min-height: 92px; font-size: 16px; padding: 10px; box-sizing: border-box; }}
    button {{ border: 0; border-radius: 6px; padding: 10px 16px; background: #1f6feb; color: white; cursor: pointer; margin-right: 8px; }}
    pre {{ white-space: pre-wrap; background: #101820; color: #e8f1ff; padding: 14px; border-radius: 8px; min-height: 120px; }}
    .signal-badge {{ display: inline-block; color: white; border-radius: 6px; padding: 6px 10px; font-weight: 700; margin-bottom: 10px; }}
    .signal-visual {{ display: flex; align-items: center; gap: 10px; margin: 8px 0 12px 0; padding: 10px 12px; background: #0f172a; border-radius: 8px; border: 1px solid #243247; }}
    .signal-stars {{ display: inline-flex; gap: 2px; font-size: 28px; line-height: 1; letter-spacing: 0; }}
    .signal-star {{ color: #475569; }}
    .signal-star.buy.full {{ color: #FFD700; }}
    .signal-star.sell.full {{ color: #2E7D32; }}
    .signal-star.half {{ color: transparent; -webkit-background-clip: text; background-clip: text; }}
    .signal-star.half.buy {{ background-image: linear-gradient(90deg, #FFD700 0 50%, #475569 50% 100%); }}
    .signal-star.half.sell {{ background-image: linear-gradient(90deg, #2E7D32 0 50%, #475569 50% 100%); }}
    .signal-level {{ color: #dbeafe; font-weight: 700; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #edf0f3; padding: 8px; text-align: left; }}
    .muted {{ color: #64748b; }}
  </style>
</head>
<body>
  <header>
    <h1>杰哥股票研究助手</h1>
    <div>本地入口 127.0.0.1:19300；重点关注池 {len(focus)} 只；最新报告：{report_state}；候选池：{candidate_state}；复盘账本：{ledger_state}</div>
  </header>
  <main>
    <section>
      <h2>问股票</h2>
      <textarea id="q">分析新易盛 / 我持仓天齐锂业还能不能拿 / 今日推荐 / 帮助</textarea>
      <p>
        <button onclick="ask()">分析</button>
        <button onclick="daily()">运行日常研究</button>
        <button onclick="ledger()">查看复盘账本</button>
        <button onclick="candidate()">查看候选池</button>
        <button onclick="openReport()">查看最新报告</button>
      </p>
      <pre id="out">等待输入...</pre>
      <p class="muted">研究助手只输出分析和风险提示，不接券商接口，不自动交易。</p>
    </section>
    <section>
      <h2>重点关注池</h2>
      <table><thead><tr><th>名称</th><th>代码</th><th>优先级</th><th>状态</th></tr></thead><tbody>{rows}</tbody></table>
    </section>
  </main>
  <script>
    async function post(url, body) {{
      const res = await fetch(url, {{method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(body || {{}})}});
      return await res.json();
    }}
    async function ask() {{
      const out = document.getElementById('out');
      out.textContent = '分析中...';
      const data = await post('/分析', {{问题: document.getElementById('q').value}});
      out.innerHTML = renderReply(data);
    }}
    function escapeHtml(text) {{
      return String(text || '').replace(/[&<>"']/g, function(ch) {{
        return {{'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}}[ch];
      }});
    }}
    function renderReply(data) {{
      const signal = data && data.规则判断 && data.规则判断.研究信号 ? data.规则判断.研究信号 : null;
      const body = escapeHtml(data.回复 || JSON.stringify(data, null, 2));
      if (!signal) return body;
      const color = signal.色值 || '#1565C0';
      const label = escapeHtml(`${{signal.标记 || ''}} ${{signal.方向 || ''}}`);
      const visual = renderSignalVisual(signal);
      return `<span class="signal-badge" style="background:${{color}}">${{label}}</span>${{visual}}\n${{body}}`;
    }}
    function renderSignalVisual(signal) {{
      const value = Number(signal.星级 || 0);
      const direction = String(signal.方向 || '');
      const side = direction.includes('卖出') || direction.includes('风险') ? 'sell' : 'buy';
      const symbol = '⭐';
      let stars = '';
      for (let i = 1; i <= 5; i++) {{
        let cls = 'signal-star';
        if (value >= i) cls += ` ${{side}} full`;
        else if (value > i - 1 && value < i) cls += ` ${{side}} half`;
        stars += `<span class="${{cls}}">${{symbol}}</span>`;
      }}
      const suffix = signal.是否S级 ? '<span class="signal-level">+S</span>' : '';
      return `<div class="signal-visual"><span class="signal-stars">${{stars}}</span>${{suffix}}<span class="signal-level">${{escapeHtml(signal.级别 || '')}} · 强度${{escapeHtml(signal.强度 || '')}}</span></div>`;
    }}
    async function daily() {{
      document.getElementById('out').textContent = '日常研究链路运行中...';
      const data = await post('/日常研究', {{}});
      document.getElementById('out').textContent = JSON.stringify(data, null, 2);
    }}
    async function ledger() {{
      document.getElementById('out').textContent = '读取复盘账本...';
      const res = await fetch('/ledger/latest');
      const data = await res.json();
      document.getElementById('out').textContent = JSON.stringify(data, null, 2);
    }}
    async function candidate() {{
      document.getElementById('out').textContent = '读取候选池...';
      const res = await fetch('/candidate/latest');
      const data = await res.json();
      document.getElementById('out').textContent = JSON.stringify(data, null, 2);
    }}
    function openReport() {{ window.open('/报告/最新', '_blank'); }}
  </script>
</body>
</html>"""


class StockAssistantHandler(BaseHTTPRequestHandler):
    server_version = "JiegeStockAssistant/0.1"

    def _send(self, response: tuple[int, bytes, str]) -> None:
        status, body, content_type = response
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw or "{}")

    def log_message(self, format: str, *args: Any) -> None:
        log_path = HISTORY_DIR / "stock-assistant-service.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {self.address_string()} {format % args}\n"
        with log_path.open("a", encoding="utf-8") as file:
            file.write(line)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        if path == "/":
            self._send(text_response(render_home(), content_type="text/html; charset=utf-8"))
        elif path in {"/帮助", "/help", "/usage"}:
            self._send(json_response(build_usage_help()))
        elif path in {"/今日推荐", "/daily-recommendation", "/recommendation/today"}:
            self._send(json_response(build_daily_recommendation_reply()))
        elif path in {"/专家总览", "/expert-overview"}:
            self._send(json_response(build_expert_overview_reply("专家总览")))
        elif path in {"/系统状态", "/system-status"}:
            self._send(json_response(build_system_status_reply()))
        elif path in {"/模型健康", "/model-health"}:
            self._send(json_response(build_model_health_reply()))
        elif path in {"/公网状态", "/public-callback-status"}:
            self._send(json_response(build_public_callback_reply()))
        elif path in {"/健康", "/health"}:
            config = load_config()
            self._send(json_response({
                "状态": "正常",
                "服务": "杰哥股票研究助手",
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "重点关注池数量": len(focus_stocks()),
                "端口": config.get("服务", {}).get("端口", 19300),
                "旧系统写入": False,
                "交易接口": False,
            }))
        elif path in {"/自选股", "/watchlist"}:
            self._send(json_response({"状态": "完成", "重点关注池": focus_stocks(), "合并股票池": merged_stocks()}))
        elif path in {"/识别", "/recognize"}:
            query = urllib.parse.parse_qs(parsed.query)
            text = str((query.get("文本") or query.get("text") or query.get("股票") or [""])[0])
            self._send(json_response(build_recognition(text)))
        elif path in {"/技术分析", "/technical"}:
            query = urllib.parse.parse_qs(parsed.query)
            text = str((query.get("股票") or query.get("stock") or query.get("代码") or query.get("code") or query.get("文本") or query.get("text") or [""])[0])
            self._send(json_response(build_technical_analysis(text, refresh=False)))
        elif path in {"/历史", "/history"}:
            latest = load_json(HISTORY_DIR / "stock-assistant-query-最新.json", {}) or {}
            self._send(json_response({"状态": "完成", "最近一次": latest}))
        elif path in {"/快照/最新", "/snapshot/latest"}:
            self._send(json_response(latest_quote_snapshot(refresh=False)))
        elif path in {"/数据健康度", "/data-health"}:
            self._send(json_response(latest_data_health()))
        elif path in {"/状态摘要", "/status-summary"}:
            self._send(json_response({"状态": "完成", "状态摘要": load_json(STATUS_SUMMARY_JSON_LATEST_PATH, {}) or {}}))
        elif path in {"/图形报告/最新", "/图形报告/最新.svg", "/card/latest", "/card/latest.svg"}:
            if CARD_LATEST_SVG_PATH.exists():
                self._send(text_response(CARD_LATEST_SVG_PATH.read_text(encoding="utf-8"), content_type="image/svg+xml; charset=utf-8"))
            else:
                self._send(text_response("股票图形报告尚未生成。", status=404))
        elif path in {"/图形报告/最新.png", "/card/latest.png"}:
            if CARD_LATEST_PNG_PATH.exists():
                self._send((200, CARD_LATEST_PNG_PATH.read_bytes(), "image/png"))
            else:
                self._send(text_response("股票PNG图形报告尚未生成。", status=404))
        elif path in {"/图形报告/本次.png", "/card/report.png"}:
            query = urllib.parse.parse_qs(parsed.query)
            name = Path(str((query.get("name") or [""])[0])).name
            target = CARD_DIR / name
            if name and target.exists() and target.suffix.lower() == ".png" and target.parent == CARD_DIR:
                self._send((200, target.read_bytes(), "image/png"))
            else:
                self._send(text_response("指定股票PNG图形报告不存在。", status=404))
        elif path in {"/图形报告/星级图标.png", "/card/signal-icon.png"}:
            if CARD_LATEST_ICON_PATH.exists():
                self._send((200, CARD_LATEST_ICON_PATH.read_bytes(), "image/png"))
            else:
                self._send(text_response("股票星级图标尚未生成。", status=404))
        elif path in {"/图形报告/元数据", "/card/latest.json"}:
            self._send(json_response({"状态": "完成", "图形报告": load_json(CARD_LATEST_JSON_PATH, {}) or {}}))
        elif path in {"/状态摘要/报告", "/status-summary/report"}:
            if STATUS_SUMMARY_MD_LATEST_PATH.exists():
                self._send(text_response(STATUS_SUMMARY_MD_LATEST_PATH.read_text(encoding="utf-8"), content_type="text/markdown; charset=utf-8"))
            else:
                self._send(text_response("股票研究系统状态摘要尚未生成。", status=404))
        elif path in {"/日常包", "/daily-package"}:
            self._send(json_response({"状态": "完成", "日常使用包": load_json(DAILY_PACKAGE_JSON_LATEST_PATH, {}) or {}}))
        elif path in {"/日常包/报告", "/daily-package/report"}:
            if DAILY_PACKAGE_MD_LATEST_PATH.exists():
                self._send(text_response(DAILY_PACKAGE_MD_LATEST_PATH.read_text(encoding="utf-8"), content_type="text/markdown; charset=utf-8"))
            else:
                self._send(text_response("股票研究日常使用包尚未生成。", status=404))
        elif path in {"/报告/最新", "/report/latest"}:
            if REPORT_LATEST_PATH.exists():
                self._send(text_response(REPORT_LATEST_PATH.read_text(encoding="utf-8"), content_type="text/markdown; charset=utf-8"))
            else:
                self._send(text_response("最新研究报告尚未生成。", status=404))
        elif path in {"/候选池/最新", "/candidate/latest"}:
            self._send(json_response({"状态": "完成", "候选池": load_json(CANDIDATE_POOL_LATEST_PATH, {}) or {}}))
        elif path in {"/候选池/报告", "/candidate/report"}:
            if CANDIDATE_REPORT_LATEST_PATH.exists():
                self._send(text_response(CANDIDATE_REPORT_LATEST_PATH.read_text(encoding="utf-8"), content_type="text/markdown; charset=utf-8"))
            else:
                self._send(text_response("候选池报告尚未生成。", status=404))
        elif path in {"/深度研究/最新", "/l5/latest"}:
            self._send(json_response({"状态": "完成", "L5深度研究": load_json(L5_RESEARCH_JSON_LATEST_PATH, {}) or {}}))
        elif path in {"/深度研究/报告", "/l5/report"}:
            if L5_RESEARCH_REPORT_LATEST_PATH.exists():
                self._send(text_response(L5_RESEARCH_REPORT_LATEST_PATH.read_text(encoding="utf-8"), content_type="text/markdown; charset=utf-8"))
            else:
                self._send(text_response("L5深度研究日报尚未生成。", status=404))
        elif path in {"/账本/最新", "/ledger/latest"}:
            self._send(json_response({"状态": "完成", "复盘账本": latest_ledgers()}))
        elif path in {"/账本/系统判断", "/ledger/system"}:
            self._send(json_response({"状态": "完成", "系统判断账": load_json(SYSTEM_JUDGMENT_LEDGER_PATH, {}) or {}}))
        elif path in {"/账本/人工决策", "/ledger/human"}:
            self._send(json_response({"状态": "完成", "人工决策账模板": load_json(HUMAN_DECISION_LEDGER_PATH, {}) or {}}))
        elif path in {"/账本/结果验证", "/ledger/verification"}:
            self._send(json_response({"状态": "完成", "结果验证计划": load_json(RESULT_VERIFICATION_LEDGER_PATH, {}) or {}}))
        elif path in {"/账本/经验提炼", "/ledger/experience"}:
            self._send(json_response({"状态": "完成", "经验提炼候选账": load_json(EXPERIENCE_CANDIDATE_LEDGER_PATH, {}) or {}}))
        else:
            self._send(json_response({"状态": "未找到", "路径": path}, status=404))

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        try:
            body = self._body_json()
            if path in {"/分析", "/analyze"}:
                question = str(body.get("问题") or body.get("question") or body.get("股票") or "")
                remember_context = not bool(body.get("不记录上下文") or body.get("no_context") or body.get("skip_context"))
                entrance_role = str(body.get("入口角色") or body.get("role") or body.get("角色") or "助手")
                self._send(json_response(build_analysis(question, refresh=True, remember_context=remember_context, entrance_role=entrance_role)))
            elif path in {"/识别", "/recognize"}:
                text = str(body.get("文本") or body.get("text") or body.get("问题") or body.get("question") or body.get("股票") or "")
                self._send(json_response(build_recognition(text)))
            elif path in {"/技术分析", "/technical"}:
                text = str(body.get("股票") or body.get("stock") or body.get("代码") or body.get("code") or body.get("文本") or body.get("text") or body.get("问题") or body.get("question") or "")
                self._send(json_response(build_technical_analysis(text, refresh=True)))
            elif path in {"/行情", "/quote"}:
                snapshot = latest_quote_snapshot(refresh=True)
                stock = find_stock(str(body.get("问题") or body.get("股票") or body.get("代码") or ""))
                if stock:
                    self._send(json_response({"状态": "完成", "股票": stock, "行情": find_quote(stock, snapshot), "快照": str(QUOTE_LATEST_PATH)}))
                else:
                    self._send(json_response(snapshot))
            elif path in {"/日常研究", "/daily"}:
                daily = run_script("运行股票日常研究链路.py", timeout=180)
                quote = run_script("生成重点关注池公开行情快照.py", timeout=60)
                self._send(json_response({"状态": "完成" if daily["返回码"] == 0 and quote["返回码"] == 0 else "部分失败", "日常研究": daily, "行情快照": quote}))
            elif path in {"/账本/生成", "/ledger/generate"}:
                judgment = run_script("记录系统判断账.py", timeout=120)
                human = run_script("生成人工决策账模板.py", timeout=120)
                verification = run_script("生成结果验证计划.py", timeout=120)
                experience = run_script("生成经验提炼候选账.py", timeout=120)
                ok = all(item["返回码"] == 0 for item in [judgment, human, verification, experience])
                self._send(json_response({
                    "状态": "完成" if ok else "部分失败",
                    "系统判断账": judgment,
                    "人工决策账模板": human,
                    "结果验证计划": verification,
                    "经验提炼候选账": experience
                }))
            elif path in {"/候选池/生成", "/candidate/generate"}:
                technical = run_script("验证技术指标计算链路.py", timeout=300)
                candidate = run_script("生成重点关注池候选池.py", timeout=120)
                ok = technical["返回码"] == 0 and candidate["返回码"] == 0
                self._send(json_response({
                    "状态": "完成" if ok else "部分失败",
                    "技术指标链路": technical,
                    "候选池生成": candidate
                }))
            elif path in {"/深度研究/生成", "/l5/generate"}:
                candidate = run_script("生成重点关注池候选池.py", timeout=120)
                report = run_script("生成L5深度研究报告.py", timeout=120)
                ok = candidate["返回码"] == 0 and report["返回码"] == 0
                self._send(json_response({
                    "状态": "完成" if ok else "部分失败",
                    "候选池生成": candidate,
                    "L5深度研究报告": report
                }))
            elif path in {"/日常包/生成", "/daily-package/generate"}:
                status = run_script("生成股票研究系统状态摘要.py", timeout=120)
                package = run_script("生成股票日常使用包.py", timeout=120)
                ok = status["返回码"] == 0 and package["返回码"] == 0
                self._send(json_response({
                    "状态": "完成" if ok else "部分失败",
                    "状态摘要": status,
                    "日常使用包": package
                }))
            elif path in {"/复盘联动/运行", "/review-loop/run"}:
                review_loop = run_script("运行L5日报复盘联动链路.py", timeout=240)
                self._send(json_response({
                    "状态": "完成" if review_loop["返回码"] == 0 else "部分失败",
                    "L5复盘联动": review_loop
                }))
            elif path in {"/反馈", "/feedback"}:
                feedback_text = str(body.get("反馈") or body.get("feedback") or body.get("内容") or "")
                feedback_script = ROOT / "02脚本" / "记录人工反馈到决策账.py"
                env = dict(os.environ)
                env["PYTHONIOENCODING"] = "utf-8"
                result = subprocess.run(
                    [sys.executable, str(feedback_script), "--feedback", feedback_text],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=env,
                    timeout=120,
                )
                self._send(json_response({
                    "状态": "完成" if result.returncode == 0 else "待人工补充",
                    "返回码": result.returncode,
                    "标准输出": result.stdout.strip(),
                    "标准错误": result.stderr.strip()
                }))
            else:
                self._send(json_response({"状态": "未找到", "路径": path}, status=404))
        except Exception as exc:  # noqa: BLE001
            self._send(json_response({"状态": "失败", "错误": str(exc)}, status=500))


def main() -> int:
    if len(sys.argv) > 1:
        args = [arg for arg in sys.argv[1:] if arg not in {"--json", "--refresh"}]
        question = " ".join(args).strip()
        if not question:
            print("请输入问题，例如：python 股票助手入口.py 分析天齐锂业", flush=True)
            return 2
        result = build_analysis(question, refresh="--refresh" in sys.argv[1:])
        if "--json" in sys.argv[1:]:
            print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        else:
            print(result.get("企业微信回复") or result.get("回复") or json.dumps(result, ensure_ascii=False), flush=True)
        return 0

    config = load_config()
    service = config.get("服务", {})
    host = service.get("地址", "127.0.0.1")
    port = int(service.get("端口", 19300))
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), StockAssistantHandler)
    print(json.dumps({"status": "started", "home": f"http://{host}:{port}/", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, ensure_ascii=True), flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

