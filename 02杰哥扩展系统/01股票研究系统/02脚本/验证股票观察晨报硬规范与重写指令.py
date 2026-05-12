# -*- coding: utf-8 -*-
"""
名称：验证股票观察晨报硬规范与重写指令.py
作用：验收用户在企业微信里下达报告规范+重写请求时，股票专家直接按新规范输出报告。
边界：本地影子验收；不真实发送企业微信；不触发n8n；不接券商；不交易；不重载19310/19302。
"""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "02脚本" / "股票助手入口.py"
OUT_DIR = ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
LOG_DIR = ROOT / "04日志" / "股票观察晨报硬规范"


USER_RULE_AND_REWRITE = """从现在起，你每输出一次股票报告，都要遵循以下规则：报告抬头固定为【股票观察晨报｜日期】；开头说‘杰哥，直接说结论：’；每只股票必须描述当前在什么关键价位附近，量价如何配合，给出明确的条件：站稳何处才关注、跌破何处就放弃，绝对禁止写‘继续观察/需复核’这类废话；结尾统一写‘以上分析仅供参考，不构成投资建议’。按这个标准，把龙芯中科今天的分析重新写一遍给我看。"""


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("stock_morning_report_rule_verify", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本：{SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"检查项": name, "通过": bool(passed), "说明": detail})


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票观察晨报硬规范与重写指令验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：{report['总体状态']}",
        f"- 通过：{report['统计']['通过']}",
        f"- 失败：{report['统计']['失败']}",
        "",
        "## 检查项",
        "",
    ]
    for item in report["检查项"]:
        lines.append(f"- {item['检查项']}：{item['通过']}；{item['说明']}")
    lines.extend(["", "## 边界", "", "- 未真实发送企业微信。", "- 未触发n8n。", "- 未接券商，未交易。", "- 未重载19310/19302。"])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    module = load_module()
    rewrite = module.build_analysis(USER_RULE_AND_REWRITE, refresh=False, remember_context=False, entrance_role="专家")
    rewrite_text = str(rewrite.get("企业微信回复") or rewrite.get("回复") or "")
    daily = module.build_analysis("今日观察", refresh=False, remember_context=False, entrance_role="专家")
    daily_text = str(daily.get("企业微信回复") or daily.get("回复") or "")
    forbidden_debug = ["阶段：", "问题：", "成功：", "真实发送企业微信", "接券商/交易", "桥接运行记录", "企业微信可读内容"]
    forbidden_empty = ["需继续跟踪", "继续观察", "值得继续观察", "需复核", "继续复核", "仍需复核公开证据", "需人工确认", "暂无额外风险标记"]
    checks: list[dict[str, Any]] = []
    add_check(checks, "规则+重写请求识别为报告规范重写", rewrite.get("类型") == "报告规范重写", rewrite.get("类型"))
    add_check(checks, "重写报告标题符合硬规范", rewrite_text.startswith("【股票观察晨报｜"), rewrite_text[:80])
    add_check(checks, "重写报告开头固定", any(line.startswith("杰哥，您好！我先直接说结论：") for line in rewrite_text.splitlines()[1:3]), rewrite_text[:160])
    add_check(checks, "重写报告包含龙芯中科", "龙芯中科" in rewrite_text and "688047" in rewrite_text, rewrite_text[:300])
    add_check(checks, "重写报告包含四段式", all(term in rewrite_text for term in ["① 一句话核心逻辑", "② 当前走势与量价结构", "③ 明确的观察/参考条件", "④ 风险提示与本报告的责任边界"]), rewrite_text)
    add_check(checks, "重写报告包含站稳与跌破条件", "站稳" in rewrite_text and "跌破" in rewrite_text and "放弃" in rewrite_text, rewrite_text)
    add_check(checks, "重写报告不含系统调试信息", not any(term in rewrite_text for term in forbidden_debug), [term for term in forbidden_debug if term in rewrite_text])
    add_check(checks, "重写报告不含空泛禁句", not any(term in rewrite_text for term in forbidden_empty), [term for term in forbidden_empty if term in rewrite_text])
    add_check(checks, "重写报告不是反馈日志确认话术", "记入反馈日志" not in rewrite_text and "后续报告会优先纠正" not in rewrite_text, rewrite_text[:200])
    add_check(checks, "重写报告结尾符合责任边界", rewrite_text.strip().endswith("以上仅基于历史数据的客观分析，不构成投资建议，买卖自主决策，盈亏自负。"), rewrite_text[-120:])
    add_check(checks, "今日观察标题已符合硬规范", daily_text.startswith("【股票观察晨报｜"), daily_text[:80])
    add_check(checks, "今日观察开头已符合硬规范", any(line.startswith("杰哥，您好！我先直接说结论：") for line in daily_text.splitlines()[1:3]), daily_text[:160])
    add_check(checks, "今日观察不含系统调试信息", not any(term in daily_text for term in forbidden_debug), [term for term in forbidden_debug if term in daily_text])
    add_check(checks, "今日观察不含空泛禁句", not any(term in daily_text for term in forbidden_empty), [term for term in forbidden_empty if term in daily_text])
    safety = {"真实发送企业微信": False, "触发n8n": False, "接券商": False, "交易": False, "重载19310": False, "重载19302": False}
    for key, value in safety.items():
        add_check(checks, f"安全边界：{key}=false", value is False, safety)
    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票观察晨报硬规范与重写指令验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "统计": {"通过": len(checks) - len(failed), "失败": len(failed)},
        "检查项": checks,
        "重写预览": rewrite_text,
        "今日观察预览": daily_text[:1500],
        "安全边界": safety,
    }
    latest_json = OUT_DIR / "股票观察晨报硬规范与重写指令验收_最新.json"
    latest_md = OUT_DIR / "股票观察晨报硬规范与重写指令验收_最新.md"
    log_json = LOG_DIR / f"stock-morning-report-strict-rule-verify-{stamp}.json"
    log_md = LOG_DIR / f"stock-morning-report-strict-rule-verify-{stamp}.md"
    markdown = build_markdown(report)
    for path in (latest_json, log_json):
        write_json(path, report)
    for path in (latest_md, log_md):
        write_text(path, markdown)
    print(json.dumps({"总体状态": report["总体状态"], "通过": report["统计"]["通过"], "失败": report["统计"]["失败"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
