# -*- coding: utf-8 -*-
"""
名称：生成股票系统质量观察面板.py
作用：汇总股票主动研究系统最新一次闭环质量、L5构成、AI模型运行、n8n手动测试和企微阻断状态。
触发方式：python 生成股票系统质量观察面板.py
依赖：L5深度研究池、AI分析报告、交付控制台、交付自检、企微可信IP修复包、可信IP状态监测。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地状态文件；只写03数据/146质量观察面板和05入口工具bat；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-system-quality-observation-panel
"""

from __future__ import annotations

import json
import re
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


def load_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8-sig")


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
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
        "大小": path.stat().st_size if path.exists() else 0,
    }


def top_counter(items: list[str], limit: int = 5) -> list[dict[str, Any]]:
    return [{"名称": key, "数量": value} for key, value in Counter(items).most_common(limit)]


def collect_l5(l5: dict[str, Any]) -> dict[str, Any]:
    stocks = l5.get("股票池", []) or []
    industries = [str(item.get("行业") or "未分类") for item in stocks]
    user_enhance_count = sum(1 for item in stocks if item.get("是否用户增强"))
    strategic_count = sum(1 for item in stocks if item.get("是否战略样本"))
    estimated_amount_count = sum(1 for item in stocks if item.get("成交额是否估算"))
    risk_count = sum(1 for item in stocks if item.get("风险标记"))
    scores = [float(item.get("调整分") or 0) for item in stocks]
    max_industry_count = max(Counter(industries).values()) if industries else 0
    return {
        "输出数量": len(stocks),
        "目标数量": int((l5.get("选取规则") or {}).get("默认数量") or 10),
        "是否完整": bool((l5.get("数据健康度") or {}).get("是否完整")),
        "最低调整分": min(scores) if scores else None,
        "最高调整分": max(scores) if scores else None,
        "行业Top": top_counter(industries),
        "最高行业集中数量": max_industry_count,
        "用户增强数量": user_enhance_count,
        "战略样本数量": strategic_count,
        "成交额估算数量": estimated_amount_count,
        "风险标记股票数": risk_count,
    }


def collect_ai(ai: dict[str, Any]) -> dict[str, Any]:
    results = ai.get("分析结果", []) or []
    model_counter = Counter(str(item.get("model_used") or "未知") for item in results)
    fallback_count = sum(1 for item in results if item.get("is_fallback"))
    error_count = sum(1 for item in results if item.get("error_msg"))
    latencies = [int(item.get("latency_ms") or 0) for item in results if item.get("latency_ms") is not None]
    return {
        "分析数量": len(results),
        "确认股票数": int((ai.get("数据健康度") or {}).get("确认股票数") or 0),
        "模型成功数": int((ai.get("数据健康度") or {}).get("模型成功数") or 0),
        "规则兜底数": int((ai.get("数据健康度") or {}).get("规则兜底数") or 0),
        "是否完整": bool((ai.get("数据健康度") or {}).get("是否完整")),
        "本次禁用复杂模型": bool((ai.get("模型路由") or {}).get("本次禁用复杂模型")),
        "模型分布": [{"模型": key, "数量": value} for key, value in model_counter.most_common()],
        "降级数量": fallback_count,
        "错误数量": error_count,
        "平均耗时_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        "最大耗时_ms": max(latencies) if latencies else None,
    }


def collect_finance_review(review: dict[str, Any]) -> dict[str, Any]:
    if not review:
        return {
            "是否存在": False,
            "股票": "",
            "主模型": "",
            "主模型成功": False,
            "是否启用交叉对照": False,
            "交叉模型": "",
            "交叉模型成功": False,
            "禁止词命中": [],
            "生成时间": "",
        }
    stock = review.get("股票") or {}
    main = review.get("主模型结果") or {}
    cross = review.get("交叉对照结果") or {}
    text = "\n".join([
        str(main.get("text") or ""),
        str(cross.get("text") or ""),
    ])
    banned_patterns = [
        "买入", "卖出", "持有", "目标价", "仓位", "收益承诺",
        "上涨动力", "前景广阔", "利好消息", "买卖建议",
    ]
    hits = [pattern for pattern in banned_patterns if re.search(pattern, text)]
    return {
        "是否存在": True,
        "股票": f"{stock.get('名称') or ''}({stock.get('展示代码') or stock.get('代码') or ''})",
        "主模型": main.get("model_used") or "",
        "主模型成功": bool(main.get("success")),
        "是否启用交叉对照": bool(review.get("是否启用交叉对照")),
        "交叉模型": cross.get("model_used") or "",
        "交叉模型成功": bool(cross.get("success")),
        "禁止词命中": hits,
        "生成时间": review.get("生成时间") or "",
    }


