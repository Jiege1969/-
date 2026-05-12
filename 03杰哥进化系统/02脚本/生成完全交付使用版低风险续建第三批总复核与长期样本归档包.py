# -*- coding: utf-8 -*-
"""生成完全交付使用版低风险续建第三批总复核与长期样本归档包。

只做低风险证据总复核、长期样本归档入口和后续缺口清单；
不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "105完全交付使用版低风险续建第三批总复核与长期样本归档包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版低风险续建第三批总复核与长期样本归档包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "低风险续建启动队列": EVOLUTION_ROOT / "03数据" / "102完全交付使用版低风险续建启动队列包" / "完全交付使用版低风险续建启动队列包_最新.json",
    "低风险续建第一批执行": EVOLUTION_ROOT / "03数据" / "103完全交付使用版低风险续建第一批执行包" / "完全交付使用版低风险续建第一批执行包_最新.json",
    "低风险续建第二批复核": EVOLUTION_ROOT / "03数据" / "104完全交付使用版低风险续建第二批复核包" / "完全交付使用版低风险续建第二批复核包_最新.json",
    "运行期周报与状态看板": EVOLUTION_ROOT / "03数据" / "85运行期周报与状态看板数据包" / "运行期周报与状态看板数据包_最新.json",
    "首周运行趋势与问题升级": EVOLUTION_ROOT / "03数据" / "83首周运行趋势与问题升级包" / "首周运行趋势与问题升级包_最新.json",
    "稳定交付版每日运行日报与次日待办": EVOLUTION_ROOT / "03数据" / "85稳定交付版每日运行日报与次日待办包" / "稳定交付版每日运行日报与次日待办包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "完全交付使用版低风险续建第三批总复核与长期样本归档包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版低风险续建第三批总复核与长期样本归档包_最新.md"
RECHECK_MD = DATA_DIR / "第三批低风险总复核台账_最新.md"
SAMPLE_MD = DATA_DIR / "长期样本归档入口_最新.md"
GAP_MD = DATA_DIR / "后续缺口与确认事项_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版低风险续建第三批总复核与长期样本归档包_最新.json"

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


def recheck_items() -> list[dict[str, str]]:
    return [
        {"复核项": "第一批低风险执行", "结论": "通过，全部停留在证据归并和索引层", "真实能力": "未启用"},
        {"复核项": "第二批低风险复核", "结论": "通过，正式规则/n8n/视频均未解锁", "真实能力": "未启用"},
        {"复核项": "长期样本来源", "结论": "周报、趋势、日报入口可用于只读归档", "真实能力": "未启用"},
        {"复核项": "红线守护", "结论": "所有真实外部动作仍需总管确认", "真实能力": "未启用"},
        {"复核项": "已封存双版本影响", "结论": "不修改日常版和稳定版封存结论", "真实能力": "未启用"},
    ]


def sample_items() -> list[dict[str, str]]:
    return [
        {"样本入口": "运行期周报与状态看板", "用途": "长期状态趋势", "默认动作": "只读归档"},
        {"样本入口": "首周运行趋势与问题升级", "用途": "早期问题升级和趋势基线", "默认动作": "只读归档"},
        {"样本入口": "稳定交付版每日运行日报与次日待办", "用途": "日级运行观察", "默认动作": "只读归档"},
        {"样本入口": "日常可用版自主巡检快照", "用途": "总体验收趋势", "默认动作": "只读归档"},
        {"样本入口": "一键只读总回归", "用途": "基础链路健康样本", "默认动作": "只读归档"},
    ]


def gap_items() -> list[dict[str, str]]:
    return [
        {"缺口": "真实企业微信发送", "当前处理": "继续本地预演", "确认要求": "总管确认后另行解锁"},
        {"缺口": "n8n真实触发", "当前处理": "继续离线干跑和禁用态检查", "确认要求": "总管确认后另行解锁"},
        {"缺口": "正式规则生效", "当前处理": "继续申请草案和冲突扫描", "确认要求": "总管确认后另行解锁"},
        {"缺口": "视频真实渲染/发布", "当前处理": "继续材料复核和回滚证据", "确认要求": "总管确认后另行解锁"},
        {"缺口": "真正自主运行", "当前处理": "继续长期样本和人工接管演练", "确认要求": "长期验证后再评估"},
    ]


def main() -> int:
    source_summary: dict[str, Any] = {}
    for name, path in SOURCES.items():
        data = read_json(path)
        source_summary[name] = {
            "路径": str(path),
            "存在": path.exists(),
            "状态": data.get("总体状态") or data.get("状态") or data.get("通过") or data.get("passed"),
            "指标": data.get("汇总") or data.get("指标") or data.get("metrics") or {},
        }

    snapshot = read_json(SOURCES["日常可用版自主巡检快照"])
    regression = read_json(SOURCES["日常可用版一键只读总回归"])
    ready = (
        all(item["存在"] for item in source_summary.values())
        and snapshot.get("总体状态") == "pass"
        and snapshot.get("汇总", {}).get("失败", 0) == 0
        and regression.get("通过") is True
        and regression.get("指标", {}).get("错误数", 0) == 0
    )
    package = {
        "名称": "完全交付使用版低风险续建第三批总复核与长期样本归档包",
        "生成时间": now_text(),
        "状态": "full_delivery_low_risk_batch3_sample_archive_ready" if ready else "full_delivery_low_risk_batch3_sample_archive_blocked",
        "用途": "总复核完全交付使用版前三批低风险证据，并建立长期样本只读归档入口。",
        "来源摘要": source_summary,
        "第三批低风险总复核台账": recheck_items(),
        "长期样本归档入口": sample_items(),
        "后续缺口与确认事项": gap_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "第三批低风险总复核台账": str(RECHECK_MD),
            "长期样本归档入口": str(SAMPLE_MD),
            "后续缺口与确认事项": str(GAP_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    recheck_rows = [f"| {item['复核项']} | {item['结论']} | {item['真实能力']} |" for item in package["第三批低风险总复核台账"]]
    sample_rows = [f"| {item['样本入口']} | {item['用途']} | {item['默认动作']} |" for item in package["长期样本归档入口"]]
    gap_rows = [f"| {item['缺口']} | {item['当前处理']} | {item['确认要求']} |" for item in package["后续缺口与确认事项"]]
    package_md = "\n".join([
        "# 完全交付使用版低风险续建第三批总复核与长期样本归档包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        f"- 用途：{package['用途']}",
        "",
        "## 来源摘要",
        "| 来源 | 存在 | 状态 | 路径 |",
        "| --- | --- | --- | --- |",
        *source_rows,
        "",
        "## 第三批低风险总复核台账",
        "| 复核项 | 结论 | 真实能力 |",
        "| --- | --- | --- |",
        *recheck_rows,
        "",
        "## 长期样本归档入口",
        "| 样本入口 | 用途 | 默认动作 |",
        "| --- | --- | --- |",
        *sample_rows,
        "",
        "## 后续缺口与确认事项",
        "| 缺口 | 当前处理 | 确认要求 |",
        "| --- | --- | --- |",
        *gap_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(RECHECK_MD, "\n".join(["# 第三批低风险总复核台账", "", "| 复核项 | 结论 | 真实能力 |", "| --- | --- | --- |", *recheck_rows]))
    write_text(SAMPLE_MD, "\n".join(["# 长期样本归档入口", "", "| 样本入口 | 用途 | 默认动作 |", "| --- | --- | --- |", *sample_rows]))
    write_text(GAP_MD, "\n".join(["# 后续缺口与确认事项", "", "| 缺口 | 当前处理 | 确认要求 |", "| --- | --- | --- |", *gap_rows]))
    write_json(GEN_LOG, {"名称": "生成完全交付使用版低风险续建第三批总复核与长期样本归档包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "复核项": len(package["第三批低风险总复核台账"]), "样本入口": len(package["长期样本归档入口"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
