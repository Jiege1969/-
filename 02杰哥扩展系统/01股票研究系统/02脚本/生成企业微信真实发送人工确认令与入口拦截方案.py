# -*- coding: utf-8 -*-
"""
名称：生成企业微信真实发送人工确认令与入口拦截方案.py
作用：记录公共企业微信受控发送器新增的真实发送人工确认令拦截，并生成不可直接使用的确认令模板和审计方案。
安全边界：只读公共发送器源码和236准入包；只写03数据/237确认令拦截方案；不创建有效确认令、不调用发送器、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "03数据"
COMMON_ROOT = ROOT.parents[0] / "00公共组件"
SENDER = COMMON_ROOT / "02脚本" / "企业微信受控发送器.py"
DEFAULT_CONFIRMATION_FILE = COMMON_ROOT / "01配置" / "企业微信真实发送人工确认令.json"
OUT_DIR = DATA / "237企业微信真实发送人工确认令与入口拦截"
PLAN_236 = DATA / "236企业微信真实发送灰度准入与停止开关方案" / "企业微信真实发送灰度准入与停止开关方案_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 企业微信真实发送人工确认令与入口拦截方案",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 一、入口拦截",
        "",
    ]
    for item in report["入口拦截"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 二、确认令字段", ""])
    for key, value in report["确认令模板_不可直接使用"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 三、安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    sender_text = read_text(SENDER)
    plan_236 = load_json(PLAN_236)
    template = {
        "确认状态": "待人工确认",
        "允许真实发送": False,
        "有效日期": now.strftime("%Y-%m-%d"),
        "确认令": f"请人工改为 ALLOW_WECOM_REAL_SEND_{now.strftime('%Y%m%d')}",
        "允许接收人": ["ChenXiaoJie"],
        "允许消息类型": ["text", "markdown"],
        "允许n8n": False,
        "允许自动交易": False,
        "确认说明": "这是不可直接使用的模板。只有人工确认后，才允许复制到公共配置目录默认确认令路径，并把确认状态、允许真实发送和确认令改为有效值。",
    }
    report = {
        "名称": "企业微信真实发送人工确认令与入口拦截方案",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": "公共受控发送器已新增真实发送人工确认令拦截；未创建有效确认令，真实发送继续默认阻断。",
        "依赖236": {
            "路径": str(PLAN_236),
            "存在": PLAN_236.exists(),
            "允许真实发送": plan_236.get("允许真实发送"),
            "允许n8n启用": plan_236.get("允许n8n启用"),
        },
        "公共发送器快照": {
            "路径": str(SENDER),
            "存在": SENDER.exists(),
            "sha256": sha256(SENDER),
            "已包含确认令校验": "validate_real_send_confirmation" in sender_text and "真实发送人工确认令有效" in sender_text,
            "支持显式确认令路径": "--confirmation-file" in sender_text,
        },
        "默认确认令路径": str(DEFAULT_CONFIRMATION_FILE),
        "默认确认令当前存在": DEFAULT_CONFIRMATION_FILE.exists(),
        "确认令模板_不可直接使用": template,
        "入口拦截": [
            "公共受控发送器在 `--real-send` 模式下必须通过当日人工确认令校验。",
            "缺少确认令、确认令非当日、确认状态不是已人工确认、接收人不匹配、消息类型不匹配、允许n8n或允许自动交易不为 false 时，均在本地阻断。",
            "dry-run 模式不需要确认令，避免影响普通本地检查。",
            "确认令默认路径位于公共组件配置目录；本步骤只生成不可直接使用的模板，不写入默认确认令路径。",
        ],
        "实际动作": {
            "创建有效确认令": False,
            "调用公共受控发送器": False,
            "调用企业微信token接口": False,
            "尝试发送企业微信": False,
            "触发n8n": False,
            "重启服务": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "企业微信真实发送人工确认令与入口拦截方案_最新.json"
    latest_md = OUT_DIR / "企业微信真实发送人工确认令与入口拦截方案_最新.md"
    template_json = OUT_DIR / "企业微信真实发送人工确认令_模板_不可直接使用.json"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    write_json(template_json, template)
    print(json.dumps({
        "状态": "完成",
        "默认确认令当前存在": DEFAULT_CONFIRMATION_FILE.exists(),
        "创建有效确认令": False,
        "输出": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
