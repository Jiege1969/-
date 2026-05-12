# -*- coding: utf-8 -*-
"""
名称：upgrade_window_check.py
作用：读取升级规则，判断当前时间属于禁止窗口、影子窗口、执行窗口或普通只读窗口。
触发方式：python upgrade_window_check.py
依赖：upgrade_governance_common.py；upgrade_rules.json。
所属系统：00杰哥系统总管/版本升级治理
输出：04日志/版本升级治理/upgrade_window_check_latest.json。
安全边界：只读判断和写日志；不调度、不执行升级、不启停服务、不触发 n8n。
创建/修改记录：2026-05-03 创建版本治理 V1.1 只读脚本；2026-05-03 补齐标准标头。
标识：upgrade-governance-window-check
"""

from __future__ import annotations

import json
from datetime import datetime, time

from upgrade_governance_common import LOG_DIR, NO_ACTION_BOUNDARY, RULES, load_json, now_stamp, write_json


def in_range(now_time: time, start: time, end: time) -> bool:
    if start <= end:
        return start <= now_time <= end
    return now_time >= start or now_time <= end


def classify(now: datetime) -> dict[str, object]:
    weekday = now.weekday()  # Monday = 0
    now_time = now.time()
    reasons: list[str] = []

    trading_window = weekday <= 4 and in_range(now_time, time(8, 0), time(16, 30))
    if trading_window:
        reasons.append("工作日08:00-16:30属于禁止窗口，优先保障股票系统日常使用")
        return {"窗口": "禁止窗口", "允许影子试验": False, "允许正式切换": False, "原因": reasons}

    execution_window = in_range(now_time, time(22, 0), time(6, 0)) or (weekday == 5 and in_range(now_time, time(14, 0), time(18, 0)))
    if execution_window:
        reasons.append("当前处于执行窗口；仍需备份、回滚、影子验收和授权")
        return {"窗口": "执行窗口", "允许影子试验": True, "允许正式切换": "仅在授权和验收齐备时", "原因": reasons}

    shadow_window = in_range(now_time, time(18, 0), time(23, 0)) or weekday >= 5
    if shadow_window:
        reasons.append("当前处于影子试验窗口；只能做影子、样本、旁路或预案")
        return {"窗口": "影子窗口", "允许影子试验": True, "允许正式切换": False, "原因": reasons}

    reasons.append("当前不属于明确影子/执行窗口；只适合只读检查和生成预案")
    return {"窗口": "普通只读窗口", "允许影子试验": False, "允许正式切换": False, "原因": reasons}


def main() -> int:
    now, stamp = now_stamp()
    rules = load_json(RULES, {})
    verdict = classify(now)
    report = {
        "名称": "升级窗口只读判断",
        "版本": "V1.1",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(RULES),
        "规则摘要": rules.get("时间窗口", {}),
        "判断": verdict,
        "安全边界": NO_ACTION_BOUNDARY,
        "结论": "只判断窗口，不触发升级、不创建容器、不启停服务。",
    }
    path = LOG_DIR / f"upgrade_window_{stamp}.json"
    latest = LOG_DIR / "upgrade_window_latest.json"
    write_json(path, report)
    write_json(latest, report)
    print(json.dumps({"状态": "完成", "窗口": verdict["窗口"], "报告": str(latest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
