# -*- coding: utf-8 -*-
"""生成双版本最终总回传与继续施工分界包。

只汇总日常可用版、稳定交付版的已封存结论，并划清完全交付/真正自主运行的继续施工边界；
不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "101双版本最终总回传与继续施工分界包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "双版本最终总回传与继续施工分界包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "双版本交付封存与后续路线": EVOLUTION_ROOT / "03数据" / "100日常稳定双版本交付封存与后续路线包" / "日常稳定双版本交付封存与后续路线包_最新.json",
    "稳定交付版签收完成": EVOLUTION_ROOT / "03数据" / "99稳定交付版本地试运行达标复核与签收完成包" / "稳定交付版本地试运行达标复核与签收完成包_最新.json",
    "稳定试运行首轮观察闭环": EVOLUTION_ROOT / "03数据" / "98稳定试运行首轮观察执行闭环包" / "稳定试运行首轮观察执行闭环包_最新.json",
    "日常签收完成与稳定试运行启动": EVOLUTION_ROOT / "03数据" / "97日常签收完成与稳定试运行启动回传包" / "日常签收完成与稳定试运行启动回传包_最新.json",
    "最终交付清单与启动索引": EVOLUTION_ROOT / "03数据" / "96日常稳定交付最终交付清单与启动索引包" / "日常稳定交付最终交付清单与启动索引包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "双版本最终总回传与继续施工分界包_最新.json"
PACKAGE_MD = DATA_DIR / "双版本最终总回传与继续施工分界包_最新.md"
FINAL_RETURN_MD = DATA_DIR / "双版本最终总回传_最新.md"
BOUNDARY_MD = DATA_DIR / "继续施工分界清单_最新.md"
NEXT_WORK_MD = DATA_DIR / "下一阶段施工路线_最新.md"
GEN_LOG = LOG_DIR / "生成双版本最终总回传与继续施工分界包_最新.json"

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


def final_return_items() -> list[dict[str, str]]:
    return [
        {"版本": "日常可用交付版", "最终状态": "已完成并封存", "可用口径": "可日常使用，可跑只读巡检，可处理低风险候选"},
        {"版本": "稳定交付版", "最终状态": "已完成本地试运行签收封存", "可用口径": "可稳定试运行，持续观察、日报、问题入账和回滚守护"},
        {"版本": "完全交付使用版", "最终状态": "继续施工", "可用口径": "只能推进低风险模板、离线预演、人工确认材料"},
        {"版本": "真正自主运行版", "最终状态": "继续施工", "可用口径": "只能推进观察、候选、规则申请草案和闸口治理"},
    ]


def boundary_items() -> list[dict[str, str]]:
    return [
        {"边界": "已封存版本", "允许做": "只读巡检、问题入账、低风险候选、展示层小修", "不允许做": "破坏已封存证据或混入未确认真实能力"},
        {"边界": "正式规则", "允许做": "候选、申请草案、冲突扫描、签收台账", "不允许做": "自动写正式规则或自动生效"},
        {"边界": "企业微信", "允许做": "本地预演、职责分流、real_send=false 验证", "不允许做": "真实发给联系人或群"},
        {"边界": "n8n", "允许做": "离线蓝图、干跑、凭据隔离、禁用态导出", "不允许做": "真实触发工作流"},
        {"边界": "股票", "允许做": "研究展示、口径一致性、风险复核", "不允许做": "接券商、交易、下单"},
        {"边界": "税收", "允许做": "待复核草案、资料清单、依据摘要", "不允许做": "登录税局、接财税软件、正式税务结论"},
        {"边界": "视频", "允许做": "脚本、分镜、预检、环境识别、回滚预案", "不允许做": "未确认前真实渲染或自动发布"},
        {"边界": "服务", "允许做": "登记需总管确认", "不允许做": "自行重载 19310/19302"},
    ]


def next_work_items() -> list[dict[str, str]]:
    return [
        {"阶段": "稳定版持续运行", "任务": "每日只读回归、日报、问题入账、次轮观察", "优先级": "高"},
        {"阶段": "完全交付低风险推进", "任务": "继续补模板、验收、离线演练、回滚材料", "优先级": "中"},
        {"阶段": "正式规则治理", "任务": "把候选变成申请草案并等待确认", "优先级": "中"},
        {"阶段": "n8n准备", "任务": "继续离线干跑和凭据隔离检查，不启用", "优先级": "中"},
        {"阶段": "视频真实能力准备", "任务": "补环境识别、白名单、放行材料，不渲染不发布", "优先级": "中"},
        {"阶段": "真正自主运行准备", "任务": "积累长期样本、失败演练、人工接管经验", "优先级": "长期"},
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
        "名称": "双版本最终总回传与继续施工分界包",
        "生成时间": now_text(),
        "状态": "dual_version_final_return_boundary_ready" if ready else "dual_version_final_return_boundary_blocked",
        "用途": "把日常可用版、稳定交付版最终总回传和后续继续施工边界分开，防止已封存版本与未解锁能力混淆。",
        "来源摘要": source_summary,
        "双版本最终总回传": final_return_items(),
        "继续施工分界清单": boundary_items(),
        "下一阶段施工路线": next_work_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "双版本最终总回传": str(FINAL_RETURN_MD),
            "继续施工分界清单": str(BOUNDARY_MD),
            "下一阶段施工路线": str(NEXT_WORK_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    final_rows = [f"| {item['版本']} | {item['最终状态']} | {item['可用口径']} |" for item in package["双版本最终总回传"]]
    boundary_rows = [f"| {item['边界']} | {item['允许做']} | {item['不允许做']} |" for item in package["继续施工分界清单"]]
    next_rows = [f"| {item['阶段']} | {item['任务']} | {item['优先级']} |" for item in package["下一阶段施工路线"]]
    package_md = "\n".join([
        "# 双版本最终总回传与继续施工分界包",
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
        "## 双版本最终总回传",
        "| 版本 | 最终状态 | 可用口径 |",
        "| --- | --- | --- |",
        *final_rows,
        "",
        "## 继续施工分界清单",
        "| 边界 | 允许做 | 不允许做 |",
        "| --- | --- | --- |",
        *boundary_rows,
        "",
        "## 下一阶段施工路线",
        "| 阶段 | 任务 | 优先级 |",
        "| --- | --- | --- |",
        *next_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(FINAL_RETURN_MD, "\n".join(["# 双版本最终总回传", "", "| 版本 | 最终状态 | 可用口径 |", "| --- | --- | --- |", *final_rows]))
    write_text(BOUNDARY_MD, "\n".join(["# 继续施工分界清单", "", "| 边界 | 允许做 | 不允许做 |", "| --- | --- | --- |", *boundary_rows]))
    write_text(NEXT_WORK_MD, "\n".join(["# 下一阶段施工路线", "", "| 阶段 | 任务 | 优先级 |", "| --- | --- | --- |", *next_rows]))
    write_json(GEN_LOG, {"名称": "生成双版本最终总回传与继续施工分界包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "分界项": len(package["继续施工分界清单"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
