# -*- coding: utf-8 -*-
"""生成日常可用版与稳定交付版最终签收启动包。

只汇总既有验收证据和使用启动材料，给出可签收、可试运行、需确认事项；
不触发外部系统、不重载服务、不写正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "94日常稳定交付最终签收启动包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "日常稳定交付最终签收启动包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "最终日常可用交付候选": EVOLUTION_ROOT / "04日志" / "最终日常可用交付候选回传验收" / "final-daily-usable-delivery-candidate-verify-最新.json",
    "日常稳定交付使用接管与续建总包": EVOLUTION_ROOT / "03数据" / "93日常稳定交付使用接管与续建总包" / "日常稳定交付使用接管与续建总包_最新.json",
    "使用者入口导航与常用指令": EVOLUTION_ROOT / "03数据" / "88使用者入口导航与常用指令包" / "使用者入口导航与常用指令包_最新.json",
    "稳定版使用者一页操作卡": EVOLUTION_ROOT / "03数据" / "89稳定版使用者一页操作卡与灯号说明包" / "稳定版使用者一页操作卡与灯号说明包_最新.json",
    "首周试用结果签收复核": EVOLUTION_ROOT / "03数据" / "91首周试用结果汇总与签收复核包" / "首周试用结果汇总与签收复核包_最新.json",
    "运行期故障恢复与回滚总索引": EVOLUTION_ROOT / "03数据" / "87运行期故障恢复与回滚总索引包" / "运行期故障恢复与回滚总索引包_最新.json",
    "运行期证据归档与版本冻结候选": EVOLUTION_ROOT / "03数据" / "86运行期证据归档与版本冻结候选包" / "运行期证据归档与版本冻结候选包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "日常稳定交付最终签收启动包_最新.json"
PACKAGE_MD = DATA_DIR / "日常稳定交付最终签收启动包_最新.md"
SIGNOFF_MD = DATA_DIR / "最终签收建议_最新.md"
START_MD = DATA_DIR / "试运行启动步骤_最新.md"
CONFIRM_MD = DATA_DIR / "需总管确认后才能解锁事项_最新.md"
GEN_LOG = LOG_DIR / "生成日常稳定交付最终签收启动包_最新.json"

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


def signoff_items() -> list[dict[str, Any]]:
    return [
        {"版本": "日常可用交付版", "签收建议": "建议签收", "理由": "公共入口、职责分流、税收、股票展示、视频阻断和一键只读回归持续通过"},
        {"版本": "稳定交付版", "签收建议": "建议进入试运行签收", "理由": "接管清单、操作卡、反馈入账、运行指挥台和回滚索引已闭环"},
        {"版本": "完全交付使用版", "签收建议": "暂不签收", "理由": "真实外部动作和正式规则仍保持红线关闭"},
        {"版本": "真正自主运行版", "签收建议": "暂不签收", "理由": "n8n、真实发送、正式规则、真实渲染/发布等仍需长期验证和人工确认"},
    ]


def start_steps() -> list[dict[str, Any]]:
    return [
        {"顺序": 1, "步骤": "查看使用者入口导航与常用指令", "预期": "明确从系统管家、工作秘书、视频助理等入口发起任务"},
        {"顺序": 2, "步骤": "执行一键只读总回归", "预期": "11项全部通过，确认日常入口可用"},
        {"顺序": 3, "步骤": "查看自主巡检快照", "预期": "全部已吸收验收项为 pass"},
        {"顺序": 4, "步骤": "按稳定版一页操作卡处理灯号", "预期": "绿色继续使用，黄色登记复核，红色停在总管确认"},
        {"顺序": 5, "步骤": "试运行问题进入本地入账执行器", "预期": "只形成候选台账和拒收清单，不直接改正式规则"},
        {"顺序": 6, "步骤": "每日查看运行日报与次日待办", "预期": "把低风险续建和需确认事项分开处理"},
        {"顺序": 7, "步骤": "遇到红线事项只登记确认", "预期": "不自行真实发送、触发、登录、交易、发布或重载"},
    ]


def confirm_items() -> list[dict[str, Any]]:
    return [
        {"事项": "19310/19302重载", "处理": "先登记为需总管确认"},
        {"事项": "企业微信真实发送", "处理": "确认前只保留本地预演"},
        {"事项": "n8n导入或启用", "处理": "确认前只做离线蓝图、干跑、凭据隔离"},
        {"事项": "正式规则生效", "处理": "确认前只生成候选、申请草案和冲突扫描"},
        {"事项": "券商连接或交易", "处理": "确认前只做研究展示和风险复核"},
        {"事项": "税局或财税软件连接", "处理": "确认前只做待复核草案"},
        {"事项": "视频真实渲染或发布", "处理": "确认前只做环境识别、预检、白名单和回滚预案"},
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
        "名称": "日常稳定交付最终签收启动包",
        "生成时间": now_text(),
        "状态": "daily_stable_final_signoff_start_ready" if ready else "daily_stable_final_signoff_start_blocked",
        "用途": "给日常可用版和稳定交付版形成最终签收建议、试运行启动步骤和需总管确认事项。",
        "来源摘要": source_summary,
        "最终签收建议": signoff_items(),
        "试运行启动步骤": start_steps(),
        "需总管确认后才能解锁事项": confirm_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "最终签收建议": str(SIGNOFF_MD),
            "试运行启动步骤": str(START_MD),
            "需总管确认后才能解锁事项": str(CONFIRM_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    signoff_rows = [f"| {item['版本']} | {item['签收建议']} | {item['理由']} |" for item in package["最终签收建议"]]
    start_rows = [f"| {item['顺序']} | {item['步骤']} | {item['预期']} |" for item in package["试运行启动步骤"]]
    confirm_rows = [f"| {item['事项']} | {item['处理']} |" for item in package["需总管确认后才能解锁事项"]]
    package_md = "\n".join([
        "# 日常稳定交付最终签收启动包",
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
        "## 最终签收建议",
        "| 版本 | 签收建议 | 理由 |",
        "| --- | --- | --- |",
        *signoff_rows,
        "",
        "## 试运行启动步骤",
        "| 顺序 | 步骤 | 预期 |",
        "| --- | --- | --- |",
        *start_rows,
        "",
        "## 需总管确认后才能解锁事项",
        "| 事项 | 处理 |",
        "| --- | --- |",
        *confirm_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(SIGNOFF_MD, "\n".join(["# 最终签收建议", "", "| 版本 | 签收建议 | 理由 |", "| --- | --- | --- |", *signoff_rows]))
    write_text(START_MD, "\n".join(["# 试运行启动步骤", "", "| 顺序 | 步骤 | 预期 |", "| --- | --- | --- |", *start_rows]))
    write_text(CONFIRM_MD, "\n".join(["# 需总管确认后才能解锁事项", "", "| 事项 | 处理 |", "| --- | --- |", *confirm_rows]))
    write_json(GEN_LOG, {"名称": "生成日常稳定交付最终签收启动包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "签收项": len(package["最终签收建议"]), "启动步骤": len(package["试运行启动步骤"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