def collect_report_safety(safety: dict[str, Any]) -> dict[str, Any]:
    if not safety:
        return {
            "是否存在": False,
            "安全结论": "未检查",
            "命中总数": None,
            "检查文件数": 0,
            "生成时间": "",
        }
    return {
        "是否存在": True,
        "安全结论": safety.get("安全结论") or "未知",
        "命中总数": safety.get("命中总数"),
        "检查文件数": safety.get("检查文件数") or 0,
        "生成时间": safety.get("生成时间") or "",
    }


def collect_report_data_caliber(caliber: dict[str, Any]) -> dict[str, Any]:
    if not caliber:
        return {
            "是否存在": False,
            "状态": "未检查",
            "严重问题数": None,
            "提示数": None,
            "生成时间": "",
        }
    return {
        "是否存在": True,
        "状态": caliber.get("状态") or "未知",
        "严重问题数": caliber.get("严重问题数"),
        "提示数": caliber.get("提示数"),
        "生成时间": caliber.get("生成时间") or "",
    }


def collect_trusted_ip_status(status: dict[str, Any]) -> dict[str, Any]:
    if not status:
        return {
            "是否存在": False,
            "状态": "未生成",
            "当前需放行IP": "",
            "是否命中60020": False,
            "企业微信真实发送已通过": False,
            "生成时间": "",
        }
    return {
        "是否存在": True,
        "状态": status.get("状态") or "未知",
        "当前需放行IP": status.get("当前需放行IP") or "",
        "是否命中60020": bool(status.get("是否命中60020")),
        "企业微信真实发送已通过": bool(status.get("企业微信真实发送已通过")),
        "生成时间": status.get("生成时间") or "",
    }


def collect_feedback_loop(root: Path) -> dict[str, Any]:
    feedback_path = root / "04日志" / "用户反馈" / "反馈日志.json"
    raw = load_json(feedback_path, {})
    records = raw.get("反馈记录", []) if isinstance(raw, dict) else []
    if not isinstance(records, list):
        records = []
    valid_records = [item for item in records if isinstance(item, dict)]
    lane_counter = Counter(str(item.get("学习沉淀主分类") or "未分类") for item in valid_records)
    subtype_counter = Counter(str(item.get("学习沉淀子分类") or "未分类") for item in valid_records)
    priority_counter = Counter(str(item.get("复盘优先级") or "未标注") for item in valid_records)
    latest = []
    for item in reversed(valid_records[-5:]):
        latest.append({
            "时间": item.get("时间") or item.get("记录时间") or "",
            "反馈类型": item.get("反馈类型") or "",
            "反馈内容": str(item.get("反馈内容") or "")[:80],
            "学习沉淀主分类": item.get("学习沉淀主分类") or "未分类",
            "复盘优先级": item.get("复盘优先级") or "未标注",
            "处理状态": item.get("处理状态") or "",
        })
    return {
        "反馈日志": file_state(feedback_path),
        "反馈数量": len(valid_records),
        "学习沉淀主分类分布": [{"分类": key, "数量": value} for key, value in lane_counter.most_common()],
        "学习沉淀子分类Top": [{"分类": key, "数量": value} for key, value in subtype_counter.most_common(5)],
        "复盘优先级分布": [{"优先级": key, "数量": value} for key, value in priority_counter.most_common()],
        "最近反馈": latest,
        "闭环口径": "企业微信反馈先入使用-反馈-改进闭环，再由经验候选账和复盘线吸收；不自动改正式规则。",
    }


def extract_ip(text: str) -> str:
    match = re.search(r"from ip:\s*([0-9]+(?:\.[0-9]+){3})", text or "")
    if match:
        return match.group(1)
    match = re.search(r"([0-9]+(?:\.[0-9]+){3})", text or "")
    return match.group(1) if match else ""


