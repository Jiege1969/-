# -*- coding: utf-8 -*-
"""
名称：check_publish_account.py
作用：检查 social-auto-upload 指定平台账号的本地登录状态。
触发方式：python check_publish_account.py --platform bilibili --account creator
依赖：Python 标准库；视频发布桥梁配置.json；social-auto-upload sau CLI。
所属系统：02杰哥扩展系统/02视频制作系统
安全边界：只执行账号登录态检查，不上传、不发布、不触发n8n、不发送企业微信真实消息。
创建/修改记录：2026-05-08 创建发布账号登录态检查工具。
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def module_root() -> Path:
    return Path(__file__).resolve().parents[2]


ROOT = module_root()
ROUND_DIR = ROOT / "03数据" / "18轮次012视频工厂总控层"
CONFIG_PATH = ROOT / "01配置" / "视频发布桥梁配置.json"
OUTPUT_DIR = ROUND_DIR / "测试与审核" / "发布账号检查"
ARCHIVE_DIR = OUTPUT_DIR / "archive"
LATEST_JSON = OUTPUT_DIR / "发布账号检查_最新.json"
LATEST_MD = OUTPUT_DIR / "发布账号检查_最新.md"


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


def normalize_platform(platform: str, config: dict[str, Any]) -> str:
    platform_map = config.get("平台映射", {})
    return platform_map.get(platform.strip(), platform.strip())


def build_markdown(report: dict[str, Any]) -> str:
    return "\n".join([
        "# 轮次012 发布账号检查报告",
        "",
        f"- 生成时间：{report.get('生成时间')}",
        f"- 总体状态：{report.get('总体状态')}",
        f"- 平台：{report.get('平台')}",
        f"- 账号：{report.get('账号')}",
        f"- 命令：{report.get('命令文本')}",
        "",
        "## 输出摘要",
        "",
        "```text",
        str(report.get("stdout", ""))[:2000],
        str(report.get("stderr", ""))[:2000],
        "```",
        "",
        "## 安全结论",
        "",
        "本检查只验证本地登录态，不执行上传或发布。若检查失败，请先在本地终端执行对应平台 login 命令。",
        "",
    ])


def run_check(platform: str, account: str) -> dict[str, Any]:
    config = read_json(CONFIG_PATH)
    bridge = config.get("发布桥梁", {})
    command = str(bridge.get("命令", "sau"))
    normalized = normalize_platform(platform, config)
    account_name = account or str(bridge.get("默认账号", "creator"))
    cmd = [command, normalized, "check", "--account", account_name]
    report: dict[str, Any] = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "平台": normalized,
        "账号": account_name,
        "命令": cmd,
        "命令文本": " ".join(cmd),
        "stdout": "",
        "stderr": "",
        "returncode": None,
        "总体状态": "blocked",
        "安全边界": {
            "上传": False,
            "发布": False,
            "触发n8n": False,
            "企业微信真实发送": False,
        },
    }
    if not shutil.which(command):
        report["错误"] = f"未找到sau命令：{command}"
        return report
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
        report["stdout"] = completed.stdout
        report["stderr"] = completed.stderr
        report["returncode"] = completed.returncode
        report["总体状态"] = "pass" if completed.returncode == 0 else "blocked"
    except Exception as exc:  # noqa: BLE001
        report["错误"] = str(exc)
        report["traceback"] = traceback.format_exc()
    return report


def save_report(report: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    markdown = build_markdown(report)
    write_json(LATEST_JSON, report)
    write_text(LATEST_MD, markdown)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(ARCHIVE_DIR / f"发布账号检查_{timestamp}.json", report)
    write_text(ARCHIVE_DIR / f"发布账号检查_{timestamp}.md", markdown)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="轮次012发布账号登录态检查")
    parser.add_argument("--platform", required=True, help="平台，如 B站/bilibili/抖音/douyin")
    parser.add_argument("--account", default="", help="账号名；为空则使用配置默认账号")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_check(args.platform, args.account)
    save_report(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
