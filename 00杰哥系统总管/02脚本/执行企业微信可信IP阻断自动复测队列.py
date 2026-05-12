# -*- coding: utf-8 -*-
"""
名称：执行企业微信可信IP阻断自动复测队列.py
作用：自动执行企业微信可信IP放行后的受控复测，并刷新阻断/交付状态。
触发方式：python 执行企业微信可信IP阻断自动复测队列.py
安全边界：只调用既有受控真实复测脚本；不启动旧容器；不启动旧n8n；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
STOCK_ROOT = ROOT / "02杰哥扩展系统" / "01股票研究系统"
SCRIPTS = STOCK_ROOT / "02脚本"
STATE_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
QUEUE_JSON = STATE_DIR / "企业微信可信IP阻断自动复测队列_最新.json"
QUEUE_MD = STATE_DIR / "企业微信可信IP阻断自动复测队列_最新.md"
PANEL = ROOT / "00杰哥系统总管" / "07文档" / "当前施工面板.md"


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


def run_script(script_name: str, args: list[str] | None = None, timeout: int = 420) -> dict[str, Any]:
    started = datetime.now()
    completed = subprocess.run(
        [sys.executable, str(SCRIPTS / script_name), *(args or [])],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
    return {
        "脚本": script_name,
        "参数": args or [],
        "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
        "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "返回码": completed.returncode,
        "成功": completed.returncode == 0,
        "stdout": (completed.stdout or "").strip()[-2000:],
        "stderr": (completed.stderr or "").strip()[-2000:],
    }


def build_markdown(state: dict[str, Any]) -> str:
    target = state.get("目标应用档案", {})
    latest = state.get("最近真实复测", {})
    lines = [
        "# 企业微信可信IP阻断自动复测队列",
        "",
        f"- 当前状态：{state['当前状态']}",
        f"- 更新时间：{state['生成时间']}",
        f"- 当前需放行IP：`{state.get('当前需放行IP') or '未提取'}`",
        f"- 目标应用档案：`{target.get('名称') or '未提取'}`",
        f"- 企业ID变量：`{target.get('企业ID变量') or '未提取'}`",
        f"- 应用ID变量：`{target.get('应用ID变量') or '未提取'}`",
        f"- 最近真实复测：`real-send`，真实发送成功={latest.get('真实发送成功')}",
        f"- 自动判定：{latest.get('自动判定') or '未判定'}",
        f"- 判定原因：{latest.get('判定原因') or '无'}",
        f"- 企业微信返回：`{latest.get('企业微信errmsg') or '无'}`",
        "",
        "## 自动动作",
        "",
    ]
    for item in state.get("自动复测", {}).get("动作", []):
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 不启动旧 n8n。",
        "- 不启动旧容器。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不绕过企业微信受控发送器。",
    ])
    return "\n".join(lines)


def append_panel(state: dict[str, Any]) -> None:
    now = state["生成时间"]
    latest = state.get("最近真实复测", {})
    target = state.get("目标应用档案", {})
    block = "\n".join([
        "",
        f"## {now} 企业微信可信 IP 自动复测队列执行",
        "",
        f"- 当前状态：{state['当前状态']}。",
        f"- 真实发送成功：{latest.get('真实发送成功')}。",
        f"- 自动判定：{latest.get('自动判定') or '未判定'}。",
        f"- 判定原因：{latest.get('判定原因') or '无'}。",
        f"- 当前需放行 IP：`{state.get('当前需放行IP') or '未提取'}`。",
        f"- 目标应用档案：`{target.get('名称') or '未提取'}`。",
        f"- 企业微信返回：`{latest.get('企业微信errmsg') or '无'}`。",
        "- 仍保持安全边界：不启动旧容器、不启动旧 n8n、不调用券商接口、不自动交易。",
        "",
    ])
    PANEL.write_text(PANEL.read_text(encoding="utf-8") + block, encoding="utf-8")


def main() -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    actions: list[dict[str, Any]] = []

    actions.append(run_script("股票系统企微真实推送复测控制器.py", ["--real-send"], timeout=420))
    actions.append(run_script("生成企业微信可信IP修复包.py", timeout=120))
    actions.append(run_script("生成股票系统可信IP状态监测.py", timeout=120))
    actions.append(run_script("验证股票系统完全交付最终验收.py", timeout=180))
    actions.append(run_script("生成股票系统交付总包.py", timeout=180))

    retest = load_json(STOCK_ROOT / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.json", {})
    fix = load_json(STOCK_ROOT / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.json", {})
    final = load_json(STOCK_ROOT / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.json", {})
    sender = load_json(ROOT / "02杰哥扩展系统" / "00公共组件" / "04日志" / "企业微信受控发送器" / "wework-controlled-sender-最新.json", {})
    send_return = sender.get("发送结果", {}).get("企业微信返回", {})
    real_success = bool(retest.get("真实发送成功"))

    if real_success:
        current_status = "真实发送已成功，已刷新交付状态"
        auto_judgement = "通过"
        judgement_reason = "企业微信真实发送复测成功，复测报告真实发送成功为true。"
    else:
        current_status = "自动复测后仍阻断，继续自动复测中"
        auto_judgement = "未通过"
        judgement_reason = (
            "企业微信真实发送复测未成功。"
            f"当前企业微信返回errcode={send_return.get('errcode', '未提取')}，"
            "只有errcode=0且真实发送成功=true时才自动判定通过。"
        )

    state = {
        "名称": "企业微信可信IP阻断自动复测队列",
        "生成时间": now,
        "当前状态": current_status,
        "阻断原因": "" if real_success else "企业微信后台可信IP白名单未包含当前公网出口IP，或目标应用白名单尚未生效",
        "当前需放行IP": fix.get("当前公网出口IP") or final.get("当前需放行IP") or retest.get("当前需放行IP") or "",
        "目标应用档案": fix.get("目标应用档案") or {},
        "最近真实复测": {
            "模式": retest.get("模式") or "real-send",
            "真实发送成功": real_success,
            "企业微信errcode": send_return.get("errcode"),
            "企业微信errmsg": send_return.get("errmsg", ""),
            "复测结论": retest.get("复测结论", ""),
            "自动判定": auto_judgement,
            "判定原因": judgement_reason,
            "最终验收": {
                "通过数量": final.get("通过数量"),
                "失败数量": final.get("失败数量"),
                "验收结论": final.get("验收结论", ""),
            },
        },
        "自动复测": {
            "已创建": True,
            "类型": "thread heartbeat",
            "频率": "每5分钟",
            "动作": [
                "运行受控真实复测",
                "刷新可信IP修复包、状态监测、最终验收和交付总包",
                "成功时继续刷新施工面板",
                "失败时登记阻断证据并等待下一轮自动复测",
            ],
        },
        "本轮动作": actions,
        "安全边界": {
            "是否启动旧n8n": False,
            "是否启动旧容器": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否绕过受控发送器": False,
        },
    }
    write_json(QUEUE_JSON, state)
    write_text(QUEUE_MD, build_markdown(state))
    append_panel(state)
    print(json.dumps({
        "状态": current_status,
        "真实发送成功": real_success,
        "当前需放行IP": state["当前需放行IP"],
        "目标应用": state["目标应用档案"].get("名称", ""),
        "最终验收": state["最近真实复测"]["最终验收"],
        "队列": str(QUEUE_MD),
    }, ensure_ascii=False))
    return 0 if real_success else 1


if __name__ == "__main__":
    raise SystemExit(main())