def build_quality_flags(
    l5_summary: dict[str, Any],
    ai_summary: dict[str, Any],
    delivery: dict[str, Any],
    finance_summary: dict[str, Any],
    safety_summary: dict[str, Any],
    data_caliber_summary: dict[str, Any],
    trusted_ip_summary: dict[str, Any],
    feedback_summary: dict[str, Any],
) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    if l5_summary["输出数量"] != l5_summary["目标数量"]:
        flags.append({"等级": "注意", "事项": f"L5输出数量为{l5_summary['输出数量']}，目标为{l5_summary['目标数量']}"})
    if not l5_summary["是否完整"]:
        flags.append({"等级": "注意", "事项": "L5数据健康度未完整"})
    if l5_summary["成交额估算数量"]:
        flags.append({"等级": "观察", "事项": f"{l5_summary['成交额估算数量']}只L5股票成交额为估算值，解读资金活跃时需保守"})
    if l5_summary["最高行业集中数量"] > 3:
        flags.append({"等级": "观察", "事项": f"L5同一行业最高集中{l5_summary['最高行业集中数量']}只，需留意行业拥挤"})
    if not ai_summary["是否完整"] or ai_summary["错误数量"]:
        flags.append({"等级": "注意", "事项": "AI报告存在不完整或错误记录"})
    if ai_summary["规则兜底数"]:
        flags.append({"等级": "观察", "事项": f"AI报告有{ai_summary['规则兜底数']}条规则兜底"})
    if ai_summary["本次禁用复杂模型"]:
        flags.append({"等级": "观察", "事项": "本次禁用复杂模型，复杂风险票未升档到deepseek-r1:32b"})
    if finance_summary.get("是否存在"):
        if not finance_summary.get("主模型成功"):
            flags.append({"等级": "注意", "事项": "金融专项复核主模型最近一次未成功"})
        if finance_summary.get("是否启用交叉对照") and not finance_summary.get("交叉模型成功"):
            flags.append({"等级": "观察", "事项": "金融专项复核交叉模型最近一次未成功"})
        if finance_summary.get("禁止词命中"):
            flags.append({"等级": "注意", "事项": f"金融专项复核命中禁用词：{','.join(finance_summary['禁止词命中'])}"})
    if safety_summary.get("是否存在"):
        hit_count = safety_summary.get("命中总数")
        if isinstance(hit_count, int) and hit_count > 0:
            flags.append({"等级": "注意", "事项": f"报告安全边界检查命中{hit_count}处，需人工复核"})
    else:
        flags.append({"等级": "观察", "事项": "报告安全边界检查尚未生成"})
    if data_caliber_summary.get("是否存在"):
        severe_count = data_caliber_summary.get("严重问题数")
        if isinstance(severe_count, int) and severe_count > 0:
            flags.append({"等级": "注意", "事项": f"报告数据口径检查存在{severe_count}个严重问题"})
    else:
        flags.append({"等级": "观察", "事项": "报告数据口径检查尚未生成"})
    if trusted_ip_summary.get("是否存在"):
        if trusted_ip_summary.get("是否命中60020") and not trusted_ip_summary.get("企业微信真实发送已通过"):
            flags.append({"等级": "阻断", "事项": f"企业微信可信IP待放行：{trusted_ip_summary.get('当前需放行IP') or '未提取到IP'}"})
    else:
        flags.append({"等级": "观察", "事项": "可信IP状态监测尚未生成"})
    if not feedback_summary.get("反馈日志", {}).get("存在"):
        flags.append({"等级": "观察", "事项": "企业微信使用反馈日志尚未生成；可用后需要从体验中继续回收问题"})
    elif not feedback_summary.get("反馈数量"):
        flags.append({"等级": "观察", "事项": "企业微信使用反馈日志存在但暂无反馈记录"})
    real_ok = bool(trusted_ip_summary.get("企业微信真实发送已通过")) or bool((delivery.get("层级验收") or {}).get("D真实灰度可用", {}).get("是否通过"))
    if not real_ok:
        flags.append({"等级": "阻断", "事项": "企业微信真实主动推送未通过，等待可信IP白名单"})
    return flags


