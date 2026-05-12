# ============================================================
# 脚本名称：执行杰哥推荐方法工作流总控.py
# 所属系统：02杰哥扩展系统/01股票研究系统/02脚本
# 功能描述：按“数据地基 -> 量价特征提取 -> 行业归因 -> 候选评分合成 -> 方法内核校准 -> 单股材料生成 -> 前台表达投影 -> 复盘进化”
#           的固定顺序，对【杰哥推荐】方法内核执行只读巡检与验收。
# 创建日期：2026-05-10
# 安全边界：默认只读；不触发企业微信真实发送、不触发n8n、不调用券商接口、不自动交易。
# ============================================================

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


STOCK_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
WORKFLOW_RULE_PATH = STOCK_ROOT / "01配置" / "杰哥推荐方法工作流规则_v1.0.json"
KERNEL_RULE_PATH = STOCK_ROOT / "01配置" / "杰哥推荐方法内核规则.json"
FRONT_CONFIG_PATH = STOCK_ROOT / "01配置" / "股票双前台入口配置.json"
REPORT_DIR = STOCK_ROOT / "03数据" / "274杰哥推荐方法工作流固化验收"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def count_records(path: Path) -> int | None:
    if not path.exists():
        return None

    data = load_json(path)
    if isinstance(data, list):
        return len(data)

    if isinstance(data, dict):
        for key in ("样本数量", "候选数量", "相似度识别数量", "记录数量"):
            value = data.get(key)
            if isinstance(value, int):
                return value

        for key in (
            "数据",
            "明细",
            "结果",
            "items",
            "records",
            "候选列表",
            "样本列表",
            "相似度结果",
            "样本",
            "候选",
        ):
            value = data.get(key)
            if isinstance(value, list):
                return len(value)

    return None


def resolve_stock_path(relative_path: str) -> Path:
    return STOCK_ROOT / relative_path.replace("/", "\\")


