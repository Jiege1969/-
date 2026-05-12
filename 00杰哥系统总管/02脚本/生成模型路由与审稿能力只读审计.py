# -*- coding: utf-8 -*-
"""
名称：生成模型路由与审稿能力只读审计.py
作用：只读审计模型资源池、模型路由策略、Ollama可见模型、审稿sidecar和低负载闸口状态。
触发方式：python 生成模型路由与审稿能力只读审计.py
所属系统：00杰哥系统总管 / 01杰哥智能系统
安全边界：只读配置、日志和本地Ollama /api/tags；只写总管运行状态报告；
不拉取模型；不删除模型；不运行批量推理；不切换生产配置；不重启服务；不触发n8n；不交易。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
INTELLIGENCE = ROOT / "01杰哥智能系统"
CONFIG = MANAGER / "01配置"
OUT_DIR = MANAGER / "03数据" / "运行状态"
MODEL_POOL = CONFIG / "模型资源池登记规则.json"
MODEL_ROUTER = CONFIG / "模型路由策略.json"
OLLAMA_RULE = CONFIG / "双系统Ollama治理规则.json"
SERVICE_REGISTRY = CONFIG / "服务注册表.json"
REVIEW_LOG_DIR = INTELLIGENCE / "04日志" / "文稿质检"
OLLAMA_TAGS_URL = "http://127.0.0.1:29134/api/tags"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def latest_file(pattern: str) -> Path | None:
    files = sorted(REVIEW_LOG_DIR.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
    return files[0] if files else None


def fetch_ollama_tags() -> dict[str, Any]:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        names = sorted([item.get("name", "") for item in payload.get("models", []) if item.get("name")])
        return {"可访问": True, "模型数量": len(names), "模型名称": names, "错误": ""}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return {"可访问": False, "模型数量": 0, "模型名称": [], "错误": str(exc)}


def extract_route_models(router: dict[str, Any]) -> list[str]:
    models: set[str] = set()
    for items in router.get("模型分层", {}).values():
        for item in items:
            models.add(str(item))
    return sorted(models)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 模型路由与审稿能力只读审计",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## Ollama 可见模型",
        "",
        f"- 可访问：{report['Ollama可见模型']['可访问']}",
        f"- 模型数量：{report['Ollama可见模型']['模型数量']}",
    ]
    if report["Ollama可见模型"]["模型名称"]:
        for name in report["Ollama可见模型"]["模型名称"]:
            lines.append(f"- {name}")
    if report["Ollama可见模型"]["错误"]:
        lines.append(f"- 错误：{report['Ollama可见模型']['错误']}")
    lines.extend(["", "## 路由覆盖", ""])
    for item in report["路由覆盖"]:
        lines.append(f"- {item['任务']}：首选 `{item['首选']}`；兜底 `{item['兜底']}`")
    lines.extend(["", "## 审稿能力", ""])
    for key, value in report["审稿能力"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 风险与缺口", ""])
    for item in report["风险与缺口"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    pool = load_json(MODEL_POOL)
    router = load_json(MODEL_ROUTER)
    governance = load_json(OLLAMA_RULE)
    service_registry = load_json(SERVICE_REGISTRY)
    ollama_tags = fetch_ollama_tags()
    route_models = extract_route_models(router)
    expected_models = [item.get("名称", "") for item in pool.get("预计模型清单", []) if item.get("名称")]
    actual = set(ollama_tags.get("模型名称", []))
    missing_expected = [name for name in expected_models if name and name not in actual]
    review_sidecar = latest_file("text-reviewer-sidecar-verify-最新.json") or latest_file("text-reviewer-sidecar-verify-*.json")
    low_load_gate = latest_file("text-review-low-load-gate-verify-最新.json") or latest_file("text-review-low-load-gate-verify-*.json")
    review_sidecar_json = load_json(review_sidecar, {}) if review_sidecar else {}
    low_load_json = load_json(low_load_gate, {}) if low_load_gate else {}
    route_tasks = router.get("任务路由", [])

    risks = []
    if not ollama_tags["可访问"]:
        risks.append("v3 Ollama /api/tags 当前不可访问；按治理规则只记录状态，不自动启动或修复。")
    if missing_expected:
        risks.append("预计模型清单中存在当前不可见模型：" + "、".join(missing_expected[:8]))
    if not review_sidecar:
        risks.append("未找到文稿质检 sidecar 最新验收记录。")
    if not low_load_gate:
        risks.append("未找到文稿质检低负载闸口最新验收记录。")
    if not risks:
        risks.append("未发现阻断；本轮只读审计未改变运行配置。")

    report = {
        "名称": "模型路由与审稿能力只读审计",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": "只读审计已完成；模型路由、资源池、Ollama可见模型和审稿验收记录已形成状态报告，未执行模型推理或配置切换。",
        "配置文件": {
            "模型资源池": str(MODEL_POOL),
            "模型路由策略": str(MODEL_ROUTER),
            "双系统Ollama治理": str(OLLAMA_RULE),
            "服务注册表": str(SERVICE_REGISTRY),
        },
        "配置解析": {
            "模型资源池存在": MODEL_POOL.exists(),
            "模型路由策略存在": MODEL_ROUTER.exists(),
            "双系统Ollama治理存在": OLLAMA_RULE.exists(),
            "服务注册表存在": SERVICE_REGISTRY.exists(),
            "预计模型数量": len(expected_models),
            "路由模型数量": len(route_models),
            "任务路由数量": len(route_tasks),
        },
        "Ollama可见模型": ollama_tags,
        "模型差异": {
            "预计但当前不可见": missing_expected,
            "路由登记模型": route_models,
        },
        "路由覆盖": route_tasks,
        "审稿能力": {
            "sidecar验收记录": str(review_sidecar) if review_sidecar else "缺失",
            "sidecar结论": review_sidecar_json.get("结论") or review_sidecar_json.get("当前结论") or "未知",
            "低负载闸口记录": str(low_load_gate) if low_load_gate else "缺失",
            "低负载闸口结论": low_load_json.get("结论") or low_load_json.get("当前结论") or "未知",
        },
        "治理边界": governance.get("安全边界", {}) or governance.get("风险动作", {}),
        "生产切换边界": router.get("显存策略", {}).get("生产切换", "必须人工确认"),
        "服务注册摘要": {
            "服务数量": len(service_registry.get("服务", [])) if isinstance(service_registry.get("服务"), list) else len(service_registry),
            "包含Ollama": "Ollama" in json.dumps(service_registry, ensure_ascii=False) or "ollama" in json.dumps(service_registry, ensure_ascii=False),
        },
        "风险与缺口": risks,
        "安全边界": {
            "拉取模型": False,
            "删除模型": False,
            "运行批量推理": False,
            "切换生产配置": False,
            "重启服务": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    latest_json = OUT_DIR / "模型路由与审稿能力只读审计_最新.json"
    latest_md = OUT_DIR / "模型路由与审稿能力只读审计_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))

    print(json.dumps({
        "状态": "完成",
        "当前结论": report["当前结论"],
        "Ollama可访问": ollama_tags["可访问"],
        "可见模型数量": ollama_tags["模型数量"],
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
