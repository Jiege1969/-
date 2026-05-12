# -*- coding: utf-8 -*-
"""
名称：验证机器人串线影子干预器.py
作用：验证EWF-005机器人串线影子干预器的规则、边界和19310影子日志。
所属系统：02杰哥扩展系统/00公共组件
边界：只读验证；不真实发送企业微信、不触发n8n、不调用券商接口、不自动交易。
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from 机器人串线影子干预器 import CrossWireIntervention


ROOT = Path("D:/杰哥智能化系统")
OUT_DIR = ROOT / "03杰哥进化系统" / "03数据" / "38本轮税收微信股票通过经验进化候选补充"
WECOM_LOG = ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置" / "04日志" / "统一指令本地服务" / "机器人串线影子干预器" / "EWF-005_机器人串线影子干预_最新.json"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def post_json(url: str, payload: dict[str, Any], timeout: int = 20) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def check(name: str, passed: bool, detail: Any = "") -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "详情": detail}


def main() -> int:
    detector = CrossWireIntervention()
    direct_cases = [
        ("/wecom/work-secretary", "帮我分析一下沪电股份", "杰哥私人股票分析顾问"),
        ("/wecom/video-assistant", "今天股票行情怎么看", "杰哥私人股票分析顾问"),
        ("/wecom-bot/message", "帮我做一个视频分镜脚本", "杰哥视频助理"),
        ("/wecom/work-secretary", "帮我整理一份工作汇报材料", ""),
    ]
    checks: list[dict[str, Any]] = []

    for route, text, expected_robot in direct_cases:
        result = detector.check(route, text)
        if expected_robot:
            passed = result.get("intervention_needed") is True and result.get("suggested_robot") == expected_robot and result.get("shadow_only") is True
        else:
            passed = result.get("intervention_needed") is False and result.get("shadow_only") is True
        checks.append(check(f"直接规则：{route} / {text}", passed, result))

    service_result: dict[str, Any] = {}
    try:
        service_result = post_json("http://127.0.0.1:19310/wecom/work-secretary", {"text": "今天股票行情怎么看"}, timeout=60)
        checks.append(check("19310仍返回原业务路由结果", bool(service_result.get("回复") or service_result.get("reply_text")), service_result))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("19310仍返回原业务路由结果", False, str(exc)))

    latest_log = json.loads(WECOM_LOG.read_text(encoding="utf-8-sig")) if WECOM_LOG.exists() else {}
    checks.append(check("19310写入影子干预日志", latest_log.get("消息类型") == "机器人串线影子干预", latest_log))
    checks.append(check("影子日志声明不改变核心路由", latest_log.get("不改变核心路由") is True, latest_log))
    safety = latest_log.get("安全边界", {})
    checks.append(check("安全边界关闭", safety.get("真实发送企业微信") is False and safety.get("触发n8n") is False and safety.get("调用券商接口") is False and safety.get("自动交易") is False, safety))

    passed = sum(1 for item in checks if item["通过"])
    failed = len(checks) - passed
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "类型": "EWF-005-cross-wire-shadow-intervention-verify",
        "汇总": {"状态": "pass" if failed == 0 else "fail", "通过": passed, "失败": failed},
        "检查项": checks,
        "安全边界": {
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "改变核心路由": False,
        },
    }
    out = OUT_DIR / "EWF-005_影子干预器验证_最新.json"
    write_json(out, report)
    print(json.dumps({"状态": report["汇总"]["状态"], "通过": passed, "失败": failed, "输出": str(out)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
