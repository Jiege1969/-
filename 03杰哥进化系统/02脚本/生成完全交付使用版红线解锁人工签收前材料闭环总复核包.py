# -*- coding: utf-8 -*-
"""生成完全交付使用版红线解锁人工签收前材料闭环总复核包。

本包只读汇总红线解锁申请材料、风险闸口、确认单草案、拒收样本、
回滚演练、缺口模板和命令静态扫描结果，不解锁红线，不执行真实动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = EVOLUTION_ROOT / "03数据"
OUTPUT_DIR = DATA_ROOT / "110完全交付使用版红线解锁人工签收前材料闭环总复核包"

PACKAGE_JSON = OUTPUT_DIR / "完全交付使用版红线解锁人工签收前材料闭环总复核包_最新.json"
PACKAGE_MD = OUTPUT_DIR / "完全交付使用版红线解锁人工签收前材料闭环总复核包_最新.md"
CHECKLIST_JSON = OUTPUT_DIR / "人工签收前材料闭环复核清单_最新.json"
CHECKLIST_MD = OUTPUT_DIR / "人工签收前材料闭环复核清单_最新.md"

SOURCE_SPECS = [
    {
        "id": "SRC-106",
        "名称": "红线解锁申请材料总索引",
        "路径": DATA_ROOT / "106完全交付使用版红线解锁申请材料总索引包" / "完全交付使用版红线解锁申请材料总索引包_最新.json",
        "期望状态": "full_delivery_redline_unlock_material_index_ready",
    },
    {
        "id": "SRC-107",
        "名称": "红线解锁申请只读风险评审与禁止生效闸口",
        "路径": DATA_ROOT / "107完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包" / "完全交付使用版红线解锁申请只读风险评审与禁止生效闸口包_最新.json",
        "期望状态": "full_delivery_redline_unlock_readonly_risk_gate_ready",
    },
    {
        "id": "SRC-108A",
        "名称": "红线解锁分项确认单草案与授权边界",
        "路径": DATA_ROOT / "108完全交付使用版红线解锁分项确认单草案与授权边界包" / "完全交付使用版红线解锁分项确认单草案与授权边界包_最新.json",
        "期望状态": "full_delivery_redline_unlock_confirmation_draft_ready",
    },
    {
        "id": "SRC-108B",
        "名称": "红线材料缺口低风险补齐第一批模板",
        "路径": DATA_ROOT / "108红线材料缺口低风险补齐第一批模板包" / "红线材料缺口低风险补齐第一批模板包_最新.json",
        "期望状态": "redline_gap_low_risk_template_batch1_ready",
    },
    {
        "id": "SRC-109",
        "名称": "红线解锁拒收样本与回滚演练",
        "路径": DATA_ROOT / "109完全交付使用版红线解锁拒收样本与回滚演练包" / "完全交付使用版红线解锁拒收样本与回滚演练包_最新.json",
        "期望状态": "full_delivery_redline_unlock_reject_rollback_drill_ready",
    },
    {
        "id": "SRC-101A",
        "名称": "低风险自主命令白名单与红线静态扫描包",
        "路径": DATA_ROOT / "101低风险自主命令白名单与红线静态扫描包" / "低风险自主命令白名单与红线静态扫描包_最新.json",
        "期望状态": "ready_for_static_scan",
    },
    {
        "id": "SRC-101B",
        "名称": "低风险自主命令红线静态扫描报告",
        "路径": DATA_ROOT / "101低风险自主命令白名单与红线静态扫描包" / "低风险自主命令红线静态扫描报告_最新.json",
        "期望状态": None,
    },
]

REDLINE_FLAG_KEYS = [
    "真实发送企业微信",
    "真实触发n8n",
    "接券商",
    "交易",
    "登录电子税务局",
    "接财税软件",
    "真实渲染视频",
    "自动发布视频",
    "写正式规则",
    "自动转正式规则",
    "红线解锁生效",
    "真实执行回滚",
    "修改运行配置",
    "修改总管面板",
    "修改一键接续包",
    "重载19310",
    "重载19302",
]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def safety_flags() -> dict[str, bool]:
    return {
        "真实发送企业微信": False,
        "真实触发n8n": False,
        "接券商": False,
        "交易": False,
        "登录电子税务局": False,
        "接财税软件": False,
        "真实渲染视频": False,
        "自动发布视频": False,
        "写正式规则": False,
        "自动转正式规则": False,
        "红线解锁生效": False,
        "真实执行回滚": False,
        "修改运行配置": False,
        "修改总管面板": False,
        "修改一键接续包": False,
        "重载19310": False,
        "重载19302": False,
    }


def load_sources() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    loaded: dict[str, Any] = {}
    summaries: list[dict[str, Any]] = []
    for spec in SOURCE_SPECS:
        path = spec["路径"]
        exists = path.exists()
        data = read_json(path) if exists else {}
        loaded[spec["id"]] = data
        actual_status = data.get("状态", data.get("status"))
        expected_status = spec["期望状态"]
        status_ok = True if expected_status is None else actual_status == expected_status
        if spec["id"] == "SRC-101B":
            actual_status = "pass" if data.get("pass") is True and data.get("violation_count") == 0 else "blocked"
            status_ok = actual_status == "pass"
        summaries.append(
            {
                "id": spec["id"],
                "名称": spec["名称"],
                "存在": exists,
                "状态": actual_status,
                "期望状态": expected_status,
                "状态通过": status_ok,
                "路径": str(path),
            }
        )
    return summaries, loaded


def all_false(flags: dict[str, Any] | None) -> bool:
    if not isinstance(flags, dict):
        return True
    return all(flags.get(key) in (False, None) for key in REDLINE_FLAG_KEYS)


def build_review_items(sources: list[dict[str, Any]], loaded: dict[str, Any]) -> list[dict[str, Any]]:
    risk_gate = loaded.get("SRC-107", {})
    confirmation = loaded.get("SRC-108A", {})
    templates = loaded.get("SRC-108B", {})
    reject_rollback = loaded.get("SRC-109", {})
    command_scan = loaded.get("SRC-101B", {})

    cards = confirmation.get("分项确认单草案", [])
    template_items = templates.get("补齐模板清单", [])
    reject_samples = reject_rollback.get("拒收样本", [])
    rollback_drills = reject_rollback.get("回滚演练", [])

    source_safety = []
    for source_id, data in loaded.items():
        if isinstance(data, dict):
            source_safety.append({"source_id": source_id, "安全边界全关闭": all_false(data.get("安全边界"))})

    return [
        {
            "编号": "CHK-001",
            "复核项": "上游材料均存在且状态符合预期",
            "通过": all(item["存在"] and item["状态通过"] for item in sources),
            "证据": f"{sum(1 for item in sources if item['存在'])}/{len(sources)} 个来源存在",
        },
        {
            "编号": "CHK-002",
            "复核项": "风险评审继续禁止生效",
            "通过": risk_gate.get("指标", {}).get("允许生效数量") == 0
            and risk_gate.get("指标", {}).get("禁止生效数量") == 7
            and risk_gate.get("指标", {}).get("全部未确认") is True
            and risk_gate.get("指标", {}).get("全部禁止自动执行") is True,
            "证据": risk_gate.get("指标", {}),
        },
        {
            "编号": "CHK-003",
            "复核项": "分项确认单仍为草案且未确认",
            "通过": len(cards) == 7
            and all(item.get("确认单状态") == "草案" for item in cards)
            and all(item.get("总管确认状态") == "未确认" for item in cards)
            and all(item.get("允许生效") is False for item in cards)
            and all(item.get("允许自动执行") is False for item in cards),
            "证据": {"确认单数量": len(cards)},
        },
        {
            "编号": "CHK-004",
            "复核项": "拒收样本与只读回滚演练闭合",
            "通过": len(reject_samples) == 7
            and len(rollback_drills) == 7
            and all(item.get("允许生效") is False for item in reject_samples)
            and all(item.get("允许自动执行") is False for item in reject_samples)
            and all(item.get("是否真实执行回滚") is False for item in rollback_drills),
            "证据": {"拒收样本": len(reject_samples), "回滚演练": len(rollback_drills)},
        },
        {
            "编号": "CHK-005",
            "复核项": "缺口补齐材料仍为模板态",
            "通过": len(template_items) >= 5 and all(item.get("执行状态") == "仅模板" for item in template_items),
            "证据": {"模板数量": len(template_items)},
        },
        {
            "编号": "CHK-006",
            "复核项": "候选自主命令静态扫描无红线命中",
            "通过": command_scan.get("pass") is True
            and command_scan.get("violation_count") == 0
            and command_scan.get("commands_executed") is False
            and command_scan.get("external_call") is False
            and command_scan.get("reload_service") is False,
            "证据": {
                "pass": command_scan.get("pass"),
                "violation_count": command_scan.get("violation_count"),
                "commands_executed": command_scan.get("commands_executed"),
            },
        },
        {
            "编号": "CHK-007",
            "复核项": "上游安全边界未出现真实动作放行",
            "通过": all(item["安全边界全关闭"] for item in source_safety),
            "证据": source_safety,
        },
    ]


def build_checklist_markdown(items: list[dict[str, Any]]) -> str:
    rows = [
        f"| {item['编号']} | {item['复核项']} | {item['通过']} |"
        for item in items
    ]
    return "\n".join(
        [
            "# 人工签收前材料闭环复核清单",
            "",
            "本清单只做只读复核，不代表总管已签收，不代表红线已解锁。",
            "",
            "| 编号 | 复核项 | 通过 |",
            "| --- | --- | --- |",
            *rows,
        ]
    )


def build_package_markdown(package: dict[str, Any]) -> str:
    source_rows = [
        f"| {item['id']} | {item['名称']} | {item['存在']} | {item['状态']} | {item['状态通过']} |"
        for item in package["来源摘要"]
    ]
    item_rows = [
        f"| {item['编号']} | {item['复核项']} | {item['通过']} |"
        for item in package["复核清单"]
    ]
    return "\n".join(
        [
            "# 完全交付使用版红线解锁人工签收前材料闭环总复核包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- pass：{package['结论']['pass']}",
            "- 结论：材料闭环可进入人工签收前复核视图，但红线未解锁、未生效、未自动执行。",
            "",
            "## 来源摘要",
            "",
            "| id | 名称 | 存在 | 状态 | 状态通过 |",
            "| --- | --- | --- | --- | --- |",
            *source_rows,
            "",
            "## 复核清单",
            "",
            "| 编号 | 复核项 | 通过 |",
            "| --- | --- | --- |",
            *item_rows,
            "",
            "## 安全边界",
            "",
            "- 不真实发送企业微信，不真实触发 n8n。",
            "- 不接券商，不交易，不登录税局，不接财税软件。",
            "- 不真实渲染/发布视频，不写正式规则，不自动解锁红线。",
            "- 不修改总管面板，不修改一键接续包，不重载 19310/19302。",
        ]
    )


def build_package() -> dict[str, Any]:
    generated_at = now_text()
    sources, loaded = load_sources()
    checklist = build_review_items(sources, loaded)
    passed = all(item["通过"] for item in checklist)
    return {
        "名称": "完全交付使用版红线解锁人工签收前材料闭环总复核包",
        "生成时间": generated_at,
        "状态": "full_delivery_redline_unlock_presign_material_closure_review_ready",
        "用途": "在总管人工签收前，只读复核红线解锁材料是否闭环；不产生授权，不执行红线动作。",
        "来源摘要": sources,
        "复核清单": checklist,
        "结论": {
            "pass": passed,
            "可进入人工签收前复核视图": passed,
            "总管已签收": False,
            "允许生效": False,
            "允许自动执行": False,
            "红线解锁生效": False,
        },
        "安全边界": safety_flags(),
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "复核清单JSON": str(CHECKLIST_JSON),
            "复核清单Markdown": str(CHECKLIST_MD),
        },
    }


def main() -> int:
    package = build_package()
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_package_markdown(package))
    write_json(CHECKLIST_JSON, package["复核清单"])
    write_text(CHECKLIST_MD, build_checklist_markdown(package["复核清单"]))
    print(
        json.dumps(
            {
                "状态": package["状态"],
                "pass": package["结论"]["pass"],
                "复核项数量": len(package["复核清单"]),
                "输出": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if package["结论"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
