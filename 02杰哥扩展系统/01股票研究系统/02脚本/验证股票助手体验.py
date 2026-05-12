# -*- coding: utf-8 -*-
"""
名称：验证股票助手体验.py
作用：验证新股票研究系统独立体验入口的配置、脚本、服务接口和安全边界。
触发方式：python 验证股票助手体验.py
依赖：Python标准库；股票助手入口.py；股票助手体验配置.json；本地股票助手服务。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只访问127.0.0.1:19300；不写旧系统；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建股票助手体验验收脚本。
标识：stock-assistant-experience-verify
"""

from __future__ import annotations

import json
import urllib.request
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


def http_get_json(url: str, timeout: int = 5) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def http_post_json(url: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"名称": name, "通过": bool(passed), "详情": detail})


def main() -> int:
    root = module_root()
    config = load_json(root / "01配置" / "股票助手体验配置.json")
    service = config.get("服务", {})
    base_url = f"http://{service.get('地址', '127.0.0.1')}:{service.get('端口', 19300)}"
    checks: list[dict[str, Any]] = []

    add_check(checks, "配置声明不占用旧系统端口18300", service.get("端口") != 18300, service)
    add_check(checks, "交易接口关闭", config.get("安全边界", {}).get("是否自动交易") is False, config.get("安全边界"))
    add_check(checks, "不写旧系统", config.get("安全边界", {}).get("是否写旧系统") is False, config.get("安全边界"))

    try:
        health = http_get_json(base_url + "/health")
        add_check(checks, "健康接口可用", health.get("状态") == "正常", health)
    except Exception as exc:  # noqa: BLE001
        health = {"错误": str(exc)}
        add_check(checks, "健康接口可用", False, health)

    try:
        watchlist = http_get_json(base_url + "/watchlist")
        add_check(checks, "重点关注池可读取", len(watchlist.get("重点关注池", [])) == 19, len(watchlist.get("重点关注池", [])))
    except Exception as exc:  # noqa: BLE001
        add_check(checks, "重点关注池可读取", False, str(exc))

    try:
        analysis = http_post_json(base_url + "/analyze", {"问题": "分析新易盛"})
        add_check(checks, "分析接口可用", analysis.get("状态") == "完成" and "研究助手快评" in analysis.get("回复", ""), analysis.get("回复", ""))
    except Exception as exc:  # noqa: BLE001
        add_check(checks, "分析接口可用", False, str(exc))

    try:
        ledger = http_get_json(base_url + "/ledger/latest")
        ledgers = ledger.get("复盘账本", {})
        add_check(checks, "复盘账本入口可用", ledger.get("状态") == "完成" and "系统判断账" in ledgers and "结果验证计划" in ledgers, ledger)
    except Exception as exc:  # noqa: BLE001
        add_check(checks, "复盘账本入口可用", False, str(exc))

    try:
        feedback = http_post_json(base_url + "/feedback", {"反馈": "继续观察：新易盛，原因：体验验收样例"})
        add_check(checks, "人工反馈入口可用", feedback.get("状态") == "完成" and "新易盛" in feedback.get("标准输出", ""), feedback)
    except Exception as exc:  # noqa: BLE001
        add_check(checks, "人工反馈入口可用", False, str(exc))

    try:
        candidate = http_get_json(base_url + "/candidate/latest")
        pool = candidate.get("候选池", {}).get("候选池", {})
        add_check(checks, "候选池入口可用", candidate.get("状态") == "完成" and any(pool.get(key) for key in ["L5深度研究", "L6轻度关注", "L7系统过滤"]), candidate)
    except Exception as exc:  # noqa: BLE001
        add_check(checks, "候选池入口可用", False, str(exc))

    try:
        l5 = http_get_json(base_url + "/l5/latest")
        add_check(checks, "L5深度研究入口可用", l5.get("状态") == "完成" and "候选池" in l5.get("L5深度研究", {}), l5)
        add_check(checks, "L5数据健康度可读取", l5.get("L5深度研究", {}).get("数据健康度", {}).get("健康等级") in {"优秀", "可用", "降级", "暂停"}, l5.get("L5深度研究", {}).get("数据健康度", {}))
    except Exception as exc:  # noqa: BLE001
        add_check(checks, "L5深度研究入口可用", False, str(exc))
        add_check(checks, "L5数据健康度可读取", False, str(exc))

    try:
        review_loop = http_post_json(base_url + "/review-loop/run", {})
        add_check(checks, "L5复盘联动入口可用", review_loop.get("状态") == "完成", review_loop)
    except Exception as exc:  # noqa: BLE001
        add_check(checks, "L5复盘联动入口可用", False, str(exc))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "服务地址": base_url,
        "通过": passed,
        "失败": failed,
        "检查项": checks,
        "结论": "股票助手体验入口可独立使用。" if failed == 0 else "股票助手体验入口仍需处理失败项。",
    }
    output_dir = root / "04日志" / "助手入口"
    output = output_dir / "stock-assistant-experience-verify-最新.json"
    latest = output_dir / "stock-assistant-experience-verify-最新.json"
    write_json(output, report)
    write_json(latest, report)
    print(json.dumps({"通过": passed, "失败": failed, "输出": str(output)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
