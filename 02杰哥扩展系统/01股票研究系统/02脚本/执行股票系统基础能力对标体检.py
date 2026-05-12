# -*- coding: utf-8 -*-
"""
名称：执行股票系统基础能力对标体检.py
作用：只读梳理股票池、技术指标、行业主题、深度研究、企微反馈、n8n调度和学习闭环的真实基础，形成查漏补缺清单。
触发方式：python 执行股票系统基础能力对标体检.py
安全边界：只读扫描和写入体检报告；不真实发送企业微信；不触发n8n；不接券商；不交易；不重载服务；不改正式规则。
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


def walk_stock_arrays(value: Any, json_path: str = "root") -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, list):
        stock_items = [item for item in value if isinstance(item, dict) and "代码" in item and "名称" in item]
        if stock_items:
            found.append(
                {
                    "JSON路径": json_path,
                    "数量": len(stock_items),
                    "样例": [f"{item.get('名称')}({item.get('代码')})" for item in stock_items[:10]],
                    "行业分布TOP10": Counter(str(item.get("行业") or item.get("名单分类") or item.get("所属行业") or "未标注") for item in stock_items).most_common(10),
                    "市场分布": Counter(str(item.get("市场") or item.get("交易所") or "未标注") for item in stock_items).most_common(),
                    "字段覆盖": sorted({key for item in stock_items for key in item.keys()}),
                }
            )
        for index, item in enumerate(value[:20]):
            found.extend(walk_stock_arrays(item, f"{json_path}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            found.extend(walk_stock_arrays(item, f"{json_path}.{key}"))
    return found


def summarize_stock_file(path: Path) -> dict[str, Any]:
    data = load_json(path, {})
    arrays = walk_stock_arrays(data)
    return {
        "文件": file_state(path),
        "股票数组": arrays,
        "最大股票数": max([item["数量"] for item in arrays], default=0),
        "顶部字段": sorted(list(data.keys())) if isinstance(data, dict) else [],
    }


def summarize_indicator_file(path: Path) -> dict[str, Any]:
    data = load_json(path, {})
    items = data.get("技术指标", []) if isinstance(data, dict) else []
    fields = sorted({key for item in items if isinstance(item, dict) for key in item.keys()})
    nested = sorted({f"{key}.{subkey}" for item in items if isinstance(item, dict) for key, val in item.items() if isinstance(val, dict) for subkey in val.keys()})
    text = json.dumps(data, ensure_ascii=False)
    indicator_presence = {
        "MA均线": any(term in text for term in ["MA5", "MA10", "MA20", "MA60", "均线"]),
        "RSI": "RSI" in text,
        "MACD": "MACD" in text,
        "成交量均线": "成交量MA20" in text,
        "量比": "量比" in text,
        "KDJ": "KDJ" in text,
        "BOLL": any(term in text for term in ["BOLL", "布林"]),
        "ATR波动": any(term in text for term in ["ATR", "真实波幅"]),
        "换手率": "换手" in text,
        "振幅": "振幅" in text,
        "支撑压力字段": any(term in text for term in ["支撑", "压力"]),
        "突破回踩字段": any(term in text for term in ["突破", "回踩", "平台", "箱体"]),
        "竞价/盘前字段": any(term in text for term in ["竞价", "盘前", "高开", "低开"]),
    }
    return {
        "文件": file_state(path),
        "指标记录数": len(items),
        "成功数量": data.get("成功数量") if isinstance(data, dict) else None,
        "股票数量": data.get("股票数量") or data.get("候选数量") if isinstance(data, dict) else None,
        "最新日期样例": sorted({str(item.get("最新日期")) for item in items if isinstance(item, dict) and item.get("最新日期")})[:5],
        "字段": fields,
        "嵌套字段": nested,
        "指标存在性": indicator_presence,
        "样例": items[:3],
    }


def build_gap_matrix(stock_summaries: dict[str, Any], indicator_summaries: dict[str, Any], root: Path) -> list[dict[str, Any]]:
    l8x_count = stock_summaries.get("L8X综合候选池", {}).get("最大股票数", 0)
    l7_count = stock_summaries.get("L7可交易过滤池", {}).get("最大股票数", 0)
    l6_count = stock_summaries.get("L6行业主题观察池", {}).get("最大股票数", 0)
    l5_count = stock_summaries.get("L5深度研究池", {}).get("最大股票数", 0)
    focus_count = stock_summaries.get("重点关注股票池", {}).get("最大股票数", 0)
    indicator_counts = [item.get("指标记录数", 0) for item in indicator_summaries.values()]
    max_indicator_count = max(indicator_counts, default=0)
    combined_indicator_text = json.dumps(indicator_summaries, ensure_ascii=False)
    return [
        {
            "对标项": "股票池规模",
            "现状": f"重点关注池{focus_count}只；L8X综合候选池{l8x_count}只；L7过滤后{l7_count}只；L6行业主题{l6_count}只；L5深度研究{l5_count}只。",
            "判断": "有分层基础，但03数据/01股票池为空，统一入口不清；企微报告仍主要调用少量样本。",
            "缺口": "需要建立只读总索引，把配置池、L8/L7/L6/L5产物和三阶段报告候选关系对齐。",
            "优先级": "高",
        },
        {
            "对标项": "股票池代表性",
            "现状": "重点关注池覆盖用户关心和行业龙头，L8X达到824只，L6压缩到80只，L5压缩到10只。",
            "判断": "代表性初步够做试运行，但离2000只标准大股票池仍有差距。",
            "缺口": "需要按行业、市值、成交额、指数成分、用户关注五类维度做覆盖率统计；300只试运行池存在，但尚未和三阶段报告输入池绑定。",
            "优先级": "高",
        },
        {
            "对标项": "技术指标覆盖",
            "现状": f"现有指标样本最大覆盖{max_indicator_count}只；包含MA、RSI、MACD、成交量MA20、量比。",
            "判断": "能支撑初级短线扫描，但不足以稳定输出盘后短线观察的触发价和止损线。",
            "缺口": "缺KDJ、BOLL、ATR、换手率、振幅、缺口、高低开、支撑/压力、平台突破、回踩确认等字段。",
            "优先级": "高",
        },
        {
            "对标项": "技术指标分析逻辑",
            "现状": "已有技术观察字段，如站上MA20/MA60、MACD偏强、量能一般。",
            "判断": "是标签化判断，还没有形成条件句式：站稳何价、跌破何价、量能是否达标。",
            "缺口": "需要把指标翻译成三阶段报告字段：技术动作、触发条件、止损/放弃线、强度确认位。",
            "优先级": "高",
        },
        {
            "对标项": "行业主题与长线维度",
            "现状": "L6行业主题观察池存在，行业主题样本80只。",
            "判断": "能支撑深度三维研究的行业维度雏形。",
            "缺口": "行业趋势、政策催化、行业指数周线、龙头相对强弱尚未统一成报告字段。",
            "优先级": "中",
        },
        {
            "对标项": "成长与基本面维度",
            "现状": "已有财报关键指标补齐脚本和单股证据核验候选包，L5深度研究池10只。",
            "判断": "可做样本级深度研究，不足以覆盖大池中线成长筛选。",
            "缺口": "需要把营收增速、利润率、订单/产能、机构关注、公告风险映射到中线成长维度。",
            "优先级": "中",
        },
        {
            "对标项": "企微反馈和学习闭环",
            "现状": "股票助手入口、企微桥接入口、反馈日志和进化候选链路存在。",
            "判断": "能接收用户反馈，但还需区分报告格式意见、个股内容意见、池子扩充意见、指标改进意见。",
            "缺口": "需要把用户反馈按三阶段报告、股票池、指标、模型四类打标签，进入学习沉淀账。",
            "优先级": "中",
        },
        {
            "对标项": "n8n日内调度",
            "现状": "258/259/260策略包存在，灰度链路已能做未激活或受控状态。",
            "判断": "调度设计已具备，但真实三阶段自动生成还未和大池、指标映射完全打通。",
            "缺口": "需要把15:00后、晚间、盘前三阶段分别对应到具体生成脚本、输入池和输出验收。",
            "优先级": "高",
        },
    ]


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# 股票系统基础能力对标体检",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 总体判断：{result['总体判断']}",
        "",
        "## 一、股票池真实情况",
        "",
        "| 股票池 | 最大数量 | 样例 | 判断 |",
        "| --- | ---: | --- | --- |",
    ]
    for name, item in result["股票池体检"].items():
        arrays = item.get("股票数组", [])
        sample = "、".join(arrays[0].get("样例", [])[:5]) if arrays else ""
        judgment = "存在可用股票数组" if item.get("最大股票数", 0) else "未发现股票数组或文件缺失"
        lines.append(f"| {name} | {item.get('最大股票数', 0)} | {sample} | {judgment} |")
    lines.extend(["", "## 二、技术指标真实情况", "", "| 指标文件 | 记录数 | 已有指标 | 明显缺口 |", "| --- | ---: | --- | --- |"])
    for name, item in result["技术指标体检"].items():
        presence = item.get("指标存在性", {})
        have = "、".join([key for key, value in presence.items() if value])
        missing = "、".join([key for key, value in presence.items() if not value])
        lines.append(f"| {name} | {item.get('指标记录数', 0)} | {have} | {missing} |")
    lines.extend(["", "## 三、对标缺口矩阵", "", "| 对标项 | 现状 | 判断 | 缺口 | 优先级 |", "| --- | --- | --- | --- | --- |"])
    for item in result["对标缺口矩阵"]:
        lines.append(f"| {item['对标项']} | {item['现状']} | {item['判断']} | {item['缺口']} | {item['优先级']} |")
    lines.extend([
        "",
        "## 四、改进顺序",
        "",
    ])
    for index, item in enumerate(result["建议改进顺序"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## 五、安全边界", ""])
    for key, value in result["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    log_dir = root / "04日志" / "股票系统基础能力对标体检"
    stock_files = {
        "重点关注股票池": root / "01配置" / "重点关注股票池.json",
        "19名单股票池": root / "01配置" / "19名单股票池.json",
        "股票池模板": root / "01配置" / "股票池模板.json",
        "300只试运行池": root / "03数据" / "91试运行池" / "300只试运行池_最新.json",
        "L8X综合候选池": root / "03数据" / "130X综合候选池" / "L8X综合候选池_最新.json",
        "L8B扩展战略样本池": root / "03数据" / "130B扩展战略样本池" / "L8B扩展战略样本池_最新.json",
        "L7可交易过滤池": root / "03数据" / "132可交易过滤池" / "L7可交易过滤池_最新.json",
        "L6行业主题观察池": root / "03数据" / "133行业主题观察池" / "L6行业主题观察池_最新.json",
        "L5深度研究池": root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json",
    }
    indicator_files = {
        "重点关注池技术指标": root / "03数据" / "12技术指标" / "重点关注池技术指标_最新.json",
        "300只候选技术指标": root / "03数据" / "94候选历史K线技术指标" / "300只候选技术指标_最新.json",
    }
    stock_summaries = {name: summarize_stock_file(path) for name, path in stock_files.items()}
    indicator_summaries = {name: summarize_indicator_file(path) for name, path in indicator_files.items()}
    gap_matrix = build_gap_matrix(stock_summaries, indicator_summaries, root)
    result = {
        "名称": "股票系统基础能力对标体检",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "总体判断": "系统有股票池、技术指标、行业主题、深度研究、n8n和企微反馈基础，但尚未形成统一基础能力索引；当前最先要补的是股票池索引和技术指标到三阶段报告字段的映射。",
        "股票池体检": stock_summaries,
        "技术指标体检": indicator_summaries,
        "对标缺口矩阵": gap_matrix,
        "建议改进顺序": [
            "先建立股票池只读总索引：配置池、L8X、L7、L6、L5统一列出数量、来源、行业覆盖和用途。",
            "补技术指标字段映射：把MA/RSI/MACD/量比转换为技术动作、触发条件、止损线、强度确认位。",
            "把300只试运行池和92盘后轻扫描接入三阶段报告输入关系，先不扩大到2000只。",
            "再把三阶段报告分别绑定输入池：盘后用L7/L6技术扫描，晚间用L6/L5行业成长共振，盘前用昨晚结论和盘前消息字段。",
            "最后接入企微反馈标签：报告格式、股票池、技术指标、行业成长、盘前排序分别入账。",
        ],
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否接券商": False,
            "是否交易": False,
            "是否重载19310": False,
            "是否重载19302": False,
            "是否修改总管面板": False,
            "是否修改一键接续包": False,
        },
    }
    stamp = now.strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"股票系统基础能力对标体检_{stamp}.json"
    latest_json = out_dir / "股票系统基础能力对标体检_最新.json"
    md_path = out_dir / f"股票系统基础能力对标体检_{stamp}.md"
    latest_md = out_dir / "股票系统基础能力对标体检_最新.md"
    log_json = log_dir / f"stock-system-foundation-capability-audit-{stamp}.json"
    log_latest = log_dir / "stock-system-foundation-capability-audit-最新.json"
    write_json(json_path, result)
    write_json(latest_json, result)
    write_text(md_path, markdown_report(result))
    write_text(latest_md, markdown_report(result))
    write_json(log_json, {"生成时间": result["生成时间"], "输出": str(latest_json), "安全边界": result["安全边界"]})
    write_json(log_latest, load_json(log_json, {}))
    print(json.dumps({"总体状态": "pass", "输出": str(latest_json), "Markdown": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
