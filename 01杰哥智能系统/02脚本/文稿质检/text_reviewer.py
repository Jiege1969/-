# -*- coding: utf-8 -*-
"""
名称：text_reviewer.py
作用：文稿质检层第一阶段旁路审稿工具。手动输入草案，输出结构化审稿 JSON，并追加 review_records.jsonl。
触发方式：python text_reviewer.py review --draft-file <path> --doc-type <type> [--skip-model]
依赖：Python标准库；可选 Ollama qwen2.5:7b；01杰哥智能系统/03数据/文稿质检。
所属系统：01杰哥智能系统/文稿质检
输出：review_records.jsonl；03数据/文稿质检/审稿报告/文稿质检审稿报告_最新.md|json；采用稿目录。
安全边界：不触发 n8n，不发送企业微信，不替换原文，不写正式模板，不参与股票判断，不调用券商接口，不自动交易。
创建/修改记录：2026-05-03 创建；2026-05-03 增加企业微信手机端排版规则；2026-05-03 增加持仓诊断免责声明口径。
标识：text-reviewer-sidecar
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import request


DEFAULT_OLLAMA_URL = "http://127.0.0.1:29134"
DEFAULT_MODEL = "qwen2.5:7b"
RECORDS_FILE = "review_records.jsonl"
FORBIDDEN_PATTERNS = {
    "stock_code": r"\b(?:sh|sz|bj)\d{6}\b|\b\d{6}\.(?:SH|SZ|BJ)\b",
    "price": r"\b\d+(?:\.\d+)?元\b",
    "percent": r"[-+]?\d+(?:\.\d+)?%",
    "date": r"\b20\d{2}[-年/]\d{1,2}[-月/]\d{1,2}日?\b",
    "star_rating": r"⭐{1,5}|[一二三四五]星|[1-5]星",
    "risk_line": r"(?:风险观察线|跌破|站稳|参考位置|参考买点)[^\n。；;]*",
    "report_path": r"[A-Z]:\\[^\s，。；;]+|https?://[^\s，。；;]+",
    "disclaimer": r"(?:不构成投资建议|不作为买卖指令|不构成自动交易指令|仅供人工查看|研究摘要|研究信息参考)[^\n。]*",
}
WORD_BUDGETS = {
    "stock_daily_recommendation": {"min": 200, "ideal_min": 200, "ideal_max": 400, "max": 400, "label": "每日推荐简报"},
    "stock_daily_report": {"min": 200, "ideal_min": 200, "ideal_max": 400, "max": 400, "label": "每日推荐简报"},
    "stock_single_report": {"min": 300, "ideal_min": 500, "ideal_max": 800, "max": 800, "label": "单股深度分析"},
    "stock_single_analysis": {"min": 300, "ideal_min": 500, "ideal_max": 800, "max": 800, "label": "单股深度分析"},
    "stock_position_diagnosis": {"min": 200, "ideal_min": 300, "ideal_max": 500, "max": 500, "label": "持仓诊断报告"},
    "stock_holding_diagnosis": {"min": 200, "ideal_min": 300, "ideal_max": 500, "max": 500, "label": "持仓诊断报告"},
    "stock_stage_review": {"min": 400, "ideal_min": 600, "ideal_max": 1000, "max": 1000, "label": "阶段复盘总结"},
}
EMOTIONAL_FORBIDDEN_WORDS = (
    "强烈推荐",
    "一定买入",
    "必须买入",
    "马上买入",
    "立即买入",
    "满仓",
    "梭哈",
    "稳赚",
    "必涨",
    "确定上涨",
    "无脑买",
    "闭眼买",
)
SOURCE_LABELS = ("数据计算", "模型推断", "人工判断", "财报", "行情", "公告", "行业")
TITLE_STOCK_PATTERN = re.compile(r"(.{1,40})\((?:sh|sz|bj)?\d{6}\)", flags=re.I)


def smart_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return smart_root() / "03数据" / "文稿质检"


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, item: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(item, ensure_ascii=False) + "\n")


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def next_record_id(records: list[dict[str, Any]]) -> str:
    max_id = 0
    for record in records:
        text = str(record.get("id", "0"))
        if text.isdigit():
            max_id = max(max_id, int(text))
    return f"{max_id + 1:03d}"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def count_report_chars(text: str) -> int:
    """按中文报告阅读体感估算字数，剔除空白、Markdown链接外壳和图片URL。"""
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", str(text or ""))
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"https?://\S+|[A-Z]:\\[^\s，。；;]+", "", cleaned)
    cleaned = re.sub(r"\s+", "", cleaned)
    return len(cleaned)


def word_budget_for(doc_type: str) -> dict[str, Any] | None:
    key = str(doc_type or "").strip()
    if key in WORD_BUDGETS:
        return WORD_BUDGETS[key]
    if key.startswith("stock_daily"):
        return WORD_BUDGETS["stock_daily_recommendation"]
    if key.startswith("stock_single"):
        return WORD_BUDGETS["stock_single_report"]
    if "position" in key or "holding" in key or "持仓" in key:
        return WORD_BUDGETS["stock_position_diagnosis"]
    if "review" in key or "复盘" in key:
        return WORD_BUDGETS["stock_stage_review"]
    return None


def rule_review(draft: str, doc_type: str) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    mobile_advice: list[str] = []
    char_count = count_report_chars(draft)
    budget = word_budget_for(doc_type)
    link_or_image_pattern = r"https?://|[A-Z]:\\|!\[.*?\]\("
    long_lines = [
        index
        for index, line in enumerate(draft.splitlines(), start=1)
        if len(line.strip()) > 80 and not re.search(link_or_image_pattern, line)
    ]
    dense_paragraphs = [index for index, line in enumerate(draft.splitlines(), start=1) if len(line.strip()) > 120 and not re.search(r"https?://|!\[|\]\(", line)]
    table_lines = [index for index, line in enumerate(draft.splitlines(), start=1) if line.count("|") >= 3]
    link_lines = [index for index, line in enumerate(draft.splitlines(), start=1) if re.search(r"https?://|[A-Z]:\\", line)]
    if len(draft.strip()) < 80:
        issues.append({"type": "format", "position": "全文", "description": "文稿过短，可能不是完整报告。"})
    first_nonempty = next((line.strip("# 【】 \t") for line in draft.splitlines() if line.strip()), "")
    if doc_type.startswith("stock"):
        if not TITLE_STOCK_PATTERN.search(first_nonempty):
            issues.append({
                "type": "format",
                "position": "标题",
                "description": "股票报告标题应包含股票名称和代码，建议采用“股票名称(代码)：核心结论/核心逻辑”的结构。",
                "suggestion": "标题即结论，避免只写“股票分析报告”。",
            })
        elif "：" not in first_nonempty and ":" not in first_nonempty and "｜" not in first_nonempty and "-" not in first_nonempty:
            issues.append({
                "type": "readability",
                "position": "标题",
                "description": "标题已包含股票名称和代码，但缺少核心逻辑或当前判断。",
                "suggestion": "可补充“风险复核/重点关注/观察等待/核心催化”等简短结论。",
            })
    if budget:
        label = str(budget.get("label", "报告"))
        min_chars = int(budget.get("min", 0))
        ideal_min = int(budget.get("ideal_min", min_chars))
        ideal_max = int(budget.get("ideal_max", budget.get("max", 0)))
        max_chars = int(budget.get("max", ideal_max))
        if char_count > max_chars:
            issues.append({
                "type": "format",
                "position": "全文",
                "description": f"{label}约{char_count}字，超过{max_chars}字上限，建议拆成主推文和详情附件或压缩表达。",
                "suggestion": "每段只讲一个数据或一个观点；详细依据放到点击详情或附件中。",
            })
            mobile_advice.append(f"{label}建议控制在{ideal_min}-{ideal_max}字；超过{max_chars}字需拆分或精简。")
        elif char_count < min_chars:
            issues.append({
                "type": "missing_section",
                "position": "全文",
                "description": f"{label}约{char_count}字，低于{min_chars}字下限，需检查是否缺少必备栏目。",
                "suggestion": "确认是否包含结论、策略、关键位置、风险提示和免责声明。",
            })
        elif char_count > ideal_max:
            issues.append({
                "type": "readability",
                "position": "全文",
                "description": f"{label}约{char_count}字，超过{ideal_max}字最佳阅读区间，手机端可能偏长。",
                "suggestion": "优先删减重复结论、后台指标解释和证据缺口长句。",
            })
            mobile_advice.append(f"{label}最佳区间为{ideal_min}-{ideal_max}字；偏长时优先保留核心结论、关键数据和风险提示。")
    if doc_type.startswith("stock") and not re.search(FORBIDDEN_PATTERNS["stock_code"], draft, flags=re.I):
        issues.append({"type": "missing_section", "position": "全文", "description": "股票类文稿未识别到股票代码。"})
    if doc_type.startswith("stock") and not re.search(r"不构成投资建议|不作为买卖指令|不构成自动交易指令|仅供人工查看|研究信息参考", draft):
        issues.append({"type": "risk_warning", "position": "文末", "description": "股票类文稿缺少明确免责声明或买卖指令边界。"})
    if re.search(r"(建议|可以|马上|立即).{0,6}(买入|卖出|满仓|清仓)", draft):
        issues.append({"type": "risk_warning", "position": "全文", "description": "疑似把研究建议表达成交易指令。"})
    emotional_hits = [word for word in EMOTIONAL_FORBIDDEN_WORDS if word in draft]
    if emotional_hits:
        issues.append({
            "type": "risk_warning",
            "position": "全文",
            "description": f"存在情绪化或交易指令化措辞：{'、'.join(emotional_hits[:5])}。",
            "suggestion": "改为客观研究口径，例如“提高研究优先级”“进入观察池”“需继续核验”。",
        })
    if doc_type.startswith("stock"):
        source_hits = [label for label in SOURCE_LABELS if label in draft]
        if not source_hits:
            issues.append({
                "type": "logic",
                "position": "全文",
                "description": "股票报告未看到明确来源标注，建议区分数据计算、模型推断、人工判断、财报、行情、公告或行业来源。",
                "suggestion": "关键结论后补充来源标签，帮助用户判断可信程度。",
            })
    if draft.count("\n") < 4:
        issues.append({"type": "format", "position": "全文", "description": "换行较少，企业微信阅读可能拥挤。"})
    if long_lines:
        shown = "、".join(str(x) for x in long_lines[:5])
        issues.append({
            "type": "format",
            "position": f"第{shown}行",
            "description": "存在较长行，企业微信手机端窄屏可能换行凌乱。",
            "suggestion": "长链接或长句应单独成段；正文长句拆成短句，避免一行承载多个判断。",
        })
        mobile_advice.append("手机端窄屏优先：长行需要拆短；链接独立成段，不和正文混排。")
    if dense_paragraphs:
        shown = "、".join(str(x) for x in dense_paragraphs[:5])
        issues.append({
            "type": "readability",
            "position": f"第{shown}行",
            "description": "段落信息密度较高，手机端阅读压力大。",
            "suggestion": "拆成“判断/策略/风险/后续观察”短句或短列表。",
        })
        mobile_advice.append("单段不要塞入多个结论；每段优先只表达一个判断。")
    if table_lines:
        shown = "、".join(str(x) for x in table_lines[:5])
        issues.append({
            "type": "format",
            "position": f"第{shown}行",
            "description": "检测到表格样式，手机端企业微信容易错位。",
            "suggestion": "改成短列表，例如“代码：... / 判断：... / 风险：...”。",
        })
        mobile_advice.append("企业微信手机端避免 Markdown 表格和空格对齐，优先短列表。")
    if link_lines:
        mobile_advice.append("图片链接、报告链接必须保留；如显示过长，应独立放一行或放在文末，不得删除。")
    score = max(0.0, 10.0 - len(issues) * 1.5)
    return {
        "pass": not issues,
        "score": round(score, 1),
        "char_count": char_count,
        "word_budget": budget or {},
        "issues": issues,
        "mobile_layout_advice": list(dict.fromkeys(mobile_advice)),
    }


def extract_forbidden(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for name, pattern in FORBIDDEN_PATTERNS.items():
        values = sorted(set(match.group(0).strip() for match in re.finditer(pattern, text, flags=re.I)))
        result[name] = values
    return result


def compare_forbidden(original: str, revision: str) -> list[dict[str, Any]]:
    original_values = extract_forbidden(original)
    revision_values = extract_forbidden(revision)
    diffs: list[dict[str, Any]] = []
    for field, before in original_values.items():
        after = revision_values.get(field, [])
        if before != after:
            diffs.append({"field": field, "original": before, "revision": after})
    return diffs


def build_prompt(draft: str, doc_type: str, rule_result: dict[str, Any]) -> str:
    return f"""你是文稿质检员，只负责审稿，不负责决策。

