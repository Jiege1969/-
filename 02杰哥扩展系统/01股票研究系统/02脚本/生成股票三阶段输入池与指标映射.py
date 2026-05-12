# -*- coding: utf-8 -*-
"""
名称：生成股票三阶段输入池与指标映射.py
作用：基于现有股票池和指标产物，生成三阶段报告的输入池、指标字段、可用程度和缺口映射。
安全边界：只读读取现有股票系统产物并写本地260映射；不发送企业微信；不触发n8n；不接券商；不交易。
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def first_stock_array(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        for key in ["股票池", "候选清单", "技术指标", "用户增强优先席位"]:
            value = data.get(key)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
        for value in data.values():
            found = first_stock_array(value)
            if found:
                return found
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data
    return []


def summarize_pool(name: str, path: Path, role: str) -> dict[str, Any]:
    data = load_json(path, {})
    stocks = first_stock_array(data)
    fields = sorted({key for item in stocks for key in item.keys()})
    industry_counts = Counter(str(item.get("行业") or item.get("名单分类") or item.get("所属行业") or "未标注") for item in stocks)
    return {
        "名称": name,
        "角色": role,
        "文件": file_state(path),
        "数量": len(stocks),
        "字段": fields,
        "行业分布TOP10": industry_counts.most_common(10),
        "样例": [f"{item.get('名称')}({item.get('代码')})" for item in stocks[:10]],
    }


def summarize_indicators(name: str, path: Path) -> dict[str, Any]:
    data = load_json(path, {})
    items = data.get("技术指标", []) if isinstance(data, dict) else []
    text = json.dumps(data, ensure_ascii=False)
    return {
        "名称": name,
        "文件": file_state(path),
        "数量": len(items),
        "最新日期": sorted({str(item.get("最新日期")) for item in items if item.get("最新日期")})[:3],
        "字段": sorted({key for item in items for key in item.keys()}),
        "已有指标": {
            "MA5/10/20/60": all(term in text for term in ["MA5", "MA10", "MA20", "MA60"]),
            "RSI14": "RSI14" in text,
            "MACD": "MACD" in text,
            "成交量MA20": "成交量MA20" in text,
            "量比5日": "量比5日" in text,
        },
        "缺口指标": ["KDJ", "BOLL", "ATR", "换手率", "振幅", "缺口", "支撑位", "压力位", "平台突破", "回踩确认", "竞价强弱"],
        "样例": items[:5],
    }


def build_mapping(root: Path) -> dict[str, Any]:
    pools = {
        "用户重点关注池": summarize_pool("用户重点关注池", root / "01配置" / "重点关注股票池.json", "用户偏好和长期关注入口"),
        "300只试运行池": summarize_pool("300只试运行池", root / "03数据" / "91试运行池" / "300只试运行池_最新.json", "大样本试运行基础池"),
        "300只盘后轻扫描": summarize_pool("300只盘后轻扫描", root / "03数据" / "92盘后轻扫描" / "300只试运行池盘后轻扫描_最新.json", "盘后短线初筛候选"),
        "L8X综合候选池": summarize_pool("L8X综合候选池", root / "03数据" / "130X综合候选池" / "L8X综合候选池_最新.json", "大样本综合候选底座"),
        "L7可交易过滤池": summarize_pool("L7可交易过滤池", root / "03数据" / "132可交易过滤池" / "L7可交易过滤池_最新.json", "过滤ST、低质量和不可交易样本后的候选池"),
        "L6行业主题观察池": summarize_pool("L6行业主题观察池", root / "03数据" / "133行业主题观察池" / "L6行业主题观察池_最新.json", "行业主题和长线方向入口"),
        "L5深度研究池": summarize_pool("L5深度研究池", root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json", "晚间深度研究候选"),
    }
    indicators = {
        "重点关注池技术指标": summarize_indicators("重点关注池技术指标", root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json"),
        "300只候选技术指标": summarize_indicators("300只候选技术指标", root / "03数据" / "94候选历史K线技术指标" / "300只候选技术指标_最新.json"),
    }
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "定位": "三阶段报告输入池与技术指标映射，不是交易规则，不发送企业微信。",
        "股票池分层": pools,
        "技术指标分层": indicators,
        "三阶段输入映射": {
            "盘后短线复盘": {
                "目标标题": "【收盘短线观察｜YYYY-MM-DD】",
                "主输入池": ["300只试运行池", "300只盘后轻扫描"],
                "辅助输入池": ["用户重点关注池", "L7可交易过滤池"],
                "当前可用字段": ["现价", "涨跌幅", "成交额", "流通市值", "轻扫描评分", "候选理由", "风险和降级说明", "MA", "RSI14", "MACD", "成交量MA20", "量比5日"],
                "当前不足": ["300只盘后轻扫描只有10只候选输出", "技术指标当前只覆盖重点关注19只和候选10只", "缺少支撑位/压力位/止损线的标准计算字段"],
                "可先落地方式": "先用300只盘后轻扫描候选清单生成短线观察，再用已有技术指标补充能匹配到的股票；无法匹配的股票标为指标不足，不进入高优先级。",
            },
            "晚间三维深度分析": {
                "目标标题": "【深度三维研究｜YYYY-MM-DD】",
                "主输入池": ["L6行业主题观察池", "L5深度研究池"],
                "辅助输入池": ["用户重点关注池", "300只盘后轻扫描"],
                "当前可用字段": ["行业", "细分领域", "行业强度", "资金活跃度", "用户增强优先席位", "技术结构", "财报候选证据"],
                "当前不足": ["行业指数周线趋势未统一入字段", "政策催化未结构化接入", "订单/产能/机构关注字段未统一"],
                "可先落地方式": "先输出行业主题、成长证据缺口和短线共振三段，不把缺口写成推卸责任，而是写成影响优先级的客观限制。",
            },
            "盘前出击排序": {
                "目标标题": "【盘前出击排序｜YYYY-MM-DD】",
                "主输入池": ["前一晚深度三维研究", "盘后短线复盘候选"],
                "辅助输入池": ["盘前消息字段", "竞价字段"],
                "当前可用字段": ["昨晚候选", "触发价", "止损/放弃线", "行业方向"],
                "当前不足": ["盘前突发消息、外盘、夜盘期货、集合竞价情绪尚未结构化接入"],
                "可先落地方式": "在盘前外部字段未接入前，只输出基于昨晚条件的预排序，并明确盘前消息字段为空，不编造消息。",
            },
        },
        "指标到报告语言映射": {
            "MA5/MA10/MA20/MA60": "判断短线位置、趋势层级、承接区和强弱线。",
            "MACD": "判断趋势动能是否配合，只能辅助，不单独构成关注条件。",
            "RSI14": "判断是否过热或弱势，不直接写成买卖理由。",
            "成交量MA20/量比5日": "判断放量、缩量和资金确认度，是盘后短线复盘的核心字段。",
            "现价/涨跌幅/成交额/流通市值": "判断盘后轻扫描入池、市场活跃度和样本代表性。",
            "缺失字段处理": "没有支撑压力、BOLL、ATR、换手率、竞价字段时，不允许写强确定性结论，只能给条件式观察。",
        },
        "第一轮改进结论": [
            "先不扩2000只，先把300只试运行池和92盘后轻扫描接入三阶段报告。",
            "先不追求全部指标，先把已有MA/RSI/MACD/量比翻译成触发条件和止损线。",
            "盘前报告暂不编造外盘、夜盘、突发消息和竞价情绪；这些字段未接入前，只能作为待接入项。",
            "下一步应优先生成盘后短线复盘正式样例，输入必须来自300只盘后轻扫描和现有技术指标，而不是手写3只样本。",
        ],
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否接券商": False,
            "是否交易": False,
            "是否修改正式规则": False,
        },
    }


def markdown(mapping: dict[str, Any]) -> str:
    lines = [
        "# 股票三阶段输入池与指标映射",
        "",
        f"- 生成时间：{mapping['生成时间']}",
        f"- 定位：{mapping['定位']}",
        "",
        "## 一、股票池分层",
        "",
        "| 层级 | 数量 | 角色 | 样例 |",
        "| --- | ---: | --- | --- |",
    ]
    for name, item in mapping["股票池分层"].items():
        lines.append(f"| {name} | {item['数量']} | {item['角色']} | {'、'.join(item['样例'][:5])} |")
    lines.extend(["", "## 二、技术指标分层", "", "| 指标产物 | 数量 | 已有指标 | 缺口指标 |", "| --- | ---: | --- | --- |"])
    for name, item in mapping["技术指标分层"].items():
        have = "、".join([key for key, value in item["已有指标"].items() if value])
        lines.append(f"| {name} | {item['数量']} | {have} | {'、'.join(item['缺口指标'])} |")
    lines.extend(["", "## 三、三阶段输入映射", ""])
    for stage, item in mapping["三阶段输入映射"].items():
        lines.extend([
            f"### {stage}",
            f"- 标题：{item['目标标题']}",
            f"- 主输入池：{'、'.join(item['主输入池'])}",
            f"- 辅助输入池：{'、'.join(item['辅助输入池'])}",
            f"- 当前可用字段：{'、'.join(item['当前可用字段'])}",
            f"- 当前不足：{'、'.join(item['当前不足'])}",
            f"- 可先落地方式：{item['可先落地方式']}",
            "",
        ])
    lines.extend(["## 四、指标到报告语言映射", ""])
    for key, value in mapping["指标到报告语言映射"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 五、第一轮改进结论", ""])
    for item in mapping["第一轮改进结论"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mapping = build_mapping(root)
    json_path = out_dir / f"股票三阶段输入池与指标映射_{stamp}.json"
    latest_json = out_dir / "股票三阶段输入池与指标映射_最新.json"
    md_path = out_dir / f"股票三阶段输入池与指标映射_{stamp}.md"
    latest_md = out_dir / "股票三阶段输入池与指标映射_最新.md"
    write_json(json_path, mapping)
    write_json(latest_json, mapping)
    write_text(md_path, markdown(mapping))
    write_text(latest_md, markdown(mapping))
    print(json.dumps({"总体状态": "pass", "输出": str(latest_json), "Markdown": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
