# -*- coding: utf-8 -*-
"""
Name: generate-stock-assistant-local-delivery-functional-acceptance-package.py
Purpose: Generate local functional acceptance package for stock assistant delivery readiness.
Trigger: python 生成股票助手本地交付功能验收包.py
Dependencies: Python standard library; local stock assistant service at 127.0.0.1:19300.
Owner system: 02杰哥扩展系统/01股票研究系统
Safety: Calls local stock assistant only; does not restart, enable or trigger Webhook, call OpenClaw, send WeWork messages, write old system, write production DB, call broker APIs, or trade.
Change log: 2026-04-28 created local delivery functional acceptance package generator.
Marker: stock-assistant-local-delivery-functional-acceptance-package-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def http_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=data, method=method, headers={"Content-Type": "application/json", "User-Agent": "jiege-stock-local-delivery-acceptance"})
    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
            try:
                body: Any = json.loads(text)
            except json.JSONDecodeError:
                body = {"文本": text[:1000]}
            return {"通过": 200 <= response.status < 300, "状态码": response.status, "内容": body}
    except HTTPError as exc:
        return {"通过": False, "状态码": exc.code, "内容": str(exc)}
    except URLError as exc:
        return {"通过": False, "状态码": None, "内容": str(exc.reason)}
    except Exception as exc:
        return {"通过": False, "状态码": None, "内容": str(exc)}


def text_get(url: str, timeout: int = 10) -> dict[str, Any]:
    request = Request(url, method="GET", headers={"User-Agent": "jiege-stock-local-delivery-acceptance"})
    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8", errors="replace")
            return {"通过": 200 <= response.status < 300 and len(text.strip()) > 20, "状态码": response.status, "片段": text[:1000], "长度": len(text)}
    except Exception as exc:
        return {"通过": False, "状态码": None, "片段": str(exc), "长度": 0}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票助手本地交付功能验收包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 一、验收结论",
        "",
        f"- 通过：{report['通过']}",
        f"- 失败：{report['失败']}",
        f"- 是否达到本地交付功能要求：{report['是否达到本地交付功能要求']}",
        "",
        "## 二、检查结果",
        "",
    ]
    for item in report["检查结果"]:
        lines.append(f"- {item['检查项']}：{item['通过']}，{item['说明']}")
    lines.extend(["", "## 三、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    base_url = "http://127.0.0.1:19300"
    checks: list[dict[str, Any]] = []
    health = http_json("GET", base_url + "/health", timeout=10)
    watchlist = http_json("GET", base_url + "/watchlist", timeout=10)
    data_health = http_json("GET", base_url + "/data-health", timeout=10)
    status_summary = http_json("GET", base_url + "/status-summary", timeout=10)
    daily_package = http_json("GET", base_url + "/daily-package", timeout=10)
    report_latest = text_get(base_url + "/report/latest", timeout=10)
    candidate_latest = http_json("GET", base_url + "/candidate/latest", timeout=10)
    l5_latest = http_json("GET", base_url + "/l5/latest", timeout=10)
    analysis = http_json("POST", base_url + "/analyze", {"问题": "分析新易盛"}, timeout=60)
    health_body = health.get("内容", {}) if isinstance(health.get("内容"), dict) else {}
    watch_body = watchlist.get("内容", {}) if isinstance(watchlist.get("内容"), dict) else {}
    analysis_body = analysis.get("内容", {}) if isinstance(analysis.get("内容"), dict) else {}
    checks.extend([
        {"检查项": "健康接口", "通过": health.get("通过") and health_body.get("状态") == "正常", "说明": str(health_body)[:300]},
        {"检查项": "重点关注池", "通过": watchlist.get("通过") and len(watch_body.get("重点关注池", [])) >= 19, "说明": f"数量={len(watch_body.get('重点关注池', []))}"},
        {"检查项": "数据健康度", "通过": data_health.get("通过") and isinstance(data_health.get("内容"), dict), "说明": str(data_health.get("内容"))[:300]},
        {"检查项": "状态摘要", "通过": status_summary.get("通过") and isinstance(status_summary.get("内容"), dict), "说明": str(status_summary.get("内容"))[:300]},
        {"检查项": "日常使用包", "通过": daily_package.get("通过") and isinstance(daily_package.get("内容"), dict), "说明": str(daily_package.get("内容"))[:300]},
        {"检查项": "最新研究报告", "通过": report_latest.get("通过"), "说明": f"长度={report_latest.get('长度')}"},
        {"检查项": "候选池", "通过": candidate_latest.get("通过") and isinstance(candidate_latest.get("内容"), dict), "说明": str(candidate_latest.get("内容"))[:300]},
        {"检查项": "L5深度研究", "通过": l5_latest.get("通过") and isinstance(l5_latest.get("内容"), dict), "说明": str(l5_latest.get("内容"))[:300]},
        {"检查项": "单股分析", "通过": analysis.get("通过") and "研究助手快评" in str(analysis_body.get("回复", "")), "说明": str(analysis_body.get("回复", ""))[:300]},
        {"检查项": "旧系统写入关闭", "通过": health_body.get("旧系统写入") is False, "说明": str(health_body.get("旧系统写入"))},
    ])
    failed = [item for item in checks if not item["通过"]]
    core_required = {"健康接口", "重点关注池", "最新研究报告", "候选池", "L5深度研究", "单股分析", "旧系统写入关闭"}
    core_passed = all(item["通过"] for item in checks if item["检查项"] in core_required)
    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "服务地址": base_url,
        "检查结果": checks,
        "通过": len(checks) - len(failed),
        "失败": len(failed),
        "核心本地查询能力是否可用": core_passed,
        "是否达到本地交付功能要求": not failed,
        "未通过项": [item["检查项"] for item in failed],
        "差距结论": "核心本地查询能力可用；完整交付仍需刷新本地股票助手服务，使新增路由生效。" if core_passed and failed else ("本地交付功能完整通过。" if not failed else "核心本地查询能力仍需修复。"),
        "原始响应摘要": {
            "健康接口": health,
            "重点关注池": {"状态码": watchlist.get("状态码"), "通过": watchlist.get("通过")},
            "单股分析": {"状态码": analysis.get("状态码"), "通过": analysis.get("通过"), "回复片段": str(analysis_body.get("回复", ""))[:600]}
        },
        "实际动作": {
            "调用本地助手接口": True,
            "重启服务": False,
            "启用Webhook": False,
            "触发Webhook": False,
            "调用OpenClaw": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        }
    }
    output_dir = root / "03数据" / "81股票助手本地交付功能验收包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = output_dir / f"股票助手本地交付功能验收包_{stamp}.json"
    latest_json = output_dir / "股票助手本地交付功能验收包_最新.json"
    output_md = output_dir / f"股票助手本地交付功能验收包_{stamp}.md"
    latest_md = output_dir / "股票助手本地交付功能验收包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"通过": report["通过"], "失败": report["失败"], "输出": str(output_json)}, ensure_ascii=False))
    return 0 if core_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
