# -*- coding: utf-8 -*-
"""生成完全交付使用版红线材料一致性复核与缺口补齐包。

只复核申请材料一致性、缺口补齐队列和禁止动作；
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
DATA_DIR = EVOLUTION_ROOT / "03数据" / "107完全交付使用版红线材料一致性复核与缺口补齐包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版红线材料一致性复核与缺口补齐包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "红线解锁申请材料总索引": EVOLUTION_ROOT / "03数据" / "106完全交付使用版红线解锁申请材料总索引包" / "完全交付使用版红线解锁申请材料总索引包_最新.json",
    "低风险第三批长期样本归档": EVOLUTION_ROOT / "03数据" / "105完全交付使用版低风险续建第三批总复核与长期样本归档包" / "完全交付使用版低风险续建第三批总复核与长期样本归档包_最新.json",
    "正式规则人工签收流转": EVOLUTION_ROOT / "03数据" / "90三业务正式规则申请人工签收流转与回滚校验包" / "三业务正式规则申请人工签收流转与回滚校验包_最新.json",
    "正式规则冲突扫描台账": EVOLUTION_ROOT / "03数据" / "86三业务正式规则申请草案冲突扫描与签收台账包" / "三业务正式规则申请草案冲突扫描与签收台账包_最新.json",
    "n8n禁用态导入草案": EVOLUTION_ROOT / "03数据" / "91n8n禁用态导入草案人工签收与回滚演练包" / "n8n禁用态导入草案人工签收与回滚演练包_最新.json",
    "视频放行材料完整性复核": VIDEO_ROOT / "04日志" / "真实渲染人工放行材料完整性复核与试运行禁入包验收" / "video-render-approval-materials-no-trial-verify-最新.json",
}

PACKAGE_JSON = DATA_DIR / "完全交付使用版红线材料一致性复核与缺口补齐包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版红线材料一致性复核与缺口补齐包_最新.md"
CHECK_MD = DATA_DIR / "红线材料一致性复核表_最新.md"
GAP_MD = DATA_DIR / "材料缺口补齐队列_最新.md"
GUARD_MD = DATA_DIR / "未确认前守护口径_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版红线材料一致性复核与缺口补齐包_最新.json"

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


def check_items() -> list[dict[str, str]]:
    return [
        {"对象": "正式规则", "一致性结论": "材料齐到申请层，未写正式规则", "当前动作": "继续补签收证据"},
        {"对象": "n8n", "一致性结论": "材料齐到禁用态草案层，未导入未触发", "当前动作": "继续补静态扫描证据"},
        {"对象": "视频真实渲染", "一致性结论": "材料齐到放行前复核层，未渲染未发布", "当前动作": "继续补白名单和回滚证据"},
        {"对象": "企业微信真实发送", "一致性结论": "材料停在预演和确认条件层，未真实发送", "当前动作": "继续补对象确认模板"},
        {"对象": "19310/19302重载", "一致性结论": "材料停在确认登记层，未自行重载", "当前动作": "继续补操作窗口模板"},
        {"对象": "券商/税局/财税软件", "一致性结论": "材料为高风险另立项说明，不进入当前解锁", "当前动作": "继续保持禁用"},
    ]


def gap_items() -> list[dict[str, str]]:
    return [
        {"缺口": "企业微信发送对象确认模板", "补齐方式": "仅生成模板，不发送", "优先级": "中"},
        {"缺口": "服务重载操作窗口模板", "补齐方式": "仅生成登记模板，不重载", "优先级": "中"},
        {"缺口": "n8n禁用态静态扫描二轮摘要", "补齐方式": "只读扫描，不导入", "优先级": "中"},
        {"缺口": "视频白名单生效前拒收口径", "补齐方式": "只读材料，不渲染", "优先级": "中"},
        {"缺口": "正式规则申请人工签收补充页", "补齐方式": "只生成申请补充页，不生效", "优先级": "中"},
    ]


def guard_items() -> list[dict[str, str]]:
    return [
        {"守护口径": "申请材料不等于授权", "说明": "任何索引、模板、草案都不代表红线已解锁"},
        {"守护口径": "只读验收不等于真实执行", "说明": "验收通过只表示材料完整，不代表可触发外部系统"},
        {"守护口径": "单项确认不扩展", "说明": "即使未来确认某一项，也不得扩展到其他红线"},
        {"守护口径": "失败优先回滚", "说明": "任何异常先停用、入账、回滚，不继续扩大动作"},
        {"守护口径": "已封存双版本不被改写", "说明": "日常版和稳定版封存结论不随红线材料变化而变化"},
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
        "名称": "完全交付使用版红线材料一致性复核与缺口补齐包",
        "生成时间": now_text(),
        "状态": "full_delivery_redline_material_consistency_ready" if ready else "full_delivery_redline_material_consistency_blocked",
        "用途": "复核红线解锁申请材料的一致性，并生成未确认前可补齐的低风险材料队列。",
        "来源摘要": source_summary,
        "红线材料一致性复核表": check_items(),
        "材料缺口补齐队列": gap_items(),
        "未确认前守护口径": guard_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "红线材料一致性复核表": str(CHECK_MD),
            "材料缺口补齐队列": str(GAP_MD),
            "未确认前守护口径": str(GUARD_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    check_rows = [f"| {item['对象']} | {item['一致性结论']} | {item['当前动作']} |" for item in package["红线材料一致性复核表"]]
    gap_rows = [f"| {item['缺口']} | {item['补齐方式']} | {item['优先级']} |" for item in package["材料缺口补齐队列"]]
    guard_rows = [f"| {item['守护口径']} | {item['说明']} |" for item in package["未确认前守护口径"]]
    package_md = "\n".join([
        "# 完全交付使用版红线材料一致性复核与缺口补齐包",
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
        "## 红线材料一致性复核表",
        "| 对象 | 一致性结论 | 当前动作 |",
        "| --- | --- | --- |",
        *check_rows,
        "",
        "## 材料缺口补齐队列",
        "| 缺口 | 补齐方式 | 优先级 |",
        "| --- | --- | --- |",
        *gap_rows,
        "",
        "## 未确认前守护口径",
        "| 守护口径 | 说明 |",
        "| --- | --- |",
        *guard_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(CHECK_MD, "\n".join(["# 红线材料一致性复核表", "", "| 对象 | 一致性结论 | 当前动作 |", "| --- | --- | --- |", *check_rows]))
    write_text(GAP_MD, "\n".join(["# 材料缺口补齐队列", "", "| 缺口 | 补齐方式 | 优先级 |", "| --- | --- | --- |", *gap_rows]))
    write_text(GUARD_MD, "\n".join(["# 未确认前守护口径", "", "| 守护口径 | 说明 |", "| --- | --- |", *guard_rows]))
    write_json(GEN_LOG, {"名称": "生成完全交付使用版红线材料一致性复核与缺口补齐包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "复核对象": len(package["红线材料一致性复核表"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