【文稿类型】
{doc_type}

【硬性要求】
1. 只审表达、逻辑、可读性、排版、风险提示。
2. 不得新增、删除、替换股票名称、股票代码、价格、涨跌幅、评分、风险线、推荐等级、日期、报告链接、免责声明。
3. 不得把研究结论改写成买入、卖出、清仓、满仓等交易指令。
4. 不得添加原文没有提供的数据、事件或结论。
5. suggested_revision 必须是完整优化稿，不是摘要。
6. 企业微信文稿必须手机端优先、电脑端兼容：手机屏幕窄，长句、宽表格、多列对齐、过密段落会导致排版乱；建议使用短段落、短列表、清晰小标题，避免 Markdown 表格和依赖空格对齐。
7. 股票报告里的图片链接、报告链接和免责声明必须保留；可以调整前后位置和说明文字，但不得删除。
8. 字数控：每日推荐简报 200-400 字；单股分析 500-800 字为最佳区间且 800 字为上限；持仓诊断 300-500 字；阶段复盘 600-1000 字。超过上限应建议拆分或精简，低于下限应检查栏目缺失。
9. 每一段只讲一个数据或一个观点，不堆指标，不把多个判断塞进同一长句。
10. 标题应尽量采用“股票名称(代码)：核心结论/核心逻辑”的结构，让用户从标题就知道主要判断。
11. 关键结论应区分来源：数据计算、模型推断、人工判断、财报、行情、公告、行业；不能把模型推断写成确定事实。
12. 禁止情绪化或交易指令化措辞，例如“强烈推荐、一定买入、马上买入、满仓、稳赚、必涨、无脑买、闭眼买”。

