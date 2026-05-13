# -*- coding: utf-8 -*-
"""
生成股票每日推送总表只读巡检报告。

安全边界：
- 只读取股票每日推送总表、前台定稿规则和推送样本文档。
- 只写入本地巡检报告目录。
- 不调用企业微信 API，不真实发送，不触发 n8n，不访问 Webhook。
- 不连接券商，不执行交易，不重启服务。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = ROOT / "01配置" / "股票每日推送总表_v1.0.json"
CONTRACT_PATH = ROOT / "01配置" / "股票前台报告表达定稿规则_v1.0.json"
SAMPLE_DOC_PATH = ROOT / "07文档" / "股票前台推送消息样本_v1.0.md"
OUT_DIR = ROOT / "03数据" / "股票每日推送总表只读巡检"
REPORT_BASENAME = "股票每日推送总表只读巡检报告"

REQUIRED_CURRENT_TASKS = [
    "preopen_shortlist_0850",
    "postclose_short_observation_1530",
    "night_expert_research_2100",
]

REQUIRED_TASK_FIELDS = [
    "任务ID",
    "状态",
    "推送时间",
    "推送类型",
    "对应机器人",
    "消息标题",
    "内容字段",
    "样本文件",
    "生成脚本",
    "是否允许真实发送",
    "是否允许触发n8n",
    "是否允许Webhook",
    "是否进入CI检查",
]

REQUIRED_NUMERIC_FIELDS = [
    "当前价",
    "最近5日平均成交量",
    "放量达标线",
    "当前成交量",
    "风险线",
]

SAFETY_FALSE_KEYS = [
    "是否允许真实发送",
    "是否允许触发n8n",
    "是否允许Webhook",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sample_anchor_exists(sample_ref: str, sample_text: str) -> bool:
    if "#" not in sample_ref:
        return False
    anchor = sample_ref.split("#", 1)[1]
    compact_anchor = "".join(ch for ch in anchor if ch.isalnum())
    for line in sample_text.splitlines():
        if not line.startswith("#"):
            continue
        compact_line = "".join(ch for ch in line.lstrip("# ").strip() if ch.isalnum())
        if compact_anchor in compact_line or compact_line in compact_anchor:
            return True
    return False


def script_path(task: dict[str, Any]) -> Path:
    return ROOT / str(task.get("生成脚本", ""))


def sample_path(task: dict[str, Any]) -> Path:
    sample_ref = str(task.get("样本文件", ""))
    return ROOT / sample_ref.split("#", 1)[0] if sample_ref else ROOT


def build_task_report(task: dict[str, Any], sample_text: str) -> dict[str, Any]:
    content_fields = task.get("内容字段", [])
    if not isinstance(content_fields, list):
        content_fields = []
    return {
        "任务ID": task.get("任务ID"),
        "推送时间": task.get("推送时间"),
        "推送类型": task.get("推送类型"),
        "对应机器人": task.get("对应机器人"),
        "状态": task.get("状态"),
        "必填字段齐全": all(field in task for field in REQUIRED_TASK_FIELDS),
        "缺失字段": [field for field in REQUIRED_TASK_FIELDS if field not in task],
        "计算字段覆盖": {
            field: field in content_fields
            for field in REQUIRED_NUMERIC_FIELDS
        },
        "脚本存在": script_path(task).exists(),
        "脚本路径": rel(script_path(task)) if script_path(task).exists() else str(task.get("生成脚本", "")),
        "样本文件存在": sample_path(task).exists(),
        "样本锚点存在": sample_anchor_exists(str(task.get("样本文件", "")), sample_text),
        "安全开关": {
            key: task.get(key) is False
            for key in SAFETY_FALSE_KEYS
        },
        "进入CI检查": task.get("是否进入CI检查") is True,
    }


def validate_report(report: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if not report["文件"]["总表存在"]:
        problems.append("missing_daily_push_table")
    if not report["文件"]["定稿规则存在"]:
        problems.append("missing_frontend_contract")
    if not report["文件"]["样本文档存在"]:
        problems.append("missing_push_sample_doc")

    for task_id, present in report["现行任务覆盖"].items():
        if not present:
            problems.append(f"missing_current_task:{task_id}")
    for key, ok in report["安全总开关"].items():
        if not ok:
            problems.append(f"global_safety_not_false:{key}")

    for task in report["任务巡检"]:
        task_id = task.get("任务ID") or "unknown"
        if not task["必填字段齐全"]:
            problems.append(f"task_missing_fields:{task_id}:{','.join(task['缺失字段'])}")
        for field, present in task["计算字段覆盖"].items():
            if not present:
                problems.append(f"task_missing_numeric_field:{task_id}:{field}")
        if not task["脚本存在"]:
            problems.append(f"task_script_missing:{task_id}")
        if not task["样本文件存在"]:
            problems.append(f"task_sample_file_missing:{task_id}")
        if not task["样本锚点存在"]:
            problems.append(f"task_sample_anchor_missing:{task_id}")
        for key, ok in task["安全开关"].items():
            if not ok:
                problems.append(f"task_safety_not_false:{task_id}:{key}")
        if not task["进入CI检查"]:
            problems.append(f"task_not_in_ci:{task_id}")
    return problems


def build_report(now: str | None = None) -> dict[str, Any]:
    generated_at = now or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    table = read_json(TABLE_PATH) if TABLE_PATH.exists() else {}
    sample_text = read_text(SAMPLE_DOC_PATH) if SAMPLE_DOC_PATH.exists() else ""
    tasks = table.get("推送任务", []) if isinstance(table.get("推送任务"), list) else []
    task_reports = [build_task_report(task, sample_text) for task in tasks if isinstance(task, dict)]

    safety = table.get("安全总开关", {}) if isinstance(table.get("安全总开关"), dict) else {}
    report = {
        "报告名称": REPORT_BASENAME,
        "生成时间": generated_at,
        "安全声明": "只读巡检和本地报告，不真实发送，不触发n8n，不访问Webhook，不连接券商，不自动交易。",
        "文件": {
            "总表": rel(TABLE_PATH),
            "总表存在": TABLE_PATH.exists(),
            "定稿规则": rel(CONTRACT_PATH),
            "定稿规则存在": CONTRACT_PATH.exists(),
            "样本文档": rel(SAMPLE_DOC_PATH),
            "样本文档存在": SAMPLE_DOC_PATH.exists(),
        },
        "现行任务覆盖": {
            task_id: any(task.get("任务ID") == task_id for task in tasks if isinstance(task, dict))
            for task_id in REQUIRED_CURRENT_TASKS
        },
        "安全总开关": {
            "允许真实发送企业微信": safety.get("允许真实发送企业微信") is False,
            "允许触发n8n": safety.get("允许触发n8n") is False,
            "允许Webhook": safety.get("允许Webhook") is False,
            "允许调用券商接口": safety.get("允许调用券商接口") is False,
            "允许自动交易": safety.get("允许自动交易") is False,
        },
        "任务巡检": task_reports,
        "实际动作": {
            "读取总表": True,
            "读取样本": SAMPLE_DOC_PATH.exists(),
            "写本地巡检报告": True,
            "企业微信真实发送": False,
            "触发n8n": False,
            "访问Webhook": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启服务": False,
        },
    }
    problems = validate_report(report)
    report["结论"] = "pass" if not problems else "fail"
    report["阻断问题"] = problems
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票每日推送总表只读巡检报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 安全声明：{report['安全声明']}",
        "",
        "## 现行任务",
        "",
    ]
    for task_id, present in report["现行任务覆盖"].items():
        lines.append(f"- {task_id}：{'通过' if present else '缺失'}")

    lines.extend(["", "## 安全总开关", ""])
    for key, ok in report["安全总开关"].items():
        lines.append(f"- {key}：{'关闭' if ok else '异常'}")

    lines.extend(["", "## 任务巡检", ""])
    for task in report["任务巡检"]:
        lines.extend(
            [
                f"### {task['任务ID']}",
                "",
                f"- 时间：{task['推送时间']}",
                f"- 类型：{task['推送类型']}",
                f"- 机器人：{task['对应机器人']}",
                f"- 脚本存在：{task['脚本存在']}",
                f"- 样本文件存在：{task['样本文件存在']}",
                f"- 样本锚点存在：{task['样本锚点存在']}",
                f"- 进入CI检查：{task['进入CI检查']}",
                "",
            ]
        )
    if report["阻断问题"]:
        lines.extend(["## 阻断问题", ""])
        for problem in report["阻断问题"]:
            lines.append(f"- {problem}")
        lines.append("")
    return "\n".join(lines)


def write_report(report: dict[str, Any]) -> dict[str, str]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"{REPORT_BASENAME}_{stamp}.json"
    md_path = OUT_DIR / f"{REPORT_BASENAME}_{stamp}.md"
    latest_json = OUT_DIR / f"{REPORT_BASENAME}_最新.json"
    latest_md = OUT_DIR / f"{REPORT_BASENAME}_最新.md"
    write_json(json_path, report)
    write_json(latest_json, report)
    markdown = render_markdown(report)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)
    return {
        "json": str(json_path),
        "markdown": str(md_path),
        "latest_json": str(latest_json),
        "latest_markdown": str(latest_md),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print JSON report")
    parser.add_argument("--check-only", action="store_true", help="do not write local report files")
    args = parser.parse_args()

    report = build_report()
    outputs: dict[str, str] = {}
    if not args.check_only:
        outputs = write_report(report)
        report["输出文件"] = outputs

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(report))

    return 0 if report["结论"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
