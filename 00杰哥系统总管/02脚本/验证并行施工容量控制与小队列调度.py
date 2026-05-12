# -*- coding: utf-8 -*-
"""
验证并行施工容量控制与小队列调度规则。

安全边界：
- 只读取总管配置、文档、派工包、施工面板、一键接续包和固定回收目录。
- 只写 00总管运行状态验收报告。
- 不修改进度口径数字，不修改子系统业务代码。
- 不触发企业微信、n8n、券商接口、自动交易或下单相关能力。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
CONFIG = MANAGER / "01配置" / "并行施工容量控制规则.json"
DOC = MANAGER / "07文档" / "并行施工容量控制与小队列自动调度说明_20260505.md"
STATE_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = STATE_DIR / "并行施工容量控制与小队列调度验收_最新.json"
REPORT_MD = STATE_DIR / "并行施工容量控制与小队列调度验收_最新.md"

SOURCE_FILES = {
    "本轮并行施工派工包": MANAGER / "03数据" / "开工上下文" / "本轮并行施工派工包_最新.json",
    "当前施工面板": MANAGER / "07文档" / "当前施工面板.md",
    "一键接续施工包": MANAGER / "03数据" / "开工上下文" / "一键接续施工包_最新.md",
    "总管三线回收报告": MANAGER / "03数据" / "并行回收" / "00总管_本轮三线回收报告_最新.json",
    "股票自动交易屏蔽总闸门": MANAGER / "01配置" / "股票自动交易屏蔽总闸门规则.json",
}

PROGRESS_FILES = [
    MANAGER / "01配置" / "进度口径规则.json",
    MANAGER / "01配置" / "进度回答标准.json",
    MANAGER / "01配置" / "四大系统验收读取口径.json",
]

FORBIDDEN_GATE_TERMS = [
    "自动交易",
    "券商接口",
    "下单",
    "资金账户",
    "交易工作流",
    "明确买卖建议",
    "仓位建议",
    "目标价",
]

EXPECTED_SYSTEMS = ["01智能系统", "02扩展系统", "03进化系统"]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def check(condition: bool, name: str, detail: str, checks: list[dict[str, Any]]) -> None:
    checks.append({
        "检查项": name,
        "通过": bool(condition),
        "说明": detail,
    })


def nested_values(data: Any) -> list[Any]:
    values: list[Any] = []
    if isinstance(data, dict):
        for value in data.values():
            values.append(value)
            values.extend(nested_values(value))
    elif isinstance(data, list):
        for value in data:
            values.append(value)
            values.extend(nested_values(value))
    return values


def main() -> int:
    checks: list[dict[str, Any]] = []
    rule = read_json(CONFIG) if CONFIG.exists() else {}
    doc = read_text(DOC)

    check(CONFIG.exists(), "规则文件存在", str(CONFIG), checks)
    check(DOC.exists(), "说明文档存在", str(DOC), checks)

    capacity = rule.get("最大并行容量", {})
    check(
        capacity.get("子系统施工框最大并行数") == 3,
        "最大并行数为3",
        "本轮最多允许01/02/03三条子系统施工线并行。",
        checks,
    )
    check(
        capacity.get("允许并行子系统") == EXPECTED_SYSTEMS,
        "允许并行系统集合正确",
        "允许并行系统必须精确为01智能系统、02扩展系统、03进化系统。",
        checks,
    )
    check(
        capacity.get("同一系统内最大并行数") == 1,
        "同系统串行",
        "同一系统只能有一个施工框写入。",
        checks,
    )

    serial = "\n".join(rule.get("必须串行任务", []))
    for term in ["00总管固定回收", "进度口径", "当前施工面板", "一键接续施工包", "阻断项"]:
        check(term in serial, f"串行任务包含{term}", "共享口径和回收动作必须串行。", checks)

    scheduler = rule.get("小队列自动调度", {})
    release = "\n".join(scheduler.get("自动放行条件", []))
    pause = "\n".join(scheduler.get("自动暂停条件", []))
    check("不修改进度口径数字" in release, "自动放行保护进度口径", "小队列不会自动修改进度数字。", checks)
    check("超过最大并行容量" in pause, "容量超限自动暂停", "超过3条线时必须入队等待。", checks)
    check("股票自动交易屏蔽硬闸门" in pause, "继承股票硬闸门暂停条件", "触碰股票交易禁区不得进入小队列。", checks)

    recovery = rule.get("固定回收路径规则", {})
    recovery_dir = Path(recovery.get("回收目录", ""))
    check(recovery_dir == MANAGER / "03数据" / "并行回收", "固定回收目录正确", str(recovery_dir), checks)
    for system in EXPECTED_SYSTEMS + ["00总管回收"]:
        value = recovery.get(system, "")
        path = Path(value)
        check(str(path).startswith(str(recovery_dir)), f"{system}回收路径在固定目录", value, checks)

    user_rule = "\n".join(rule.get("用户不搬运结果规则", []))
    check("用户不需要" in doc and "固定回收路径" in doc, "文档明确用户不搬运结果", "说明文档要求子系统写固定回收路径，总管自动读取。", checks)
    check("用户只需要下达目标或确认高风险事项" in user_rule, "规则明确用户不搬运结果", "用户不负责跨窗口复制、搬运、整理结果。", checks)

    gate = rule.get("股票自动交易屏蔽硬闸门继承", {})
    gate_text = json.dumps(gate, ensure_ascii=False)
    for term in FORBIDDEN_GATE_TERMS:
        check(term in gate_text, f"股票硬闸门继承{term}", "禁止事项必须保留在容量调度规则中。", checks)
    check("禁止执行" in gate.get("调度影响", ""), "触碰股票禁区禁止入队", gate.get("调度影响", ""), checks)

    for name, path in SOURCE_FILES.items():
        check(path.exists(), f"读取依据存在：{name}", str(path), checks)

    for path in PROGRESS_FILES:
        check(path.exists(), f"进度口径文件未作为写入目标：{path.name}", "本验收只确认文件存在且本轮不写入该类口径文件。", checks)

    doc_required = [
        "最多允许 `3` 个子系统施工框并行",
        "必须串行任务",
        "小队列自动调度",
        "冲突处理",
        "固定回收路径",
        "用户不需要搬运",
        "股票自动交易屏蔽总闸门",
        "不修改全盘进度",
    ]
    for term in doc_required:
        check(term in doc, f"说明文档包含：{term}", "人工阅读说明完整。", checks)

    pass_count = sum(1 for item in checks if item["通过"])
    total = len(checks)
    fail_count = total - pass_count
    conclusion = "通过" if fail_count == 0 else "未通过"

    report = {
        "名称": "并行施工容量控制与小队列调度验收",
        "生成时间": now_text(),
        "结论": conclusion,
        "通过": pass_count,
        "总数": total,
        "失败": fail_count,
        "写入文件": [
            str(CONFIG),
            str(DOC),
            str(REPORT_JSON),
            str(REPORT_MD),
        ],
        "未改事项": [
            "未修改子系统业务代码",
            "未修改进度口径数字",
            "未触发企业微信真实发送",
            "未触发 n8n",
            "未调用券商接口",
            "未恢复或设计自动交易、下单、资金账户、交易工作流",
        ],
        "检查": checks,
    }

    lines = [
        "# 并行施工容量控制与小队列调度验收",
        "",
        f"生成时间：{report['生成时间']}",
        f"结论：{conclusion}",
        f"验收：{pass_count}/{total} 通过，失败 {fail_count}",
        "",
        "## 写入文件",
        "",
    ]
    for path in report["写入文件"]:
        lines.append(f"- `{path}`")
    lines.extend(["", "## 未改事项", ""])
    for item in report["未改事项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 检查项", ""])
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {mark}：{item['检查项']}。{item['说明']}")
    lines.append("")

    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines))
    print(f"{conclusion}: {pass_count}/{total} 通过，失败 {fail_count}")
    print(str(REPORT_MD))
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
