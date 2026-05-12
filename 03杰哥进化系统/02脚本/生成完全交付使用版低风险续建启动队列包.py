# -*- coding: utf-8 -*-
"""生成完全交付使用版低风险续建启动队列包。

只启动离线、候选、只读、预演类施工队列；外部真实能力继续保持红线关闭。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
VIDEO_ROOT = ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "102完全交付使用版低风险续建启动队列包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "完全交付使用版低风险续建启动队列包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "双版本最终总回传与继续施工分界": EVOLUTION_ROOT / "03数据" / "101双版本最终总回传与继续施工分界包" / "双版本最终总回传与继续施工分界包_最新.json",
    "完全交付缺口拆解与红线解锁路线图": EVOLUTION_ROOT / "03数据" / "64完全交付使用版缺口拆解与红线解锁路线图包" / "完全交付使用版缺口拆解与红线解锁路线图包_最新.json",
    "完全交付低风险可推进拆单": EVOLUTION_ROOT / "03数据" / "68完全交付使用版低风险可推进拆单包" / "完全交付使用版低风险可推进拆单包_最新.json",
    "完全交付低风险模板落地": EVOLUTION_ROOT / "03数据" / "72完全交付低风险模板落地包" / "完全交付低风险模板落地包_最新.json",
    "正式规则人工签收流转与回滚校验": EVOLUTION_ROOT / "03数据" / "90三业务正式规则申请人工签收流转与回滚校验包" / "三业务正式规则申请人工签收流转与回滚校验包_最新.json",
    "n8n禁用态导入草案人工签收与回滚演练": EVOLUTION_ROOT / "03数据" / "91n8n禁用态导入草案人工签收与回滚演练包" / "n8n禁用态导入草案人工签收与回滚演练包_最新.json",
    "视频真实渲染白名单未生效闸口验收": VIDEO_ROOT / "04日志" / "真实渲染试运行批次预检与白名单未生效闸口包验收" / "video-render-trial-batch-precheck-whitelist-inactive-verify-最新.json",
    "视频真实渲染失败回滚证据验收": VIDEO_ROOT / "04日志" / "真实渲染试运行批次失败回滚与证据留存包验收" / "video-render-trial-failure-rollback-evidence-verify-最新.json",
}

PACKAGE_JSON = DATA_DIR / "完全交付使用版低风险续建启动队列包_最新.json"
PACKAGE_MD = DATA_DIR / "完全交付使用版低风险续建启动队列包_最新.md"
QUEUE_MD = DATA_DIR / "低风险续建启动队列_最新.md"
GATE_MD = DATA_DIR / "红线解锁申请队列_最新.md"
VERIFY_MD = DATA_DIR / "续建验收与回滚要求_最新.md"
GEN_LOG = LOG_DIR / "生成完全交付使用版低风险续建启动队列包_最新.json"

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


def queue_items() -> list[dict[str, str]]:
    return [
        {"编号": "FULL-LOW-001", "施工项": "完全交付低风险模板补齐", "默认动作": "补模板、索引、只读验收", "可直接执行": "是"},
        {"编号": "FULL-LOW-002", "施工项": "反馈候选复跑去重", "默认动作": "本地入账、候选去重、拒收清单", "可直接执行": "是"},
        {"编号": "FULL-LOW-003", "施工项": "正式规则申请材料完善", "默认动作": "申请草案、冲突扫描、签收流转", "可直接执行": "是"},
        {"编号": "FULL-LOW-004", "施工项": "n8n离线蓝图与禁用态导入草案", "默认动作": "离线干跑、凭据隔离、禁用态导出", "可直接执行": "是"},
        {"编号": "FULL-LOW-005", "施工项": "视频真实渲染放行材料补齐", "默认动作": "环境识别、白名单未生效检查、回滚证据", "可直接执行": "是"},
        {"编号": "FULL-LOW-006", "施工项": "长期运行样本与趋势记录", "默认动作": "只读巡检、日报、周报、趋势样本", "可直接执行": "是"},
    ]


def gate_items() -> list[dict[str, str]]:
    return [
        {"红线": "企业微信真实发送", "当前状态": "关闭", "解锁要求": "总管确认、目标对象、回滚和审计"},
        {"红线": "n8n真实触发", "当前状态": "关闭", "解锁要求": "总管确认、凭据隔离、禁用态回滚演练通过"},
        {"红线": "正式规则生效", "当前状态": "关闭", "解锁要求": "总管确认、冲突扫描、人工签收、回滚方案"},
        {"红线": "视频真实渲染/发布", "当前状态": "关闭", "解锁要求": "总管确认、白名单生效、预检、回滚证据"},
        {"红线": "券商/交易", "当前状态": "关闭", "解锁要求": "长期不启用，未来另立高风险项目"},
        {"红线": "税局/财税软件", "当前状态": "关闭", "解锁要求": "长期不启用，未来另立高风险项目"},
        {"红线": "19310/19302重载", "当前状态": "需确认", "解锁要求": "先登记、记录 PID、只操作确认端口"},
    ]


def verify_items() -> list[dict[str, str]]:
    return [
        {"要求": "每个续建项必须有生成脚本和只读验收", "回滚": "删除候选产物或标记废弃，不影响已封存双版本"},
        {"要求": "新增验收纳入自主巡检快照", "回滚": "从快照源移除对应验收项"},
        {"要求": "红线项只能生成申请材料", "回滚": "确认材料作废，不改变运行配置"},
        {"要求": "n8n只能离线干跑", "回滚": "禁用态导出草案作废"},
        {"要求": "视频只能放行前检查", "回滚": "保持 blocked 并保留证据"},
        {"要求": "正式规则只停在申请草案", "回滚": "申请草案撤回，不写正式规则"},
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
        "名称": "完全交付使用版低风险续建启动队列包",
        "生成时间": now_text(),
        "状态": "full_delivery_low_risk_continue_queue_ready" if ready else "full_delivery_low_risk_continue_queue_blocked",
        "用途": "在日常版和稳定版已封存后，启动完全交付使用版的低风险续建队列，同时列出必须确认的红线解锁申请队列。",
        "来源摘要": source_summary,
        "低风险续建启动队列": queue_items(),
        "红线解锁申请队列": gate_items(),
        "续建验收与回滚要求": verify_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "低风险续建启动队列": str(QUEUE_MD),
            "红线解锁申请队列": str(GATE_MD),
            "续建验收与回滚要求": str(VERIFY_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    queue_rows = [f"| {item['编号']} | {item['施工项']} | {item['默认动作']} | {item['可直接执行']} |" for item in package["低风险续建启动队列"]]
    gate_rows = [f"| {item['红线']} | {item['当前状态']} | {item['解锁要求']} |" for item in package["红线解锁申请队列"]]
    verify_rows = [f"| {item['要求']} | {item['回滚']} |" for item in package["续建验收与回滚要求"]]
    package_md = "\n".join([
        "# 完全交付使用版低风险续建启动队列包",
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
        "## 低风险续建启动队列",
        "| 编号 | 施工项 | 默认动作 | 可直接执行 |",
        "| --- | --- | --- | --- |",
        *queue_rows,
        "",
        "## 红线解锁申请队列",
        "| 红线 | 当前状态 | 解锁要求 |",
        "| --- | --- | --- |",
        *gate_rows,
        "",
        "## 续建验收与回滚要求",
        "| 要求 | 回滚 |",
        "| --- | --- |",
        *verify_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(QUEUE_MD, "\n".join(["# 低风险续建启动队列", "", "| 编号 | 施工项 | 默认动作 | 可直接执行 |", "| --- | --- | --- | --- |", *queue_rows]))
    write_text(GATE_MD, "\n".join(["# 红线解锁申请队列", "", "| 红线 | 当前状态 | 解锁要求 |", "| --- | --- | --- |", *gate_rows]))
    write_text(VERIFY_MD, "\n".join(["# 续建验收与回滚要求", "", "| 要求 | 回滚 |", "| --- | --- |", *verify_rows]))
    write_json(GEN_LOG, {"名称": "生成完全交付使用版低风险续建启动队列包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "低风险项": len(package["低风险续建启动队列"]), "红线项": len(package["红线解锁申请队列"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