【输出格式】
必须只输出 JSON，不能输出 Markdown，不能使用 ```json 代码块。suggested_revision 如有换行，必须在 JSON 字符串中使用 \\n 转义，格式如下：
{{
  "pass": true,
  "total_score": 0,
  "issues": [
    {{"type": "readability|format|logic|risk_warning|missing_section", "position": "第X段或全文", "description": "具体问题"}}
  ],
  "suggested_revision": "完整优化稿",
  "review_summary": "一句话说明"
}}

【规则质检初步结果】
{json.dumps(rule_result, ensure_ascii=False)}

【企业微信手机端排版经验】
昨天股票分析报告在手机端和电脑端显示不同：电脑端宽，手机端窄；手机端会把长链接、长句、表格、多列对齐挤乱。审稿时请按以下逻辑处理：
1. 图片链接、报告链接、免责声明必须保留，但要独立成段，不和正文混排。
2. 不要使用 Markdown 表格或空格对齐来表达股票信息，手机端容易错位。
3. 一段只讲一个重点；判断、策略、位置、风险、后续观察分段或短列表。
4. 关键结论放前面，技术细节留在后面或报告链接中。
5. 不能为了排版删除事实、链接、价格、代码、风险线或免责声明。
6. 字数超标时先压缩重复表达和后台指标解释，不得删除核心结论、关键价格线、风险提示和免责声明。
7. 优先使用“数据→判断→后续观察”的句式，把多个维度数据收敛为一个可执行的研究判断。

【待审稿原文】
{draft}
"""


def call_ollama(prompt: str, model: str, url: str, timeout: int) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 1400,
        },
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        f"{url.rstrip('/')}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return {"status": "success", "response": raw.get("response", ""), "raw": raw}
    except Exception as exc:
        return {"status": "failed", "response": "", "error": str(exc)}


def parse_model_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.I)
        stripped = re.sub(r"\s*```$", "", stripped)
    candidates = [stripped]
    match = re.search(r"\{.*\}", stripped, flags=re.S)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return parse_lenient_model_json(stripped)


