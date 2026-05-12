# -*- coding: utf-8 -*-
"""
名称：生成股票企微推送草案.py
作用：读取最新L5 AI分析报告，生成企业微信Markdown推送草案；只生成文件，不真实发送。
触发方式：python 生成股票企微推送草案.py
依赖：03数据/135分层日报/AI分析报告_最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读AI分析报告；只写03数据/136推送草案与04日志/人工闸口；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
标识：stock-wecom-push-draft-generate
"""

from __future__ import annotations

import json
import importlib.util
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any


FORBIDDEN_WORDS = ["买入", "卖出", "持有", "仓位", "目标价", "收益承诺", "保证上涨", "确定收益"]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_caliber_module() -> Any:
    path = module_root() / "02脚本" / "stock_frontend_caliber.py"
    spec = importlib.util.spec_from_file_location("stock_frontend_caliber", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载股票前台口径模块：{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_entry_config(root: Path) -> dict[str, Any]:
    path = root / "01配置" / "股票公网入口配置.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def public_base_url(root: Path) -> str:
    config = public_entry_config(root)
    return str(config.get("公网基址") or "").rstrip("/")


def public_bot_message_path(root: Path) -> str:
    config = public_entry_config(root)
    return str(config.get("智能机器人路径") or "/wecom-bot/message")


def public_stock_url(root: Path, query: str) -> str:
    path = public_bot_message_path(root)
    return f"{public_base_url(root)}{path}?{query}"


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if text.startswith(("6", "9")):
        return "sh" + text.zfill(6)
    if text.startswith(("4", "8")):
        return "bj" + text.zfill(6)
    return "sz" + text.zfill(6) if text.isdigit() else text


def load_l3_report_for_item(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("名称") or item.get("name") or "").strip()
    code = normalize_code(item.get("代码") or item.get("code") or "")
    score_dir = root / "03数据" / "245L3评分基础资产" / "单股L3评分"
    if not score_dir.exists():
        return {}
    candidates = []
    for path in score_dir.glob("*.json"):
        text = path.name.lower()
        score = 0
        if name and name in path.name:
            score += 10
        if code and code in text:
            score += 10
        if "最新" in path.name:
            score += 3
        if score:
            candidates.append((score, path.stat().st_mtime, path))
    if not candidates:
        return {}
    candidates.sort(reverse=True)
    return load_json(candidates[0][2])


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def first_sentence(text: str, max_len: int = 90) -> str:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    clean = re.sub(r"^\d+[\.\、]\s*", "", clean)
    clean = clean.lstrip("：:，,。；; ")
    parts = re.split(r"[。；;]", clean)
    sentence = parts[0].strip() if parts else clean
    if len(sentence) > max_len:
        return sentence[: max_len - 1] + "…"
    return sentence


def extract_research_summary(text: str) -> str:
    match = re.search(r"8[\.\、]\s*研究小结\s*(.*)", text, flags=re.DOTALL)
    if match:
        return first_sentence(match.group(1))
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    return first_sentence(lines[-1] if lines else "")


def chinese_date(value: Any) -> str:
    text = str(value or "").strip()
    match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if match:
        year, month, day = match.groups()
        return f"{int(year)}年{int(month)}月{int(day)}日"
    return datetime.now().strftime("%Y年%m月%d日").replace("年0", "年").replace("月0", "月")


def score_stars(score: float) -> str:
    if score >= 4.5:
        count = 5
    elif score >= 3.8:
        count = 4
    elif score >= 3.0:
        count = 3
    elif score >= 2.0:
        count = 2
    else:
        count = 1
    return "⭐" * count


def frontend_level(item: dict[str, Any]) -> str:
    report = load_l3_report_for_item(module_root(), item)
    if report.get("conclusion_text"):
        return load_caliber_module().normalize_frontend_caliber(
            raw_level=report.get("conclusion_text"),
            score=report.get("total_score"),
            confidence=(report.get("confidence", {}) or {}).get("level") if isinstance(report.get("confidence"), dict) else report.get("confidence"),
        )["研究等级"]
    score = safe_float(item.get("调整分"))
    industry = str(item.get("行业") or "")
    user_focus = bool(item.get("是否用户增强"))
    strategic = bool(item.get("是否战略样本"))
    if score >= 4.5 and (user_focus or strategic):
        return "重点研究"
    if score >= 4.25:
        return "常规研究"
    if score >= 3.8:
        return "观察"
    return "观察"


def frontend_status(item: dict[str, Any]) -> str:
    report = load_l3_report_for_item(module_root(), item)
    if report.get("conclusion_text"):
        return load_caliber_module().normalize_frontend_caliber(
            raw_level=report.get("conclusion_text"),
            score=report.get("total_score"),
            confidence=(report.get("confidence", {}) or {}).get("level") if isinstance(report.get("confidence"), dict) else report.get("confidence"),
        )["当前状态"]
    score = safe_float(item.get("调整分"))
    text = extract_research_summary(item.get("analysis_text", ""))
    if any(token in text for token in ("风险", "超买", "过热", "破位", "回撤")):
        return "风险复核"
    if score < 3.8:
        return "回避"
    if score >= 4.25:
        return "等待承接"
    return "等待转强"


def frontend_weakness(item: dict[str, Any]) -> str:
    text = extract_research_summary(item.get("analysis_text", ""))
    level = frontend_level(item)
    if "待核验" in text or "验证" in text:
        return "需要继续核验趋势持续性和证据完整度"
    if "风险" in text or "超买" in text or "过热" in text:
        return "短线风险信号需要继续观察"
    if level in {"重点研究", "常规研究"}:
        return "仍需观察资金持续性、公告财报和市场环境变化"
    return "当前条件尚未完全达到推荐标准"


def format_flags(item: dict[str, Any]) -> str:
    flags = []
    if item.get("是否用户增强"):
        flags.append("用户关注")
    if item.get("是否战略样本"):
        flags.append("战略样本")
    return f" [{' / '.join(flags)}]" if flags else ""


def stock_query_url(item: dict[str, Any], root: Path) -> str:
    code = str(item.get("代码") or "").strip()
    name = str(item.get("名称") or "").strip()
    query = f"分析{name or code}".strip()
    return public_stock_url(root, "ask=" + urllib.parse.quote(query))


def stock_query_display_url(item: dict[str, Any], root: Path) -> str:
    code = str(item.get("代码") or "").strip()
    name = str(item.get("名称") or "").strip()
    query = f"分析{name or code}".strip()
    return public_stock_url(root, "ask=" + urllib.parse.quote(query))


def stock_label(item: dict[str, Any]) -> str:
    name = str(item.get("名称") or "").strip()
    code = str(item.get("代码") or "").strip()
    label = f"{name}({code})" if code else name
    return label or "未命名股票"


def build_l5_map(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json"
    data = load_json(path)
    return {
        str(item.get("代码") or "").lower(): item
        for item in data.get("股票池", [])
        if isinstance(item, dict) and item.get("代码")
    }


def merge_runtime_item(item: dict[str, Any], l5_map: dict[str, dict[str, Any]]) -> dict[str, Any]:
    code = str(item.get("代码") or "").lower()
    merged = dict(l5_map.get(code, {}))
    merged.update(item)
    return merged


def price_text(value: Any) -> str:
    number = safe_float(value)
    return f"{number:.2f}元" if number else "-"


def daily_reference_line(item: dict[str, Any]) -> str:
    close = safe_float(item.get("收盘价") or item.get("最新价"))
    if not close:
        return "【参考价位】等待趋势、行业强度和资金活跃度继续配合；若信号转弱则进入风险复核。"
    observe = close * 0.98
    risk = close * 0.94
    pressure = close * 1.08
    return f"【参考价位】现价{price_text(close)}；观察{price_text(observe)}附近承接；若跌破{price_text(risk)}转为风险复核；站稳{price_text(pressure)}附近再看强度。"


def section_lines(title: str, body: str) -> list[str]:
    """手机企业微信会吞单换行，前台小节统一用空行隔开标题和正文。"""
    return ["", f"【{title}】：", "", str(body or "").strip(), ""]


def strip_section_label(text: str, label: str) -> str:
    prefix = f"【{label}】"
    value = str(text or "").strip()
    if value.startswith(prefix):
        return value[len(prefix):].strip()
    return value


def has_forbidden(text: str) -> list[str]:
    return [word for word in FORBIDDEN_WORDS if word in text]


def build_markdown(report: dict[str, Any], md_path: Path, l5_map: dict[str, dict[str, Any]] | None = None, root: Path | None = None) -> str:
    root = root or module_root()
    l5_map = l5_map or {}
    results = [merge_runtime_item(item, l5_map) for item in list(report.get("分析结果", []))]
    recommendations = [item for item in results if frontend_level(item) in {"重点研究", "常规研究"} and frontend_status(item) not in {"风险复核", "回避"}]
    observations = [item for item in results if item not in recommendations]
    if not observations:
        observations = [item for item in results if item not in recommendations]
    top_recommendations = recommendations[:5]
    top_observations = observations[:5]
    direction_names: list[str] = []
    for item in results:
        industry = str(item.get("行业") or "待映射").strip()
        if industry and industry not in direction_names:
            direction_names.append(industry)
        if len(direction_names) >= 3:
            break
    lines = [
        f"【股票分析报告｜行情数据截止{chinese_date(report.get('数据日期'))}】",
        "",
    ]
    if top_recommendations:
        lines.extend([
            f"杰哥，您好！根据系统分析，今日形成以下{len(top_recommendations)}只股票研究对象供您参考：",
            "",
        ])
        for index, item in enumerate(top_recommendations, start=1):
            score = safe_float(item.get("调整分"))
            label = stock_label(item)
            url = stock_query_url(item, root)
            level = frontend_level(item)
            status = frontend_status(item)
            stars = "⭐" if status in {"风险复核", "回避"} else score_stars(score)
            summary = extract_research_summary(item.get("analysis_text", ""))
            reference = strip_section_label(daily_reference_line(item), "参考价位")
            risk = f"{frontend_weakness(item)}。"
            lines.extend([
                f"{index}. [{label}]({url})：研究等级={level}；当前状态={status}{stars}",
            ])
            lines.extend(section_lines("建议策略", summary))
            lines.extend(section_lines("参考价位", reference))
            lines.extend(section_lines("主要风险", risk))
    else:
        lines.extend([
            "杰哥，您好！根据系统分析，今日暂未发现完全符合重点研究条件的股票。",
            "",
            f"当前更适合观察的方向：{'、'.join(direction_names) if direction_names else '等待下一轮行业强度刷新'}。",
            "",
        ])
    if top_observations:
        lines.append("可观察股票：")
        for index, item in enumerate(top_observations, start=1):
            if item in top_recommendations:
                continue
            score = safe_float(item.get("调整分"))
            label = stock_label(item)
            url = stock_query_url(item, root)
            level = frontend_level(item)
            status = frontend_status(item)
            stars = "⭐" if status in {"风险复核", "回避"} else score_stars(score)
            summary = extract_research_summary(item.get("analysis_text", ""))
            reference = strip_section_label(daily_reference_line(item), "参考价位")
            risk = f"主要缺口：{frontend_weakness(item)}。"
            lines.extend([
                f"{index}. [{label}]({url})：研究等级={level}；当前状态={status}{stars}",
            ])
            lines.extend(section_lines("建议策略", summary))
            lines.extend(section_lines("参考价位", reference))
            lines.extend(section_lines("主要风险", risk))
        lines.append("")
    if not top_recommendations:
        lines.extend([
            "建议：今日以观察为主，等待评分、行业强度和资金活跃度同时改善后，再进入重点研究名单。",
            "",
        ])
    lines.extend([
        "",
        "完整报告：",
        str(md_path),
        "",
        "【温馨提醒】：点击股票名称查看详细报告",
        "",
        "口径说明：研究等级只表示研究优先级，可为重点研究/常规研究/观察；当前状态只表示当下处理口径，可为等待承接/等待转强/风险复核/回避。分层排序分不等同于单股系统评分。",
        "",
        "说明：本消息为研究摘要，仅供人工查看，不构成投资建议，不作为买卖指令。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    report_path = root / "03数据" / "135分层日报" / "AI分析报告_最新.json"
    report = load_json(report_path, required=True)

    output_dir = root / "03数据" / "136推送草案"
    output_json = output_dir / f"股票企微推送草案_{stamp}.json"
    output_md = output_dir / f"股票企微推送草案_{stamp}.md"
    latest_json = output_dir / "股票企微推送草案_最新.json"
    latest_md = output_dir / "股票企微推送草案_最新.md"
    log_dir = root / "04日志" / "人工闸口"
    log_path = log_dir / f"股票企微推送草案生成日志_{stamp}.json"
    log_latest_path = log_dir / "股票企微推送草案生成日志_最新.json"

    full_report_md = Path(str(report.get("输出文件", {}).get("Markdown最新文件") or (root / "03数据" / "135分层日报" / "AI分析报告_最新.md")))
    markdown = build_markdown(report, full_report_md, build_l5_map(root), root)
    forbidden = has_forbidden(markdown)
    draft = {
        "名称": "股票企微推送草案",
        "版本": "2026-05-01",
        "定位": "企业微信Markdown推送草案，只生成文件，不真实发送。",
        "数据日期": report.get("数据日期"),
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票企微推送草案.py",
        "上游文件": str(report_path),
        "推送状态": "草案未发送",
        "是否允许真实发送": False,
        "数据健康度": {
            "摘要股票数": min(5, len(report.get("分析结果", []))),
            "上游分析股票数": len(report.get("分析结果", [])),
            "禁用词命中": forbidden,
            "是否完整": len(report.get("分析结果", [])) > 0 and not forbidden,
        },
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
        "实际动作": {
            "读取AI分析报告": True,
            "生成Markdown草案": True,
            "写入03数据": True,
            "写入04日志": True,
            "触发n8n": False,
            "企业微信真实发送": False,
            "调用券商接口": False,
            "自动交易": False,
        },
        "输出文件": {
            "JSON时间戳文件": str(output_json),
            "Markdown时间戳文件": str(output_md),
            "JSON最新文件": str(latest_json),
            "Markdown最新文件": str(latest_md),
        },
        "markdown": markdown,
    }
    write_json(output_json, draft)
    write_json(latest_json, draft)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, {
        "名称": "股票企微推送草案生成日志",
        "生成时间": draft["生成时间"],
        "数据健康度": draft["数据健康度"],
        "输出文件": draft["输出文件"],
        "安全边界": draft["安全边界"],
        "实际动作": draft["实际动作"],
    })
    write_json(log_latest_path, load_json(log_path, required=True))
    print(json.dumps({
        "状态": "完成",
        "摘要股票数": draft["数据健康度"]["摘要股票数"],
        "是否完整": draft["数据健康度"]["是否完整"],
        "禁用词命中": forbidden,
        "Markdown": str(output_md),
        "JSON": str(output_json),
    }, ensure_ascii=False))
    return 0 if draft["数据健康度"]["是否完整"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
