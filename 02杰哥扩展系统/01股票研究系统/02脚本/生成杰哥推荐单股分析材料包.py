# ============================================================
# 脚本名称：生成杰哥推荐单股分析材料包.py
# 所属系统：02杰哥扩展系统/01股票研究系统/02脚本
# 功能描述：当用户询问单只股票时，按【杰哥推荐】方法自动抓取候选评分、量价特征、
#           行业归因、强势成功样本和失败对照样本，生成后台分析材料包。
# 创建日期：2026-05-10
# 安全边界：默认只读本地数据；不触发企业微信真实发送、不触发n8n、不调用券商接口、不自动交易。
# ============================================================

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime
from pathlib import Path
from typing import Any


STOCK_ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
DATA_ROOT = STOCK_ROOT / "03数据"
OUT_DIR = DATA_ROOT / "275杰哥推荐单股分析材料包"

SIMILARITY_PATH = DATA_ROOT / "270杰哥推荐方法内核" / "当前候选股相似度识别_最新.json"
CALIBRATION_PATH = DATA_ROOT / "278杰哥推荐方法内核校准" / "杰哥推荐方法内核校准报告_最新.json"
METHOD_SCORE_PATH = DATA_ROOT / "280杰哥推荐分析方法v1" / "全候选方法评分_最新.json"
STRONG_SAMPLE_PATH = DATA_ROOT / "270杰哥推荐方法内核" / "强势成功样本库_最新.json"
FAILED_SAMPLE_PATH = DATA_ROOT / "270杰哥推荐方法内核" / "失败对照样本库_最新.json"
ALL_FEATURE_PATH = DATA_ROOT / "272杰哥推荐量价特征" / "全候选量价特征_最新.json"
P0_ENHANCED_ALL_FEATURE_PATH = DATA_ROOT / "279杰哥推荐P0指标补足" / "全候选P0增强量价特征_最新.json"
STRONG_FEATURE_PATH = DATA_ROOT / "272杰哥推荐量价特征" / "强势成功样本量价特征_最新.json"
FAILED_FEATURE_PATH = DATA_ROOT / "272杰哥推荐量价特征" / "失败对照样本量价特征_最新.json"
INDUSTRY_REPORT_PATH = DATA_ROOT / "273杰哥推荐行业归因" / "杰哥推荐行业归因报告_最新.json"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def active_all_feature_path() -> Path:
    return P0_ENHANCED_ALL_FEATURE_PATH if P0_ENHANCED_ALL_FEATURE_PATH.exists() else ALL_FEATURE_PATH


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_code(value: str) -> str:
    text = str(value or "").lower().strip()
    text = text.replace(".", "").replace("_", "").replace("-", "")
    if re.fullmatch(r"\d{6}", text):
        if text.startswith(("6", "9")):
            return f"sh{text}"
        return f"sz{text}"
    if re.fullmatch(r"(sh|sz)\d{6}", text):
        return text
    if re.fullmatch(r"\d{6}(sh|sz)", text):
        return f"{text[-2:]}{text[:6]}"
    return text


def iter_records(data: Any, preferred_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]

    if isinstance(data, dict):
        for key in preferred_keys:
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    return []


def record_matches(record: dict[str, Any], query: str) -> bool:
    query_text = str(query or "").strip().lower()
    query_code = normalize_code(query_text)
    code_candidates = {
        normalize_code(str(record.get("代码", ""))),
        normalize_code(str(record.get("展示代码", ""))),
    }
    name = str(record.get("名称", "")).strip().lower()
    return (
        query_code in code_candidates
        or query_text == name
        or (query_text and query_text in name)
        or (name and name in query_text)
    )


def find_record(records: list[dict[str, Any]], query: str) -> dict[str, Any] | None:
    for record in records:
        if record_matches(record, query):
            return record
    return None


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def pick(record: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: record.get(key) for key in keys if key in record}


