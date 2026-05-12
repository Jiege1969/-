# -*- coding: utf-8 -*-
"""
名称：生成环境自适应三级漏斗推荐引擎.py
作用：把市场状态、行业归因、个股方法评分和风险刹车汇总成影子推荐列表。
安全边界：只读本地数据；只写本地03数据；不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不替换正式前台。
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "01配置"
DATA = ROOT / "03数据"

RULE_PATH = CONFIG / "环境自适应三级漏斗推荐引擎_v1.0.json"
SELECTOR_PATH = DATA / "282股票指标智能选择引擎" / "股票指标智能选择引擎_最新.json"
METHOD_REPORT_PATH = DATA / "280杰哥推荐分析方法v1" / "杰哥推荐分析方法v1报告_最新.json"
METHOD_SCORE_PATH = DATA / "280杰哥推荐分析方法v1" / "全候选方法评分_最新.json"
INDUSTRY_REPORT_PATH = DATA / "273杰哥推荐行业归因" / "杰哥推荐行业归因报告_最新.json"
OUT_DIR = DATA / "283环境自适应三级漏斗推荐引擎"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def f(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def market_key(state: str) -> str:
    if "恐慌" in state:
        return "恐慌市"
    if "弱势" in state or "熊" in state:
        return "弱势市"
    if "趋势" in state or "强势" in state or "牛" in state:
        return "趋势市"
    return "震荡市"


def state_probabilities(rule: dict[str, Any], state: str) -> dict[str, float]:
    defaults = rule.get("状态概率默认值", {})
    if state in defaults:
        return defaults[state]
    key = market_key(state)
    return defaults.get(key) or defaults.get("震荡市/中性市") or {"震荡市": 1.0}


def blended_weights(rule: dict[str, Any], probs: dict[str, float]) -> dict[str, float]:
    table = rule.get("判断线权重表", {})
    weights: dict[str, float] = defaultdict(float)
    for state, prob in probs.items():
        row = table.get(state, {})
        for key, value in row.items():
            weights[key] += f(value) * f(prob)
    total = sum(weights.values()) or 1.0
    return {key: round(value / total, 4) for key, value in weights.items()}


def industry_rows(industry_report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = industry_report.get("全部行业归因")
    if isinstance(rows, list):
        return rows
    rows = []
    for key in ("强势行业Top", "弱势或降权行业Top"):
        value = industry_report.get(key)
        if isinstance(value, list):
            rows.extend(value)
    seen = set()
    unique = []
    for row in rows:
        name = row.get("行业")
        if name and name not in seen:
            seen.add(name)
            unique.append(row)
    return unique


def score_industry(row: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any]:
    industry_rule = rule.get("行业筛选规则", {})
    strong_cap = f(industry_rule.get("强势过度代表上限"), 3.0) or 3.0
    fail_cap = f(industry_rule.get("失败过度代表上限"), 4.0) or 4.0
    candidate_count = max(f(row.get("候选数")), 1.0)
    priority_rate = f(row.get("优先研究数")) / candidate_count
    watch_rate = f(row.get("观察验证数")) / candidate_count
    strong_over = f(row.get("强势过度代表指数"))
    fail_over = f(row.get("失败过度代表指数"))
    avg_score = f(row.get("平均杰哥推荐分"))
    label = str(row.get("归因标签") or "")

    label_bonus = 0
    if "强势共振" in label:
        label_bonus = 18
    elif "结构活跃" in label:
        label_bonus = 10
    elif "弱势" in label or "失败" in label:
        label_bonus = -22

    score = (
        min(strong_over / strong_cap, 1.0) * 30
        + max(0.0, 1 - min(fail_over / fail_cap, 1.0)) * 25
        + min(priority_rate, 0.4) / 0.4 * 20
        + min(watch_rate, 0.6) / 0.6 * 8
        + clamp((avg_score - 55) / 40 * 17)
        + label_bonus
    )
    score = clamp(score)

    if "弱势" in label or fail_over >= 2.5:
        layer = "暂缓行业"
    elif score >= f(industry_rule.get("顺风行业最低分"), 75):
        layer = "优先行业"
    elif score >= f(industry_rule.get("结构活跃最低分"), 60):
        layer = "结构活跃行业"
    else:
        layer = "中性观察行业"

    return {
        "行业": row.get("行业"),
        "行业漏斗分": round(score, 2),
        "行业分层": layer,
        "归因标签": label,
        "候选数": int(f(row.get("候选数"))),
        "强势样本数": int(f(row.get("强势样本数"))),
        "失败样本数": int(f(row.get("失败样本数"))),
        "优先研究数": int(f(row.get("优先研究数"))),
        "观察验证数": int(f(row.get("观察验证数"))),
        "强势过度代表指数": strong_over,
        "失败过度代表指数": fail_over,
        "行业权重建议": row.get("行业权重建议"),
        "行业风险": build_industry_risk(label, fail_over),
    }


def build_industry_risk(label: str, fail_over: float) -> str:
    if "弱势" in label or fail_over >= 2.5:
        return "失败集中或逆风"
    if fail_over >= 1.5:
        return "失败样本偏多"
    return "正常"


def median_by_industry(scores: list[dict[str, Any]]) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for item in scores:
        grouped[str(item.get("行业") or "未知")].append(f(item.get("综合方法分")))
    return {key: median(values) if values else 0.0 for key, values in grouped.items()}


def score_stock(
    item: dict[str, Any],
    industry: dict[str, Any],
    industry_median: float,
    weights: dict[str, float],
) -> dict[str, Any]:
    method_score = f(item.get("综合方法分"))
    industry_score = f(industry.get("行业漏斗分"), 45)
    trend_score = f(item.get("趋势资格分"))
    volume_score = f(item.get("强势结构分"))
    risk_score = f(item.get("失败对照分"))
    market_score = 70.0

    independent_raw = method_score - industry_median
    independent_score = clamp(55 + independent_raw * 2)
    if item.get("方法分层") == "方法重点候选":
        independent_score += 8
    independent_score = clamp(independent_score)

    line_score = (
        weights.get("市场环境", 0.1) * market_score
        + weights.get("行业强弱", 0.18) * industry_score
        + weights.get("行业内个股", 0.22) * independent_score
        + weights.get("趋势阶段", 0.18) * trend_score
        + weights.get("量价承接", 0.14) * volume_score
        + weights.get("风险刹车", 0.18) * risk_score
    )
    final_score = clamp(line_score)

    caps = conclusion_caps(item, industry)
    layer = decide_stock_layer(final_score, caps, item, industry)

    return {
        "代码": item.get("代码"),
        "展示代码": item.get("展示代码"),
        "名称": item.get("名称"),
        "行业": item.get("行业"),
        "三级漏斗分": round(final_score, 2),
        "推荐分层": layer,
        "结论上限": caps["结论上限"],
        "结论上限原因": caps["原因"],
        "行业漏斗分": round(industry_score, 2),
        "个股独立强度分": round(independent_score, 2),
        "综合方法分": method_score,
        "方法分层": item.get("方法分层"),
        "方法风险等级": item.get("方法风险等级"),
        "市场平衡分位": item.get("市场平衡分位"),
        "趋势资格分": trend_score,
        "强势结构分": volume_score,
        "行业验证分": f(item.get("行业验证分")),
        "失败对照分": risk_score,
        "核心门槛通过": bool(item.get("核心门槛通过")),
        "刹车项数量": len(item.get("刹车项") or []),
        "行业归因标签": industry.get("归因标签"),
        "行业风险": industry.get("行业风险"),
        "个股类型": classify_independent(industry, independent_score),
        "量价模式标签": item.get("量价模式标签", []),
        "复盘任务": item.get("学习标记", {}),
    }


def conclusion_caps(item: dict[str, Any], industry: dict[str, Any]) -> dict[str, Any]:
    reasons = []
    cap = "重点关注"
    if not item.get("核心门槛通过"):
        cap = "观察验证"
        reasons.append("核心门槛未通过")
    if item.get("刹车项"):
        cap = min_cap(cap, "观察验证")
        reasons.append("存在方法刹车项")
    if industry.get("行业分层") == "暂缓行业":
        cap = min_cap(cap, "观察验证")
        reasons.append("行业弱势或失败集中")
    if industry.get("行业风险") == "失败样本偏多":
        cap = min_cap(cap, "重点待验证")
        reasons.append("行业失败样本偏多")
    if item.get("方法风险等级") not in ("通过", None):
        cap = min_cap(cap, "观察验证")
        reasons.append(f"方法风险等级={item.get('方法风险等级')}")
    return {"结论上限": cap, "原因": reasons or ["无硬性上限触发"]}


def min_cap(current: str, new: str) -> str:
    order = {"重点关注": 3, "重点待验证": 2, "观察验证": 1, "暂缓": 0}
    return current if order.get(current, 0) <= order.get(new, 0) else new


def decide_stock_layer(score: float, caps: dict[str, Any], item: dict[str, Any], industry: dict[str, Any]) -> str:
    cap = caps["结论上限"]
    if score >= 82 and cap == "重点关注" and item.get("方法分层") == "方法重点候选":
        return "重点关注个股"
    if score >= 78 and cap in ("重点关注", "重点待验证"):
        return "重点待验证个股"
    if score >= 70 and cap != "暂缓":
        return "观察验证个股"
    if industry.get("行业分层") == "暂缓行业":
        return "暂缓个股"
    return "暂缓个股"


def classify_independent(industry: dict[str, Any], independent_score: float) -> str:
    if industry.get("行业分层") in ("优先行业", "结构活跃行业") and independent_score >= 65:
        return "行业强且个股独立强"
    if industry.get("行业分层") in ("优先行业", "结构活跃行业"):
        return "行业强但个股需验证"
    if independent_score >= 70:
        return "行业弱但个股独立强"
    return "行业和个股均需暂缓"


def pick_limits(rule: dict[str, Any], state_key: str) -> tuple[int, int, int]:
    industry_limit = int(rule.get("行业筛选规则", {}).get("优先行业数量上限", {}).get(state_key, 5))
    focus_limit = int(rule.get("个股筛选规则", {}).get("重点关注上限", {}).get(state_key, 8))
    watch_limit = int(rule.get("个股筛选规则", {}).get("观察验证上限", {}).get(state_key, 18))
    return industry_limit, focus_limit, watch_limit


def make_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 环境自适应三级漏斗推荐引擎",
        "",
        f"生成时间：{report['生成时间']}",
        f"运行模式：{report['运行模式']}",
        f"市场状态：{report['市场环境']['市场状态']}",
        f"主状态：{report['市场环境']['主状态']}",
        "",
        "## 前台影子摘要",
        "",
        f"- 当前模式：{report['前台影子摘要']['当前模式']}",
        f"- 优先行业：{'、'.join(report['前台影子摘要']['优先行业'])}",
        f"- 重点关注：{'、'.join(report['前台影子摘要']['重点关注'])}",
        f"- 观察验证：{'、'.join(report['前台影子摘要']['观察验证'])}",
        f"- 暂缓方向：{'、'.join(report['前台影子摘要']['暂缓方向'])}",
        f"- 风险边界：{report['前台影子摘要']['风险边界']}",
        "",
        "## 判断线权重",
        "",
    ]
    for key, value in report["判断线权重"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 优先行业", ""])
    for idx, item in enumerate(report["优先行业"], 1):
        lines.append(f"{idx}. {item['行业']}：{item['行业分层']}，行业分={item['行业漏斗分']}，风险={item['行业风险']}")
    lines.extend(["", "## 重点关注个股", ""])
    for idx, item in enumerate(report["重点关注个股"], 1):
        lines.append(
            f"{idx}. {item['名称']}({item['展示代码']})：行业={item['行业']}，"
            f"漏斗分={item['三级漏斗分']}，独立强度={item['个股独立强度分']}，上限={item['结论上限']}"
        )
    lines.extend(["", "## 观察验证个股", ""])
    for idx, item in enumerate(report["观察验证个股"][:20], 1):
        lines.append(f"{idx}. {item['名称']}({item['展示代码']})：行业={item['行业']}，分层={item['推荐分层']}，原因={';'.join(item['结论上限原因'])}")
    lines.extend(["", "## 暂缓行业", ""])
    for item in report["暂缓行业"]:
        lines.append(f"- {item['行业']}：{item['归因标签']}，失败过度代表={item['失败过度代表指数']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def build_front_shadow_summary(report_core: dict[str, Any]) -> dict[str, Any]:
    market_state = report_core["市场环境"]["市场状态"]
    state = report_core["市场环境"]["主状态"]
    if state == "趋势市":
        mode = "趋势扩散筛选"
    elif state == "弱势市":
        mode = "防守精选"
    elif state == "恐慌市":
        mode = "风险收缩"
    else:
        mode = "结构精选"

    focus_names = [item["名称"] for item in report_core["重点关注个股"][:8]]
    watch_names = [item["名称"] for item in (report_core["重点待验证个股"][:4] + report_core["观察验证个股"][:4])]
    weak_names = [item["行业"] for item in report_core["暂缓行业"][:5]]
    return {
        "当前模式": mode,
        "市场状态": market_state,
        "优先行业": [item["行业"] for item in report_core["优先行业"][:5]],
        "重点关注": focus_names,
        "观察验证": watch_names,
        "暂缓方向": weak_names,
        "风险边界": "影子运行；只做研究筛选，不输出买卖、仓位、下单或收益承诺。",
        "下次重判条件": [
            "市场状态概率明显切换",
            "行业失败集中度升高",
            "重点个股出现方法刹车项",
            "风险安全边界触发"
        ],
    }


def main() -> None:
    rule = read_json(RULE_PATH, {})
    selector = read_json(SELECTOR_PATH, {})
    method_report = read_json(METHOD_REPORT_PATH, {})
    scores = read_json(METHOD_SCORE_PATH, [])
    industry_report = read_json(INDUSTRY_REPORT_PATH, {})

    market_state = selector.get("市场状态") or method_report.get("市场环境", {}).get("市场状态") or "震荡市/中性市"
    probs = state_probabilities(rule, market_state)
    state_key = max(probs, key=lambda k: probs[k])
    weights = blended_weights(rule, probs)

    industry_scored = [score_industry(row, rule) for row in industry_rows(industry_report)]
    industry_scored.sort(key=lambda x: x["行业漏斗分"], reverse=True)
    industry_map = {row["行业"]: row for row in industry_scored}

    industry_limit, focus_limit, watch_limit = pick_limits(rule, state_key)
    priority_industries = [row for row in industry_scored if row["行业分层"] in ("优先行业", "结构活跃行业")][:industry_limit]
    weak_industries = [row for row in industry_scored if row["行业分层"] == "暂缓行业"]

    medians = median_by_industry(scores)
    stock_scored = []
    for item in scores:
        industry_name = item.get("行业") or "未知"
        industry = industry_map.get(industry_name) or {"行业": industry_name, "行业漏斗分": 45, "行业分层": "中性观察行业", "行业风险": "未知"}
        stock_scored.append(score_stock(item, industry, medians.get(str(industry_name), 0.0), weights))

    stock_scored.sort(key=lambda x: x["三级漏斗分"], reverse=True)
    focus = [item for item in stock_scored if item["推荐分层"] == "重点关注个股"][:focus_limit]
    wait_focus = [item for item in stock_scored if item["推荐分层"] == "重点待验证个股"][:focus_limit]
    watch = [item for item in stock_scored if item["推荐分层"] == "观察验证个股"][:watch_limit]
    paused = [item for item in stock_scored if item["推荐分层"] == "暂缓个股"][:50]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_core = {
        "名称": "环境自适应三级漏斗推荐引擎",
        "版本": rule.get("版本"),
        "运行模式": rule.get("运行模式", "影子运行"),
        "生成时间": now,
        "输入": {
            "规则": str(RULE_PATH),
            "指标智能选择": str(SELECTOR_PATH),
            "方法评分": str(METHOD_SCORE_PATH),
            "行业归因": str(INDUSTRY_REPORT_PATH),
        },
        "市场环境": {
            "市场状态": market_state,
            "主状态": state_key,
            "状态概率": probs,
            "说明": "v1.0使用规则默认概率；后续可升级为HMM或ICIR校正。",
        },
        "判断线权重": weights,
        "漏斗数量控制": {
            "优先行业上限": industry_limit,
            "重点关注上限": focus_limit,
            "观察验证上限": watch_limit,
        },
        "优先行业": priority_industries,
        "全部行业排序": industry_scored,
        "暂缓行业": weak_industries,
        "重点关注个股": focus,
        "重点待验证个股": wait_focus,
        "观察验证个股": watch,
        "暂缓个股样本": paused,
        "全量个股漏斗评分": stock_scored,
        "复盘任务": [
            {
                "展示代码": item["展示代码"],
                "名称": item["名称"],
                "行业": item["行业"],
                "推荐分层": item["推荐分层"],
                "复盘周期": ["5日", "20日", "60日", "120日"],
                "复盘重点": ["市场状态是否判对", "行业筛选是否有效", "个股独立强度是否有效", "风险刹车是否合理"],
            }
            for item in focus + wait_focus + watch[:10]
        ],
        "安全边界": rule.get("安全边界", {}),
    }
    report_core["前台影子摘要"] = build_front_shadow_summary(report_core)
    report = report_core

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(OUT_DIR / f"环境自适应三级漏斗推荐引擎_{timestamp}.json", report)
    write_json(OUT_DIR / "环境自适应三级漏斗推荐引擎_最新.json", report)
    markdown = make_markdown(report)
    write_text(OUT_DIR / f"环境自适应三级漏斗推荐引擎_{timestamp}.md", markdown)
    write_text(OUT_DIR / "环境自适应三级漏斗推荐引擎_最新.md", markdown)

    print(
        json.dumps(
            {
                "结论": "完成",
                "市场状态": market_state,
                "主状态": state_key,
                "优先行业数量": len(priority_industries),
                "重点关注个股数量": len(focus),
                "重点待验证个股数量": len(wait_focus),
                "观察验证个股数量": len(watch),
                "输出": str(OUT_DIR / "环境自适应三级漏斗推荐引擎_最新.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
