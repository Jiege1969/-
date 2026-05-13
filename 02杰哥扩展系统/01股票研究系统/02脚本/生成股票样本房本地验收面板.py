#!/usr/bin/env python3
"""生成股票样本房本地验收面板。

定位：
- 只读检查股票系统作为“样本房”的关键资产是否齐备。
- 复用既有样本库、推荐方法、证据核验、安全边界和交付闭环产物。
- 不触发 n8n，不发送企业微信，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any


STOCK_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = STOCK_ROOT.parents[1]
DATA_ROOT = STOCK_ROOT / "03数据"
OUT_DIR = DATA_ROOT / "286股票样本房本地验收面板"
LOG_DIR = STOCK_ROOT / "04日志" / "股票样本房本地验收面板"

REDLINE_KEYWORDS = [
    "真实发送",
    "触发n8n",
    "Webhook",
    "券商接口",
    "自动交易",
    "交易指令",
    "收益承诺",
]

SAMPLE_ROOM_ASSETS = [
    {
        "group": "样本双账",
        "name": "强势成功样本库",
        "path": "03数据/270杰哥推荐方法内核/强势成功样本库_最新.json",
        "min_bytes": 100_000,
    },
    {
        "group": "样本双账",
        "name": "失败对照样本库",
        "path": "03数据/270杰哥推荐方法内核/失败对照样本库_最新.json",
        "min_bytes": 100_000,
    },
    {
        "group": "样本双账",
        "name": "当前候选相似度识别",
        "path": "03数据/270杰哥推荐方法内核/当前候选股相似度识别_最新.json",
        "min_bytes": 100_000,
    },
    {
        "group": "方法内核",
        "name": "杰哥推荐方法内核验收",
        "path": "03数据/270杰哥推荐方法内核/杰哥推荐方法内核验收_最新.json",
        "require_pass": True,
    },
    {
        "group": "方法内核",
        "name": "杰哥推荐工作流固化验收",
        "path": "03数据/274杰哥推荐方法工作流固化验收/杰哥推荐方法工作流固化验收_最新.json",
        "require_pass": True,
    },
    {
        "group": "通用判断",
        "name": "股票通用分析判断机制验收",
        "path": "03数据/281股票通用分析判断机制验收/股票通用分析判断机制验收_最新.json",
        "require_pass": True,
    },
    {
        "group": "推荐引擎",
        "name": "环境自适应三级漏斗推荐引擎验收",
        "path": "03数据/284环境自适应三级漏斗推荐引擎验收/环境自适应三级漏斗推荐引擎验收_最新.json",
        "require_pass": True,
    },
    {
        "group": "证据核验",
        "name": "股票证据核验总览面板",
        "path": "03数据/180证据核验总览面板/股票证据核验总览面板_最新.json",
        "min_bytes": 1_000,
    },
    {
        "group": "证据核验",
        "name": "股票报告证据源映射验收",
        "path": "03数据/219股票报告证据源映射/股票报告证据源映射预览验收_最新.json",
        "require_pass": True,
    },
    {
        "group": "安全边界",
        "name": "报告安全边界检查",
        "path": "03数据/150报告安全边界检查/股票系统报告安全边界检查_最新.json",
        "require_pass": True,
    },
    {
        "group": "安全边界",
        "name": "自动交易屏蔽加固验收",
        "path": "03数据/243股票自动交易屏蔽加固/股票自动交易屏蔽加固验收_最新.json",
        "require_pass": True,
    },
    {
        "group": "企业微信边界",
        "name": "主动推送灰度链路一键只读巡检",
        "path": "03数据/257主动推送灰度链路一键只读巡检包/股票主动推送灰度链路一键只读巡检_最新.json",
        "require_pass": True,
    },
    {
        "group": "交付闭环",
        "name": "股票研究系统交付闭环验收",
        "path": "03数据/237股票研究系统交付闭环验收/股票研究系统交付闭环验收报告验收_最新.json",
        "require_pass": True,
    },
]

LOCAL_MECHANISM_LINKS = [
    {
        "stock_sample_room_need": "样本双账",
        "existing_mechanism": "270杰哥推荐方法内核",
        "reuse_reason": "成功样本和失败对照同时存在，降低幸存者偏差。",
    },
    {
        "stock_sample_room_need": "标准工作流",
        "existing_mechanism": "274杰哥推荐方法工作流固化验收",
        "reuse_reason": "先数据地基、再量价、再行业、再前台表达、最后复盘。",
    },
    {
        "stock_sample_room_need": "通用可迁移方法",
        "existing_mechanism": "281股票通用分析判断机制验收",
        "reuse_reason": "股票样本房沉淀的是可迁移判断机制，不是照搬股票专有逻辑。",
    },
    {
        "stock_sample_room_need": "环境适配推荐",
        "existing_mechanism": "284环境自适应三级漏斗推荐引擎验收",
        "reuse_reason": "先判市场环境，再选择主指标、辅助指标和风险闸门。",
    },
    {
        "stock_sample_room_need": "外部动作红线",
        "existing_mechanism": "150报告安全边界 + 243自动交易屏蔽 + 257只读巡检",
        "reuse_reason": "研究助手只输出分析和待复核材料，不触发真实发送、n8n、券商或交易。",
    },
]


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def flatten_json(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(flatten_json(child, next_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(flatten_json(child, f"{prefix}[{index}]"))
    else:
        rows.append((prefix, value))
    return rows


def contains_pass(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return "通过" in value or lowered == "pass" or lowered == "ok"
    if isinstance(value, dict):
        return any(contains_pass(child) for child in value.values())
    if isinstance(value, list):
        return any(contains_pass(child) for child in value)
    return False


def redline_true_hits(data: Any) -> list[str]:
    hits: list[str] = []
    for path, value in flatten_json(data):
        if value is not True:
            continue
        if any(keyword in path for keyword in REDLINE_KEYWORDS):
            hits.append(path)
    return hits


def count_records(data: Any) -> int | None:
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in ("数据", "样本", "items", "records", "rows", "候选", "结果"):
            child = data.get(key)
            if isinstance(child, list):
                return len(child)
        list_lengths = [len(child) for child in data.values() if isinstance(child, list)]
        return max(list_lengths) if list_lengths else len(data)
    return None


def inspect_asset(asset: dict[str, Any]) -> dict[str, Any]:
    path = STOCK_ROOT / asset["path"]
    item: dict[str, Any] = {
        "group": asset["group"],
        "name": asset["name"],
        "path": asset["path"],
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
        "json_ok": False,
        "record_count": None,
        "pass_signal": False,
        "redline_true_hits": [],
        "status": "missing",
    }
    if not path.exists():
        return item

    try:
        data = read_json(path)
        item["json_ok"] = True
        item["record_count"] = count_records(data)
        item["pass_signal"] = contains_pass(data)
        item["redline_true_hits"] = redline_true_hits(data)
    except Exception as exc:  # noqa: BLE001 - report keeps the failure visible.
        item["json_error"] = str(exc)
        item["status"] = "json_error"
        return item

    min_bytes = asset.get("min_bytes", 0)
    required_pass = asset.get("require_pass", False)
    problems: list[str] = []
    if item["bytes"] < min_bytes:
        problems.append(f"bytes<{min_bytes}")
    if required_pass and not item["pass_signal"]:
        problems.append("missing_pass_signal")
    if item["redline_true_hits"]:
        problems.append("redline_true")

    item["status"] = "pass" if not problems else "review"
    item["problems"] = problems
    return item


def build_report() -> dict[str, Any]:
    checked_assets = [inspect_asset(asset) for asset in SAMPLE_ROOM_ASSETS]
    status_counts: dict[str, int] = {}
    group_counts: dict[str, dict[str, int]] = {}
    for asset in checked_assets:
        status_counts[asset["status"]] = status_counts.get(asset["status"], 0) + 1
        group = asset["group"]
        group_counts.setdefault(group, {})
        group_counts[group][asset["status"]] = group_counts[group].get(asset["status"], 0) + 1

    redline_hits = [
        f"{asset['name']}: {hit}"
        for asset in checked_assets
        for hit in asset.get("redline_true_hits", [])
    ]
    failed_assets = [asset for asset in checked_assets if asset["status"] != "pass"]
    gate_failures = [
        asset
        for asset in checked_assets
        if asset["status"] in {"missing", "json_error"} or asset.get("redline_true_hits")
    ]
    conclusion = "通过" if not failed_assets and not redline_hits else "需复核"
    ci_gate_status = "fail" if gate_failures or redline_hits else "pass"

    return {
        "名称": "股票样本房本地验收面板",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "定位": "股票系统作为样本房，沉淀可复用的分析、验收、边界和回灌机制。",
        "结论": conclusion,
        "检查资产数": len(checked_assets),
        "状态统计": status_counts,
        "分组统计": group_counts,
        "红线命中数": len(redline_hits),
        "红线命中": redline_hits,
        "CI闸口状态": ci_gate_status,
        "CI闸口说明": "CircleCI拦截缺失、JSON损坏和红线开启；业务复核项先记录为样本房提醒。",
        "本地机制复用关系": LOCAL_MECHANISM_LINKS,
        "资产检查": checked_assets,
        "下一步建议": next_actions(conclusion, failed_assets),
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "触发Webhook": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式库": False,
        },
    }


def next_actions(conclusion: str, failed_assets: list[dict[str, Any]]) -> list[str]:
    if conclusion == "通过":
        return [
            "继续把股票系统作为样本房，优先沉淀可复用判断机制。",
            "下一轮可补强样本房到总管/进化系统的轻量回灌索引。",
            "CircleCI 只做代码外部验收，本地施工判断继续走本面板和总管机制。",
        ]
    return [
        f"先复核 {asset['name']}：{', '.join(asset.get('problems', []))}"
        for asset in failed_assets
    ]


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票样本房本地验收面板",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 检查资产数：{report['检查资产数']}",
        f"- 红线命中数：{report['红线命中数']}",
        f"- CI闸口状态：{report['CI闸口状态']}",
        f"- CI闸口说明：{report['CI闸口说明']}",
        "",
        "## 本地机制复用关系",
    ]
    for item in report["本地机制复用关系"]:
        lines.append(
            f"- {item['stock_sample_room_need']} -> {item['existing_mechanism']}：{item['reuse_reason']}"
        )

    lines.extend(["", "## 分组统计"])
    for group, counts in report["分组统计"].items():
        detail = "，".join(f"{name}={count}" for name, count in sorted(counts.items()))
        lines.append(f"- {group}：{detail}")

    lines.extend(["", "## 资产检查"])
    for asset in report["资产检查"]:
        lines.append(
            f"- [{asset['status']}] {asset['group']} / {asset['name']}："
            f"bytes={asset['bytes']}，records={asset['record_count']}，path={asset['path']}"
        )

    lines.extend(["", "## 下一步建议"])
    for action in report["下一步建议"]:
        lines.append(f"- {action}")

    lines.extend(["", "## 安全边界"])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{str(value).lower()}")

    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = OUT_DIR / f"股票样本房本地验收面板_{stamp}.json"
    output_md = OUT_DIR / f"股票样本房本地验收面板_{stamp}.md"
    latest_json = OUT_DIR / "股票样本房本地验收面板_最新.json"
    latest_md = OUT_DIR / "股票样本房本地验收面板_最新.md"
    log_json = LOG_DIR / f"stock-sample-room-local-acceptance-{stamp}.json"

    text_json = json.dumps(report, ensure_ascii=False, indent=2)
    text_md = render_markdown(report)
    for path in (output_json, latest_json, log_json):
        path.write_text(text_json, encoding="utf-8")
    for path in (output_md, latest_md):
        path.write_text(text_md, encoding="utf-8")
    return latest_json, latest_md


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci-check", action="store_true", help="CI gate: fail only on missing/broken/redline assets")
    parser.add_argument("--no-write", action="store_true", help="do not write report files")
    parser.add_argument("--json", action="store_true", help="print JSON report to stdout")
    args = parser.parse_args()

    report = build_report()
    if not args.no_write:
        latest_json, latest_md = write_report(report)
    else:
        latest_json = latest_md = None

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"结论：{report['结论']}")
        print(f"CI闸口状态：{report['CI闸口状态']}")
        if latest_json and latest_md:
            print(f"JSON：{latest_json}")
            print(f"Markdown：{latest_md}")

    if args.ci_check:
        return 0 if report["CI闸口状态"] == "pass" else 1
    return 0 if report["结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
