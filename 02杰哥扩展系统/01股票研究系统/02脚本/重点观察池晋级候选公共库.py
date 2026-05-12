# -*- coding: utf-8 -*-
"""
名称：重点观察池晋级候选公共库.py
作用：为L5、共振信号、用户反馈等来源统一写入重点观察池晋级候选账。
安全边界：只写候选账，不直接修改重点关注股票池；正式写入由自动入池执行器负责备份、记录和回滚。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def candidate_account_path(root: Path | None = None) -> Path:
    base = root or module_root()
    return base / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "重点观察池晋级候选账_最新.json"


def normalize_code(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lower = text.lower()
    if lower.startswith(("sh", "sz", "bj")):
        return lower
    if "." in text:
        code, suffix = text.split(".", 1)
        suffix = suffix.upper()
        if suffix == "SH":
            return f"sh{code}"
        if suffix == "SZ":
            return f"sz{code}"
        if suffix == "BJ":
            return f"bj{code}"
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) != 6:
        return lower
    if digits.startswith(("6", "9")):
        return f"sh{digits}"
    if digits.startswith(("0", "2", "3")):
        return f"sz{digits}"
    if digits.startswith(("4", "8")):
        return f"bj{digits}"
    return digits


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_account(path: Path) -> dict[str, Any]:
    data = load_json(path, {})
    if not isinstance(data, dict):
        data = {}
    rows = data.get("候选")
    if not isinstance(rows, list):
        rows = []
    data.setdefault("名称", "重点观察池晋级候选账")
    data.setdefault("生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    data["候选"] = rows
    data.setdefault("安全边界", {
        "是否自动改正式池": False,
        "是否触发n8n": False,
        "是否真实发送企业微信": False,
        "是否接券商": False,
        "是否交易": False,
    })
    return data


def register_promotion_candidate(
    *,
    code: Any,
    name: Any,
    source_type: str,
    reason: str,
    trigger_time: str | None = None,
    industry: Any = "",
    score: Any = None,
    evidence: dict[str, Any] | None = None,
    source_path: str = "",
    root: Path | None = None,
) -> dict[str, Any]:
    stock_root = root or module_root()
    path = candidate_account_path(stock_root)
    account = load_account(path)
    now = trigger_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    norm_code = normalize_code(code)
    if not norm_code:
        return {"写入": False, "原因": "代码为空", "候选账": str(path)}

    rows = account["候选"]
    existing = None
    for item in rows:
        if isinstance(item, dict) and normalize_code(item.get("代码")) == norm_code:
            existing = item
            break

    if existing is None:
        existing = {
            "代码": norm_code,
            "名称": str(name or ""),
            "行业": str(industry or ""),
            "来源类型": [],
            "晋级理由": [],
            "触发时间": now,
            "最近触发时间": now,
            "候选分": 0.0,
            "候选状态": "待自动入池",
            "建议动作": "满足自动入池条件，等待执行重点观察池自动入池.py",
            "证据": [],
        }
        rows.append(existing)

    if str(name or "") and not existing.get("名称"):
        existing["名称"] = str(name)
    if str(industry or "") and not existing.get("行业"):
        existing["行业"] = str(industry)
    if source_type and source_type not in existing["来源类型"]:
        existing["来源类型"].append(source_type)
    if reason and reason not in existing["晋级理由"]:
        existing["晋级理由"].append(reason)
    existing["最近触发时间"] = now
    try:
        existing["候选分"] = round(float(existing.get("候选分") or 0) + float(score or 0), 4)
    except (TypeError, ValueError):
        existing["候选分"] = existing.get("候选分") or 0.0
    if evidence or source_path:
        existing.setdefault("证据", []).append({
            "时间": now,
            "来源类型": source_type,
            "来源文件": source_path,
            "证据": evidence or {},
        })

    account["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    account["更新时间"] = account["生成时间"]
    account["候选数量"] = len(rows)
    account["待自动入池数量"] = len([item for item in rows if isinstance(item, dict) and item.get("候选状态") in {"待自动入池", "待人工确认"}])
    write_json(path, account)
    return {"写入": True, "代码": norm_code, "候选账": str(path)}
