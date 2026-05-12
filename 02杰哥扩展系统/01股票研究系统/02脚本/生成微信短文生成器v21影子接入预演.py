# -*- coding: utf-8 -*-
"""
名称：生成微信短文生成器v21影子接入预演.py
作用：基于 v2.1 正式接入方案和华虹影子样板，生成微信短文生成器 v2.1 影子接入预演。
触发方式：python 生成微信短文生成器v21影子接入预演.py
所属系统：02杰哥扩展系统/01股票研究系统；复盘字段归属03进化系统；边界归属00总管。
安全边界：只读接入方案和影子样板；只写03数据/218微信短文生成器v21影子接入预演；
不修改股票助手入口.py、股票企业微信桥接入口.py、生成企业微信单股短回复.py；
不重启19300/19302；不发送企业微信；不触发n8n；不写正式库；不调用券商接口；不自动交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "218微信短文生成器v21影子接入预演"
PLAN_JSON = DATA / "217微信短文生成器v21接入方案" / "微信短文生成器v21正式接入方案_最新.json"
SHADOW_JSON = DATA / "186报告v21影子样板" / "华虹公司v21影子样板_最新.json"
SHADOW_SHORT = DATA / "186报告v21影子样板" / "华虹公司v21微信短文预览_最新.md"
FORMAL_FILES = [
    ROOT / "02脚本" / "股票助手入口.py",
    ROOT / "02脚本" / "股票企业微信桥接入口.py",
    ROOT / "02脚本" / "生成企业微信单股短回复.py",
]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_snapshot(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"路径": str(path), "存在": False, "sha256": ""}
    stat = path.stat()
    return {
        "路径": str(path),
        "存在": True,
        "大小": stat.st_size,
        "修改时间": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "sha256": sha256(path),
    }


def build_shadow_text(shadow: dict[str, Any]) -> str:
    short = shadow.get("微信短文层", {}).get("短文", "")
    if short:
        return short.strip()
    return load_text(SHADOW_SHORT).replace("# 华虹公司 v2.1 微信短文预览", "").strip()


def build_markdown(preview: dict[str, Any]) -> str:
    lines = [
        "# 微信短文生成器 v2.1 影子接入预演",
        "",
        f"- 生成时间：{preview['生成时间']}",
        f"- 当前结论：{preview['当前结论']}",
        "",
        "## 影子接入方式",
        "",
    ]
    for item in preview["影子接入方式"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 输入输出契约", ""])
    for row in preview["输入输出契约"]:
        lines.append(f"- {row['字段']}：来源 `{row['来源']}`；输出要求：{row['输出要求']}")
    lines.extend(["", "## 华虹影子短文预览", "", preview["影子短文预览"], "", "## 验收条件", ""])
    for item in preview["验收条件"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 正式入口快照", ""])
    for item in preview["正式入口快照"]:
        status = "存在" if item["存在"] else "缺失"
        lines.append(f"- {item['路径']}：{status}；sha256={item.get('sha256', '')[:12]}")
    lines.extend(["", "## 禁止动作", ""])
    for item in preview["禁止动作"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 下一步", "", preview["下一步"]])
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    plan = load_json(PLAN_JSON)
    shadow = load_json(SHADOW_JSON)
    short_text = build_shadow_text(shadow)
    field_names = [row.get("目标字段") for row in plan.get("字段映射", [])]
    formal_snapshot = [file_snapshot(path) for path in FORMAL_FILES]

    preview = {
        "名称": "微信短文生成器v21影子接入预演",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": "影子接入预演已生成；当前只允许本地预览和验收，不替换正式微信回复入口。",
        "依据文件": {
            "正式接入方案": str(PLAN_JSON),
            "华虹影子样板": str(SHADOW_JSON),
            "华虹短文预览": str(SHADOW_SHORT),
        },
        "影子接入方式": [
            "新增独立影子预演产物，先验证 v2.1 短文输入输出契约，再决定是否进入小样本对照。",
            "正式入口文件只做哈希快照，不做任何写入、替换、重启或特性开关接入。",
            "影子短文必须保留详情路径和非交易边界；长报告仍由后台样板承接。",
            "任何正式入口替换、19300/19302 重启或企业微信真实发送，仍属于必须停下报告项。"
        ],
        "输入输出契约": [
            {"字段": "一句话结论", "来源": "研究判断层.关注级别 + 股票.名称", "输出要求": "必须明确可观察/回避/低可信度等状态，不使用买卖动作。"},
            {"字段": "逻辑", "来源": "研究判断层.判断主因", "输出要求": "只写核心矛盾，不堆技术指标。"},
            {"字段": "财务", "来源": "后台完整分析层.财务与估值", "输出要求": "必须暴露关键数据缺口和估值风险。"},
            {"字段": "观察条件", "来源": "复盘字段预演.观察条件", "输出要求": "必须包含价格区间、交易日窗口、成交额阈值和口径说明。"},
            {"字段": "转强条件", "来源": "复盘字段预演.转强条件", "输出要求": "必须包含连续交易日、价格阈值和成交额金额阈值。"},
            {"字段": "失败条件", "来源": "复盘字段预演.失败条件", "输出要求": "必须包含风险线、修复期限和降级处理。"},
            {"字段": "风险", "来源": "研究判断层.估值状态 + 数据缺口", "输出要求": "不得写强推荐，不得承诺收益，不得引导下单。"},
            {"字段": "详情路径", "来源": "复盘字段预演.详情路径", "输出要求": "正式接入时保留现有详情入口，不让短文替代完整报告。"}
        ],
        "字段覆盖": field_names,
        "影子短文预览": short_text,
        "影子短文检查": {
            "包含观察条件": "观察条件" in short_text,
            "包含转强条件": "转强条件" in short_text,
            "包含失败条件": "失败条件" in short_text,
            "包含财务段": "财务" in short_text,
            "包含风险段": "风险" in short_text,
            "未出现买卖动作": not any(word in short_text for word in ["买入", "卖出", "下单", "调仓", "目标价", "收益承诺"]),
            "说明估算或待核验": ("估算" in short_text) or ("待核验" in short_text),
        },
        "正式入口快照": formal_snapshot,
        "验收条件": [
            "预演 JSON 和 Markdown 可读。",
            "6+1 字段和详情路径契约完整。",
            "影子短文包含观察、转强、失败、财务和风险段。",
            "影子短文不得包含买入、卖出、下单、调仓、目标价、收益承诺等交易或承诺表达。",
            "正式入口文件存在并只记录哈希快照，本脚本不写入这些文件。",
            "安全边界全部为 false。"
        ],
        "禁止动作": [
            "不得修改股票助手入口.py。",
            "不得修改股票企业微信桥接入口.py。",
            "不得修改生成企业微信单股短回复.py。",
            "不得重启19300。",
            "不得重启19302。",
            "不得发送企业微信真实消息。",
            "不得触发n8n。",
            "不得写正式库。",
            "不得调用券商接口、自动交易、下单、撤单、调仓。"
        ],
        "安全边界": {
            "修改正式入口": False,
            "重启19300": False,
            "重启19302": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False
        },
        "下一步": "运行影子接入预演验收；通过后进入小样本对照或模型路由与审稿能力只读审计。"
    }

    latest_json = OUT_DIR / "微信短文生成器v21影子接入预演_最新.json"
    latest_md = OUT_DIR / "微信短文生成器v21影子接入预演_最新.md"
    write_json(latest_json, preview)
    write_text(latest_md, build_markdown(preview))

    print(json.dumps({
        "状态": "完成",
        "当前结论": preview["当前结论"],
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
        "未改正式入口": True,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
