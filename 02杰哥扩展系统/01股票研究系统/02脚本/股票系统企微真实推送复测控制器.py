# -*- coding: utf-8 -*-
"""
名称：股票系统企微真实推送复测控制器.py
作用：在企业微信可信IP放行后，受控执行股票主动研究真实推送复测并刷新交付状态。
触发方式：python 股票系统企微真实推送复测控制器.py [--real-send] [--open-report]
依赖：股票主动研究企微灰度发送脚本、可信IP状态监测、交付自检、质量面板、C+++总验收。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：默认只预检不真实发送；真实发送必须显式 --real-send；不启用n8n自动触发；不调用券商接口；不自动交易。
标识：stock-wework-real-push-retest-controller
"""

from __future__ import annotations

import argparse
import json
import os
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


def run_script(root: Path, script: str, args: list[str] | None = None, timeout: int = 300) -> dict[str, Any]:
    started = datetime.now()
    command = [sys.executable, str(root / "02脚本" / script), *(args or [])]
    completed = subprocess.run(
        command,
        cwd=str(root / "02脚本"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return {
        "脚本": script,
        "参数": args or [],
        "开始时间": started.strftime("%Y-%m-%d %H:%M:%S"),
        "结束时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "返回码": completed.returncode,
        "成功": completed.returncode == 0,
        "stdout": (completed.stdout or "").strip()[-3000:],
        "stderr": (completed.stderr or "").strip()[-3000:],
    }


def parse_last_json(stdout: str) -> dict[str, Any]:
    text = str(stdout or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text.splitlines()[-1])
    except json.JSONDecodeError:
        return {"原始stdout": text}


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def latest_gray_send_state(root: Path) -> dict[str, Any]:
    """读取企业微信灰度发送正式日志，避免子进程stdout编码问题导致误判。"""
    path = root / "04日志" / "企业微信主动研究灰度发送" / "stock-active-research-wework-gray-send-最新.json"
    data = load_json(path, {})
    return {
        "路径": str(path),
        "存在": path.exists(),
        "模式": data.get("模式", ""),
        "真实发送成功": bool(
            data.get("结果判定", {}).get("真实发送成功")
            or data.get("实际动作", {}).get("企业微信真实发送成功")
        ),
        "公共发送器通过": bool(data.get("结果判定", {}).get("是否通过公共发送器检查")),
        "生成时间": data.get("生成时间", ""),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统企微真实推送复测控制器 - {report['生成时间']}",
        "",
        "## 一、复测结论",
        "",
        f"- 模式：{report['模式']}",
        f"- 结论：{report['复测结论']}",
        f"- 当前需放行IP：`{report['当前需放行IP'] or '未提取'}`",
        f"- 真实发送成功：{report['真实发送成功']}",
        "",
        "## 二、本次动作",
        "",
    ]
    for item in report["动作"]:
        lines.append(f"- {item['脚本']}：{'成功' if item['成功'] else '失败'}")
    lines.extend([
        "",
        "## 三、下一步",
        "",
    ])
    for item in report["下一步动作"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 四、关键文件",
        "",
    ])
    for name, state in report["关键文件"].items():
        lines.append(f"- {name}：{'存在' if state['存在'] else '缺失'}，`{state['路径']}`")
    lines.extend([
        "",
        "## 五、安全边界",
        "",
        f"- 本次是否真实发送企业微信：{report['实际动作']['企业微信真实发送']}",
        "- 不启用n8n自动触发。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_bats(root: Path, script_path: Path) -> dict[str, str]:
    entry_dir = root / "05入口工具"
    precheck = entry_dir / "股票系统企微真实推送复测_预检不发送.bat"
    real = entry_dir / "股票系统企微真实推送复测_确认可信IP后真实发送.bat"
    write_text(precheck, (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'python "{script_path}" --open-report\r\n'
        "pause\r\n"
    ))
    write_text(real, (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'python "{script_path.parent / "生成股票系统可信IP状态监测.py"}"\r\n'
        "powershell -NoProfile -Command \"$p='D:\\杰哥智能化系统\\02杰哥扩展系统\\01股票研究系统\\03数据\\155可信IP状态监测\\股票系统可信IP状态监测_最新.json'; $j=Get-Content -LiteralPath $p -Raw -Encoding UTF8 | ConvertFrom-Json; Write-Host ('当前应放行IP：' + $j.'当前需放行IP')\"\r\n"
        "echo 请确认：企业微信后台已加入当前可信IP，且你允许发送本人白名单灰度消息。\r\n"
        "choice /M \"确认执行企业微信真实推送复测\"\r\n"
        "if errorlevel 2 exit /b 1\r\n"
        f'python "{script_path}" --real-send --open-report\r\n'
        "pause\r\n"
    ))
    return {"预检不发送": str(precheck), "真实发送复测": str(real)}


def maybe_open(path: Path, enabled: bool) -> None:
    if not enabled:
        return
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-send", action="store_true", help="显式执行本人白名单真实灰度发送")
    parser.add_argument("--open-report", action="store_true", help="执行后打开复测报告")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    actions: list[dict[str, Any]] = []

    actions.append(run_script(root, "生成股票系统可信IP状态监测.py", timeout=120))
    send_args = ["--real-send", "--fixed-public-egress"] if args.real_send else []
    actions.append(run_script(root, "执行股票主动研究企微灰度发送.py", send_args, timeout=180))
    actions.append(run_script(root, "生成企业微信可信IP修复包.py", timeout=120))
    actions.append(run_script(root, "生成股票系统可信IP状态监测.py", timeout=120))
    actions.append(run_script(root, "生成股票系统交付自检报告.py", timeout=120))
    actions.append(run_script(root, "检查股票系统报告安全边界.py", timeout=120))
    actions.append(run_script(root, "生成股票系统质量观察面板.py", timeout=120))
    actions.append(run_script(root, "记录股票系统质量观察历史.py", timeout=120))
    actions.append(run_script(root, "验证股票系统C加加加日常可用总验收.py", timeout=120))
    actions.append(run_script(root, "生成股票系统交付总包.py", timeout=120))

    send_action = actions[1]
    send_stdout = parse_last_json(send_action.get("stdout", ""))
    latest_send = latest_gray_send_state(root)
    real_success = bool(send_stdout.get("真实发送成功") or send_stdout.get("real_send_success") or latest_send.get("真实发送成功"))
    fix = load_json(root / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.json", {})
    trusted = load_json(root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.json", {})

    if args.real_send and real_success:
        conclusion = "真实推送复测成功：可进入最终交付确认"
        next_actions = [
            "查看企业微信是否收到股票主动研究灰度消息。",
            "打开05入口工具中的“股票系统完全交付最终验收_打开”确认是否进入完全交付状态。",
            "运行日常一键入口观察1-2轮报告质量。",
            "保持券商接口和自动交易继续关闭。",
        ]
    elif args.real_send:
        conclusion = "真实推送复测未成功：优先检查可信IP是否已放行"
        next_actions = [
            f"确认企业微信后台已加入固定公网出口IP：{FIXED_PUBLIC_EGRESS_IP}。",
            "若企业微信仍返回60020，只围绕这个固定公网出口复核，不再追着本地宽带IP变化。",
            "不要排查券商接口、n8n自动触发或交易模块；它们仍保持关闭。",
        ]
    else:
        conclusion = "预检完成：未真实发送，等待可信IP放行后执行真实复测"
        next_actions = [
            f"在企业微信后台加入固定公网出口IP：{FIXED_PUBLIC_EGRESS_IP}。",
            "加入后运行05入口工具中的“股票系统企微真实推送复测_确认可信IP后真实发送”。",
            "真实复测完成后打开05入口工具中的“股票系统完全交付最终验收_打开”。",
            "预检模式不会发送企业微信消息。",
        ]

    report = {
        "名称": "股票系统企微真实推送复测控制器",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "股票系统企微真实推送复测控制器.py",
        "模式": "real-send" if args.real_send else "precheck-only",
        "复测结论": conclusion,
        "当前需放行IP": FIXED_PUBLIC_EGRESS_IP if args.real_send else (fix.get("当前公网出口IP") or trusted.get("当前需放行IP") or FIXED_PUBLIC_EGRESS_IP),
        "固定公网出口IP": FIXED_PUBLIC_EGRESS_IP,
        "真实发送成功": real_success,
        "动作": actions,
        "下一步动作": next_actions,
        "关键文件": {
            "推送草案": file_state(root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"),
            "可信IP修复包": file_state(root / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.md"),
            "可信IP状态监测": file_state(root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.md"),
            "交付自检": file_state(root / "03数据" / "140交付自检" / "股票系统交付自检报告_最新.md"),
            "质量观察面板": file_state(root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.md"),
            "C+++总验收": file_state(root / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.md"),
            "交付总包": file_state(root / "03数据" / "144交付总包" / "股票系统交付总包_最新.md"),
            "完全交付最终验收": file_state(root / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md"),
            "企业微信灰度发送日志": latest_send,
        },
        "实际动作": {
            "企业微信真实发送": bool(args.real_send),
            "企业微信真实发送成功": real_success,
            "使用固定公网出口": bool(args.real_send),
            "启用n8n自动触发": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "安全边界": {
            "真实发送必须显式参数": True,
            "只允许本人白名单灰度": True,
            "是否启用n8n自动触发": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "157企微真实推送复测"
    output_json = output_dir / f"股票系统企微真实推送复测_{stamp}.json"
    output_md = output_dir / f"股票系统企微真实推送复测_{stamp}.md"
    latest_json = output_dir / "股票系统企微真实推送复测_最新.json"
    latest_md = output_dir / "股票系统企微真实推送复测_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)

    final_acceptance = run_script(root, "验证股票系统完全交付最终验收.py", timeout=120)
    if final_acceptance.get("返回码") in {0, 1}:
        final_acceptance["成功"] = True
        final_acceptance["说明"] = "复测报告已先写入，再执行最终验收；返回码1表示仍有外部可信IP等未完成项，不算复测控制器失败。"
    actions.append(final_acceptance)
    report["动作"] = actions
    report["最终验收执行时机"] = "复测报告写入后执行，避免最终验收读取上一次复测结果。"
    report["关键文件"]["完全交付最终验收"] = file_state(root / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md")

    post_final_package = run_script(root, "生成股票系统交付总包.py", timeout=120)
    actions.append(post_final_package)
    report["动作"] = actions
    report["最终交付总包刷新"] = "完全交付最终验收执行后再次刷新交付总包，确保总包引用最新最终验收状态。"
    report["关键文件"]["交付总包"] = file_state(root / "03数据" / "144交付总包" / "股票系统交付总包_最新.md")

    final_trusted_status = run_script(root, "生成股票系统可信IP状态监测.py", timeout=120)
    actions.append(final_trusted_status)
    report["动作"] = actions
    report["可信IP状态监测最终刷新"] = "复测报告写入后再次刷新可信IP状态，避免状态面板引用上一轮复测时间。"
    report["关键文件"]["可信IP状态监测"] = file_state(root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.md")

    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)

    entries = write_entry_bats(root, root / "02脚本" / "股票系统企微真实推送复测控制器.py")
    maybe_open(latest_md, args.open_report)
    if args.real_send and args.open_report:
        maybe_open(root / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.md", True)

    ok = real_success if args.real_send else all(item.get("成功") for item in actions if item["脚本"] != "执行股票主动研究企微灰度发送.py")
    print(json.dumps({
        "状态": "完成" if ok else "存在阻断",
        "模式": report["模式"],
        "真实发送成功": real_success,
        "当前需放行IP": report["当前需放行IP"],
        "报告": str(latest_md),
        "入口工具": entries,
    }, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
