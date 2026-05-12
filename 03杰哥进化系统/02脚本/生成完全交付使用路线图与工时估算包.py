# -*- coding: utf-8 -*-
"""生成完全交付使用路线图与有效工时估算包。

只生成候选级路线图、进度判断和工时估算；不写正式规则、不修改运行配置、不触发外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "45完全交付使用路线图与工时估算"
LATEST_JSON = OUTPUT_DIR / "完全交付使用路线图与工时估算包_最新.json"
LATEST_MD = OUTPUT_DIR / "完全交付使用路线图与工时估算包_最新.md"

SNAPSHOT_JSON = EVOLUTION_ROOT / "03数据" / "40日常可用版自主巡检快照" / "日常可用版自主巡检快照_最新.json"
STATUS_PACKAGE_JSON = EVOLUTION_ROOT / "03数据" / "43日常可用交付版状态包" / "日常可用交付版状态包_最新.json"
REGRESSION_JSON = EVOLUTION_ROOT / "03数据" / "44日常可用交付版一键只读总回归" / "日常可用交付版一键只读总回归_最新.json"
BLOCKED_JSON = EVOLUTION_ROOT / "03数据" / "39阶段性多业务联调通过封版候选" / "仍阻断能力清单候选_最新.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_workstreams() -> list[dict[str, Any]]:
    return [
        {
            "阶段ID": "DELIVERY-01",
            "名称": "日常可用交付版收口",
            "当前状态": "基本完成",
            "完成度": "88%-93%",
            "剩余有效工时": {"乐观": 8, "常规": 16, "保守": 28},
            "剩余工作": [
                "连续多轮一键总回归稳定记录",
                "日常使用说明与故障处理清单",
                "税收业务对话框接续包重建或替代说明",
                "19310无重载日常巡检节奏固化为候选",
            ],
            "不包含": ["真实外部系统接入", "自动发布", "自动交易", "正式规则自动变更"],
        },
        {
            "阶段ID": "DELIVERY-02",
            "名称": "稳定交付版",
            "当前状态": "中段偏上",
            "完成度": "62%-72%",
            "剩余有效工时": {"乐观": 45, "常规": 75, "保守": 120},
            "剩余工作": [
                "一键总回归的连续多日稳定性记录",
                "异常恢复手册与端口/进程故障分级",
                "日志统一索引与失败定位卡",
                "税收/股票/视频跨线回归样本扩充",
                "候选规则去重、优先级和人工确认台账",
                "服务重载需总管确认的申请/回执模板标准化",
            ],
            "不包含": ["券商交易", "电子税务局登录", "真实视频发布"],
        },
        {
            "阶段ID": "DELIVERY-03",
            "名称": "半自主运行版",
            "当前状态": "底座已形成",
            "完成度": "42%-55%",
            "剩余有效工时": {"乐观": 95, "常规": 155, "保守": 240},
            "剩余工作": [
                "n8n沙盒编排候选与禁用态门禁",
                "企业微信白名单/测试群真实发送候选方案",
                "低风险自动巡检定时化与失败通知候选",
                "跨线任务自动分派策略候选",
                "候选经验到人工确认规则的审批流",
                "视频真实渲染环境识别后的沙盒渲染门禁",
            ],
            "不包含": ["无人工确认的正式规则变更", "资金类交易", "税局真实办理"],
        },
        {
            "阶段ID": "DELIVERY-04",
            "名称": "完全交付使用版",
            "当前状态": "长期目标",
            "完成度": "34%-46%",
            "剩余有效工时": {"乐观": 170, "常规": 280, "保守": 430},
            "剩余工作": [
                "真实外部系统接入的分级授权体系",
                "n8n真实编排的沙盒到白名单到生产灰度",
                "企业微信真实发送白名单与撤回/回滚机制",
                "视频真实渲染环境接通、沙盒成片、人工验收、受控发布",
                "长期日志、审计、异常恢复、权限与凭据隔离",
                "正式规则治理：候选、评审、确认、生效、回滚",
                "用户日常操作面板或替代入口的最终交付形态",
            ],
            "说明": "这里的完全交付使用不等于完全无人驾驶；高风险动作仍建议保留人工确认。",
        },
        {
            "阶段ID": "DELIVERY-05",
            "名称": "真正自主运行版",
            "当前状态": "远期目标",
            "完成度": "28%-38%",
            "剩余有效工时": {"乐观": 280, "常规": 520, "保守": 850},
            "剩余工作": [
                "长期自动决策质量评估",
                "多业务真实动作自动授权矩阵",
                "持续学习的正式规则治理和回滚能力",
                "生产级监控、审计、安全和故障恢复",
                "对税务、资金、发布等高风险域建立可证明的人工监督链",
            ],
            "说明": "基于当前红线和实际风险，该阶段不应作为近期交付目标。",
        },
    ]


def build_package() -> dict[str, Any]:
    snapshot = read_json(SNAPSHOT_JSON)
    status_package = read_json(STATUS_PACKAGE_JSON)
    regression = read_json(REGRESSION_JSON)
    blocked = read_json(BLOCKED_JSON)
    workstreams = build_workstreams()
    return {
        "名称": "完全交付使用路线图与工时估算包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "性质": "候选估算包，不是正式规则或承诺排期",
        "当前基线": {
            "日常可用状态": status_package.get("整体状态"),
            "自主巡检": snapshot.get("汇总", {}),
            "一键只读总回归": regression.get("汇总", {}),
            "仍阻断能力数量": blocked.get("阻断能力数量"),
        },
        "整体进度判断": {
            "日常可用交付版": "88%-93%",
            "稳定交付版": "62%-72%",
            "半自主运行版": "42%-55%",
            "完全交付使用版": "34%-46%",
            "真正自主运行版": "28%-38%",
        },
        "剩余有效工时判断": {
            "日常可用交付版剩余": {"乐观": 8, "常规": 16, "保守": 28},
            "稳定交付版剩余": {"乐观": 45, "常规": 75, "保守": 120},
            "完全交付使用版剩余": {"乐观": 170, "常规": 280, "保守": 430},
            "真正自主运行版剩余": {"乐观": 280, "常规": 520, "保守": 850},
        },
        "路线图": workstreams,
        "近期优先级": [
            "连续3-5轮一键只读总回归保持全通过",
            "生成日常使用说明和故障处理手册",
            "整理19310/19302端口异常时的只读诊断与需总管确认申请模板",
            "补税收业务对话框归档后的接续替代包",
            "补视频真实渲染环境缺口的人工配置说明，不自动接入",
            "补n8n沙盒编排候选，不触发真实工作流",
        ],
        "高风险长期项": [
            "企业微信真实发送",
            "n8n真实触发",
            "券商接口和交易",
            "电子税务局登录",
            "财税软件连接",
            "视频真实发布",
            "候选经验自动转正式规则",
        ],
        "估算口径": [
            "有效工时指真正产出脚本、清单、验收、联调或排障的时间，不包含等待、沟通和人工外部确认。",
            "当前红线继续存在时，完全交付使用版按参谋型/受控型系统估算，不按无人驾驶系统估算。",
            "若放开真实企业微信、n8n、视频渲染等外部动作，工时会增加，因为需要灰度、回滚、安全审计和凭据隔离。",
        ],
        "安全边界": {
            "写正式规则": False,
            "修改运行配置": False,
            "触发服务重载": False,
            "重载19310": False,
            "重载19302": False,
            "真实发送企业微信": False,
            "接n8n": False,
            "触发n8n": False,
            "接券商": False,
            "交易": False,
            "登录电子税务局": False,
            "接财税软件": False,
            "真实渲染视频": False,
            "自动发布视频": False,
            "写正式税务结论": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }


def build_markdown(package: dict[str, Any]) -> str:
    progress = package["整体进度判断"]
    hours = package["剩余有效工时判断"]
    lines = [
        "# 完全交付使用路线图与工时估算包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 性质：{package['性质']}",
        f"- 当前日常可用状态：{package['当前基线']['日常可用状态']}",
        f"- 自主巡检：{package['当前基线']['自主巡检'].get('通过')}/{package['当前基线']['自主巡检'].get('总数')} pass",
        f"- 一键只读总回归：{package['当前基线']['一键只读总回归'].get('通过')}/{package['当前基线']['一键只读总回归'].get('总数')} pass",
        "",
        "## 整体进度",
        "",
        "| 目标版本 | 当前完成度 | 剩余有效工时-乐观 | 常规 | 保守 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    mapping = [
        ("日常可用交付版", "日常可用交付版剩余"),
        ("稳定交付版", "稳定交付版剩余"),
        ("完全交付使用版", "完全交付使用版剩余"),
        ("真正自主运行版", "真正自主运行版剩余"),
    ]
    for name, key in mapping:
        h = hours[key]
        lines.append(f"| {name} | {progress[name]} | {h['乐观']} | {h['常规']} | {h['保守']} |")

    lines.extend(["", "## 路线图", ""])
    for item in package["路线图"]:
        h = item["剩余有效工时"]
        lines.extend(
            [
                f"### {item['阶段ID']} {item['名称']}",
                "",
                f"- 当前状态：{item['当前状态']}",
                f"- 完成度：{item['完成度']}",
                f"- 剩余有效工时：乐观 {h['乐观']} / 常规 {h['常规']} / 保守 {h['保守']}",
                "- 剩余工作：",
                *[f"  - {work}" for work in item["剩余工作"]],
                "",
            ]
        )
    lines.extend(
        [
            "## 近期优先级",
            "",
            *[f"- {item}" for item in package["近期优先级"]],
            "",
            "## 估算口径",
            "",
            *[f"- {item}" for item in package["估算口径"]],
            "",
            "## 安全边界",
            "",
            "- 本包只做候选估算，不写正式规则、不改运行配置。",
            "- 不重载19310/19302，不真实发送企业微信，不触发n8n。",
            "- 不接券商、不交易，不登录税局、不接财税软件。",
            "- 不真实渲染或发布视频，不改总管面板和一键接续包。",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    package = build_package()
    write_json(LATEST_JSON, package)
    write_text(LATEST_MD, build_markdown(package))
    print(json.dumps({"名称": package["名称"], "完全交付常规剩余工时": package["剩余有效工时判断"]["完全交付使用版剩余"]["常规"], "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
