# -*- coding: utf-8 -*-
"""
名称：验证股票推荐点击详情与手机排版.py
作用：验证今日推荐草案中的股票名称链接可打开详细图文报告，并检查手机端排版基础规则。
触发方式：手动验收；推荐草案、桥接入口或手机端排版规则变更后本地执行。
依赖：本机Python标准库；股票企微推送草案_最新.md；股票企业微信桥接入口127.0.0.1:19302；股票助手127.0.0.1:19300。
所属系统：02杰哥扩展系统/01股票研究系统
输出：03数据/196推荐点击详情与手机排版验收/股票推荐点击详情与手机排版验收_最新.json 与 .md。
安全边界：只读推送草案并访问本机19302/19300只读详情入口；只写验收报告；不真实发送企业微信、不触发n8n、不重启服务、不写正式业务库、不调用券商接口、不自动交易。
标识：stock-recommendation-detail-mobile-layout-acceptance
"""

from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统")
PUSH_DRAFT = ROOT / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"
FRONT_STANDARD = ROOT / "01配置" / "股票前台输出标准_v2.json"
OUT_DIR = ROOT / "03数据" / "196推荐点击详情与手机排版验收"
LOCAL_BRIDGE_BASE = "http://127.0.0.1:19302"
ALLOWED_FRONT_URL = "http://43.167.210.211/wecom-bot/message?view=stock-reco"
ALLOWED_SINGLE_REPORT_RE = re.compile(r"http://43\.167\.210\.211/wecom-bot/message\?ask=分析[^\s]+")

