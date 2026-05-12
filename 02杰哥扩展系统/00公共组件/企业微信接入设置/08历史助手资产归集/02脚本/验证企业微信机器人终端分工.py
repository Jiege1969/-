# -*- coding: utf-8 -*-
"""
验证企业微信机器人终端分工。

只做本地回环和配置核验；不发送企业微信，不触发n8n，不调用OpenClaw，不调用券商接口。
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EXT_ROOT = Path(__file__).resolve().parents[2]
WECOM_ROOT = EXT_ROOT / "06企业微信助手系统"
STOCK_ROOT = EXT_ROOT / "01股票研究系统"
CONFIG = WECOM_ROOT / "01配置" / "企业微信机器人终端分工总表.json"
TOTAL = WECOM_ROOT / "01配置" / "企业微信助手总表.json"
DOC = WECOM_ROOT / "07文档" / "企业微信机器人终端分工与输入输出机制.md"
LOG_DIR = WECOM_ROOT / "04日志" / "企业微信机器人终端分工"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def post_json(url: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def get_json(url: str, timeout: int = 10) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def stream_content(result: dict[str, Any]) -> str:
    reply = result.get("智能机器人回复", {})
    if isinstance(reply, dict):
        stream = reply.get("stream", {})
        if isinstance(stream, dict):
            return str(stream.get("content") or "")
    return str(result.get("企业微信内容") or result.get("回复") or "")


def check(name: str, passed: bool, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(passed), "详情": detail}


def main() -> int:
    checks: list[dict[str, Any]] = []
    config = read_json(CONFIG)
    total = read_json(TOTAL)
    names = [str(item.get("名称") or "") for item in config.get("终端列表", [])]
    total_names = [str(item.get("名称") or "") for item in total.get("助手列表", [])]
    required = ["杰哥股票分析助手", "杰哥的股票分析专家", "杰哥系统管家", "杰哥工作秘书", "杰哥视频助理"]

    checks.append(check("终端分工总表存在", CONFIG.exists(), str(CONFIG)))
    checks.append(check("企业微信助手总表已纳入股票双入口", all(name in total_names for name in required[:2]), total_names))
    checks.append(check("五个企业微信终端全部登记", all(name in names for name in required), names))
    checks.append(check("机制说明文档存在", DOC.exists() and "企业微信机器人终端分工" in DOC.read_text(encoding="utf-8"), str(DOC)))
    checks.append(check("总表不展开Secret明文", "Secret" not in CONFIG.read_text(encoding="utf-8"), str(CONFIG)))

    try:
        health = get_json("http://127.0.0.1:19302/health")
        checks.append(check("股票企业微信桥接入口健康", health.get("状态") == "正常", health))
    except Exception as exc:
        health = {"错误": str(exc)}
        checks.append(check("股票企业微信桥接入口健康", False, str(exc)))

    try:
        assistant_result = post_json(
            "http://127.0.0.1:19302/wecom-bot/message",
            {"text": "分析天齐锂业", "stream": {"id": "wecom-terminal-division-assistant"}},
        )
        assistant_text = stream_content(assistant_result)
        assistant_terms = ["![股票图形报告]", "当前判断", "操作策略", "关注条件", "转强条件", "风险线", "图文详情"]
        checks.append(check("股票助手显示符合个股短答要求", all(term in assistant_text for term in assistant_terms), assistant_text[:700]))
    except Exception as exc:
        assistant_text = ""
        checks.append(check("股票助手显示符合个股短答要求", False, str(exc)))

    try:
        expert_result = post_json(
            "http://127.0.0.1:19302/wecom-bot/message",
            {"text": "推荐几只股票", "stream": {"id": "wecom-terminal-division-expert"}},
        )
        expert_text = stream_content(expert_result)
        expert_terms = ["完整图文报告", "专家总览", "重点关注", "观察股票", "主要方向", "证据边界"]
        checks.append(check("股票专家显示符合推荐总览要求", all(term in expert_text for term in expert_terms), expert_text[:700]))
    except Exception as exc:
        expert_text = ""
        checks.append(check("股票专家显示符合推荐总览要求", False, str(exc)))

    try:
        trade_result = post_json(
            "http://127.0.0.1:19302/wecom-bot/message",
            {"text": "帮我买入贵州茅台", "stream": {"id": "wecom-terminal-division-trade-block"}},
        )
        trade_text = stream_content(trade_result)
        action = trade_result.get("实际动作", {})
        checks.append(
            check(
                "交易类输入被终端拦截",
                "已拦截" in trade_text
                and action.get("调用股票助手") is False
                and action.get("调用券商接口") is False
                and action.get("自动交易") is False,
                {"回复": trade_text, "实际动作": action},
            )
        )
    except Exception as exc:
        checks.append(check("交易类输入被终端拦截", False, str(exc)))

    passed = sum(1 for item in checks if item["通过"])
    failed = [item for item in checks if not item["通过"]]
    result = {
        "名称": "企业微信机器人终端分工验收",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": not failed,
        "通过数量": passed,
        "总数量": len(checks),
        "检查项": checks,
        "当前结论": "企业微信机器人终端分工机制已建立，股票助手/专家显示符合当前设置要求。" if not failed else "企业微信机器人终端分工仍有未通过项。",
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "调用OpenClaw": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    latest = LOG_DIR / "wecom-terminal-division-verify-最新.json"
    text = json.dumps(result, ensure_ascii=False, indent=2)
    latest.write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["通过"] else 1


if __name__ == "__main__":
    sys.exit(main())
