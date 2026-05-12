# -*- coding: utf-8 -*-
"""
生成视频真实渲染试运行白名单与回滚预案草案包。

本脚本只读取第22包试运行禁入材料，生成白名单草案和回滚预案草案。
它不调用 MoneyPrinterTurbo，不执行 magick 或 magick -version，不真实渲染，
不生成真实视频，不上传发布，不接 n8n，不改公共配置或服务。
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
SOURCE22_TRIAL_BAN = SOURCE22_DIR / "视频真实渲染试运行禁入清单_最新.json"
SOURCE22_READONLY_CHECK = SOURCE22_DIR / "视频真实渲染人工放行材料只读复核_最新.json"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染试运行白名单与回滚预案草案包_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染试运行白名单与回滚预案草案包_最新.md"
WHITELIST_LATEST = DATA_DIR / "视频真实渲染试运行白名单草案_最新.json"
WHITELIST_MD_LATEST = DATA_DIR / "视频真实渲染试运行白名单草案_最新.md"
ROLLBACK_LATEST = DATA_DIR / "视频真实渲染试运行回滚预案草案_最新.json"
ROLLBACK_MD_LATEST = DATA_DIR / "视频真实渲染试运行回滚预案草案_最新.md"


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


def guarded_status(generated_at: str) -> dict[str, Any]:
    return {
        "生成时间": generated_at,
        "error_count": 0,
        "whitelist_effective": False,
        "trial_run_allowed": False,
        "trial_run_forbidden": True,
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
        "readonly_flags_ascii": {
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
        },
    }


def source_summary(source_package: dict[str, Any], trial_ban: dict[str, Any], readonly_check: dict[str, Any]) -> dict[str, Any]:
    return {
        "第22包总包存在": bool(source_package),
        "第22包试运行禁入清单存在": bool(trial_ban),
        "第22包只读复核存在": bool(readonly_check),
        "第22包名称": source_package.get("名称", ""),
        "第22包结论": source_package.get("包结论", ""),
        "第22包只读复核结论": readonly_check.get("复核结论", ""),
        "第22包error_count": readonly_check.get("error_count"),
        "第22包试运行禁入": source_package.get("试运行禁入"),
        "第22包可进入真实渲染": source_package.get("可进入真实渲染"),
        "第22包真实渲染": source_package.get("真实渲染"),
        "第22包生成真实视频": source_package.get("生成真实视频"),
        "第22包上传发布": source_package.get("上传发布"),
        "第22包调用MoneyPrinterTurbo": source_package.get("调用MoneyPrinterTurbo"),
        "第22包执行magick": source_package.get("执行magick"),
        "第22包执行magick_version": source_package.get("执行magick_version"),
    }


def allowed_task_types() -> list[dict[str, Any]]:
    return [
        {
            "任务类型": "最小真实渲染连通性试运行",
            "范围": "仅允许单条、低风险、人工指定任务在未来独立放行后进入。",
            "当前是否允许执行": False,
            "要求": [
                "必须绑定唯一测试任务编号。",
                "必须使用已授权测试素材。",
                "必须写入隔离输出目录。",
                "必须在人工签收后另行生效。",
            ],
        },
        {
            "任务类型": "短时长素材格式兼容性试运行",
            "范围": "仅覆盖素材读取、字幕/封面/音频合成链路的最小验证。",
            "当前是否允许执行": False,
            "要求": [
                "不得复用生产发布素材。",
                "不得写入生产目录。",
                "不得触发上传发布或外部自动化。",
            ],
        },
    ]


def build_whitelist(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染试运行白名单草案",
        "状态": "draft_only",
        "白名单结论": "白名单仅为草案，未生效；试运行仍不允许。",
        "承接来源": {
            "第22包总包": str(SOURCE22_PACKAGE),
            "第22包试运行禁入清单": str(SOURCE22_TRIAL_BAN),
            "第22包只读复核": str(SOURCE22_READONLY_CHECK),
            "第22包摘要": summary,
        },
        "允许任务类型草案": allowed_task_types(),
        "测试素材要求": [
            "素材来源、授权、格式、分辨率、时长、任务编号必须人工签收。",
            "素材仅限测试用途，不得混入生产素材池或发布链路。",
            "素材必须可追溯，缺任一签收项时不得试运行。",
        ],
        "输出目录要求": [
            "输出目录必须为隔离测试目录，禁止写入生产成片目录。",
            "目录命名、容量、权限、清理策略、失败隔离策略必须人工签收。",
            "试运行产物不得自动进入发布、n8n、企业微信、总管面板或一键接续链路。",
        ],
        "最大时长": {
            "单条视频最大时长秒": 15,
            "单次试运行最大任务数": 1,
            "说明": "该限制仅为未来白名单草案参数，不代表当前允许执行。",
        },
        "失败回滚要求": [
            "任何失败均立即保持禁入态。",
            "清理隔离目录内临时产物，并保留失败日志。",
            "不得重试真实渲染，不得扩大任务范围。",
            "回滚结果必须人工签收后再讨论下一轮。",
        ],
        "日志留存要求": [
            "保留输入摘要、任务编号、草案版本、人工签收记录和只读核对结果。",
            "日志不得包含真实视频发布凭据。",
            "日志留存不少于30天或按人工签收要求延长。",
        ],
        "人工确认签收": {
            "签收状态": "未签收",
            "必须签收角色": ["总管", "视频制作负责人", "素材授权负责人", "回滚负责人"],
            "签收后仍需另行启用": True,
        },
    }
    result.update(guarded_status(generated_at))
    return result


def build_rollback(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染试运行回滚预案草案",
        "状态": "draft_only",
        "回滚结论": "回滚预案仅为草案；不会触发试运行、真实渲染或服务变更。",
        "承接来源": {
            "第22包总包": str(SOURCE22_PACKAGE),
            "第22包摘要": summary,
        },
        "触发条件草案": [
            "MoneyPrinterTurbo调用异常或入口不一致。",
            "ImageMagick可用性异常、版本不一致或命令失败。",
            "输出目录越界、容量不足、权限异常或生成产物不可追溯。",
            "素材授权、任务编号、日志留存或人工签收任一缺失。",
            "出现上传发布、n8n、企业微信、总管面板、一键接续或服务重载迹象。",
        ],
        "回滚步骤草案": [
            "立即确认 whitelist_effective=false、trial_run_allowed=false。",
            "停止扩大任务范围，保持真实渲染禁入。",
            "隔离并清点测试输出目录内临时产物。",
            "记录失败原因、输入摘要、任务编号、时间戳和责任人。",
            "恢复到第22包试运行禁入口径，并标记需要人工复核。",
            "形成回滚签收记录后再进入下一轮草案修订。",
        ],
        "临时产物处理": [
            "仅允许清点和登记隔离测试目录内临时文件。",
            "真实视频、发布产物、外部平台记录均不得生成。",
            "清理动作须由人工另行批准；本草案包不执行删除或清理命令。",
        ],
        "配置恢复要求": [
            "不得修改企业微信公共配置。",
            "不得修改总管面板。",
            "不得修改一键接续包。",
            "不得重载服务。",
        ],
        "日志留存要求": [
            "保留回滚触发原因、处置步骤、人工签收与只读核对报告。",
            "保留第22包承接关系与本包草案版本。",
        ],
        "人工确认签收": {
            "签收状态": "未签收",
            "必须签收角色": ["总管", "视频制作负责人", "回滚负责人"],
            "签收前是否可执行回滚预案": False,
        },
    }
    result.update(guarded_status(generated_at))
    return result


def build_package(generated_at: str, whitelist: dict[str, Any], rollback: dict[str, Any]) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染试运行白名单与回滚预案草案包",
        "包状态": "draft_only",
        "包结论": "承接第22包试运行禁入；白名单与回滚预案均为草案，未生效，仍不允许试运行。",
        "产物": {
            "白名单草案JSON": str(WHITELIST_LATEST),
            "白名单草案MD": str(WHITELIST_MD_LATEST),
            "回滚预案草案JSON": str(ROLLBACK_LATEST),
            "回滚预案草案MD": str(ROLLBACK_MD_LATEST),
        },
        "白名单草案": whitelist,
        "回滚预案草案": rollback,
        "红线": [
            "不调用 MoneyPrinterTurbo。",
            "不执行 magick 或 magick -version。",
            "不真实渲染，不生成真实视频，不发布。",
            "不接 n8n，不改企业微信公共配置，不改总管面板，不改一键接续包，不重载服务。",
        ],
    }
    result.update(guarded_status(generated_at))
    return result


def markdown_bool(value: Any) -> str:
    return "true" if value is True else "false" if value is False else str(value)


def build_whitelist_markdown(doc: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行白名单草案",
        "",
        f"- 生成时间：{doc['生成时间']}",
        f"- whitelist_effective：{markdown_bool(doc['whitelist_effective'])}",
        f"- trial_run_allowed：{markdown_bool(doc['trial_run_allowed'])}",
        f"- can_enter_real_render：{markdown_bool(doc['can_enter_real_render'])}",
        f"- 真实渲染：{markdown_bool(doc['真实渲染'])}",
        f"- 生成真实视频：{markdown_bool(doc['生成真实视频'])}",
        f"- 上传发布：{markdown_bool(doc['上传发布'])}",
        "",
        "## 允许任务类型草案",
        "",
    ]
    for item in doc["允许任务类型草案"]:
        lines.append(f"- {item['任务类型']}：当前是否允许执行={markdown_bool(item['当前是否允许执行'])}；{item['范围']}")
    lines.extend(["", "## 最大时长", "", f"- 单条视频最大时长秒：{doc['最大时长']['单条视频最大时长秒']}", "- 说明：该白名单未生效，当前仍不允许试运行。"])
    return "\n".join(lines) + "\n"


def build_rollback_markdown(doc: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行回滚预案草案",
        "",
        f"- 生成时间：{doc['生成时间']}",
        f"- whitelist_effective：{markdown_bool(doc['whitelist_effective'])}",
        f"- trial_run_allowed：{markdown_bool(doc['trial_run_allowed'])}",
        f"- can_enter_real_render：{markdown_bool(doc['can_enter_real_render'])}",
        f"- 执行magick：{markdown_bool(doc['执行magick'])}",
        f"- 执行magick_version：{markdown_bool(doc['执行magick_version'])}",
        "",
        "## 回滚步骤草案",
        "",
    ]
    lines.extend(f"- {item}" for item in doc["回滚步骤草案"])
    lines.extend(["", "## 配置恢复要求", ""])
    lines.extend(f"- {item}" for item in doc["配置恢复要求"])
    return "\n".join(lines) + "\n"


def build_package_markdown(doc: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行白名单与回滚预案草案包",
        "",
        f"- 生成时间：{doc['生成时间']}",
        f"- 包状态：{doc['包状态']}",
        f"- 包结论：{doc['包结论']}",
        f"- whitelist_effective：{markdown_bool(doc['whitelist_effective'])}",
        f"- trial_run_allowed：{markdown_bool(doc['trial_run_allowed'])}",
        f"- can_enter_real_render：{markdown_bool(doc['can_enter_real_render'])}",
        f"- 调用MoneyPrinterTurbo：{markdown_bool(doc['调用MoneyPrinterTurbo'])}",
        f"- 执行magick：{markdown_bool(doc['执行magick'])}",
        f"- 执行magick_version：{markdown_bool(doc['执行magick_version'])}",
        "",
        "## 产物",
        "",
    ]
    lines.extend(f"- {key}：{value}" for key, value in doc["产物"].items())
    lines.extend(["", "## 红线", ""])
    lines.extend(f"- {item}" for item in doc["红线"])
    return "\n".join(lines) + "\n"


def main() -> int:
    generated_at = now_text()
    source_package = load_json(SOURCE22_PACKAGE)
    trial_ban = load_json(SOURCE22_TRIAL_BAN)
    readonly_check = load_json(SOURCE22_READONLY_CHECK)
    summary = source_summary(source_package, trial_ban, readonly_check)

    whitelist = build_whitelist(generated_at, summary)
    rollback = build_rollback(generated_at, summary)
    package = build_package(generated_at, whitelist, rollback)
    stamp = stamp_text()

    write_json(DATA_DIR / f"视频真实渲染试运行白名单草案_{stamp}.json", whitelist)
    write_json(WHITELIST_LATEST, whitelist)
    write_text(WHITELIST_MD_LATEST, build_whitelist_markdown(whitelist))
    write_json(DATA_DIR / f"视频真实渲染试运行回滚预案草案_{stamp}.json", rollback)
    write_json(ROLLBACK_LATEST, rollback)
    write_text(ROLLBACK_MD_LATEST, build_rollback_markdown(rollback))
    write_json(DATA_DIR / f"视频真实渲染试运行白名单与回滚预案草案包_{stamp}.json", package)
    write_json(PACKAGE_LATEST, package)
    write_text(PACKAGE_MD_LATEST, build_package_markdown(package))

    print(
        json.dumps(
            {
                "package": str(PACKAGE_LATEST),
                "whitelist": str(WHITELIST_LATEST),
                "rollback": str(ROLLBACK_LATEST),
                "whitelist_effective": False,
                "trial_run_allowed": False,
                "can_enter_real_render": False,
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "调用MoneyPrinterTurbo": False,
                "执行magick": False,
                "执行magick_version": False,
                "error_count": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