def parse_lenient_model_json(text: str) -> dict[str, Any]:
    """Handle common local-model JSON mistakes, especially unescaped newlines in suggested_revision."""
    obj_match = re.search(r"\{.*\}", text, flags=re.S)
    source = obj_match.group(0) if obj_match else text
    result: dict[str, Any] = {}
    pass_match = re.search(r'"pass"\s*:\s*(true|false)', source, flags=re.I)
    if pass_match:
        result["pass"] = pass_match.group(1).lower() == "true"
    score_match = re.search(r'"total_score"\s*:\s*([0-9]+(?:\.[0-9]+)?)', source)
    if score_match:
        result["total_score"] = float(score_match.group(1))
    issues_match = re.search(r'"issues"\s*:\s*(\[[\s\S]*?\])\s*,\s*"suggested_revision"', source)
    if issues_match:
        try:
            result["issues"] = json.loads(issues_match.group(1))
        except json.JSONDecodeError:
            result["issues"] = []
    revision_match = re.search(r'"suggested_revision"\s*:\s*"([\s\S]*?)"\s*,\s*"review_summary"', source)
    if revision_match:
        result["suggested_revision"] = revision_match.group(1).replace('\\"', '"')
    summary_match = re.search(r'"review_summary"\s*:\s*"([\s\S]*?)"\s*\}?$', source)
    if summary_match:
        result["review_summary"] = summary_match.group(1).replace('\\"', '"')
    return result if "suggested_revision" in result else {}


