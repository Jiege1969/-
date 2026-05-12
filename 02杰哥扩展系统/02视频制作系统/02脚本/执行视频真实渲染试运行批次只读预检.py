# -*- coding: utf-8 -*-
"""
执行视频真实渲染试运行批次只读预检。

只读取第23包白名单草案和第24包预检产物，输出只读预检报告。
不调用 MoneyPrinterTurbo，不执行 magick，不真实渲染，不生成真实视频，不发布。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
SOURCE23_DIR = ROOT / "03数据" / "23真实渲染试运行白名单与回滚预案草案包"
DATA_DIR = ROOT / "03数据" / "24真实渲染试运行批次预检与白名单未生效闸口包"

SOURCE23_WHITELIST = SOURCE23_DIR / "视频真实渲染试运行白名单草案_最新.json"
SOURCE23_READONLY_CHECK = SOURCE23_DIR / "视频真实渲染试运行白名单只读核对报告_最新.json"
PACKAGE_LATEST = DATA_DIR / "视频真实渲染试运行批次预检与白名单未生效闸口包_最新.json"
PRECHECK_LATEST = DATA_DIR / "视频真实渲染试运行批次预检_最新.json"
GATE_LATEST = DATA_DIR / "视频真实渲染白名单未生效闸口_最新.json"
SIGNOFF_LATEST = DATA_DIR / "视频真实渲染试运行批次人工签收清单_最新.json"
CHECK_LATEST = DATA_DIR / "视频真实渲染试运行批次只读预检报告_最新.json"
CHECK_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次只读预检报告_最新.md"


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


def required_ascii_blocked(doc: dict[str, Any]) -> bool:
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


def build_check() -> dict[str, Any]:
    source23_whitelist = load_json(SOURCE23_WHITELIST)
    source23_check = load_json(SOURCE23_READONLY_CHECK)
    package = load_json(PACKAGE_LATEST)
    precheck = load_json(PRECHECK_LATEST)
    gate = load_json(GATE_LATEST)
    signoff = load_json(SIGNOFF_LATEST)
    checks: list[dict[str, Any]] = []

    add_check(checks, "第23包白名单草案存在", SOURCE23_WHITELIST.exists(), str(SOURCE23_WHITELIST))
    add_check(checks, "第23包白名单未生效", source23_whitelist.get("whitelist_effective") is False, source23_whitelist.get("whitelist_effective"))
    add_check(checks, "第23包试运行未允许", source23_whitelist.get("trial_run_allowed") is False, source23_whitelist.get("trial_run_allowed"))
    add_check(checks, "第23包只读核对通过", source23_check.get("error_count") == 0, source23_check.get("核对结论", ""))

    expected_files = {
        "第24包总包": PACKAGE_LATEST,
        "批次预检": PRECHECK_LATEST,
        "白名单未生效闸口": GATE_LATEST,
        "人工签收清单": SIGNOFF_LATEST,
    }
    for name, path in expected_files.items():
        add_check(checks, f"{name}存在", path.exists(), str(path))

    for name, doc in {"package": package, "precheck": precheck, "gate": gate, "signoff": signoff}.items():
        add_check(checks, f"{name}: 红线字段保持未启用", required_blocked(doc), {
            "batch_allowed": doc.get("batch_allowed"),
            "whitelist_effective": doc.get("whitelist_effective"),
            "trial_run_allowed": doc.get("trial_run_allowed"),
            "can_enter_real_render": doc.get("can_enter_real_render"),
            "真实渲染": doc.get("真实渲染"),
            "生成真实视频": doc.get("生成真实视频"),
            "上传发布": doc.get("上传发布"),
        })
        add_check(checks, f"{name}: 英文只读红线字段保持 false", required_ascii_blocked(doc), doc.get("readonly_flags_ascii", {}))
        add_check(checks, f"{name}: error_count=0", doc.get("error_count") == 0, doc.get("error_count"))

    batch = precheck.get("试运行批次样例", {})
    add_check(checks, "批次样例覆盖批次ID", bool(batch.get("批次ID")), batch.get("批次ID"))
    add_check(checks, "批次样例覆盖任务ID", bool(batch.get("任务ID")), batch.get("任务ID"))
    add_check(checks, "批次样例覆盖素材要求", bool(batch.get("素材要求")), batch.get("素材要求", {}))
    add_check(checks, "批次样例覆盖输出目录", bool(batch.get("输出目录")), batch.get("输出目录", {}))
    add_check(checks, "批次样例覆盖最大时长", batch.get("最大时长", {}).get("单条视频最大时长秒") == 15, batch.get("最大时长", {}))
    add_check(checks, "批次样例覆盖失败回滚", bool(batch.get("失败回滚")), batch.get("失败回滚", []))
    add_check(checks, "批次样例覆盖日志留存", bool(batch.get("日志留存")), batch.get("日志留存", []))
    add_check(checks, "批次样例覆盖人工签收", batch.get("人工签收", {}).get("签收状态") == "未签收", batch.get("人工签收", {}))
    add_check(checks, "未生效闸口关闭", gate.get("闸口状态") == "closed", gate.get("闸口状态"))
    add_check(checks, "人工签收清单未签收", signoff.get("清单状态") == "unsigned", signoff.get("清单状态"))

    errors = [item for item in checks if not item["通过"]]
    result = {
        "名称": "视频真实渲染试运行批次只读预检报告",
        "生成时间": now_text(),
        "核对方式": "只读预检",
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
        "来源": {
            "第23包白名单草案": str(SOURCE23_WHITELIST),
            "第24包总包": str(PACKAGE_LATEST),
            "批次预检": str(PRECHECK_LATEST),
            "白名单未生效闸口": str(GATE_LATEST),
            "人工签收清单": str(SIGNOFF_LATEST),
        },
        "检查结果": checks,
        "错误项": errors,
        "核对结论": "通过；白名单未生效，批次不允许，试运行仍不允许。" if not errors else "不通过；试运行仍不允许。",
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


def build_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行批次只读预检报告",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- error_count：{result['error_count']}",
        f"- batch_allowed：{str(result['batch_allowed']).lower()}",
        f"- whitelist_effective：{str(result['whitelist_effective']).lower()}",
        f"- trial_run_allowed：{str(result['trial_run_allowed']).lower()}",
        f"- can_enter_real_render：{str(result['can_enter_real_render']).lower()}",
        f"- 真实渲染：{str(result['真实渲染']).lower()}",
        f"- 生成真实视频：{str(result['生成真实视频']).lower()}",
        f"- 上传发布：{str(result['上传发布']).lower()}",
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
    write_json(DATA_DIR / f"视频真实渲染试运行批次只读预检报告_{stamp}.json", result)
    write_json(CHECK_LATEST, result)
    write_text(CHECK_MD_LATEST, build_markdown(result))
    print(
        json.dumps(
            {
                "readonly_precheck": str(CHECK_LATEST),
                "batch_allowed": False,
                "whitelist_effective": False,
                "trial_run_allowed": False,
                "can_enter_real_render": False,
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "error_count": result["error_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
