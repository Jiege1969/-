# -*- coding: utf-8 -*-
"""生成完全交付使用版红线解锁申请材料总索引包。

只汇总红线解锁所需申请材料、验收证据和确认条件；
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
DATA_DIR = EVOLUTION_ROOT / "03数据" / "106完全交付使用版红线解锁申请材料总索引包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版红线解锁申请材料总索引包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "低风险续建第三批总复核": EVOLUTION_ROOT / "03数据" / "105完全交付使用版低风险续建第三批总复核与长期样本归档包" / "完全交付使用版低风险续建第三批总复核与长期样本归档包_最新.json",
    "正式规则人工签收流转": EVOLUTION_ROOT / "03数据" / "90三业务正式规则申请人工签收流转与回滚校验包" / "三业务正式规则申请人工签收流转与回滚校验包_最新.json",
    "正式规则冲突扫描台账": EVOLUTION_ROOT / "03数据" / "86三业务正式规则申请草案冲突扫描与签收台账包" / "三业务正式规则申请草案冲突扫描与签收台账包_最新.json",
    "n8n禁用态导入草案": EVOLUTION_ROOT / "03数据" / "91n8n禁用态导入草案人工签收与回滚演练包" / "n8n禁用态导入草案人工签收与回滚演练包_最新.json",
    "n8n凭据隔离与启用禁入": EVOLUTION_ROOT / "03数据" / "84n8n离线导入前凭据隔离与启用禁入包" / "n8n离线导入前凭据隔离与启用禁入包_最新.json",
    "视频放行材料完整性复核": VIDEO_ROOT / "04日志" / "真实渲染人工放行材料完整性复核与试运行禁入包验收" / "video-render-approval-materials-no-trial-verify-最新.json",
    "视频白名单未生效闸口": VIDEO_ROOT / "04日志" / "真实渲染试运行批次预检与白名单未生效闸口包验收" / "video-render-trial-batch-precheck-whitelist-inactive-verify-最新.json",
}

PACKAGE_JSON = DATA_DIR / "完全交付使用版红线解锁申请材料总索引包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版红线解锁申请材料总索引包_最新.md"
INDEX_MD = DATA_DIR / "红线解锁申请材料总索引_最新.md"
CONFIRM_MD = DATA_DIR / "总管确认条件清单_最新.md"
REJECT_MD = DATA_DIR / "未确认前禁止动作清单_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版红线解锁申请材料总索引包_最新.json"

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


def index_items() -> list[dict[str, str]]:
    return [
        {"红线": "正式规则生效", "材料": "人工签收流转、冲突扫描台账、回滚校验", "当前状态": "仅申请材料"},
        {"红线": "n8n真实触发", "材料": "禁用态导入草案、凭据隔离、启用禁入、干跑证据", "当前状态": "仅离线材料"},
        {"红线": "视频真实渲染", "材料": "放行材料完整性复核、白名单未生效闸口、失败回滚证据", "当前状态": "仅放行前材料"},
        {"红线": "企业微信真实发送", "材料": "公共入口巡检、real_send=false 证据、发送对象确认模板", "当前状态": "仅预演"},
        {"红线": "19310/19302重载", "材料": "端口/PID记录、操作范围、回滚记录模板", "当前状态": "仅确认条件"},
        {"红线": "券商/交易", "材料": "高风险另立项说明", "当前状态": "不进入当前解锁"},
        {"红线": "税局/财税软件", "材料": "高风险另立项说明", "当前状态": "不进入当前解锁"},
    ]


def confirm_items() -> list[dict[str, str]]:
    return [
        {"确认项": "明确解锁对象", "要求": "具体到功能、入口、范围、责任人"},
        {"确认项": "明确回滚路径", "要求": "必须可停止、可恢复、可审计"},
        {"确认项": "明确验收样本", "要求": "至少包含成功、失败、拒收样本"},
        {"确认项": "明确外部影响", "要求": "说明是否会发消息、触发流程、生成文件、改变配置"},
        {"确认项": "明确单次授权边界", "要求": "不得一次授权扩展到所有红线"},
        {"确认项": "明确服务重载窗口", "要求": "涉及 19310/19302 时必须先登记再操作"},
    ]


def reject_items() -> list[dict[str, str]]:
    return [
        {"未确认前禁止": "真实发送企业微信", "原因": "会影响联系人或群"},
        {"未确认前禁止": "真实触发n8n", "原因": "会连锁执行自动化流程"},
        {"未确认前禁止": "写入正式规则", "原因": "会改变全局行为"},
        {"未确认前禁止": "真实渲染/发布视频", "原因": "会生成或发布真实内容"},
        {"未确认前禁止": "连接券商/交易", "原因": "高风险金融动作"},
        {"未确认前禁止": "登录税局/接财税软件", "原因": "高风险真实业务数据"},
        {"未确认前禁止": "自行重载19310/19302", "原因": "会影响运行入口"},
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
        "名称": "完全交付使用版红线解锁申请材料总索引包",
        "生成时间": now_text(),
        "状态": "full_delivery_redline_unlock_material_index_ready" if ready else "full_delivery_redline_unlock_material_index_blocked",
        "用途": "汇总完全交付使用版后续红线解锁申请材料和总管确认条件；不代表解锁。",
        "来源摘要": source_summary,
        "红线解锁申请材料总索引": index_items(),
        "总管确认条件清单": confirm_items(),
        "未确认前禁止动作清单": reject_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "红线解锁申请材料总索引": str(INDEX_MD),
            "总管确认条件清单": str(CONFIRM_MD),
            "未确认前禁止动作清单": str(REJECT_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    index_rows = [f"| {item['红线']} | {item['材料']} | {item['当前状态']} |" for item in package["红线解锁申请材料总索引"]]
    confirm_rows = [f"| {item['确认项']} | {item['要求']} |" for item in package["总管确认条件清单"]]
    reject_rows = [f"| {item['未确认前禁止']} | {item['原因']} |" for item in package["未确认前禁止动作清单"]]
    package_md = "\n".join([
        "# 完全交付使用版红线解锁申请材料总索引包",
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
        "## 红线解锁申请材料总索引",
        "| 红线 | 材料 | 当前状态 |",
        "| --- | --- | --- |",
        *index_rows,
        "",
        "## 总管确认条件清单",
        "| 确认项 | 要求 |",
        "| --- | --- |",
        *confirm_rows,
        "",
        "## 未确认前禁止动作清单",
        "| 未确认前禁止 | 原因 |",
        "| --- | --- |",
        *reject_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(INDEX_MD, "\n".join(["# 红线解锁申请材料总索引", "", "| 红线 | 材料 | 当前状态 |", "| --- | --- | --- |", *index_rows]))
    write_text(CONFIRM_MD, "\n".join(["# 总管确认条件清单", "", "| 确认项 | 要求 |", "| --- | --- |", *confirm_rows]))
    write_text(REJECT_MD, "\n".join(["# 未确认前禁止动作清单", "", "| 未确认前禁止 | 原因 |", "| --- | --- |", *reject_rows]))
    write_json(GEN_LOG, {"名称": "生成完全交付使用版红线解锁申请材料总索引包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "红线项": len(package["红线解锁申请材料总索引"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
