#!/usr/bin/env python3
"""生成股票主线施工闸口面板。

这个面板只做本地只读检查：把股票系统主线的人工核验、批量填报、
推送前人工闸口、复盘闭环和安全边界拉到一个总闸口里。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


STOCK_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = STOCK_ROOT / "03数据"
OUT_DIR = DATA_ROOT / "287股票主线施工闸口面板"
LOG_DIR = STOCK_ROOT / "04日志" / "股票主线施工闸口面板"

REDLINE_TRUE_PATTERNS = [
    re.compile(r"真实发送[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"触发n8n[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"触发Webhook[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"调用券商接口[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"自动交易[\"']?\s*[:=]\s*true\b", re.IGNORECASE),
    re.compile(r"\breal_send\s*=\s*True\b"),
]

MAINLINE_LANES = [
    {
        "name": "人工核验入口",
        "purpose": "确认公告、财务、行业事件正文核验任务是否具备填写和完整性检查入口。",
        "assets": [
            "03数据/103人工核验结果填写/300只候选人工核验结果填写模板_最新.json",
            "03数据/116人工核验任务优先级清单/300只候选人工核验任务优先级清单_最新.json",
            "03数据/117人工核验完整性闸口/300只候选人工核验填写结果完整性闸口报告_最新.json",
            "02脚本/记录单条人工核验结果.py",
            "02脚本/验证300只候选人工核验填写结果完整性闸口报告.py",
        ],
        "expected_next": "先补齐103人工核验填写，再运行117完整性闸口。",
    },
    {
        "name": "批量填报受控导入",
        "purpose": "确认119填报表、120预演、121闸口、122受控导入的安全链路是否齐备。",
        "assets": [
            "03数据/119人工核验批量填报模板/300只候选人工核验批量填报模板_最新.csv",
            "03数据/119人工核验批量填报模板/300只候选人工核验批量填报表校验报告_最新.json",
            "03数据/120人工核验批量导入预演/300只候选人工核验批量填报导入预演_最新.json",
            "03数据/121人工核验批量导入执行闸口/300只候选人工核验批量导入执行闸口报告_最新.json",
            "03数据/122人工核验批量受控导入103/300只候选人工核验批量受控导入103报告_最新.json",
            "02脚本/受控导入300只候选人工核验批量填报到103.py",
        ],
        "expected_next": "只有120预演产生有效变更且121放行后，才允许另行显式受控导入103。",
    },
    {
        "name": "推送前人工闸口",
        "purpose": "确认候选包和人工闸口存在，但真实发送继续关闭。",
        "assets": [
            "03数据/96推送前候选包/300只候选推送前候选包_最新.json",
            "03数据/99推送前人工闸口/300只候选推送前人工闸口复核单_最新.json",
            "03数据/138推送前放行包/股票企微推送前放行包_最新.json",
            "02脚本/生成300只候选推送前人工闸口复核单.py",
        ],
        "expected_next": "未完成人工确认和正文核验前，只允许生成草案和只读闸口。",
    },
    {
        "name": "复盘闭环",
        "purpose": "确认T+1/T+3/T+5复盘、权重建议闸口和学习闭环入口是否齐备。",
        "assets": [
            "03数据/107复盘结果填写/300只候选复盘执行任务包_带人工复盘结果_最新.json",
            "03数据/114复盘到期提醒与人工填写清单/300只候选复盘到期提醒与人工填写清单_最新.json",
            "03数据/115权重建议生成闸口/300只候选权重建议生成闸口报告_最新.json",
            "03数据/187复盘学习闭环状态面板/股票复盘学习闭环状态面板_最新.json",
            "02脚本/记录单条复盘结果.py",
        ],
        "expected_next": "录入真实复盘结果前，不自动改权重，只生成候选建议或阻断原因。",
    },
    {
        "name": "安全红线闭环",
        "purpose": "确认外部动作、n8n、企业微信、券商和自动交易仍由只读闸口阻断。",
        "assets": [
            "03数据/150报告安全边界检查/股票系统报告安全边界检查_最新.json",
            "03数据/243股票自动交易屏蔽加固/股票自动交易屏蔽加固验收_最新.json",
            "03数据/252主动推送真实灰度发送前最终只读总闸口/股票主动推送真实灰度发送前最终只读总闸口_最新.json",
            "02脚本/生成股票主动推送真实灰度发送前最终只读总闸口.py",
        ],
        "expected_next": "只登记阻断状态；不进入真实外部动作。",
    },
]


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def parse_json_if_possible(path: Path) -> tuple[bool | None, str | None]:
    if path.suffix.lower() != ".json":
        return None, None
    try:
        json.loads(read_text(path))
    except Exception as exc:  # noqa: BLE001 - report must keep going.
        return False, str(exc)
    return True, None


def redline_true_hits(text: str) -> list[str]:
    return [pattern.pattern for pattern in REDLINE_TRUE_PATTERNS if pattern.search(text)]


def inspect_asset(relative_path: str) -> dict[str, Any]:
    path = STOCK_ROOT / relative_path
    item: dict[str, Any] = {
        "path": relative_path,
        "exists": path.exists(),
        "bytes": 0,
        "json_valid": None,
        "json_error": None,
        "redline_true_hits": [],
        "status": "missing",
        "problems": [],
    }
    if not path.exists():
        item["problems"].append("missing")
        return item

    item["bytes"] = path.stat().st_size
    text = read_text(path)
    item["redline_true_hits"] = redline_true_hits(text)
    json_valid, json_error = parse_json_if_possible(path)
    item["json_valid"] = json_valid
    item["json_error"] = json_error

    if item["bytes"] == 0:
        item["problems"].append("empty_file")
    if json_valid is False:
        item["problems"].append("json_parse_review")
    if item["redline_true_hits"]:
        item["problems"].append("redline_true")

    if not item["problems"]:
        item["status"] = "pass"
    elif item["problems"] == ["json_parse_review"]:
        item["status"] = "review"
    else:
        item["status"] = "fail" if "missing" in item["problems"] or "redline_true" in item["problems"] else "review"
    return item


def inspect_lane(lane: dict[str, Any]) -> dict[str, Any]:
    assets = [inspect_asset(path) for path in lane["assets"]]
    missing = [asset for asset in assets if not asset["exists"]]
    redline_hits = [
        f"{asset['path']}: {hit}"
        for asset in assets
        for hit in asset.get("redline_true_hits", [])
    ]
    review_assets = [asset for asset in assets if asset["status"] == "review"]
    if missing or redline_hits:
        status = "fail"
    elif review_assets:
        status = "review"
    else:
        status = "pass"
    return {
        "name": lane["name"],
        "purpose": lane["purpose"],
        "expected_next": lane["expected_next"],
        "status": status,
        "assets": assets,
        "missing_count": len(missing),
        "review_count": len(review_assets),
        "redline_hit_count": len(redline_hits),
        "redline_hits": redline_hits,
    }


def build_report() -> dict[str, Any]:
    lanes = [inspect_lane(lane) for lane in MAINLINE_LANES]
    missing_assets = [
        asset
        for lane in lanes
        for asset in lane["assets"]
        if not asset["exists"]
    ]
    redline_hits = [
        hit
        for lane in lanes
        for hit in lane["redline_hits"]
    ]
    review_assets = [
        asset
        for lane in lanes
        for asset in lane["assets"]
        if asset["status"] == "review"
    ]
    status_counts: dict[str, int] = {}
    for lane in lanes:
        status_counts[lane["status"]] = status_counts.get(lane["status"], 0) + 1

    ci_gate_status = "fail" if missing_assets or redline_hits else "pass"
    conclusion = "通过" if not missing_assets and not redline_hits and not review_assets else "需复核"
    return {
        "名称": "股票主线施工闸口面板",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "定位": "股票分析系统主线施工的本地只读总闸口，服务样本房规范搭建。",
        "结论": conclusion,
        "CI闸口状态": ci_gate_status,
        "CI闸口说明": "CI只拦截缺失资产和红线开启；历史JSON格式问题记录为业务复核，不阻塞代码构建。",
        "泳道数": len(lanes),
        "泳道状态统计": status_counts,
        "缺失资产数": len(missing_assets),
        "需复核资产数": len(review_assets),
        "红线命中数": len(redline_hits),
        "主线泳道": lanes,
        "下一步建议": next_actions(lanes, missing_assets, review_assets, redline_hits),
        "construction_queue": build_construction_queue(lanes),
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "触发Webhook": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式库": False,
            "重启服务": False,
        },
    }


def lane_blocking_reason(lane: dict[str, Any]) -> str:
    if lane.get("redline_hit_count", 0):
        return "redline_hit"
    if lane.get("missing_count", 0):
        return "missing_asset"
    if lane.get("review_count", 0):
        return "review_asset"
    return "ready"


def lane_asset_paths_by_status(lane: dict[str, Any], status: str) -> list[str]:
    return [
        asset["path"]
        for asset in lane.get("assets", [])
        if asset.get("status") == status
    ]


def build_construction_queue(lanes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for index, lane in enumerate(lanes, start=1):
        queue.append(
            {
                "priority": index * 10,
                "lane": lane["name"],
                "status": lane["status"],
                "blocking_reason": lane_blocking_reason(lane),
                "expected_next": lane["expected_next"],
                "missing_assets": lane_asset_paths_by_status(lane, "missing"),
                "review_assets": lane_asset_paths_by_status(lane, "review"),
                "redline_hits": lane.get("redline_hits", []),
            }
        )
    return sorted(queue, key=lambda item: (item["blocking_reason"] == "ready", item["priority"]))


def next_actions(
    lanes: list[dict[str, Any]],
    missing_assets: list[dict[str, Any]],
    review_assets: list[dict[str, Any]],
    redline_hits: list[str],
) -> list[str]:
    if redline_hits:
        return ["立即停止外部动作，只保留本地排查；红线命中必须先清零。"]
    if missing_assets:
        return [f"先补齐缺失资产：{asset['path']}" for asset in missing_assets[:8]]
    if review_assets:
        return [
            "历史JSON格式存在复核项，但主线闸口和CI可继续；优先把人工核验和复盘材料补齐。",
            "下一轮主线：103人工核验填写 -> 117完整性闸口 -> 108联动刷新 -> 推送前草案闸口。",
        ]
    return [lane["expected_next"] for lane in lanes]


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票主线施工闸口面板",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- CI闸口状态：{report['CI闸口状态']}",
        f"- CI闸口说明：{report['CI闸口说明']}",
        f"- 泳道数：{report['泳道数']}",
        f"- 缺失资产数：{report['缺失资产数']}",
        f"- 需复核资产数：{report['需复核资产数']}",
        f"- 红线命中数：{report['红线命中数']}",
        "",
        "## 主线泳道",
    ]
    for lane in report["主线泳道"]:
        lines.extend(
            [
                f"### {lane['name']}",
                "",
                f"- 状态：{lane['status']}",
                f"- 作用：{lane['purpose']}",
                f"- 下一步：{lane['expected_next']}",
                f"- 缺失：{lane['missing_count']}，复核：{lane['review_count']}，红线：{lane['redline_hit_count']}",
                "",
            ]
        )
        for asset in lane["assets"]:
            problems = ",".join(asset.get("problems", [])) or "none"
            lines.append(f"- [{asset['status']}] {asset['path']} bytes={asset['bytes']} problems={problems}")
        lines.append("")

    lines.extend(["## 下一步建议", ""])
    lines.extend([f"- {action}" for action in report["下一步建议"]])
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{str(value).lower()}")
    if report.get("construction_queue"):
        lines.extend(["", "## Construction Queue", ""])
        for item in report["construction_queue"]:
            lines.append(
                "- "
                f"P{item['priority']} {item['lane']}: "
                f"{item['status']}; {item['blocking_reason']}; "
                f"{item['expected_next']}"
            )
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = OUT_DIR / f"股票主线施工闸口面板_{stamp}.json"
    output_md = OUT_DIR / f"股票主线施工闸口面板_{stamp}.md"
    latest_json = OUT_DIR / "股票主线施工闸口面板_最新.json"
    latest_md = OUT_DIR / "股票主线施工闸口面板_最新.md"
    log_json = LOG_DIR / f"stock-mainline-construction-gate-{stamp}.json"

    text_json = json.dumps(report, ensure_ascii=False, indent=2)
    text_md = render_markdown(report)
    for path in (output_json, latest_json, log_json):
        path.write_text(text_json, encoding="utf-8")
    for path in (output_md, latest_md):
        path.write_text(text_md, encoding="utf-8")
    return latest_json, latest_md


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ci-check", action="store_true", help="CI gate: fail only on missing assets or redline true")
    parser.add_argument("--no-write", action="store_true", help="do not write report files")
    parser.add_argument("--json", action="store_true", help="print JSON report to stdout")
    args = parser.parse_args()

    report = build_report()
    if not args.no_write:
        latest_json, latest_md = write_report(report)
        print(f"已生成：{latest_json}")
        print(f"已生成：{latest_md}")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    print(f"结论：{report['结论']}")
    print(f"CI闸口状态：{report['CI闸口状态']}")
    if args.ci_check:
        return 0 if report["CI闸口状态"] == "pass" else 1
    return 0 if report["结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
