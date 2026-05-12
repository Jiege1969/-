# -*- coding: utf-8 -*-
"""
名称：验证企业微信统一指令本地服务入口.py
作用：验证企业微信统一指令本地HTTP服务可用，并确认股票、系统状态、税收待复核分析和澄清入口均只在低风险本地范围内执行。
触发方式：python 验证企业微信统一指令本地服务入口.py
依赖：Python标准库；企业微信统一指令本地服务入口.py正在监听127.0.0.1:19310。
所属系统：02杰哥扩展系统/00公共组件/企业微信接入设置
安全边界：只请求127.0.0.1本地服务并写入本系统04日志；不真实发送企业微信；不触发Webhook；不触发n8n；不写正式库；不写旧系统；不接入税收真实业务；不接入交易。
创建/修改记录：2026-04-29 创建企业微信统一指令本地服务入口验收脚本；2026-05-06 兼容系统管家确定性状态查询当前路由；2026-05-08 迁入公共接入设置后改用当前路由样例。
标识：wecom-unified-command-local-service-verify
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


SERVICE = "http://127.0.0.1:19310"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_json(url: str, timeout: int = 20) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def post_json(url: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def safety_closed(item: dict[str, Any]) -> bool:
    safety = item.get("安全边界", {})
    return (
        safety.get("真实发送企业微信") is False
        and safety.get("触发Webhook") is False
        and safety.get("触发n8n") is False
        and safety.get("写旧系统") is False
        and safety.get("交易接口") is False
    )


def main() -> int:
    root = module_root()
    health = get_json(f"{SERVICE}/health")
    stock = post_json(f"{SERVICE}/command", {"text": "分析云南锗业"})
    status = get_json(f"{SERVICE}/command?text={urllib.request.quote('系统现在进度多少')}" if False else f"{SERVICE}/command?text=%E7%B3%BB%E7%BB%9F%E7%8E%B0%E5%9C%A8%E8%BF%9B%E5%BA%A6%E5%A4%9A%E5%B0%91")
    tax = post_json(f"{SERVICE}/wecom/unified", {"content": "增值税政策怎么处理"})
    clarify = post_json(f"{SERVICE}/command", {"message": "这个事情你怎么看"})
    checks: list[dict[str, Any]] = []
    add_check(checks, "健康入口正常", health.get("状态") == "正常" and health.get("地址") == SERVICE, health)
    add_check(checks, "绑定本机地址", health.get("安全边界", {}).get("绑定地址") == "127.0.0.1", health.get("安全边界", {}))
    add_check(checks, "股票指令可返回", stock.get("路由") == "股票研究" and bool(str(stock.get("回复", "")).strip()), stock)
    status_route_ok = status.get("路由") in {"系统状态", "系统管家确定性状态查询"} or status.get("route") == "system-manager-status"
    status_reply = str(status.get("回复", ""))
    status_reply_ok = ("当前进度" in status_reply and "安全边界" in status_reply) or "日常可用版总览面板" in status_reply
    add_check(checks, "系统状态指令可返回", status_route_ok and status_reply_ok, status)
    tax_route_ok = tax.get("路由") == "税收业务待复核分析"
    tax_safe_ok = tax.get("安全边界", {}).get("接入税收真实业务") is False
    add_check(checks, "税收业务保持低风险边界", tax_route_ok and tax_safe_ok and bool(str(tax.get("回复", "")).strip()), tax)
    add_check(checks, "澄清入口可用", clarify.get("路由") == "澄清一次" and clarify.get("状态") == "需澄清", clarify)
    for name, item in {"股票": stock, "系统状态": status, "税收": tax, "澄清": clarify}.items():
        add_check(checks, f"{name}安全边界关闭", safety_closed(item), item.get("安全边界", {}))
    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "wecom-unified-command-local-service-verify",
        "汇总": {"通过": passed, "失败": failed},
        "检查项": checks,
        "安全边界": {
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "写正式库": False,
            "写旧系统": False,
            "接入税收真实业务": False,
            "交易接口": False,
        },
    }
    output = root / "04日志" / "wecom-unified-command-local-service-verify-最新.json"
    write_json(output, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
