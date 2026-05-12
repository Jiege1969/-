# -*- coding: utf-8 -*-
"""生成日常交付版与稳定版协同施工完成度复核包。

本包用于多对话框协同施工时复核日常交付版、稳定版的完成状态，
并给出后续低风险续建边界。不修改已封存证据，不执行外部真实动作。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = EVOLUTION_ROOT / "03数据"
LOG_ROOT = EVOLUTION_ROOT / "04日志"
OUTPUT_DIR = DATA_ROOT / "111日常交付版与稳定版协同施工完成度复核包"

PACKAGE_JSON = OUTPUT_DIR / "日常交付版与稳定版协同施工完成度复核包_最新.json"
PACKAGE_MD = OUTPUT_DIR / "日常交付版与稳定版协同施工完成度复核包_最新.md"
BOUNDARY_JSON = OUTPUT_DIR / "协同施工接力边界清单_最新.json"
BOUNDARY_MD = OUTPUT_DIR / "协同施工接力边界清单_最新.md"

SOURCE_SPECS = [
    {
        "id": "SRC-040",
        "名称": "日常可用版自主巡检快照",
        "路径": DATA_ROOT / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
        "期望": "pass",
    },
    {
        "id": "SRC-REG",
        "名称": "日常可用版一键只读总回归",
        "路径": LOG_ROOT / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
        "期望": True,
    },
    {
        "id": "SRC-093",
        "名称": "日常稳定交付使用接管与续建总包",
        "路径": DATA_ROOT / "93日常稳定交付使用接管与续建总包" / "日常稳定交付使用接管与续建总包_最新.json",
        "期望": "daily_stable_handoff_continue_ready",
    },
    {
        "id": "SRC-096",
        "名称": "日常稳定交付最终交付清单与启动索引",
        "路径": DATA_ROOT / "96日常稳定交付最终交付清单与启动索引包" / "日常稳定交付最终交付清单与启动索引包_最新.json",
        "期望": "daily_stable_final_delivery_start_index_ready",
    },
    {
        "id": "SRC-097",
        "名称": "日常签收完成与稳定试运行启动回传",
        "路径": DATA_ROOT / "97日常签收完成与稳定试运行启动回传包" / "日常签收完成与稳定试运行启动回传包_最新.json",
        "期望": "daily_signoff_done_stable_trial_start_ready",
    },
    {
        "id": "SRC-098",
        "名称": "稳定试运行首轮观察执行闭环",
        "路径": DATA_ROOT / "98稳定试运行首轮观察执行闭环包" / "稳定试运行首轮观察执行闭环包_最新.json",
        "期望": "stable_trial_round1_observation_loop_ready",
    },
    {
        "id": "SRC-099",
        "名称": "稳定交付版本地试运行达标复核与签收完成",
        "路径": DATA_ROOT / "99稳定交付版本地试运行达标复核与签收完成包" / "稳定交付版本地试运行达标复核与签收完成包_最新.json",
        "期望": "stable_local_trial_acceptance_signoff_done",
    },
    {
        "id": "SRC-100",
        "名称": "日常稳定双版本交付封存与后续路线",
        "路径": DATA_ROOT / "100日常稳定双版本交付封存与后续路线包" / "日常稳定双版本交付封存与后续路线包_最新.json",
        "期望": "daily_stable_dual_delivery_freeze_ready",
    },
    {
        "id": "SRC-101",
        "名称": "双版本最终总回传与继续施工分界",
        "路径": DATA_ROOT / "101双版本最终总回传与继续施工分界包" / "双版本最终总回传与继续施工分界包_最新.json",
        "期望": "dual_version_final_return_boundary_ready",
    },
    {
        "id": "SRC-102",
        "名称": "完全交付使用版低风险续建启动队列",
        "路径": DATA_ROOT / "102完全交付使用版低风险续建启动队列包" / "完全交付使用版低风险续建启动队列包_最新.json",
        "期望": "full_delivery_low_risk_continue_queue_ready",
    },
]

HARD_FALSE_KEYS = [
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
    "修改运行配置",
    "修改总管面板",
    "修改一键接续包",
    "红线解锁生效",
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def status_of(data: Any) -> Any:
    if not isinstance(data, dict):
        return None
    if data.get("状态") is not None:
        return data.get("状态")
    if data.get("总体状态") is not None:
        return data.get("总体状态")
    if data.get("status") is not None:
        return data.get("status")
    if data.get("通过") is not None:
        return data.get("通过")
    if data.get("pass") is not None:
        return "pass" if data.get("pass") is True else "fail"
    return None


def source_ok(actual: Any, expected: Any) -> bool:
    if expected == "pass":
        return actual == "pass" or actual is True
    return actual == expected


def safety_flags() -> dict[str, bool]:
    return {key: False for key in HARD_FALSE_KEYS}


def load_sources() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    loaded: dict[str, Any] = {}
    summaries: list[dict[str, Any]] = []
    for spec in SOURCE_SPECS:
        path = spec["路径"]
        exists = path.exists()
        data = read_json(path) if exists else {}
        actual = status_of(data)
        ok = exists and source_ok(actual, spec["期望"])
        loaded[spec["id"]] = data
        summaries.append(
            {
                "id": spec["id"],
                "名称": spec["名称"],
                "存在": exists,
                "状态": actual,
                "期望": spec["期望"],
                "通过": ok,
                "路径": str(path),
            }
        )
    return summaries, loaded


def all_safety_closed(data: Any) -> bool:
    if not isinstance(data, dict):
        return True
    flags = data.get("安全边界") or data.get("红线动作") or data.get("hard_red_line_confirmation")
    if not isinstance(flags, dict):
        return True
    return all(flags.get(key) in (False, None) for key in HARD_FALSE_KEYS)


def build_completion_matrix(sources: list[dict[str, Any]], loaded: dict[str, Any]) -> list[dict[str, Any]]:
    source_map = {item["id"]: item for item in sources}

    def ok(*ids: str) -> bool:
        return all(source_map[item]["通过"] for item in ids)

    return [
        {
            "版本": "日常可用交付版",
            "完成状态": "已完成并可日常交付使用",
            "通过": ok("SRC-040", "SRC-REG", "SRC-093", "SRC-096", "SRC-097", "SRC-100", "SRC-101"),
            "交付口径": "可日常使用、每日只读回归、问题入账、低风险候选续建",
            "不可混入": "未确认真实发送、n8n触发、正式规则自动生效、服务重载",
        },
        {
            "版本": "稳定交付版",
            "完成状态": "已完成本地试运行签收并进入持续观察",
            "通过": ok("SRC-098", "SRC-099", "SRC-100", "SRC-101"),
            "交付口径": "可稳定试运行、持续观察、日报、问题闭环和回滚守护",
            "不可混入": "未确认外部真实能力、真实业务连接、正式规则写入",
        },
        {
            "版本": "后续完全交付低风险续建",
            "完成状态": "队列已启动，仍受红线确认约束",
            "通过": ok("SRC-102", "SRC-101"),
            "交付口径": "只做模板、索引、只读验收、离线预演、候选材料",
            "不可混入": "把低风险续建误当作红线已解锁",
        },
    ]


def build_boundary() -> list[dict[str, Any]]:
    return [
        {
            "编号": "COOP-001",
            "边界": "已封存日常可用交付版",
            "允许": "读取、引用、跑只读回归、补充问题入账说明",
            "禁止": "覆盖封存证据、改写签收状态、混入未确认真实能力",
        },
        {
            "编号": "COOP-002",
            "边界": "已封存稳定交付版",
            "允许": "持续观察、日报、样本扩展、候选问题分流",
            "禁止": "绕过观察闭环直接改正式规则或运行配置",
        },
        {
            "编号": "COOP-003",
            "边界": "多对话框并行施工",
            "允许": "新增独立编号包、只读汇总、生成验收日志",
            "禁止": "覆盖其他对话框刚生成的目录、同名脚本和最新文件",
        },
        {
            "编号": "COOP-004",
            "边界": "完全交付使用版续建",
            "允许": "补模板、补索引、补回滚材料、静态扫描、离线预演",
            "禁止": "红线未确认前执行真实动作或宣称已完全解锁",
        },
        {
            "编号": "COOP-005",
            "边界": "服务与外部系统",
            "允许": "登记需总管确认、写只读预案",
            "禁止": "重载19310/19302、真实发送企业微信、真实触发n8n、接券商/税局/财税软件",
        },
    ]


def build_package_markdown(package: dict[str, Any]) -> str:
    source_rows = [
        f"| {item['id']} | {item['名称']} | {item['存在']} | {item['状态']} | {item['通过']} |"
        for item in package["来源摘要"]
    ]
    matrix_rows = [
        f"| {item['版本']} | {item['完成状态']} | {item['通过']} | {item['交付口径']} |"
        for item in package["完成度矩阵"]
    ]
    boundary_rows = [
        f"| {item['编号']} | {item['边界']} | {item['允许']} | {item['禁止']} |"
        for item in package["协同施工接力边界"]
    ]
    return "\n".join(
        [
            "# 日常交付版与稳定版协同施工完成度复核包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- pass：{package['结论']['pass']}",
            "- 结论：日常交付版和稳定版完成状态可继续作为协同施工基线；后续只进入低风险续建和持续观察。",
            "",
            "## 来源摘要",
            "",
            "| id | 名称 | 存在 | 状态 | 通过 |",
            "| --- | --- | --- | --- | --- |",
            *source_rows,
            "",
            "## 完成度矩阵",
            "",
            "| 版本 | 完成状态 | 通过 | 交付口径 |",
            "| --- | --- | --- | --- |",
            *matrix_rows,
            "",
            "## 协同施工接力边界",
            "",
            "| 编号 | 边界 | 允许 | 禁止 |",
            "| --- | --- | --- | --- |",
            *boundary_rows,
            "",
            "## 红线口径",
            "",
            "- 不覆盖已封存日常版、稳定版证据。",
            "- 不真实发送企业微信，不真实触发 n8n。",
            "- 不接券商，不交易，不登录税局，不接财税软件。",
            "- 不真实渲染/发布视频，不写正式规则，不自动解锁红线。",
            "- 不修改总管面板，不修改一键接续包，不重载 19310/19302。",
        ]
    )


def build_boundary_markdown(boundary: list[dict[str, Any]]) -> str:
    rows = [
        f"| {item['编号']} | {item['边界']} | {item['允许']} | {item['禁止']} |"
        for item in boundary
    ]
    return "\n".join(
        [
            "# 协同施工接力边界清单",
            "",
            "本清单用于多对话框同时施工时对齐边界，只新增低风险材料，不覆盖已封存成果。",
            "",
            "| 编号 | 边界 | 允许 | 禁止 |",
            "| --- | --- | --- | --- |",
            *rows,
        ]
    )


def build_package() -> dict[str, Any]:
    sources, loaded = load_sources()
    matrix = build_completion_matrix(sources, loaded)
    boundary = build_boundary()
    source_safety = [
        {"id": source_id, "安全边界全关闭": all_safety_closed(data)}
        for source_id, data in loaded.items()
    ]
    passed = (
        all(item["通过"] for item in sources)
        and all(item["通过"] for item in matrix)
        and all(item["安全边界全关闭"] for item in source_safety)
    )
    return {
        "名称": "日常交付版与稳定版协同施工完成度复核包",
        "生成时间": now_text(),
        "状态": "daily_stable_coop_completion_review_ready",
        "用途": "给多对话框协同施工提供日常交付版、稳定版完成度基线和接力边界。",
        "来源摘要": sources,
        "完成度矩阵": matrix,
        "协同施工接力边界": boundary,
        "上游安全边界复核": source_safety,
        "结论": {
            "pass": passed,
            "日常交付版可作为完成基线": matrix[0]["通过"],
            "稳定版可作为完成基线": matrix[1]["通过"],
            "后续只进入低风险续建": matrix[2]["通过"],
            "允许覆盖已封存证据": False,
            "允许红线自动生效": False,
        },
        "安全边界": safety_flags(),
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "边界清单JSON": str(BOUNDARY_JSON),
            "边界清单Markdown": str(BOUNDARY_MD),
        },
    }


def main() -> int:
    package = build_package()
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_package_markdown(package))
    write_json(BOUNDARY_JSON, package["协同施工接力边界"])
    write_text(BOUNDARY_MD, build_boundary_markdown(package["协同施工接力边界"]))
    print(
        json.dumps(
            {
                "状态": package["状态"],
                "pass": package["结论"]["pass"],
                "来源数量": len(package["来源摘要"]),
                "完成度项": len(package["完成度矩阵"]),
                "输出": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if package["结论"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
