# -*- coding: utf-8 -*-
"""
名称：核实企业微信视频助理轮次012对齐.py
作用：自动核实公共组件企业微信接入设置是否与视频工厂轮次012总控层对齐。
触发方式：python 核实企业微信视频助理轮次012对齐.py
安全边界：只读配置并调用本机127.0.0.1:19310低风险GET/POST回环；不真实发送企业微信、不触发n8n、不真实渲染、不发布。
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


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


ROOT = module_root()
SYSTEM_ROOT = ROOT.parents[2]
PUBLIC_CONFIG = ROOT / "01配置"
VIDEO_ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
OUTPUT_DIR = ROOT / "03数据" / "14视频助理轮次012对齐核实"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
LATEST_JSON = OUTPUT_DIR / "企业微信视频助理轮次012自动核实_最新.json"
LATEST_MD = OUTPUT_DIR / "企业微信视频助理轮次012自动核实_最新.md"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def http_get_json(url: str, timeout: int = 10) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def http_post_json(url: str, payload: dict[str, Any], timeout: int = 10) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def check(name: str, passed: bool, detail: Any = "") -> dict[str, Any]:
    return {"检查项": name, "结果": "pass" if passed else "fail", "详情": detail}


def current_listener() -> dict[str, Any]:
    command = (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        "$conn=Get-NetTCPConnection -LocalPort 19310 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; "
        "if($conn){$p=Get-Process -Id $conn.OwningProcess; "
        "[pscustomobject]@{pid=$conn.OwningProcess;process=$p.ProcessName;path=$p.Path}|ConvertTo-Json -Compress} "
        "else {'{}'}"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    try:
        return json.loads(completed.stdout.strip() or "{}")
    except json.JSONDecodeError:
        return {"错误": completed.stderr or completed.stdout}


def run_check() -> dict[str, Any]:
    assistant = read_json(PUBLIC_CONFIG / "杰哥视频助理.json")
    terminal = read_json(PUBLIC_CONFIG / "企业微信机器人终端分工总表.json")
    route = read_json(PUBLIC_CONFIG / "企业微信统一指令路由预演规则.json")
    local_call = read_json(PUBLIC_CONFIG / "企业微信统一指令本地调用预演规则.json")
    access_route = read_json(PUBLIC_CONFIG / "企业微信统一指令路由预演规则.json")
    video_task = read_json(VIDEO_ROOT / "03数据" / "18轮次012视频工厂总控层" / "视频工厂任务单_最新.json")
    checks: list[dict[str, Any]] = []

    checks.append(check("公共组件权威路径存在", ROOT.exists(), str(ROOT)))
    checks.append(check("视频助理建议路径为/wecom/video-assistant", assistant.get("建议通讯路径") == "/wecom/video-assistant", assistant.get("建议通讯路径")))
    checks.append(check("视频助理登记轮次012", "轮次012视频工厂总控层" in json.dumps(assistant, ensure_ascii=False), "杰哥视频助理.json"))
    checks.append(check("终端分工登记生成放行", "生成放行" in json.dumps(terminal, ensure_ascii=False), "企业微信机器人终端分工总表.json"))
    checks.append(check("公共路由包含复核通过关键词", "复核通过" in json.dumps(route, ensure_ascii=False), "企业微信统一指令路由预演规则.json"))
    checks.append(check("接入设置路由包含生成预检关键词", "生成预检" in json.dumps(access_route, ensure_ascii=False), "企业微信接入设置路由"))
    checks.append(check("本地调用说明区分专用入口", "/wecom/video-assistant" in json.dumps(local_call, ensure_ascii=False), "本地调用预演规则"))
    checks.append(check("视频任务单仍禁止真实渲染", video_task.get("生成控制", {}).get("允许真实渲染") is False, video_task.get("任务ID")))
    checks.append(check("视频任务单仍禁止自动发布", video_task.get("生成控制", {}).get("允许自动发布") is False, video_task.get("任务ID")))

    listener = current_listener()
    checks.append(check("19310存在监听进程", bool(listener.get("pid")), listener))

    health: dict[str, Any] = {}
    get_payload: dict[str, Any] = {}
    post_payload: dict[str, Any] = {}
    wecom_text_payload: dict[str, Any] = {}
    render_fix_payload: dict[str, Any] = {}
    render_apply_payload: dict[str, Any] = {}
    final_render_payload: dict[str, Any] = {}
    try:
        health = http_get_json("http://127.0.0.1:19310/health")
        checks.append(check("health正常", health.get("状态") == "正常", health))
        safety = health.get("安全边界", {})
        checks.append(check("health真实发送关闭", safety.get("真实发送企业微信") is False, safety))
        checks.append(check("health n8n关闭", safety.get("触发n8n") is False, safety))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("health正常", False, str(exc)))

    try:
        text = urllib.parse.quote("生成预检 VF-20260508-005")
        get_payload = http_get_json(f"http://127.0.0.1:19310/wecom/video-assistant?text={text}", timeout=20)
        checks.append(check("GET视频助理进入轮次012", "视频生成桥梁预检已完成" in str(get_payload.get("回复", "")), get_payload.get("回复", "")))
        checks.append(check("GET视频助理不真实发送", get_payload.get("real_send") is False, get_payload))
        checks.append(check("GET视频助理不触发n8n", get_payload.get("n8n") is False, get_payload))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("GET视频助理进入轮次012", False, str(exc)))

    try:
        post_payload = http_post_json(
            "http://127.0.0.1:19310/wecom/video-assistant",
            {"text": "生成预检 VF-20260508-005"},
            timeout=20,
        )
        checks.append(check("POST视频助理进入轮次012", "视频生成桥梁预检已完成" in str(post_payload.get("回复", "")), post_payload.get("回复", "")))
        checks.append(check("POST视频助理不真实发送", post_payload.get("real_send") is False, post_payload))
        checks.append(check("POST视频助理不触发n8n", post_payload.get("n8n") is False, post_payload))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("POST视频助理进入轮次012", False, str(exc)))

    try:
        wecom_text_payload = http_post_json(
            "http://127.0.0.1:19310/wecom/video-assistant",
            {
                "msgtype": "text",
                "text": {"content": "生成预检 VF-20260508-005"},
            },
            timeout=20,
        )
        checks.append(check(
            "企业微信text.content消息体进入轮次012",
            "视频生成桥梁预检已完成" in str(wecom_text_payload.get("回复", "")),
            wecom_text_payload.get("回复", ""),
        ))
        checks.append(check("企业微信text.content消息体不真实发送", wecom_text_payload.get("real_send") is False, wecom_text_payload))
        checks.append(check("企业微信text.content消息体不触发n8n", wecom_text_payload.get("n8n") is False, wecom_text_payload))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("企业微信text.content消息体进入轮次012", False, str(exc)))

    try:
        text = urllib.parse.quote("渲染环境修复清单")
        render_fix_payload = http_get_json(f"http://127.0.0.1:19310/wecom/video-assistant?text={text}", timeout=20)
        checks.append(check(
            "GET视频助理支持渲染环境修复清单",
            "视频生成环境修复清单已生成" in str(render_fix_payload.get("回复", "")),
            render_fix_payload.get("回复", ""),
        ))
        checks.append(check("渲染环境修复清单不启用真实渲染", render_fix_payload.get("render_environment_prepare", {}).get("report", {}).get("安全边界", {}).get("启用真实渲染") is False, render_fix_payload))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("GET视频助理支持渲染环境修复清单", False, str(exc)))

    try:
        text = urllib.parse.quote("应用渲染配置建议")
        render_apply_payload = http_get_json(f"http://127.0.0.1:19310/wecom/video-assistant?text={text}", timeout=20)
        checks.append(check(
            "GET视频助理支持应用渲染配置建议",
            "视频生成桥梁建议配置应用已执行" in str(render_apply_payload.get("回复", "")),
            render_apply_payload.get("回复", ""),
        ))
        checks.append(check(
            "应用渲染配置建议不启用真实渲染",
            render_apply_payload.get("render_suggestion_apply", {}).get("report", {}).get("安全边界", {}).get("启用真实渲染") is False,
            render_apply_payload,
        ))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("GET视频助理支持应用渲染配置建议", False, str(exc)))

    try:
        text = urllib.parse.quote("最终启用真实渲染 VF-20260508-005 我确认启用真实渲染")
        final_render_payload = http_get_json(f"http://127.0.0.1:19310/wecom/video-assistant?text={text}", timeout=20)
        checks.append(check(
            "GET视频助理支持最终真实渲染门禁",
            "最终真实渲染启用门禁已执行" in str(final_render_payload.get("回复", "")),
            final_render_payload.get("回复", ""),
        ))
        checks.append(check(
            "最终真实渲染门禁不直接调用渲染",
            final_render_payload.get("final_real_render_gate", {}).get("report", {}).get("安全边界", {}).get("调用MoneyPrinterTurbo") is False,
            final_render_payload,
        ))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("GET视频助理支持最终真实渲染门禁", False, str(exc)))

    failed = [item for item in checks if item["结果"] != "pass"]
    return {
        "类型": "wecom-video-assistant-r012-alignment-check",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "检查项": checks,
        "失败项": failed,
        "监听进程": listener,
        "health": health,
        "GET视频助理样例": get_payload,
        "POST视频助理样例": post_payload,
        "企业微信text.content消息体样例": wecom_text_payload,
        "渲染环境修复清单样例": render_fix_payload,
        "应用渲染配置建议样例": render_apply_payload,
        "最终真实渲染门禁样例": final_render_payload,
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "真实渲染": False,
            "自动发布": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    rows = "\n".join(f"| {item['检查项']} | {item['结果']} | {item.get('详情', '')} |" for item in report.get("检查项", []))
    return "\n".join([
        "# 企业微信视频助理轮次012自动核实",
        "",
        f"- 生成时间：{report.get('生成时间')}",
        f"- 总体状态：{report.get('总体状态')}",
        f"- 监听进程：{report.get('监听进程')}",
        "",
        "| 检查项 | 结果 | 详情 |",
        "| --- | --- | --- |",
        rows,
        "",
        "## 安全结论",
        "",
        "本核实只做本机回环验证；不真实发送企业微信、不触发n8n、不真实渲染、不自动发布。",
        "",
    ])


def save_report(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(report)
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, markdown)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"企业微信视频助理轮次012自动核实_{timestamp}.json", report)
    write_text(ARCHIVE_DIR / f"企业微信视频助理轮次012自动核实_{timestamp}.md", markdown)


def main() -> int:
    report = run_check()
    save_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("总体状态") == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
