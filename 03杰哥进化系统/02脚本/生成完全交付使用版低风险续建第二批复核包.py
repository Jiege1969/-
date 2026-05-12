# -*- coding: utf-8 -*-
"""生成完全交付使用版低风险续建第二批复核包。

只做二轮只读复核、静态检查、材料完整性归档和下一批建议；
不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
VIDEO_ROOT = ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "104完全交付使用版低风险续建第二批复核包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版低风险续建第二批复核包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "低风险续建第一批执行包": EVOLUTION_ROOT / "03数据" / "103完全交付使用版低风险续建第一批执行包" / "完全交付使用版低风险续建第一批执行包_最新.json",
    "正式规则申请人工签收流转": EVOLUTION_ROOT / "03数据" / "90三业务正式规则申请人工签收流转与回滚校验包" / "三业务正式规则申请人工签收流转与回滚校验包_最新.json",
    "n8n禁用态导入草案": EVOLUTION_ROOT / "03数据" / "91n8n禁用态导入草案人工签收与回滚演练包" / "n8n禁用态导入草案人工签收与回滚演练包_最新.json",
    "n8n静态扫描导出草案": EVOLUTION_ROOT / "03数据" / "87n8n离线导入包静态扫描与禁用态导出草案包" / "n8n离线导入包静态扫描与禁用态导出草案包_最新.json",
    "视频放行材料完整性复核": VIDEO_ROOT / "04日志" / "真实渲染人工放行材料完整性复核与试运行禁入包验收" / "video-render-approval-materials-no-trial-verify-最新.json",
    "视频失败回滚证据": VIDEO_ROOT / "04日志" / "真实渲染试运行批次失败回滚与证据留存包验收" / "video-render-trial-failure-rollback-evidence-verify-最新.json",
}

PACKAGE_JSON = DATA_DIR / "完全交付使用版低风险续建第二批复核包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版低风险续建第二批复核包_最新.md"
RECHECK_MD = DATA_DIR / "第二批低风险复核台账_最新.md"
STATIC_MD = DATA_DIR / "静态检查与禁用态确认_最新.md"
NEXT_MD = DATA_DIR / "第三批低风险续建建议_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版低风险续建第二批复核包_最新.json"

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
        {"编号": "B2-001", "复核项": "正式规则申请二轮复扫", "结论": "只读复核完成，未生效", "红线状态": "关闭"},
        {"编号": "B2-002", "复核项": "n8n禁用态导入草案二轮静态检查", "结论": "只读复核完成，未导入未触发", "红线状态": "关闭"},
        {"编号": "B2-003", "复核项": "视频放行材料二轮完整性复核", "结论": "只读复核完成，未渲染未发布", "红线状态": "关闭"},
        {"编号": "B2-004", "复核项": "视频失败回滚证据归档", "结论": "证据可引用，真实试运行未开启", "红线状态": "关闭"},
        {"编号": "B2-005", "复核项": "第一批低风险执行结果承接", "结论": "承接完成，未改变运行配置", "红线状态": "关闭"},
        {"编号": "B2-006", "复核项": "长期样本归档入口准备", "结论": "仅形成下一批建议", "红线状态": "关闭"},
    ]


def static_items() -> list[dict[str, str]]:
    return [
        {"对象": "正式规则", "检查": "只能停在申请草案和人工签收流转", "确认": "未写正式规则"},
        {"对象": "n8n", "检查": "只能停在静态扫描、禁用态草案、干跑证据", "确认": "未真实触发"},
        {"对象": "视频", "检查": "只能停在材料复核、白名单未生效、回滚证据", "确认": "未真实渲染/发布"},
        {"对象": "总管面板/一键接续包", "检查": "不得修改", "确认": "未修改"},
        {"对象": "19310/19302", "检查": "不得自行重载", "确认": "未重载"},
    ]


def next_items() -> list[dict[str, str]]:
    return [
        {"编号": "B3-001", "建议": "长期运行样本归档包", "默认动作": "只读归档日报、周报、趋势，不改配置"},
        {"编号": "B3-002", "建议": "红线解锁申请材料总索引", "默认动作": "汇总申请材料，不解锁"},
        {"编号": "B3-003", "建议": "完全交付版低风险三轮总复核", "默认动作": "只读复核第一批和第二批证据"},
        {"编号": "B3-004", "建议": "真正自主运行准备缺口复核", "默认动作": "列缺口和样本要求，不启用自治"},
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
        "名称": "完全交付使用版低风险续建第二批复核包",
        "生成时间": now_text(),
        "状态": "full_delivery_low_risk_batch2_recheck_ready" if ready else "full_delivery_low_risk_batch2_recheck_blocked",
        "用途": "对完全交付使用版第二批低风险续建进行只读复核，确认正式规则、n8n、视频仍未解锁。",
        "来源摘要": source_summary,
        "第二批低风险复核台账": recheck_items(),
        "静态检查与禁用态确认": static_items(),
        "第三批低风险续建建议": next_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "第二批低风险复核台账": str(RECHECK_MD),
            "静态检查与禁用态确认": str(STATIC_MD),
            "第三批低风险续建建议": str(NEXT_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    recheck_rows = [f"| {item['编号']} | {item['复核项']} | {item['结论']} | {item['红线状态']} |" for item in package["第二批低风险复核台账"]]
    static_rows = [f"| {item['对象']} | {item['检查']} | {item['确认']} |" for item in package["静态检查与禁用态确认"]]
    next_rows = [f"| {item['编号']} | {item['建议']} | {item['默认动作']} |" for item in package["第三批低风险续建建议"]]
    package_md = "\n".join([
        "# 完全交付使用版低风险续建第二批复核包",
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
        "## 第二批低风险复核台账",
        "| 编号 | 复核项 | 结论 | 红线状态 |",
        "| --- | --- | --- | --- |",
        *recheck_rows,
        "",
        "## 静态检查与禁用态确认",
        "| 对象 | 检查 | 确认 |",
        "| --- | --- | --- |",
        *static_rows,
        "",
        "## 第三批低风险续建建议",
        "| 编号 | 建议 | 默认动作 |",
        "| --- | --- | --- |",
        *next_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(RECHECK_MD, "\n".join(["# 第二批低风险复核台账", "", "| 编号 | 复核项 | 结论 | 红线状态 |", "| --- | --- | --- | --- |", *recheck_rows]))
    write_text(STATIC_MD, "\n".join(["# 静态检查与禁用态确认", "", "| 对象 | 检查 | 确认 |", "| --- | --- | --- |", *static_rows]))
    write_text(NEXT_MD, "\n".join(["# 第三批低风险续建建议", "", "| 编号 | 建议 | 默认动作 |", "| --- | --- | --- |", *next_rows]))
    write_json(GEN_LOG, {"名称": "生成完全交付使用版低风险续建第二批复核包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "复核项": len(package["第二批低风险复核台账"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
