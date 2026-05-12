# -*- coding: utf-8 -*-
"""生成交付后首日运行观察与问题登记包。

只生成本地观察清单、问题登记模板和复验建议；不触发任何外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "81交付后首日运行观察与问题登记包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "交付后首日运行观察与问题登记包验收"

SNAPSHOT_JSON = EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"
REGRESSION_JSON = EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json"

PACKAGE_JSON = DATA_DIR / "交付后首日运行观察与问题登记包_最新.json"
PACKAGE_MD = DATA_DIR / "交付后首日运行观察与问题登记包_最新.md"
OBSERVE_MD = DATA_DIR / "首日运行观察清单_最新.md"
ISSUE_LEDGER_JSON = DATA_DIR / "首日问题登记台账模板_最新.json"
ISSUE_LEDGER_MD = DATA_DIR / "首日问题登记台账模板_最新.md"
RECHECK_MD = DATA_DIR / "首日复验建议_最新.md"
GEN_LOG = LOG_DIR / "生成交付后首日运行观察与问题登记包_最新.json"

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


def build_observation_items() -> list[dict[str, Any]]:
    return [
        {"编号": "D1-001", "观察项": "企业微信公共入口本地预演", "期望": "职责分流正确，real_send=false", "异常处理": "登记问题，不真实发送"},
        {"编号": "D1-002", "观察项": "税收待复核草案摘要", "期望": "标题和事项识别正确，不生成正式税务结论", "异常处理": "登记为税收候选问题"},
        {"编号": "D1-003", "观察项": "股票研究展示口径", "期望": "无交易化、推荐/回避冲突表述", "异常处理": "只修展示候选，不改交易能力"},
        {"编号": "D1-004", "观察项": "视频脚本/分镜/预检", "期望": "真实渲染和发布保持 blocked", "异常处理": "记录环境缺口，不执行渲染"},
        {"编号": "D1-005", "观察项": "n8n 离线干跑", "期望": "real_trigger=false，webhook_enabled=false", "异常处理": "仅更新离线闸口矩阵候选"},
        {"编号": "D1-006", "观察项": "进化候选吸收", "期望": "只生成候选和只读验收，不转正式规则", "异常处理": "暂停并登记需总管确认"},
        {"编号": "D1-007", "观察项": "19310/19302 服务状态", "期望": "不重载；如需重载只登记", "异常处理": "需总管确认"},
        {"编号": "D1-008", "观察项": "总巡检与一键只读总回归", "期望": "失败数为0", "异常处理": "按失败项登记台账，不做外部动作"},
    ]


def main() -> int:
    snapshot = read_json(SNAPSHOT_JSON)
    regression = read_json(REGRESSION_JSON)
    observation_items = build_observation_items()
    issue_template = [
        {
            "问题编号": "D1-ISSUE-001",
            "来源观察项": "",
            "业务域": "企业微信/税收/股票/视频/进化/n8n/通用",
            "问题描述": "",
            "严重级别": "低/中/高/红线",
            "是否触碰红线": False,
            "是否需总管确认": False,
            "处理状态": "待确认",
            "证据路径": "",
            "下一步建议": "",
        }
    ]
    package = {
        "名称": "交付后首日运行观察与问题登记包",
        "生成时间": now_text(),
        "状态": "day1_observation_ready",
        "用途": "把日常可用版和稳定交付版交付后的首日观察、问题登记、复验动作固定为低风险本地流程。",
        "当前总巡检": {"路径": str(SNAPSHOT_JSON), "汇总": snapshot.get("汇总", {}), "总体状态": snapshot.get("总体状态")},
        "当前一键只读总回归": {"路径": str(REGRESSION_JSON), "指标": regression.get("指标", {}), "通过": regression.get("通过")},
        "观察项": observation_items,
        "问题台账模板条目数": len(issue_template),
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "首日运行观察清单": str(OBSERVE_MD),
            "首日问题登记台账模板JSON": str(ISSUE_LEDGER_JSON),
            "首日问题登记台账模板Markdown": str(ISSUE_LEDGER_MD),
            "首日复验建议": str(RECHECK_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    write_json(ISSUE_LEDGER_JSON, {"名称": "首日问题登记台账模板", "模板": issue_template, "安全边界": SAFETY_BOUNDARY})

    rows = [f"| {item['编号']} | {item['观察项']} | {item['期望']} | {item['异常处理']} |" for item in observation_items]
    package_md = "\n".join([
        "# 交付后首日运行观察与问题登记包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 状态：{package['状态']}",
        "- 结论：只做首日观察、问题登记和复验建议，不执行任何真实外部动作。",
        "",
        "| 编号 | 观察项 | 期望 | 异常处理 |",
        "| --- | --- | --- | --- |",
        *rows,
    ])
    write_text(PACKAGE_MD, package_md)
    write_text(OBSERVE_MD, package_md)
    write_text(ISSUE_LEDGER_MD, "\n".join([
        "# 首日问题登记台账模板",
        "",
        "| 字段 | 说明 |",
        "| --- | --- |",
        "| 问题编号 | D1-ISSUE-xxx |",
        "| 来源观察项 | 对应 D1-001 到 D1-008 |",
        "| 是否触碰红线 | true 时立即暂停 |",
        "| 是否需总管确认 | true 时不得自行执行 |",
        "| 处理状态 | 待确认/候选已生成/已复验/关闭 |",
    ]))
    write_text(RECHECK_MD, "\n".join([
        "# 首日复验建议",
        "",
        "- 使用前查看总巡检快照和一键只读总回归。",
        "- 首日只观察本地预演、候选、只读巡检和阻断状态。",
        "- 出现红线或服务重载需求，登记为需总管确认。",
        "- 首日结束后，可把问题台账转为候选补强包，不自动转正式规则。",
    ]))
    write_json(GEN_LOG, {"名称": "生成交付后首日运行观察与问题登记包", "生成时间": now_text(), "通过": True, "错误数": 0, "输出": package["输出文件"]})
    print(json.dumps({"状态": "ready", "观察项": len(observation_items), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
