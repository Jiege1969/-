# -*- coding: utf-8 -*-
"""
名称：生成股票主动推送真实灰度人工确认回执模板包.py
作用：读取248主动推送白名单频率熔断规则包，生成250真实灰度人工确认回执模板包。
触发方式：python 生成股票主动推送真实灰度人工确认回执模板包.py
依赖：Python标准库；248主动推送白名单频率熔断规则包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写本地250模板包；不调用企业微信API；不真实发送；不启用或触发n8n；不接券商；不交易；不登录税局；不写正式规则；不重载19310/19302；不改总管面板；不改一键接续包。
创建/修改记录：2026-05-09 创建股票主动推送真实灰度人工确认回执模板包。
标识：stock-active-push-real-gray-human-confirmation-receipt-template-package-generate
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


PACKAGE_NAME = "股票主动推送真实灰度人工确认回执模板包"
TEMPLATE_STATUS = "待人工确认，未生效"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def file_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_receipt_template(source_rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "确认人": "",
        "确认时间": "",
        "目标用户": "",
        "单人白名单确认": False,
        "首轮消息条数": 1,
        "频率确认": False,
        "内容边界确认": False,
        "熔断规则确认": False,
        "回滚方式确认": False,
        "是否允许真实发送": False,
        "模板填写说明": {
            "状态要求": TEMPLATE_STATUS,
            "目标用户要求": "仅允许人工填写单人白名单目标，不允许群发、部门群发、客户群发。",
            "频率来源": source_rule.get("频率规则草案", {}),
            "内容边界来源": source_rule.get("内容边界", {}),
            "熔断规则来源": source_rule.get("熔断规则", []),
            "回滚方式": "保持本地模板待确认状态；如任一确认项不通过，继续阻断真实发送并保留04日志验收记录。",
            "真实发送许可声明": "本模板默认不写入、不给予、不得推断任何真实发送许可。",
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    template = report["确认回执模板"]
    lines = [
        "# 股票主动推送真实灰度人工确认回执模板包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 模板状态：{report['模板状态']}",
        f"- 是否允许真实发送：{report['是否允许真实发送']}",
        f"- 是否启用n8n：{report['是否启用n8n']}",
        f"- 是否接券商：{report['是否接券商']}",
        f"- 是否交易：{report['是否交易']}",
        "",
        "## 确认回执模板字段",
        "",
    ]
    for key in [
        "确认人",
        "确认时间",
        "目标用户",
        "单人白名单确认",
        "首轮消息条数",
        "频率确认",
        "内容边界确认",
        "熔断规则确认",
        "回滚方式确认",
        "是否允许真实发送",
    ]:
        lines.append(f"- {key}：{template.get(key)}")
    lines.extend(["", "## 来源规则包", ""])
    for key, value in report["来源规则包"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    source_path = root / "03数据" / "248主动推送白名单频率熔断规则包" / "股票主动推送白名单频率熔断规则包_最新.json"
    source_rule = load_json(source_path)
    source_actions = source_rule.get("实际动作", {})
    source_safe = (
        source_path.exists()
        and source_rule.get("是否允许真实发送") is False
        and source_rule.get("是否允许n8n自动推送") is False
        and source_actions.get("调用券商接口") is False
        and source_actions.get("自动交易") is False
        and source_actions.get("写正式规则库") is False
    )

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "包名": PACKAGE_NAME,
        "模板状态": TEMPLATE_STATUS,
        "当前结论": "已生成真实灰度人工确认回执模板；模板待人工确认且未生效，不构成真实发送许可。",
        "是否允许真实发送": False,
        "是否启用n8n": False,
        "是否触发n8n": False,
        "是否接券商": False,
        "是否交易": False,
        "是否写正式规则": False,
        "来源规则包": {
            "路径": str(source_path),
            "存在": source_path.exists(),
            "sha256": file_sha256(source_path),
            "来源状态": source_rule.get("当前状态", ""),
            "来源安全边界通过": source_safe,
        },
        "确认回执模板": build_receipt_template(source_rule),
        "人工确认生效前置": [
            "确认人、确认时间、目标用户必须由人工填写。",
            "单人白名单、频率、内容边界、熔断规则、回滚方式均必须人工确认。",
            "是否允许真实发送默认且保持为false；本模板包不写入真实发送许可。",
            "任何n8n、券商、交易、正式规则、服务重载动作均不在本包执行。",
        ],
        "实际动作": {
            "读取248规则包": source_path.exists(),
            "写本地250模板包": True,
            "调用企业微信API": False,
            "真实发送企业微信": False,
            "启用n8n": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "登录税局": False,
            "写正式规则库": False,
            "重载19310": False,
            "重载19302": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }

    out_dir = root / "03数据" / "250主动推送真实灰度人工确认回执模板包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"股票主动推送真实灰度人工确认回执模板包_{stamp}.json"
    latest_json = out_dir / "股票主动推送真实灰度人工确认回执模板包_最新.json"
    output_md = out_dir / f"股票主动推送真实灰度人工确认回执模板包_{stamp}.md"
    latest_md = out_dir / "股票主动推送真实灰度人工确认回执模板包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": "wait_human_confirmation", "模板状态": TEMPLATE_STATUS, "是否允许真实发送": False, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
