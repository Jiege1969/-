# -*- coding: utf-8 -*-
"""
名称：验证企业微信统一指令路由预演.py
作用：验证企业微信统一指令路由预演可生成，并确认路由判断不触发真实发送、Webhook、n8n、正式写库、旧系统写入、税收真实业务和交易接口。
触发方式：python 验证企业微信统一指令路由预演.py
依赖：Python标准库；生成企业微信统一指令路由预演.py。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只运行本地预演和验收；只写入本系统04日志；不真实发送企业微信；不触发Webhook；不触发n8n；不写正式库；不写旧系统；不接入税收真实业务；不接入交易。
创建/修改记录：2026-04-29 创建企业微信统一指令路由预演验收脚本。
标识：wecom-unified-command-router-preview-verify
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


def main() -> int:
    root = module_root()
    generator = root / "02脚本" / "生成企业微信统一指令路由预演.py"
    latest_json = root / "03数据" / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json"
    latest_md = root / "03数据" / "08统一指令路由预演" / "企业微信统一指令路由预演_最新.md"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    report = load_json(latest_json) if latest_json.exists() else {}
    summary = report.get("汇总", {})
    safety = report.get("安全边界", {})
    routes = {item.get("命中路由") for item in report.get("样例结果", [])}
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists(), str(latest_md))
    add_check(checks, "总体状态健康", summary.get("状态") == "healthy", summary)
    add_check(checks, "样例全部命中期望", summary.get("样例数量") == summary.get("命中期望数量") and summary.get("样例数量", 0) >= 6, summary)
    add_check(checks, "股票路由存在", "股票研究" in routes, sorted(routes))
    add_check(checks, "系统状态路由存在", "系统状态" in routes, sorted(routes))
    add_check(checks, "税收待复核分析路由存在", "税收业务待复核分析" in routes, sorted(routes))
    add_check(checks, "兜底澄清存在", "澄清一次" in routes, sorted(routes))
    add_check(checks, "无真实动作", summary.get("真实动作数量") == 0, summary)
    add_check(checks, "未真实发送企业微信", safety.get("真实发送企业微信") is False, safety)
    add_check(checks, "未触发Webhook", safety.get("触发Webhook") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未写正式库", safety.get("写正式库") is False, safety)
    add_check(checks, "未写旧系统", safety.get("写旧系统") is False, safety)
    add_check(checks, "未接入税收真实业务", safety.get("接入税收真实业务") is False, safety)
    add_check(checks, "未接入交易", safety.get("交易接口") is False, safety)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-unified-command-router-preview-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
    }
    output = root / "04日志" / "wecom-unified-command-router-preview-verify-最新.json"
    write_json(output, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