REQUIRED_DETAIL_TERMS = ["结论", "操作策略", "关注条件", "价格观察", "风险提醒"]
FORBIDDEN_DETAIL_TERMS = ["你想看哪只股票", "我还没对齐你的意思", "需要补充股票", "股票图文报告暂不可用"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace") if path.exists() else ""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return {}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"名称": name, "通过": bool(passed), "说明": detail}


def extract_stock_links(text: str) -> list[dict[str, str]]:
    pattern = re.compile(r"\[([^\]]+\([^)]+\))\]\((https?://[^)]+/wecom-bot/message\?ask=[^)]+)\)")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        label = match.group(1).strip()
        url = match.group(2).strip()
        name_match = re.match(r"(.+?)\(([^)]+)\)", label)
        name = name_match.group(1).strip() if name_match else label
        code = name_match.group(2).strip() if name_match else ""
        key = f"{name}|{code}|{url}"
        if key in seen:
            continue
        seen.add(key)
        rows.append({"名称": name, "代码": code, "标签": label, "公网URL": url, "本地URL": to_local_url(url)})
    return rows


def to_local_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return urllib.parse.urlunparse(("http", "127.0.0.1:19302", parsed.path, "", parsed.query, ""))


def fetch_text(url: str, timeout: int = 25) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "jiege-stock-mobile-layout-check/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return int(response.status), raw


def fetch_bot_message_text(message: str) -> str:
    payload = json.dumps({"text": message}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{LOCAL_BRIDGE_BASE}/wecom-bot/message",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "jiege-stock-mobile-layout-check/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    stream = data.get("智能机器人回复", {}).get("stream", {}) if isinstance(data, dict) else {}
    return str(stream.get("content") or data.get("企业微信内容") or data.get("回复") or "")


def remove_allowed_front_urls(text: str) -> str:
    text = str(text or "").replace(ALLOWED_FRONT_URL, "")
    return ALLOWED_SINGLE_REPORT_RE.sub("", text)


def fetch_stock_reco_page() -> str:
    status, content = fetch_text(f"{LOCAL_BRIDGE_BASE}/wecom-bot/message?view=stock-reco")
    if status != 200:
        raise RuntimeError(f"stock-reco view HTTP {status}")
    return content


def visible_text(html_text: str) -> str:
    text = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", "", html_text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)


def mobile_layout_checks(content: str) -> list[dict[str, Any]]:
    text = visible_text(content)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    long_lines = [
        line for line in lines
        if len(line) > 48 and not line.startswith(("http://", "https://", "D:\\"))
    ]
    forbidden_placeholders = ["待补充 / 待补充", "待补充/待补充", "行业：待补充", "公司概况：当前系统已识别为待补充"]
    forbidden_front_terms = ["RSI", "MA5", "MA10", "MA20", "MA60", "MACD", "DIF", "DEA"]
    return [
        check("包含移动端viewport", 'name="viewport"' in content and "width=device-width" in content, "HTML头部需要适配手机宽度"),
        check("图片自适应手机宽度", "max-width:100%" in content, "图形报告图片不得撑破手机屏幕"),
        check("无HTML宽表格", "<table" not in content.lower(), "手机端详情页不使用宽表格"),
        check("正文长行可控", len(long_lines) == 0, long_lines[:5]),
        check("占位字段不直出", not any(term in text for term in forbidden_placeholders), forbidden_placeholders),
        check("前台不直出后台技术指标", not any(term in text for term in forbidden_front_terms), forbidden_front_terms),
    ]


def validate_detail_link(row: dict[str, str]) -> dict[str, Any]:
    item_checks: list[dict[str, Any]] = []
    try:
        status, content = fetch_text(row["本地URL"])
        text = visible_text(content)
        item_checks.extend([
            check("HTTP 200", status == 200, status),
            check("包含股票名称", row["名称"] in text, row["名称"]),
            check("不是缺股票澄清话术", not any(term in text for term in FORBIDDEN_DETAIL_TERMS), FORBIDDEN_DETAIL_TERMS),
            check("包含详细报告关键段落", all(term in text for term in REQUIRED_DETAIL_TERMS), REQUIRED_DETAIL_TERMS),
            check("包含图形报告图片", "<img " in content and "src=" in content, "详情页应显示图形报告图片"),
        ])
        item_checks.extend(mobile_layout_checks(content))
        excerpt = text[:500]
    except Exception as exc:
        item_checks.append(check("详情页可访问", False, str(exc)))
        excerpt = ""
    return {
        **row,
        "通过": all(item["通过"] for item in item_checks),
        "检查项": item_checks,
        "正文摘录": excerpt,
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票推荐点击详情与手机排版验收 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 验收结论：{report['验收结论']}",
        f"- 推荐/观察链接数量：{report['链接数量']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 二、链接检查",
        "",
    ]
    for item in report["链接详情"]:
        lines.append(f"- {'通过' if item['通过'] else '失败'}：{item['标签']} -> {item['本地URL']}")
        failed = [check_item for check_item in item["检查项"] if not check_item["通过"]]
        for failed_item in failed[:3]:
            lines.append(f"  - 失败项：{failed_item['名称']}；{failed_item['说明']}")
    lines.extend([
        "",
        "## 三、手机端排版口径",
        "",
        "- 点击股票名称后必须进入单股详细图文报告，不得回到“你想看哪只股票”的澄清回复。",
        "- 手机端优先：图片自适应宽度、少用表格、短段落、短列表、长句受控。",
        "- 图形报告图片、结论、操作策略、关注条件、价格观察和风险提醒必须保留。",
        "",
        "## 四、安全边界",
        "",
        "- 只访问本机 19302 / 19300。",
        "- 不真实发送企业微信。",
        "- 不触发 n8n。",
        "- 不重启服务。",
        "- 不写正式业务库，不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    draft = read_text(PUSH_DRAFT)
    standard = read_json(FRONT_STANDARD)
    single_template = standard.get("单股短答模板", {}) if isinstance(standard, dict) else {}
    forbidden_template_terms = single_template.get("禁止话术", []) if isinstance(single_template.get("禁止话术"), list) else []
    links = extract_stock_links(draft)
    link_results = [validate_detail_link(row) for row in links[:12]]
    try:
        expert_text = fetch_bot_message_text("请推荐几只股票")
        expert_error = ""
    except Exception as exc:
        expert_text = ""
        expert_error = str(exc)
    try:
        single_text = fetch_bot_message_text("分析摩尔线程")
        single_error = ""
    except Exception as exc:
        single_text = ""
        single_error = str(exc)
    try:
        risk_single_text = fetch_bot_message_text("分析正丹股份")
        risk_single_error = ""
    except Exception as exc:
        risk_single_text = ""
        risk_single_error = str(exc)
    try:
        stock_reco_html = fetch_stock_reco_page()
        stock_reco_error = ""
    except Exception as exc:
        stock_reco_html = ""
        stock_reco_error = str(exc)
    single_text_without_image = re.sub(r"!\[[^\]]+\]\(https?://[^)]+\)\s*", "", single_text)
    single_url_stripped = remove_allowed_front_urls(single_text_without_image)
    checks: list[dict[str, Any]] = [
        check("推送草案存在", PUSH_DRAFT.exists(), str(PUSH_DRAFT)),
        check("单股短答模板已固化到前台输出标准", bool(single_template), str(FRONT_STANDARD)),
        check("单股短答模板含量化标准", all(key in (single_template.get("量化标准", {}) if isinstance(single_template.get("量化标准"), dict) else {}) for key in ["承接区上沿比例", "成交活跃量比5日", "成交明显活跃量比5日"]), single_template.get("量化标准", {})),
        check("单股短答模板保存用户纠偏样例", all(term in "\n".join(str(x) for x in single_template.get("标准样例", [])) for term in ["承接成立", "近5日成交活跃度", "风险线", "wecom-bot/message?ask=分析"]), single_template.get("标准样例", [])),
        check("至少提取到5个股票详情链接", len(links) >= 5, len(links)),
        check("链接均使用ask=分析股票名", all("ask=" in row["公网URL"] and "分析" in urllib.parse.unquote(row["公网URL"]) for row in links), [row["公网URL"] for row in links]),
        check("详情链接全部通过", bool(link_results) and all(item["通过"] for item in link_results), [item["标签"] for item in link_results if not item["通过"]]),
        check("专家推荐总览可获取", bool(expert_text), expert_error or expert_text[:120]),
        check("专家推荐总览不暴露Markdown链接", not re.search(r"\[[^\]]+\]\(https?://", expert_text), expert_text[:300]),
        check("专家推荐总览只保留图文报告短入口", not re.search(r"https?://", expert_text.replace(ALLOWED_FRONT_URL, "")), expert_text[:500]),
        check("专家推荐总览恢复摘要信息密度", all(term in expert_text for term in ["今日摘要", "行业：", "得分：", "结论：", "关注点："]), expert_text[:700]),
        check("专家推荐总览保留星级", "⭐⭐⭐⭐" in expert_text, expert_text[:300]),
        check("专家推荐总览提供图文详情入口", ALLOWED_FRONT_URL in expert_text and "进入图文报告后可点股票名称" in expert_text, expert_text[-260:]),
        check("股票推荐图文页可获取", bool(stock_reco_html), stock_reco_error or stock_reco_html[:120]),
        check("股票推荐图文页含股票详情链接", stock_reco_html.count("/wecom-bot/message?ask=") >= 5, stock_reco_html[:500]),
        check("单股聊天短答可获取", bool(single_text), single_error or single_text[:120]),
        check("单股聊天短答图片置顶", single_text.startswith("![股票图形报告](") and "card=report_png" in single_text and "name=" in single_text, single_text[:260]),
        check("单股聊天短答不暴露Markdown文字链接", not re.search(r"(?<!!)\[[^\]]+\]\(https?://", single_text), single_text[:300]),
        check("单股聊天短答只保留单股详情直达入口", not re.search(r"https?://", single_url_stripped) and "wecom-bot/message?ask=分析" in single_text, single_text[:700]),
        check("单股聊天短答不直出后台指标", not re.search(r"\b(RSI|MA5|MA10|MA20|MA60|MACD|DIF|DEA)\b", single_text), single_text[:300]),
        check("单股聊天短答保留答案字段", all(term in single_text for term in ["当前判断", "操作策略", "关注条件", "风险线", "结论"]), single_text[:500]),
        check("单股聊天短答不提示不可用点击", "点击股票名称" not in single_text, single_text[:500]),
        check("单股聊天短答无模糊旧话术", not any(term in single_text for term in (forbidden_template_terms or ["按观察线跟踪", "证据仍需补齐", "承接和成交量持续性", "聊天先给结论", "成交量保持活跃"])), single_text[:700]),
        check("单股聊天短答给出大白话量化标准", all(term in single_text for term in ["近5日成交活跃度", "平时的1.10倍", "承接成立", "风险线", "成交标准"]), single_text[:700]),
        check("风险股票短答可获取", bool(risk_single_text), risk_single_error or risk_single_text[:120]),
        check("风险股票不再写已跌破风险线为未来条件", "跌破20.04元" not in risk_single_text and "当前已低于20.04元风险线" in risk_single_text, risk_single_text[:900]),
        check("风险股票说明站上口径", "当天收盘价或当前实时价高于18.90元" in risk_single_text and "连续2个交易日收盘价" in risk_single_text, risk_single_text[:900]),
        check("风险股票无无意义边界声明", "边界：研究提醒" not in risk_single_text and "最终由你人工判断" not in risk_single_text, risk_single_text[-300:]),
    ]
    failed_checks = [item for item in checks if not item["通过"]]
    failed_links = [item for item in link_results if not item["通过"]]
    report: dict[str, Any] = {
        "名称": "股票推荐点击详情与手机排版验收",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": str(Path(__file__).resolve()),
        "推送草案": str(PUSH_DRAFT),
        "验收结论": "通过：推荐股票点击详情和手机端基础排版可用" if not failed_checks and not failed_links else "失败：存在点击详情或手机排版问题",
        "链接数量": len(links),
        "通过数量": len(link_results) - len(failed_links),
        "失败数量": len(failed_links) + len(failed_checks),
        "总检查项": checks,
        "链接详情": link_results,
        "专家推荐总览样本": expert_text,
        "单股聊天短答样本": single_text,
        "风险股票短答样本": risk_single_text,
        "安全边界": {
            "触发n8n": False,
            "企业微信真实发送": False,
            "重启服务": False,
            "写正式业务库": False,
            "券商接口": False,
            "自动交易": False,
        },
    }
    write_json(OUT_DIR / f"股票推荐点击详情与手机排版验收_{stamp}.json", report)
    write_json(OUT_DIR / "股票推荐点击详情与手机排版验收_最新.json", report)
    markdown = build_markdown(report)
    write_text(OUT_DIR / f"股票推荐点击详情与手机排版验收_{stamp}.md", markdown)
    write_text(OUT_DIR / "股票推荐点击详情与手机排版验收_最新.md", markdown)
    print(json.dumps({
        "状态": report["验收结论"],
        "链接数量": report["链接数量"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(OUT_DIR / "股票推荐点击详情与手机排版验收_最新.md"),
    }, ensure_ascii=False))
    return 0 if report["失败数量"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
