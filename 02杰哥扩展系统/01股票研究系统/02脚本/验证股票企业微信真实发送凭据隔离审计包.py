# -*- coding: utf-8 -*-
"""
名称：验证股票企业微信真实发送凭据隔离审计包.py
作用：验证股票企业微信真实发送凭据隔离审计包已生成，并确认真实发送、n8n、OpenClaw和交易均保持关闭。
触发方式：python 验证股票企业微信真实发送凭据隔离审计包.py
依赖：Python标准库；生成股票企业微信真实发送凭据隔离审计包.py；股票企业微信真实发送凭据隔离审计规则.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地凭据隔离审计验收；不读取真实密钥内容；不调用企业微信接口；不真实发送企业微信；不触发n8n；不调用OpenClaw；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-28 创建股票企业微信真实发送凭据隔离审计包验收脚本。
标识：stock-wework-real-send-credential-isolation-audit-package-verify
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


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成股票企业微信真实发送凭据隔离审计包.py"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    latest_json = root / "03数据" / "40真实发送凭据隔离审计" / "股票企业微信真实发送凭据隔离审计包_最新.json"
    latest_md = root / "03数据" / "40真实发送凭据隔离审计" / "股票企业微信真实发送凭据隔离审计包_最新.md"
    report = load_json(latest_json)
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    actions = report.get("实际动作", {})
    config_audit = report.get("统一消息出口配置审计", {})
    package_audit = report.get("股票回复包审计", {})
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "生成脚本执行成功", result.returncode == 0, {"标准输出": result.stdout.strip(), "标准错误": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists() and "统一消息出口配置审计" in report, str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "股票企业微信真实发送凭据隔离审计包" in text, str(latest_md))
    add_check(checks, "统一出口仍为本地队列", config_audit.get("唯一出口") is True and config_audit.get("当前发送模式") == "本地队列" and config_audit.get("是否允许真实发送") is False, config_audit)
    add_check(checks, "股票回复包真实动作关闭", all(package_audit.get(key) is False for key in ["real_send", "trigger_n8n", "call_openclaw", "write_official_db", "write_old_system", "trade"]), package_audit)
    add_check(checks, "未命中阻断敏感词", report.get("敏感关键词命中") == [], report.get("敏感关键词命中"))
    add_check(checks, "审计未执行高风险动作", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票企业微信真实发送凭据隔离审计包可用。" if failed == 0 else "股票企业微信真实发送凭据隔离审计包存在失败项。",
    }
    output_dir = root / "04日志" / "真实发送凭据隔离审计"
    output = output_dir / f"stock-wework-real-send-credential-isolation-audit-package-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-wework-real-send-credential-isolation-audit-package-verify-最新.json"
    write_json(output, verify)
    write_json(latest, verify)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
