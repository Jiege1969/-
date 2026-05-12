# -*- coding: utf-8 -*-
"""生成稳定候选异常样例库与演练包。

只生成异常样例和只读演练资料，不制造真实故障，不触发服务或外部系统。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "60稳定候选异常样例库与演练包"
LATEST_JSON = OUTPUT_DIR / "稳定候选异常样例库与演练包_最新.json"
LATEST_MD = OUTPUT_DIR / "稳定候选异常样例库与演练包_最新.md"
SAMPLE_MD = OUTPUT_DIR / "稳定候选异常样例库_最新.md"
DRILL_MD = OUTPUT_DIR / "异常分级演练说明_最新.md"
ACTION_MD = OUTPUT_DIR / "异常处置演练结果口径_最新.md"


EXCEPTION_SAMPLES: list[dict[str, Any]] = [
    {
        "编号": "SES-001",
        "业务线": "企业微信公共接入层",
        "异常现象": "19310 在线但工作秘书税收三样本失败",
        "预期分级": "L2",
        "自动动作": "复跑企业微信公共入口日常只读巡检；只检查路由和传参。",
        "停止条件": "需要重载 19310 时升级 L3，需总管确认。",
    },
    {
        "编号": "SES-002",
        "业务线": "企业微信公共接入层",
        "异常现象": "19310 端口不在线或运行态未加载新代码",
        "预期分级": "L3",
        "自动动作": "停止自动施工，生成重载申请。",
        "停止条件": "不得自行重载 19310。",
    },
    {
        "编号": "SES-003",
        "业务线": "税收业务",
        "异常现象": "税收回复标题不是待复核草案摘要",
        "预期分级": "L2",
        "自动动作": "检查公共层是否把原始文本传给税收新入口。",
        "停止条件": "不得生成正式税务结论，不得登录税局。",
    },
    {
        "编号": "SES-004",
        "业务线": "股票研究",
        "异常现象": "前台展示同时出现研究价值推荐与回避/风险复核",
        "预期分级": "L2",
        "自动动作": "只修展示层或展示产物，复跑展示口径一致性验收。",
        "停止条件": "不得改评分引擎，不得接券商或交易。",
    },
    {
        "编号": "SES-005",
        "业务线": "股票研究",
        "异常现象": "出现下单、加仓、减仓、仓位等交易化表达",
        "预期分级": "L2",
        "自动动作": "执行展示口径扫雷和只读验收。",
        "停止条件": "任何券商连接或交易动作升级 L4。",
    },
    {
        "编号": "SES-006",
        "业务线": "视频制作",
        "异常现象": "真实渲染预检从 blocked 变为可进入",
        "预期分级": "L4",
        "自动动作": "立即停止，保留预检日志。",
        "停止条件": "不得调用 MoneyPrinterTurbo 或 ImageMagick 真实渲染。",
    },
    {
        "编号": "SES-007",
        "业务线": "视频制作",
        "异常现象": "发布预检未放行却显示可发布",
        "预期分级": "L4",
        "自动动作": "立即停止，保留发布预检日志。",
        "停止条件": "不得上传或自动发布。",
    },
    {
        "编号": "SES-008",
        "业务线": "智能进化候选",
        "异常现象": "候选经验被误当作正式规则",
        "预期分级": "L5",
        "自动动作": "停止，只生成候选说明和差异清单。",
        "停止条件": "不得写正式规则或改运行配置。",
    },
    {
        "编号": "SES-009",
        "业务线": "总回归",
        "异常现象": "一键只读总回归 11 项中 1 项失败",
        "预期分级": "L2",
        "自动动作": "按失败项定位到业务线，复跑对应只读验收。",
        "停止条件": "若涉及服务重载或红线，升级 L3-L5。",
    },
    {
        "编号": "SES-010",
        "业务线": "接续与交接",
        "异常现象": "候选资料索引缺失或路径断裂",
        "预期分级": "L1",
        "自动动作": "重建候选索引或复跑对应生成脚本。",
        "停止条件": "不得修改原一键接续包。",
    },
]


DRILL_RULES = [
    "演练只读取样例，不制造真实异常。",
    "L1/L2 可继续只读复跑或低风险候选修复。",
    "L3 涉及 19310/19302 运行态，必须停下等总管确认。",
    "L4 涉及真实外部动作风险，必须停下并保留日志。",
    "L5 涉及正式规则或总管资产，必须停下并只写候选说明。",
]


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "触发n8n": False,
    "接n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "生成正式税务结论": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "修改运行配置": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "重载19310": False,
    "重载19302": False,
    "请求19302业务接口": False,
    "制造真实异常": False,
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_sample_md(report: dict[str, Any]) -> str:
    rows = [
        f"| {item['编号']} | {item['业务线']} | {item['异常现象']} | {item['预期分级']} | {item['自动动作']} | {item['停止条件']} |"
        for item in report["异常样例"]
    ]
    return "\n".join(["# 稳定候选异常样例库", "", "| 编号 | 业务线 | 异常现象 | 预期分级 | 自动动作 | 停止条件 |", "| --- | --- | --- | --- | --- | --- |", *rows, ""])


def build_drill_md(report: dict[str, Any]) -> str:
    lines = ["# 异常分级演练说明", ""]
    lines.extend([f"- {item}" for item in report["演练规则"]])
    return "\n".join(lines)


def build_action_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 异常处置演练结果口径",
            "",
            "- 演练通过不代表真实故障已发生或已恢复。",
            "- 演练通过只说明异常样例、分级和处置边界齐全。",
            "- 出现 L3/L4/L5 时，自动施工必须停下汇报。",
        ]
    )


def build_summary_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 稳定候选异常样例库与演练包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 异常样例：{len(report['异常样例'])}",
            f"- 演练规则：{len(report['演练规则'])}",
            "",
            "## 输出文件",
            "",
            f"- 稳定候选异常样例库：{SAMPLE_MD}",
            f"- 异常分级演练说明：{DRILL_MD}",
            f"- 异常处置演练结果口径：{ACTION_MD}",
            "",
            "## 核心口径",
            "",
            "- 只读演练，不制造真实故障。",
            "- L3/L4/L5 一律停下等待确认或汇报红线。",
        ]
    )


def main() -> int:
    report = {
        "名称": "稳定候选异常样例库与演练包",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "stable_candidate_exception_samples_drill_ready",
        "异常样例": EXCEPTION_SAMPLES,
        "演练规则": DRILL_RULES,
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(LATEST_JSON),
            "总包Markdown": str(LATEST_MD),
            "稳定候选异常样例库": str(SAMPLE_MD),
            "异常分级演练说明": str(DRILL_MD),
            "异常处置演练结果口径": str(ACTION_MD),
        },
    }
    write_json(LATEST_JSON, report)
    write_text(SAMPLE_MD, build_sample_md(report))
    write_text(DRILL_MD, build_drill_md(report))
    write_text(ACTION_MD, build_action_md(report))
    write_text(LATEST_MD, build_summary_md(report))
    print(json.dumps({"状态": report["状态"], "异常样例": len(EXCEPTION_SAMPLES), "输出": str(LATEST_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
