# -*- coding: utf-8 -*-
"""
名称：执行重点观察池人工确认写入.py
作用：生成重点观察池晋级候选账；仅在人工确认后受控写回重点关注股票池.json。
安全边界：默认只写候选账；未提供--apply和有效人工确认文件时，不修改正式重点关注池。
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


CONFIRM_TEXT = "我确认写入重点关注股票池"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None, required: bool = False) -> Any:
    if not path.exists():
        if required:
            raise FileNotFoundError(str(path))
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_code(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    lower = text.lower()
    if lower.startswith(("sh", "sz", "bj")):
        return lower
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) != 6:
        return text
    if digits.startswith(("6", "9")):
        return f"sh{digits}"
    if digits.startswith(("0", "2", "3")):
        return f"sz{digits}"
    if digits.startswith(("4", "8")):
        return f"bj{digits}"
    return digits


def market_from_code(code: str) -> str:
    if code.startswith("sh"):
        return "上交所"
    if code.startswith("sz"):
        return "深交所"
    if code.startswith("bj"):
        return "北交所"
    return ""


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def focus_codes(focus_data: dict[str, Any]) -> set[str]:
    rows = focus_data.get("股票池", []) if isinstance(focus_data.get("股票池"), list) else []
    return {normalize_code(item.get("代码")) for item in rows if isinstance(item, dict) and normalize_code(item.get("代码"))}


def add_candidate(candidates: dict[str, dict[str, Any]], code: str, name: str, industry: str, source: str, reason: str, score: float) -> None:
    if not code:
        return
    row = candidates.setdefault(code, {
        "代码": code,
        "名称": name,
        "行业": industry,
        "来源类型": [],
        "晋级理由": [],
        "候选分": 0.0,
    })
    row["名称"] = row.get("名称") or name
    row["行业"] = row.get("行业") or industry
    if source not in row["来源类型"]:
        row["来源类型"].append(source)
    if reason and reason not in row["晋级理由"]:
        row["晋级理由"].append(reason)
    row["候选分"] += score


def collect_l5(candidates: dict[str, dict[str, Any]], l5_data: dict[str, Any]) -> None:
    for item in l5_data.get("股票池", []) if isinstance(l5_data.get("股票池"), list) else []:
        if not isinstance(item, dict):
            continue
        code = normalize_code(item.get("代码"))
        score = to_float(item.get("调整分"))
        reason = f"L5入选，调整分{score:.2f}，行业强度{to_float(item.get('行业强度分')):.2f}。"
        add_candidate(candidates, code, str(item.get("名称", "")), str(item.get("行业", "")), "L5入选", reason, 40 + score)


def collect_strong_resonance(candidates: dict[str, dict[str, Any]], close_data: dict[str, Any]) -> None:
    for item in close_data.get("股票", []) if isinstance(close_data.get("股票"), list) else []:
        if not isinstance(item, dict):
            continue
        code = normalize_code(item.get("代码"))
        for signal in item.get("指标共振信号", []) if isinstance(item.get("指标共振信号"), list) else []:
            if not isinstance(signal, dict):
                continue
            if signal.get("触发") is True and "强势突破" in str(signal.get("规则名称", "")):
                reason = "强势突破确认信号触发，可提升该标的观察优先级。"
                add_candidate(candidates, code, str(item.get("名称", "")), "", "强共振触发", reason, 55)


def collect_feedback(candidates: dict[str, dict[str, Any]], feedback_data: dict[str, Any]) -> None:
    for item in feedback_data.get("反馈记录", []) if isinstance(feedback_data.get("反馈记录"), list) else []:
        if not isinstance(item, dict) or item.get("是否有效") is False:
            continue
        code = normalize_code(item.get("代码"))
        if not code:
            continue
        reason = f"用户反馈：{item.get('反馈类型', '')}；{item.get('理由', '')}"
        add_candidate(candidates, code, str(item.get("名称", "")), str(item.get("行业", "")), "用户反馈", reason, 20)


def build_candidate_account(root: Path) -> dict[str, Any]:
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    l5_path = root / "03数据" / "134深度研究池" / "L5深度研究池_最新.json"
    close_path = out_dir / "收盘短线观察_基于300只轻扫描_最新.json"
    feedback_path = root / "04日志" / "用户反馈" / "反馈日志.json"
    focus_path = root / "01配置" / "重点关注股票池.json"

    l5_data = load_json(l5_path, {})
    close_data = load_json(close_path, {})
    feedback_data = load_json(feedback_path, {})
    focus_data = load_json(focus_path, {"股票池": []})
    existing = focus_codes(focus_data if isinstance(focus_data, dict) else {})

    candidates: dict[str, dict[str, Any]] = {}
    collect_l5(candidates, l5_data if isinstance(l5_data, dict) else {})
    collect_strong_resonance(candidates, close_data if isinstance(close_data, dict) else {})
    collect_feedback(candidates, feedback_data if isinstance(feedback_data, dict) else {})

    rows = sorted(candidates.values(), key=lambda item: item["候选分"], reverse=True)
    for row in rows:
        row["候选分"] = round(row["候选分"], 2)
        row["已在重点关注池"] = row["代码"] in existing
        row["候选状态"] = "待人工确认"
        row["建议动作"] = "已在重点关注池，仅记录晋级来源" if row["已在重点关注池"] else "可提交人工确认后写入重点关注股票池"

    return {
        "名称": "重点观察池晋级候选账",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "候选来源": {
            "L5入选": str(l5_path),
            "强共振触发": str(close_path),
            "用户反馈": str(feedback_path),
            "正式重点关注池": str(focus_path),
        },
        "候选数量": len(rows),
        "待人工确认数量": len([item for item in rows if not item["已在重点关注池"]]),
        "候选": rows,
        "人工确认模板": {
            "确认状态": "已人工确认",
            "确认指令": CONFIRM_TEXT,
            "确认人": "",
            "确认时间": "",
            "确认项": [
                {
                    "代码": "sh688047",
                    "人工确认": "纳入",
                    "变更原因": "示例：L5入选且用户明确要求纳入重点观察池"
                }
            ]
        },
        "安全边界": {
            "是否自动改正式池": False,
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }


def save_candidate_account(root: Path, account: dict[str, Any]) -> Path:
    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = out_dir / f"重点观察池晋级候选账_{stamp}.json"
    latest = out_dir / "重点观察池晋级候选账_最新.json"
    write_json(output, account)
    write_json(latest, account)
    return latest


def validate_confirmation(confirm: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if str(confirm.get("确认状态") or confirm.get("人工确认状态") or "") != "已人工确认":
        errors.append("确认状态不是已人工确认")
    if CONFIRM_TEXT not in str(confirm.get("确认指令") or confirm.get("确认文本") or ""):
        errors.append(f"确认指令必须包含：{CONFIRM_TEXT}")
    if not str(confirm.get("确认人", "")).strip():
        errors.append("确认人为空")
    if not isinstance(confirm.get("确认项"), list) or not confirm.get("确认项"):
        errors.append("确认项为空")
    return errors


def apply_confirmed_write(root: Path, account: dict[str, Any], confirm_path: Path) -> dict[str, Any]:
    confirm = load_json(confirm_path, {}, required=True)
    if not isinstance(confirm, dict):
        raise ValueError("人工确认文件不是JSON对象")
    errors = validate_confirmation(confirm)
    if errors:
        return {
            "执行状态": "blocked",
            "阻断原因": errors,
            "写入数量": 0,
            "安全说明": "未通过人工确认闸口，未修改正式重点关注池。",
        }

    candidate_index = {item["代码"]: item for item in account.get("候选", []) if isinstance(item, dict)}
    focus_path = root / "01配置" / "重点关注股票池.json"
    focus = load_json(focus_path, {"股票池": []}, required=True)
    if not isinstance(focus, dict):
        raise ValueError("重点关注股票池格式不是JSON对象")
    rows = focus.setdefault("股票池", [])
    if not isinstance(rows, list):
        raise ValueError("重点关注股票池.股票池不是列表")
    existing = focus_codes(focus)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / "01配置" / "备份"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"重点关注股票池_{stamp}_写入前备份.json"
    shutil.copy2(focus_path, backup_path)

    written: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for item in confirm.get("确认项", []):
        if not isinstance(item, dict):
            continue
        code = normalize_code(item.get("代码"))
        action = str(item.get("人工确认") or item.get("动作") or "")
        if action not in {"纳入", "写入", "确认纳入", "新增"}:
            skipped.append({"代码": code, "原因": f"人工确认动作不是纳入类：{action}"})
            continue
        candidate = candidate_index.get(code)
        if not candidate:
            skipped.append({"代码": code, "原因": "不在晋级候选账内"})
            continue
        if code in existing:
            skipped.append({"代码": code, "原因": "已在重点关注股票池"})
            continue
        reason = str(item.get("变更原因") or "人工确认纳入重点观察池")
        rows.append({
            "代码": code,
            "名称": candidate.get("名称", ""),
            "市场": market_from_code(code),
            "关注级别": "重点",
            "来源": f"人工确认晋级候选账；{reason}",
            "行业": candidate.get("行业", ""),
            "纳入日期": datetime.now().strftime("%Y-%m-%d"),
            "晋级来源": candidate.get("来源类型", []),
            "回滚备份": str(backup_path),
        })
        existing.add(code)
        written.append({"代码": code, "名称": candidate.get("名称", ""), "变更原因": reason})

    focus["股票数量"] = len(rows)
    focus["创建修改记录"] = f"{focus.get('创建修改记录', '')}；{datetime.now().strftime('%Y-%m-%d')} 人工确认写入重点观察池晋级候选。"
    write_json(focus_path, focus)
    return {
        "执行状态": "success",
        "写入数量": len(written),
        "跳过数量": len(skipped),
        "写入": written,
        "跳过": skipped,
        "回滚备份": str(backup_path),
        "正式池": str(focus_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="生成重点观察池晋级候选账，并在人工确认后受控写回正式重点关注池。")
    parser.add_argument("--apply", action="store_true", help="执行人工确认写入；不加此参数时只刷新候选账。")
    parser.add_argument("--confirm-file", default="", help="人工确认JSON文件路径。")
    args = parser.parse_args()

    root = module_root()
    account = build_candidate_account(root)
    latest = save_candidate_account(root, account)
    result: dict[str, Any] = {
        "执行状态": "candidate_account_refreshed",
        "候选账": str(latest),
        "写正式池": False,
    }
    exit_code = 0
    if args.apply:
        if not args.confirm_file:
            result = {"执行状态": "blocked", "阻断原因": ["缺少--confirm-file"], "候选账": str(latest), "写正式池": False}
            exit_code = 2
        else:
            result = apply_confirmed_write(root, account, Path(args.confirm_file))
            result["候选账"] = str(latest)
            result["写正式池"] = result.get("执行状态") == "success"
            exit_code = 0 if result.get("执行状态") == "success" else 2

    out_dir = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    write_json(out_dir / f"重点观察池人工确认写入执行记录_{stamp}.json", result)
    write_json(out_dir / "重点观察池人工确认写入执行记录_最新.json", result)
    print(json.dumps(result, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
