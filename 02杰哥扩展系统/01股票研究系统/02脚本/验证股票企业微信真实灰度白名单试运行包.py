# -*- coding: utf-8 -*-
"""
名称：验证股票企业微信真实灰度白名单试运行包.py
作用：验证股票企业微信真实灰度白名单试运行包是否具备白名单、试运行用例、前置条件和安全边界。
触发方式：python 验证股票企业微信真实灰度白名单试运行包.py
依赖：Python标准库；生成股票企业微信真实灰度白名单试运行包.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读取本地文件并写入04日志；不删除文件；不覆盖配置；不重启服务；不调用n8n API；不触发n8n；不调用OpenClaw；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票企业微信真实灰度白名单试运行包验收脚本。
标识：stock-wework-real-gray-whitelist-trial-package-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    checks.append({"检查项": name, "通过": ok, "说明": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票企业微信真实灰度白名单试运行包.py"
    subprocess.run([sys.executable, str(generator)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    latest = root / "03数据" / "42真实灰度白名单试运行" / "股票企业微信真实灰度白名单试运行包_最新.json"
    report = load_json(latest)
    checks: list[dict[str, Any]] = []
    whitelist = report.get("白名单草案", {})
    cases = report.get("试运行用例", [])
    case_types = {item.get("输入类型") for item in cases}
    actions = report.get("实际动作", {})

    add_check(checks, "最新白名单试运行包存在", latest.exists(), str(latest))
    add_check(checks, "试运行材料结论通过", report.get("是否满足灰度试运行材料要求") is True, str(report.get("当前结论", "")))
    add_check(checks, "白名单禁止全员和群发", whitelist.get("允许全员发送") is False and whitelist.get("禁止群发") is True, str(whitelist))
    add_check(checks, "默认接收人待人工确认", "待人工确认" in str(whitelist.get("默认接收人", "")), str(whitelist.get("默认接收人", "")))
    add_check(checks, "试运行用例覆盖完整", len(cases) >= 5 and {"文字", "重庆话语音转写", "模糊语音转写", "越权请求"}.issubset(case_types), str(case_types))
    add_check(checks, "前置条件完整", all(report.get("前置条件", {}).values()), str(report.get("前置条件", {})))
    add_check(checks, "不触发真实动作", all(actions.get(key) is True for key in [
        "不删除文件",
        "不覆盖配置",
        "不重启服务",
        "不调用n8n API",
        "不触发n8n",
        "不调用OpenClaw",
        "不发送企业微信",
        "不写正式库",
        "不写旧系统",
        "不调用券商接口",
        "不自动交易",
    ]), str(actions))

    failed = [item for item in checks if not item["通过"]]
    result = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "检查结果": checks,
        "通过": len(checks) - len(failed),
        "失败": len(failed),
    }
    log_dir = root / "04日志" / "真实灰度白名单试运行"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = log_dir / f"stock-wework-real-gray-whitelist-trial-package-verify-{stamp}.json"
    latest_output = log_dir / "stock-wework-real-gray-whitelist-trial-package-verify-最新.json"
    write_json(output, result)
    write_json(latest_output, result)
    print(json.dumps({"通过": result["通过"], "失败": result["失败"], "输出": str(output)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
