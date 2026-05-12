# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信分析契约输入包到待复核草案骨架.py
作用：把企业微信分析契约输入包整理为待复核分析草案骨架。
安全边界：只读本地输入包和分析契约；不联网、不读取凭据、不调用模型、不写正式业务库、不生成正式税务结论。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收企业微信分析契约输入包到待复核草案骨架规则.json"
INPUT_PACKAGE = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信证据匹配到分析契约输入包_最新.json"
CONTRACT = ROOT / "01配置" / "涉税业务分析契约.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
DRAFT_DIR = OUT_DIR / "待复核分析草案骨架"
OUT_JSON = OUT_DIR / "税收企业微信分析契约输入包到待复核草案骨架_最新.json"
OUT_MD = OUT_DIR / "税收企业微信分析契约输入包到待复核草案骨架_最新.md"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def has_unmasked_sensitive(text: str) -> bool:
    patterns = [
        r"(?<!\d)1[3-9]\d{9}(?!\d)",
        r"(?<![0-9A-Za-z])\d{17}[\dXx](?![0-9A-Za-z])",
        r"https://qyapi\.weixin\.qq\.com/cgi-bin/webhook/send\?key=",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def build_draft(package: dict[str, Any], rule: dict[str, Any], index: int) -> dict[str, Any]:
    fact_text = package.get("业务事实摘要", "")
    status = "pending_review"
    if package.get("输入包状态") == "pending_fact_completion":
        status = "draft"
    if has_unmasked_sensitive(fact_text):
        status = "draft"
    policy_topics = as_list(package.get("政策依据候选主题"))
    review_items = list(dict.fromkeys(as_list(package.get("人工复核项")) + [
        "人工确认候选政策依据是否存在全文有效或已人工确认有效资料",
        "人工确认业务事实和资料缺口是否足以进入下一步待复核分析草案",
        "人工确认不得将本骨架作为正式税务意见或对外结论",
    ]))
    return {
        "草案ID": f"tax-wecom-review-draft-skeleton-{index:03d}",
        "来源输入包ID": package.get("输入包ID"),
        "消息ID": package.get("消息ID"),
        "契约状态": status,
        "业务事项": package.get("业务事项", "涉税业务分析"),
        "业务事实": {
            "摘要": fact_text,
            "待补充事实": as_list(package.get("资料缺口")),
            "来源机器人": package.get("来源机器人"),
        },
        "政策依据": {
            "依据状态": rule.get("政策依据骨架规则", {}).get("依据状态"),
            "候选主题": policy_topics,
            "说明": rule.get("政策依据骨架规则", {}).get("说明"),
        },
        "依据层级": as_list(package.get("依据层级")),
        "依据层级明细": as_list(package.get("依据层级明细")),
        "适用条件": rule.get("适用条件骨架", []),
        "待复核资料清单": as_list(package.get("待复核资料清单")),
        "待复核说明": package.get("待复核说明", ""),
        "资料缺口": as_list(package.get("资料缺口")),
        "风险点": as_list(package.get("风险点")),
        "置信度": package.get("置信度", "low"),
        "人工复核项": review_items,
        "输出边界": rule.get("输出边界", []),
        "禁止动作": rule.get("禁止动作", []),
        "是否写正式业务库": False,
        "是否调用模型推理": False,
        "是否生成正式税务结论": False,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE)
    package_report = load_json(INPUT_PACKAGE)
    contract = load_json(CONTRACT)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allowed = set(rule.get("允许输入包状态", []))
    packages = as_list(package_report.get("输入包"))
    drafts = [
        build_draft(package, rule, index + 1)
        for index, package in enumerate(packages)
        if package.get("输入包状态") in allowed
    ]
    blocked = [
        {
            "输入包ID": package.get("输入包ID"),
            "消息ID": package.get("消息ID"),
            "输入包状态": package.get("输入包状态"),
            "阻断原因": "输入包状态不允许进入待复核草案骨架",
            "是否写正式业务库": False,
            "是否生成正式税务结论": False,
        }
        for package in packages
        if package.get("输入包状态") not in allowed
    ]
    draft_file = DRAFT_DIR / "税收企业微信分析契约输入包到待复核草案骨架_预演.json"
    draft_file.write_text(json.dumps(drafts, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "名称": "税收企业微信分析契约输入包到待复核草案骨架",
        "生成时间": now,
        "规则来源": str(RULE),
        "输入包来源": str(INPUT_PACKAGE),
        "草案骨架文件": str(draft_file),
        "运行状态": rule.get("运行状态"),
        "输入包数量": len(packages),
        "草案骨架数量": len(drafts),
        "阻断数量": len(blocked),
        "草案骨架": drafts,
        "阻断留痕": blocked,
        "分析契约摘要": {
            "分析契约存在": CONTRACT.exists(),
            "分析契约名称": contract.get("名称", "未读取到"),
            "状态词": contract.get("状态词", []),
            "禁用状态词": contract.get("禁用状态词", []),
        },
        "安全边界": rule.get("安全边界", {}),
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信分析契约输入包到待复核草案骨架",
        "",
        f"- 生成时间：{now}",
        f"- 运行状态：{report['运行状态']}",
        f"- 输入包数量：{report['输入包数量']}",
        f"- 草案骨架数量：{report['草案骨架数量']}",
        f"- 阻断数量：{report['阻断数量']}",
        "",
        "## 草案骨架",
        "",
    ]
    for item in drafts:
        lines.append(f"- {item['草案ID']}：消息={item['消息ID']}，契约状态={item['契约状态']}，事项={item['业务事项']}，置信度={item['置信度']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "草案骨架数量": len(drafts), "阻断数量": len(blocked), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
