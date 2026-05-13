# -*- coding: utf-8 -*-
"""生成股票单股前台闭环对齐包。

目标：不新造链路，只把现有“单股报告 -> 证据映射 -> 企业微信短答 -> 推送巡检
-> 前台实样门禁”收口到同一只股票，形成一个本地可验收的业务闭环。

安全边界：只读现有本地资产，只写 03数据/290股票单股前台闭环对齐包；
不真实发送、不触发 n8n、不访问 Webhook、不切正式入口、不重启服务、不写正式库、
不调用券商接口、不自动交易。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
OUT_DIR = DATA / "290股票单股前台闭环对齐包"
JSON_OUT = OUT_DIR / "股票单股前台闭环对齐包_最新.json"
MD_OUT = OUT_DIR / "股票单股前台闭环对齐包_最新.md"


ASSETS = [
    {
        "id": "single_report",
        "name": "单股标准报告v2",
        "role": "承载当前单股分析正文、价格、风险线、证据缺口",
        "path": DATA / "135分层日报" / "单股标准报告v2_最新.md",
        "required": True,
    },
    {
        "id": "evidence_map",
        "name": "股票报告证据源映射预览",
        "role": "把报告字段对应到本地证据源和缺口",
        "path": DATA / "219股票报告证据源映射" / "股票报告证据源映射预览_最新.json",
        "required": True,
    },
    {
        "id": "evidence_map_validation",
        "name": "股票报告证据源映射验收",
        "role": "确认证据映射本地验收通过",
        "path": DATA / "219股票报告证据源映射" / "股票报告证据源映射预览验收_最新.json",
        "required": True,
        "require_pass": True,
    },
    {
        "id": "wecom_short_reply",
        "name": "企业微信单股短回复",
        "role": "双前台中的用户可读短答草稿",
        "path": DATA / "24企业微信短回复" / "企业微信单股短回复_最新.json",
        "required": True,
    },
    {
        "id": "wecom_shadow_validation",
        "name": "企业微信短回复 shadow_v21 实跑输出验收",
        "role": "确认短答 dry-run 已走通且没有真实发送",
        "path": DATA / "231企业微信短回复shadow_v21_dry_run" / "企业微信单股短回复shadow_v21_dry_run实跑输出验收_最新.json",
        "required": True,
        "require_pass": True,
    },
    {
        "id": "daily_push_readonly",
        "name": "股票每日推送总表只读巡检",
        "role": "确认 08:50、15:30、21:00 推送任务和样本锚点存在",
        "path": DATA / "股票每日推送总表只读巡检" / "股票每日推送总表只读巡检报告_最新.json",
        "required": True,
        "require_pass": True,
    },
    {
        "id": "frontend_real_sample_gate",
        "name": "股票前台报告实样影子门禁",
        "role": "检查真实报告是否符合前台结果表达要求",
        "path": DATA / "289股票前台报告实样影子门禁" / "股票前台报告实样影子门禁_最新.json",
        "required": True,
    },
    {
        "id": "frontend_real_sample_gate_validation",
        "name": "股票前台报告实样影子门禁验收",
        "role": "确认前台实样门禁本身可运行",
        "path": DATA / "289股票前台报告实样影子门禁" / "股票前台报告实样影子门禁验收_最新.json",
        "required": True,
        "require_pass": True,
    },
]


RISK_ACTION_KEYS = ["真实发送", "触发n8n", "Webhook", "正式入口", "服务重启", "正式库", "券商", "自动交易", "下单"]
ACTION_CONTEXT_KEYS = ["实际动作", "本次是否", "执行动作", "执行结果", "已执行", "已触发", "已发送", "调用结果"]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True) if value is not None else ""


def walk(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            rows.extend(walk(child, f"{prefix}.{key}" if prefix else str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(walk(child, f"{prefix}[{index}]"))
    else:
        rows.append((prefix, value))
    return rows


def pass_signal(value: Any) -> bool:
    text = json_text(value)
    return any(token in text for token in ["通过", '"pass"', '"ok"', "验收通过", '"passed": true', '"passed":true'])


def risk_true_hits(value: Any) -> list[str]:
    hits: list[str] = []
    for path, child in walk(value):
        if child is not True:
            continue
        if not any(context in path for context in ACTION_CONTEXT_KEYS):
            continue
        if any(skip in path for skip in ["安全总开关", "安全开关", "正式入口快照", "存在"]):
            continue
        if any(key in path for key in RISK_ACTION_KEYS):
            hits.append(path)
    return hits


def normalize_code(text: str) -> str:
    value = str(text or "").strip().lower()
    match = re.search(r"(sh|sz|bj)\s*[-_\.]?\s*(\d{6})", value)
    if match:
        return match.group(1) + match.group(2)
    match = re.search(r"\b(\d{6})\b", value)
    if not match:
        return ""
    code = match.group(1)
    if code.startswith(("6", "9")):
        return "sh" + code
    if code.startswith(("4", "8")):
        return "bj" + code
    return "sz" + code


def extract_stock_identity() -> dict[str, str]:
    sources = [
        load_json(DATA / "24企业微信短回复" / "企业微信单股短回复_最新.json"),
        load_json(DATA / "219股票报告证据源映射" / "股票报告证据源映射预览_最新.json"),
        read_text(DATA / "135分层日报" / "单股标准报告v2_最新.md"),
    ]
    name = ""
    code = ""
    display_code = ""
    for source in sources:
        text = json_text(source) if not isinstance(source, str) else source
        if not code:
            code = normalize_code(text)
        if not display_code and code:
            display_code = f"{code[2:]}.{code[:2].upper()}"
        if not name:
            for candidate in ["永鼎股份", "新易盛", "云南锗业", "正丹股份", "中际旭创", "润建股份", "沪电股份"]:
                if candidate in text:
                    name = candidate
                    break
    return {"名称": name or "未识别", "代码": code, "展示代码": display_code}


def inspect_asset(asset: dict[str, Any], stock: dict[str, str]) -> dict[str, Any]:
    path = asset["path"]
    exists = path.exists()
    data = load_json(path) if exists and path.suffix.lower() == ".json" else None
    text = json_text(data) if data is not None else read_text(path)
    stock_name = stock.get("名称", "")
    stock_code = stock.get("代码", "")
    code6 = stock_code[2:] if len(stock_code) == 8 else ""
    pass_ok = pass_signal(data) if data is not None else True
    stock_match = bool(
        exists
        and (
            not stock_code
            or stock_code in text.lower()
            or code6 in text
            or (stock_name and stock_name in text)
            or asset["id"] in {"daily_push_readonly", "frontend_real_sample_gate", "frontend_real_sample_gate_validation"}
        )
    )
    problems: list[str] = []
    if asset.get("required") and not exists:
        problems.append("缺少资产")
    if exists and asset.get("require_pass") and not pass_ok:
        problems.append("验收未通过")
    if exists and not stock_match:
        problems.append("未对齐到当前标的")
    risky = risk_true_hits(data) if data is not None else []
    if risky:
        problems.append("存在红线动作开启")
    return {
        "id": asset["id"],
        "name": asset["name"],
        "role": asset["role"],
        "path": str(path),
        "exists": exists,
        "sha256": sha256(path),
        "bytes": path.stat().st_size if exists and path.is_file() else 0,
        "pass_signal": pass_ok,
        "stock_match": stock_match,
        "risk_true_hits": risky,
        "status": "pass" if not problems else "review",
        "problems": problems,
    }


def build_report() -> dict[str, Any]:
    stock = extract_stock_identity()
    assets = [inspect_asset(item, stock) for item in ASSETS]
    frontend_gate = load_json(DATA / "289股票前台报告实样影子门禁" / "股票前台报告实样影子门禁_最新.json") or {}
    must_fix_total = int(frontend_gate.get("must_fix_total") or 0)
    review_total = int(frontend_gate.get("review_total") or 0)
    hard_reviews = [asset for asset in assets if asset["status"] != "pass"]
    safety_boundary = {
        "真实发送": False,
        "真实n8n": False,
        "Webhook": False,
        "正式入口切换": False,
        "服务重启": False,
        "正式库写入": False,
        "券商接口": False,
        "自动交易": False,
    }
    deliverable = not hard_reviews
    return {
        "名称": "股票单股前台闭环对齐包",
        "版本": "v1.0",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "标的": stock,
        "阶段结论": "本地影子闭环可交付" if deliverable else "本地影子闭环待补齐",
        "可交付": deliverable,
        "资产数量": len(assets),
        "通过资产数": sum(1 for item in assets if item["status"] == "pass"),
        "待补齐资产数": len(hard_reviews),
        "前台报告表达缺口": {
            "必改缺口数": must_fix_total,
            "复核提示数": review_total,
            "处理口径": "不阻断本地链路交付，但进入下一轮前台报告生成器优化；重点补齐具体价量阈值和后续只盯事项。",
        },
        "闭环链路": [
            "单股标准报告v2",
            "股票报告证据源映射",
            "企业微信短回复 dry-run",
            "每日推送总表只读巡检",
            "股票前台报告实样影子门禁",
        ],
        "资产检查": assets,
        "下一步收口": [
            "把前台报告表达缺口回补到单股报告生成逻辑，不让使用者二次计算价量阈值。",
            "把本对齐包纳入样本房本地验收面板，形成业务闭环验收项。",
            "CircleCI 只做后台守门，不作为主线等待点。",
        ],
        "安全边界": safety_boundary,
    }


def render_markdown(report: dict[str, Any]) -> str:
    stock = report["标的"]
    lines = [
        "# 股票单股前台闭环对齐包",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 标的：{stock.get('名称')}（{stock.get('展示代码') or stock.get('代码')}）",
        f"- 阶段结论：{report['阶段结论']}",
        f"- 可交付：{str(report['可交付']).lower()}",
        f"- 资产数量：{report['资产数量']}",
        f"- 通过资产数：{report['通过资产数']}",
        f"- 待补齐资产数：{report['待补齐资产数']}",
        "",
        "## 闭环链路",
        "",
    ]
    lines.extend([f"- {item}" for item in report["闭环链路"]])
    lines.extend(["", "## 前台报告表达缺口", ""])
    gap = report["前台报告表达缺口"]
    lines.extend([
        f"- 必改缺口数：{gap['必改缺口数']}",
        f"- 复核提示数：{gap['复核提示数']}",
        f"- 处理口径：{gap['处理口径']}",
        "",
        "## 资产检查",
        "",
    ])
    for item in report["资产检查"]:
        lines.append(f"- [{item['status']}] {item['name']}：{item['role']}；stock_match={str(item['stock_match']).lower()}；path={item['path']}")
        if item["problems"]:
            lines.append(f"  - 问题：{'; '.join(item['problems'])}")
    lines.extend(["", "## 下一步收口", ""])
    lines.extend([f"- {item}" for item in report["下一步收口"]])
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{str(value).lower()}")
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    JSON_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    MD_OUT.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "状态": report["阶段结论"],
        "可交付": report["可交付"],
        "标的": report["标的"],
        "待补齐资产数": report["待补齐资产数"],
        "前台必改缺口数": report["前台报告表达缺口"]["必改缺口数"],
    }, ensure_ascii=False))
    return 0 if report["可交付"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
