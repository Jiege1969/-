# -*- coding: utf-8 -*-
"""
名称：生成L5AI分析报告.py
作用：读取已人工确认的L5股票池，调用本地Ollama生成结构化AI分析报告。
触发方式：python 生成L5AI分析报告.py [--auto-confirm] [--no-complex] [--max-stocks N]
依赖：L5AI分析报告规则.json；L5人工确认结果_最新.json；L5深度研究池_最新.json；本地Ollama。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读L5和人工确认结果；只调用本地Ollama；只写03数据/135分层日报与04日志/人工闸口；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
标识：stock-l5-ai-analysis-report-generate
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if not text:
        return ""
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        if suffix.upper() == "SH":
            return f"sh{num}"
        if suffix.upper() == "SZ":
            return f"sz{num}"
        if suffix.upper() == "BJ":
            return f"bj{num}"
    if len(text) == 6 and text.isdigit():
        if text.startswith(("6", "9")):
            return f"sh{text}"
        if text.startswith(("4", "8")):
            return f"bj{text}"
        return f"sz{text}"
    return text


def available_models(ollama_url: str, timeout: int = 8) -> list[str]:
    try:
        with urllib.request.urlopen(f"{ollama_url.rstrip('/')}/api/tags", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [item.get("name") for item in payload.get("models", []) if item.get("name")]
    except Exception:  # noqa: BLE001
        return []


def strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()


def ollama_generate(ollama_url: str, model: str, prompt: str, timeout: int) -> tuple[str, int]:
    started = time.perf_counter()
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.8,
            "num_predict": 1200,
        },
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{ollama_url.rstrip('/')}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    latency_ms = int((time.perf_counter() - started) * 1000)
    return strip_think(str(payload.get("response", "")).strip()), latency_ms


def risk_count(stock: dict[str, Any]) -> int:
    flags = stock.get("风险标记", [])
    return len(flags) if isinstance(flags, list) else 0


def is_complex(stock: dict[str, Any], rule: dict[str, Any], manual_deep_codes: set[str], enable_complex: bool) -> tuple[bool, str]:
    if not enable_complex:
        return False, "复杂模型未启用"
    code = normalize_code(stock.get("代码"))
    if code in manual_deep_codes:
        return True, "人工指定深度复核"
    cond = rule.get("模型路由", {}).get("复杂触发条件", {})
    flags = stock.get("风险标记", [])
    if isinstance(flags, list) and len(flags) >= int(cond.get("风险标记数量大于等于", 2)):
        return True, "风险标记数量达到阈值"
    if safe_float(stock.get("资金放量率")) > float(cond.get("放量率大于", 1.0)):
        return True, "资金放量率超过阈值"
    if any(flag in {"涨停_强", "跌停_风险"} for flag in flags if isinstance(flags, list)):
        return True, "存在涨跌停标记"
    return False, "默认分析"


def route_models(stock: dict[str, Any], rule: dict[str, Any], manual_deep_codes: set[str], args: argparse.Namespace, models: list[str]) -> tuple[list[str], str]:
    routing = rule.get("模型路由", {})
    default_model = routing.get("默认分析模型", "qwen3:14b")
    complex_model = routing.get("复杂推理模型", "deepseek-r1:32b")
    fallback_model = routing.get("快速兜底模型", "qwen2.5:7b")
    complex_enabled = bool(routing.get("启用复杂模型", True)) and not args.no_complex
    complex_needed, reason = is_complex(stock, rule, manual_deep_codes, complex_enabled)

    ordered = [complex_model, default_model, fallback_model] if complex_needed else [default_model, fallback_model]
    result = []
    for model in ordered:
        if model in models and model not in result:
            result.append(model)
    if not result and models:
        result.append(models[0])
    return result, reason


def format_pct(value: Any) -> str:
    number = safe_float(value)
    return f"{number:.2f}%"


def format_amount_yuan(value: Any) -> str:
    """Format amount values stored in yuan to avoid model-side unit guessing."""
    number = safe_float(value)
    if number <= 0:
        return "0.00亿元"
    return f"{number / 100000000:.2f}亿元"


def stock_prompt(stock: dict[str, Any]) -> str:
    payload = {
        "代码": stock.get("代码"),
        "名称": stock.get("名称"),
        "行业": stock.get("行业"),
        "细分领域": stock.get("细分领域"),
        "是否用户增强": stock.get("是否用户增强"),
        "是否战略样本": stock.get("是否战略样本"),
        "L5入选原因": stock.get("L5入选原因"),
        "系统入选理由": stock.get("入选理由"),
        "调整分": stock.get("调整分"),
        "原始分": stock.get("原始分"),
        "收盘价": stock.get("收盘价"),
        "涨跌幅": stock.get("涨跌幅"),
        "近5日涨跌幅": stock.get("近5日涨跌幅"),
        "近20日涨跌幅": stock.get("近20日涨跌幅"),
        "资金放量率": stock.get("资金放量率"),
        "成交额口径": "金额字段已按人民币亿元格式化，禁止自行改写为万元、万亿元等其他单位；若成交额是否估算=true，不要强调具体成交额金额，只描述放量率和需核验",
        "近5日日均成交额": format_amount_yuan(stock.get("近5日日均成交额")),
        "近20日日均成交额": format_amount_yuan(stock.get("近20日日均成交额")),
        "行业强度分": stock.get("行业强度分"),
        "资金活跃度分": stock.get("资金活跃度分"),
        "技术面分": stock.get("技术面分"),
        "风险标记": stock.get("风险标记"),
        "数据源": stock.get("数据源"),
        "成交额是否估算": stock.get("成交额是否估算"),
    }
    return (
        "你是股票数据分析助手。只基于我提供的数据写结构化研究摘要，不补充未提供的新闻、公告、财报事实。"
        "禁止输出买入、卖出、持有、仓位建议、目标价、收益承诺或明确交易指令。"
        "不要使用“无风险”表述；若未发现系统风险标记，只写“未见系统风险标记”。"
        "允许输出继续跟踪、暂缓观察、需人工确认。不要输出思考过程。"
        "成交额只允许使用数据JSON里的亿元口径，不得自行换算成万亿元；若成交额为估算值，资金活跃项优先写放量率，不展开具体金额。\n\n"
        "请按以下8项输出，每项一句话，中文：\n"
        "1. 基本信息\n2. 入选原因\n3. 技术结构\n4. 资金活跃\n5. 行业背景\n6. 风险提示\n7. 证据状态\n8. 研究小结\n\n"
        f"数据JSON：{json.dumps(payload, ensure_ascii=False)}"
    )


def sanitize_analysis_text(text: str) -> str:
    """Normalize risky wording that can be mistaken for promise-like safety claims."""
    replacements = {
        "当前无风险标记": "当前未见系统风险标记",
        "无风险标记": "未见系统风险标记",
        "无风险提示": "未见系统风险提示",
        "无风险": "未见系统风险",
    }
    cleaned = text
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    cleaned = re.sub(r"(\d+(?:\.\d+)?)\s*万亿元", r"\1亿元（单位待核验）", cleaned)
    return cleaned


def rule_summary(stock: dict[str, Any], reason: str = "模型不可用，使用规则摘要兜底") -> str:
    user = "是" if stock.get("是否用户增强") else "否"
    strategic = "是" if stock.get("是否战略样本") else "否"
    risk_flags = stock.get("风险标记") or []
    risk_text = "、".join(risk_flags) if risk_flags else "未见系统风险标记"
    evidence = "成交额为估算值，需人工核验原始行情源" if stock.get("成交额是否估算") else "来自系统本地数据快照"
    return "\n".join([
        f"1. 基本信息：{stock.get('名称')}({stock.get('代码')}) 属于 {stock.get('行业') or '待映射'}，用户增强={user}，战略样本={strategic}。",
        f"2. 入选原因：L5入选原因为{stock.get('L5入选原因')}，调整分{safe_float(stock.get('调整分')):.4f}。",
        f"3. 技术结构：近5日涨跌幅{format_pct(stock.get('近5日涨跌幅'))}，近20日涨跌幅{format_pct(stock.get('近20日涨跌幅'))}，技术面分{safe_float(stock.get('技术面分')):.2f}。",
        f"4. 资金活跃：近5/20日成交额放量率{safe_float(stock.get('资金放量率')) * 100:.2f}%，资金活跃度分{safe_float(stock.get('资金活跃度分')):.2f}。",
        f"5. 行业背景：行业强度分{safe_float(stock.get('行业强度分')):.2f}，行业字段来自系统映射，仍可继续复核。",
        f"6. 风险提示：{risk_text}，不得据此直接形成交易动作。",
        f"7. 证据状态：{evidence}；{reason}。",
        "8. 研究小结：可作为继续跟踪对象，是否进入精选草案需人工结合公告、财报和消息面复核。",
    ])


def is_complete_analysis(text: str) -> bool:
    if len(text.strip()) < 280:
        return False
    return all(re.search(rf"(^|\n)\s*{index}[\.\、]", text) for index in range(1, 9))


def analyze_stock(stock: dict[str, Any], rule: dict[str, Any], manual_deep_codes: set[str], args: argparse.Namespace, models: list[str]) -> dict[str, Any]:
    routing = rule.get("模型路由", {})
    ollama_url = routing.get("ollama_url", "http://127.0.0.1:29134")
    model_order, route_reason = route_models(stock, rule, manual_deep_codes, args, models)
    errors: list[str] = []
    prompt = stock_prompt(stock)
    timeout_default = int(routing.get("单只超时秒", 90))
    timeout_complex = int(routing.get("复杂模型超时秒", 120))
    started = time.perf_counter()

    for index, model in enumerate(model_order):
        timeout = timeout_complex if model == routing.get("复杂推理模型") else timeout_default
        try:
            text, latency_ms = ollama_generate(ollama_url, model, prompt, timeout)
            if not text:
                raise RuntimeError("模型返回空文本")
            text = sanitize_analysis_text(text)
            if not is_complete_analysis(text):
                raise RuntimeError("模型输出未满足8项完整格式")
            return {
                "代码": stock.get("代码"),
                "展示代码": stock.get("展示代码"),
                "名称": stock.get("名称"),
                "行业": stock.get("行业"),
                "优先级": stock.get("优先级"),
                "调整分": stock.get("调整分"),
                "是否用户增强": stock.get("是否用户增强"),
                "是否战略样本": stock.get("是否战略样本"),
                "路由原因": route_reason,
                "model_used": model,
                "is_fallback": index > 0,
                "latency_ms": latency_ms,
                "error_msg": None,
                "analysis_text": text,
                "规则摘要兜底": False,
            }
        except (urllib.error.URLError, TimeoutError, RuntimeError, Exception) as exc:  # noqa: BLE001
            errors.append(f"{model}: {type(exc).__name__}: {exc}")

    return {
        "代码": stock.get("代码"),
        "展示代码": stock.get("展示代码"),
        "名称": stock.get("名称"),
        "行业": stock.get("行业"),
        "优先级": stock.get("优先级"),
        "调整分": stock.get("调整分"),
        "是否用户增强": stock.get("是否用户增强"),
        "是否战略样本": stock.get("是否战略样本"),
        "路由原因": route_reason,
        "model_used": "规则摘要兜底",
        "is_fallback": True,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "error_msg": "；".join(errors),
        "analysis_text": rule_summary(stock, reason="；".join(errors)),
        "规则摘要兜底": True,
    }


def load_confirmed_pool(root: Path, rule: dict[str, Any], args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    confirm_path = root / rule.get("输入", {}).get("人工确认结果", "03数据/135分层日报/L5人工确认结果_最新.json")
    l5_path = root / rule.get("输入", {}).get("L5深度研究池", "03数据/134深度研究池/L5深度研究池_最新.json")
    confirm_data = load_json(confirm_path, required=False)
    if confirm_data.get("是否允许AI分析"):
        return list(confirm_data.get("确认后股票池", [])), confirm_data
    if args.auto_confirm:
        l5_data = load_json(l5_path, required=True)
        return list(l5_data.get("股票池", [])), {
            "名称": "临时自动确认",
            "状态": "自动确认",
            "是否允许AI分析": True,
            "数据日期": l5_data.get("数据日期"),
            "确认后股票池": l5_data.get("股票池", []),
            "深度复核代码": [],
        }
    raise RuntimeError(f"未找到已确认的L5人工确认结果，且未启用--auto-confirm: {confirm_path}")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# AI分析报告 - {report['数据日期']}",
        "",
        "> 本报告由本地股票研究系统基于L5候选池和本地数据快照生成，仅供研究参考，不构成投资建议，不作为买卖指令。",
        "",
        "## 一、运行概览",
        "",
        f"- 分析股票数：{report['数据健康度']['分析股票数']}",
        f"- 模型成功数：{report['数据健康度']['模型成功数']}",
        f"- 规则兜底数：{report['数据健康度']['规则兜底数']}",
        f"- 生成时间：{report['生成时间']}",
        "",
        "## 二、AI分析摘要",
        "",
    ]
    for item in report.get("分析结果", []):
        flags = []
        if item.get("是否用户增强"):
            flags.append("用户增强")
        if item.get("是否战略样本"):
            flags.append("战略样本")
        flag_text = f"（{'、'.join(flags)}）" if flags else ""
        lines.extend([
            f"### {item.get('优先级')}. {item.get('名称')}({item.get('代码')}){flag_text}",
            "",
            f"- 行业：{item.get('行业') or '待映射'}",
            f"- 调整分：{safe_float(item.get('调整分')):.4f}",
            f"- 模型：{item.get('model_used')}，耗时：{item.get('latency_ms')}ms，兜底：{item.get('规则摘要兜底')}",
            "",
            item.get("analysis_text", ""),
            "",
        ])
    lines.extend([
        "## 三、人工反馈入口",
        "",
        "可反馈：`有价值 sh688041` / `无价值 sh688256` / `继续跟踪 sz300750` / `误报 sh600519`。",
        "",
        "## 四、安全边界",
        "",
        "- 未触发n8n。",
        "- 未发送企业微信真实消息。",
        "- 未调用券商接口。",
        "- 未自动交易。",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成L5 AI分析报告")
    parser.add_argument("--auto-confirm", action="store_true", help="没有人工确认结果时，临时使用当前L5作为确认池。")
    parser.add_argument("--no-complex", action="store_true", help="本次运行不启用复杂推理模型，只用默认模型和快速兜底。")
    parser.add_argument("--max-stocks", type=int, default=0, help="仅分析前N只，用于调试；0表示全量。")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    rule_path = root / "01配置" / "L5AI分析报告规则.json"
    rule = load_json(rule_path, required=True)
    stocks, confirm_data = load_confirmed_pool(root, rule, args)
    if args.max_stocks and args.max_stocks > 0:
        stocks = stocks[: args.max_stocks]

    routing = rule.get("模型路由", {})
    ollama_url = routing.get("ollama_url", "http://127.0.0.1:29134")
    models = available_models(ollama_url)
    manual_deep_codes = {normalize_code(code) for code in confirm_data.get("深度复核代码", [])}

    results = [analyze_stock(stock, rule, manual_deep_codes, args, models) for stock in stocks]
    data_date = confirm_data.get("数据日期") or (stocks[0].get("数据日期") if stocks else now.strftime("%Y-%m-%d"))
    output_dir = root / "03数据" / "135分层日报"
    output_json = output_dir / f"AI分析报告_{str(data_date).replace('-', '')}_{stamp}.json"
    output_md = output_dir / f"AI分析报告_{str(data_date).replace('-', '')}_{stamp}.md"
    latest_json = output_dir / "AI分析报告_最新.json"
    latest_md = output_dir / "AI分析报告_最新.md"
    log_dir = root / "04日志" / "人工闸口"
    log_path = log_dir / f"L5AI分析报告生成日志_{stamp}.json"
    log_latest_path = log_dir / "L5AI分析报告生成日志_最新.json"

    fallback_count = sum(1 for item in results if item.get("规则摘要兜底"))
    report = {
        "名称": "L5AI分析报告",
        "版本": "2026-05-01",
        "定位": "基于人工确认后的L5深度研究池生成的结构化AI分析报告，不构成投资建议。",
        "数据日期": data_date,
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成L5AI分析报告.py",
        "规则文件": str(rule_path),
        "人工确认状态": confirm_data.get("状态"),
        "模型路由": {
            "ollama_url": ollama_url,
            "可用模型": models,
            "默认分析模型": routing.get("默认分析模型"),
            "复杂推理模型": routing.get("复杂推理模型"),
            "快速兜底模型": routing.get("快速兜底模型"),
            "本次禁用复杂模型": bool(args.no_complex),
        },
        "数据健康度": {
            "确认股票数": len(stocks),
            "分析股票数": len(results),
            "模型成功数": len(results) - fallback_count,
            "规则兜底数": fallback_count,
            "是否完整": len(results) == len(stocks) and len(results) > 0,
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
            "读取L5人工确认结果": bool(confirm_data),
            "调用本地Ollama": True,
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
        "分析结果": results,
    }
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, {
        "名称": "L5AI分析报告生成日志",
        "生成时间": report["生成时间"],
        "数据健康度": report["数据健康度"],
        "模型路由": report["模型路由"],
        "输出文件": report["输出文件"],
        "安全边界": report["安全边界"],
        "实际动作": report["实际动作"],
    })
    write_json(log_latest_path, load_json(log_path, required=True))

    print(json.dumps({
        "状态": "完成",
        "分析股票数": len(results),
        "模型成功数": report["数据健康度"]["模型成功数"],
        "规则兜底数": fallback_count,
        "是否完整": report["数据健康度"]["是否完整"],
        "Markdown": str(output_md),
        "JSON": str(output_json),
    }, ensure_ascii=False))
    return 0 if report["数据健康度"]["是否完整"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
