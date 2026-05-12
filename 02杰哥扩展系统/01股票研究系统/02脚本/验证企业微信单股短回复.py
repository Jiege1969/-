# -*- coding: utf-8 -*-
"""
名称：验证企业微信单股短回复.py
作用：验证企业微信单股短回复可生成，且复用股票助手统一单股短答模板，不再输出旧指标堆砌话术。
触发方式：python 验证企业微信单股短回复.py
依赖：Python标准库；生成企业微信单股短回复.py。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只运行本地短回复验收；不联网；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信单股短回复验收脚本；2026-05-04 改为验收统一模板、量化标准和旧话术拦截。
标识：stock-wework-single-brief-reply-verify
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
    generator = root / "02脚本" / "生成企业微信单股短回复.py"
    samples = ["新易盛", "浙商中拓", "光迅科技"]
    runs = [
        subprocess.run([sys.executable, str(generator), "--stock", stock], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        for stock in samples
    ]
    latest_json = root / "03数据" / "24企业微信短回复" / "企业微信单股短回复_最新.json"
    latest_md = root / "03数据" / "24企业微信短回复" / "企业微信单股短回复_最新.md"
    front_standard = root / "01配置" / "股票前台输出标准_v2.json"
    package = load_json(latest_json)
    standard = load_json(front_standard)
    single_template = standard.get("单股短答模板", {}) if isinstance(standard, dict) else {}
    forbidden_terms = single_template.get("禁止话术", []) if isinstance(single_template.get("禁止话术"), list) else []
    text = latest_md.read_text(encoding="utf-8") if latest_md.exists() else ""
    actions = package.get("实际动作", {})
    reply = package.get("短回复", "")
    checks: list[dict[str, Any]] = []
    add_check(checks, "短回复生成脚本存在", generator.exists(), str(generator))
    add_check(checks, "样例短回复全部生成成功", all(run.returncode == 0 for run in runs), [{"stdout": run.stdout.strip(), "stderr": run.stderr.strip()} for run in runs])
    add_check(checks, "最新JSON存在", latest_json.exists() and package.get("模式") == "dry_run_reply_brief_only", str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists() and "企业微信单股短回复草稿" in text, str(latest_md))
    add_check(checks, "短回复长度适合聊天窗口", 0 < package.get("短回复长度", 0) <= 1400, package.get("短回复长度"))
    add_check(checks, "复用统一股票助手入口", str(package.get("统一入口", "")).endswith("股票助手入口.py"), package.get("统一入口"))
    add_check(checks, "复用前台输出标准模板", str(package.get("模板来源", "")).endswith("股票前台输出标准_v2.json") and bool(single_template), package.get("模板来源"))
    add_check(checks, "包含单股量化观察字段", all(word in reply for word in ["当前判断", "操作策略", "关注条件", "转强条件", "成交标准", "风险线", "结论"]), reply)
    add_check(checks, "包含大白话量化阈值", all(word in reply for word in ["承接成立", "近5日成交活跃度", "平时的1.10倍", "明显活跃", "转为谨慎观察"]), reply)
    add_check(checks, "不输出旧技术指标堆砌", not any(word in reply for word in ["MA5", "MA20", "MA60", "RSI14", "MACD", "DIF", "DEA", "分层：", "数据健康度", "反馈："]), reply)
    add_check(checks, "不输出模板禁止话术", not any(term in reply for term in forbidden_terms), reply)
    add_check(checks, "高风险动作关闭", all(value is False for value in actions.values()), actions)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "企业微信单股短回复可生成并保持真实发送关闭。" if failed == 0 else "企业微信单股短回复存在失败项。",
    }
    output_dir = root / "04日志" / "企业微信短回复"
    output = output_dir / f"stock-wework-single-brief-reply-verify-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    latest = output_dir / "stock-wework-single-brief-reply-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
