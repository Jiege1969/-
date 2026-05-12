# -*- coding: utf-8 -*-
"""
名称：执行股票金融专项复核.py
作用：对L5深度研究池中的单只股票调用金融专项模型进行补充复核。
触发方式：python 执行股票金融专项复核.py [--code sh688047] [--cross]
依赖：股票金融专项复核规则.json；L5深度研究池；AI分析报告；本地Ollama。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读L5/AI报告/模型健康；只调用本地Ollama；只写03数据/149金融专项复核；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-finance-special-review
"""

from __future__ import annotations

import argparse
import json
import re
import time
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


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
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


def strip_think(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"</?answer>", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def sanitize_finance_text(text: str) -> str:
    replacements = {
        "短期内上涨动力强": "短期交易关注度较高",
        "上涨动力强": "交易关注度较高",
        "发展前景广阔": "行业关注度较高",
        "前景广阔": "行业关注度较高",
        "表现优异": "系统指标表现较强",
        "市场情绪高涨": "市场交易关注度较高",
        "存在利好消息": "存在未核验事件因素",
        "利好消息": "未核验事件因素",
        "重大利好": "重大事件",
        "双重利好": "双重因素",
        "投资价值": "研究关注价值",
        "市场前景": "市场需求变化",
        "未来盈利能力": "后续盈利能力",
        "买卖建议": "交易动作建议",
        "目标价预测": "价格预测",
    }
    cleaned = text
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    cleaned = re.sub(r"提供具体的交易动作建议或价格预测[^。\n]*[。\n]?", "仅列出需人工核验的财务和风险要点，不提供交易动作或价格预测。\n", cleaned)
    cleaned = re.sub(r"提供具体的买卖建议或目标价预测[^。\n]*[。\n]?", "仅列出需人工核验的财务和风险要点，不提供交易动作或价格预测。\n", cleaned)
    return cleaned


def ensure_complete_review(text: str, stock: dict[str, Any]) -> str:
    if not re.search(r"6[\.\、]\s*\*{0,2}复核结论\*{0,2}\s*\S+", text, flags=re.DOTALL):
        addition = (
            f"\n   {stock.get('名称')}当前只能确认系统分层指标、行业强度和资金活跃信号，"
            "尚不能确认财务基本面改善或估值合理性；建议作为需人工核验财报、公告和成交额原始数据的继续跟踪对象。"
        )
        if re.search(r"6[\.\、]\s*\*{0,2}复核结论\*{0,2}", text):
            return re.sub(r"(6[\.\、]\s*\*{0,2}复核结论\*{0,2})\s*$", r"\1" + addition, text.strip(), flags=re.DOTALL)
        return text.rstrip() + "\n\n6. 复核结论" + addition
    return text


def ollama_generate(ollama_url: str, model: str, prompt: str, timeout: int) -> tuple[str, int]:
    started = time.perf_counter()
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.15,
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


def available_models(health: dict[str, Any]) -> set[str]:
    return set(str(item) for item in health.get("全部模型", []) if item)


def find_stock(l5: dict[str, Any], code: str | None) -> dict[str, Any]:
    stocks = l5.get("股票池") or []
    if not stocks:
        raise ValueError("L5深度研究池为空")
    if not code:
        return stocks[0]
    norm = normalize_code(code)
    for stock in stocks:
        if normalize_code(stock.get("代码")) == norm or normalize_code(stock.get("展示代码")) == norm:
            return stock
    raise ValueError(f"指定股票不在L5深度研究池中: {code}")


def find_ai_text(ai: dict[str, Any], code: str) -> str:
    norm = normalize_code(code)
    for item in ai.get("分析结果", []) or []:
        if normalize_code(item.get("代码")) == norm or normalize_code(item.get("展示代码")) == norm:
            return str(item.get("analysis_text") or "")
    return ""


def build_prompt(stock: dict[str, Any], ai_text: str) -> str:
    payload = {
        "代码": stock.get("代码"),
        "展示代码": stock.get("展示代码"),
        "名称": stock.get("名称"),
        "行业": stock.get("行业"),
        "细分领域": stock.get("细分领域"),
        "是否用户增强": stock.get("是否用户增强"),
        "是否战略样本": stock.get("是否战略样本"),
        "调整分": stock.get("调整分"),
        "原始分": stock.get("原始分"),
        "收盘价": stock.get("收盘价"),
        "涨跌幅": stock.get("涨跌幅"),
        "近5日涨跌幅": stock.get("近5日涨跌幅"),
        "近20日涨跌幅": stock.get("近20日涨跌幅"),
        "资金放量率": stock.get("资金放量率"),
        "近5日日均成交额": stock.get("近5日日均成交额"),
        "近20日日均成交额": stock.get("近20日日均成交额"),
        "行业强度分": stock.get("行业强度分"),
        "资金活跃度分": stock.get("资金活跃度分"),
        "技术面分": stock.get("技术面分"),
        "风险标记": stock.get("风险标记"),
        "成交额是否估算": stock.get("成交额是否估算"),
        "原AI分析摘要": ai_text[:2500],
    }
    return (
        "你是金融专项复核助手。任务是对股票研究系统已经生成的L5分析做补充复核。"
        "只能基于输入数据和原AI摘要进行解释，不能编造公告、财报、新闻或实时行情。"
        "禁止输出买入、卖出、持有、仓位建议、目标价、收益承诺或明确交易指令。"
        "请按6项输出，每项1-2句话：\n"
        "1. 财务口径关注点\n"
        "2. 行业经营变量\n"
        "3. 资金与估值解释边界\n"
        "4. 需要人工核验的公告或财报证据\n"
        "5. 与原AI报告的差异\n"
        "6. 复核结论\n\n"
        f"输入JSON：{json.dumps(payload, ensure_ascii=False)}"
    )


def fallback_review(stock: dict[str, Any], reason: str) -> str:
    return "\n".join([
        f"1. 财务口径关注点：{stock.get('名称')}当前缺少财报正文输入，无法确认收入、利润、现金流等财务口径。",
        f"2. 行业经营变量：行业为{stock.get('行业')}，细分领域为{stock.get('细分领域')}，需结合后续官方公告或财报核验。",
        "3. 资金与估值解释边界：系统资金活跃指标只说明交易活跃变化，不等同于估值合理或基本面改善。",
        "4. 需要人工核验的公告或财报证据：需核验最近一期定期报告、重大合同/减持/诉讼/监管问询等公告。",
        f"5. 与原AI报告的差异：本次未调用金融模型，原因：{reason}。",
        "6. 复核结论：仅可作为待人工核验清单，不构成交易建议。",
    ])


def build_markdown(report: dict[str, Any]) -> str:
    stock = report["股票"]
    lines = [
        f"# 股票金融专项复核 - {stock['名称']}({stock['展示代码']})",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 主模型：{report['主模型结果']['model_used']}",
        f"- 主模型是否成功：{report['主模型结果']['success']}",
        f"- 交叉对照：{report['是否启用交叉对照']}",
        "",
        "## 一、主模型复核",
        "",
        report["主模型结果"]["text"],
    ]
    if report.get("交叉对照结果"):
        lines.extend([
            "",
            "## 二、交叉对照复核",
            "",
            report["交叉对照结果"]["text"],
        ])
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 本复核只解释证据边界，不给交易指令。",
        "- 不触发n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_sample_bat(root: Path, script_path: Path) -> Path:
    entry_dir = root / "05入口工具"
    bat = entry_dir / "股票系统金融专项复核_运行L5第一只.bat"
    content = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'cd /d "{script_path.parent}"\r\n'
        f'python "{script_path.name}"\r\n'
        'python "生成股票金融专项复核索引.py"\r\n'
        'start "" "D:\\杰哥智能化系统\\02杰哥扩展系统\\01股票研究系统\\03数据\\149金融专项复核\\股票金融专项复核_最新.md"\r\n'
        "pause\r\n"
    )
    write_text(bat, content)
    return bat


