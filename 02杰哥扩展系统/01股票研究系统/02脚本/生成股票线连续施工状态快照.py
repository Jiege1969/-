# -*- coding: utf-8 -*-
"""
生成股票线连续施工状态快照。

只汇总股票线 W1/W2 资产状态，不修改总管、企业微信、n8n、服务或正式配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_DIR = BASE_DIR / "03数据" / "245L3评分基础资产"
JSON_OUT = DATA_DIR / "股票线连续施工状态快照_最新.json"
MD_OUT = DATA_DIR / "股票线连续施工状态快照_最新.md"

COMPLETED_ASSETS = [
    "前台缺口话术规则草案",
    "五样本前台结论型短答验收清单",
    "五样本前台结论型短答修订样例",
    "后台证据链到前台短答字段映射草案",
    "五样本后台到前台字段映射验收样例",
    "五样本财报资金证据补齐路线图",
    "五样本财报资金证据采集模板草案",
    "股票L3五样本统一刷新验收清单",
    "股票L3统一刷新验收执行记录模板",
    "股票L3统一刷新验收执行记录样例",
    "影子前台短答刷新验收样例",
]

REMAINING_DEBTS = [
    {
        "debt": "真实财报/资金字段仍未采集",
        "status": "open",
        "reason": "当前只有空白采集模板，未抓取真实数据、未人工填写、未 evidence_ready。",
        "next_low_risk_action": "生成人工填写回执模板或字段填报说明。",
    },
    {
        "debt": "市场风格日表仍需连续刷新样例",
        "status": "open",
        "reason": "已有市场风格 schema/样例方向，但未形成与五样本统一刷新执行记录的每日样例闭环。",
        "next_low_risk_action": "生成市场风格日表影子刷新记录模板。",
    },
    {
        "debt": "行业价格连续观测仍缺真实观测点",
        "status": "open",
        "reason": "已有补数队列，但大部分样本观测点不足，不能写趋势确认。",
        "next_low_risk_action": "生成行业价格观测人工填报回执模板。",
    },
    {
        "debt": "复盘闭环仍未进入自动修正规则",
        "status": "open",
        "reason": "当前只能生成候选和验收，人工修正不能自动改正式规则。",
        "next_low_risk_action": "生成复盘人工修正候选接收模板。",
    },
]


def latest_acceptance_files() -> list[dict]:
    files = sorted(DATA_DIR.glob("*验收_最新.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    result = []
    for path in files[:15]:
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            data = {"passed": False, "errors": [str(exc)]}
        result.append(
            {
                "name": path.name,
                "path": str(path),
                "passed": data.get("passed"),
                "generated_at": data.get("generated_at"),
                "errors_count": len(data.get("errors", [])) if isinstance(data.get("errors"), list) else None,
                "warnings_count": len(data.get("warnings", [])) if isinstance(data.get("warnings"), list) else None,
            }
        )
    return result


def latest_acceptance_by_name(files: list[dict]) -> list[dict]:
    latest: dict[str, dict] = {}
    for item in files:
        normalized = item["name"].replace("验收_最新.json", "")
        if normalized not in latest:
            latest[normalized] = item
    return list(latest.values())


def build_asset() -> dict:
    acceptances = latest_acceptance_files()
    current_acceptances = latest_acceptance_by_name(acceptances)
    return {
        "name": "股票线连续施工状态快照",
        "version": "v1.0",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "asset_identity": "W1状态快照",
        "status": "snapshot",
        "not_formal_config": True,
        "not_entrypoint": True,
        "not_external_send": True,
        "not_adapter_write": True,
        "not_score_write": True,
        "current_position": "股票线已形成前台结论型短答、后台证据到前台映射、财报资金采集模板、统一刷新验收与影子前台短答验收的 W1 闭环。",
        "completed_assets": COMPLETED_ASSETS,
        "latest_acceptance_files": acceptances,
        "current_acceptance_files": current_acceptances,
        "remaining_debts": REMAINING_DEBTS,
        "must_not_misread": [
            "已通过验收的是 W1/W2 草案、模板或影子样例，不是正式上线。",
            "财报资金模板为空白字段，不代表财报证据已采集。",
            "影子前台短答可生成，不代表企业微信真实发送放行。",
            "统一刷新验收记录样例不是一次真实数据刷新。",
            "任何正式入口、真实外发、n8n、服务、19310、正式库或交易相关动作都仍是 W3阻断。",
        ],
        "next_auto_queue": [
            "财报资金证据人工填写回执模板",
            "行业价格观测人工填报回执模板",
            "市场风格日表影子刷新记录模板",
            "复盘人工修正候选接收模板",
        ],
        "summary": {
            "completed_asset_count": len(COMPLETED_ASSETS),
            "latest_acceptance_count": len(acceptances),
            "current_acceptance_count": len(current_acceptances),
            "open_debt_count": len(REMAINING_DEBTS),
            "all_current_acceptances_passed": all(item.get("passed") is True for item in current_acceptances if item.get("passed") is not None),
        },
        "safety_boundary": {
            "not_n8n": True,
            "not_external_send": True,
            "not_service_restart": True,
            "not_19310": True,
            "not_real_account": True,
            "not_formal_database_write": True,
            "not_adapter_write": True,
            "not_score_write": True,
            "not_entrypoint": True,
            "not_broker_interface": True,
            "not_auto_trade": True,
            "not_real_refresh": True,
        },
    }


def write_markdown(asset: dict) -> None:
    lines = [
        "# 股票线连续施工状态快照",
        "",
        f"- 生成时间：{asset['generated_at']}",
        f"- 资产身份：{asset['asset_identity']}",
        f"- 状态：{asset['status']}",
        "- 边界：W1 状态快照，不改正式配置、不外发、不写库。",
        "",
        "## 当前定位",
        "",
        asset["current_position"],
        "",
        "## 已完成资产",
        "",
    ]
    lines.extend([f"- {item}" for item in asset["completed_assets"]])
    lines.extend(["", "## 最近验收", ""])
    for item in asset["latest_acceptance_files"]:
        lines.append(f"- {item['name']}：passed={item['passed']}，errors={item['errors_count']}，warnings={item['warnings_count']}")
    lines.extend(["", "## 剩余旧债", ""])
    for item in asset["remaining_debts"]:
        lines.extend(
            [
                f"### {item['debt']}",
                "",
                f"- 状态：{item['status']}",
                f"- 原因：{item['reason']}",
                f"- 下一低风险动作：{item['next_low_risk_action']}",
                "",
            ]
        )
    lines.extend(["## 禁止误读", ""])
    lines.extend([f"- {item}" for item in asset["must_not_misread"]])
    lines.extend(["", "## 下一自动队列", ""])
    lines.extend([f"- {item}" for item in asset["next_auto_queue"]])
    lines.append("")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    asset = build_asset()
    JSON_OUT.write_text(json.dumps(asset, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(asset)
    print(json.dumps({"status": "ok", "json": str(JSON_OUT), "md": str(MD_OUT), "summary": asset["summary"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
