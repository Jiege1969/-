# -*- coding: utf-8 -*-
"""
名称：生成税收政策引用周度进化评估.py
作用：读取税收草案输出规则调试日志，周度评估政策引用准确率和待复核高频政策，生成规则更新建议候选。
触发方式：python 生成税收政策引用周度进化评估.py
安全边界：只读税收调试日志；只写进化评估报告；不自动改正式规则；不生成正式税务结论；不登录电子税务局；不接财税软件。
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(r"D:\杰哥智能化系统")
TAX_ROOT = ROOT / "02杰哥扩展系统" / "05税收业务系统"
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
LOG_SCRIPT = TAX_ROOT / "02脚本" / "生成税收草案输出规则调试日志.py"
DEBUG_DIR = TAX_ROOT / "03数据" / "34税收草案输出规则调试日志"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "87税收政策引用周度进化评估"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_debug_log_refresh() -> dict[str, Any]:
    if not LOG_SCRIPT.exists():
        return {"执行": False, "成功": False, "原因": f"脚本不存在：{LOG_SCRIPT}"}
    completed = subprocess.run(
        [sys.executable, str(LOG_SCRIPT)],
        cwd=str(LOG_SCRIPT.parent),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return {
        "执行": True,
        "成功": completed.returncode == 0,
        "返回码": completed.returncode,
        "stdout": (completed.stdout or "").strip()[-2000:],
        "stderr": (completed.stderr or "").strip()[-2000:],
    }


def debug_log_files() -> list[Path]:
    files = sorted(DEBUG_DIR.glob("税收草案输出规则调试日志_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    archived = [item for item in files if item.name != "税收草案输出规则调试日志_最新.json"]
    return archived or [DEBUG_DIR / "税收草案输出规则调试日志_最新.json"]


def collect_policy_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for path in debug_log_files():
        data = load_json(path, {})
        for draft in data.get("调试日志", []) if isinstance(data.get("调试日志"), list) else []:
            for policy in draft.get("政策引用", []) if isinstance(draft.get("政策引用"), list) else []:
                key = (
                    str(draft.get("草案来源", "")),
                    str(draft.get("问题ID", "")),
                    str(policy.get("政策键", "")),
                    str(policy.get("角色", "")),
                )
                if key in seen:
                    continue
                seen.add(key)
                rows.append({
                    "草案来源": draft.get("草案来源", ""),
                    "问题ID": draft.get("问题ID", ""),
                    "问题": draft.get("问题", ""),
                    "政策键": policy.get("政策键", ""),
                    "标题": policy.get("标题", ""),
                    "文号": policy.get("文号", ""),
                    "角色": policy.get("角色", ""),
                    "文件时效": policy.get("文件时效", ""),
                    "引用状态": policy.get("引用状态", ""),
                    "阻断原因": policy.get("阻断原因", []),
                })
    return rows


def evaluate(rows: list[dict[str, Any]], refresh: dict[str, Any]) -> dict[str, Any]:
    total = len(rows)
    accurate = [item for item in rows if item.get("引用状态") == "准确引用"]
    pending = [item for item in rows if item.get("引用状态") == "待复核"]
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"引用次数": 0, "准确次数": 0, "待复核次数": 0, "样本": []})
    for item in rows:
        bucket = grouped[str(item.get("政策键") or "未命名政策")]
        bucket["引用次数"] += 1
        if item.get("引用状态") == "准确引用":
            bucket["准确次数"] += 1
        if item.get("引用状态") == "待复核":
            bucket["待复核次数"] += 1
            bucket["样本"].append({
                "问题": item.get("问题", ""),
                "角色": item.get("角色", ""),
                "文件时效": item.get("文件时效", ""),
                "阻断原因": item.get("阻断原因", []),
            })
    policy_stats = []
    suggestions = []
    for key, value in sorted(grouped.items(), key=lambda pair: (-pair[1]["待复核次数"], pair[0])):
        total_ref = int(value["引用次数"])
        pending_count = int(value["待复核次数"])
        pending_rate = pending_count / total_ref if total_ref else 0
        stat = {
            "政策键": key,
            "引用次数": total_ref,
            "准确次数": int(value["准确次数"]),
            "待复核次数": pending_count,
            "待复核率百分比": round(pending_rate * 100, 2),
            "样本": value["样本"][:5],
        }
        policy_stats.append(stat)
        if pending_count >= 2 or (total_ref >= 3 and pending_rate >= 0.5):
            suggestions.append(f"建议更新税收草案引用规则：{key} 被标记待复核 {pending_count}/{total_ref} 次，先补正式依据角色、发文机关、施行日期、适用期间和上下位关系校验后，再允许支撑草案结论。")
    accuracy_rate = len(accurate) / total if total else None
    if not rows:
        conclusion = "暂无可评估政策引用样本，先继续积累税收草案输出规则调试日志。"
    elif suggestions:
        conclusion = f"发现 {len(suggestions)} 条税收政策引用规则更新建议，需人工待阅。"
    else:
        conclusion = "本周政策引用准确率未触发规则更新建议，继续观察。"
    return {
        "名称": "税收政策引用周度进化评估",
        "状态": "完成",
        "生成时间": now_text(),
        "调试日志刷新": refresh,
        "政策引用总数": total,
        "准确引用数": len(accurate),
        "待复核引用数": len(pending),
        "政策引用准确率": accuracy_rate,
        "政策引用准确率百分比": round(accuracy_rate * 100, 2) if accuracy_rate is not None else None,
        "待阅建议数": len(suggestions),
        "评估结论": conclusion,
        "规则更新建议": suggestions,
        "政策统计": policy_stats,
        "安全边界": {
            "是否自动改正式规则": False,
            "是否生成正式税务结论": False,
            "是否登录电子税务局": False,
            "是否接财税软件": False,
            "是否企业微信真实发送": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 税收政策引用周度进化评估 - {report['生成时间']}",
        "",
        f"- 政策引用总数：{report['政策引用总数']}",
        f"- 准确引用数：{report['准确引用数']}",
        f"- 待复核引用数：{report['待复核引用数']}",
        f"- 政策引用准确率：{report['政策引用准确率百分比']}%",
        f"- 待阅建议数：{report['待阅建议数']}",
        f"- 评估结论：{report['评估结论']}",
        "",
        "## 规则更新建议",
        "",
    ]
    if report["规则更新建议"]:
        lines.extend([f"- {item}" for item in report["规则更新建议"]])
    else:
        lines.append("- 暂无。")
    lines.extend(["", "## 政策统计", "", "| 政策 | 引用 | 准确 | 待复核 | 待复核率 |", "| --- | ---: | ---: | ---: | ---: |"])
    for item in report["政策统计"]:
        lines.append(f"| {item['政策键']} | {item['引用次数']} | {item['准确次数']} | {item['待复核次数']} | {item['待复核率百分比']}% |")
    lines.extend(["", "## 安全边界", "", "- 不自动改正式规则。", "- 不生成正式税务结论。", "- 不登录电子税务局。", "- 不接财税软件。", "- 不企业微信真实发送。"])
    return "\n".join(lines) + "\n"


def main() -> int:
    refresh = run_debug_log_refresh()
    rows = collect_policy_rows()
    report = evaluate(rows, refresh)
    stamp = stamp_text()
    output_json = OUTPUT_DIR / f"税收政策引用周度进化评估_{stamp}.json"
    output_md = OUTPUT_DIR / f"税收政策引用周度进化评估_{stamp}.md"
    latest_json = OUTPUT_DIR / "税收政策引用周度进化评估_最新.json"
    latest_md = OUTPUT_DIR / "税收政策引用周度进化评估_最新.md"
    quality_weekly_md = OUTPUT_DIR / "系统质量周报_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_text(quality_weekly_md, markdown)
    print(json.dumps({"状态": "完成", "政策引用总数": report["政策引用总数"], "待阅建议数": report["待阅建议数"], "输出": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
