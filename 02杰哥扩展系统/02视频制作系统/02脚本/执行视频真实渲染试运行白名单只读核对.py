# -*- coding: utf-8 -*-
"""
执行视频真实渲染试运行白名单只读核对。

只读取第23包草案与第22包禁入材料，输出只读核对报告。
不调用 MoneyPrinterTurbo，不执行 magick，不真实渲染，不生成真实视频，不发布。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
SOURCE22_DIR = ROOT / "03数据" / "22真实渲染人工放行材料完整性复核与试运行禁入包"
DATA_DIR = ROOT / "03数据" / "23真实渲染试运行白名单与回滚预案草案包"

SOURCE22_PACKAGE = SOURCE22_DIR / "视频真实渲染人工放行材料完整性复核与试运行禁入包_最新.json"
PACKAGE_LATEST = DATA_DIR / "视频真实渲染试运行白名单与回滚预案草案包_最新.json"
WHITELIST_LATEST = DATA_DIR / "视频真实渲染试运行白名单草案_最新.json"
ROLLBACK_LATEST = DATA_DIR / "视频真实渲染试运行回滚预案草案_最新.json"
CHECK_LATEST = DATA_DIR / "视频真实渲染试运行白名单只读核对报告_最新.json"
CHECK_MD_LATEST = DATA_DIR / "视频真实渲染试运行白名单只读核对报告_最新.md"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stamp_text() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"检查项": name, "通过": bool(passed), "详情": detail})


def required_blocked(doc: dict[str, Any]) -> bool:
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
        and doc.get("触发n8n") is False
        and doc.get("修改企业微信公共配置") is False
        and doc.get("修改总管面板") is False
        and doc.get("修改一键接续包") is False
        and doc.get("重载服务") is False
    )


def required_ascii_blocked(doc: dict[str, Any]) -> bool:
    flags = doc.get("readonly_flags_ascii", {})
    keys = [
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


def build_check() -> dict[str, Any]:
    source22 = load_json(SOURCE22_PACKAGE)
    package = load_json(PACKAGE_LATEST)
    whitelist = load_json(WHITELIST_LATEST)
    rollback = load_json(ROLLBACK_LATEST)
    checks: list[dict[str, Any]] = []

    add_check(checks, "第22包总包存在", SOURCE22_PACKAGE.exists(), str(SOURCE22_PACKAGE))
    add_check(checks, "第22包保持试运行禁入", source22.get("试运行禁入") is True, source22.get("试运行禁入"))
    add_check(checks, "第23包总包存在", PACKAGE_LATEST.exists(), str(PACKAGE_LATEST))
    add_check(checks, "白名单草案存在", WHITELIST_LATEST.exists(), str(WHITELIST_LATEST))
    add_check(checks, "回滚预案草案存在", ROLLBACK_LATEST.exists(), str(ROLLBACK_LATEST))

    for name, doc in {"package": package, "whitelist": whitelist, "rollback": rollback}.items():
        add_check(checks, f"{name}: 红线字段保持未启用", required_blocked(doc), {
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
        add_check(checks, f"{name}: 英文只读红线字段保持 false", required_ascii_blocked(doc), doc.get("readonly_flags_ascii", {}))
        add_check(checks, f"{name}: error_count=0", doc.get("error_count") == 0, doc.get("error_count"))

    task_types = [item.get("任务类型") for item in whitelist.get("允许任务类型草案", [])]
    add_check(checks, "白名单草案覆盖允许任务类型", len(task_types) >= 2, task_types)
    add_check(checks, "白名单草案覆盖测试素材要求", bool(whitelist.get("测试素材要求")), whitelist.get("测试素材要求", []))
    add_check(checks, "白名单草案覆盖输出目录要求", bool(whitelist.get("输出目录要求")), whitelist.get("输出目录要求", []))
    add_check(checks, "白名单草案覆盖最大时长", whitelist.get("最大时长", {}).get("单条视频最大时长秒") == 15, whitelist.get("最大时长", {}))
    add_check(checks, "白名单草案覆盖失败回滚", bool(whitelist.get("失败回滚要求")), whitelist.get("失败回滚要求", []))
    add_check(checks, "白名单草案覆盖日志留存", bool(whitelist.get("日志留存要求")), whitelist.get("日志留存要求", []))
    add_check(checks, "白名单草案覆盖人工确认签收", whitelist.get("人工确认签收", {}).get("签收状态") == "未签收", whitelist.get("人工确认签收", {}))
    add_check(checks, "回滚预案覆盖触发条件", bool(rollback.get("触发条件草案")), rollback.get("触发条件草案", []))
    add_check(checks, "回滚预案覆盖回滚步骤", bool(rollback.get("回滚步骤草案")), rollback.get("回滚步骤草案", []))
    add_check(checks, "回滚预案保持不改配置不重载", all(item in rollback.get("配置恢复要求", []) for item in ["不得修改企业微信公共配置。", "不得修改总管面板。", "不得修改一键接续包。", "不得重载服务。"]), rollback.get("配置恢复要求", []))

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染试运行白名单只读核对报告",
        "生成时间": now_text(),
        "核对方式": "只读核对",
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
        "来源": {
            "第22包总包": str(SOURCE22_PACKAGE),
            "第23包总包": str(PACKAGE_LATEST),
            "白名单草案": str(WHITELIST_LATEST),
            "回滚预案草案": str(ROLLBACK_LATEST),
        },
        "检查结果": checks,
        "错误项": errors,
        "核对结论": "通过；白名单未生效，试运行仍不允许。" if not errors else "不通过；试运行仍不允许。",
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


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行白名单只读核对报告",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- error_count：{result['error_count']}",
        f"- whitelist_effective：{str(result['whitelist_effective']).lower()}",
        f"- trial_run_allowed：{str(result['trial_run_allowed']).lower()}",
        f"- can_enter_real_render：{str(result['can_enter_real_render']).lower()}",
        f"- 真实渲染：{str(result['真实渲染']).lower()}",
        f"- 生成真实视频：{str(result['生成真实视频']).lower()}",
        f"- 上传发布：{str(result['上传发布']).lower()}",
        f"- 调用MoneyPrinterTurbo：{str(result['调用MoneyPrinterTurbo']).lower()}",
        f"- 执行magick：{str(result['执行magick']).lower()}",
        f"- 执行magick_version：{str(result['执行magick_version']).lower()}",
        "",
        "## 检查结果",
        "",
    ]
    lines.extend(f"- {item['检查项']}：{str(item['通过']).lower()}" for item in result["检查结果"])
    lines.extend(["", f"结论：{result['核对结论']}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    result = build_check()
    stamp = stamp_text()
    write_json(DATA_DIR / f"视频真实渲染试运行白名单只读核对报告_{stamp}.json", result)
    write_json(CHECK_LATEST, result)
    write_text(CHECK_MD_LATEST, build_markdown(result))
    print(
        json.dumps(
            {
                "readonly_check": str(CHECK_LATEST),
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
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
