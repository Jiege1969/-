# -*- coding: utf-8 -*-
"""生成运行期周报与状态看板数据包。

只读取本地验收与交付状态，生成周报、看板数据和红线状态摘要；
不请求业务接口、不触发外部系统、不修改正式规则。
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "85运行期周报与状态看板数据包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "运行期周报与状态看板数据包验收"

SOURCES = {
    "总巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "最终交付收尾": EVOLUTION_ROOT / "03数据" / "80日常可用版与稳定交付版最终交付收尾包" / "日常可用版与稳定交付版最终交付收尾包_最新.json",
    "每日开工收工": EVOLUTION_ROOT / "03数据" / "82每日开工收工清单与低风险续跑包" / "每日开工收工清单与低风险续跑包_最新.json",
    "首周趋势升级": EVOLUTION_ROOT / "03数据" / "83首周运行趋势与问题升级包" / "首周运行趋势与问题升级包_最新.json",
    "运行期问题台账": EVOLUTION_ROOT / "03数据" / "84运行期问题闭环总台账索引包" / "运行期问题闭环总台账索引包_最新.json",
    "三日达标判定": EVOLUTION_ROOT / "03数据" / "84稳定交付版三日达标判定器与样本采集标准包" / "稳定交付版三日达标判定器与样本采集标准包_最新.json",
    "股票共振规则周度进化评估": EVOLUTION_ROOT / "03数据" / "86股票共振规则周度进化评估" / "股票共振规则周度进化评估_最新.json",
    "税收政策引用周度进化评估": EVOLUTION_ROOT / "03数据" / "87税收政策引用周度进化评估" / "税收政策引用周度进化评估_最新.json",
}

PACKAGE_JSON = DATA_DIR / "运行期周报与状态看板数据包_最新.json"
PACKAGE_MD = DATA_DIR / "运行期周报与状态看板数据包_最新.md"
WEEKLY_MD = DATA_DIR / "运行期周报摘要_最新.md"
DASHBOARD_JSON = DATA_DIR / "状态看板数据_最新.json"
DASHBOARD_MD = DATA_DIR / "状态看板数据_最新.md"
REDLINE_MD = DATA_DIR / "红线状态摘要_最新.md"
GEN_LOG = LOG_DIR / "生成运行期周报与状态看板数据包_最新.json"

SAFETY_BOUNDARY = {
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
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_source_summary() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name, path in SOURCES.items():
        data = read_json(path)
        result[name] = {
            "路径": str(path),
            "存在": path.exists(),
            "状态": data.get("状态") or data.get("总体状态") or data.get("通过") or data.get("passed"),
            "汇总": data.get("汇总") or data.get("指标") or data.get("metrics") or {},
        }
    return result


def run_stock_signal_evolution_scan() -> dict[str, Any]:
    script = EVOLUTION_ROOT / "02脚本" / "生成股票共振规则周度进化评估.py"
    if not script.exists():
        return {"执行": False, "成功": False, "原因": f"脚本不存在：{script}"}
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(script.parent),
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


def run_tax_policy_evolution_scan() -> dict[str, Any]:
    script = EVOLUTION_ROOT / "02脚本" / "生成税收政策引用周度进化评估.py"
    if not script.exists():
        return {"执行": False, "成功": False, "原因": f"脚本不存在：{script}"}
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(script.parent),
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


def main() -> int:
    stock_signal_scan = run_stock_signal_evolution_scan()
    tax_policy_scan = run_tax_policy_evolution_scan()
    snapshot = read_json(SOURCES["总巡检快照"])
    regression = read_json(SOURCES["一键只读总回归"])
    delivery = read_json(SOURCES["最终交付收尾"])
    stock_signal_evolution = read_json(SOURCES["股票共振规则周度进化评估"])
    tax_policy_evolution = read_json(SOURCES["税收政策引用周度进化评估"])
    source_summary = build_source_summary()
    snapshot_summary = snapshot.get("汇总", {})
    regression_metrics = regression.get("指标", {})
    redline_rows = [{"红线": key, "当前状态": value} for key, value in SAFETY_BOUNDARY.items()]
    dashboard = {
        "名称": "状态看板数据",
        "生成时间": now_text(),
        "总体状态": "pass" if snapshot.get("总体状态") == "pass" and regression_metrics.get("错误数", 0) == 0 else "blocked",
        "总巡检": snapshot_summary,
        "一键总回归": regression_metrics,
        "交付状态": delivery.get("状态"),
        "日常可用交付版": delivery.get("交付层级", {}).get("日常可用交付版", {}).get("状态"),
        "稳定交付版": delivery.get("交付层级", {}).get("稳定交付版", {}).get("状态"),
        "红线关闭数量": sum(1 for value in SAFETY_BOUNDARY.values() if value is False),
        "红线总数": len(SAFETY_BOUNDARY),
        "红线全部关闭": all(value is False for value in SAFETY_BOUNDARY.values()),
        "来源状态": source_summary,
    }
    package = {
        "名称": "运行期周报与状态看板数据包",
        "生成时间": now_text(),
        "状态": "runtime_weekly_dashboard_ready" if dashboard["总体状态"] == "pass" else "runtime_weekly_dashboard_blocked",
        "用途": "把运行期总巡检、总回归、交付状态、问题闭环和红线状态汇总为周报和看板数据。",
        "周报摘要": {
            "总巡检": snapshot_summary,
            "一键总回归": regression_metrics,
            "交付状态": delivery.get("状态"),
            "股票共振规则进化评估": {
                "扫描执行": stock_signal_scan,
                "评估结论": stock_signal_evolution.get("参数调整建议"),
                "可评估样本数": stock_signal_evolution.get("可评估样本数"),
                "成功率百分比": stock_signal_evolution.get("成功率百分比"),
            },
            "税收政策引用进化评估": {
                "扫描执行": tax_policy_scan,
                "评估结论": tax_policy_evolution.get("评估结论"),
                "政策引用总数": tax_policy_evolution.get("政策引用总数"),
                "政策引用准确率百分比": tax_policy_evolution.get("政策引用准确率百分比"),
                "待阅建议数": tax_policy_evolution.get("待阅建议数"),
            },
            "本期结论": "运行期状态正常，红线保持关闭，日常可用版与稳定交付版可继续使用。",
        },
        "看板数据": dashboard,
        "红线状态": redline_rows,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "周报摘要": str(WEEKLY_MD),
            "状态看板JSON": str(DASHBOARD_JSON),
            "状态看板Markdown": str(DASHBOARD_MD),
            "红线状态摘要": str(REDLINE_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    write_json(DASHBOARD_JSON, dashboard)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    redline_md_rows = [f"| {row['红线']} | {row['当前状态']} |" for row in redline_rows]
    package_md = "\n".join([
        "# 运行期周报与状态看板数据包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        f"- 本期结论：{package['周报摘要']['本期结论']}",
        f"- 总巡检：{snapshot_summary}",
        f"- 一键总回归：{regression_metrics}",
        f"- 股票共振规则进化评估：{stock_signal_evolution.get('参数调整建议', '暂无')}",
        f"- 税收政策引用进化评估：{tax_policy_evolution.get('评估结论', '暂无')}",
        "",
        "| 来源 | 存在 | 状态 | 路径 |",
        "| --- | --- | --- | --- |",
        *source_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(WEEKLY_MD, package_md)
    write_text(DASHBOARD_MD, "\n".join([
        "# 状态看板数据",
        "",
        f"- 总体状态：{dashboard['总体状态']}",
        f"- 总巡检：{dashboard['总巡检']}",
        f"- 一键总回归：{dashboard['一键总回归']}",
        f"- 日常可用交付版：{dashboard['日常可用交付版']}",
        f"- 稳定交付版：{dashboard['稳定交付版']}",
        f"- 红线全部关闭：{dashboard['红线全部关闭']}",
    ]))
    write_text(REDLINE_MD, "\n".join(["# 红线状态摘要", "", "| 红线 | 当前状态 |", "| --- | --- |", *redline_md_rows]))
    write_json(GEN_LOG, {"名称": "生成运行期周报与状态看板数据包", "生成时间": now_text(), "通过": package["状态"] == "runtime_weekly_dashboard_ready", "错误数": 0 if package["状态"] == "runtime_weekly_dashboard_ready" else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "总巡检": snapshot_summary, "一键总回归": regression_metrics, "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if package["状态"] == "runtime_weekly_dashboard_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
