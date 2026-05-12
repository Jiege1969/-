# -*- coding: utf-8 -*-
"""
名称：验证企业微信统一指令使用速查卡.py
作用：验证企业微信统一指令使用速查卡可生成，且内容覆盖股票、系统状态、知识库、内容办公、视频、税收待复核分析和澄清入口。
触发方式：python 验证企业微信统一指令使用速查卡.py
依赖：Python标准库；生成企业微信统一指令使用速查卡.py。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只运行本地速查卡生成和验收；只写入本系统04日志；不真实发送企业微信；不触发Webhook；不触发n8n；不写旧系统；不接入税收真实业务；不接入交易。
创建/修改记录：2026-04-29 创建企业微信统一指令使用速查卡验收脚本。
标识：wecom-unified-command-quick-card-verify
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


OLD_STOCK_WORDS = ["买入研究信号", "研究星级", "19300/technical", "technical?stock", "新易盛（sz300502）"]


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
    generator = root / "02脚本" / "生成企业微信统一指令使用速查卡.py"
    latest_json = root / "03数据" / "11统一指令使用速查卡" / "wecom-unified-command-quick-card-最新.json"
    latest_md = root / "03数据" / "11统一指令使用速查卡" / "企业微信统一指令使用速查卡_最新.md"
    doc_md = root / "07文档" / "企业微信统一指令使用速查卡.md"
    result = subprocess.run([sys.executable, str(generator)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    card = load_json(latest_json) if latest_json.exists() else {}
    routes = {item.get("路由") for item in card.get("指令", [])}
    safety = card.get("安全边界", {})
    required_routes = {"股票研究", "系统状态", "知识库问答", "内容办公处理", "视频制作", "税收业务待复核分析", "澄清一次"}
    card_text = json.dumps(card, ensure_ascii=False)
    checks: list[dict[str, Any]] = []
    add_check(checks, "生成脚本返回码", result.returncode == 0, {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    add_check(checks, "最新JSON存在", latest_json.exists(), str(latest_json))
    add_check(checks, "最新Markdown存在", latest_md.exists(), str(latest_md))
    add_check(checks, "文档速查卡存在", doc_md.exists(), str(doc_md))
    add_check(checks, "总体状态健康", card.get("总体状态") == "healthy", card.get("总体状态"))
    add_check(checks, "关键路由覆盖完整", required_routes.issubset(routes), sorted(routes))
    add_check(
        checks,
        "股票推荐说法可直接使用",
        any(item.get("路由") == "股票研究" and item.get("推荐说法") and item.get("当前返回预演") for item in card.get("指令", [])),
        card.get("指令", []),
    )
    add_check(checks, "速查卡不含旧股票模板", not any(word in card_text for word in OLD_STOCK_WORDS), "")
    add_check(checks, "包含税收待复核分析边界", any(item.get("路由") == "税收业务待复核分析" for item in card.get("指令", [])), sorted(routes))
    add_check(checks, "未真实发送企业微信", safety.get("真实发送企业微信") is False, safety)
    add_check(checks, "未触发Webhook", safety.get("触发Webhook") is False, safety)
    add_check(checks, "未触发n8n", safety.get("触发n8n") is False, safety)
    add_check(checks, "未写旧系统", safety.get("写旧系统") is False, safety)
    add_check(checks, "未写正式库", safety.get("写正式库") is False, safety)
    add_check(checks, "未接入交易", safety.get("交易接口") is False, safety)
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    verify_report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-unified-command-quick-card-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
    }
    output = root / "04日志" / "wecom-unified-command-quick-card-verify-最新.json"
    write_json(output, verify_report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