def check_stage_outputs(stage: dict[str, Any]) -> list[dict[str, Any]]:
    outputs = stage.get("标准产物", [])
    checks = []

    for output in outputs:
        path = resolve_stock_path(output)
        exists = path.exists()
        info = path.stat() if exists else None
        checks.append(
            {
                "产物": output,
                "绝对路径": str(path),
                "状态": "存在" if exists else "缺失",
                "大小KB": round(info.st_size / 1024, 2) if info else None,
                "最后修改时间": datetime.fromtimestamp(info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                if info
                else None,
                "记录数量": count_records(path) if exists and path.suffix.lower() == ".json" else None,
            }
        )

    return checks


def check_core_counts() -> list[dict[str, Any]]:
    targets = [
        {
            "名称": "强势成功样本库",
            "路径": STOCK_ROOT / "03数据" / "270杰哥推荐方法内核" / "强势成功样本库_最新.json",
            "期望数量": 150,
        },
        {
            "名称": "失败对照样本库",
            "路径": STOCK_ROOT / "03数据" / "270杰哥推荐方法内核" / "失败对照样本库_最新.json",
            "期望数量": 150,
        },
        {
            "名称": "当前候选股相似度识别器",
            "路径": STOCK_ROOT / "03数据" / "270杰哥推荐方法内核" / "当前候选股相似度识别_最新.json",
            "期望数量": 2000,
        },
    ]

    checks = []
    for target in targets:
        actual = count_records(target["路径"])
        expected = target["期望数量"]
        checks.append(
            {
                "名称": target["名称"],
                "路径": str(target["路径"]),
                "期望数量": expected,
                "实际数量": actual,
                "状态": "通过" if actual == expected else "异常",
            }
        )

    return checks


def check_extra_workflow_artifacts(workflow_rule: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    single_paths: list[tuple[str, Any]] = [
        ("只读总控脚本", workflow_rule.get("只读总控脚本")),
        ("学习链路验收脚本", workflow_rule.get("学习链路验收脚本")),
    ]
    for name, value in single_paths:
        if not value:
            checks.append({"名称": name, "路径": None, "状态": "缺失"})
            continue
        path = resolve_stock_path(str(value))
        checks.append({"名称": name, "路径": str(path), "状态": "存在" if path.exists() else "缺失"})

    list_paths: list[tuple[str, Any]] = [
        ("总控巡检产物", workflow_rule.get("总控巡检产物", [])),
        ("学习链路验收产物", workflow_rule.get("学习链路验收产物", [])),
    ]
    for name, values in list_paths:
        if not isinstance(values, list) or not values:
            checks.append({"名称": name, "路径": None, "状态": "缺失"})
            continue
        for value in values:
            path = resolve_stock_path(str(value))
            state = "存在" if path.exists() else "缺失"
            conclusion = None
            if path.exists() and path.suffix.lower() == ".json":
                try:
                    data = load_json(path)
                    if isinstance(data, dict):
                        conclusion = data.get("结论")
                        if conclusion and conclusion != "通过":
                            state = "需复核"
                except Exception:
                    state = "JSON解析失败"
            checks.append({"名称": name, "路径": str(path), "状态": state, "结论": conclusion})

    return checks


def build_report() -> dict[str, Any]:
    workflow_rule = load_json(WORKFLOW_RULE_PATH)
    kernel_rule = load_json(KERNEL_RULE_PATH)
    front_config = load_json(FRONT_CONFIG_PATH)

    stage_reports = []
    for stage in workflow_rule.get("固定先后顺序", []):
        stage_reports.append(
            {
                "顺序": stage.get("顺序"),
                "阶段": stage.get("阶段"),
                "目标": stage.get("目标"),
                "标准脚本": stage.get("标准脚本"),
                "标准入口": stage.get("标准入口"),
                "产物检查": check_stage_outputs(stage),
                "硬性验收": stage.get("硬性验收", []),
            }
        )

    required_order = [
        "数据地基",
        "量价特征提取",
        "行业归因",
        "候选评分合成",
        "分析方法v1",
        "方法内核校准",
        "单股分析材料生成",
        "前台表达投影",
        "复盘进化",
    ]
    actual_order = [stage.get("阶段") for stage in workflow_rule.get("固定先后顺序", [])]
    core_count_checks = check_core_counts()
    extra_artifact_checks = check_extra_workflow_artifacts(workflow_rule)
    missing_outputs = [
        item
        for stage in stage_reports
        for item in stage.get("产物检查", [])
        if item.get("状态") != "存在"
    ]
    abnormal_counts = [item for item in core_count_checks if item.get("状态") != "通过"]
    abnormal_extra_artifacts = [item for item in extra_artifact_checks if item.get("状态") != "存在"]

    safety = {
        "真实企微发送": False,
        "n8n触发": False,
        "券商接口": False,
        "自动交易": False,
        "买卖指令": False,
    }

    status = "通过"
    if actual_order != required_order or missing_outputs or abnormal_counts or abnormal_extra_artifacts:
        status = "需人工复核"

    return {
        "巡检时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "巡检模式": "只读",
        "巡检对象": "杰哥推荐方法工作流总控",
        "结论": status,
        "方法定位": workflow_rule.get("方法定位"),
        "固定先后顺序_期望": required_order,
        "固定先后顺序_实际": actual_order,
        "顺序检查": "通过" if actual_order == required_order else "异常",
        "规则版本": {
            "工作流规则": workflow_rule.get("版本"),
            "方法内核规则": kernel_rule.get("版本"),
            "方法内核阶段": kernel_rule.get("当前阶段"),
            "前台入口": front_config.get("入口名称"),
        },
        "核心数量检查": core_count_checks,
        "阶段巡检": stage_reports,
        "扩展验收检查": extra_artifact_checks,
        "安全边界": safety,
        "下一步建议": [
            "日常开工先运行本脚本做只读巡检。",
            "若核心数量异常，先修数据地基，再做量价特征。",
            "若量价产物缺失，禁止直接进入行业归因。",
            "若前台表达异常，先复核后台评分和观察/重点分层，不要直接改话术掩盖问题。",
        ],
    }


def save_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# 杰哥推荐方法工作流总控巡检",
        "",
        f"巡检时间：{report['巡检时间']}",
        f"结论：{report['结论']}",
        f"巡检模式：{report['巡检模式']}",
        "",
        "## 固定先后顺序",
    ]

    for index, stage in enumerate(report["固定先后顺序_实际"], 1):
        lines.append(f"{index}. {stage}")

    lines.extend(
        [
            "",
            "## 核心数量检查",
        ]
    )
    for item in report["核心数量检查"]:
        lines.append(
            f"- {item['名称']}：实际 {item['实际数量']}，期望 {item['期望数量']}，状态 {item['状态']}"
        )

    lines.extend(
        [
            "",
            "## 扩展验收检查",
        ]
    )
    for item in report.get("扩展验收检查", []):
        conclusion = f"，结论 {item.get('结论')}" if item.get("结论") else ""
        lines.append(f"- {item['名称']}：{item['状态']}{conclusion}")

    lines.extend(
        [
            "",
            "## 安全边界",
            "- 未触发真实企微发送。",
            "- 未触发n8n。",
            "- 未调用券商接口。",
            "- 未执行自动交易。",
            "- 未输出买卖指令。",
            "",
            "## 下一步建议",
        ]
    )
    for item in report["下一步建议"]:
        lines.append(f"- {item}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="【杰哥推荐】方法工作流只读总控巡检")
    parser.add_argument("--json", action="store_true", help="同时在控制台输出JSON")
    args = parser.parse_args()

    report = build_report()
    json_path = REPORT_DIR / "杰哥推荐方法工作流总控巡检_最新.json"
    md_path = REPORT_DIR / "杰哥推荐方法工作流总控巡检_最新.md"
    save_json(json_path, report)
    save_markdown(md_path, report)

    print(f"巡检结论：{report['结论']}")
    print(f"顺序检查：{report['顺序检查']}")
    print(f"巡检JSON：{json_path}")
    print(f"巡检Markdown：{md_path}")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    return 0 if report["结论"] == "通过" else 2


if __name__ == "__main__":
    raise SystemExit(main())
