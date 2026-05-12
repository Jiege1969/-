# -*- coding: utf-8 -*-
"""
生成视频真实渲染试运行批次预检与白名单未生效闸口包。

本脚本只读取第23包白名单草案和本包产物，生成试运行批次样例、
白名单未生效闸口和人工签收清单。它不调用 MoneyPrinterTurbo，不执行
magick 或 magick -version，不真实渲染，不生成真实视频，不上传发布，
不接 n8n，不改公共配置、面板、接续包或服务。
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

SOURCE23_PACKAGE = SOURCE23_DIR / "视频真实渲染试运行白名单与回滚预案草案包_最新.json"
SOURCE23_WHITELIST = SOURCE23_DIR / "视频真实渲染试运行白名单草案_最新.json"
SOURCE23_READONLY_CHECK = SOURCE23_DIR / "视频真实渲染试运行白名单只读核对报告_最新.json"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染试运行批次预检与白名单未生效闸口包_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次预检与白名单未生效闸口包_最新.md"
PRECHECK_LATEST = DATA_DIR / "视频真实渲染试运行批次预检_最新.json"
PRECHECK_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次预检_最新.md"
GATE_LATEST = DATA_DIR / "视频真实渲染白名单未生效闸口_最新.json"
GATE_MD_LATEST = DATA_DIR / "视频真实渲染白名单未生效闸口_最新.md"
SIGNOFF_LATEST = DATA_DIR / "视频真实渲染试运行批次人工签收清单_最新.json"
SIGNOFF_MD_LATEST = DATA_DIR / "视频真实渲染试运行批次人工签收清单_最新.md"


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
        "batch_allowed": False,
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
        },
    }


def source23_summary(package: dict[str, Any], whitelist: dict[str, Any], readonly_check: dict[str, Any]) -> dict[str, Any]:
    return {
        "第23包总包存在": bool(package),
        "第23包白名单草案存在": bool(whitelist),
        "第23包只读核对存在": bool(readonly_check),
        "第23包名称": package.get("名称", ""),
        "第23包结论": package.get("包结论", ""),
        "第23包只读核对结论": readonly_check.get("核对结论", ""),
        "第23包error_count": readonly_check.get("error_count"),
        "第23包白名单状态": whitelist.get("状态", ""),
        "第23包whitelist_effective": whitelist.get("whitelist_effective"),
        "第23包trial_run_allowed": whitelist.get("trial_run_allowed"),
        "第23包can_enter_real_render": whitelist.get("can_enter_real_render"),
        "第23包真实渲染": whitelist.get("真实渲染"),
        "第23包生成真实视频": whitelist.get("生成真实视频"),
        "第23包上传发布": whitelist.get("上传发布"),
    }


def build_batch_sample(generated_at: str, whitelist: dict[str, Any]) -> dict[str, Any]:
    return {
        "批次ID": "TRIAL-BATCH-PRECHECK-20260508-001",
        "任务ID": "TRIAL-TASK-PRECHECK-20260508-001",
        "批次类型": "真实渲染试运行批次样例",
        "批次状态": "precheck_only",
        "当前是否允许进入批次": False,
        "白名单来源状态": {
            "来源文件": str(SOURCE23_WHITELIST),
            "白名单状态": whitelist.get("状态", ""),
            "whitelist_effective": whitelist.get("whitelist_effective"),
            "trial_run_allowed": whitelist.get("trial_run_allowed"),
        },
        "素材要求": {
            "素材用途": "仅限未来人工放行后的低风险测试用途",
            "授权要求": "素材来源、授权证明、格式、分辨率、时长、任务编号均需人工签收",
            "禁止项": [
                "不得使用生产发布素材",
                "不得混入生产素材池",
                "不得触发外部上传发布链路",
            ],
        },
        "输出目录": {
            "样例目录": str(DATA_DIR / "隔离试运行输出样例" / "TRIAL-BATCH-PRECHECK-20260508-001"),
            "要求": [
                "仅作为路径样例，不创建真实渲染产物",
                "必须隔离于生产成片目录",
                "不得被 n8n、企业微信、总管面板或一键接续包读取为发布输入",
            ],
        },
        "最大时长": {
            "单条视频最大时长秒": 15,
            "单批次最大任务数": 1,
            "说明": "样例参数来自第23包草案口径；当前不代表允许执行。",
        },
        "失败回滚": [
            "任何预检失败均保持 batch_allowed=false。",
            "任何白名单未生效均保持 trial_run_allowed=false。",
            "不得重试真实渲染，不得扩大任务范围。",
            "仅登记失败原因和人工复核要求，不执行删除、清理、重载或发布动作。",
        ],
        "日志留存": [
            "留存批次ID、任务ID、来源白名单草案、闸口结论和人工签收状态。",
            "留存不少于30天或按人工要求延长。",
            "日志不得包含发布凭据或真实视频产物。",
        ],
        "人工签收": {
            "签收状态": "未签收",
            "签收后仍需另行启用白名单": True,
            "签收后仍需另行试运行放行": True,
        },
        "生成时间": generated_at,
    }


def build_precheck(generated_at: str, summary: dict[str, Any], batch_sample: dict[str, Any]) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染试运行批次预检",
        "预检方式": "只读样例预检",
        "预检结论": "白名单未生效，批次不允许，试运行不允许，不可进入真实渲染。",
        "承接来源": {
            "第23包总包": str(SOURCE23_PACKAGE),
            "第23包白名单草案": str(SOURCE23_WHITELIST),
            "第23包只读核对": str(SOURCE23_READONLY_CHECK),
            "第23包摘要": summary,
        },
        "试运行批次样例": batch_sample,
        "预检项": [
            {"项目": "批次ID", "值": batch_sample["批次ID"], "通过": True},
            {"项目": "任务ID", "值": batch_sample["任务ID"], "通过": True},
            {"项目": "素材要求", "值": batch_sample["素材要求"], "通过": True},
            {"项目": "输出目录", "值": batch_sample["输出目录"], "通过": True},
            {"项目": "最大时长", "值": batch_sample["最大时长"], "通过": True},
            {"项目": "失败回滚", "值": batch_sample["失败回滚"], "通过": True},
            {"项目": "日志留存", "值": batch_sample["日志留存"], "通过": True},
            {"项目": "人工签收", "值": batch_sample["人工签收"], "通过": True},
            {"项目": "白名单未生效", "值": False, "通过": True},
        ],
    }
    result.update(guarded_status(generated_at))
    return result


def build_inactive_gate(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染白名单未生效闸口",
        "闸口状态": "closed",
        "闸口结论": "白名单未生效，阻止试运行批次进入真实渲染。",
        "关闭原因": [
            "第23包白名单仍为草案。",
            "缺少人工签收和另行启用动作。",
            "本包仅做只读预检，不授权试运行。",
        ],
        "承接来源摘要": summary,
        "阻断字段": {
            "batch_allowed": False,
            "whitelist_effective": False,
            "trial_run_allowed": False,
            "can_enter_real_render": False,
            "真实渲染": False,
            "生成真实视频": False,
            "上传发布": False,
        },
        "放行前置条件草案": [
            "第23包白名单必须由人工另行签收并改为生效。",
            "批次ID、任务ID、素材授权、隔离输出目录、失败回滚和日志留存均需人工签收。",
            "仍需新的独立闸口包确认试运行允许；本包不提供放行能力。",
        ],
    }
    result.update(guarded_status(generated_at))
    return result


def build_signoff(generated_at: str, batch_sample: dict[str, Any]) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染试运行批次人工签收清单",
        "清单状态": "unsigned",
        "签收结论": "未签收；白名单未生效；批次不允许。",
        "批次ID": batch_sample["批次ID"],
        "任务ID": batch_sample["任务ID"],
        "签收项": [
            {"签收项": "批次ID唯一且仅用于试运行样例", "签收状态": "未签收", "当前可执行": False},
            {"签收项": "任务ID唯一且可追溯", "签收状态": "未签收", "当前可执行": False},
            {"签收项": "测试素材来源与授权齐备", "签收状态": "未签收", "当前可执行": False},
            {"签收项": "输出目录隔离且不接发布链路", "签收状态": "未签收", "当前可执行": False},
            {"签收项": "最大时长和单批任务数确认", "签收状态": "未签收", "当前可执行": False},
            {"签收项": "失败回滚负责人确认", "签收状态": "未签收", "当前可执行": False},
            {"签收项": "日志留存责任人确认", "签收状态": "未签收", "当前可执行": False},
            {"签收项": "白名单另行启用确认", "签收状态": "未签收", "当前可执行": False},
        ],
        "必须签收角色": ["总管", "视频制作负责人", "素材授权负责人", "回滚负责人", "日志留存负责人"],
        "签收后限制": [
            "签收本清单不等于白名单生效。",
            "签收本清单不等于允许试运行。",
            "仍需新的独立放行包确认 batch_allowed=true；本包不会产生该状态。",
        ],
    }
    result.update(guarded_status(generated_at))
    return result


def build_package(generated_at: str, precheck: dict[str, Any], gate: dict[str, Any], signoff: dict[str, Any]) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染试运行批次预检与白名单未生效闸口包",
        "包状态": "precheck_only",
        "包结论": "承接第23包白名单草案；白名单未生效，批次不允许，试运行不允许，不可进入真实渲染。",
        "产物": {
            "批次预检JSON": str(PRECHECK_LATEST),
            "批次预检MD": str(PRECHECK_MD_LATEST),
            "白名单未生效闸口JSON": str(GATE_LATEST),
            "白名单未生效闸口MD": str(GATE_MD_LATEST),
            "人工签收清单JSON": str(SIGNOFF_LATEST),
            "人工签收清单MD": str(SIGNOFF_MD_LATEST),
        },
        "批次预检": precheck,
        "白名单未生效闸口": gate,
        "人工签收清单": signoff,
        "红线": [
            "不调用 MoneyPrinterTurbo。",
            "不执行 magick 或 magick -version。",
            "不真实渲染，不生成真实视频，不发布。",
            "不接 n8n，不改企业微信公共配置，不改总管面板，不改一键接续包，不重载服务。",
        ],
    }
    result.update(guarded_status(generated_at))
    return result


def bullet_lines(items: list[Any]) -> list[str]:
    lines: list[str] = []
    for item in items:
        if isinstance(item, dict):
            title = item.get("项目") or item.get("签收项") or item.get("任务类型") or "项目"
            lines.append(f"- {title}：{json.dumps(item, ensure_ascii=False)}")
        else:
            lines.append(f"- {item}")
    return lines


def build_precheck_markdown(result: dict[str, Any]) -> str:
    batch = result["试运行批次样例"]
    lines = [
        "# 视频真实渲染试运行批次预检",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- batch_allowed：{str(result['batch_allowed']).lower()}",
        f"- whitelist_effective：{str(result['whitelist_effective']).lower()}",
        f"- trial_run_allowed：{str(result['trial_run_allowed']).lower()}",
        f"- can_enter_real_render：{str(result['can_enter_real_render']).lower()}",
        f"- 真实渲染：{str(result['真实渲染']).lower()}",
        f"- 生成真实视频：{str(result['生成真实视频']).lower()}",
        f"- 上传发布：{str(result['上传发布']).lower()}",
        "",
        "## 批次样例",
        "",
        f"- 批次ID：{batch['批次ID']}",
        f"- 任务ID：{batch['任务ID']}",
        f"- 最大时长：{batch['最大时长']['单条视频最大时长秒']}秒",
        "",
        "## 预检项",
        "",
    ]
    lines.extend(bullet_lines(result["预检项"]))
    lines.extend(["", f"结论：{result['预检结论']}"])
    return "\n".join(lines) + "\n"


def build_gate_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染白名单未生效闸口",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 闸口状态：{result['闸口状态']}",
        f"- batch_allowed：{str(result['batch_allowed']).lower()}",
        f"- whitelist_effective：{str(result['whitelist_effective']).lower()}",
        f"- trial_run_allowed：{str(result['trial_run_allowed']).lower()}",
        f"- can_enter_real_render：{str(result['can_enter_real_render']).lower()}",
        "",
        "## 关闭原因",
        "",
    ]
    lines.extend(bullet_lines(result["关闭原因"]))
    lines.extend(["", f"结论：{result['闸口结论']}"])
    return "\n".join(lines) + "\n"


def build_signoff_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行批次人工签收清单",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 批次ID：{result['批次ID']}",
        f"- 任务ID：{result['任务ID']}",
        f"- 清单状态：{result['清单状态']}",
        f"- batch_allowed：{str(result['batch_allowed']).lower()}",
        f"- trial_run_allowed：{str(result['trial_run_allowed']).lower()}",
        "",
        "## 签收项",
        "",
    ]
    lines.extend(bullet_lines(result["签收项"]))
    lines.extend(["", f"结论：{result['签收结论']}"])
    return "\n".join(lines) + "\n"


def build_package_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行批次预检与白名单未生效闸口包",
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
        "## 产物",
        "",
    ]
    lines.extend(f"- {name}：{path}" for name, path in result["产物"].items())
    lines.extend(["", f"结论：{result['包结论']}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    generated_at = now_text()
    stamp = stamp_text()
    source23_package = load_json(SOURCE23_PACKAGE)
    source23_whitelist = load_json(SOURCE23_WHITELIST)
    source23_check = load_json(SOURCE23_READONLY_CHECK)
    summary = source23_summary(source23_package, source23_whitelist, source23_check)
    batch_sample = build_batch_sample(generated_at, source23_whitelist)
    precheck = build_precheck(generated_at, summary, batch_sample)
    gate = build_inactive_gate(generated_at, summary)
    signoff = build_signoff(generated_at, batch_sample)
    package = build_package(generated_at, precheck, gate, signoff)

    write_json(DATA_DIR / f"视频真实渲染试运行批次预检_{stamp}.json", precheck)
    write_json(PRECHECK_LATEST, precheck)
    write_text(PRECHECK_MD_LATEST, build_precheck_markdown(precheck))
    write_json(DATA_DIR / f"视频真实渲染白名单未生效闸口_{stamp}.json", gate)
    write_json(GATE_LATEST, gate)
    write_text(GATE_MD_LATEST, build_gate_markdown(gate))
    write_json(DATA_DIR / f"视频真实渲染试运行批次人工签收清单_{stamp}.json", signoff)
    write_json(SIGNOFF_LATEST, signoff)
    write_text(SIGNOFF_MD_LATEST, build_signoff_markdown(signoff))
    write_json(DATA_DIR / f"视频真实渲染试运行批次预检与白名单未生效闸口包_{stamp}.json", package)
    write_json(PACKAGE_LATEST, package)
    write_text(PACKAGE_MD_LATEST, build_package_markdown(package))

    print(
        json.dumps(
            {
                "package": str(PACKAGE_LATEST),
                "precheck": str(PRECHECK_LATEST),
                "inactive_gate": str(GATE_LATEST),
                "signoff": str(SIGNOFF_LATEST),
                "batch_allowed": False,
                "whitelist_effective": False,
                "trial_run_allowed": False,
                "can_enter_real_render": False,
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "error_count": 0,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
