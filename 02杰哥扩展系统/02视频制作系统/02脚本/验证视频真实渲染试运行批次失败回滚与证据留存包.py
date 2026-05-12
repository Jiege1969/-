# -*- coding: utf-8 -*-
"""
验证视频真实渲染试运行批次失败回滚与证据留存包。

验收只检查第25包材料、只读演练报告和固定红线状态，并写入固定验收日志。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "25真实渲染试运行批次失败回滚与证据留存包"
LOG_DIR = ROOT / "04日志" / "真实渲染试运行批次失败回滚与证据留存包验收"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚与证据留存包_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚与证据留存包_最新.md"
MATRIX_LATEST = DATA_DIR / "视频真实渲染试运行批次失败场景矩阵_最新.json"
MATRIX_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次失败场景矩阵_最新.md"
ROLLBACK_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚动作清单_最新.json"
ROLLBACK_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚动作清单_最新.md"
EVIDENCE_LATEST = DATA_DIR / "视频真实渲染试运行批次失败证据留存索引_最新.json"
EVIDENCE_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次失败证据留存索引_最新.md"
DRILL_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚只读演练报告_最新.json"
DRILL_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次失败回滚只读演练报告_最新.md"
VERIFY_LATEST = LOG_DIR / "video-render-trial-failure-rollback-evidence-verify-最新.json"

REQUIRED_SCENARIOS = {"环境不可用", "素材缺失", "白名单未生效", "输出目录不可写", "生成后人工否决"}


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def required_status(doc: dict[str, Any]) -> bool:
    return (
        doc.get("batch_allowed") is False
        and doc.get("whitelist_effective") is False
        and doc.get("trial_run_allowed") is False
        and doc.get("can_enter_real_render") is False
        and doc.get("real_render") is False
        and doc.get("publish") is False
        and doc.get("真实渲染") is False
        and doc.get("生成真实视频") is False
        and doc.get("上传发布") is False
        and doc.get("调用MoneyPrinterTurbo") is False
        and doc.get("执行magick") is False
        and doc.get("执行magick_version") is False
        and doc.get("触发n8n") is False
        and doc.get("修改企业微信公共配置") is False
        and doc.get("修改总管面板") is False
        and doc.get("修改一键接续包") is False
        and doc.get("重载服务") is False
    )


def required_ascii_status(doc: dict[str, Any]) -> bool:
    flags = doc.get("readonly_flags_ascii", {})
    keys = [
        "batch_allowed",
        "whitelist_effective",
        "trial_run_allowed",
        "can_enter_real_render",
        "real_render",
        "generate_real_video",
        "publish",
        "upload_publish",
        "call_money_printer_turbo",
        "execute_magick",
        "execute_magick_version",
        "trigger_n8n",
        "modify_wecom_public_config",
        "modify_supervisor_panel",
        "modify_one_click_continuation_pack",
        "reload_service",
    ]
    return all(flags.get(key) is False for key in keys)


def validate() -> dict[str, Any]:
    package = load_json(PACKAGE_LATEST)
    matrix = load_json(MATRIX_LATEST)
    rollback = load_json(ROLLBACK_LATEST)
    evidence = load_json(EVIDENCE_LATEST)
    drill = load_json(DRILL_LATEST)
    checks: list[dict[str, Any]] = []

    expected_files = {
        "总包JSON": PACKAGE_LATEST,
        "总包MD": PACKAGE_MD_LATEST,
        "失败场景矩阵JSON": MATRIX_LATEST,
        "失败场景矩阵MD": MATRIX_MD_LATEST,
        "回滚动作清单JSON": ROLLBACK_LATEST,
        "回滚动作清单MD": ROLLBACK_MD_LATEST,
        "证据留存索引JSON": EVIDENCE_LATEST,
        "证据留存索引MD": EVIDENCE_MD_LATEST,
        "只读演练报告JSON": DRILL_LATEST,
        "只读演练报告MD": DRILL_MD_LATEST,
    }
    for name, path in expected_files.items():
        add_check(checks, f"{name}存在", path.exists(), str(path))

    docs = {
        "package": package,
        "matrix": matrix,
        "rollback": rollback,
        "evidence": evidence,
        "drill": drill,
    }
    for name, doc in docs.items():
        add_check(checks, f"{name}: 核心红线字段正确", required_status(doc), {
            "batch_allowed": doc.get("batch_allowed"),
            "whitelist_effective": doc.get("whitelist_effective"),
            "trial_run_allowed": doc.get("trial_run_allowed"),
            "can_enter_real_render": doc.get("can_enter_real_render"),
            "real_render": doc.get("real_render"),
            "publish": doc.get("publish"),
        })
        add_check(checks, f"{name}: 英文字段红线正确", required_ascii_status(doc), doc.get("readonly_flags_ascii", {}))
        add_check(checks, f"{name}: error_count=0", doc.get("error_count") == 0, doc.get("error_count"))

    scenario_names = {item.get("失败场景") for item in matrix.get("失败场景矩阵", [])}
    add_check(checks, "失败场景矩阵覆盖五类必需场景", REQUIRED_SCENARIOS.issubset(scenario_names), sorted(scenario_names))

    actions = rollback.get("回滚动作清单", [])
    add_check(checks, "回滚动作清单全部dry_run_only=true", bool(actions) and all(item.get("dry_run_only") is True for item in actions), actions)
    add_check(checks, "回滚动作清单不删除真实文件", bool(actions) and all(item.get("删除真实文件") is False for item in actions), actions)
    add_check(checks, "回滚动作清单不清理生产目录", bool(actions) and all(item.get("清理生产目录") is False for item in actions), actions)
    add_check(checks, "回滚动作清单不重试真实渲染", bool(actions) and all(item.get("重试真实渲染") is False for item in actions), actions)

    add_check(checks, "证据索引包含批次ID", bool(evidence.get("批次ID")), evidence.get("批次ID"))
    add_check(checks, "证据索引包含任务ID", bool(evidence.get("任务ID")), evidence.get("任务ID"))
    add_check(checks, "证据索引包含前置快照", bool(evidence.get("前置快照")), evidence.get("前置快照", {}))
    add_check(checks, "证据索引包含失败原因", len(evidence.get("失败原因", [])) >= 5, evidence.get("失败原因", []))
    add_check(checks, "证据索引人工签收状态unsigned", evidence.get("人工签收状态") == "unsigned", evidence.get("人工签收状态"))
    retention = evidence.get("留存期限", {})
    add_check(checks, "证据索引包含留存期限", retention.get("retention_days", 0) >= 180, retention)
    add_check(checks, "只读演练通过", drill.get("error_count") == 0 and "通过" in drill.get("演练结论", ""), drill.get("演练结论"))

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染试运行批次失败回滚与证据留存包验收",
        "生成时间": now_text(),
        "error_count": len(errors),
        "batch_allowed": False,
        "whitelist_effective": False,
        "trial_run_allowed": False,
        "can_enter_real_render": False,
        "real_render": False,
        "publish": False,
        "真实渲染": False,
        "生成真实视频": False,
        "上传发布": False,
        "调用MoneyPrinterTurbo": False,
        "执行magick": False,
        "执行magick_version": False,
        "触发n8n": False,
        "修改企业微信公共配置": False,
        "修改总管面板": False,
        "修改一键接续包": False,
        "重载服务": False,
        "readonly_flags_ascii": {
            "batch_allowed": False,
            "whitelist_effective": False,
            "trial_run_allowed": False,
            "can_enter_real_render": False,
            "real_render": False,
            "generate_real_video": False,
            "publish": False,
            "upload_publish": False,
            "call_money_printer_turbo": False,
            "execute_magick": False,
            "execute_magick_version": False,
            "trigger_n8n": False,
            "modify_wecom_public_config": False,
            "modify_supervisor_panel": False,
            "modify_one_click_continuation_pack": False,
            "reload_service": False,
        },
        "检查结果": checks,
        "错误项": errors,
        "产物路径": {
            "总包": str(PACKAGE_LATEST),
            "失败场景矩阵": str(MATRIX_LATEST),
            "回滚动作清单": str(ROLLBACK_LATEST),
            "证据留存索引": str(EVIDENCE_LATEST),
            "只读演练报告": str(DRILL_LATEST),
            "验收日志": str(VERIFY_LATEST),
        },
        "红线确认": {
            "不调用MoneyPrinterTurbo": True,
            "不执行magick": True,
            "不执行magick_version": True,
            "不真实渲染": True,
            "不生成真实视频": True,
            "不上传发布": True,
            "不接n8n": True,
            "不改企业微信公共配置": True,
            "不改总管面板": True,
            "不改一键接续包": True,
            "不重载服务": True,
        },
        "验收结论": "通过" if not errors else "不通过",
    }
    return result


def main() -> int:
    result = validate()
    write_json(VERIFY_LATEST, result)
    print(
        json.dumps(
            {
                "verify_log": str(VERIFY_LATEST),
                "batch_allowed": False,
                "whitelist_effective": False,
                "trial_run_allowed": False,
                "can_enter_real_render": False,
                "real_render": False,
                "publish": False,
                "error_count": result["error_count"],
                "验收结论": result["验收结论"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
