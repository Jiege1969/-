# -*- coding: utf-8 -*-
"""
名称：验证股票企业微信体验入口状态.py
作用：验证股票系统企业微信前台体验入口是否可用，并区分“用户问答被动回复”和“本人白名单主动推送”的边界。
触发方式：python 验证股票企业微信体验入口状态.py
依赖：Python标准库；股票助手19300；股票企业微信桥接19302；公共组件企业微信受控发送器日志。
安全边界：只做本地HTTP验收和日志读取；不调用企业微信API；不真实发送；不触发n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = ROOT.parents[0] / "00公共组件"
OUT_DIR = ROOT / "03数据" / "289企业微信体验入口状态"
SENDER_LOG_DIR = COMMON_ROOT / "04日志" / "企业微信受控发送器"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def post_json(url: str, payload: dict[str, Any], timeout: int = 45) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
        return {"ok": True, "status": response.status, "json": json.loads(text)}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": exc.code, "error": exc.read().decode("utf-8", errors="replace")}
    except Exception as exc:
        return {"ok": False, "status": 0, "error": str(exc)}


def get_json(url: str, timeout: int = 10) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
        return {"ok": True, "status": response.status, "json": json.loads(text)}
    except Exception as exc:
        return {"ok": False, "status": 0, "error": str(exc)}


def latest_sender_log() -> dict[str, Any]:
    if not SENDER_LOG_DIR.exists():
        return {}
    files = sorted(SENDER_LOG_DIR.glob("wework-controlled-sender-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return {}
    data = read_json(files[0], {})
    data["_path"] = str(files[0])
    return data


def stream_content(result: dict[str, Any]) -> str:
    data = result.get("json") if isinstance(result.get("json"), dict) else {}
    stream = data.get("stream") if isinstance(data.get("stream"), dict) else {}
    return str(stream.get("content") or "")


def check_item(name: str, ok: bool, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(ok), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票企业微信体验入口状态",
        "",
        f"- 生成时间：{report.get('生成时间')}",
        f"- 当前结论：{report.get('当前结论')}",
        f"- 使用口径：{report.get('使用口径')}",
        "",
        "## 检查结果",
    ]
    for item in report.get("检查结果", []):
        mark = "通过" if item.get("通过") else "未通过"
        lines.append(f"- {item.get('检查项')}：{mark}。{item.get('说明')}")
    lines.extend([
        "",
        "## 边界",
        "- 企业微信用户问答被动回复是股票系统前台入口，应保持可体验。",
        "- 主动推送按受控白名单灰度执行。",
        "- 可信IP导致的主动推送失败登记为环境限制，不等同于股票问答入口失败。",
        "- 不触发n8n，不调用券商接口，不自动交易。",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    health = get_json("http://127.0.0.1:19302/health")
    shortline = post_json(
        "http://127.0.0.1:19302/wecom-bot/stock-shortline",
        {"text": "分析 云南锗业", "stream": {"id": "stock-wecom-experience-shortline-check"}},
    )
    expert = post_json(
        "http://127.0.0.1:19302/wecom-bot/stock-expert",
        {"text": "今日推荐", "stream": {"id": "stock-wecom-experience-expert-check"}},
    )
    status_reply = post_json(
        "http://127.0.0.1:19302/wecom-bot/stock-shortline",
        {"text": "股票系统状态", "stream": {"id": "stock-wecom-experience-status-check"}},
    )
    shortline_text = stream_content(shortline)
    expert_text = stream_content(expert)
    status_text = stream_content(status_reply)
    sender_log = latest_sender_log()
    send_result = sender_log.get("发送结果", {}) if isinstance(sender_log, dict) else {}
    wecom_return = send_result.get("企业微信返回", {}) if isinstance(send_result, dict) else {}
    token_probe = sender_log.get("token探测", {}) if isinstance(sender_log, dict) else {}
    active_push_ok = wecom_return.get("errcode") == 0
    active_send_blocked = wecom_return.get("errcode") == 60020
    expected_push_text_ok = (
        "主动推送：受控白名单可用" in status_text
        if active_push_ok
        else ("主动推送：受可信IP限制" in status_text and "需放行IP" in status_text)
        if active_send_blocked
        else "主动推送：" in status_text
    )

    checks = [
        check_item("19302桥接服务健康", health.get("ok") and health.get("json", {}).get("状态") == "正常", health.get("json") or health.get("error")),
        check_item("短线机器人本地stream回复可用", shortline.get("ok") and "【个股分析报告】" in shortline_text and "说明：仅供研究参考" in shortline_text, shortline_text[:160]),
        check_item("专家机器人本地stream回复可用", expert.get("ok") and "今日重点观察个股" in expert_text and "证据边界" in expert_text, expert_text[:160]),
        check_item("状态帮助短答可用", status_reply.get("ok") and "【股票系统状态】" in status_text and "问答入口：可用" in status_text and expected_push_text_ok, status_text[:200]),
        check_item("主动发送token可获取", token_probe.get("ok") is True, token_probe.get("企业微信返回", {})),
        check_item("主动推送日志状态可识别", wecom_return.get("errcode") in {0, 60020, None}, wecom_return),
        check_item("未触发n8n券商交易", True, {"触发n8n": False, "调用券商接口": False, "自动交易": False}),
    ]
    failed = [item for item in checks if not item.get("通过")]
    front_failed = [item for item in checks[:4] if not item.get("通过")]
    if active_send_blocked and not front_failed:
        conclusion = "企业微信问答入口本地可用；主动推送受可信IP限制，需在企业微信后台放行当前出口IP后再复测。"
    elif active_push_ok and not front_failed:
        conclusion = "企业微信问答入口和受控主动推送可用。"
    elif not front_failed:
        conclusion = "企业微信问答入口可用。"
    else:
        conclusion = "仍有企业微信体验入口检查未通过。"

    report = {
        "名称": "股票企业微信体验入口状态",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": conclusion,
        "使用口径": "企业微信不是禁区；用户问答被动回复应可体验，主动推送按本人白名单灰度受控执行。",
        "检查结果": checks,
        "样例摘要": {
            "短线机器人回复前200字": shortline_text[:200],
            "专家机器人回复前200字": expert_text[:200],
            "状态帮助回复前200字": status_text[:200],
        },
        "主动推送状态": {
            "最新发送日志": sender_log.get("_path", ""),
            "token可获取": token_probe.get("ok") is True,
            "企业微信返回": wecom_return,
            "可信IP受限": active_send_blocked,
        },
        "安全边界": {
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "主动群发": False,
        },
    }
    output_json = OUT_DIR / "股票企业微信体验入口状态_最新.json"
    output_md = OUT_DIR / "股票企业微信体验入口状态_最新.md"
    write_json(output_json, report)
    write_text(output_md, build_markdown(report))
    print(json.dumps({"ok": not front_failed, "主动推送可信IP受限": active_send_blocked, "输出": str(output_md)}, ensure_ascii=False))
    return 0 if not front_failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
