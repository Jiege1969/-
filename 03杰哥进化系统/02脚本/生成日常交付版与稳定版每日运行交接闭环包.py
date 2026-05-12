# -*- coding: utf-8 -*-
"""生成日常交付版与稳定版每日运行交接闭环包。

本包只读汇总日常交付版、稳定版的每日开工、收工、问题入账、
样本等待期保活和回滚守护材料，不执行真实入口，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = EVOLUTION_ROOT / "03数据"
LOG_ROOT = EVOLUTION_ROOT / "04日志"
OUTPUT_DIR = DATA_ROOT / "112日常交付版与稳定版每日运行交接闭环包"

PACKAGE_JSON = OUTPUT_DIR / "日常交付版与稳定版每日运行交接闭环包_最新.json"
PACKAGE_MD = OUTPUT_DIR / "日常交付版与稳定版每日运行交接闭环包_最新.md"
HANDOFF_JSON = OUTPUT_DIR / "每日运行交接清单_最新.json"
HANDOFF_MD = OUTPUT_DIR / "每日运行交接清单_最新.md"
COMMANDS_JSON = OUTPUT_DIR / "每日只读入口命令清单_最新.json"
COMMANDS_MD = OUTPUT_DIR / "每日只读入口命令清单_最新.md"

SOURCE_SPECS = [
    {
        "id": "SRC-111",
        "名称": "日常交付版与稳定版协同施工完成度复核",
        "路径": DATA_ROOT / "111日常交付版与稳定版协同施工完成度复核包" / "日常交付版与稳定版协同施工完成度复核包_最新.json",
        "期望": "daily_stable_coop_completion_review_ready",
    },
    {
        "id": "SRC-100D",
        "名称": "日常稳定双版本交付封存与后续路线",
        "路径": DATA_ROOT / "100日常稳定双版本交付封存与后续路线包" / "日常稳定双版本交付封存与后续路线包_最新.json",
        "期望": "daily_stable_dual_delivery_freeze_ready",
    },
    {
        "id": "SRC-101D",
        "名称": "双版本最终总回传与继续施工分界",
        "路径": DATA_ROOT / "101双版本最终总回传与继续施工分界包" / "双版本最终总回传与继续施工分界包_最新.json",
        "期望": "dual_version_final_return_boundary_ready",
    },
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
        "id": "SRC-098",
        "名称": "稳定版每日唯一入口操作卡同步",
        "路径": DATA_ROOT / "98稳定版每日唯一入口操作卡同步包" / "稳定版每日唯一入口操作卡同步包_最新.json",
        "期望": "stable_daily_single_entry_operation_card_ready",
    },
    {
        "id": "SRC-100S",
        "名称": "稳定版样本等待期低风险保活巡检",
        "路径": DATA_ROOT / "100稳定版样本等待期低风险保活巡检包" / "稳定版样本等待期低风险保活巡检包_最新.json",
        "期望": "stable_sample_waiting_keepalive_patrol_ready",
    },
    {
        "id": "SRC-092",
        "名称": "稳定版试运行反馈本地入账执行器",
        "路径": DATA_ROOT / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈本地入账执行器包_最新.json",
        "期望": "stable_trial_feedback_local_intake_executor_ready",
    },
    {
        "id": "SRC-087",
        "名称": "运行期故障恢复与回滚总索引",
        "路径": DATA_ROOT / "87运行期故障恢复与回滚总索引包" / "运行期故障恢复与回滚总索引包_最新.json",
        "期望": "runtime_recovery_rollback_index_ready",
    },
]

HARD_FALSE_KEYS = [
    "真实发送企业微信",
    "真实触发n8n",
    "触发n8n",
    "接券商",
    "交易",
    "登录电子税务局",
    "接财税软件",
    "真实渲染视频",
    "视频真实渲染",
    "自动发布视频",
    "自动发布",
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
    for key in ["状态", "总体状态", "status", "通过", "pass"]:
        if key in data:
            value = data.get(key)
            if key == "pass":
                return "pass" if value is True else "fail"
            return value
    return None


def source_ok(actual: Any, expected: Any) -> bool:
    if expected == "pass":
        return actual == "pass" or actual is True
    return actual == expected


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
        "修改运行配置": False,
        "修改总管面板": False,
        "修改一键接续包": False,
        "红线解锁生效": False,
        "重载19310": False,
        "重载19302": False,
    }


def all_safety_closed(data: Any) -> bool:
    if not isinstance(data, dict):
        return True
    flags = data.get("安全边界") or data.get("红线动作") or data.get("hard_red_line_confirmation")
    if not isinstance(flags, dict):
        return True
    return all(flags.get(key) in (False, None) for key in HARD_FALSE_KEYS)


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


def build_handoff_checklist() -> list[dict[str, Any]]:
    return [
        {
            "编号": "DAY-START-001",
            "阶段": "开工前",
            "动作": "查看第111包完成度复核，确认日常版和稳定版仍作为完成基线",
            "通过标准": "第111包 pass=True，日常交付版与稳定版完成基线为 True",
            "是否执行真实动作": False,
        },
        {
            "编号": "DAY-START-002",
            "阶段": "开工前",
            "动作": "运行或读取一键只读总回归结果",
            "通过标准": "一键只读总回归通过，失败数为0",
            "是否执行真实动作": False,
        },
        {
            "编号": "DAY-START-003",
            "阶段": "开工前",
            "动作": "刷新或读取日常可用版自主巡检快照",
            "通过标准": "总体状态 pass，阻断检查无失败",
            "是否执行真实动作": False,
        },
        {
            "编号": "STABLE-001",
            "阶段": "稳定版观察",
            "动作": "按稳定版每日唯一入口操作卡查看推荐入口和样本等待状态",
            "通过标准": "只使用推荐唯一入口；三日样本不足时不误判稳定版长期达标",
            "是否执行真实动作": False,
        },
        {
            "编号": "STABLE-002",
            "阶段": "稳定版观察",
            "动作": "样本等待期只做低风险保活巡检",
            "通过标准": "只扫描收件箱、刷新索引和快照，不新增伪样本",
            "是否执行真实动作": False,
        },
        {
            "编号": "ISSUE-001",
            "阶段": "问题入账",
            "动作": "试运行反馈先进本地入账执行器",
            "通过标准": "形成候选、拒收或需确认分类，不直接改正式规则",
            "是否执行真实动作": False,
        },
        {
            "编号": "CLOSE-001",
            "阶段": "收工前",
            "动作": "记录当日观察、问题入账状态和下一步待办",
            "通过标准": "可追溯到日报、台账或候选清单",
            "是否执行真实动作": False,
        },
        {
            "编号": "ROLLBACK-001",
            "阶段": "异常时",
            "动作": "只查看运行期故障恢复与回滚总索引",
            "通过标准": "不执行真实回滚；需回滚时登记总管确认",
            "是否执行真实动作": False,
        },
    ]


def build_command_list() -> list[dict[str, Any]]:
    return [
        {
            "编号": "CMD-DAILY-REGRESSION",
            "用途": "日常可用交付版一键只读总回归",
            "命令": f'python "{EVOLUTION_ROOT / "02脚本" / "执行日常可用交付版一键只读总回归.py"}"',
            "本包是否执行": False,
            "红线说明": "只读回归，不触发外部真实动作",
        },
        {
            "编号": "CMD-DAILY-SNAPSHOT",
            "用途": "刷新日常可用版自主巡检快照",
            "命令": f'python "{EVOLUTION_ROOT / "02脚本" / "生成日常可用版自主巡检快照.py"}"',
            "本包是否执行": False,
            "红线说明": "只刷新本地快照，不重载服务",
        },
        {
            "编号": "CMD-STABLE-SAMPLE",
            "用途": "稳定版自然日样本采集与达标刷新推荐入口",
            "命令": f'python "{EVOLUTION_ROOT / "02脚本" / "执行稳定版自然日样本采集与达标刷新.py"}"',
            "本包是否执行": False,
            "红线说明": "按唯一入口操作卡人工触发，本包不代执行",
        },
        {
            "编号": "CMD-STABLE-KEEPALIVE",
            "用途": "稳定版样本等待期低风险保活巡检",
            "命令": f'python "{EVOLUTION_ROOT / "02脚本" / "执行稳定版样本等待期低风险保活巡检.py"}"',
            "本包是否执行": False,
            "红线说明": "只做等待期保活，不误增自然日样本",
        },
        {
            "编号": "CMD-FEEDBACK-INTAKE",
            "用途": "稳定版试运行反馈本地入账",
            "命令": f'python "{EVOLUTION_ROOT / "02脚本" / "执行稳定版试运行反馈本地入账.py"}"',
            "本包是否执行": False,
            "红线说明": "只本地入账，不写正式规则",
        },
    ]


def build_package_markdown(package: dict[str, Any]) -> str:
    source_rows = [
        f"| {item['id']} | {item['名称']} | {item['存在']} | {item['状态']} | {item['通过']} |"
        for item in package["来源摘要"]
    ]
    handoff_rows = [
        f"| {item['编号']} | {item['阶段']} | {item['动作']} | {item['通过标准']} |"
        for item in package["每日运行交接清单"]
    ]
    command_rows = [
        f"| {item['编号']} | {item['用途']} | `{item['命令']}` | {item['本包是否执行']} |"
        for item in package["每日只读入口命令清单"]
    ]
    return "\n".join(
        [
            "# 日常交付版与稳定版每日运行交接闭环包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            f"- pass：{package['结论']['pass']}",
            "- 结论：每日运行交接链已闭合；本包只登记入口、标准和边界，不执行真实动作。",
            "",
            "## 来源摘要",
            "",
            "| id | 名称 | 存在 | 状态 | 通过 |",
            "| --- | --- | --- | --- | --- |",
            *source_rows,
            "",
            "## 每日运行交接清单",
            "",
            "| 编号 | 阶段 | 动作 | 通过标准 |",
            "| --- | --- | --- | --- |",
            *handoff_rows,
            "",
            "## 每日只读入口命令清单",
            "",
            "| 编号 | 用途 | 命令 | 本包是否执行 |",
            "| --- | --- | --- | --- |",
            *command_rows,
            "",
            "## 红线口径",
            "",
            "- 本包不执行任何登记命令，只生成交接材料。",
            "- 不真实发送企业微信，不真实触发 n8n。",
            "- 不接券商，不交易，不登录税局，不接财税软件。",
            "- 不真实渲染/发布视频，不写正式规则，不自动解锁红线。",
            "- 不修改总管面板，不修改一键接续包，不重载 19310/19302。",
        ]
    )


def build_handoff_markdown(items: list[dict[str, Any]]) -> str:
    rows = [
        f"| {item['编号']} | {item['阶段']} | {item['动作']} | {item['通过标准']} | {item['是否执行真实动作']} |"
        for item in items
    ]
    return "\n".join(
        [
            "# 每日运行交接清单",
            "",
            "本清单用于日常交付版与稳定版每日开工、观察、问题入账、收工接力。",
            "",
            "| 编号 | 阶段 | 动作 | 通过标准 | 是否执行真实动作 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def build_commands_markdown(items: list[dict[str, Any]]) -> str:
    rows = [
        f"| {item['编号']} | {item['用途']} | `{item['命令']}` | {item['本包是否执行']} | {item['红线说明']} |"
        for item in items
    ]
    return "\n".join(
        [
            "# 每日只读入口命令清单",
            "",
            "本清单只登记命令，不在本包内执行。",
            "",
            "| 编号 | 用途 | 命令 | 本包是否执行 | 红线说明 |",
            "| --- | --- | --- | --- | --- |",
            *rows,
        ]
    )


def build_package() -> dict[str, Any]:
    sources, loaded = load_sources()
    handoff = build_handoff_checklist()
    commands = build_command_list()
    source_safety = [
        {"id": source_id, "安全边界全关闭": all_safety_closed(data)}
        for source_id, data in loaded.items()
    ]
    passed = (
        all(item["通过"] for item in sources)
        and all(item["是否执行真实动作"] is False for item in handoff)
        and all(item["本包是否执行"] is False for item in commands)
        and all(item["安全边界全关闭"] for item in source_safety)
    )
    return {
        "名称": "日常交付版与稳定版每日运行交接闭环包",
        "生成时间": now_text(),
        "状态": "daily_stable_daily_handoff_loop_ready",
        "用途": "为日常交付版与稳定版提供每日开工、观察、问题入账、收工和异常查看的接力闭环。",
        "来源摘要": sources,
        "每日运行交接清单": handoff,
        "每日只读入口命令清单": commands,
        "上游安全边界复核": source_safety,
        "结论": {
            "pass": passed,
            "每日开工链闭合": passed,
            "稳定观察链闭合": passed,
            "问题入账链闭合": passed,
            "回滚守护链闭合": passed,
            "本包执行真实命令": False,
            "允许红线自动生效": False,
        },
        "安全边界": safety_flags(),
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "交接清单JSON": str(HANDOFF_JSON),
            "交接清单Markdown": str(HANDOFF_MD),
            "命令清单JSON": str(COMMANDS_JSON),
            "命令清单Markdown": str(COMMANDS_MD),
        },
    }


def main() -> int:
    package = build_package()
    write_json(PACKAGE_JSON, package)
    write_text(PACKAGE_MD, build_package_markdown(package))
    write_json(HANDOFF_JSON, package["每日运行交接清单"])
    write_text(HANDOFF_MD, build_handoff_markdown(package["每日运行交接清单"]))
    write_json(COMMANDS_JSON, package["每日只读入口命令清单"])
    write_text(COMMANDS_MD, build_commands_markdown(package["每日只读入口命令清单"]))
    print(
        json.dumps(
            {
                "状态": package["状态"],
                "pass": package["结论"]["pass"],
                "来源数量": len(package["来源摘要"]),
                "交接项": len(package["每日运行交接清单"]),
                "输出": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0 if package["结论"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
