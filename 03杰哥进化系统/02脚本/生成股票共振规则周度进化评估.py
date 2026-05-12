# -*- coding: utf-8 -*-
"""
名称：生成股票共振规则周度进化评估.py
作用：只读扫描股票共振规则调试日志，评估“短线反弹共振信号”触发后三个交易日内的反弹成功率。
安全边界：只读股票系统本地产物，只写03进化系统本地评估报告；不反向修改股票规则；不触发n8n；不发送企业微信；不接券商；不交易。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ROOT = Path(r"D:\杰哥智能化系统")
STOCK_ROOT = ROOT / "02杰哥扩展系统" / "01股票研究系统"
EVOLUTION_ROOT = ROOT / "03杰哥进化系统"
DEBUG_DIR = STOCK_ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
HISTORY_PATH = STOCK_ROOT / "03数据" / "94候选历史K线技术指标" / "300只候选历史K线_最新.json"
OUTPUT_DIR = EVOLUTION_ROOT / "03数据" / "86股票共振规则周度进化评估"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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


def code_key(code: Any) -> str:
    return str(code or "").lower().replace(".", "")


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def build_history_index() -> dict[str, list[dict[str, Any]]]:
    data = load_json(HISTORY_PATH, {})
    index: dict[str, list[dict[str, Any]]] = {}
    for item in data.get("历史K线", []):
        if isinstance(item, dict):
            rows = [row for row in item.get("K线", []) if isinstance(row, dict)]
            index[code_key(item.get("代码"))] = rows
    return index


def debug_log_files() -> list[Path]:
    if not DEBUG_DIR.exists():
        return []
    return sorted(path for path in DEBUG_DIR.glob("共振信号规则调试日志_*.json") if path.name != "共振信号规则调试日志_最新.json")


def collect_trigger_samples() -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for path in debug_log_files():
        data = load_json(path, {})
        signal_date = str(data.get("数据日期") or "")[:10]
        for item in data.get("调试日志", []):
            code = code_key(item.get("代码"))
            name = str(item.get("名称") or "")
            for signal in item.get("规则调试", []):
                if not isinstance(signal, dict):
                    continue
                if signal.get("规则名称") != "短线反弹共振信号" or signal.get("触发") is not True:
                    continue
                key = (code, signal_date, signal.get("规则名称", ""))
                if key in seen:
                    continue
                seen.add(key)
                samples.append({
                    "代码": code,
                    "名称": name,
                    "信号日期": signal_date,
                    "规则名称": signal.get("规则名称"),
                    "触发条件": signal.get("条件", {}),
                    "日志文件": str(path),
                })
    return samples


def evaluate_sample(sample: dict[str, Any], history_index: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    rows = history_index.get(sample["代码"], [])
    dates = [str(row.get("日期") or "") for row in rows]
    if sample["信号日期"] not in dates:
        return {**sample, "可评估": False, "原因": "历史K线中未找到信号日期", "是否成功": False}
    idx = dates.index(sample["信号日期"])
    base_close = safe_float(rows[idx].get("收盘"))
    next_rows = rows[idx + 1: idx + 4]
    if base_close <= 0 or len(next_rows) < 3:
        return {**sample, "可评估": False, "原因": "后续三个交易日数据不足", "是否成功": False}
    max_close = max(safe_float(row.get("收盘")) for row in next_rows)
    rebound_pct = (max_close / base_close - 1) * 100
    return {
        **sample,
        "可评估": True,
        "基准收盘": round(base_close, 4),
        "后三交易日最高收盘": round(max_close, 4),
        "后三交易日最大反弹幅度": round(rebound_pct, 4),
        "是否成功": rebound_pct > 2,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票共振规则周度进化评估 - {report['生成时间']}",
        "",
        f"- 评估规则：短线反弹共振信号",
        f"- 可评估样本数：{report['可评估样本数']}",
        f"- 成功样本数：{report['成功样本数']}",
        f"- 成功率：{report['成功率百分比']}%",
        f"- 参数建议：{report['参数调整建议']}",
        "",
        "## 样本明细",
        "",
    ]
    if report["样本评估"]:
        for item in report["样本评估"]:
            lines.append(f"- {item.get('名称')}({item.get('代码')}) {item.get('信号日期')}：可评估={item.get('可评估')}，成功={item.get('是否成功')}，后三交易日最大反弹={item.get('后三交易日最大反弹幅度', '暂无')}%，原因={item.get('原因', '')}")
    else:
        lines.append("- 暂无触发样本")
    lines.extend(["", "## 安全边界", "", "- 不修改股票正式规则。", "- 不触发n8n。", "- 不发送企业微信。", "- 不接券商、不交易。"])
    return "\n".join(lines)


def main() -> int:
    history_index = build_history_index()
    samples = collect_trigger_samples()
    evaluated = [evaluate_sample(sample, history_index) for sample in samples]
    evaluable = [item for item in evaluated if item.get("可评估") is True]
    successes = [item for item in evaluable if item.get("是否成功") is True]
    success_rate = (len(successes) / len(evaluable)) if evaluable else None
    if success_rate is None:
        suggestion = "触发样本或后三交易日数据不足，暂不调整正式参数，继续积累调试日志。"
    elif success_rate < 0.5:
        suggestion = "建议将 RSI < 30 调整为 RSI < 25，以提升信号质量；该建议仅进入进化候选，不自动改正式规则。"
    else:
        suggestion = "当前成功率不低于50%，暂不建议收紧 RSI 参数。"
    report = {
        "名称": "股票共振规则周度进化评估",
        "状态": "完成",
        "生成时间": now_text(),
        "输入": {
            "共振信号规则调试日志目录": str(DEBUG_DIR),
            "候选历史K线": str(HISTORY_PATH),
        },
        "评估规则": "短线反弹共振信号",
        "触发样本数": len(samples),
        "可评估样本数": len(evaluable),
        "成功样本数": len(successes),
        "成功率": success_rate,
        "成功率百分比": round(success_rate * 100, 2) if success_rate is not None else None,
        "参数调整建议": suggestion,
        "样本评估": evaluated,
        "安全边界": {
            "是否修改股票正式规则": False,
            "是否触发n8n": False,
            "是否发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = OUTPUT_DIR / f"股票共振规则周度进化评估_{stamp}.json"
    output_md = OUTPUT_DIR / f"股票共振规则周度进化评估_{stamp}.md"
    latest_json = OUTPUT_DIR / "股票共振规则周度进化评估_最新.json"
    latest_md = OUTPUT_DIR / "股票共振规则周度进化评估_最新.md"
    quality_weekly_md = OUTPUT_DIR / "系统质量周报_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_text(quality_weekly_md, markdown)
    print(json.dumps({"状态": "完成", "触发样本数": len(samples), "可评估样本数": len(evaluable), "成功率": report["成功率百分比"], "输出": str(latest_md)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
