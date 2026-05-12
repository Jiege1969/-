# -*- coding: utf-8 -*-
"""
名称：生成股票微信短文条件口径影子预览.py
作用：把证据源映射和价位成交额条件口径合成为微信端 6+1 短文影子预览。
安全边界：只读影子映射和口径预览；只写 03数据/221微信短文条件口径影子预览；不改正式入口，不重启服务，不发送企业微信，不触发 n8n，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "221微信短文条件口径影子预览"

EVIDENCE_JSON = DATA / "219股票报告证据源映射" / "股票报告证据源映射预览_最新.json"
CALIBER_JSON = DATA / "220价位成交额条件口径" / "股票价位成交额条件口径预览_最新.json"
DETAIL_MD = DATA / "135分层日报" / "单股标准报告v2_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def pick_condition(caliber: dict[str, Any], name: str) -> str:
    for item in caliber.get("微信短文可用表达", []):
        if item.startswith(name):
            return item
    return ""


def build_markdown(preview: dict[str, Any]) -> str:
    lines = [
        "# 股票微信短文条件口径影子预览",
        "",
        f"- 生成时间：{preview['生成时间']}",
        f"- 样本股票：{preview['样本股票']['名称']}({preview['样本股票']['市场代码']})",
        f"- 当前结论：{preview['当前结论']}",
        "",
        "## 短文预览",
        "",
        preview["微信短文"],
        "",
        "## 字段来源",
        "",
    ]
    for item in preview["字段来源"]:
        lines.append(f"- {item['字段']}：{item['来源']}；状态={item['状态']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in preview["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    evidence = load_json(EVIDENCE_JSON, {})
    caliber = load_json(CALIBER_JSON, {})
    stock = caliber.get("样本股票") or evidence.get("样本股票") or {"名称": "未知", "市场代码": "未知", "代码": "未知"}
    base = caliber.get("基准数据", {})
    current_price = str(base.get("当前价", "缺失"))
    support = str(base.get("承接区", "缺失"))
    amount_reliability = str(base.get("阈值可信度", "缺失"))
    detail_path = str(DETAIL_MD)

    observation = pick_condition(caliber, "观察条件")
    turn_strong = pick_condition(caliber, "转强条件")
    failure = pick_condition(caliber, "失败条件")
    amount_note = pick_condition(caliber, "成交额口径")

    stock_title = f"【{stock.get('名称', '未知')}】可观察，暂不提高优先级。"
    logic = f"逻辑：当前价{current_price}低于承接区{support}；行情字段已有公开快照支撑，但财报、公告、行业景气和事件风险仍缺正式依据。"
    risk = f"风险：正式依据缺口未补齐；{amount_note.replace('成交额口径：', '')}"
    detail = f"详情：{detail_path}"
    statement = "声明：本内容为研究分析短文，不自动交易。"
    short_text = "\n".join([
        stock_title,
        "",
        logic,
        "",
        observation,
        "",
        turn_strong,
        "",
        failure,
        "",
        risk,
        "",
        detail,
        "",
        statement,
    ])

    preview = {
        "名称": "股票微信短文条件口径影子预览",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "样本股票": stock,
        "当前结论": "微信短文条件口径影子预览已生成；短文包含结论、逻辑、观察条件、转强条件、失败条件、风险、详情和非交易声明，但不替换正式企业微信入口。",
        "读取文件": {
            "证据源映射": str(EVIDENCE_JSON),
            "价位成交额条件口径": str(CALIBER_JSON),
            "详情报告": detail_path,
        },
        "微信短文": short_text,
        "字段来源": [
            {"字段": "一句话结论", "来源": "证据源映射 + 价位口径", "状态": "影子预览"},
            {"字段": "逻辑", "来源": "证据源映射正式依据缺口 + 当前价/承接区", "状态": "明确降级"},
            {"字段": "观察条件", "来源": "价位成交额条件口径预览", "状态": "含价格、天数、金额"},
            {"字段": "转强条件", "来源": "价位成交额条件口径预览", "状态": "含连续天数、价格、金额"},
            {"字段": "失败条件", "来源": "价位成交额条件口径预览", "状态": "含风险线和修复窗口"},
            {"字段": "风险", "来源": "证据源映射缺口 + 成交额口径", "状态": f"{amount_reliability}"},
            {"字段": "详情", "来源": "本地标准报告", "状态": "保留详情入口"},
        ],
        "禁用表达检查": {
            "未裸用稳住": "稳住" not in short_text,
            "未裸用有承接": "有承接" not in short_text,
            "未裸用放量": "放量" not in short_text,
            "未裸用继续观察": "继续观察" not in short_text,
            "未承诺收益": "收益" not in short_text,
            "未出现下单动作": not any(word in short_text for word in ["下单", "自动买入", "自动卖出", "券商接口"]),
        },
        "安全边界": {
            "修改正式入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
            "本步骤仅生成微信短文影子预览": True,
        },
        "下一步计划": "先验收影子短文；通过后再评估是否把该模板接入正式微信短文生成器的影子分支，正式入口替换仍需停下报告。",
    }

    latest_json = OUT_DIR / "股票微信短文条件口径影子预览_最新.json"
    latest_md = OUT_DIR / "股票微信短文条件口径影子预览_最新.md"
    write_json(latest_json, preview)
    write_text(latest_md, build_markdown(preview))

    print(json.dumps({
        "状态": "完成",
        "样本股票": stock,
        "短文字数": len(short_text),
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
