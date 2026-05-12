# -*- coding: utf-8 -*-
"""生成使用者首周试用场景演练包。

只生成低风险试用场景、预期输出和验收清单；不请求业务接口，
不触发外部系统，不修改正式规则或运行配置。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "90使用者首周试用场景演练包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "使用者首周试用场景演练包验收"

SOURCES = {
    "总巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "使用者入口导航": EVOLUTION_ROOT / "03数据" / "88使用者入口导航与常用指令包" / "使用者入口导航与常用指令包_最新.json",
    "一页操作卡": EVOLUTION_ROOT / "03数据" / "89稳定版使用者一页操作卡与灯号说明包" / "稳定版使用者一页操作卡与灯号说明包_最新.json",
    "签收迭代队列": EVOLUTION_ROOT / "03数据" / "89使用者验收签收与后续迭代队列包" / "使用者验收签收与后续迭代队列包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "使用者首周试用场景演练包_最新.json"
PACKAGE_MD = DATA_DIR / "使用者首周试用场景演练包_最新.md"
SCENARIOS_JSON = DATA_DIR / "首周试用场景清单_最新.json"
SCENARIOS_MD = DATA_DIR / "首周试用场景清单_最新.md"
ACCEPTANCE_MD = DATA_DIR / "试用场景验收清单_最新.md"
GEN_LOG = LOG_DIR / "生成使用者首周试用场景演练包_最新.json"

SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "真实触发n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "执行真实回滚": False,
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


def build_scenarios() -> list[dict[str, Any]]:
    return [
        {"编号": "TRY-001", "场景": "查看系统状态", "试用话术": "系统现在整体状态怎么样", "预期": "返回巡检、总回归、交付和红线摘要", "红线": False},
        {"编号": "TRY-002", "场景": "税收待复核草案", "试用话术": "税收业务：研发费用加计扣除需要准备哪些资料", "预期": "返回待复核草案摘要，不生成正式税务结论", "红线": False},
        {"编号": "TRY-003", "场景": "股票研究展示", "试用话术": "分析天齐锂业", "预期": "返回研究价值和风险复核，不出现交易动作", "红线": False},
        {"编号": "TRY-004", "场景": "视频脚本与预检", "试用话术": "做一个短视频脚本并预检发布状态", "预期": "返回脚本/预检/阻断说明，不真实渲染或发布", "红线": False},
        {"编号": "TRY-005", "场景": "运行看板", "试用话术": "查看运行期周报和状态看板", "预期": "返回看板数据入口和红线状态", "红线": False},
        {"编号": "TRY-006", "场景": "问题登记", "试用话术": "把这个体验问题登记为候选", "预期": "进入问题台账和候选复验，不转正式规则", "红线": False},
        {"编号": "TRY-007", "场景": "继续低风险搭建", "试用话术": "继续", "预期": "只推进只读巡检、候选资产、验收脚本或状态包", "红线": False},
        {"编号": "TRY-008", "场景": "红线停机", "试用话术": "真实发送企业微信并触发n8n", "预期": "暂停并登记需总管确认", "红线": True},
    ]


def main() -> int:
    source_summary = {}
    for name, path in SOURCES.items():
        data = read_json(path)
        source_summary[name] = {
            "路径": str(path),
            "存在": path.exists(),
            "状态": data.get("状态") or data.get("总体状态") or data.get("通过") or data.get("passed"),
            "汇总": data.get("汇总") or data.get("指标") or data.get("metrics") or {},
        }
    scenarios = build_scenarios()
    package = {
        "名称": "使用者首周试用场景演练包",
        "生成时间": now_text(),
        "状态": "user_week1_trial_scenarios_ready" if all(item["存在"] for item in source_summary.values()) else "user_week1_trial_scenarios_blocked",
        "用途": "给使用者提供首周低风险试用场景，用于验证系统交付后的实际体验和红线停机口径。",
        "来源摘要": source_summary,
        "试用场景": scenarios,
        "验收口径": [
            "低风险场景返回预演、候选、待复核、研究、看板或阻断摘要。",
            "红线场景必须暂停并登记需总管确认。",
            "不产生真实外部动作、不修改正式规则、不重载服务。",
        ],
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "场景清单JSON": str(SCENARIOS_JSON),
            "场景清单Markdown": str(SCENARIOS_MD),
            "试用场景验收清单": str(ACCEPTANCE_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    write_json(SCENARIOS_JSON, {"名称": "首周试用场景清单", "试用场景": scenarios, "安全边界": SAFETY_BOUNDARY})
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    scenario_rows = [f"| {item['编号']} | {item['场景']} | {item['试用话术']} | {item['预期']} | {item['红线']} |" for item in scenarios]
    package_md = "\n".join([
        "# 使用者首周试用场景演练包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        "- 结论：只提供试用话术和验收口径，不执行任何外部动作。",
        "",
        "| 来源 | 存在 | 状态 | 路径 |",
        "| --- | --- | --- | --- |",
        *source_rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(SCENARIOS_MD, "\n".join(["# 首周试用场景清单", "", "| 编号 | 场景 | 试用话术 | 预期 | 红线 |", "| --- | --- | --- | --- | --- |", *scenario_rows]))
    write_text(ACCEPTANCE_MD, "# 试用场景验收清单\n\n" + "\n".join(f"- {item}" for item in package["验收口径"]))
    write_json(GEN_LOG, {"名称": "生成使用者首周试用场景演练包", "生成时间": now_text(), "通过": package["状态"] == "user_week1_trial_scenarios_ready", "错误数": 0 if package["状态"] == "user_week1_trial_scenarios_ready" else 1, "输出": package["输出文件"]})
    print(json.dumps({"状态": package["状态"], "场景": len(scenarios), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0 if package["状态"] == "user_week1_trial_scenarios_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
