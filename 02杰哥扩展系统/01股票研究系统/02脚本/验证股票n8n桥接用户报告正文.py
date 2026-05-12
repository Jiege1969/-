# -*- coding: utf-8 -*-
"""
名称：验证股票n8n桥接用户报告正文.py
作用：验收n8n股票桥接写给企业微信发送器的正文只包含用户报告，不混入技术运行记录。
边界：本地生成预演输出；不真实发送企业微信；不触发n8n；不接券商；不交易；不重载19310/19302。
"""

from __future__ import annotations

import importlib.util
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "02脚本" / "股票n8n企业微信终端桥接服务.py"
OUT_DIR = ROOT / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
LOG_DIR = ROOT / "04日志" / "n8n企业微信终端灰度链路"
BRIDGE_MD = Path(r"D:\杰哥智能化系统\01杰哥智能系统\03数据\n8n\jiege_bridge\stock_active_research_response.md")
BRIDGE_JSON = Path(r"D:\杰哥智能化系统\01杰哥智能系统\03数据\n8n\jiege_bridge\stock_active_research_response.json")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_bridge_module() -> Any:
    spec = importlib.util.spec_from_file_location("stock_n8n_wecom_bridge_verify", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载脚本：{SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any = "") -> None:
    checks.append({"检查项": name, "通过": bool(passed), "说明": detail})


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票n8n桥接用户报告正文验收",
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
    lines.extend([
        "",
        "## 边界",
        "",
        "- 未真实发送企业微信。",
        "- 未触发n8n。",
        "- 未接券商，未交易。",
        "- 未重载19310/19302。",
    ])
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    module = load_bridge_module()
    bridge_report = module.run_bridge_task({
        "stage": "after_close_report",
        "source": "local_user_report_body_verify",
        "text": "今日观察",
    })
    bridge_text = BRIDGE_MD.read_text(encoding="utf-8-sig", errors="replace") if BRIDGE_MD.exists() else ""
    bridge_json = json.loads(BRIDGE_JSON.read_text(encoding="utf-8-sig")) if BRIDGE_JSON.exists() else {}
    forbidden = [
        "股票n8n企业微信终端桥接运行记录",
        "阶段：",
        "问题：",
        "成功：True",
        "真实发送企业微信：",
        "接券商/交易：",
        "企业微信可读内容",
    ]
    trading_terms = ["买入研究信号", "卖出研究信号", "重点推荐", "常规推荐", "加仓", "减仓", "满仓", "清仓", "下单"]
    checks: list[dict[str, Any]] = []
    add_check(checks, "桥接任务本地生成成功", bridge_report.get("成功") is True, bridge_report.get("股票助手结果", {}))
    add_check(checks, "桥接Markdown存在", BRIDGE_MD.exists(), str(BRIDGE_MD))
    add_check(checks, "桥接Markdown为股票观察晨报用户正文", bridge_text.startswith("【股票观察晨报｜") and "杰哥，您好！我先直接说结论：" in bridge_text, bridge_text[:200])
    add_check(checks, "桥接Markdown不含技术运行记录外壳", not any(term in bridge_text for term in forbidden), [term for term in forbidden if term in bridge_text])
    add_check(checks, "股票名称保留可点击详情链接", bool(re.search(r"\[[^\]]+\]\(http[^)]+/wecom-bot/message\?ask=", bridge_text)), bridge_text[:500])
    add_check(checks, "报告包含四段式量价结构", all(term in bridge_text for term in ["① 一句话核心逻辑", "② 当前走势与量价结构", "③ 明确的观察/参考条件", "④ 风险提示与本报告的责任边界"]), bridge_text[:1200])
    add_check(checks, "报告包含站稳与跌破条件", "站稳" in bridge_text and "跌破" in bridge_text and "放弃" in bridge_text, bridge_text[:1200])
    add_check(checks, "保留用户反馈入口", "太空泛" in bridge_text and "风险没讲清" in bridge_text and "更严谨的结构重新输出" in bridge_text, bridge_text[-700:])
    add_check(checks, "无交易化旧口径残留", not any(term in bridge_text for term in trading_terms), [term for term in trading_terms if term in bridge_text])
    add_check(checks, "桥接JSON保留企业微信发送正文", str(bridge_json.get("企业微信发送正文") or "").strip() == bridge_text.strip(), "JSON正文与Markdown一致")
    safety = bridge_json.get("安全边界", {})
    add_check(checks, "安全动作仍为false", all(safety.get(key) is False for key in ["真实发送企业微信", "群发", "调用券商接口", "自动交易", "重载19310", "重载19302"]), safety)

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票n8n桥接用户报告正文验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "pass" if not failed else "blocked",
        "统计": {"通过": len(checks) - len(failed), "失败": len(failed)},
        "检查项": checks,
        "桥接Markdown": str(BRIDGE_MD),
        "桥接JSON": str(BRIDGE_JSON),
        "安全边界": {
            "真实发送企业微信": False,
            "触发n8n": False,
            "接券商": False,
            "交易": False,
            "重载19310": False,
            "重载19302": False,
        },
    }
    latest_json = OUT_DIR / "股票n8n桥接用户报告正文验收_最新.json"
    latest_md = OUT_DIR / "股票n8n桥接用户报告正文验收_最新.md"
    log_json = LOG_DIR / f"stock-n8n-bridge-user-report-body-verify-{stamp}.json"
    log_md = LOG_DIR / f"stock-n8n-bridge-user-report-body-verify-{stamp}.md"
    markdown = build_markdown(report)
    for path in (latest_json, log_json):
        write_json(path, report)
    for path in (latest_md, log_md):
        write_text(path, markdown)
    print(json.dumps({"总体状态": report["总体状态"], "通过": report["统计"]["通过"], "失败": report["统计"]["失败"], "报告": str(latest_md)}, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
