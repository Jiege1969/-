# -*- coding: utf-8 -*-
"""
名称：生成企业微信助手知识库问答入口禁用态桥接检查.py
作用：只读检查企业微信助手知识库问答路由与知识库只读入口方案之间的禁用态桥接边界。
触发方式：python 生成企业微信助手知识库问答入口禁用态桥接检查.py
安全边界：只读现有预演产物并写总管报告；不接正式入口、不调用企业微信、不触发Webhook/n8n、不启动问答、不入库。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
WECOM = ROOT / "02杰哥扩展系统" / "06企业微信助手系统"
OUT_DIR = MANAGER / "03数据" / "运行状态"
ENTRY_PLAN = OUT_DIR / "知识库只读问答入口影子方案_最新.json"
ROUTE_PREVIEW = WECOM / "03数据" / "08统一指令路由预演" / "wecom-unified-command-router-preview-最新.json"
LOCAL_CALL = WECOM / "03数据" / "09统一指令本地调用预演" / "wecom-unified-command-local-call-preview-最新.json"
QUICK_CARD = WECOM / "03数据" / "11统一指令使用速查卡" / "wecom-unified-command-quick-card-最新.json"
WECOM_BASELINE = OUT_DIR / "企业微信助手统一路由状态基线_最新.json"
REPORT_JSON = OUT_DIR / "企业微信助手知识库问答入口禁用态桥接检查_最新.json"
REPORT_MD = OUT_DIR / "企业微信助手知识库问答入口禁用态桥接检查_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def find_route(items: list[dict[str, Any]], key: str) -> dict[str, Any]:
    for item in items:
        if item.get("命中路由") == key or item.get("路由") == key:
            return item
    return {}


def main() -> int:
    entry_plan = load_json(ENTRY_PLAN, {})
    route_preview = load_json(ROUTE_PREVIEW, {})
    local_call = load_json(LOCAL_CALL, {})
    quick_card = load_json(QUICK_CARD, {})
    baseline = load_json(WECOM_BASELINE, {})
    route_item = find_route(route_preview.get("样例结果", []), "知识库问答")
    local_item = find_route(local_call.get("调用结果", []), "知识库问答")
    quick_item = find_route(quick_card.get("指令", []), "知识库问答")
    baseline_summary = baseline.get("汇总", {})
    checks = [
        {"检查项": "知识库只读入口影子方案存在", "通过": ENTRY_PLAN.exists(), "说明": str(ENTRY_PLAN)},
        {"检查项": "影子方案未接正式入口", "通过": entry_plan.get("安全边界", {}).get("接入正式入口") is False, "说明": entry_plan.get("安全边界", {})},
        {"检查项": "企业微信路由预演存在知识库问答", "通过": bool(route_item), "说明": route_item},
        {"检查项": "路由预演知识库问答无真实动作", "通过": route_item.get("真实动作") is False, "说明": route_item},
        {"检查项": "本地调用预演存在知识库问答", "通过": bool(local_item), "说明": local_item.get("来源", "")},
        {"检查项": "本地调用预演未真实发送/未触发n8n", "通过": local_item.get("真实发送企业微信") is False and local_item.get("触发n8n") is False, "说明": local_item},
        {"检查项": "速查卡存在知识库问答且无真实动作", "通过": bool(quick_item) and quick_item.get("真实动作") is False, "说明": quick_item},
        {"检查项": "企业微信助手统一路由基线健康", "通过": baseline_summary.get("系统状态") == "healthy" and baseline_summary.get("路由状态") == "healthy", "说明": baseline_summary},
        {"检查项": "企业微信真实发送/Webhook/n8n关闭", "通过": baseline_summary.get("企业微信真实发送") is False and baseline_summary.get("触发Webhook") is False and baseline_summary.get("触发n8n") is False, "说明": baseline_summary},
    ]
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "企业微信助手知识库问答入口禁用态桥接检查",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "引用产物": {
            "知识库只读入口影子方案": str(ENTRY_PLAN),
            "企业微信路由预演": str(ROUTE_PREVIEW),
            "企业微信本地调用预演": str(LOCAL_CALL),
            "企业微信速查卡": str(QUICK_CARD),
            "企业微信统一路由状态基线": str(WECOM_BASELINE),
        },
        "知识库路由": {
            "路由预演": route_item,
            "本地调用预演": local_item,
            "速查卡": quick_item,
        },
        "检查结果": checks,
        "安全边界": {
            "接入正式入口": False,
            "调用企业微信接口": False,
            "真实发送企业微信": False,
            "触发Webhook": False,
            "触发n8n": False,
            "启动问答": False,
            "调用模型推理": False,
            "写正式知识库": False,
            "写Qdrant": False,
            "写PostgreSQL": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    lines = [
        "# 企业微信助手知识库问答入口禁用态桥接检查",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "本轮只读检查禁用态桥接，不接入正式入口，不调用企业微信接口，不真实发送，不触发 Webhook/n8n，不启动问答，不写库。",
    ])
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines) + "\n")
    print(json.dumps({"状态": report["结论"], "通过数量": report["通过数量"], "失败数量": report["失败数量"], "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