def feature_vector(record: dict[str, Any]) -> dict[str, float]:
    keys = (
        "20日涨跌幅",
        "60日涨跌幅",
        "120日涨跌幅",
        "250日涨跌幅",
        "成交额20_60比",
        "成交量20_60比",
        "60日最大回撤",
        "250日最大回撤",
        "250日距高点",
        "近60日放量天数",
    )
    vector = {}
    for key in keys:
        value = to_float(record.get(key))
        if value is not None:
            vector[key] = value
    return vector


def distance(a: dict[str, float], b: dict[str, float]) -> float:
    scales = {
        "20日涨跌幅": 30,
        "60日涨跌幅": 60,
        "120日涨跌幅": 100,
        "250日涨跌幅": 200,
        "成交额20_60比": 1,
        "成交量20_60比": 1,
        "60日最大回撤": 30,
        "250日最大回撤": 50,
        "250日距高点": 30,
        "近60日放量天数": 10,
    }
    common = [key for key in a if key in b]
    if not common:
        return 999999.0
    total = 0.0
    for key in common:
        scale = scales.get(key, 1)
        total += abs(a[key] - b[key]) / scale
    return total / len(common)


def nearest_samples(target: dict[str, Any], samples: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    target_vector = feature_vector(target)
    target_codes = {
        normalize_code(str(target.get("代码", ""))),
        normalize_code(str(target.get("展示代码", ""))),
    }
    ranked = []
    for sample in samples:
        sample_codes = {
            normalize_code(str(sample.get("代码", ""))),
            normalize_code(str(sample.get("展示代码", ""))),
        }
        if target_codes.intersection(sample_codes):
            continue
        sample_vector = feature_vector(sample)
        score = distance(target_vector, sample_vector)
        ranked.append((score, sample))

    ranked.sort(key=lambda item: item[0])
    result = []
    for score, sample in ranked[:limit]:
        result.append(
            {
                "名称": sample.get("名称"),
                "展示代码": sample.get("展示代码"),
                "行业": sample.get("行业"),
                "距离": round(score, 4),
                "识别结论": sample.get("识别结论") or sample.get("状态"),
                "杰哥推荐相似度分": sample.get("杰哥推荐相似度分") or sample.get("影子评分"),
                "量价摘要": pick(
                    sample,
                    (
                        "60日涨跌幅",
                        "120日涨跌幅",
                        "250日涨跌幅",
                        "成交额20_60比",
                        "250日距高点",
                        "量价模式标签",
                    ),
                ),
            }
        )
    return result


def find_industry_nodes(data: Any, industry: str) -> list[dict[str, Any]]:
    found = []
    if isinstance(data, dict):
        if data.get("行业") == industry:
            found.append(data)
        for value in data.values():
            found.extend(find_industry_nodes(value, industry))
    elif isinstance(data, list):
        for item in data:
            found.extend(find_industry_nodes(item, industry))
    return found


def build_observation(candidate: dict[str, Any] | None, feature: dict[str, Any] | None) -> dict[str, Any]:
    source = feature or candidate or {}
    score = to_float(source.get("杰哥推荐相似度分") or source.get("影子评分"))
    label = source.get("识别结论") or source.get("状态") or "待补充"
    stars = "⭐⭐⭐⭐⭐" if score and score >= 90 else "⭐⭐⭐⭐" if score and score >= 80 else "⭐⭐⭐"

    return {
        "研究分层": label,
        "综合得分": round(score, 2) if score is not None else None,
        "星级": stars,
        "行业": source.get("行业"),
        "核心提示": [
            "先用量价特征判断强弱，不先看概念讲故事。",
            "再用行业归因解释是否有板块顺风或逆风。",
            "最后对照强势成功样本和失败样本，防止只看成功案例。",
        ],
    }


def build_calibrated_observation(
    candidate: dict[str, Any] | None,
    feature: dict[str, Any] | None,
    calibration: dict[str, Any] | None,
) -> dict[str, Any]:
    observation = build_observation(candidate, feature)
    if not calibration:
        return observation
    score = to_float(calibration.get("原始分数")) or to_float(observation.get("综合得分"))
    suggestion = str(calibration.get("校准建议") or observation.get("研究分层") or "观察验证")
    p0_count = int(to_float(calibration.get("P0问题数")) or 0)
    p1_count = int(to_float(calibration.get("P1问题数")) or 0)
    if suggestion == "重点关注候选":
        stars = "⭐⭐⭐⭐⭐"
    elif suggestion == "重点关注待验证":
        stars = "⭐⭐⭐⭐"
    elif p0_count > 0:
        stars = "⭐⭐⭐"
    else:
        stars = observation.get("星级") or "⭐⭐⭐"
    issues = calibration.get("问题清单") if isinstance(calibration.get("问题清单"), list) else []
    issue_text = "；".join(str(item.get("问题") or "") for item in issues[:3] if isinstance(item, dict) and item.get("问题"))
    return {
        **observation,
        "研究分层": suggestion,
        "综合得分": score,
        "星级": stars,
        "方法内核校准": {
            "校准建议": suggestion,
            "P0问题数": p0_count,
            "P1问题数": p1_count,
            "主要问题": issue_text or "暂无P0/P1校准问题",
        },
    }


def build_material_package(query: str) -> dict[str, Any]:
    similarity_data = load_json(SIMILARITY_PATH)
    calibration_data = load_json(CALIBRATION_PATH) if CALIBRATION_PATH.exists() else {}
    method_score_data = load_json(METHOD_SCORE_PATH) if METHOD_SCORE_PATH.exists() else []
    all_feature_data = load_json(active_all_feature_path())
    strong_feature_data = load_json(STRONG_FEATURE_PATH)
    failed_feature_data = load_json(FAILED_FEATURE_PATH)
    industry_report = load_json(INDUSTRY_REPORT_PATH)

    candidates = iter_records(similarity_data, ("候选", "候选列表", "相似度结果"))
    calibrations = iter_records(calibration_data, ("全量校准明细", "重点关注候选Top", "重点关注待验证Top", "P0冲突样本Top"))
    method_scores = iter_records(method_score_data, ("全量方法评分", "方法重点候选Top", "方法待验证Top"))
    all_features = iter_records(all_feature_data, ("数据", "明细", "候选", "records"))
    strong_features = iter_records(strong_feature_data, ("样本", "数据", "明细", "records"))
    failed_features = iter_records(failed_feature_data, ("样本", "数据", "明细", "records"))

    candidate = find_record(candidates, query)
    calibration = find_record(calibrations, query)
    method_score = find_record(method_scores, query)
    feature = find_record(all_features, query)
    if not candidate and feature:
        candidate = find_record(candidates, str(feature.get("代码") or feature.get("展示代码") or feature.get("名称")))
    if not calibration and feature:
        calibration = find_record(calibrations, str(feature.get("代码") or feature.get("展示代码") or feature.get("名称")))
    if not method_score and feature:
        method_score = find_record(method_scores, str(feature.get("代码") or feature.get("展示代码") or feature.get("名称")))
    if not feature and candidate:
        feature = find_record(all_features, str(candidate.get("代码") or candidate.get("展示代码") or candidate.get("名称")))
    if not calibration and candidate:
        calibration = find_record(calibrations, str(candidate.get("代码") or candidate.get("展示代码") or candidate.get("名称")))
    if not method_score and candidate:
        method_score = find_record(method_scores, str(candidate.get("代码") or candidate.get("展示代码") or candidate.get("名称")))

    if not candidate and not feature:
        raise ValueError(f"未在当前2000只候选池中找到分析对象：{query}")

    source = feature or candidate or {}
    code = source.get("展示代码") or source.get("代码") or query
    name = source.get("名称") or query
    industry = source.get("行业")
    industry_nodes = find_industry_nodes(industry_report, industry) if industry else []

    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "方法": "杰哥推荐v3五年基础近三年方法",
        "分析对象": {
            "名称": name,
            "代码": code,
            "行业": industry,
        },
        "材料抓取顺序": [
            "候选评分与研究分层",
            "量价结构特征",
            "分析方法v1证据链",
            "方法内核校准",
            "P0增强指标",
            "行业归因",
            "强势成功样本相似对照",
            "失败对照样本风险校验",
            "前台表达建议",
        ],
        "候选评分材料": pick(
            candidate or {},
            (
                "名称",
                "代码",
                "展示代码",
                "行业",
                "识别结论",
                "杰哥推荐相似度分",
                "影子评分",
                "最新收盘",
                "最新日期",
                "量价模式标签",
            ),
        ),
        "量价特征材料": pick(
            feature or {},
            (
                "最新收盘",
                "20日涨跌幅",
                "60日涨跌幅",
                "120日涨跌幅",
                "250日涨跌幅",
                "均线多头排列",
                "成交额20_60比",
                "成交量20_60比",
                "近60日放量天数",
                "60日最大回撤",
                "250日最大回撤",
                "250日距高点",
                "60日突破",
                "量价模式标签",
                "成交量60日波动率",
                "成交额60日波动率",
                "周线趋势状态",
                "周线MA多头",
                "周线MACD向上",
                "周线收盘在MA20上",
                "行业动态强度分",
                "行业动态排名",
                "行业动态状态",
            ),
        ),
        "方法内核校准材料": pick(
            calibration or {},
            (
                "校准建议",
                "原始识别结论",
                "原始分数",
                "问题数量",
                "P0问题数",
                "P1问题数",
                "行业归因标签",
                "强势相似度",
                "失败相似度",
                "问题清单",
            ),
        ),
        "分析方法v1材料": pick(
            method_score or {},
            (
                "综合方法分",
                "方法分层",
                "方法风险等级",
                "趋势资格分",
                "强势结构分",
                "行业验证分",
                "失败对照分",
                "A股刹车分",
                "第二阶段趋势模板通过数",
                "第二阶段趋势模板总数",
                "核心门槛通过",
                "市场环境",
                "市场温度分",
                "市场平衡排名",
                "市场平衡分位",
                "市场平衡说明",
                "指标动态权重",
                "指标主辅角色",
                "权重调整说明",
                "智能分析路线",
                "250日低点涨幅",
                "250日距高点重算",
                "MA250近20日上行",
                "VCP状态",
                "行业拥挤状态",
                "结构证据",
                "行业证据",
                "失败对照证据",
                "刹车项",
                "学习标记",
            ),
        ),
        "行业归因材料": industry_nodes[:3],
        "强势成功样本对照": nearest_samples(feature or candidate or {}, strong_features, limit=5),
        "失败对照样本校验": nearest_samples(feature or candidate or {}, failed_features, limit=5),
        "后台判断提示": build_calibrated_observation(candidate, feature, calibration),
        "前台表达建议": {
            "原则": "前台只给结论、星级、行业、关注条件和证据边界；不机械堆指标。",
            "不得输出": ["买入", "卖出", "仓位", "下单", "确保上涨"],
            "必须保留": ["证据边界", "不构成投资建议", "不作为买卖指令"],
        },
        "证据边界": [
            "本材料包基于当前本地样本库、量价特征库和行业归因报告生成。",
            "公告、财报正文、行业价格、解禁减持等证据仍需继续核验。",
            "历史相似不等于未来必然，只用于研究排序和观察条件。",
        ],
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "输出交易指令": False,
        },
    }
    return package


