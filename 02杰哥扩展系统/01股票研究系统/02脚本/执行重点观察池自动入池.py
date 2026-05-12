# -*- coding: utf-8 -*-
"""
名称：执行重点观察池自动入池.py
作用：读取重点观察池晋级候选账，把满足条件的股票自动写入重点关注股票池。
安全边界：只写重点关注股票池配置、备份和变更日志；不触发n8n；不发送企业微信；不接券商；不交易。
"""

from __future__ import annotations

import getpass
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from 重点观察池晋级候选公共库 import normalize_code


AUTO_SOURCES = {"L5入选", "短线反弹共振信号", "强势突破确认信号", "用户反馈"}


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def market_from_code(code: str) -> str:
    if code.startswith("sh"):
        return "上交所"
    if code.startswith("sz"):
        return "深交所"
    if code.startswith("bj"):
        return "北交所"
    return ""


def focus_codes(focus: dict[str, Any]) -> set[str]:
    rows = focus.get("股票池", []) if isinstance(focus.get("股票池"), list) else []
    return {normalize_code(item.get("代码")) for item in rows if isinstance(item, dict) and normalize_code(item.get("代码"))}


def candidate_sources(item: dict[str, Any]) -> set[str]:
    raw = item.get("来源类型", [])
    if isinstance(raw, str):
        return {raw}
    if isinstance(raw, list):
        return {str(x) for x in raw if str(x)}
    return set()


def auto_allowed(item: dict[str, Any]) -> bool:
    if item.get("候选状态") in {"已自动入池", "已在重点关注池"}:
        return False
    return bool(candidate_sources(item) & AUTO_SOURCES)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    account_path = root / "03数据" / "260股票n8n日内报告闭环与晨报推送策略包" / "重点观察池晋级候选账_最新.json"
    focus_path = root / "01配置" / "重点关注股票池.json"
    account = load_json(account_path, {})
    focus = load_json(focus_path, {"股票池": []})
    rows = focus.setdefault("股票池", [])
    existing = focus_codes(focus)

    candidates = account.get("候选", []) if isinstance(account.get("候选"), list) else []
    to_add = []
    skipped = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        code = normalize_code(item.get("代码"))
        if not code:
            skipped.append({"代码": "", "原因": "代码为空"})
            continue
        if code in existing:
            item["候选状态"] = "已在重点关注池"
            skipped.append({"代码": code, "名称": item.get("名称", ""), "原因": "已在重点关注池"})
            continue
        if not auto_allowed(item):
            skipped.append({"代码": code, "名称": item.get("名称", ""), "原因": "来源未满足自动入池条件或状态已完成"})
            continue
        to_add.append((code, item))

    backup_path = ""
    written = []
    if to_add:
        backup_dir = root / "01配置" / "备份"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"重点关注股票池_{stamp}_自动入池前备份.json"
        shutil.copy2(focus_path, backup)
        backup_path = str(backup)
        for code, item in to_add:
            reason = "；".join(str(x) for x in item.get("晋级理由", []) if str(x)) or "晋级候选账满足自动入池条件"
            rows.append({
                "代码": code,
                "名称": item.get("名称", ""),
                "市场": market_from_code(code),
                "关注级别": "重点",
                "来源": f"自动晋级候选账；{reason}",
                "行业": item.get("行业", ""),
                "纳入日期": now.strftime("%Y-%m-%d"),
                "入池原因": reason,
                "触发时间": item.get("最近触发时间") or item.get("触发时间") or account.get("生成时间"),
                "晋级来源": sorted(candidate_sources(item)),
                "回滚备份": backup_path,
            })
            existing.add(code)
            item["候选状态"] = "已自动入池"
            item["自动入池时间"] = now.strftime("%Y-%m-%d %H:%M:%S")
            written.append({
                "代码": code,
                "名称": item.get("名称", ""),
                "入池原因": reason,
                "触发时间": item.get("触发时间") or item.get("最近触发时间"),
                "来源类型": sorted(candidate_sources(item)),
            })
        focus["股票数量"] = len(rows)
        focus["创建修改记录"] = f"{focus.get('创建修改记录', '')}；{now.strftime('%Y-%m-%d')} 自动晋级候选账写入{len(written)}只。"
        write_json(focus_path, focus)
        account["更新时间"] = now.strftime("%Y-%m-%d %H:%M:%S")
        account["待自动入池数量"] = len([item for item in candidates if isinstance(item, dict) and item.get("候选状态") == "待自动入池"])
        write_json(account_path, account)

    log = {
        "名称": "重点观察池自动入池变更日志",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "执行人": getpass.getuser(),
        "候选账": str(account_path),
        "正式池": str(focus_path),
        "写入前备份": backup_path,
        "写入数量": len(written),
        "跳过数量": len(skipped),
        "写入": written,
        "跳过": skipped,
        "安全边界": {
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }
    log_dir = root / "04日志" / "重点观察池自动入池"
    write_json(log_dir / f"重点观察池自动入池变更日志_{stamp}.json", log)
    write_json(log_dir / "重点观察池自动入池变更日志_最新.json", log)
    print(json.dumps({"写入数量": len(written), "跳过数量": len(skipped), "变更日志": str(log_dir / "重点观察池自动入池变更日志_最新.json")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
