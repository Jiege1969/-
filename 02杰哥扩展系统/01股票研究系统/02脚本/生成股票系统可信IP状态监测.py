# -*- coding: utf-8 -*-
"""
名称：生成股票系统可信IP状态监测.py
作用：汇总股票系统企业微信主动推送的可信IP阻断、当前需放行IP和复测入口。
触发方式：python 生成股票系统可信IP状态监测.py
依赖：企微可信IP修复包、交付自检、交付控制台、可信IP放行后最终验收包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地状态文件；只写03数据/155可信IP状态监测和05入口工具bat；不调用企业微信API；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
标识：stock-trusted-ip-status-monitor
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

FIXED_PUBLIC_EGRESS_IP = "43.167.210.211"

def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
        "大小": path.stat().st_size if path.exists() else 0,
    }


def run_script(root: Path, script_name: str, timeout: int = 120) -> dict[str, Any]:
    script_path = root / "02脚本" / script_name
    if not script_path.exists():
        return {
            "脚本": str(script_path),
            "已执行": False,
            "是否成功": False,
            "返回码": None,
            "错误": "脚本不存在",
        }
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(script_path.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "脚本": str(script_path),
            "已执行": True,
            "是否成功": result.returncode == 0,
            "返回码": result.returncode,
            "输出摘要": (result.stdout or "").strip()[-800:],
            "错误摘要": (result.stderr or "").strip()[-800:],
        }
    except Exception as exc:
        return {
            "脚本": str(script_path),
            "已执行": True,
            "是否成功": False,
            "返回码": None,
            "错误": str(exc),
        }


def extract_ip(text: str) -> str:
    match = re.search(r"from ip:\s*([0-9]+(?:\.[0-9]+){3})", text or "")
    return match.group(1) if match else ""


def latest_controlled_sender_status(root: Path) -> dict[str, Any]:
    log_dir = root.parents[0] / "00公共组件" / "04日志" / "企业微信受控发送器"
    if not log_dir.exists():
        return {}
    candidates = sorted(
        [p for p in log_dir.glob("wework-controlled-sender-*.json") if p.name != "wework-controlled-sender-最新.json"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    latest_alias = log_dir / "wework-controlled-sender-最新.json"
    path = latest_alias if latest_alias.exists() else (candidates[0] if candidates else None)
    if path is None:
        return {}
    data = load_json(path, {})
    if not isinstance(data, dict):
        return {}
    wecom_return = data.get("发送结果", {}).get("企业微信返回", {})
    errmsg = str(wecom_return.get("errmsg") or "")
    fixed_public = data.get("固定公网出口", {}) if isinstance(data.get("固定公网出口"), dict) else {}
    errcode = wecom_return.get("errcode")
    return {
        "路径": str(path),
        "生成时间": data.get("生成时间", ""),
        "发送出口模式": data.get("发送出口模式", ""),
        "固定公网出口IP": fixed_public.get("公网IP") or "",
        "实际出口IP": fixed_public.get("实际出口IP") or "",
        "发送企业微信成功": bool((data.get("实际动作") or {}).get("发送企业微信成功")),
        "errcode": errcode,
        "errmsg": errmsg,
        "是否命中60020": errcode == 60020,
        "拦截公网IP": extract_ip(errmsg) if errcode == 60020 else "",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统可信IP状态监测 - {report['生成时间']}",
        "",
        "## 一、当前状态",
        "",
        f"- 状态：{report['状态']}",
        f"- 当前需放行IP：`{report['当前需放行IP'] or '未提取到'}`",
        f"- 企业微信真实发送是否已通过：{report['企业微信真实发送已通过']}",
        f"- 最新真实发送复测是否已通过：{report.get('最新真实发送复测已通过')}",
        f"- 最新真实发送复测时间：{report.get('最新真实发送复测生成时间') or '无'}",
        f"- 是否命中60020：{report['是否命中60020']}",
        f"- 历史修复包是否命中60020：{report.get('历史修复包是否命中60020')}",
        f"- 最新受控发送出口：{report.get('最新受控发送状态', {}).get('发送出口模式') or '无'}",
        f"- 最新受控发送实际出口IP：`{report.get('最新受控发送状态', {}).get('实际出口IP') or '无'}`",
        f"- 交付层级：{report['当前交付层级']}",
        "",
        "## 二、下一步",
        "",
    ]
    for item in report["下一步动作"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 三、可信IP修复包刷新",
        "",
        f"- 是否已刷新：{report['可信IP修复包刷新动作'].get('已执行')}",
        f"- 是否成功：{report['可信IP修复包刷新动作'].get('是否成功')}",
        f"- 返回码：{report['可信IP修复包刷新动作'].get('返回码')}",
        "",
        "## 四、复测入口",
        "",
        f"- 入口工具：`{report['复测入口']}`",
        "- 命令行：",
        "",
        "```powershell",
        r"cd D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本",
        "python 股票系统企微真实推送复测控制器.py --real-send --open-report",
        "```",
        "",
        "## 五、关键文件",
        "",
    ])
    for name, state in report["关键文件"].items():
        lines.append(f"- {name}：{'存在' if state['存在'] else '缺失'}，`{state['路径']}`")
    lines.extend([
        "",
        "## 六、安全边界",
        "",
        "- 不调用企业微信API。",
        "- 不真实发送企业微信。",
        "- 不启用n8n。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(root: Path, script_path: Path, target: Path) -> Path:
    bat = root / "05入口工具" / "股票系统可信IP状态监测_打开.bat"
    write_text(bat, (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'python "{script_path}"\r\n'
        f'start "" "{target}"\r\n'
    ))
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    refresh_fix = run_script(root, "生成企业微信可信IP修复包.py")

    fix_json_path = root / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.json"
    self_check_path = root / "03数据" / "140交付自检" / "股票系统交付自检报告_最新.json"
    console_path = root / "03数据" / "143交付控制台" / "股票系统交付控制台_最新.json"
    final_pack_path = root / "03数据" / "154可信IP放行后最终验收包" / "股票系统可信IP放行后最终验收包_最新.md"
    retest_json_path = root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.json"

    fix = load_json(fix_json_path, {})
    self_check = load_json(self_check_path, {})
    console = load_json(console_path, {})
    retest = load_json(retest_json_path, {})
    layers = self_check.get("层级验收") or {}
    latest_sender = latest_controlled_sender_status(root)
    latest_sender_blocked = bool(latest_sender.get("是否命中60020"))
    latest_sender_ok = bool(latest_sender.get("发送企业微信成功"))
    real_retest_ok = (bool(retest.get("真实发送成功")) or latest_sender_ok) and not latest_sender_blocked
    real_ok = (real_retest_ok or bool(layers.get("D真实灰度可用", {}).get("是否通过"))) and not latest_sender_blocked
    current_ip = str(
        latest_sender.get("拦截公网IP")
        or latest_sender.get("实际出口IP")
        or latest_sender.get("固定公网出口IP")
        or retest.get("当前需放行IP")
        or fix.get("当前公网出口IP")
        or FIXED_PUBLIC_EGRESS_IP
    )
    historical_hit_60020 = bool(fix.get("是否命中60020"))
    hit_60020 = latest_sender_blocked or (historical_hit_60020 and not real_retest_ok)

    if real_retest_ok:
        status = "已通过：企业微信真实主动推送已可用"
        next_actions = [
            "保持当前可信IP配置，不需要重复修改企业微信后台。",
            "后续只做观察复测；若公网出口IP变化，再重新生成可信IP修复包并复测。",
            "继续保持不启用n8n自动触发、不调用券商接口、不自动交易。",
        ]
    elif hit_60020 and current_ip:
        status = "待外部放行：企业微信可信IP白名单未包含当前公网出口IP"
        next_actions = [
            f"在企业微信后台对应自建应用可信IP中加入 {current_ip}。",
            "加入后运行05入口工具中的“股票系统企微真实推送复测_确认可信IP后真实发送”。",
            f"如果仍失败，只围绕固定公网出口 {FIXED_PUBLIC_EGRESS_IP} 复核，不再追着本地宽带IP变化。",
        ]
    elif real_ok:
        status = "已通过：企业微信真实主动推送已可用"
        next_actions = [
            "保持当前配置，不需要重复修改可信IP。",
            "日常运行仍先看质量观察面板和C+++总验收。",
        ]
    else:
        status = "待复核：未从最新修复包确认60020阻断"
        next_actions = [
            "先运行交付控制台的企微通道检查或可信IP修复包生成脚本。",
            "确认最新企业微信返回后，再决定是否需要加入可信IP。",
        ]

    delivery_level = (console.get("当前状态") or {}).get("交付层级") or self_check.get("当前交付层级") or ""
    if real_ok and "真实主动消息尚未成功" in delivery_level:
        delivery_level = delivery_level.replace("真实主动消息尚未成功", "真实主动消息已通过")

    report = {
        "名称": "股票系统可信IP状态监测",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统可信IP状态监测.py",
        "状态": status,
        "当前需放行IP": current_ip,
        "固定公网出口IP": FIXED_PUBLIC_EGRESS_IP,
        "是否命中60020": hit_60020,
        "历史修复包是否命中60020": historical_hit_60020,
        "企业微信真实发送已通过": real_ok,
        "最新真实发送复测已通过": real_retest_ok,
        "最新真实发送复测生成时间": retest.get("生成时间", ""),
        "当前交付层级": delivery_level,
        "企业微信返回errmsg": fix.get("企业微信返回errmsg") or "",
        "最新受控发送状态": latest_sender,
        "最新受控发送可信IP拦截": latest_sender if latest_sender_blocked else {},
        "复测入口": str(root / "05入口工具" / "股票系统企微真实推送复测_确认可信IP后真实发送.bat"),
        "可信IP修复包刷新动作": refresh_fix,
        "下一步动作": next_actions,
        "关键文件": {
            "可信IP修复包JSON": file_state(fix_json_path),
            "交付自检": file_state(self_check_path),
            "交付控制台": file_state(console_path),
            "可信IP放行后最终验收包": file_state(final_pack_path),
            "企业微信真实推送复测报告": file_state(retest_json_path),
        },
        "安全边界": {
            "是否调用企业微信API": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "155可信IP状态监测"
    output_json = output_dir / f"股票系统可信IP状态监测_{stamp}.json"
    output_md = output_dir / f"股票系统可信IP状态监测_{stamp}.md"
    latest_json = output_dir / "股票系统可信IP状态监测_最新.json"
    latest_md = output_dir / "股票系统可信IP状态监测_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    bat = write_entry_open_bat(root, root / "02脚本" / "生成股票系统可信IP状态监测.py", latest_md)

    print(json.dumps({
        "状态": "完成",
        "可信IP状态": status,
        "当前需放行IP": current_ip,
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