def normalize_model_review(model_json: dict[str, Any], draft: str) -> dict[str, Any]:
    issues = model_json.get("issues", [])
    if not isinstance(issues, list):
        issues = [{"type": "logic", "position": "模型输出", "description": "模型 issues 字段格式异常。"}]
    normalized_issues = []
    for item in issues:
        if isinstance(item, dict):
            normalized_issues.append({
                "type": str(item.get("type", "logic")),
                "position": str(item.get("position", "全文")),
                "description": str(item.get("description", "")),
            })
    revision = str(model_json.get("suggested_revision") or "").strip() or draft
    try:
        score = float(model_json.get("total_score", 0))
    except (TypeError, ValueError):
        score = 0.0
    return {
        "pass": bool(model_json.get("pass")) and not normalized_issues,
        "total_score": max(0.0, min(10.0, round(score, 1))),
        "issues": normalized_issues,
        "suggested_revision": revision,
        "review_summary": str(model_json.get("review_summary", "")).strip(),
    }


def review_draft(args: argparse.Namespace) -> int:
    if args.draft_file:
        draft = load_text(Path(args.draft_file))
        draft_source = str(Path(args.draft_file))
    else:
        draft = args.draft_text or ""
        draft_source = "命令行文本"
    if not draft.strip():
        raise SystemExit("缺少待审稿文稿。请使用 --draft-file 或 --draft-text。")

    records_path = data_dir() / RECORDS_FILE
    records = read_records(records_path)
    record_id = next_record_id(records)
    rule_result = rule_review(draft, args.doc_type)
    model_call = {"status": "skipped", "reason": "skip_model=true"}
    model_review = {
        "pass": rule_result["pass"],
        "total_score": rule_result["score"],
        "issues": rule_result["issues"],
        "suggested_revision": draft,
        "review_summary": "仅完成规则质检，未调用本地模型。",
    }
    if not args.skip_model:
        prompt = build_prompt(draft[: args.max_chars], args.doc_type, rule_result)
        model_call = call_ollama(prompt, args.model, args.ollama_url, args.timeout)
        parsed = parse_model_json(model_call.get("response", ""))
        if parsed:
            model_review = normalize_model_review(parsed, draft)
        else:
            model_review["pass"] = False
            model_review["issues"] = rule_result["issues"] + [{
                "type": "format",
                "position": "模型输出",
                "description": "本地模型未返回可解析 JSON，已保留原文。",
            }]
            model_review["review_summary"] = "模型审稿输出不可解析，已降级为规则质检。"

    forbidden_modified = compare_forbidden(draft, model_review["suggested_revision"])
    if forbidden_modified:
        model_review["pass"] = False
        model_review["suggested_revision"] = draft
        model_review["issues"].append({
            "type": "fact_safety",
            "position": "建议稿",
            "description": "建议稿改动了禁止字段，已回退原文。",
        })

    record = {
        "id": record_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "doc_type": args.doc_type,
        "draft_source": draft_source,
        "draft_sha256": sha256_text(draft),
        "draft": draft,
        "rule_review": rule_result,
        "model": args.model if not args.skip_model else "",
        "model_call": {key: value for key, value in model_call.items() if key != "raw"},
        "review": model_review,
        "forbidden_modified": forbidden_modified,
        "status": "reviewed",
        "adopted_revision_path": "",
        "safety_boundary": {
            "是否替换原文": False,
            "是否发送企业微信": False,
            "是否触发n8n": False,
            "是否写正式模板": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    append_jsonl(records_path, record)
    output_dir = data_dir() / "审稿报告"
    output_json = output_dir / f"文稿质检审稿报告_{record_id}.json"
    output_md = output_dir / f"文稿质检审稿报告_{record_id}.md"
    write_text(output_json, json.dumps(record, ensure_ascii=False, indent=2))
    write_text(output_md, build_markdown(record))
    latest_json = output_dir / "文稿质检审稿报告_最新.json"
    latest_md = output_dir / "文稿质检审稿报告_最新.md"
    write_text(latest_json, json.dumps(record, ensure_ascii=False, indent=2))
    write_text(latest_md, build_markdown(record))
    print(json.dumps({
        "状态": "完成",
        "审稿编号": record_id,
        "是否通过": model_review["pass"],
        "总评分": model_review["total_score"],
        "禁止字段改动数": len(forbidden_modified),
        "记录库": str(records_path),
        "报告": str(output_md),
    }, ensure_ascii=False))
    return 0


def update_record_status(record_id: str, status: str) -> dict[str, Any]:
    records_path = data_dir() / RECORDS_FILE
    records = read_records(records_path)
    target = None
    for record in records:
        if str(record.get("id")) == record_id:
            target = record
            break
    if not target:
        raise SystemExit(f"未找到审稿编号：{record_id}")
    target["status"] = status
    target["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if status == "adopted":
        adopted_dir = data_dir() / "采用稿"
        adopted_path = adopted_dir / f"采用稿_{record_id}.md"
        write_text(adopted_path, target.get("review", {}).get("suggested_revision", target.get("draft", "")))
        target["adopted_revision_path"] = str(adopted_path)
    write_text(records_path, "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n")
    return target


def adopt_or_discard(args: argparse.Namespace, status: str) -> int:
    record = update_record_status(args.id, status)
    print(json.dumps({
        "状态": "完成",
        "审稿编号": args.id,
        "记录状态": record.get("status"),
        "采用稿": record.get("adopted_revision_path", ""),
    }, ensure_ascii=False))
    return 0


def build_markdown(record: dict[str, Any]) -> str:
    review = record.get("review", {})
    mobile_advice = record.get("rule_review", {}).get("mobile_layout_advice", [])
    lines = [
        f"# 文稿质检审稿报告 - {record.get('id')}",
        "",
        f"- 生成时间：{record.get('created_at')}",
        f"- 文稿类型：{record.get('doc_type')}",
        f"- 是否通过：{review.get('pass')}",
        f"- 总评分：{review.get('total_score')}/10",
        f"- 禁止字段改动数：{len(record.get('forbidden_modified', []))}",
        f"- 模型：{record.get('model') or '未调用'}",
        f"- 状态：{record.get('status')}",
        "",
        "## 问题清单",
        "",
    ]
    issues = review.get("issues", [])
    if not issues:
        lines.append("- 暂无。")
    for issue in issues:
        suggestion = f" 建议：{issue.get('suggestion')}" if issue.get("suggestion") else ""
        lines.append(f"- [{issue.get('type')}] {issue.get('position')}：{issue.get('description')}{suggestion}")
    lines.extend(["", "## 手机端排版建议", ""])
    if not mobile_advice:
        lines.append("- 暂无额外建议。")
    for item in mobile_advice:
        lines.append(f"- {item}")
    lines.extend(["", "## 审稿摘要", "", review.get("review_summary") or "无。", "", "## 建议稿", "", review.get("suggested_revision", ""), "", "## 安全边界", ""])
    for key, value in record.get("safety_boundary", {}).items():
        lines.append(f"- {key}：{value}")
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="文稿质检层第一阶段旁路审稿工具")
    subparsers = parser.add_subparsers(dest="command", required=True)
    review_parser = subparsers.add_parser("review", help="审稿并写入记录库")
    review_parser.add_argument("--draft-file", default="")
    review_parser.add_argument("--draft-text", default="")
    review_parser.add_argument("--doc-type", default="generic")
    review_parser.add_argument("--model", default=DEFAULT_MODEL)
    review_parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    review_parser.add_argument("--timeout", type=int, default=180)
    review_parser.add_argument("--max-chars", type=int, default=5000)
    review_parser.add_argument("--skip-model", action="store_true")
    review_parser.set_defaults(func=review_draft)

    adopt_parser = subparsers.add_parser("adopt", help="标记采用并生成采用稿")
    adopt_parser.add_argument("id")
    adopt_parser.set_defaults(func=lambda args: adopt_or_discard(args, "adopted"))

    discard_parser = subparsers.add_parser("discard", help="标记废弃")
    discard_parser.add_argument("id")
    discard_parser.set_defaults(func=lambda args: adopt_or_discard(args, "discarded"))
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
