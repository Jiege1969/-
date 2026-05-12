# -*- coding: utf-8 -*-
"""验证多业务并行施工每日交接摘要与下一步队列包。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


EVOLUTION_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = EVOLUTION_ROOT / "03数据" / "120多业务并行施工每日交接摘要与下一步队列包"
LOG_DIR = EVOLUTION_ROOT / "04日志" / "多业务并行施工每日交接摘要与下一步队列包验收"

PACKAGE_JSON = DATA_DIR / "多业务并行施工每日交接摘要与下一步队列包_最新.json"
PACKAGE_MD = DATA_DIR / "多业务并行施工每日交接摘要与下一步队列包_最新.md"
STATUS_MD = DATA_DIR / "当前状态摘要_最新.md"
BOUNDARY_MD = DATA_DIR / "阻断项与红线边界_最新.md"
QUEUE_MD = DATA_DIR / "下一步自主施工队列_最新.md"
INDEX_MD = DATA_DIR / "最近阶段包索引_最新.md"
VERIFY_JSON = LOG_DIR / "multi-business-parallel-daily-handoff-next-queue-verify-最新.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def require_false(errors: list[str], data: dict[str, Any], key: str) -> None:
    if data.get(key) is not False:
        errors.append(f"{key} 必须为 false")


def require_true(errors: list[str], data: dict[str, Any], key: str) -> None:
    if data.get(key) is not True:
        errors.append(f"{key} 必须为 true")


def main() -> int:
    errors: list[str] = []
    required_files = [PACKAGE_JSON, PACKAGE_MD, STATUS_MD, BOUNDARY_MD, QUEUE_MD, INDEX_MD]
    for path in required_files:
        if not path.exists():
            errors.append(f"缺少产物：{path}")

    package = read_json(PACKAGE_JSON) if PACKAGE_JSON.exists() else {}
    if package.get("状态") != "multi_business_parallel_daily_handoff_next_queue_ready":
        errors.append("总包状态不正确")
    if package.get("数据目录") != str(DATA_DIR):
        errors.append("数据目录不正确")

    for key in ["readonly_or_candidate_only", "local_file_only", "handoff_summary_only", "next_queue_only"]:
        require_true(errors, package, key)
    for key in [
        "real_wecom_send",
        "connect_n8n",
        "trigger_n8n",
        "broker_connection",
        "trade_order",
        "tax_bureau_login",
        "finance_tax_software_connection",
        "formal_tax_conclusion",
        "video_real_render",
        "video_real_publish",
        "write_formal_rule",
        "auto_promote_formal_rule",
        "modify_supervisor_panel",
        "modify_one_click_continuation_package",
        "reload_19310",
        "reload_19302",
        "external_network_call",
    ]:
        require_false(errors, package, key)

    status = package.get("当前状态摘要", {})
    patrol = status.get("最新自主巡检", {})
    if patrol.get("总体状态") != "pass":
        errors.append("最新自主巡检总体状态必须为 pass")
    if patrol.get("失败") not in (0, "0"):
        errors.append("最新自主巡检失败数必须为 0")
    if patrol.get("通过") != patrol.get("总数"):
        errors.append("最新自主巡检通过数必须等于总数")

    regression = status.get("一键只读总回归", {})
    if regression.get("通过") is not True:
        errors.append("一键只读总回归必须为通过")

    blockers = package.get("阻断项", [])
    if len(blockers) < 4:
        errors.append("阻断项数量不足")
    blocker_text = json.dumps(blockers, ensure_ascii=False)
    for token in ["MoneyPrinterTurbo", "ImageMagick", "企业微信真实发送", "n8n", "正式规则"]:
        if token not in blocker_text:
            errors.append(f"阻断项缺少关键字：{token}")

    queue = package.get("下一步自主施工队列", [])
    if len(queue) < 6:
        errors.append("下一步自主施工队列数量不足")
    if not any(item.get("任务") == "总巡检聚合与交付快照更新" for item in queue):
        errors.append("队列缺少总巡检聚合任务")
    if not all(item.get("可自主执行") is True for item in queue):
        errors.append("队列存在不可自主执行项")

    artifacts = package.get("产物", {})
    for name, path_text in artifacts.items():
        if not Path(path_text).exists():
            errors.append(f"产物登记但不存在：{name} {path_text}")
    if len(artifacts) < 6:
        errors.append("产物登记数量不足")

    for path in [PACKAGE_MD, STATUS_MD, BOUNDARY_MD, QUEUE_MD, INDEX_MD]:
        if path.exists():
            text = path.read_text(encoding="utf-8-sig")
            if len(text.strip()) < 80:
                errors.append(f"Markdown 内容过短：{path.name}")

    verification = {
        "名称": "多业务并行施工每日交接摘要与下一步队列包验收",
        "生成时间": now(),
        "通过": len(errors) == 0,
        "错误数": len(errors),
        "错误": errors,
        "数据目录": str(DATA_DIR),
        "日志目录": str(LOG_DIR),
        "验证日志": str(VERIFY_JSON),
        "required_file_count": len(required_files),
        "existing_file_count": sum(1 for path in required_files if path.exists()),
        "队列数量": len(queue),
        "阻断项数量": len(blockers),
        "巡检总数": patrol.get("总数"),
        "巡检通过": patrol.get("通过"),
        "巡检失败": patrol.get("失败"),
        "real_wecom_send": False,
        "connect_n8n": False,
        "trigger_n8n": False,
        "broker_connection": False,
        "trade_order": False,
        "tax_bureau_login": False,
        "finance_tax_software_connection": False,
        "video_real_render": False,
        "video_real_publish": False,
        "write_formal_rule": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_package": False,
        "reload_19310": False,
        "reload_19302": False,
    }
    write_json(VERIFY_JSON, verification)
    print(json.dumps({"通过": verification["通过"], "错误数": verification["错误数"], "验证日志": str(VERIFY_JSON)}, ensure_ascii=False))
    return 0 if verification["通过"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
