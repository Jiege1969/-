# -*- coding: utf-8 -*-
"""
验证视频真实渲染试运行白名单与回滚预案草案包。

验证只检查草案产物和红线状态，并写入固定验收日志：
video-render-trial-whitelist-rollback-draft-verify-最新.json
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
DATA_DIR = ROOT / "03数据" / "23真实渲染试运行白名单与回滚预案草案包"
LOG_DIR = ROOT / "04日志" / "真实渲染试运行白名单与回滚预案草案包验收"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染试运行白名单与回滚预案草案包_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染试运行白名单与回滚预案草案包_最新.md"
WHITELIST_LATEST = DATA_DIR / "视频真实渲染试运行白名单草案_最新.json"
WHITELIST_MD_LATEST = DATA_DIR / "视频真实渲染试运行白名单草案_最新.md"
ROLLBACK_LATEST = DATA_DIR / "视频真实渲染试运行回滚预案草案_最新.json"
ROLLBACK_MD_LATEST = DATA_DIR / "视频真实渲染试运行回滚预案草案_最新.md"
CHECK_LATEST = DATA_DIR / "视频真实渲染试运行白名单只读核对报告_最新.json"
CHECK_MD_LATEST = DATA_DIR / "视频真实渲染试运行白名单只读核对报告_最新.md"
VERIFY_LATEST = LOG_DIR / "video-render-trial-whitelist-rollback-draft-verify-最新.json"


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
        doc.get("whitelist_effective") is False
        and doc.get("trial_run_allowed") is False
        and doc.get("can_enter_real_render") is False
        and doc.get("真实渲染") is False
        and doc.get("生成真实视频") is False
        and doc.get("上传发布") is False
        and doc.get("调用MoneyPrinterTurbo") is False
        and doc.get("执行magick") is False
        and doc.get("执行magick_version") is False
    )


def required_ascii_status(doc: dict[str, Any]) -> bool:
    flags = doc.get("readonly_flags_ascii", {})
    return (
        flags.get("whitelist_effective") is False
        and flags.get("trial_run_allowed") is False
        and flags.get("can_enter_real_render") is False
        and flags.get("real_render") is False
        and flags.get("generate_real_video") is False
        and flags.get("upload_publish") is False
        and flags.get("call_money_printer_turbo") is False
        and flags.get("execute_magick") is False
        and flags.get("execute_magick_version") is False
    )


def validate() -> dict[str, Any]:
    package = load_json(PACKAGE_LATEST)
    whitelist = load_json(WHITELIST_LATEST)
    rollback = load_json(ROLLBACK_LATEST)
    readonly_check = load_json(CHECK_LATEST)
    checks: list[dict[str, Any]] = []

    expected_files = {
        "总包JSON": PACKAGE_LATEST,
        "总包MD": PACKAGE_MD_LATEST,
        "白名单草案JSON": WHITELIST_LATEST,
        "白名单草案MD": WHITELIST_MD_LATEST,
        "回滚预案草案JSON": ROLLBACK_LATEST,
        "回滚预案草案MD": ROLLBACK_MD_LATEST,
        "只读核对报告JSON": CHECK_LATEST,
        "只读核对报告MD": CHECK_MD_LATEST,
    }
    for name, path in expected_files.items():
        add_check(checks, f"{name}存在", path.exists(), str(path))

    for name, doc in {"package": package, "whitelist": whitelist, "rollback": rollback, "readonly_check": readonly_check}.items():
        add_check(checks, f"{name}: 核心红线字段正确", required_status(doc), {
            "whitelist_effective": doc.get("whitelist_effective"),
            "trial_run_allowed": doc.get("trial_run_allowed"),
            "can_enter_real_render": doc.get("can_enter_real_render"),
            "真实渲染": doc.get("真实渲染"),
            "生成真实视频": doc.get("生成真实视频"),
            "上传发布": doc.get("上传发布"),
            "调用MoneyPrinterTurbo": doc.get("调用MoneyPrinterTurbo"),
            "执行magick": doc.get("执行magick"),
            "执行magick_version": doc.get("执行magick_version"),
        })
        add_check(checks, f"{name}: 英文红线字段正确", required_ascii_status(doc), doc.get("readonly_flags_ascii", {}))
        add_check(checks, f"{name}: error_count=0", doc.get("error_count") == 0, doc.get("error_count"))

    add_check(checks, "白名单草案未生效", whitelist.get("状态") == "draft_only" and whitelist.get("人工确认签收", {}).get("签收状态") == "未签收", whitelist.get("人工确认签收", {}))
    add_check(checks, "白名单草案覆盖指定内容", all(bool(whitelist.get(key)) for key in ["允许任务类型草案", "测试素材要求", "输出目录要求", "失败回滚要求", "日志留存要求", "人工确认签收"]) and bool(whitelist.get("最大时长", {}).get("单条视频最大时长秒")), list(whitelist.keys()))
    add_check(checks, "回滚预案草案覆盖指定内容", all(bool(rollback.get(key)) for key in ["触发条件草案", "回滚步骤草案", "临时产物处理", "配置恢复要求", "日志留存要求", "人工确认签收"]), list(rollback.keys()))
    add_check(checks, "只读核对通过", readonly_check.get("error_count") == 0 and "通过" in readonly_check.get("核对结论", ""), readonly_check.get("核对结论", ""))

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染试运行白名单与回滚预案草案包验收",
        "生成时间": now_text(),
        "error_count": len(errors),
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
            "白名单草案": str(WHITELIST_LATEST),
            "回滚预案草案": str(ROLLBACK_LATEST),
            "只读核对报告": str(CHECK_LATEST),
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
                "whitelist_effective": False,
                "trial_run_allowed": False,
                "can_enter_real_render": False,
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "调用MoneyPrinterTurbo": False,
                "执行magick": False,
                "执行magick_version": False,
                "error_count": result["error_count"],
                "验收结论": result["验收结论"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