def write_entry_code_bat(script_path: Path) -> Path:
    entry_dir = script_path.parents[1] / "05入口工具"
    bat = entry_dir / "股票系统金融专项复核_按代码运行.bat"
    content = (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'cd /d "{script_path.parent}"\r\n'
        "set /p STOCK_CODE=请输入L5股票代码（如 sh688047 或 688047.SH）：\r\n"
        f'python "{script_path.name}" --code %STOCK_CODE%\r\n'
        'python "生成股票金融专项复核索引.py"\r\n'
        'start "" "D:\\杰哥智能化系统\\02杰哥扩展系统\\01股票研究系统\\03数据\\149金融专项复核\\股票金融专项复核_最新.md"\r\n'
        "pause\r\n"
    )
    write_text(bat, content)
    return bat


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", default="", help="复核L5中的指定股票代码，如 sh688047；为空则复核L5第一只")
    parser.add_argument("--cross", action="store_true", help="启用金融观点交叉对照模型")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    rule = load_json(root / "01配置" / "股票金融专项复核规则.json", required=True)
    l5 = load_json(root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json", required=True)
    ai = load_json(root / "03数据" / "135分层日报" / "AI分析报告_最新.json", {})
    health = load_json(root / "03数据" / "148模型健康检查" / "股票系统模型健康检查_最新.json", {})
    models = available_models(health)

    stock = find_stock(l5, args.code or None)
    ai_text = find_ai_text(ai, stock.get("代码"))
    model_cfg = rule.get("模型") or {}
    ollama_url = model_cfg.get("ollama_url", "http://127.0.0.1:29134")
    main_model = model_cfg.get("主模型", "mychen76/Fin-R1:Q5")
    cross_model = model_cfg.get("交叉对照模型", "martain7r/finance-llama-8b:q4_k_m")
    timeout = int(model_cfg.get("超时秒", 180))
    prompt = build_prompt(stock, ai_text)

    main_result: dict[str, Any]
    if main_model not in models:
        main_result = {
            "model_used": main_model,
            "success": False,
            "latency_ms": None,
            "error_msg": "主模型不可用",
            "text": fallback_review(stock, "主模型不可用"),
        }
    else:
        try:
            text, latency = ollama_generate(ollama_url, main_model, prompt, timeout)
            text = sanitize_finance_text(text)
            text = ensure_complete_review(text, stock)
            main_result = {
                "model_used": main_model,
                "success": True,
                "latency_ms": latency,
                "error_msg": None,
                "text": text or fallback_review(stock, "模型返回空文本"),
            }
        except Exception as exc:  # noqa: BLE001
            main_result = {
                "model_used": main_model,
                "success": False,
                "latency_ms": None,
                "error_msg": str(exc),
                "text": fallback_review(stock, str(exc)),
            }

    cross_result = None
    if args.cross or bool(model_cfg.get("默认启用交叉对照", False)):
        if cross_model in models:
            try:
                text, latency = ollama_generate(ollama_url, cross_model, prompt, timeout)
                text = sanitize_finance_text(text)
                text = ensure_complete_review(text, stock)
                cross_result = {
                    "model_used": cross_model,
                    "success": True,
                    "latency_ms": latency,
                    "error_msg": None,
                    "text": text or fallback_review(stock, "交叉对照模型返回空文本"),
                }
            except Exception as exc:  # noqa: BLE001
                cross_result = {
                    "model_used": cross_model,
                    "success": False,
                    "latency_ms": None,
                    "error_msg": str(exc),
                    "text": fallback_review(stock, str(exc)),
                }
        else:
            cross_result = {
                "model_used": cross_model,
                "success": False,
                "latency_ms": None,
                "error_msg": "交叉对照模型不可用",
                "text": fallback_review(stock, "交叉对照模型不可用"),
            }

    output_dir = root / "03数据" / "149金融专项复核"
    display_code = stock.get("展示代码") or stock.get("代码")
    report = {
        "名称": "股票金融专项复核",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "执行股票金融专项复核.py",
        "规则文件": str(root / "01配置" / "股票金融专项复核规则.json"),
        "股票": {
            "代码": stock.get("代码"),
            "展示代码": display_code,
            "名称": stock.get("名称"),
            "行业": stock.get("行业"),
            "细分领域": stock.get("细分领域"),
        },
        "是否启用交叉对照": bool(cross_result),
        "主模型结果": main_result,
        "交叉对照结果": cross_result,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    json_path = output_dir / f"股票金融专项复核_{display_code}_{stamp}.json"
    md_path = output_dir / f"股票金融专项复核_{display_code}_{stamp}.md"
    latest_json = output_dir / "股票金融专项复核_最新.json"
    latest_md = output_dir / "股票金融专项复核_最新.md"
    markdown = build_markdown(report)
    write_json(json_path, report)
    write_json(latest_json, report)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)
    entry_bat = write_entry_sample_bat(root, Path(__file__).resolve())
    entry_code_bat = write_entry_code_bat(Path(__file__).resolve())

    print(json.dumps({
        "状态": "完成",
        "股票": f"{stock.get('名称')}({display_code})",
        "主模型": main_model,
        "主模型成功": main_result["success"],
        "报告": str(latest_md),
        "入口工具": str(entry_bat),
        "按代码入口": str(entry_code_bat),
    }, ensure_ascii=False))
    return 0 if main_result["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
