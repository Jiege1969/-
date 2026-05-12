# -*- coding: utf-8 -*-
"""生成运行期问题闭环总台账索引包。

只汇总运行期问题状态、证据入口和升级规则，不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DATA_DIR = EVOLUTION_ROOT / "03数据" / "84运行期问题闭环总台账索引包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "运行期问题闭环总台账索引包验收"

SOURCES = {
    "总巡检快照": EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json",
    "一键只读总回归": EVOLUTION_ROOT / "04日志" / "日常可用交付版一键只读总回归验收" / "daily-usable-readonly-regression-verify-最新.json",
    "首日观察": EVOLUTION_ROOT / "03数据" / "81交付后首日运行观察与问题登记包" / "交付后首日运行观察与问题登记包_最新.json",
    "每日开工收工": EVOLUTION_ROOT / "03数据" / "82每日开工收工清单与低风险续跑包" / "每日开工收工清单与低风险续跑包_最新.json",
    "首周趋势升级": EVOLUTION_ROOT / "03数据" / "83首周运行趋势与问题升级包" / "首周运行趋势与问题升级包_最新.json",
    "反馈人工确认状态机": EVOLUTION_ROOT / "03数据" / "80三业务反馈人工确认状态机与候选生效前闸口包" / "三业务反馈人工确认状态机与候选生效前闸口包_最新.json",
    "n8n失败演练回滚": EVOLUTION_ROOT / "03数据" / "81n8n离线闸口失败演练与回滚剧本包" / "n8n离线闸口失败演练与回滚剧本包_最新.json",
}

PACKAGE_JSON = DATA_DIR / "运行期问题闭环总台账索引包_最新.json"
PACKAGE_MD = DATA_DIR / "运行期问题闭环总台账索引包_最新.md"
LEDGER_JSON = DATA_DIR / "运行期问题总台账模板_最新.json"
LEDGER_MD = DATA_DIR / "运行期问题总台账模板_最新.md"
STATE_MD = DATA_DIR / "问题状态流转说明_最新.md"
EVIDENCE_MD = DATA_DIR / "运行期证据入口索引_最新.md"
GEN_LOG = LOG_DIR / "生成运行期问题闭环总台账索引包_最新.json"

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


def build_state_flow() -> list[dict[str, Any]]:
    return [
        {"状态": "发现", "说明": "来自首日观察、每日清单、总巡检或用户反馈", "下一步": "登记台账", "需总管确认": False},
        {"状态": "候选", "说明": "生成低风险候选资产或复验卡", "下一步": "只读复验", "需总管确认": False},
        {"状态": "复验", "说明": "本地只读复验或离线干跑", "下一步": "关闭/升级", "需总管确认": False},
        {"状态": "升级", "说明": "连续问题、影响使用体验或需要外部动作", "下一步": "总管确认", "需总管确认": True},
        {"状态": "暂停", "说明": "触碰红线、服务重载、正式规则或真实外部动作", "下一步": "只登记不执行", "需总管确认": True},
        {"状态": "关闭", "说明": "问题已复验通过且无红线动作", "下一步": "保留证据", "需总管确认": False},
    ]


def build_ledger_template() -> list[dict[str, Any]]:
    return [
        {
            "问题编号": "RUN-ISSUE-001",
            "发现时间": "",
            "来源": "首日观察/每日清单/首周趋势/用户反馈/总巡检/总回归",
            "业务域": "企业微信/税收/股票/视频/n8n/进化/通用",
            "当前状态": "发现",
            "严重级别": "观察/复验/升级/暂停",
            "是否触碰红线": False,
            "是否需总管确认": False,
            "证据路径": "",
            "候选产物路径": "",
            "复验日志路径": "",
            "关闭条件": "",
        }
    ]


def main() -> int:
    source_summary = {}
    for name, path in SOURCES.items():
        data = read_json(path)
        source_summary[name] = {
            "路径": str(path),
            "存在": path.exists(),
            "状态": data.get("状态") or data.get("总体状态") or data.get("通过") or data.get("passed"),
            "汇总": data.get("汇总", data.get("指标", data.get("metrics", {}))),
        }
    state_flow = build_state_flow()
    ledger_template = build_ledger_template()
    package = {
        "名称": "运行期问题闭环总台账索引包",
        "生成时间": now_text(),
        "状态": "runtime_issue_loop_ledger_index_ready",
        "用途": "把交付后观察、每日清单、首周趋势、反馈确认和n8n离线失败演练串成运行期问题闭环台账。",
        "来源摘要": source_summary,
        "状态流转": state_flow,
        "台账模板": ledger_template,
        "关闭原则": [
            "只读复验通过且错误数为0。",
            "未触碰红线，且不需要服务重载。",
            "未写正式规则，未修改总管面板或一键接续包。",
            "证据路径、候选产物、复验日志至少保留一个可查入口。",
        ],
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "台账模板JSON": str(LEDGER_JSON),
            "台账模板Markdown": str(LEDGER_MD),
            "状态流转说明": str(STATE_MD),
            "证据入口索引": str(EVIDENCE_MD),
        },
    }
    write_json(PACKAGE_JSON, package)
    write_json(LEDGER_JSON, {"名称": "运行期问题总台账模板", "模板": ledger_template, "状态流转": state_flow})
    source_rows = [f"| {name} | {item['存在']} | {item['状态']} | {item['路径']} |" for name, item in source_summary.items()]
    state_rows = [f"| {item['状态']} | {item['说明']} | {item['下一步']} | {item['需总管确认']} |" for item in state_flow]
    write_text(
        PACKAGE_MD,
        "\n".join([
            "# 运行期问题闭环总台账索引包",
            "",
            f"- 生成时间：{package['生成时间']}",
            f"- 状态：{package['状态']}",
            "- 结论：只做运行期问题登记、复验、升级、关闭索引，不执行外部动作。",
            "",
            "| 来源 | 存在 | 状态 | 路径 |",
            "| --- | --- | --- | --- |",
            *source_rows,
        ]),
    )
    write_text(LEDGER_MD, "# 运行期问题总台账模板\n\n" + "\n".join(f"- {k}：{v}" for k, v in ledger_template[0].items()))
    write_text(STATE_MD, "\n".join(["# 问题状态流转说明", "", "| 状态 | 说明 | 下一步 | 需总管确认 |", "| --- | --- | --- | --- |", *state_rows]))
    write_text(EVIDENCE_MD, "\n".join(["# 运行期证据入口索引", "", *[f"- {name}：{item['路径']}" for name, item in source_summary.items()]]))
    write_json(GEN_LOG, {"名称": "生成运行期问题闭环总台账索引包", "生成时间": now_text(), "通过": True, "错误数": 0, "输出": package["输出文件"]})
    print(json.dumps({"状态": "ready", "来源": len(source_summary), "状态数": len(state_flow), "输出": str(PACKAGE_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
