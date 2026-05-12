# -*- coding: utf-8 -*-
"""
生成股票指标智能选择引擎产物。

作用：
1. 读取通用分析判断机制和指标智能选择规则。
2. 读取当前杰哥推荐分析方法v1市场环境。
3. 按客观环境输出当前默认方法组合、主导指标、辅助指标、降权指标和切换说明。

安全边界：只读本地配置和报告；只写本地03数据；不触发企业微信、n8n、券商接口或交易链路。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "01配置"
DATA = ROOT / "03数据"
OUT_DIR = DATA / "282股票指标智能选择引擎"

UNIVERSAL_PATH = CONFIG / "股票通用分析判断机制_v1.0.json"
SELECTOR_RULE_PATH = CONFIG / "股票指标智能选择与方法切换规则_v1.0.json"
FUSION_RULE_PATH = CONFIG / "股票分析指标方法融合规则_v1.0.json"
JIEGE_METHOD_REPORT_PATH = DATA / "280杰哥推荐分析方法v1" / "杰哥推荐分析方法v1报告_最新.json"


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


def normalize_market_state(state: str) -> str:
    text = state or "震荡市/中性市"
    if "强势" in text or "牛" in text:
        return "强势市/牛市"
    if "弱势" in text or "熊" in text:
        return "弱势市/熊市"
    return "震荡市/中性市"


def method_combinations(rule: dict[str, Any]) -> list[dict[str, Any]]:
    combos: list[dict[str, Any]] = []
    for raw in rule.get("方法组合库", []):
        if "方法组合" in raw:
            combos.append(raw)
            continue
        for name, value in raw.items():
            if isinstance(value, dict):
                item = {"方法组合": name}
                item.update(value)
                combos.append(item)
    return combos


def select_default_combo(market_state: str, question_type: str, combos: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = normalize_market_state(market_state)
    if question_type == "长期研究":
        target = "长期质量组合"
    elif question_type == "事件驱动":
        target = "事件驱动核验组合"
    elif normalized == "弱势市/熊市":
        target = "弱势防守组合"
    elif normalized == "强势市/牛市":
        target = "强趋势延续组合"
    else:
        target = "回踩不破组合"
    for combo in combos:
        if combo.get("方法组合") == target:
            return combo
    return combos[0] if combos else {}


def build_indicator_scores(
    selector_rule: dict[str, Any],
    market_state: str,
    question_type: str,
    selected_combo: dict[str, Any],
) -> list[dict[str, Any]]:
    normalized_market = normalize_market_state(market_state)
    main_set = set(selected_combo.get("主导指标", []))
    aux_set = set(selected_combo.get("辅助指标", []))
    veto_set = set(selected_combo.get("否决指标", []))

    scores: list[dict[str, Any]] = []
    for indicator in selector_rule.get("指标能力画像", []):
        name = indicator.get("指标组")
        best_env = indicator.get("最佳环境", [])
        failure_risk = indicator.get("失效风险", [])

        problem_fit = 75
        if question_type == "长期研究" and name in {"基本面与财务", "估值"}:
            problem_fit = 95
        elif question_type == "事件驱动" and name == "事件与政策":
            problem_fit = 95
        elif question_type == "推荐榜" and name in {"趋势与均线", "相对强度", "失败对照", "行业与市场宽度"}:
            problem_fit = 90

        market_fit = 70
        if normalized_market in best_env or any(normalized_market.split("/")[0] in item for item in best_env):
            market_fit = 90
        if normalized_market == "弱势市/熊市" and name in {"失败对照", "波动与回撤", "趋势与均线"}:
            market_fit = 92

        stage_fit = 90 if name in main_set else 75 if name in aux_set else 60
        data_quality = 85
        timeliness = {"快": 90, "中快": 82, "中": 75, "中慢": 65, "慢": 55}.get(indicator.get("响应速度"), 70)
        risk = 15 if failure_risk else 5
        redundancy = 5

        fit_score = (
            problem_fit * 0.25
            + market_fit * 0.25
            + stage_fit * 0.20
            + data_quality * 0.15
            + timeliness * 0.10
            - risk * 0.15
            - redundancy * 0.10
        )

        if name in veto_set or name == "失败对照":
            role = "否决/核心刹车" if name in veto_set or name == "失败对照" else "辅助"
        elif name in main_set:
            role = "主导指标"
        elif name in aux_set:
            role = "辅助指标"
        elif normalized_market == "弱势市/熊市" and name in {"事件与政策", "估值"}:
            role = "降权指标"
        else:
            role = "背景指标"

        scores.append(
            {
                "指标组": name,
                "角色": role,
                "适配分": round(fit_score, 2),
                "擅长": indicator.get("擅长"),
                "局限": indicator.get("局限"),
                "响应速度": indicator.get("响应速度"),
                "选择理由": build_reason(name, role, normalized_market, question_type),
            }
        )

    scores.sort(key=lambda item: (role_rank(item["角色"]), item["适配分"]), reverse=True)
    return scores


def role_rank(role: str) -> int:
    if role == "主导指标":
        return 4
    if role == "否决/核心刹车":
        return 3
    if role == "辅助指标":
        return 2
    if role == "背景指标":
        return 1
    return 0


def build_reason(name: str, role: str, market: str, question_type: str) -> str:
    if role == "主导指标":
        return f"当前为{market}，问题类型为{question_type}，{name}对本场景有主要解释权。"
    if role == "辅助指标":
        return f"{name}用于补充验证主导指标，不能单独推翻硬门槛。"
    if role == "否决/核心刹车":
        return f"{name}负责防错和限制结论上限，不参与简单加权投票。"
    if role == "降权指标":
        return f"{name}在当前{market}中容易失效或解释力不足，暂时降权。"
    return f"{name}保留为背景信息，等待客观环境变化后再提升角色。"


def build_switch_policy(market_state: str, selected_combo: dict[str, Any], selector_rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "当前市场状态": normalize_market_state(market_state),
        "当前方法组合": selected_combo.get("方法组合"),
        "普通切换确认": "连续2个观察周期满足触发条件，且新主导指标适配分比旧主导高10分以上。",
        "立即切换": "P0风险、失败对照、重大数据缺口、安全边界立即生效。",
        "防摇摆": selector_rule.get("方法切换机制", {}).get("防频繁摇摆", []),
        "触发条件": selector_rule.get("方法切换机制", {}).get("触发条件", []),
    }


def build_combo_quality(selected_combo: dict[str, Any], selector_rule: dict[str, Any]) -> dict[str, Any]:
    main_count = len(selected_combo.get("主导指标", []))
    aux_count = len(selected_combo.get("辅助指标", []))
    veto_count = len(selected_combo.get("否决指标", []))
    dimensions = set(selected_combo.get("主导指标", [])) | set(selected_combo.get("辅助指标", []))
    quality_checks = []
    quality_checks.append(
        {
            "标准": "主导指标数量",
            "状态": "通过" if 1 <= main_count <= 3 else "需复核",
            "说明": f"当前主导指标{main_count}组。",
        }
    )
    quality_checks.append(
        {
            "标准": "辅助指标数量",
            "状态": "通过" if 2 <= aux_count <= 5 else "需复核",
            "说明": f"当前辅助指标{aux_count}组。",
        }
    )
    quality_checks.append(
        {
            "标准": "风险闸门",
            "状态": "通过" if veto_count >= 1 else "需复核",
            "说明": f"当前否决/风险指标{veto_count}组。",
        }
    )
    quality_checks.append(
        {
            "标准": "互补性",
            "状态": "通过" if len(dimensions) >= 4 else "需复核",
            "说明": f"当前覆盖{len(dimensions)}类指标维度。",
        }
    )
    return {
        "评价标准": selector_rule.get("指标组合评价标准", []),
        "本次组合检查": quality_checks,
    }


def build_task_matrix(selector_rule: dict[str, Any], market_state: str) -> list[dict[str, Any]]:
    normalized_market = normalize_market_state(market_state)
    matrix: list[dict[str, Any]] = []
    for task in selector_rule.get("多层分析任务矩阵", []):
        main = task.get("主导指标", [])
        aux = task.get("辅助指标", [])
        veto = task.get("否决或降权", [])
        emphasis = "标准"
        if normalized_market == "弱势市/熊市" and task.get("判断线") in {"风险刹车判断", "市场环境判断"}:
            emphasis = "提高权重"
        elif normalized_market == "强势市/牛市" and task.get("判断线") in {"行业强弱判断", "行业内个股筛选"}:
            emphasis = "提高权重"
        elif normalized_market == "震荡市/中性市" and task.get("判断线") in {"行业内个股筛选", "个股趋势阶段判断", "风险刹车判断"}:
            emphasis = "提高权重"
        matrix.append(
            {
                "判断线": task.get("判断线"),
                "回答问题": task.get("回答问题"),
                "当前权重状态": emphasis,
                "主导指标": main,
                "辅助指标": aux,
                "否决或降权": veto,
                "输出": task.get("输出", []),
                "说明": build_task_reason(task.get("判断线"), normalized_market, emphasis),
            }
        )
    return matrix


def build_fusion_summary(fusion_rule: dict[str, Any]) -> dict[str, Any]:
    layers = fusion_rule.get("分析方法层", [])
    scenes = fusion_rule.get("场景到方法映射", [])
    return {
        "规则名称": fusion_rule.get("名称"),
        "版本": fusion_rule.get("版本"),
        "定位": fusion_rule.get("定位"),
        "上位原则": fusion_rule.get("上位原则", []),
        "方法层数量": len(layers),
        "场景数量": len(scenes),
        "方法层": [
            {
                "层级": item.get("层级"),
                "名称": item.get("名称"),
                "回答问题": item.get("回答问题"),
                "权限": item.get("权限"),
                "主导指标": item.get("主导指标", []),
                "辅助指标": item.get("辅助指标", []),
                "降权指标": item.get("降权指标", []),
                "否决指标": item.get("否决指标", []),
                "输出": item.get("输出", []),
            }
            for item in layers
        ],
        "场景映射": scenes,
        "结论生成规则": fusion_rule.get("结论生成规则", {}),
        "复盘学习规则": fusion_rule.get("复盘学习规则", {}),
    }


def build_task_reason(line: str | None, market: str, emphasis: str) -> str:
    if line == "市场环境判断":
        return "先判断整体环境，只决定方法宽严和风险预算，不直接替代个股判断。"
    if line == "行业强弱判断":
        return "最终落脚点要回到行业，行业顺逆风决定优先研究方向。"
    if line == "行业内个股筛选":
        return "在行业内部筛选真正强的个股，避免只被行业贝塔带动。"
    if line == "个股趋势阶段判断":
        return "判断个股结构是否处在可研究阶段，不能脱离行业和风险线。"
    if line == "量价承接判断":
        return "验证上涨或回踩是否有真实成交承接，防止尖峰异动。"
    if line == "风险刹车判断":
        return "风险刹车决定结论上限，不参与简单平均。"
    return f"当前{market}下该判断线权重状态为{emphasis}。"


def build_landing_summary(task_matrix: list[dict[str, Any]], market_state: str) -> dict[str, Any]:
    return {
        "固定落脚点": "行业以及行业中值得关注的个股",
        "当前市场只负责": "决定方法宽严、风险预算和候选数量上限",
        "行业判断负责": "决定优先研究方向和降权方向",
        "个股判断负责": "在行业内部识别真正强、风险可控、证据完整的对象",
        "趋势量价负责": "验证个股是否具备可研究结构和承接质量",
        "风险刹车负责": "决定结论上限，防止高分假象进入前台重点",
        "当前市场状态": normalize_market_state(market_state),
        "判断线数量": len(task_matrix),
    }


def make_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票指标智能选择引擎",
        "",
        f"生成时间：{report['生成时间']}",
        f"问题类型：{report['问题类型']}",
        f"市场状态：{report['市场状态']}",
        f"当前方法组合：{report['当前方法组合']['方法组合']}",
        "",
        "## 综合判断落脚点",
        "",
        f"- 固定落脚点：{report['综合落脚点']['固定落脚点']}",
        f"- 市场判断：{report['综合落脚点']['当前市场只负责']}",
        f"- 行业判断：{report['综合落脚点']['行业判断负责']}",
        f"- 个股判断：{report['综合落脚点']['个股判断负责']}",
        "",
        "## 多层分析任务矩阵",
        "",
    ]
    for item in report.get("多层分析任务矩阵", []):
        lines.append(f"### {item['判断线']}")
        lines.append(f"- 回答问题：{item['回答问题']}")
        lines.append(f"- 当前权重状态：{item['当前权重状态']}")
        lines.append(f"- 主导指标：{'、'.join(item['主导指标'])}")
        lines.append(f"- 辅助指标：{'、'.join(item['辅助指标'])}")
        lines.append(f"- 否决或降权：{'、'.join(item['否决或降权'])}")
        lines.append(f"- 说明：{item['说明']}")
        lines.append("")
    if report.get("指标方法融合"):
        fusion = report["指标方法融合"]
        lines.extend(["## 指标方法融合框架", ""])
        for principle in fusion.get("上位原则", []):
            lines.append(f"- {principle}")
        lines.append("")
        lines.append("### 方法层")
        for item in fusion.get("方法层", []):
            lines.append(
                f"- {item['层级']} {item['名称']}：{item['回答问题']}；权限：{item['权限']}"
            )
        lines.append("")
        lines.append("### 场景映射")
        for item in fusion.get("场景映射", []):
            lines.append(
                f"- {item.get('场景')}：主导层={'、'.join(item.get('主导层', []))}；输出={item.get('输出', '')}"
            )
        lines.append("")
    lines.extend(
        [
        "## 理论底座",
        "",
        ]
    )
    for item in report.get("理论底座", []):
        lines.append(f"- {item['来源学科']}：{item['系统落地']}")
    lines.extend(
        [
            "",
            "## 技术核心架构",
            "",
        ]
    )
    for item in report.get("技术核心架构", []):
        lines.append(f"- {item['层级']} {item['名称']}：{item['职责']}")
    lines.extend(
        [
            "",
            "## 主导指标",
            "",
        ]
    )
    for item in report["指标选择结果"]:
        if item["角色"] == "主导指标":
            lines.append(f"- {item['指标组']}：适配分{item['适配分']}；{item['选择理由']}")
    lines.extend(["", "## 辅助指标", ""])
    for item in report["指标选择结果"]:
        if item["角色"] == "辅助指标":
            lines.append(f"- {item['指标组']}：适配分{item['适配分']}；{item['选择理由']}")
    lines.extend(["", "## 否决或核心刹车", ""])
    for item in report["指标选择结果"]:
        if item["角色"] == "否决/核心刹车":
            lines.append(f"- {item['指标组']}：{item['选择理由']}")
    lines.extend(["", "## 组合质量检查", ""])
    for item in report["组合质量检查"]["本次组合检查"]:
        lines.append(f"- {item['标准']}：{item['状态']}；{item['说明']}")
    lines.extend(["", "## 切换机制", ""])
    lines.append(f"- 普通切换：{report['切换机制']['普通切换确认']}")
    lines.append(f"- 立即切换：{report['切换机制']['立即切换']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def main() -> None:
    selector_rule = read_json(SELECTOR_RULE_PATH, {})
    universal = read_json(UNIVERSAL_PATH, {})
    fusion_rule = read_json(FUSION_RULE_PATH, {})
    method_report = read_json(JIEGE_METHOD_REPORT_PATH, {})

    market_state = method_report.get("市场环境", {}).get("市场状态", "震荡市/中性市")
    question_type = "推荐榜"
    combos = method_combinations(selector_rule)
    selected_combo = select_default_combo(market_state, question_type, combos)
    indicator_scores = build_indicator_scores(selector_rule, market_state, question_type, selected_combo)
    task_matrix = build_task_matrix(selector_rule, market_state)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "名称": "股票指标智能选择引擎",
        "生成时间": now,
        "输入": {
            "通用分析判断机制": str(UNIVERSAL_PATH),
            "指标选择规则": str(SELECTOR_RULE_PATH),
            "指标方法融合规则": str(FUSION_RULE_PATH),
            "杰哥推荐分析方法v1报告": str(JIEGE_METHOD_REPORT_PATH),
        },
        "上位规则": {
            "名称": universal.get("名称"),
            "分析法阶": [item.get("层级") for item in universal.get("分析法阶", [])],
        },
        "理论底座": selector_rule.get("理论底座", []),
        "技术核心架构": selector_rule.get("技术核心架构", []),
        "决策数学化定义": selector_rule.get("决策数学化定义", {}),
        "综合判断框架": selector_rule.get("综合判断框架", {}),
        "指标方法融合": build_fusion_summary(fusion_rule),
        "综合落脚点": build_landing_summary(task_matrix, market_state),
        "问题类型": question_type,
        "市场状态": normalize_market_state(market_state),
        "当前方法组合": selected_combo,
        "当前方法组合说明": "这是当前推荐榜场景的默认组合，不代表整个分析系统只使用这一条组合；完整判断以多层分析任务矩阵为准。",
        "多层分析任务矩阵": task_matrix,
        "指标选择结果": indicator_scores,
        "组合质量检查": build_combo_quality(selected_combo, selector_rule),
        "切换机制": build_switch_policy(market_state, selected_combo, selector_rule),
        "复盘验证机制": selector_rule.get("复盘验证机制", {}),
        "未想到但已补充": selector_rule.get("还需补充的落地点", []),
        "安全边界": selector_rule.get("安全边界", {}),
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(OUT_DIR / f"股票指标智能选择引擎_{timestamp}.json", report)
    write_json(OUT_DIR / "股票指标智能选择引擎_最新.json", report)
    markdown = make_markdown(report)
    write_text(OUT_DIR / f"股票指标智能选择引擎_{timestamp}.md", markdown)
    write_text(OUT_DIR / "股票指标智能选择引擎_最新.md", markdown)

    print(
        json.dumps(
            {
                "结论": "完成",
                "市场状态": report["市场状态"],
                "当前方法组合": selected_combo.get("方法组合"),
                "判断线数量": len(task_matrix),
                "主导指标": [item["指标组"] for item in indicator_scores if item["角色"] == "主导指标"],
                "输出": str(OUT_DIR / "股票指标智能选择引擎_最新.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
