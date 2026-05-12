# -*- coding: utf-8 -*-
"""生成红线材料缺口低风险补齐第一批模板包。

只补齐确认模板、登记模板、拒收口径和申请补充页；
不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "108红线材料缺口低风险补齐第一批模板包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "红线材料缺口低风险补齐第一批模板包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "红线材料一致性复核与缺口补齐": EVOLUTION_ROOT / "03数据" / "107完全交付使用版红线材料一致性复核与缺口补齐包" / "完全交付使用版红线材料一致性复核与缺口补齐包_最新.json",
    "红线解锁申请材料总索引": EVOLUTION_ROOT / "03数据" / "106完全交付使用版红线解锁申请材料总索引包" / "完全交付使用版红线解锁申请材料总索引包_最新.json",
    "长期样本归档包": EVOLUTION_ROOT / "03数据" / "105完全交付使用版低风险续建第三批总复核与长期样本归档包" / "完全交付使用版低风险续建第三批总复核与长期样本归档包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "红线材料缺口低风险补齐第一批模板包_最新.json"
PACKAGE_MD = DATA_DIR / "红线材料缺口低风险补齐第一批模板包_最新.md"
WECOM_MD = DATA_DIR / "企业微信发送对象确认模板_最新.md"
RELOAD_MD = DATA_DIR / "服务重载操作窗口登记模板_最新.md"
N8N_MD = DATA_DIR / "n8n禁用态静态扫描二轮摘要模板_最新.md"
VIDEO_MD = DATA_DIR / "视频白名单生效前拒收口径模板_最新.md"
RULE_MD = DATA_DIR / "正式规则申请人工签收补充页模板_最新.md"
GEN_LOG = LOG_DIR / "生成红线材料缺口低风险补齐第一批模板包_最新.json"

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


def template_items() -> list[dict[str, str]]:
    return [
        {"编号": "TPL-001", "模板": "企业微信发送对象确认模板", "用途": "记录对象、范围、消息草案和审计要求", "执行状态": "仅模板"},
        {"编号": "TPL-002", "模板": "服务重载操作窗口登记模板", "用途": "记录端口、PID、窗口、回滚和确认人", "执行状态": "仅模板"},
        {"编号": "TPL-003", "模板": "n8n禁用态静态扫描二轮摘要模板", "用途": "记录离线草案、凭据隔离和禁用态检查", "执行状态": "仅模板"},
        {"编号": "TPL-004", "模板": "视频白名单生效前拒收口径模板", "用途": "记录白名单、预检、回滚和拒收原因", "执行状态": "仅模板"},
        {"编号": "TPL-005", "模板": "正式规则申请人工签收补充页模板", "用途": "记录规则候选、冲突扫描和回滚说明", "执行状态": "仅模板"},
    ]


def guard_items() -> list[dict[str, str]]:
    return [
        {"模板": "企业微信发送对象确认模板", "守护口径": "仅记录对象确认，不发送消息"},
        {"模板": "服务重载操作窗口登记模板", "守护口径": "仅登记窗口，不重载服务"},
        {"模板": "n8n禁用态静态扫描二轮摘要模板", "守护口径": "仅静态扫描，不导入不触发"},
        {"模板": "视频白名单生效前拒收口径模板", "守护口径": "仅拒收说明，不渲染不发布"},
        {"模板": "正式规则申请人工签收补充页模板", "守护口径": "仅申请补充，不写正式规则"},
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
    templates = template_items()
    guards = guard_items()
    package = {
        "名称": "红线材料缺口低风险补齐第一批模板包",
        "生成时间": now_text(),
        "状态": "redline_gap_low_risk_template_batch1_ready" if ready else "redline_gap_low_risk_template_batch1_blocked",
        "用途": "补齐红线材料一致性复核中列出的第一批低风险模板，不代表任何红线解锁。",
        "来源摘要": source_summary,
        "补齐模板清单": templates,
        "模板守护口径": guards,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "企业微信发送对象确认模板": str(WECOM_MD),
            "服务重载操作窗口登记模板": str(RELOAD_MD),
            "n8n禁用态静态扫描二轮摘要模板": str(N8N_MD),
            "视频白名单生效前拒收口径模板": str(VIDEO_MD),
            "正式规则申请人工签收补充页模板": str(RULE_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    template_rows = [f"| {item['编号']} | {item['模板']} | {item['用途']} | {item['执行状态']} |" for item in templates]
    guard_rows = [f"| {item['模板']} | {item['守护口径']} |" for item in guards]
    package_md = "\n".join([
        "# 红线材料缺口低风险补齐第一批模板包",
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
        "## 补齐模板清单",
        "| 编号 | 模板 | 用途 | 执行状态 |",
        "| --- | --- | --- | --- |",
        *template_rows,
        "",
        "## 模板守护口径",
        "| 模板 | 守护口径 |",
        "| --- | --- |",
        *guard_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(WECOM_MD, "\n".join([
        "# 企业微信发送对象确认模板",
        "",
        "- 确认对象：待填写",
        "- 消息草案：待填写",
        "- 单次范围：待填写",
        "- 审计记录：待填写",
        "- 当前口径：仅模板，不发送消息",
    ]))
    write_text(RELOAD_MD, "\n".join([
        "# 服务重载操作窗口登记模板",
        "",
        "- 端口：19310 / 19302 二选一",
        "- 重载前 PID：待填写",
        "- 重载窗口：待填写",
        "- 回滚方式：待填写",
        "- 当前口径：仅模板，不重载服务",
    ]))
    write_text(N8N_MD, "\n".join([
        "# n8n禁用态静态扫描二轮摘要模板",
        "",
        "- 草案来源：待填写",
        "- 凭据隔离：待填写",
        "- 禁用态检查：待填写",
        "- 回滚演练：待填写",
        "- 当前口径：仅静态扫描，不导入不触发",
    ]))
    write_text(VIDEO_MD, "\n".join([
        "# 视频白名单生效前拒收口径模板",
        "",
        "- 任务ID：待填写",
        "- 白名单状态：未生效/待确认",
        "- 预检结果：待填写",
        "- 拒收原因：待填写",
        "- 当前口径：仅拒收说明，不渲染不发布",
    ]))
    write_text(RULE_MD, "\n".join([
        "# 正式规则申请人工签收补充页模板",
        "",
        "- 规则候选：待填写",
        "- 冲突扫描：待填写",
        "- 人工签收：待填写",
        "- 回滚说明：待填写",
        "- 当前口径：仅申请补充，不写正式规则",
    ]))
    write_json(GEN_LOG, {"名称": "生成红线材料缺口低风险补齐第一批模板包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "模板数": len(templates), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
