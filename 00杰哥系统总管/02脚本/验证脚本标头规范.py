# -*- coding: utf-8 -*-
"""
名称：验证脚本标头规范.py
作用：审计主线自有脚本是否具备八项标准标头，并生成历史存量脚本标头债务清单。
触发方式：手动验收；新建或改造脚本后本地执行；不由n8n自动触发。
依赖：本机Python标准库、00/01/02/03系统脚本目录。
所属系统：00杰哥系统总管。
输出：04日志/脚本标头规范/脚本标头规范审计_最新.json 与 .md。
安全边界：只读脚本文件；只写总管04日志审计结果；不触发n8n、不发送企业微信、不重启服务、不写正式业务库、不调用券商接口。
标识：脚本治理；八项标头；只读审计；存量债务不阻断主线。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
INTELLIGENCE = ROOT / "01杰哥智能系统"
STOCK = ROOT / "02杰哥扩展系统" / "01股票研究系统"
EVOLUTION = ROOT / "03杰哥进化系统"
OUT_DIR = MANAGER / "04日志" / "脚本标头规范"

REQUIRED_FIELDS = [
    "名称：",
    "作用：",
    "触发方式：",
    "依赖：",
    "所属系统：",
    "输出：",
    "安全边界：",
    "标识：",
]

SCAN_ROOTS = [
    MANAGER / "02脚本",
    INTELLIGENCE / "02脚本",
    STOCK / "02脚本",
    EVOLUTION / "02脚本",
]

EXCLUDED_PARTS = {
    ".venv",
    "venv",
    "__pycache__",
    "site-packages",
    "node_modules",
    ".git",
    "缓存",
    "cache",
    "归档",
    "桌面bat归档",
    "backup",
    "bak",
}

MAINLINE_SCRIPTS = [
    MANAGER / "02脚本" / "验证脚本标头规范.py",
    MANAGER / "02脚本" / "执行四系统小闭环开工快检.py",
    MANAGER / "02脚本" / "验证四系统小闭环开工快检.py",
    MANAGER / "02脚本" / "生成智能化施工落地检查清单.py",
    MANAGER / "02脚本" / "验证智能化施工落地检查清单.py",
    MANAGER / "02脚本" / "执行四系统股票小闭环.py",
    MANAGER / "02脚本" / "生成四系统股票小闭环状态面板.py",
    MANAGER / "02脚本" / "生成四系统股票小闭环历史观察面板.py",
    MANAGER / "02脚本" / "验证四系统股票小闭环.py",
    MANAGER / "02脚本" / "生成股票四系统融合闭环状态面板.py",
    MANAGER / "02脚本" / "验证股票四系统融合闭环状态面板.py",
    MANAGER / "02脚本" / "验证散点共识归集落实.py",
    MANAGER / "02脚本" / "验证版本升级治理闭环.py",
    MANAGER / "02脚本" / "维护" / "auto_version_snapshot.py",
    MANAGER / "02脚本" / "维护" / "version_intel.py",
    MANAGER / "02脚本" / "维护" / "generate_n8n_shadow_plan.py",
    MANAGER / "02脚本" / "维护" / "rollback_capability_inventory.py",
    MANAGER / "02脚本" / "维护" / "ledger_update_draft.py",
    MANAGER / "02脚本" / "维护" / "upgrade_window_check.py",
    MANAGER / "02脚本" / "维护" / "upgrade_governance_common.py",
    MANAGER / "02脚本" / "维护" / "version_check.py",
    INTELLIGENCE / "02脚本" / "文稿质检" / "text_reviewer.py",
    INTELLIGENCE / "02脚本" / "文稿质检" / "生成文稿质检旁路观察面板.py",
    INTELLIGENCE / "02脚本" / "文稿质检" / "验证文稿质检旁路观察面板.py",
    INTELLIGENCE / "02脚本" / "文稿质检" / "生成文稿质检样本复盘报告.py",
    INTELLIGENCE / "02脚本" / "文稿质检" / "验证文稿质检样本复盘报告.py",
    STOCK / "02脚本" / "股票助手入口.py",
    STOCK / "02脚本" / "股票企业微信桥接入口.py",
    STOCK / "02脚本" / "验证股票企微前台交互回归.py",
    STOCK / "02脚本" / "验证股票推荐点击详情与手机排版.py",
    STOCK / "02脚本" / "验证股票系统C加加加日常可用总验收.py",
    STOCK / "02脚本" / "生成股票证据链人工核验入口.py",
    STOCK / "02脚本" / "验证股票证据链人工核验入口.py",
    STOCK / "02脚本" / "生成单股证据核验人工填写台账.py",
    STOCK / "02脚本" / "验证单股证据核验人工填写台账.py",
    STOCK / "02脚本" / "生成单股证据核验人工填写CSV表单.py",
    STOCK / "02脚本" / "验证单股证据核验人工填写CSV表单.py",
    STOCK / "02脚本" / "生成单股证据核验人工填写最小行动卡.py",
    STOCK / "02脚本" / "验证单股证据核验人工填写最小行动卡.py",
    STOCK / "02脚本" / "生成单股证据核验人工填写工作台.py",
    STOCK / "02脚本" / "验证单股证据核验人工填写工作台.py",
    STOCK / "02脚本" / "生成单股证据核验资料来源导航卡.py",
    STOCK / "02脚本" / "验证单股证据核验资料来源导航卡.py",
    STOCK / "02脚本" / "生成单股证据核验资料候选处理包.py",
    STOCK / "02脚本" / "验证单股证据核验资料候选处理包.py",
    STOCK / "02脚本" / "生成单股证据核验191填写建议草案.py",
    STOCK / "02脚本" / "验证单股证据核验191填写建议草案.py",
    STOCK / "02脚本" / "生成单股证据核验最小人工确认清单.py",
    STOCK / "02脚本" / "验证单股证据核验最小人工确认清单.py",
    STOCK / "02脚本" / "生成单股证据核验191候选填写CSV副本.py",
    STOCK / "02脚本" / "验证单股证据核验191候选填写CSV副本.py",
    STOCK / "02脚本" / "生成单股证据核验191候选写入差异预览.py",
    STOCK / "02脚本" / "验证单股证据核验191候选写入差异预览.py",
    STOCK / "02脚本" / "生成单股证据核验191候选采用后质量预演.py",
    STOCK / "02脚本" / "验证单股证据核验191候选采用后质量预演.py",
    STOCK / "02脚本" / "生成单股证据核验191候选采用确认回执草案.py",
    STOCK / "02脚本" / "验证单股证据核验191候选采用确认回执草案.py",
    STOCK / "02脚本" / "生成单股证据核验确认回执状态面板.py",
    STOCK / "02脚本" / "验证单股证据核验确认回执状态面板.py",
    STOCK / "02脚本" / "生成单股证据核验回执后调度清单.py",
    STOCK / "02脚本" / "验证单股证据核验回执后调度清单.py",
    STOCK / "02脚本" / "生成单股证据核验确认回执填写样例副本.py",
    STOCK / "02脚本" / "验证单股证据核验确认回执填写样例副本.py",
    STOCK / "02脚本" / "生成单股证据核验确认后路径演练报告.py",
    STOCK / "02脚本" / "验证单股证据核验确认后路径演练报告.py",
    STOCK / "02脚本" / "生成单股证据核验正式回执待办卡.py",
    STOCK / "02脚本" / "验证单股证据核验正式回执待办卡.py",
    STOCK / "02脚本" / "生成单股证据核验正式回执填写前自检.py",
    STOCK / "02脚本" / "验证单股证据核验正式回执填写前自检.py",
    STOCK / "02脚本" / "生成单股证据核验正式回执录入后受控重跑预演.py",
    STOCK / "02脚本" / "验证单股证据核验正式回执录入后受控重跑预演.py",
    STOCK / "02脚本" / "生成单股证据核验191候选采用前闸口.py",
    STOCK / "02脚本" / "验证单股证据核验191候选采用前闸口.py",
    STOCK / "02脚本" / "生成单股证据核验191候选采用受控执行预案.py",
    STOCK / "02脚本" / "验证单股证据核验191候选采用受控执行预案.py",
    STOCK / "02脚本" / "生成单股证据核验191候选采用预览.py",
    STOCK / "02脚本" / "验证单股证据核验191候选采用预览.py",
    STOCK / "02脚本" / "生成单股证据核验受控写入命令草案.py",
    STOCK / "02脚本" / "验证单股证据核验受控写入命令草案.py",
    STOCK / "02脚本" / "生成单股证据核验191填写质量闸口.py",
    STOCK / "02脚本" / "验证单股证据核验191填写质量闸口.py",
    STOCK / "02脚本" / "同步单股证据核验CSV表单到台账.py",
    STOCK / "02脚本" / "生成单股证据核验台账同步预览.py",
    STOCK / "02脚本" / "验证单股证据核验台账同步预览.py",
    STOCK / "02脚本" / "生成单股证据核验模板同步执行闸口.py",
    STOCK / "02脚本" / "验证单股证据核验模板同步执行闸口.py",
    STOCK / "02脚本" / "执行单股证据核验191完成后预演检查.py",
    STOCK / "02脚本" / "验证单股证据核验191完成后预演检查.py",
]


def read_head(path: Path, lines: int = 55) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8-sig", errors="replace").splitlines()[:lines])
    except Exception as exc:
        return f"读取失败：{exc}"


def missing_fields(path: Path) -> list[str]:
    head = read_head(path)
    return [field.rstrip("：") for field in REQUIRED_FIELDS if field not in head]


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def audit_script(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"路径": str(path), "相对路径": rel(path), "存在": False, "通过": False, "缺失字段": REQUIRED_FIELDS}
    missing = missing_fields(path)
    return {
        "路径": str(path),
        "相对路径": rel(path),
        "存在": True,
        "通过": not missing,
        "缺失字段": missing,
    }


def scan_owned_scripts() -> list[Path]:
    paths: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if not is_excluded(path):
                paths.append(path)
    return sorted(set(paths), key=lambda item: str(item))


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 脚本标头规范审计",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 主线结论：{report['主线结论']}",
        f"- 主线脚本：{report['主线通过数量']} / {report['主线总数']} 通过",
        f"- 存量自有脚本：{report['存量通过数量']} / {report['存量扫描数量']} 已补齐八项标头",
        f"- 存量债务数量：{report['存量债务数量']}",
        "",
        "## 一、主线脚本",
        "",
    ]
    for item in report["主线脚本"]:
        status = "通过" if item["通过"] else "失败"
        missing = "、".join(item["缺失字段"]) if item["缺失字段"] else "无"
        lines.append(f"- {status}：{item['相对路径']}；缺失字段：{missing}")
    lines.extend([
        "",
        "## 二、存量债务说明",
        "",
        "存量债务用于后续分批治理，不阻断当前股票系统与四系统小闭环主线施工。第三方库、虚拟环境、缓存目录和归档副本已排除，避免把外部文件误判为自有脚本问题。",
        "",
        "### 债务样例（前50条）",
        "",
    ])
    for item in report["存量债务前50条"]:
        missing = "、".join(item["缺失字段"])
        lines.append(f"- {item['相对路径']}；缺失字段：{missing}")
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 只读脚本文件。",
        "- 不触发 n8n。",
        "- 不真实发送企业微信。",
        "- 不重启服务。",
        "- 不写正式业务库。",
        "- 不调用券商接口，不自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    mainline_results = [audit_script(path) for path in MAINLINE_SCRIPTS]
    owned_results = [audit_script(path) for path in scan_owned_scripts()]
    debt = [item for item in owned_results if item["存在"] and not item["通过"]]
    mainline_failed = [item for item in mainline_results if not item["通过"]]
    report: dict[str, Any] = {
        "名称": "脚本标头规范审计",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": str(MAINLINE_SCRIPTS[0]),
        "必备字段": [field.rstrip("：") for field in REQUIRED_FIELDS],
        "排除目录": sorted(EXCLUDED_PARTS),
        "主线结论": "通过：主线脚本已补齐八项标头" if not mainline_failed else "失败：主线脚本存在标头缺失",
        "主线总数": len(mainline_results),
        "主线通过数量": sum(1 for item in mainline_results if item["通过"]),
        "主线失败数量": len(mainline_failed),
        "主线脚本": mainline_results,
        "存量扫描数量": len(owned_results),
        "存量通过数量": sum(1 for item in owned_results if item["通过"]),
        "存量债务数量": len(debt),
        "存量债务前50条": debt[:50],
        "安全边界": {
            "触发n8n": False,
            "企业微信真实发送": False,
            "重启服务": False,
            "写正式业务库": False,
            "券商接口": False,
            "自动交易": False,
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(report, ensure_ascii=False, indent=2)
    markdown = build_markdown(report)
    (OUT_DIR / "脚本标头规范审计_最新.json").write_text(json_text, encoding="utf-8")
    (OUT_DIR / "脚本标头规范审计_最新.md").write_text(markdown, encoding="utf-8")
    print(json.dumps({
        "状态": report["主线结论"],
        "主线通过数量": report["主线通过数量"],
        "主线失败数量": report["主线失败数量"],
        "存量债务数量": report["存量债务数量"],
        "报告": str(OUT_DIR / "脚本标头规范审计_最新.md"),
    }, ensure_ascii=False))
    return 0 if not mainline_failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
