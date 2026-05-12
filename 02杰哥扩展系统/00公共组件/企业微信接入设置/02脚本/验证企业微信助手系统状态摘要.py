# -*- coding: utf-8 -*-
"""
名称：验证企业微信接入设置状态摘要.py
作用：验证企业微信接入设置状态摘要生成链路可运行，并确认统一指令路由预演、本地调用预演、灰度放行门禁、真实发送、Webhook、n8n触发等高风险动作仍关闭。
触发方式：python 验证企业微信助手系统状态摘要.py
依赖：Python标准库；生成企业微信助手系统状态摘要.py（历史文件名，当前生成企业微信接入设置状态摘要）。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只运行本地状态摘要生成和验收；只写入04日志；不写真实凭据；不触发Webhook；不触发n8n；不发送企业微信；不写旧系统；不接入税收业务；不接入交易。
创建/修改记录：2026-04-29 创建企业微信接入设置状态摘要验收脚本；2026-04-29 增加统一指令路由预演验收项；2026-04-29 增加统一指令本地调用预演验收项；2026-04-29 增加统一指令灰度放行门禁验收项；2026-04-29 增加统一指令使用速查卡验收项；2026-04-29 增加统一指令本地服务验收项。
标识：wecom-assistant-system-status-summary-verify
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
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成企业微信助手系统状态摘要.py"
    latest_json = root / "03数据" / "07状态摘要" / "wecom-assistant-system-status-summary-最新.json"
    latest_md = root / "03数据" / "07状态摘要" / "企业微信接入设置状态摘要_最新.md"
    log_dir = root / "04日志"

    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON摘要存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown摘要存在", latest_md.exists(), str(latest_md))

    report = load_json(latest_json) if latest_json.exists() else {}
    summary = report.get("汇总", {})
    safety = report.get("安全边界", {})
    add_check(checks, "总体状态健康", summary.get("状态") == "healthy", summary)
    add_check(checks, "沙箱脚本无失败", summary.get("沙箱脚本失败数") == 0, summary)
    add_check(checks, "无高风险凭据发现", summary.get("凭据高风险发现数") == 0, summary)
    add_check(checks, "统一指令路由健康", summary.get("统一指令路由状态") == "healthy", summary)
    add_check(checks, "路由样例全部命中", summary.get("路由样例数量") == summary.get("路由命中期望数量") and summary.get("路由样例数量", 0) >= 6, summary)
    add_check(checks, "路由无真实动作", summary.get("路由真实动作数量") == 0, summary)
    add_check(checks, "统一指令本地调用健康", summary.get("统一指令本地调用状态") == "healthy", summary)
    add_check(checks, "本地调用样例全部成功", summary.get("本地调用样例数量") == summary.get("本地调用成功数量") and summary.get("本地调用样例数量", 0) >= 6, summary)
    add_check(checks, "本地调用无真实动作", summary.get("本地调用真实动作数量") == 0, summary)
    add_check(checks, "统一指令本地服务健康", summary.get("统一指令本地服务状态") == "healthy", summary)
    add_check(checks, "本地服务验收无失败", summary.get("本地服务验收失败数量") == 0, summary)
    add_check(checks, "本地服务覆盖核心入口", int(summary.get("本地服务验收通过数量", 0) or 0) >= 10, summary)
    add_check(checks, "统一指令速查卡健康", summary.get("统一指令速查卡状态") == "healthy", summary)
    add_check(checks, "速查卡覆盖常用入口", int(summary.get("速查卡指令数量", 0) or 0) >= 7, summary)
    add_check(checks, "速查卡刷新成功", summary.get("速查卡刷新退出码") == 0, summary)
    add_check(checks, "股票L3接入对齐通过", summary.get("股票L3接入对齐状态") == "passed", summary)
    add_check(checks, "股票L3接入对齐无失败", int_value(summary.get("股票L3接入对齐失败数量"), 1) == 0, summary)
    add_check(checks, "股票L3接入对齐覆盖完整", int_value(summary.get("股票L3接入对齐通过数量"), 0) == int_value(summary.get("股票L3接入对齐总数"), 1) and int_value(summary.get("股票L3接入对齐总数"), 0) >= 18, summary)
    add_check(checks, "灰度放行门禁通过", summary.get("灰度放行门禁状态") == "pass", summary)
    add_check(checks, "灰度放行无失败项", summary.get("灰度放行失败数量") == 0, summary)
    add_check(checks, "首轮真实消息上限为0", int_value(summary.get("最大首轮真实消息数"), 99) == 0, summary)
    add_check(checks, "真实发送禁用", safety.get("企业微信真实发送") is False, safety)
    add_check(checks, "Webhook关闭", safety.get("触发Webhook") is False, safety)
    add_check(checks, "n8n触发关闭", safety.get("触发n8n") is False, safety)
    add_check(checks, "未写真实凭据", safety.get("写入真实凭据") is False, safety)
    add_check(checks, "未写旧系统", safety.get("写旧系统") is False, safety)
    add_check(checks, "未接入税收", safety.get("接入税收") is False, safety)
    add_check(checks, "未接入交易", safety.get("交易接口") is False, safety)

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-assistant-system-status-summary-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
    }
    output = log_dir / "wecom-assistant-system-status-summary-verify-最新.json"
    write_json(output, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
