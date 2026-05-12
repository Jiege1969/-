# -*- coding: utf-8 -*-
"""
名称：执行企业微信公共接入层日常只读巡检.py
作用：快速确认19310企业微信总入口日常可用状态，覆盖health、税收工作秘书、职责分流、视频阻断和安全边界。
触发方式：python 执行企业微信公共接入层日常只读巡检.py
安全边界：只请求127.0.0.1:19310本地入口；19302只读取端口状态，不请求股票业务接口；不真实发送企业微信；不触发n8n；不重载服务。
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


SERVICE = "http://127.0.0.1:19310"
OLD_STOCK_WORDS = ["重点推荐", "常规推荐", "买入研究信号", "卖出研究信号", "加仓", "减仓", "满仓", "清仓", "仓位"]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
OUTPUT_DIR = ROOT / "03数据" / "15日常可用版只读巡检包"
LATEST_JSON = OUTPUT_DIR / "企业微信公共接入层日常只读巡检_最新.json"
LATEST_MD = OUTPUT_DIR / "企业微信公共接入层日常只读巡检_最新.md"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def http_get_json(path: str, text: str = "", timeout: int = 30) -> dict[str, Any]:
    url = f"{SERVICE}{path}"
    if text:
        url += "?text=" + urllib.parse.quote(text)
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def port_status(port: int) -> dict[str, Any]:
    command = (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        f"$conns=Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue; "
        "$rows=@(); "
        "foreach($c in $conns){"
        "$p=Get-CimInstance Win32_Process -Filter \"ProcessId=$($c.OwningProcess)\" -ErrorAction SilentlyContinue; "
        "$rows += [pscustomobject]@{LocalPort=$c.LocalPort;State=\"$($c.State)\";OwningProcess=$c.OwningProcess;ProcessName=$p.Name;CommandLine=$p.CommandLine}"
        "}; "
        "$rows | ConvertTo-Json -Depth 4"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    raw = completed.stdout.strip()
    if not raw:
        return {"端口": port, "记录": [], "错误": completed.stderr.strip()}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"端口": port, "记录": [], "错误": completed.stderr.strip() or raw}
    rows = data if isinstance(data, list) else [data]
    return {"端口": port, "记录": rows, "错误": completed.stderr.strip()}


def check(name: str, passed: bool, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "结果": "pass" if passed else "fail", "详情": detail}


def reply_text(payload: dict[str, Any]) -> str:
    return str(payload.get("reply_text") or payload.get("回复") or payload.get("message") or json.dumps(payload, ensure_ascii=False))


def safety_value(payload: dict[str, Any], key: str) -> Any:
    safety = payload.get("安全边界", {})
    if key == "real_send":
        return payload.get("real_send") if "real_send" in payload else safety.get("真实发送企业微信")
    if key == "触发n8n":
        return safety.get("触发n8n")
    return safety.get(key)


def lines_title_and_subject(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    title = next((line for line in lines if line.startswith("【")), "")
    subject = next((line.replace("事项：", "", 1) for line in lines if line.startswith("事项：")), "")
    return title, subject


def run_patrol() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    samples: dict[str, Any] = {}
    reload_required: list[str] = []

    port_19310 = port_status(19310)
    port_19302 = port_status(19302)
    listen_19310 = [row for row in port_19310.get("记录", []) if str(row.get("State")) == "Listen"]
    listen_19302 = [row for row in port_19302.get("记录", []) if str(row.get("State")) == "Listen"]
    checks.append(check("19310端口监听", bool(listen_19310), port_19310))
    checks.append(check("19302仅记录端口状态，不请求业务接口", True, {"监听记录": listen_19302, "说明": "本巡检不访问19302 HTTP业务接口"}))
    if not listen_19310:
        reload_required.append("19310未监听，需总管确认是否受控重载或启动。")

    health: dict[str, Any] = {}
    try:
        health = http_get_json("/health", timeout=15)
        samples["health"] = health
        health_safety = health.get("安全边界", {})
        checks.append(check("health正常", health.get("状态") == "正常", health))
        n8n_phrase = health.get("n8n口径")
        n8n_closed = health_safety.get("触发n8n") is False
        checks.append(check(
            "health n8n口径/关闭状态正确",
            n8n_phrase == "检查项可读，真实触发关闭" or n8n_closed,
            {"n8n口径": n8n_phrase, "触发n8n": health_safety.get("触发n8n"), "判定": "真实触发关闭即可通过只读巡检"},
        ))
        checks.append(check("health真实发送关闭", health_safety.get("真实发送企业微信") is False, health_safety))
        checks.append(check("health触发n8n关闭", health_safety.get("触发n8n") is False, health_safety))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("health正常", False, str(exc)))
        reload_required.append("19310 health不可用，需总管确认。")

    tax_cases = [
        ("税收业务：软件产品即征即退需要准备哪些资料", "软件产品增值税即征即退"),
        ("税收业务：帮我查一下增值税法的依据", "增值税法依据"),
        ("税收业务：研发费用加计扣除需要准备哪些资料", "研发费用加计扣除"),
    ]
    tax_results = []
    for text, expected_subject in tax_cases:
        try:
            payload = http_get_json("/wecom/work-secretary", text, timeout=30)
            reply = reply_text(payload)
            title, subject = lines_title_and_subject(reply)
            item = {
                "输入": text,
                "状态": payload.get("状态"),
                "路由": payload.get("路由") or payload.get("route"),
                "标题": title,
                "事项": subject,
                "期望事项": expected_subject,
                "real_send": safety_value(payload, "real_send"),
                "触发n8n": safety_value(payload, "触发n8n"),
            }
            draft_ok = title == "【税收分析助手-待复核草案摘要】" and subject == expected_subject
            paused_ok = (
                item["状态"] == "已暂停"
                and item["路由"] == "税收业务暂停"
                and "暂停" in reply
                and "不执行抓取、登录、申报、写库" in reply
            )
            tax_results.append(item)
            checks.append(check(
                f"工作秘书税收边界正确：{expected_subject}",
                (draft_ok or paused_ok)
                and item["real_send"] is False
                and item["触发n8n"] is False,
                item,
            ))
        except Exception as exc:  # noqa: BLE001
            checks.append(check(f"工作秘书税收边界正确：{expected_subject}", False, str(exc)))
    samples["税收三条"] = tax_results

    route_cases = [
        ("/wecom/system-manager", "分析天齐锂业", ["股票分析助手", "股票分析专家", "股票助手"]),
        ("/wecom/work-secretary", "分析天齐锂业", ["股票分析助手", "股票分析专家", "股票助手"]),
        ("/wecom/video-assistant", "系统现在进度多少", ["系统管家"]),
    ]
    route_results = []
    for path, text, expected_words in route_cases:
        try:
            payload = http_get_json(path, text, timeout=20)
            reply = reply_text(payload)
            old_words = [word for word in OLD_STOCK_WORDS if word in reply]
            item = {
                "入口": path,
                "输入": text,
                "期望转交关键词": expected_words,
                "回复片段": reply[:240],
                "命中股票旧口径词": old_words,
                "real_send": safety_value(payload, "real_send"),
                "触发n8n": safety_value(payload, "触发n8n"),
            }
            route_results.append(item)
            checks.append(check(
                f"职责分流正确：{path}",
                any(word in reply for word in expected_words)
                and not old_words
                and item["real_send"] is False
                and item["触发n8n"] is False,
                item,
            ))
        except Exception as exc:  # noqa: BLE001
            checks.append(check(f"职责分流正确：{path}", False, str(exc)))
    samples["职责分流"] = route_results

    video_cases = [
        ("生成预检 VF-20260508-005", "blocked"),
        ("最终启用真实渲染 VF-20260508-005 我确认启用真实渲染", "blocked"),
        ("发布预检", "blocked"),
    ]
    video_results = []
    for text, expected in video_cases:
        try:
            payload = http_get_json("/wecom/video-assistant", text, timeout=30)
            raw = json.dumps(payload, ensure_ascii=False)
            item = {
                "输入": text,
                "期望": expected,
                "包含blocked": "blocked" in raw,
                "放行成功词命中": [word for word in ["已发布", "发布成功", "真实渲染完成", "已生成视频文件"] if word in raw],
                "real_send": safety_value(payload, "real_send"),
                "触发n8n": safety_value(payload, "触发n8n"),
                "回复片段": reply_text(payload)[:260],
            }
            video_results.append(item)
            checks.append(check(
                f"视频真实动作仍阻断：{text}",
                item["包含blocked"]
                and not item["放行成功词命中"]
                and item["real_send"] is False
                and item["触发n8n"] is False,
                item,
            ))
        except Exception as exc:  # noqa: BLE001
            checks.append(check(f"视频真实动作仍阻断：{text}", False, str(exc)))
    samples["视频阻断"] = video_results

    failed = [item for item in checks if item["结果"] != "pass"]
    return {
        "类型": "wecom-public-access-daily-readonly-patrol",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "汇总": {"总数": len(checks), "通过": len(checks) - len(failed), "失败": len(failed)},
        "检查项": checks,
        "失败项": failed,
        "需总管确认": reload_required,
        "样例结果": samples,
        "端口状态": {"19310": port_19310, "19302": port_19302},
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "请求19302股票业务接口": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "重载19310": False,
            "重载19302": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['检查项']} | {item['结果']} | {str(item.get('详情', ''))[:180].replace(chr(10), ' / ')} |"
        for item in report.get("检查项", [])
    ]
    return "\n".join([
        "# 企业微信公共接入层日常只读巡检",
        "",
        f"- 生成时间：{report.get('生成时间')}",
        f"- 总体状态：{report.get('总体状态')}",
        f"- 通过/总数：{report.get('汇总', {}).get('通过')} / {report.get('汇总', {}).get('总数')}",
        f"- 需总管确认：{'; '.join(report.get('需总管确认', [])) if report.get('需总管确认') else '无'}",
        "",
        "| 检查项 | 结果 | 摘要 |",
        "| --- | --- | --- |",
        *rows,
        "",
        "## 安全边界",
        "",
        "- 只请求 127.0.0.1:19310。",
        "- 19302 只确认端口状态，不请求股票业务接口。",
        "- 不真实发送企业微信，不触发 n8n。",
        "- 不接券商、不交易、不登录电子税务局、不接财税软件。",
        "- 不修改总管面板，不修改一键接续包，不重载 19310/19302。",
        "",
    ])


def main() -> int:
    report = run_patrol()
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, build_markdown(report))
    print(json.dumps({
        "总体状态": report["总体状态"],
        "通过": report["汇总"]["通过"],
        "失败": report["汇总"]["失败"],
        "输出": str(LATEST_JSON),
        "报告": str(LATEST_MD),
    }, ensure_ascii=False))
    return 0 if report["总体状态"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
