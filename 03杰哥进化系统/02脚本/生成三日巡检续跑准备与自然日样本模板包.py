# -*- coding: utf-8 -*-
"""生成三日巡检续跑准备与自然日样本模板包。

本脚本只生成后续第 2/3 自然日手动巡检模板与准备材料，不伪造样本，
不触发外部系统，不修改服务配置或正式规则。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
SOURCE_59_DIR = EVOLUTION_ROOT / "03数据" / "59稳定候选补强与三日巡检启动包"
SOURCE_LEDGER_JSON = SOURCE_59_DIR / "三日只读巡检样本台账_最新.json"
SOURCE_RECORD_JSON = SOURCE_59_DIR / "三日巡检当日样本记录_最新.json"

OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "65三日巡检续跑准备与自然日样本模板包"
PACKAGE_JSON = OUTPUT_DIR / "三日巡检续跑准备与自然日样本模板包_最新.json"
PACKAGE_MD = OUTPUT_DIR / "三日巡检续跑准备与自然日样本模板包_最新.md"
DAY2_TEMPLATE_MD = OUTPUT_DIR / "第2自然日手动巡检执行模板_最新.md"
DAY3_TEMPLATE_MD = OUTPUT_DIR / "第3自然日手动巡检执行模板_最新.md"
COUNTING_RULES_MD = OUTPUT_DIR / "自然日计数规则_最新.md"
NAMING_GUIDE_MD = OUTPUT_DIR / "样本文件命名建议_最新.md"
FAILURE_GUIDE_MD = OUTPUT_DIR / "失败分级处理说明_最新.md"
READONLY_CHECK_JSON = OUTPUT_DIR / "只读核对结果_最新.json"


SAFETY_BOUNDARY = {
    "真实发送企业微信": False,
    "触发n8n": False,
    "接n8n": False,
    "接券商": False,
    "交易": False,
    "登录电子税务局": False,
    "接财税软件": False,
    "真实渲染视频": False,
    "自动发布视频": False,
    "自动转正式规则": False,
    "修改总管面板": False,
    "修改一键接续包": False,
    "修改服务配置": False,
    "重载19310": False,
    "重载19302": False,
    "伪造第2自然日样本": False,
    "伪造第3自然日样本": False,
}


NATURAL_DAY_RULES = [
    "自然日以本机当前日期 yyyy-mm-dd 为准，同一日期内多次复跑只能覆盖或补充当日样本，不增加自然日计数。",
    "三日达标必须来自 3 个不同自然日，且每个自然日样本状态均为 pass。",
    "当前 59 包首日样本只能作为第 1 自然日；第 2/3 自然日必须在真实到达对应自然日后人工执行并记录。",
    "任一自然日出现 blocked、missing、fail、红线动作或服务重载未确认，三日达标继续保持 false，并按失败分级处理。",
    "模板包只提供手动执行口径和文件命名建议，不创建定时任务，不调用外部业务系统。",
]


CHECKLIST = [
    "确认 59 包样本台账仍可读取，并且当前只记录 1 个自然日。",
    "确认第 2/3 自然日没有被提前写入样本台账或模板包。",
    "按 59 包巡检源逐项只读核对产物，不触发企业微信、n8n、券商、税局、财税软件、视频渲染或发布。",
    "记录执行日期、执行人、巡检源状态、失败分级、处置建议和是否需要总管确认。",
    "完成后只把真实自然日样本追加到后续台账，不把模板占位内容计入三日达标。",
]


FAILURE_LEVELS = [
    {
        "级别": "L1_observation",
        "适用": "单项产物缺失、时间戳较旧、摘要字段不完整，但无真实外部动作风险。",
        "处理": "标记 blocked，补充只读证据；不重载服务，不转正式规则。",
    },
    {
        "级别": "L2_regression_blocker",
        "适用": "总回归失败、巡检源状态非 pass、自然日计数冲突或安全边界字段异常。",
        "处理": "停止三日达标推进，保留失败样本，提交总管确认后再复跑。",
    },
    {
        "级别": "L3_red_line",
        "适用": "出现真实发送、触发 n8n、连接交易/税务/财税软件、服务重载或正式规则写入迹象。",
        "处理": "立即停止续跑，记录红线证据，等待总管人工处置；不得自行修复后继续计数。",
    },
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def source_status() -> dict[str, Any]:
    ledger = read_json(SOURCE_LEDGER_JSON) if SOURCE_LEDGER_JSON.exists() else {}
    record = read_json(SOURCE_RECORD_JSON) if SOURCE_RECORD_JSON.exists() else {}
    samples = ledger.get("自然日样本", [])
    unique_dates = sorted({item.get("样本日期") for item in samples if item.get("样本日期")})
    return {
        "来源台账": str(SOURCE_LEDGER_JSON),
        "来源当日样本": str(SOURCE_RECORD_JSON),
        "来源台账存在": SOURCE_LEDGER_JSON.exists(),
        "来源当日样本存在": SOURCE_RECORD_JSON.exists(),
        "已记录自然日数": len(unique_dates),
        "已记录自然日": unique_dates,
        "三日达标": ledger.get("三日达标"),
        "首日样本状态": record.get("当日状态"),
        "首日样本日期": record.get("样本日期"),
        "确认结论": len(unique_dates) == 1 and ledger.get("三日达标") is False,
    }


def sample_name(day_index: int) -> str:
    return f"三日巡检第{day_index}自然日样本记录_yyyy-mm-dd_手动确认.json"


def build_day_template(day_index: int, status: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# 第{day_index}自然日手动巡检执行模板",
            "",
            "## 前置确认",
            "",
            f"- 当前 59 包已记录自然日数：{status['已记录自然日数']}",
            f"- 当前 59 包三日达标：{status['三日达标']}",
            f"- 本模板不得在第{day_index}自然日真实到达前转为样本。",
            "",
            "## 手动执行步骤",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(CHECKLIST, 1)],
            "",
            "## 建议记录字段",
            "",
            "- 样本日期：yyyy-mm-dd",
            "- 记录时间：yyyy-mm-dd HH:MM:SS",
            f"- 自然日序号：{day_index}",
            "- 当日状态：pass / blocked",
            "- 巡检源结果：沿用 59 包巡检源编号、名称、路径、通过口径、当前结果、摘要",
            "- 失败分级：L1_observation / L2_regression_blocker / L3_red_line",
            "- 总管确认：无需 / 需要 / 已确认",
            "- 三日达标：仅当 3 个不同自然日样本均 pass 时才可为 true",
            "",
            "## 建议文件名",
            "",
            f"- {sample_name(day_index)}",
            f"- 三日巡检第{day_index}自然日样本记录_yyyy-mm-dd_手动确认.md",
        ]
    )


def build_package_md(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# 三日巡检续跑准备与自然日样本模板包",
            "",
            f"- 生成时间：{report['生成时间']}",
            f"- 状态：{report['状态']}",
            f"- 当前已记录自然日数：{report['59包首日样本确认']['已记录自然日数']}",
            f"- 当前三日达标：{report['59包首日样本确认']['三日达标']}",
            f"- 允许作为三日达标：{report['允许作为三日达标']}",
            "",
            "## 输出文件",
            "",
            *[f"- {name}：{path}" for name, path in report["输出文件"].items()],
            "",
            "## 结论",
            "",
            "- 当前仅确认首日样本存在，三日达标仍为 false。",
            "- 第 2/3 自然日仅提供手动执行模板和命名建议，未生成真实样本。",
        ]
    )


def main() -> int:
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = source_status()
    report = {
        "名称": "三日巡检续跑准备与自然日样本模板包",
        "生成时间": now_text,
        "状态": "three_day_patrol_rerun_template_ready",
        "59包首日样本确认": status,
        "允许作为三日达标": False,
        "自然日计数规则": NATURAL_DAY_RULES,
        "手动执行检查项": CHECKLIST,
        "失败分级处理": FAILURE_LEVELS,
        "样本文件命名建议": {
            "第2自然日JSON": sample_name(2),
            "第2自然日Markdown": "三日巡检第2自然日样本记录_yyyy-mm-dd_手动确认.md",
            "第3自然日JSON": sample_name(3),
            "第3自然日Markdown": "三日巡检第3自然日样本记录_yyyy-mm-dd_手动确认.md",
        },
        "未生成样本声明": {
            "第2自然日样本": "未生成，等待真实自然日到达后人工记录",
            "第3自然日样本": "未生成，等待真实自然日到达后人工记录",
        },
        "安全边界": SAFETY_BOUNDARY,
        "输出文件": {
            "总包JSON": str(PACKAGE_JSON),
            "总包Markdown": str(PACKAGE_MD),
            "第2自然日手动巡检执行模板": str(DAY2_TEMPLATE_MD),
            "第3自然日手动巡检执行模板": str(DAY3_TEMPLATE_MD),
            "自然日计数规则": str(COUNTING_RULES_MD),
            "样本文件命名建议": str(NAMING_GUIDE_MD),
            "失败分级处理说明": str(FAILURE_GUIDE_MD),
        },
    }

    write_json(PACKAGE_JSON, report)
    write_text(PACKAGE_MD, build_package_md(report))
    write_text(DAY2_TEMPLATE_MD, build_day_template(2, status))
    write_text(DAY3_TEMPLATE_MD, build_day_template(3, status))
    write_text(COUNTING_RULES_MD, "# 自然日计数规则\n\n" + "\n".join(f"- {item}" for item in NATURAL_DAY_RULES))
    write_text(
        NAMING_GUIDE_MD,
        "\n".join(
            [
                "# 样本文件命名建议",
                "",
                f"- 第2自然日 JSON：{report['样本文件命名建议']['第2自然日JSON']}",
                f"- 第2自然日 Markdown：{report['样本文件命名建议']['第2自然日Markdown']}",
                f"- 第3自然日 JSON：{report['样本文件命名建议']['第3自然日JSON']}",
                f"- 第3自然日 Markdown：{report['样本文件命名建议']['第3自然日Markdown']}",
                "",
                "命名中的 yyyy-mm-dd 必须替换为真实执行当天日期，不得提前填写未来日期。",
            ]
        ),
    )
    write_text(
        FAILURE_GUIDE_MD,
        "# 失败分级处理说明\n\n"
        + "\n\n".join(
            f"## {item['级别']}\n\n- 适用：{item['适用']}\n- 处理：{item['处理']}" for item in FAILURE_LEVELS
        ),
    )
    print(
        json.dumps(
            {
                "状态": report["状态"],
                "已记录自然日数": status["已记录自然日数"],
                "三日达标": status["三日达标"],
                "输出": str(PACKAGE_JSON),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