def save_markdown(path: Path, package: dict[str, Any]) -> None:
    obj = package["分析对象"]
    hint = package["后台判断提示"]
    calibration = package.get("方法内核校准材料") if isinstance(package.get("方法内核校准材料"), dict) else {}
    method_score = package.get("分析方法v1材料") if isinstance(package.get("分析方法v1材料"), dict) else {}
    lines = [
        f"# 杰哥推荐单股分析材料包：{obj['名称']}（{obj['代码']}）",
        "",
        f"生成时间：{package['生成时间']}",
        f"行业：{obj.get('行业')}",
        "",
        "## 后台判断提示",
        f"- 研究分层：{hint.get('研究分层')}",
        f"- 综合得分：{hint.get('综合得分')}",
        f"- 星级：{hint.get('星级')}",
        "",
        "## 方法内核校准",
        f"- 校准建议：{calibration.get('校准建议', '待补充')}",
        f"- 原始识别：{calibration.get('原始识别结论', '待补充')}；原始分数：{calibration.get('原始分数', '待补充')}",
        f"- P0问题数：{calibration.get('P0问题数', 0)}；P1问题数：{calibration.get('P1问题数', 0)}",
        "",
        "## 分析方法v1",
        f"- 方法分层：{method_score.get('方法分层', '待补充')}；方法分：{method_score.get('综合方法分', '待补充')}；风险：{method_score.get('方法风险等级', '待补充')}",
        f"- 趋势资格：{method_score.get('第二阶段趋势模板通过数', '待补充')}/{method_score.get('第二阶段趋势模板总数', '待补充')}；VCP：{method_score.get('VCP状态', '待补充')}；行业拥挤：{method_score.get('行业拥挤状态', '待补充')}",
        f"- 方法法阶：核心门槛通过={method_score.get('核心门槛通过', '待补充')}；市场={method_score.get('市场环境', '待补充')}；市场分位={method_score.get('市场平衡分位', '待补充')}%",
        "",
        "## 智能分析路线",
    ]
    for item in method_score.get("智能分析路线", []) if isinstance(method_score.get("智能分析路线"), list) else []:
        lines.append(f"- {item.get('顺序')}｜{item.get('分析层')}｜{item.get('当前角色')}：{item.get('理由')}")
    roles = method_score.get("指标主辅角色") if isinstance(method_score.get("指标主辅角色"), dict) else {}
    lines.extend(["", "## 本次主辅指标"])
    for title, key in (("主指标", "本次主指标"), ("辅助指标", "本次辅助指标"), ("降权或否决指标", "本次降权或否决指标")):
        lines.append(f"- {title}：")
        for item in roles.get(key, [])[:8] if isinstance(roles.get(key), list) else []:
            lines.append(f"  - {item.get('指标')}｜{item.get('本次角色')}：{item.get('理由')}")
    lines.extend([
        "",
        "## 量价材料",
    ])
    for key, value in package["量价特征材料"].items():
        lines.append(f"- {key}：{value}")

    lines.extend(["", "## 强势成功样本对照"])
    for item in package["强势成功样本对照"]:
        lines.append(f"- {item.get('名称')}（{item.get('展示代码')}）：距离 {item.get('距离')}，行业 {item.get('行业')}")

    lines.extend(["", "## 失败对照样本校验"])
    for item in package["失败对照样本校验"]:
        lines.append(f"- {item.get('名称')}（{item.get('展示代码')}）：距离 {item.get('距离')}，行业 {item.get('行业')}")

    lines.extend(
        [
            "",
            "## 证据边界",
        ]
    )
    for item in package["证据边界"]:
        lines.append(f"- {item}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成【杰哥推荐】单股分析材料包")
    parser.add_argument("--query", required=True, help="股票名称或代码，例如：龙芯中科、sh688047、600105")
    parser.add_argument("--json", action="store_true", help="同时向控制台输出完整JSON")
    args = parser.parse_args()

    package = build_material_package(args.query)
    obj = package["分析对象"]
    safe_code = normalize_code(str(obj.get("代码") or args.query))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{safe_code}_{obj.get('名称')}_{timestamp}".replace("/", "_").replace("\\", "_")
    latest_json = OUT_DIR / "单股分析材料包_最新.json"
    latest_md = OUT_DIR / "单股分析材料包_最新.md"
    dated_json = OUT_DIR / f"{base_name}.json"
    dated_md = OUT_DIR / f"{base_name}.md"

    save_json(dated_json, package)
    save_json(latest_json, package)
    save_markdown(dated_md, package)
    save_markdown(latest_md, package)

    print(f"分析对象：{obj.get('名称')}（{obj.get('代码')}）")
    print(f"研究分层：{package['后台判断提示'].get('研究分层')}")
    print(f"综合得分：{package['后台判断提示'].get('综合得分')}")
    print(f"材料包JSON：{latest_json}")
    print(f"材料包Markdown：{latest_md}")

    if args.json:
        print(json.dumps(package, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