def judge_quality_light(l5_summary: dict[str, Any], ai_summary: dict[str, Any], flags: list[dict[str, str]], rules: dict[str, Any]) -> dict[str, Any]:
    red = rules.get("红灯") or {}
    yellow = rules.get("黄灯") or {}
    target = int(l5_summary.get("目标数量") or 10)
    l5_count = int(l5_summary.get("输出数量") or 0)
    ai_success = int(ai_summary.get("模型成功数") or 0)
    ai_errors = int(ai_summary.get("错误数量") or 0)
    ai_fallback = int(ai_summary.get("规则兜底数") or 0)
    ai_downgrade = int(ai_summary.get("降级数量") or 0)
    max_industry = int(l5_summary.get("最高行业集中数量") or 0)
    blockers = [item for item in flags if item.get("等级") == "阻断"]

    red_reasons: list[str] = []
    yellow_reasons: list[str] = []

    if l5_count < int(red.get("L5输出数量低于", 5)):
        red_reasons.append(f"L5输出数量低于红灯阈值：{l5_count}")
    if ai_errors > int(red.get("AI错误数量大于", 1)):
        red_reasons.append(f"AI错误数量过高：{ai_errors}")
    if ai_fallback > int(red.get("AI规则兜底数大于", 2)):
        red_reasons.append(f"AI规则兜底数过高：{ai_fallback}")
    if ai_success < int(red.get("AI模型成功数低于", 8)):
        red_reasons.append(f"AI模型成功数过低：{ai_success}")
    if max_industry > int(red.get("最高行业集中数量大于", 4)):
        red_reasons.append(f"行业集中度过高：{max_industry}")

    if not red_reasons:
        if l5_count < target:
            yellow_reasons.append(f"L5输出数量低于目标：{l5_count}/{target}")
        if ai_fallback > int((rules.get("绿灯") or {}).get("AI规则兜底数上限", 0)):
            yellow_reasons.append(f"存在AI规则兜底：{ai_fallback}")
        if ai_downgrade > int((rules.get("绿灯") or {}).get("AI降级数量上限", 0)):
            yellow_reasons.append(f"存在AI模型降级：{ai_downgrade}")
        if ai_errors > 0:
            yellow_reasons.append(f"存在AI错误：{ai_errors}")
        if max_industry > int((rules.get("绿灯") or {}).get("最高行业集中数量上限", 3)):
            yellow_reasons.append(f"行业集中度超过绿灯阈值：{max_industry}")

    light = "红灯" if red_reasons else ("黄灯" if yellow_reasons else "绿灯")
    return {
        "灯号": light,
        "红灯原因": red_reasons,
        "黄灯原因": yellow_reasons,
        "外部阻断数量": len(blockers),
        "外部阻断事项": [item.get("事项") for item in blockers],
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统质量观察面板 - {report['生成时间']}",
        "",
        "## 一、总览",
        "",
        f"- 当前交付层级：{report['当前交付层级']}",
        f"- 质量结论：{report['质量结论']}",
        f"- 质量灯号：{report['质量灯号']['灯号']}",
        f"- 当前公网IP：`{report['当前公网IP'] or '未提取'}`",
        "",
        "## 二、L5深度研究池",
        "",
    ]
    l5 = report["L5摘要"]
    lines.extend([
        f"- 输出数量：{l5['输出数量']} / 目标 {l5['目标数量']}",
        f"- 调整分区间：{l5['最低调整分']} - {l5['最高调整分']}",
        f"- 用户增强数量：{l5['用户增强数量']}",
        f"- 战略样本数量：{l5['战略样本数量']}",
        f"- 成交额估算数量：{l5['成交额估算数量']}",
        f"- 风险标记股票数：{l5['风险标记股票数']}",
        "",
        "行业分布：",
    ])
    for item in l5["行业Top"]:
        lines.append(f"- {item['名称']}：{item['数量']}只")

    ai = report["AI摘要"]
    lines.extend([
        "",
        "## 三、AI分析运行",
        "",
        f"- 分析数量：{ai['分析数量']} / 确认 {ai['确认股票数']}",
        f"- 模型成功数：{ai['模型成功数']}",
        f"- 规则兜底数：{ai['规则兜底数']}",
        f"- 降级数量：{ai['降级数量']}",
        f"- 错误数量：{ai['错误数量']}",
        f"- 平均耗时：{ai['平均耗时_ms']} ms",
        f"- 最大耗时：{ai['最大耗时_ms']} ms",
        f"- 本次禁用复杂模型：{ai['本次禁用复杂模型']}",
        "",
        "模型分布：",
    ])
    for item in ai["模型分布"]:
        lines.append(f"- {item['模型']}：{item['数量']}条")

    finance = report["金融专项复核摘要"]
    lines.extend([
        "",
        "## 四、金融专项复核",
        "",
        f"- 是否存在最新复核：{finance['是否存在']}",
        f"- 复核股票：{finance['股票'] or '无'}",
        f"- 主模型：{finance['主模型'] or '无'}，成功：{finance['主模型成功']}",
        f"- 交叉对照：{finance['是否启用交叉对照']}，模型：{finance['交叉模型'] or '无'}，成功：{finance['交叉模型成功']}",
        f"- 禁止词命中：{', '.join(finance['禁止词命中']) if finance['禁止词命中'] else '无'}",
        f"- 生成时间：{finance['生成时间'] or '无'}",
    ])

    safety = report["报告安全边界摘要"]
    data_caliber = report["报告数据口径摘要"]
    trusted_ip = report["可信IP状态摘要"]
    feedback = report["使用反馈闭环摘要"]
    lines.extend([
        "",
        "## 五、质量观察项",
        "",
        f"- 报告安全边界：{safety['安全结论']}，命中：{safety['命中总数'] if safety['命中总数'] is not None else '未检查'}，检查文件数：{safety['检查文件数']}",
        f"- 报告数据口径：{data_caliber['状态']}，严重问题：{data_caliber['严重问题数'] if data_caliber['严重问题数'] is not None else '未检查'}，提示：{data_caliber['提示数'] if data_caliber['提示数'] is not None else '未检查'}",
        f"- 可信IP状态：{trusted_ip['状态']}；需放行IP：`{trusted_ip['当前需放行IP'] or '未提取'}`；真实发送已通过：{trusted_ip['企业微信真实发送已通过']}",
        f"- 使用反馈闭环：反馈日志{'存在' if feedback['反馈日志']['存在'] else '缺失'}，累计反馈 {feedback['反馈数量']} 条",
        "",
    ])
    light = report["质量灯号"]
    if light["红灯原因"]:
        lines.append("红灯原因：")
        for item in light["红灯原因"]:
            lines.append(f"- {item}")
    if light["黄灯原因"]:
        lines.append("黄灯原因：")
        for item in light["黄灯原因"]:
            lines.append(f"- {item}")
    if light["外部阻断事项"]:
        lines.append("外部阻断：")
        for item in light["外部阻断事项"]:
            lines.append(f"- {item}")
    lines.append("")
    for flag in report["质量观察项"]:
        lines.append(f"- [{flag['等级']}] {flag['事项']}")
    lines.extend(["", "## 六、使用反馈闭环", ""])
    lines.append(f"- 闭环口径：{feedback['闭环口径']}")
    if feedback["学习沉淀主分类分布"]:
        lines.append("- 学习沉淀主分类分布：")
        for item in feedback["学习沉淀主分类分布"]:
            lines.append(f"  - {item['分类']}：{item['数量']}条")
    else:
        lines.append("- 学习沉淀主分类分布：暂无")
    if feedback["最近反馈"]:
        lines.append("- 最近反馈：")
        for item in feedback["最近反馈"]:
            lines.append(
                f"  - {item['时间'] or '未记录时间'}｜{item['学习沉淀主分类']}｜{item['复盘优先级']}｜{item['反馈内容'] or item['反馈类型']}"
            )
    else:
        lines.append("- 最近反馈：暂无")
    lines.extend(["", "## 七、关键文件", ""])
    for name, state in report["关键文件"].items():
        lines.append(f"- {name}：{'存在' if state['存在'] else '缺失'}，`{state['路径']}`")
    lines.extend([
        "",
        "## 八、安全边界",
        "",
        "- 本面板只读分析现有结果。",
        "- 不触发n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(root: Path, target: Path) -> Path:
    bat = root / "05入口工具" / "股票系统质量观察面板_打开.bat"
    write_text(bat, f'@echo off\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    l5_path = root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json"
    ai_path = root / "03数据" / "135分层日报" / "AI分析报告_最新.json"
    control_path = root / "03数据" / "143交付控制台" / "股票系统交付控制台_最新.json"
    delivery_path = root / "03数据" / "140交付自检" / "股票系统交付自检报告_最新.json"
    ip_fix_path = root / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.md"
    finance_path = root / "03数据" / "149金融专项复核" / "股票金融专项复核_最新.json"
    safety_path = root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.json"
    data_caliber_path = root / "03数据" / "183报告数据口径检查" / "股票报告数据口径检查_最新.json"
    trusted_ip_path = root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.json"
    rules_path = root / "01配置" / "股票系统质量观察规则.json"

    l5 = load_json(l5_path, {})
    ai = load_json(ai_path, {})
    control = load_json(control_path, {})
    delivery = load_json(delivery_path, {})
    finance_review = load_json(finance_path, {})
    safety_review = load_json(safety_path, {})
    data_caliber_review = load_json(data_caliber_path, {})
    trusted_ip_status = load_json(trusted_ip_path, {})
    rules = load_json(rules_path, {})
    ip_text = load_text(ip_fix_path)

    l5_summary = collect_l5(l5)
    ai_summary = collect_ai(ai)
    finance_summary = collect_finance_review(finance_review)
    safety_summary = collect_report_safety(safety_review)
    data_caliber_summary = collect_report_data_caliber(data_caliber_review)
    trusted_ip_summary = collect_trusted_ip_status(trusted_ip_status)
    feedback_summary = collect_feedback_loop(root)
    flags = build_quality_flags(l5_summary, ai_summary, delivery, finance_summary, safety_summary, data_caliber_summary, trusted_ip_summary, feedback_summary)
    quality_light = judge_quality_light(l5_summary, ai_summary, flags, rules)
    blocking_count = sum(1 for item in flags if item["等级"] == "阻断")
    warning_count = sum(1 for item in flags if item["等级"] == "注意")
    delivery_level = (control.get("当前状态") or {}).get("交付层级") or delivery.get("当前交付层级") or "未知"
    if trusted_ip_summary.get("企业微信真实发送已通过") and "真实主动消息尚未成功" in delivery_level:
        delivery_level = delivery_level.replace("真实主动消息尚未成功", "真实主动消息已通过")
    if quality_light["灯号"] == "红灯":
        quality_conclusion = "质量红灯，需要先排查本地闭环"
    elif quality_light["灯号"] == "黄灯":
        quality_conclusion = "质量黄灯，可用但需关注"
    else:
        quality_conclusion = "可日常使用，存在外部阻断" if blocking_count else ("需关注质量问题" if warning_count else "运行质量正常")

    report = {
        "名称": "股票系统质量观察面板",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统质量观察面板.py",
        "当前交付层级": delivery_level,
        "质量结论": quality_conclusion,
        "质量灯号": quality_light,
        "当前公网IP": trusted_ip_summary.get("当前需放行IP") or extract_ip(ip_text),
        "L5摘要": l5_summary,
        "AI摘要": ai_summary,
        "金融专项复核摘要": finance_summary,
        "报告安全边界摘要": safety_summary,
        "报告数据口径摘要": data_caliber_summary,
        "可信IP状态摘要": trusted_ip_summary,
        "使用反馈闭环摘要": feedback_summary,
        "质量观察项": flags,
        "关键文件": {
            "L5深度研究池": file_state(l5_path),
            "AI分析报告": file_state(ai_path),
            "交付控制台": file_state(control_path),
            "交付自检": file_state(delivery_path),
            "可信IP修复包": file_state(ip_fix_path),
            "金融专项复核": file_state(finance_path),
            "报告安全边界检查": file_state(safety_path),
            "报告数据口径检查": file_state(data_caliber_path),
            "可信IP状态监测": file_state(trusted_ip_path),
            "使用反馈日志": feedback_summary["反馈日志"],
        },
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "146质量观察面板"
    output_json = output_dir / f"股票系统质量观察面板_{stamp}.json"
    output_md = output_dir / f"股票系统质量观察面板_{stamp}.md"
    latest_json = output_dir / "股票系统质量观察面板_最新.json"
    latest_md = output_dir / "股票系统质量观察面板_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    entry_bat = write_entry_open_bat(root, latest_md)

    print(json.dumps({
        "状态": "完成",
        "质量结论": quality_conclusion,
        "质量观察项": len(flags),
        "面板": str(latest_md),
        "入口工具": str(entry_bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
