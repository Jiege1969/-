# -*- coding: utf-8 -*-
"""
名称：验证股票系统交付使用版总验收.py
作用：汇总验证股票系统交付使用版的本地入口、桥接入口、智能机器人stream入口、PNG图形报告、星级小图标、公网回调、交易拦截、response_url闭环、n8n未激活入口和可信IP状态。
触发方式：python 验证股票系统交付使用版总验收.py
依赖：Python标准库；股票助手19300；股票企业微信桥接19302；v3 n8n；相关验收日志。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读状态和本地dry-run请求；不启用n8n；不发送企业微信；不写旧系统；不写正式库；不交易。
创建修改记录：2026-04-29 创建交付使用版总验收脚本；纳入旧系统验证过的智能机器人stream回复入口；纳入公网回调交付检查；2026-04-29 纳入PNG图形报告和企业微信图片语法验收；2026-04-29 纳入企业微信彩色星级字符验收；2026-04-29 纳入星级小图标兜底验收；2026-04-30 验收企业微信图形报告置顶和⭐金色/绿色信号格式；2026-04-30 精简为单主图回复，取消星级小图重复展示；2026-04-30 验收企业微信图片绑定本次报告文件，避免桌面端缓存latest旧图。
"""

from __future__ import annotations

import json
import importlib.util
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "04日志" / "股票系统交付使用版总验收"
IP_STATUS = ROOT / "03数据" / "85企业微信可信IP放行状态" / "企业微信可信IP放行状态_最新.json"
RESPONSE_LOOPBACK = ROOT / "04日志" / "企业微信响应URL本地闭环" / "stock-response-url-local-loopback-verify-最新.json"
PUBLIC_CALLBACK = ROOT / "04日志" / "公网回调验证" / "public-callback-encrypted-verify-latest.json"
PUBLIC_STATUS_SCRIPT = ROOT / "02脚本" / "查看股票公网回调状态.ps1"
STOCK_ASSISTANT_SCRIPT = ROOT / "02脚本" / "股票助手入口.py"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def get_json(url: str, timeout: int = 5) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def get_binary_info(url: str, timeout: int = 8) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        body = response.read()
        return {
            "状态码": response.status,
            "内容类型": response.headers.get("Content-Type", ""),
            "字节数": len(body),
        }


def post_json(url: str, payload: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def post_json_timed(url: str, payload: dict[str, Any], timeout: int = 20) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    result = post_json(url, payload, timeout=timeout)
    return result, round(time.perf_counter() - started, 3)


def run(args: list[str], timeout: int = 120) -> tuple[int, str, str]:
    completed = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return completed.returncode, completed.stdout, completed.stderr


def n8n_bridge_workflow_present() -> bool:
    code, stdout, _ = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=false"], timeout=120)
    return code == 0 and "股票助手企业微信Webhook桥接入口未激活v2" in stdout


def n8n_no_active_stock_workflow() -> bool:
    code, stdout, _ = run(["docker", "exec", "jiege_v3_n8n", "n8n", "list:workflow", "--active=true"], timeout=120)
    return code == 0 and "股票助手" not in stdout


def public_callback_status() -> dict[str, Any]:
    """读取公网回调隧道状态脚本结果。"""
    code, stdout, stderr = run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PUBLIC_STATUS_SCRIPT)],
        timeout=60,
    )
    if code != 0:
        return {"status": "script_failed", "stdout": stdout, "stderr": stderr}
    try:
        parsed = json.loads(stdout)
        return parsed if isinstance(parsed, dict) else {"status": "invalid_output", "stdout": stdout}
    except Exception:
        return {"status": "parse_failed", "stdout": stdout, "stderr": stderr}


def stock_signal_color_contract() -> dict[str, bool]:
    """直接验证星级函数的机会星和风险星契约，避免回复层退化。"""
    spec = importlib.util.spec_from_file_location("stock_assistant_entry_for_acceptance", STOCK_ASSISTANT_SCRIPT)
    if spec is None or spec.loader is None:
        return {"红色机会星": False, "绿色风险星": False}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    opportunity = module.build_research_signal(88, "L5深度研究", [])
    risk = module.build_research_signal(10, "L7风险观察", ["破位"])
    return {
        "机会星": opportunity.get("企业微信标记") == "⭐⭐⭐⭐⭐",
        "风险星": risk.get("企业微信标记") == "⭐⭐⭐⭐⭐",
        "停用HTML彩色标记": "font" not in str(opportunity.get("企业微信标记")) and "font" not in str(risk.get("企业微信标记")),
    }


