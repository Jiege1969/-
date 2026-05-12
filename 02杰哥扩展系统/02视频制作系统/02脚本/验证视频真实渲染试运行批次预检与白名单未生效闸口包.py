# -*- coding: utf-8 -*-
"""
验证视频真实渲染试运行批次预检与白名单未生效闸口包。

验证只检查预检产物、白名单未生效闸口、人工签收清单和红线状态，并写入固定验收日志：
video-render-trial-batch-precheck-whitelist-inactive-verify-最新.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "24真实渲染试运行批次预检与白名单未生效闸口包"
LOG_DIR = ROOT / "04日志" / "真实渲染试运行批次预检与白名单未生效闸口包验收"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染试运行批次预检与白名单未生效闸口包_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次预检与白名单未生效闸口包_最新.md"
PRECHECK_LATEST = DATA_DIR / "视频真实渲染试运行批次预检_最新.json"
PRECHECK_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次预检_最新.md"
GATE_LATEST = DATA_DIR / "视频真实渲染白名单未生效闸口_最新.json"
GATE_MD_LATEST = DATA_DIR / "视频真实渲染白名单未生效闸口_最新.md"
SIGNOFF_LATEST = DATA_DIR / "视频真实渲染试运行批次人工签收清单_最新.json"
SIGNOFF_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次人工签收清单_最新.md"
CHECK_LATEST = DATA_DIR / "视频真实渲染试运行批次只读预检报告_最新.json"
CHECK_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次只读预检报告_最新.md"
VERIFY_LATEST = LOG_DIR / "video-render-trial-batch-precheck-whitelist-inactive-verify-最新.json"


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
    precheck = load_json(PRECHECK_LATEST)
    gate = load_json(GATE_LATEST)
    signoff = load_json(SIGNOFF_LATEST)
    readonly_check = load_json(CHECK_LATEST)
    checks: list[dict[str, Any]] = []

    expected_files = {
        "总包JSON": PACKAGE_LATEST,
        "总包MD": PACKAGE_MD_LATEST,
        "批次预检JSON": PRECHECK_LATEST,
        "批次预检MD": PRECHECK_MD_LATEST,
        "白名单未生效闸口JSON": GATE_LATEST,
        "白名单未生效闸口MD": GATE_MD_LATEST,
        "人工签收清单JSON": SIGNOFF_LATEST,
        "人工签收清单MD": SIGNOFF_MD_LATEST,
        "只读预检报告JSON": CHECK_LATEST,
        "只读预检报告MD": CHECK_MD_LATEST,
    }
    for name, path in expected_files.items():
        add_check(checks, f"{name}存在", path.exists(), str(path))

    for name, doc in {"package": package, "precheck": precheck, "gate": gate, "signoff": signoff, "readonly_check": readonly_check}.items():
        add_check(checks, f"{name}: 核心红线字段正确", required_status(doc), {
            "batch_allowed": doc.get("batch_allowed"),
            "whitelist_effective": doc.get("whitelist_effective"),
            "trial_run_allowed": doc.get("trial_run_allowed"),
            "can_enter_real_render": doc.get("can_enter_real_render"),
            "真实渲染": doc.get("真实渲染"),
            "生成真实视频": doc.get("生成真实视频"),
            "上传发布": doc.get("上传发布"),
        })
        add_check(checks, f"{name}: 英文红线字段正确", required_ascii_status(doc), doc.get("readonly_flags_ascii", {}))
        add_check(checks, f"{name}: error_count=0", doc.get("error_count") == 0, doc.get("error_count"))

    batch = precheck.get("试运行批次样例", {})
    add_check(checks, "批次预检覆盖批次ID", bool(batch.get("批次ID")), batch.get("批次ID"))
    add_check(checks, "批次预检覆盖任务ID", bool(batch.get("任务ID")), batch.get("任务ID"))
    add_check(checks, "批次预检覆盖素材要求", bool(batch.get("素材要求")), batch.get("素材要求", {}))
    add_check(checks, "批次预检覆盖输出目录", bool(batch.get("输出目录")), batch.get("输出目录", {}))
    add_check(checks, "批次预检覆盖最大时长", batch.get("最大时长", {}).get("单条视频最大时长秒") == 15, batch.get("最大时长", {}))
    add_check(checks, "批次预检覆盖失败回滚", bool(batch.get("失败回滚")), batch.get("失败回滚", []))
    add_check(checks, "批次预检覆盖日志留存", bool(batch.get("日志留存")), batch.get("日志留存", []))
    add_check(checks, "批次预检覆盖人工签收", batch.get("人工签收", {}).get("签收状态") == "未签收", batch.get("人工签收", {}))
    add_check(checks, "未生效闸口关闭", gate.get("闸口状态") == "closed" and gate.get("阻断字段", {}).get("batch_allowed") is False, gate.get("阻断字段", {}))
    add_check(checks, "人工签收清单未签收", signoff.get("清单状态") == "unsigned", signoff.get("清单状态"))
    add_check(checks, "只读预检通过", readonly_check.get("error_count") == 0 and "通过" in readonly_check.get("核对结论", ""), readonly_check.get("核对结论", ""))

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染试运行批次预检与白名单未生效闸口包验收",
        "生成时间": now_text(),
        "error_count": len(errors),
        "batch_allowed": False,
        "whitelist_effective": False,
        "trial_run_allowed": False,
        "can_enter_real_render": False,
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
        "检查结果": checks,
        "错误项": errors,
        "产物路径": {
            "总包": str(PACKAGE_LATEST),
            "批次预检": str(PRECHECK_LATEST),
            "白名单未生效闸口": str(GATE_LATEST),
            "人工签收清单": str(SIGNOFF_LATEST),
            "只读预检报告": str(CHECK_LATEST),
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
    result["readonly_flags_ascii"] = {
        "batch_allowed": False,
        "whitelist_effective": False,
        "trial_run_allowed": False,
        "can_enter_real_render": False,
        "real_render": False,
        "generate_real_video": False,
        "upload_publish": False,
        "call_money_printer_turbo": False,
        "execute_magick": False,
        "execute_magick_version": False,
        "trigger_n8n": False,
        "modify_wecom_public_config": False,
        "modify_supervisor_panel": False,
        "modify_one_click_continuation_pack": False,
        "reload_service": False,
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
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "error_count": result["error_count"],
                "验收结论": result["验收结论"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
