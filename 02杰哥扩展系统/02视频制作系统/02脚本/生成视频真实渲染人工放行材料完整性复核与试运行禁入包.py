# -*- coding: utf-8 -*-
"""
生成视频真实渲染人工放行材料完整性复核与试运行禁入包。

红线：
- 不调用 MoneyPrinterTurbo。
- 不执行 magick，也不执行 magick -version。
- 不真实渲染，不生成真实视频，不上传发布。
- 不接 n8n，不改企业微信公共配置，不改总管面板，不改一键接续包，不重载服务。

本脚本只读取第21包总闸口与人工放行申请草案，输出材料完整性复核、
试运行禁入清单和下一步人工补齐卡。它不是放行单，也不触发试运行。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
SOURCE21_DIR = ROOT / "03数据" / "21真实渲染启用前总闸口与人工放行申请包"
DATA_DIR = ROOT / "03数据" / "22真实渲染人工放行材料完整性复核与试运行禁入包"

SOURCE21_PACKAGE = SOURCE21_DIR / "视频真实渲染启用前总闸口与人工放行申请包_最新.json"
SOURCE21_GATE = SOURCE21_DIR / "视频真实渲染启用前总闸口核对结果_最新.json"
SOURCE21_APPROVAL = SOURCE21_DIR / "视频真实渲染人工放行申请草案_最新.json"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染人工放行材料完整性复核与试运行禁入包_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染人工放行材料完整性复核与试运行禁入包_最新.md"
MATERIAL_REVIEW_LATEST = DATA_DIR / "视频真实渲染人工放行材料完整性复核_最新.json"
MATERIAL_REVIEW_MD_LATEST = DATA_DIR / "视频真实渲染人工放行材料完整性复核_最新.md"
TRIAL_BAN_LATEST = DATA_DIR / "视频真实渲染试运行禁入清单_最新.json"
TRIAL_BAN_MD_LATEST = DATA_DIR / "视频真实渲染试运行禁入清单_最新.md"
NEXT_CARD_LATEST = DATA_DIR / "视频真实渲染下一步人工补齐卡_最新.json"
NEXT_CARD_MD_LATEST = DATA_DIR / "视频真实渲染下一步人工补齐卡_最新.md"


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


def blocked_flags_cn() -> dict[str, bool]:
    return {
        "试运行禁入": True,
        "可进入真实渲染": False,
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
    }


def blocked_flags_ascii() -> dict[str, bool]:
    return {
        "trial_run_forbidden": True,
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


def required_materials() -> list[dict[str, str]]:
    return [
        {
            "材料项": "MoneyPrinterTurbo入口",
            "复核口径": "入口文件、启动方式、依赖环境、项目配置与责任人签收必须齐全。",
            "当前结论": "待人工补齐",
            "禁入原因": "第21包为申请草案，不包含可执行入口签收；本包不调用 MoneyPrinterTurbo。",
        },
        {
            "材料项": "ImageMagick可用性",
            "复核口径": "安装路径、magick.exe、PATH、版本核对和人工签收必须齐全。",
            "当前结论": "待人工补齐",
            "禁入原因": "第21包未执行版本核对；本包不执行 magick 或 magick -version。",
        },
        {
            "材料项": "测试素材",
            "复核口径": "素材来源、授权、格式、分辨率、时长和测试任务编号必须齐全。",
            "当前结论": "待人工补齐",
            "禁入原因": "未见真实渲染测试素材授权与任务级签收。",
        },
        {
            "材料项": "输出目录",
            "复核口径": "输出目录、命名规则、容量、权限、清理策略与隔离策略必须齐全。",
            "当前结论": "待人工补齐",
            "禁入原因": "未见真实输出目录人工确认；不得生成真实视频。",
        },
        {
            "材料项": "生成放行清单",
            "复核口径": "真实渲染前最终放行清单、责任人、回执、时间戳和追溯路径必须齐全。",
            "当前结论": "待人工补齐",
            "禁入原因": "第21包为草案，不是最终放行清单。",
        },
        {
            "材料项": "发布阻断保持",
            "复核口径": "真实渲染放行不得自动扩展为上传发布、n8n、企业微信或总管面板放行。",
            "当前结论": "保持阻断",
            "禁入原因": "发布链路必须独立放行；本包明确上传发布=false。",
        },
        {
            "材料项": "回滚方案",
            "复核口径": "失败回滚、产物隔离、临时文件清理、配置恢复和责任人必须齐全。",
            "当前结论": "待人工补齐",
            "禁入原因": "未见真实渲染试运行回滚方案签收。",
        },
        {
            "材料项": "人工确认签收",
            "复核口径": "总管/责任人签收、签收时间、签收范围和禁止外溢声明必须齐全。",
            "当前结论": "待人工补齐",
            "禁入原因": "第21包仅提供申请草案，不包含人工签收回执。",
        },
    ]


def base_status(generated_at: str) -> dict[str, Any]:
    return {
        "生成时间": generated_at,
        "error_count": 0,
        "试运行禁入": True,
        "trial_run_forbidden": True,
        "可进入真实渲染": False,
        "can_enter_real_render": False,
        "真实渲染": False,
        "生成真实视频": False,
        "上传发布": False,
        "调用MoneyPrinterTurbo": False,
        "执行magick": False,
        "执行magick_version": False,
        "readonly_flags": blocked_flags_cn(),
        "readonly_flags_ascii": blocked_flags_ascii(),
    }


def source_summary(source_package: dict[str, Any], source_gate: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    return {
        "第21包总包存在": bool(source_package),
        "第21包总闸口结果存在": bool(source_gate),
        "第21包人工放行申请草案存在": bool(approval),
        "第21包名称": source_package.get("名称", ""),
        "第21包生成时间": source_package.get("生成时间", ""),
        "第21包总闸口": source_package.get("总闸口", ""),
        "第21包申请状态": approval.get("申请状态", ""),
        "第21包可进入真实渲染": source_package.get("可进入真实渲染", None),
        "第21包真实渲染": source_package.get("真实渲染", None),
        "第21包生成真实视频": source_package.get("生成真实视频", None),
        "第21包上传发布": source_package.get("上传发布", None),
        "第21包调用MoneyPrinterTurbo": source_package.get("调用MoneyPrinterTurbo", None),
        "第21包执行magick": source_package.get("执行magick", None),
        "第21包执行magick_version": source_package.get("执行magick_version", None),
        "第21包人工确认项": [item.get("确认项") for item in approval.get("需人工确认项", [])],
        "第21包阻断原因": source_gate.get("总闸口阻断原因", []),
    }


def build_material_review(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染人工放行材料完整性复核",
        "来源": {
            "第21包总包": str(SOURCE21_PACKAGE),
            "第21包总闸口结果": str(SOURCE21_GATE),
            "第21包人工放行申请草案": str(SOURCE21_APPROVAL),
        },
        "复核方式": "只读复核",
        "复核结论": "材料待人工补齐，试运行禁入，真实渲染禁入。",
        "第21包承接摘要": summary,
        "材料复核项": required_materials(),
        "材料完整性结论": {
            "MoneyPrinterTurbo入口": "待人工补齐",
            "ImageMagick可用性": "待人工补齐",
            "测试素材": "待人工补齐",
            "输出目录": "待人工补齐",
            "生成放行清单": "待人工补齐",
            "发布阻断保持": "已确认保持阻断",
            "回滚方案": "待人工补齐",
            "人工确认签收": "待人工补齐",
        },
    }
    result.update(base_status(generated_at))
    return result


def build_trial_ban(generated_at: str, material_review_path: Path) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染试运行禁入清单",
        "来源材料完整性复核": str(material_review_path),
        "禁入结论": "试运行禁入=true；任何真实渲染、真实视频生成或上传发布均不得开始。",
        "禁入项": [
            {"动作": "试运行真实渲染", "允许": False, "原因": "人工放行材料未完整签收。"},
            {"动作": "调用MoneyPrinterTurbo", "允许": False, "原因": "入口和依赖未人工确认。"},
            {"动作": "执行magick", "允许": False, "原因": "本包禁止执行 ImageMagick 命令。"},
            {"动作": "执行magick -version", "允许": False, "原因": "版本核对须人工另行执行，本包只读。"},
            {"动作": "生成真实视频", "允许": False, "原因": "输出目录和测试素材未签收。"},
            {"动作": "上传发布", "允许": False, "原因": "发布阻断保持，发布链路需独立放行。"},
            {"动作": "接入n8n", "允许": False, "原因": "红线禁止。"},
            {"动作": "修改企业微信公共配置", "允许": False, "原因": "红线禁止。"},
            {"动作": "修改总管面板", "允许": False, "原因": "红线禁止。"},
            {"动作": "修改一键接续包", "允许": False, "原因": "红线禁止。"},
            {"动作": "重载服务", "允许": False, "原因": "红线禁止。"},
        ],
    }
    result.update(base_status(generated_at))
    return result


def build_next_card(generated_at: str, material_review_path: Path, trial_ban_path: Path) -> dict[str, Any]:
    result = {
        "名称": "视频真实渲染下一步人工补齐卡",
        "来源": {
            "材料完整性复核": str(material_review_path),
            "试运行禁入清单": str(trial_ban_path),
        },
        "卡片状态": "待人工补齐",
        "下一步人工动作": [
            "补齐 MoneyPrinterTurbo 入口、启动方式、依赖环境、配置文件和责任人签收。",
            "由人工另行确认 ImageMagick 安装、PATH、版本和 magick.exe 可用性；本包不执行命令。",
            "补齐测试素材授权、格式、分辨率、时长、任务编号和用途边界。",
            "补齐真实渲染输出目录、权限、容量、命名规则、清理策略和隔离策略。",
            "形成独立的真实渲染生成放行清单，并写明不包含上传发布放行。",
            "补齐失败回滚方案、临时产物清理方案、配置恢复方案和责任人。",
            "补齐总管/责任人的人工确认签收回执。",
        ],
        "不得误解": [
            "本卡不是试运行许可。",
            "材料补齐前，试运行禁入保持 true。",
            "即使未来真实渲染被人工放行，上传发布仍需独立放行。",
        ],
    }
    result.update(base_status(generated_at))
    return result


def build_package() -> dict[str, Any]:
    generated_at = now_text()
    source_package = load_json(SOURCE21_PACKAGE)
    source_gate = load_json(SOURCE21_GATE)
    approval = load_json(SOURCE21_APPROVAL)
    summary = source_summary(source_package, source_gate, approval)
    material_review = build_material_review(generated_at, summary)
    trial_ban = build_trial_ban(generated_at, MATERIAL_REVIEW_LATEST)
    next_card = build_next_card(generated_at, MATERIAL_REVIEW_LATEST, TRIAL_BAN_LATEST)
    result = {
        "名称": "视频真实渲染人工放行材料完整性复核与试运行禁入包",
        "总闸口承接": "承接第21包总闸口；保持 blocked。",
        "包结论": "材料待人工补齐；试运行禁入；不可进入真实渲染。",
        "材料完整性复核": material_review,
        "试运行禁入清单": trial_ban,
        "下一步人工补齐卡": next_card,
        "产物路径": {
            "总包": str(PACKAGE_LATEST),
            "材料完整性复核": str(MATERIAL_REVIEW_LATEST),
            "试运行禁入清单": str(TRIAL_BAN_LATEST),
            "下一步人工补齐卡": str(NEXT_CARD_LATEST),
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
    }
    result.update(base_status(generated_at))
    return result


def material_review_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染人工放行材料完整性复核",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 复核方式：{result['复核方式']}",
        f"- 试运行禁入：{result['试运行禁入']}",
        f"- 可进入真实渲染：{result['可进入真实渲染']}",
        f"- error_count：{result['error_count']}",
        "",
        "## 材料复核项",
        "",
    ]
    for item in result["材料复核项"]:
        lines.append(f"- {item['材料项']}：{item['当前结论']}；{item['禁入原因']}")
    lines.extend(["", f"结论：{result['复核结论']}"])
    return "\n".join(lines) + "\n"


def trial_ban_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染试运行禁入清单",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 试运行禁入：{result['试运行禁入']}",
        f"- 可进入真实渲染：{result['可进入真实渲染']}",
        f"- 真实渲染：{result['真实渲染']}",
        f"- 生成真实视频：{result['生成真实视频']}",
        f"- 上传发布：{result['上传发布']}",
        "",
        "## 禁入项",
        "",
    ]
    for item in result["禁入项"]:
        lines.append(f"- {item['动作']}：允许={item['允许']}；{item['原因']}")
    return "\n".join(lines) + "\n"


def next_card_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染下一步人工补齐卡",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 卡片状态：{result['卡片状态']}",
        f"- 试运行禁入：{result['试运行禁入']}",
        "",
        "## 下一步人工动作",
        "",
    ]
    for action in result["下一步人工动作"]:
        lines.append(f"- {action}")
    lines.extend(["", "## 不得误解", ""])
    for item in result["不得误解"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def package_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# 视频真实渲染人工放行材料完整性复核与试运行禁入包",
        "",
        f"- 生成时间：{result['生成时间']}",
        f"- 试运行禁入：{result['试运行禁入']}",
        f"- 可进入真实渲染：{result['可进入真实渲染']}",
        f"- 真实渲染：{result['真实渲染']}",
        f"- 生成真实视频：{result['生成真实视频']}",
        f"- 上传发布：{result['上传发布']}",
        f"- 调用MoneyPrinterTurbo：{result['调用MoneyPrinterTurbo']}",
        f"- 执行magick：{result['执行magick']}",
        f"- 执行magick_version：{result['执行magick_version']}",
        f"- error_count：{result['error_count']}",
        "",
        "## 包结论",
        "",
        result["包结论"],
        "",
        "## 产物",
        "",
    ]
    for name, path in result["产物路径"].items():
        lines.append(f"- {name}：{path}")
    return "\n".join(lines) + "\n"


def main() -> int:
    package = build_package()
    stamp = stamp_text()
    material_review = package["材料完整性复核"]
    trial_ban = package["试运行禁入清单"]
    next_card = package["下一步人工补齐卡"]

    write_json(DATA_DIR / f"视频真实渲染人工放行材料完整性复核与试运行禁入包_{stamp}.json", package)
    write_json(PACKAGE_LATEST, package)
    write_text(PACKAGE_MD_LATEST, package_markdown(package))

    write_json(DATA_DIR / f"视频真实渲染人工放行材料完整性复核_{stamp}.json", material_review)
    write_json(MATERIAL_REVIEW_LATEST, material_review)
    write_text(MATERIAL_REVIEW_MD_LATEST, material_review_markdown(material_review))

    write_json(DATA_DIR / f"视频真实渲染试运行禁入清单_{stamp}.json", trial_ban)
    write_json(TRIAL_BAN_LATEST, trial_ban)
    write_text(TRIAL_BAN_MD_LATEST, trial_ban_markdown(trial_ban))

    write_json(DATA_DIR / f"视频真实渲染下一步人工补齐卡_{stamp}.json", next_card)
    write_json(NEXT_CARD_LATEST, next_card)
    write_text(NEXT_CARD_MD_LATEST, next_card_markdown(next_card))

    print(
        json.dumps(
            {
                "package": str(PACKAGE_LATEST),
                "material_review": str(MATERIAL_REVIEW_LATEST),
                "trial_ban": str(TRIAL_BAN_LATEST),
                "next_card": str(NEXT_CARD_LATEST),
                "试运行禁入": True,
                "可进入真实渲染": False,
                "真实渲染": False,
                "生成真实视频": False,
                "上传发布": False,
                "调用MoneyPrinterTurbo": False,
                "执行magick": False,
                "执行magick_version": False,
                "error_count": package["error_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if package["error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
