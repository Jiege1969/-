# -*- coding: utf-8 -*-
"""
生成视频真实渲染启用前总闸口与人工放行申请包。

红线：
- 不调用 MoneyPrinterTurbo。
- 不执行 magick，也不执行 magick -version。
- 不真实渲染，不生成真实视频，不上传发布。
- 不接 n8n，不改企业微信公共配置，不改总管面板，不改一键接续包，不重载服务。

本脚本只读取第20包候选路径矩阵/缺口与本包固定闸口规则，生成 blocked 状态的总闸口核对结果
和人工放行申请草案。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


SYSTEM_ROOT = Path(r"D:\杰哥智能化系统")
ROOT = SYSTEM_ROOT / "02杰哥扩展系统" / "02视频制作系统"
SOURCE20_DIR = ROOT / "03数据" / "20真实渲染环境候选路径矩阵与安装缺口清单"
DATA_DIR = ROOT / "03数据" / "21真实渲染启用前总闸口与人工放行申请包"

SOURCE20_PACKAGE = SOURCE20_DIR / "视频真实渲染环境候选路径矩阵与安装缺口清单_最新.json"
SOURCE20_CHECK = SOURCE20_DIR / "视频真实渲染环境候选路径只读核对_最新.json"
SOURCE20_GAP = SOURCE20_DIR / "视频真实渲染环境安装缺口清单_最新.json"

PACKAGE_LATEST = DATA_DIR / "视频真实渲染启用前总闸口与人工放行申请包_最新.json"
GATE_LATEST = DATA_DIR / "视频真实渲染启用前总闸口核对结果_最新.json"
APPROVAL_LATEST = DATA_DIR / "视频真实渲染人工放行申请草案_最新.json"
PACKAGE_MD_LATEST = DATA_DIR / "视频真实渲染启用前总闸口与人工放行申请包_最新.md"


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


def source_summary(source_package: dict[str, Any], source_check: dict[str, Any], source_gap: dict[str, Any]) -> dict[str, Any]:
    matrix = source_package.get("候选路径矩阵", {})
    money_rows = matrix.get("MoneyPrinterTurbo", [])
    magick_rows = matrix.get("ImageMagick", [])
    gaps = source_gap.get("缺口清单", [])

    return {
        "第20包名称": source_package.get("名称", ""),
        "第20包生成时间": source_package.get("生成时间", ""),
        "第20包可进入真实渲染": source_package.get("可进入真实渲染", False),
        "第20包只读核对可进入真实渲染": source_check.get("可进入真实渲染", False),
        "MoneyPrinterTurbo候选目录数": len(money_rows),
        "MoneyPrinterTurbo存在目录数": source_check.get("候选路径摘要", {}).get("MoneyPrinterTurbo存在目录数", 0),
        "MoneyPrinterTurbo含入口文件目录数": source_check.get("候选路径摘要", {}).get("MoneyPrinterTurbo含入口文件目录数", 0),
        "ImageMagick候选目录数": len(magick_rows),
        "ImageMagick存在目录数": source_check.get("候选路径摘要", {}).get("ImageMagick存在目录数", 0),
        "ImageMagick含magick_exe目录数": source_check.get("候选路径摘要", {}).get("ImageMagick含magick_exe目录数", 0),
        "安装缺口数量": source_gap.get("缺口数量", len(gaps)),
        "安装缺口清单": gaps,
        "第20包不得进入真实渲染原因": source_check.get("不得进入真实渲染原因", []),
    }


def manual_confirmation_items() -> list[dict[str, str]]:
    return [
        {
            "确认项": "MoneyPrinterTurbo入口",
            "当前状态": "blocked",
            "需人工确认": "确认实际入口文件、启动方式、依赖环境和项目配置；本包不调用 MoneyPrinterTurbo。",
        },
        {
            "确认项": "ImageMagick可用性",
            "当前状态": "blocked",
            "需人工确认": "确认安装目录、magick.exe、PATH 与版本；本包不执行 magick 或 magick -version。",
        },
        {
            "确认项": "测试素材",
            "当前状态": "blocked",
            "需人工确认": "确认素材来源、授权、格式、时长、分辨率和可用于真实渲染的测试任务。",
        },
        {
            "确认项": "输出目录",
            "当前状态": "blocked",
            "需人工确认": "确认真实渲染输出目录、命名规则、容量、权限和清理策略。",
        },
        {
            "确认项": "生成放行清单",
            "当前状态": "blocked",
            "需人工确认": "确认真实渲染前最终放行清单、责任人、回执和可追溯记录。",
        },
        {
            "确认项": "发布阻断保持",
            "当前状态": "blocked",
            "需人工确认": "确认真实渲染放行不等于上传发布放行；发布、n8n、企业微信和总管面板仍保持阻断。",
        },
    ]


def build_gate_result(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    return {
        "名称": "视频真实渲染启用前总闸口核对结果",
        "生成时间": generated_at,
        "来源": {
            "第20包候选路径矩阵": str(SOURCE20_PACKAGE),
            "第20包只读核对": str(SOURCE20_CHECK),
            "第20包安装缺口": str(SOURCE20_GAP),
        },
        "error_count": 0,
        "总闸口": "blocked",
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
        "第20包承接摘要": summary,
        "总闸口阻断原因": [
            "第20包仍为候选路径矩阵与安装缺口清单，未形成真实渲染放行授权。",
            "MoneyPrinterTurbo入口、依赖、配置、测试素材和输出目录均需人工确认。",
            "ImageMagick可用性需人工确认；本包不执行 magick 或 magick -version。",
            "生成放行清单未人工确认前，不得启用真实渲染。",
            "发布阻断保持；不得上传发布，不接 n8n，不改企业微信公共配置、总管面板或一键接续包。",
        ],
        "核对结论": "总闸口保持 blocked；当前不可进入真实渲染。",
    }


def build_approval_draft(generated_at: str, gate_result_path: Path) -> dict[str, Any]:
    return {
        "名称": "视频真实渲染人工放行申请草案",
        "生成时间": generated_at,
        "来源总闸口核对结果": str(gate_result_path),
        "申请状态": "blocked",
        "总闸口": "blocked",
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
        "需人工确认项": manual_confirmation_items(),
        "申请草案说明": [
            "这是人工放行申请草案，不是放行单。",
            "草案保持 blocked，不得被下游解释为真实渲染启用。",
            "完成全部人工确认并形成独立放行清单前，真实渲染、真实视频生成和上传发布均保持 false。",
        ],
    }


def build_package() -> dict[str, Any]:
    generated_at = now_text()
    source_package = load_json(SOURCE20_PACKAGE)
    source_check = load_json(SOURCE20_CHECK)
    source_gap = load_json(SOURCE20_GAP)
    summary = source_summary(source_package, source_check, source_gap)
    gate_result = build_gate_result(summary, generated_at)
    approval_draft = build_approval_draft(generated_at, GATE_LATEST)

    return {
        "名称": "视频真实渲染启用前总闸口与人工放行申请包",
        "生成时间": generated_at,
        "error_count": 0,
        "总闸口": "blocked",
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
        "总闸口核对结果": gate_result,
        "人工放行申请草案": approval_draft,
        "红线保持": {
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


def build_markdown(package: dict[str, Any]) -> str:
    gate = package["总闸口核对结果"]
    approval = package["人工放行申请草案"]
    lines = [
        "# 视频真实渲染启用前总闸口与人工放行申请包",
        "",
        f"- 生成时间：{package['生成时间']}",
        f"- 总闸口：{package['总闸口']}",
        f"- 可进入真实渲染：{package['可进入真实渲染']}",
        f"- 真实渲染：{package['真实渲染']}",
        f"- 生成真实视频：{package['生成真实视频']}",
        f"- 上传发布：{package['上传发布']}",
        f"- error_count：{package['error_count']}",
        "",
        "## 总闸口阻断原因",
        "",
    ]
    for item in gate["总闸口阻断原因"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 需人工确认项", ""])
    for item in approval["需人工确认项"]:
        lines.append(f"- {item['确认项']}：{item['需人工确认']}（{item['当前状态']}）")
    return "\n".join(lines) + "\n"


def main() -> int:
    package = build_package()
    gate_result = package["总闸口核对结果"]
    approval_draft = package["人工放行申请草案"]
    stamp = stamp_text()

    package_stamped = DATA_DIR / f"视频真实渲染启用前总闸口与人工放行申请包_{stamp}.json"
    gate_stamped = DATA_DIR / f"视频真实渲染启用前总闸口核对结果_{stamp}.json"
    approval_stamped = DATA_DIR / f"视频真实渲染人工放行申请草案_{stamp}.json"

    write_json(PACKAGE_LATEST, package)
    write_json(package_stamped, package)
    write_json(GATE_LATEST, gate_result)
    write_json(gate_stamped, gate_result)
    write_json(APPROVAL_LATEST, approval_draft)
    write_json(approval_stamped, approval_draft)
    write_text(PACKAGE_MD_LATEST, build_markdown(package))

    print(
        json.dumps(
            {
                "package": str(PACKAGE_LATEST),
                "gate_result": str(GATE_LATEST),
                "approval_draft": str(APPROVAL_LATEST),
                "总闸口": "blocked",
                "可进入真实渲染": False,
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
