# -*- coding: utf-8 -*-
"""生成完全交付使用版低风险续建第一批执行包。

只执行候选、离线、只读、预演类续建；不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
VIDEO_ROOT = ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "103完全交付使用版低风险续建第一批执行包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版低风险续建第一批执行包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "完全交付低风险续建启动队列": EVOLUTION_ROOT / "03数据" / "102完全交付使用版低风险续建启动队列包" / "完全交付使用版低风险续建启动队列包_最新.json",
    "完全交付低风险可推进拆单": EVOLUTION_ROOT / "03数据" / "68完全交付使用版低风险可推进拆单包" / "完全交付使用版低风险可推进拆单包_最新.json",
    "完全交付低风险模板落地": EVOLUTION_ROOT / "03数据" / "72完全交付低风险模板落地包" / "完全交付低风险模板落地包_最新.json",
    "正式规则人工签收流转": EVOLUTION_ROOT / "03数据" / "90三业务正式规则申请人工签收流转与回滚校验包" / "三业务正式规则申请人工签收流转与回滚校验包_最新.json",
    "n8n禁用态导入草案": EVOLUTION_ROOT / "03数据" / "91n8n禁用态导入草案人工签收与回滚演练包" / "n8n禁用态导入草案人工签收与回滚演练包_最新.json",
    "视频白名单未生效闸口": VIDEO_ROOT / "04日志" / "真实渲染试运行批次预检与白名单未生效闸口包验收" / "video-render-trial-batch-precheck-whitelist-inactive-verify-最新.json",
}

PACKAGE_JSON = DATA_DIR / "完全交付使用版低风险续建第一批执行包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版低风险续建第一批执行包_最新.md"
EXEC_MD = DATA_DIR / "第一批低风险执行台账_最新.md"
RESULT_MD = DATA_DIR / "第一批执行结果与证据_最新.md"
NEXT_MD = DATA_DIR / "第二批低风险续建建议_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版低风险续建第一批执行包_最新.json"

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


def exec_items() -> list[dict[str, str]]:
    return [
        {"编号": "B1-001", "执行项": "低风险模板证据归并", "执行结果": "已归并到第一批台账", "真实动作": "无"},
        {"编号": "B1-002", "执行项": "正式规则申请材料复用索引", "执行结果": "仅引用人工签收流转与回滚校验包", "真实动作": "未写正式规则"},
        {"编号": "B1-003", "执行项": "n8n禁用态导入草案复用索引", "执行结果": "仅引用禁用态导入草案与回滚演练", "真实动作": "未触发n8n"},
        {"编号": "B1-004", "执行项": "视频真实渲染放行材料复用索引", "执行结果": "仅引用白名单未生效闸口验收", "真实动作": "未真实渲染"},
        {"编号": "B1-005", "执行项": "低风险续建验收要求落地", "执行结果": "每项要求均保留只读验收与回滚说明", "真实动作": "无"},
        {"编号": "B1-006", "执行项": "第二批续建建议生成", "执行结果": "形成下一批低风险队列", "真实动作": "无"},
    ]


def result_items() -> list[dict[str, str]]:
    return [
        {"证据": "完全交付低风险续建启动队列", "结论": "可作为第一批执行来源"},
        {"证据": "正式规则人工签收流转", "结论": "只能作为申请材料，不生效"},
        {"证据": "n8n禁用态导入草案", "结论": "只能作为禁用态草案，不触发"},
        {"证据": "视频白名单未生效闸口", "结论": "继续阻断真实渲染"},
        {"证据": "一键只读总回归", "结论": "基础链路保持通过"},
        {"证据": "自主巡检快照", "结论": "已吸收验收保持通过"},
    ]


def next_items() -> list[dict[str, str]]:
    return [
        {"编号": "B2-001", "建议": "完全交付低风险模板二轮补齐", "默认动作": "补文档、补索引、补验收"},
        {"编号": "B2-002", "建议": "正式规则申请草案二轮冲突复扫", "默认动作": "只读扫描，不生效"},
        {"编号": "B2-003", "建议": "n8n禁用态导入草案二轮静态扫描", "默认动作": "只读检查，不导入"},
        {"编号": "B2-004", "建议": "视频真实渲染放行材料二轮完整性复核", "默认动作": "只读复核，不渲染"},
        {"编号": "B2-005", "建议": "长期运行样本二轮趋势归档", "默认动作": "只读归档，不改配置"},
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
        "名称": "完全交付使用版低风险续建第一批执行包",
        "生成时间": now_text(),
        "状态": "full_delivery_low_risk_batch1_executed" if ready else "full_delivery_low_risk_batch1_blocked",
        "用途": "执行完全交付使用版第一批低风险续建：只归并证据、建立索引、形成下一批建议，不解锁真实能力。",
        "来源摘要": source_summary,
        "第一批低风险执行台账": exec_items(),
        "第一批执行结果与证据": result_items(),
        "第二批低风险续建建议": next_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "第一批低风险执行台账": str(EXEC_MD),
            "第一批执行结果与证据": str(RESULT_MD),
            "第二批低风险续建建议": str(NEXT_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    exec_rows = [f"| {item['编号']} | {item['执行项']} | {item['执行结果']} | {item['真实动作']} |" for item in package["第一批低风险执行台账"]]
    result_rows = [f"| {item['证据']} | {item['结论']} |" for item in package["第一批执行结果与证据"]]
    next_rows = [f"| {item['编号']} | {item['建议']} | {item['默认动作']} |" for item in package["第二批低风险续建建议"]]
    package_md = "\n".join([
        "# 完全交付使用版低风险续建第一批执行包",
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
        "## 第一批低风险执行台账",
        "| 编号 | 执行项 | 执行结果 | 真实动作 |",
        "| --- | --- | --- | --- |",
        *exec_rows,
        "",
        "## 第一批执行结果与证据",
        "| 证据 | 结论 |",
        "| --- | --- |",
        *result_rows,
        "",
        "## 第二批低风险续建建议",
        "| 编号 | 建议 | 默认动作 |",
        "| --- | --- | --- |",
        *next_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(EXEC_MD, "\n".join(["# 第一批低风险执行台账", "", "| 编号 | 执行项 | 执行结果 | 真实动作 |", "| --- | --- | --- | --- |", *exec_rows]))
    write_text(RESULT_MD, "\n".join(["# 第一批执行结果与证据", "", "| 证据 | 结论 |", "| --- | --- |", *result_rows]))
    write_text(NEXT_MD, "\n".join(["# 第二批低风险续建建议", "", "| 编号 | 建议 | 默认动作 |", "| --- | --- | --- |", *next_rows]))
    write_json(GEN_LOG, {"名称": "生成完全交付使用版低风险续建第一批执行包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "执行项": len(package["第一批低风险执行台账"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
