# -*- coding: utf-8 -*-
"""
名称：验证股票四系统融合闭环状态面板.py
作用：验证股票任务与四系统闭环任务是否已合并到一个可验收状态面板。
触发方式：python 验证股票四系统融合闭环状态面板.py
依赖：股票四系统融合闭环状态面板_最新.json。
所属系统：00杰哥系统总管
输出：标准输出 JSON 验收结果。
安全边界：只读验证；不触发n8n、不发送企业微信、不重启服务、不交易。
创建/修改记录：2026-05-03 创建；2026-05-03 增加文稿质检旁路观察面板检查；2026-05-03 增加文稿质检样本复盘检查；2026-05-03 增加189入口下一只待处理口径验证；2026-05-03 增加进度依据验证；2026-05-03 增加194受控同步验证；2026-05-03 更新进度估算验证口径；2026-05-03 增加文稿质检用户确认进度验证；2026-05-03 增加191最小行动卡验证；2026-05-03 增加197完成后预演检查验证；2026-05-03 增加191资料来源导航卡验证；2026-05-03 增加198填写质量闸口验证；2026-05-03 进度验证改为动态估算口径；2026-05-03 增加199资料候选处理包验证；2026-05-03 增加200填写建议草案验证；2026-05-03 增加201最小人工确认清单验证；2026-05-03 增加202候选填写CSV副本验证；2026-05-03 增加203候选写入差异预览验证；2026-05-03 增加204候选采用后质量预演验证；2026-05-03 增加205候选采用确认回执草案验证；2026-05-03 增加206候选采用前闸口验证。
标识：stock-four-system-fusion-panel-verify
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
REPORT = MANAGER / "03数据" / "四系统小闭环" / "股票四系统融合闭环状态面板_最新.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def main() -> int:
    report = load(REPORT)
    groups = report.get("检查组", [])
    all_checks = [item for group in groups for item in group.get("检查项", [])]
    boundary = report.get("安全边界", {})
    evidence_entry_check = next((item for item in all_checks if item.get("名称") == "证据链人工核验入口按权威状态排序"), {})
    evidence_entry_detail = evidence_entry_check.get("详情", {}) if isinstance(evidence_entry_check, dict) else {}
    next_pending = evidence_entry_detail.get("下一只待处理", {}) if isinstance(evidence_entry_detail, dict) else {}
    review_observation_check = next((item for item in all_checks if item.get("名称") == "文稿质检旁路观察面板存在且不允许第二阶段"), {})
    review_confirmation = (review_observation_check.get("详情", {}) or {}).get("用户确认进度", {}) if isinstance(review_observation_check, dict) else {}
    checks = [
        {"名称": "融合状态面板存在", "通过": REPORT.exists()},
        {"名称": "融合结论允许继续施工", "通过": report.get("融合结论") == "通过：可以按融合主线继续施工"},
        {"名称": "明确不影响股票日常使用", "通过": "不影响" in report.get("是否影响股票日常使用", "")},
        {"名称": "检查组不少于4类", "通过": len(groups) >= 4},
        {"名称": "包含股票系统日常可用", "通过": any(group.get("名称") == "股票系统日常可用" for group in groups)},
        {"名称": "包含四系统闭环治理", "通过": any(group.get("名称") == "四系统闭环治理" for group in groups)},
        {"名称": "包含进化沉淀与复用", "通过": any(group.get("名称") == "进化沉淀与复用" for group in groups)},
        {"名称": "包含文稿质检旁路观察面板", "通过": any(item.get("名称") == "文稿质检旁路观察面板存在且不允许第二阶段" for item in all_checks)},
        {"名称": "包含文稿质检样本复盘", "通过": any(item.get("名称") == "文稿质检样本复盘存在且不允许第二阶段" for item in all_checks)},
        {"名称": "包含文稿质检用户确认进度", "通过": int(review_confirmation.get("第二阶段评估最低确认次数") or 0) == 5 and int(review_confirmation.get("仍需确认次数") or 0) >= 0},
        {"名称": "189入口下一只待处理为天齐锂业", "通过": next_pending.get("名称") == "天齐锂业" and int(next_pending.get("合计待填") or 0) > 0},
        {"名称": "包含191最小行动卡检查", "通过": any(item.get("名称") == "191最小行动卡存在且验证通过" for item in all_checks)},
        {"名称": "包含191资料来源导航卡检查", "通过": any(item.get("名称") == "191资料来源导航卡存在且验证通过" for item in all_checks)},
        {"名称": "包含199资料候选处理包检查", "通过": any(item.get("名称") == "199资料候选处理包存在且验证通过" for item in all_checks)},
        {"名称": "包含200填写建议草案检查", "通过": any(item.get("名称") == "200填写建议草案存在且验证通过" for item in all_checks)},
        {"名称": "包含201最小人工确认清单检查", "通过": any(item.get("名称") == "201最小人工确认清单存在且验证通过" for item in all_checks)},
        {"名称": "包含202候选填写CSV副本检查", "通过": any(item.get("名称") == "202候选填写CSV副本存在且验证通过" for item in all_checks)},
        {"名称": "包含203候选写入差异预览检查", "通过": any(item.get("名称") == "203候选写入差异预览存在且验证通过" for item in all_checks)},
        {"名称": "包含204候选采用后质量预演检查", "通过": any(item.get("名称") == "204候选采用后质量预演存在且验证通过" for item in all_checks)},
        {"名称": "包含205候选采用确认回执草案检查", "通过": any(item.get("名称") == "205候选采用确认回执草案存在且验证通过" for item in all_checks)},
        {"名称": "包含210确认回执状态面板检查", "通过": any(item.get("名称") == "210确认回执状态面板存在且验证通过" for item in all_checks)},
        {"名称": "包含211回执后调度清单检查", "通过": any(item.get("名称") == "211回执后调度清单存在且验证通过" for item in all_checks)},
        {"名称": "包含212确认回执填写样例副本检查", "通过": any(item.get("名称") == "212确认回执填写样例副本存在且验证通过" for item in all_checks)},
        {"名称": "包含213确认后路径演练报告检查", "通过": any(item.get("名称") == "213确认后路径演练报告存在且验证通过" for item in all_checks)},
        {"名称": "包含214正式回执待办卡检查", "通过": any(item.get("名称") == "214正式回执待办卡存在且验证通过" for item in all_checks)},
        {"名称": "包含215正式回执填写前自检检查", "通过": any(item.get("名称") == "215正式回执填写前自检存在且验证通过" for item in all_checks)},
        {"名称": "包含216正式回执录入后受控重跑预演检查", "通过": any(item.get("名称") == "216正式回执录入后受控重跑预演存在且验证通过" for item in all_checks)},
        {"名称": "包含206候选采用前闸口检查", "通过": any(item.get("名称") == "206候选采用前闸口存在且验证通过" for item in all_checks)},
        {"名称": "包含207候选采用受控执行预案检查", "通过": any(item.get("名称") == "207候选采用受控执行预案存在且验证通过" for item in all_checks)},
        {"名称": "包含208候选采用预览检查", "通过": any(item.get("名称") == "208候选采用预览存在且验证通过" for item in all_checks)},
        {"名称": "包含209受控写入命令草案检查", "通过": any(item.get("名称") == "209受控写入命令草案存在且验证通过" for item in all_checks)},
        {"名称": "包含198填写质量闸口检查", "通过": any(item.get("名称") == "198填写质量闸口存在且验证通过" for item in all_checks)},
        {"名称": "包含194受控同步执行验证", "通过": any(item.get("名称") == "194受控同步执行验证通过" for item in all_checks)},
        {"名称": "包含197完成后预演检查", "通过": any(item.get("名称") == "197完成后预演检查已同步191且验证通过" for item in all_checks)},
        {"名称": "包含股票四系统闭环完成观察记录检查", "通过": any(item.get("名称") == "股票四系统闭环完成观察记录存在且验证通过" for item in all_checks)},
        {"名称": "包含进度和剩余有效工作时间", "通过": "%" in str(report.get("当前进度", "")) and "小时" in str(report.get("剩余有效工作时间估算", ""))},
        {"名称": "进度依据包含199资料候选到194受控同步执行", "通过": any("199" in item and "200" in item and "201" in item and "202" in item and "203" in item and "204" in item and "205" in item and "216" in item and "193" in item and "194" in item for item in report.get("进度依据", []))},
        {"名称": "所有检查项通过", "通过": bool(all_checks) and all(item.get("通过") is True for item in all_checks)},
        {"名称": "安全边界全部禁止", "通过": bool(boundary) and all(value is False for value in boundary.values())},
        {"名称": "下一步包含手机端排版", "通过": any("手机端" in item and "排版" in item for item in report.get("下一步", []))},
        {"名称": "下一步包含文稿质检样本观察口径", "通过": any("文稿质检" in item and "样本" in item and "第二阶段" in item for item in report.get("下一步", []))},
        {"名称": "下一步包含文稿质检硬守门口径", "通过": any("硬守门" in item or "脚本硬守门" in item for item in report.get("下一步", []))},
        {"名称": "下一步保留198闸口193闸口197和194顺序", "通过": any("198填写质量闸口" in item and "193闸口" in item and "197" in item and "194" in item for item in report.get("下一步", []))},
        {"名称": "下一步包含观察期口径", "通过": any("观察" in item and ("24小时" in item or "完整业务周期" in item) for item in report.get("下一步", []))},
        {"名称": "施工主线体现股票为真实业务样板", "通过": any("真实业务样板" in item for item in report.get("融合施工主线", []))},
    ]
    ok = all(item["通过"] for item in checks)
    print(json.dumps({
        "状态": "完成",
        "验收结论": "通过：股票任务与四系统闭环任务已融合到同一状态面板" if ok else "未通过：融合状态面板存在缺口",
        "通过数量": sum(1 for item in checks if item["通过"]),
        "失败数量": sum(1 for item in checks if not item["通过"]),
        "检查项": checks,
        "报告": str(REPORT),
    }, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