def main() -> int:
    stock_health = get_json("http://127.0.0.1:19300/health")
    bridge_health = get_json("http://127.0.0.1:19302/health")
    stock_reply = post_json("http://127.0.0.1:19302/wecom/stock", {"text": "分析云南锗业"})
    bot_stream_reply, bot_stream_seconds = post_json_timed("http://127.0.0.1:19302/wecom-bot/message", {"text": "分析云南锗业", "stream": {"id": "acceptance-stream-test"}}, timeout=60)
    fast_ack_reply, fast_ack_seconds = post_json_timed("http://127.0.0.1:19302/wecom-bot/message", {"text": "分析002929", "response_url": "http://127.0.0.1:9/mock-response-url", "stream": {"id": "acceptance-fast-ack-test"}}, timeout=8)
    trade_block = post_json("http://127.0.0.1:19302/wecom/stock", {"text": "帮我买入贵州茅台"})
    local_png = get_binary_info("http://127.0.0.1:19300/card/latest.png")
    bridge_png = get_binary_info("http://127.0.0.1:19302/wecom-bot/message?card=latest_png")
    local_icon = get_binary_info("http://127.0.0.1:19300/card/signal-icon.png")
    bridge_icon = get_binary_info("http://127.0.0.1:19302/wecom-bot/message?card=signal_icon")
    response_loopback = load_json(RESPONSE_LOOPBACK, {})
    ip_status = load_json(IP_STATUS, {})
    public_callback = load_json(PUBLIC_CALLBACK, {})
    public_status = public_callback_status()
    signal_contract = stock_signal_color_contract()
    stream_content = str(bot_stream_reply.get("stream", {}).get("content", ""))
    fast_ack_content = str(fast_ack_reply.get("stream", {}).get("content", ""))
    image_pos = stream_content.find("![股票图形报告]")
    conclusion_pos = stream_content.find("结论：")
    checks = [
        {"检查项": "股票助手19300健康", "通过": stock_health.get("状态") == "正常"},
        {"检查项": "桥接入口19302健康", "通过": bridge_health.get("状态") == "正常"},
        {"检查项": "桥接查询可返回L3结论型分析", "通过": stock_reply.get("股票助手状态") == "完成" and "云南锗业" in str(stock_reply.get("回复", "")) and "结论：" in str(stock_reply.get("回复", ""))},
        {"检查项": "智能机器人stream入口可直接返回企业微信stream", "通过": bot_stream_reply.get("msgtype") == "stream" and "云南锗业" in stream_content and "【个股分析报告】" in stream_content and "一、先说结论" in stream_content},
        {"检查项": "智能机器人完整同步分析小于20秒", "通过": bot_stream_seconds <= 20},
        {"检查项": "短线助手response_url快速回执小于3秒", "通过": fast_ack_reply.get("msgtype") == "stream" and fast_ack_reply.get("stream", {}).get("finish") is False and fast_ack_seconds <= 3 and "已收到" in fast_ack_content},
        {"检查项": "企业微信回复不使用买入机会和HTML标签", "通过": "买入机会研究信号" not in stream_content and "<font" not in stream_content},
        {"检查项": "星级函数同时支持机会星和风险星纯文本", "通过": signal_contract.get("机会星") and signal_contract.get("风险星") and signal_contract.get("停用HTML彩色标记")},
        {"检查项": "智能机器人回复不重复展示星级小图标", "通过": "![研究星级图标]" not in stream_content and "card=signal_icon" not in stream_content},
        {"检查项": "智能机器人回复包含本次PNG图片语法", "通过": "![股票图形报告]" in stream_content and "card=report_png" in stream_content and "name=" in stream_content},
        {"检查项": "图形报告置顶后再显示分析报告正文", "通过": 0 <= image_pos < conclusion_pos},
        {"检查项": "前台详情不裸露图形和详细报告URL行", "通过": "图形报告：http" not in stream_content and "详细图文报告：http" not in stream_content},
        {"检查项": "企业微信回复包含用户模板版结论报告结构", "通过": all(part in stream_content for part in ["分析对象：", "【个股分析报告】", "一、先说结论", "二、重新关注时机", "三、关键价位对照表", "四、通俗风险说明", "五、行业和基本面快照", "六、后续只盯这3件事"]) and all(part not in stream_content for part in ["当前判断：", "操作策略：", "关注条件：", "转强条件：", "成交标准：", "图文详情："])},
        {"检查项": "股票助手PNG图形报告可访问", "通过": local_png.get("状态码") == 200 and "image/png" in local_png.get("内容类型", "") and local_png.get("字节数", 0) > 10000},
        {"检查项": "桥接PNG公网代理可访问", "通过": bridge_png.get("状态码") == 200 and "image/png" in bridge_png.get("内容类型", "") and bridge_png.get("字节数", 0) > 10000},
        {"检查项": "股票助手星级小图标可访问", "通过": local_icon.get("状态码") == 200 and "image/png" in local_icon.get("内容类型", "") and local_icon.get("字节数", 0) > 1000},
        {"检查项": "桥接星级小图标公网代理可访问", "通过": bridge_icon.get("状态码") == 200 and "image/png" in bridge_icon.get("内容类型", "") and bridge_icon.get("字节数", 0) > 1000},
        {"检查项": "公网回调隧道运行且可达", "通过": public_status.get("status") == "ready"},
        {"检查项": "公网加密回调验收通过", "通过": public_callback.get("失败", public_callback.get("failed", 1)) == 0 and public_callback.get("通过", public_callback.get("passed", 0)) >= 4},
        {"检查项": "交易指令已拦截", "通过": trade_block.get("股票助手状态") == "已拦截" and "不执行任何交易指令" in str(trade_block.get("回复", ""))},
        {"检查项": "response_url本地闭环通过", "通过": response_loopback.get("失败") == 0 and response_loopback.get("通过", 0) >= 5},
        {"检查项": "n8n桥接入口v2未激活存在", "通过": n8n_bridge_workflow_present()},
        {"检查项": "n8n无股票active工作流", "通过": n8n_no_active_stock_workflow()},
        {"检查项": "可信IP状态已记录", "通过": ip_status.get("状态") in {"需放行可信IP", "未检测到可信IP阻断"}},
    ]
    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查结果": checks,
        "公网回调状态": public_status,
        "星级颜色契约": signal_contract,
        "性能计时": {
            "智能机器人完整同步秒": bot_stream_seconds,
            "response_url快速回执秒": fast_ack_seconds,
        },
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "当前结论": "股票系统交付使用版已具备本地、桥接、公网智能机器人加密回调能力；应用消息仍取决于可信IP放行。" if not failed else "仍有交付项未通过。",
        "安全边界": {
            "启用n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = LOG_DIR / f"stock-delivery-total-acceptance-{stamp}.json"
    latest = LOG_DIR / "stock-delivery-total-acceptance-最新.json"
    write_json(output, result)
    write_json(latest, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
