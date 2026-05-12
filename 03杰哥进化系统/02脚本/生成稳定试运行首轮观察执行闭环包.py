# -*- coding: utf-8 -*-
"""生成稳定交付版首轮试运行观察执行闭环包。

只汇总试运行任务、观察点、问题入账和次轮处理建议；
不触发外部系统、不写正式规则、不重载服务。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "98稳定试运行首轮观察执行闭环包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "稳定试运行首轮观察执行闭环包验收"

SOURCES = {
    "日常可用版自主巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "日常可用版一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "日常签收完成与稳定试运行启动回传": EVOLUTION_ROOT / "03数据" / "97日常签收完成与稳定试运行启动回传包" / "日常签收完成与稳定试运行启动回传包_最新.json",
    "最终交付清单与启动索引": EVOLUTION_ROOT / "03数据" / "96日常稳定交付最终交付清单与启动索引包" / "日常稳定交付最终交付清单与启动索引包_最新.json",
    "签收回执与首轮试运行任务单": EVOLUTION_ROOT / "03数据" / "95日常稳定交付签收回执与首轮试运行任务单包" / "日常稳定交付签收回执与首轮试运行任务单包_最新.json",
    "稳定版试运行反馈本地入账": EVOLUTION_ROOT / "03数据" / "92稳定版试运行反馈本地入账执行器包" / "稳定版试运行反馈本地入账执行器包_最新.json",
    "运行期问题闭环总台账索引": EVOLUTION_ROOT / "03数据" / "84运行期问题闭环总台账索引包" / "运行期问题闭环总台账索引包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "稳定试运行首轮观察执行闭环包_最新.json"
PACKAGE_MD = DATA_DIR / "稳定试运行首轮观察执行闭环包_最新.md"
OBSERVE_MD = DATA_DIR / "首轮观察执行清单_最新.md"
LOOP_MD = DATA_DIR / "问题闭环处理清单_最新.md"
NEXT_MD = DATA_DIR / "次轮试运行建议_最新.md"
GEN_LOG = LOG_DIR / "生成稳定试运行首轮观察执行闭环包_最新.json"

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


def observe_items() -> list[dict[str, str]]:
    return [
        {"编号": "OBS-001", "观察项": "一键只读总回归", "通过口径": "11/11 通过", "失败动作": "停止扩大试运行，进入问题回收"},
        {"编号": "OBS-002", "观察项": "税收待复核样例", "通过口径": "只输出待复核草案摘要", "失败动作": "回收到税收候选"},
        {"编号": "OBS-003", "观察项": "股票展示口径", "通过口径": "无交易化表达和冲突口径", "失败动作": "回收到展示层候选"},
        {"编号": "OBS-004", "观察项": "视频真实动作阻断", "通过口径": "真实渲染/发布均 blocked", "失败动作": "立即登记红线"},
        {"编号": "OBS-005", "观察项": "反馈入账", "通过口径": "进入候选台账或拒收清单", "失败动作": "手工登记到问题闭环索引"},
        {"编号": "OBS-006", "观察项": "需确认事项", "通过口径": "未自动执行红线动作", "失败动作": "标记需总管确认"},
    ]


def loop_items() -> list[dict[str, str]]:
    return [
        {"类型": "低风险体验问题", "处理": "形成候选和只读验收", "是否需总管确认": "否"},
        {"类型": "展示口径问题", "处理": "限定展示层修复", "是否需总管确认": "否"},
        {"类型": "入口路由问题", "处理": "公共接入层最小适配，重载另行确认", "是否需总管确认": "可能"},
        {"类型": "正式规则问题", "处理": "申请草案和冲突扫描", "是否需总管确认": "是"},
        {"类型": "外部自动化问题", "处理": "离线干跑和禁用态检查", "是否需总管确认": "是"},
        {"类型": "真实发布/渲染/交易/登录", "处理": "保持阻断", "是否需总管确认": "是"},
    ]


def next_items() -> list[dict[str, str]]:
    return [
        {"下一步": "稳定试运行第二轮样本扩展", "默认动作": "只读抽测和反馈入账", "目标": "增加稳定性样本"},
        {"下一步": "日报与次日待办持续刷新", "默认动作": "本地汇总", "目标": "把低风险续建和确认事项分开"},
        {"下一步": "问题闭环去重复跑", "默认动作": "候选台账去重", "目标": "减少重复修复"},
        {"下一步": "正式规则申请准备", "默认动作": "草案审查", "目标": "等待总管确认"},
        {"下一步": "外部真实能力继续禁用", "默认动作": "只做离线预演", "目标": "保持安全边界"},
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
        "名称": "稳定试运行首轮观察执行闭环包",
        "生成时间": now_text(),
        "状态": "stable_trial_round1_observation_loop_ready" if ready else "stable_trial_round1_observation_loop_blocked",
        "用途": "把稳定交付版首轮试运行的观察项、问题闭环处理和次轮建议收成一个执行闭环。",
        "来源摘要": source_summary,
        "首轮观察执行清单": observe_items(),
        "问题闭环处理清单": loop_items(),
        "次轮试运行建议": next_items(),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "首轮观察执行清单": str(OBSERVE_MD),
            "问题闭环处理清单": str(LOOP_MD),
            "次轮试运行建议": str(NEXT_MD),
        },
    }

    write_json(PACKAGE_JSON, package)
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    observe_rows = [f"| {item['编号']} | {item['观察项']} | {item['通过口径']} | {item['失败动作']} |" for item in package["首轮观察执行清单"]]
    loop_rows = [f"| {item['类型']} | {item['处理']} | {item['是否需总管确认']} |" for item in package["问题闭环处理清单"]]
    next_rows = [f"| {item['下一步']} | {item['默认动作']} | {item['目标']} |" for item in package["次轮试运行建议"]]
    package_md = "\n".join([
        "# 稳定试运行首轮观察执行闭环包",
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
        "## 首轮观察执行清单",
        "| 编号 | 观察项 | 通过口径 | 失败动作 |",
        "| --- | --- | --- | --- |",
        *observe_rows,
        "",
        "## 问题闭环处理清单",
        "| 类型 | 处理 | 是否需总管确认 |",
        "| --- | --- | --- |",
        *loop_rows,
        "",
        "## 次轮试运行建议",
        "| 下一步 | 默认动作 | 目标 |",
        "| --- | --- | --- |",
        *next_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(OBSERVE_MD, "\n".join(["# 首轮观察执行清单", "", "| 编号 | 观察项 | 通过口径 | 失败动作 |", "| --- | --- | --- | --- |", *observe_rows]))
    write_text(LOOP_MD, "\n".join(["# 问题闭环处理清单", "", "| 类型 | 处理 | 是否需总管确认 |", "| --- | --- | --- |", *loop_rows]))
    write_text(NEXT_MD, "\n".join(["# 次轮试运行建议", "", "| 下一步 | 默认动作 | 目标 |", "| --- | --- | --- |", *next_rows]))
    write_json(GEN_LOG, {"名称": "生成稳定试运行首轮观察执行闭环包", "生成时间": now_text(), "通过": ready, "错误数": 0 if ready else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "观察项": len(package["首轮观察执行清单"]), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
