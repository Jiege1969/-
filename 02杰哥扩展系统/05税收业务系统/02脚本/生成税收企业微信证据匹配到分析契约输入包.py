# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信证据匹配到分析契约输入包.py
作用：把企业微信输入队列证据匹配影子任务整理为涉税业务分析契约草案输入包。
安全边界：只读本地影子流转和分析契约；不联网、不读取凭据、不调用模型、不写正式业务库、不生成正式税务结论。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统\02杰哥扩展系统\05税收业务系统")
RULE = ROOT / "01配置" / "税收企业微信证据匹配到分析契约输入包规则.json"
SHADOW_FLOW = ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信输入队列证据匹配影子流转_最新.json"
CONTRACT = ROOT / "01配置" / "涉税业务分析契约.json"
OUT_DIR = ROOT / "03数据" / "32税收企业微信正式入口"
PACKAGE_DIR = OUT_DIR / "分析契约输入包"
OUT_JSON = OUT_DIR / "税收企业微信证据匹配到分析契约输入包_最新.json"
OUT_MD = OUT_DIR / "税收企业微信证据匹配到分析契约输入包_最新.md"


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


def build_package(task: dict[str, Any], rule: dict[str, Any], index: int) -> dict[str, Any]:
    shadow_status = task.get("影子流转状态")
    text = task.get("脱敏文本", "")
    if has_unmasked_sensitive(text):
        package_status = "blocked_sensitive_unmasked"
    elif shadow_status == "pending_fact_completion":
        package_status = "pending_fact_completion"
    else:
        package_status = "pending_review_input"
    confidence = rule.get("置信度规则", {}).get(shadow_status, "low")
    fact_gaps = list(dict.fromkeys(as_list(task.get("待补充事实"))))
    review_materials = list(dict.fromkeys(as_list(task.get("待复核资料清单"))))
    review_items = list(dict.fromkeys(as_list(task.get("待人工复核项")) + [
        "人工确认该输入包只作为待复核分析草案输入",
        "人工确认政策证据有效状态后才能进入当前适用依据候选",
    ]))
    return {
        "输入包ID": f"tax-wecom-analysis-input-{index:03d}",
        "来源流转ID": task.get("流转ID"),
        "消息ID": task.get("消息ID"),
        "来源机器人": task.get("来源机器人"),
        "输入包状态": package_status,
        "业务事项": task.get("业务事项猜测", "涉税业务分析"),
        "适用税种": as_list(task.get("适用税种猜测")) or ["待识别"],
        "政策依据候选主题": as_list(task.get("候选证据主题")) or ["待政策证据底座匹配"],
        "依据层级": as_list(task.get("依据层级要求")),
        "依据层级明细": as_list(task.get("依据层级明细")),
        "业务事实摘要": text,
        "待复核资料清单": review_materials,
        "待复核说明": task.get("待复核说明", ""),
        "资料缺口": fact_gaps,
        "风险点": rule.get("默认风险点", []),
        "置信度": confidence,
        "人工复核项": review_items,
        "禁止动作": rule.get("禁止动作", []),
        "下一步建议": "进入涉税业务分析契约草案生成前的待复核输入区；只能生成待复核分析草案，不得生成正式税务结论。",
        "是否写正式业务库": False,
        "是否生成正式税务结论": False,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    rule = load_json(RULE)
    shadow = load_json(SHADOW_FLOW)
    contract = load_json(CONTRACT)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allowed = set(rule.get("允许影子流转状态", []))
    tasks = as_list(shadow.get("影子任务"))
    packages = [build_package(task, rule, index + 1) for index, task in enumerate(tasks) if task.get("影子流转状态") in allowed]
    blocked = [
        {
            "流转ID": task.get("流转ID"),
            "消息ID": task.get("消息ID"),
            "影子流转状态": task.get("影子流转状态"),
            "阻断原因": "影子流转状态不允许进入分析契约输入包",
            "是否写正式业务库": False,
            "是否生成正式税务结论": False,
        }
        for task in tasks
        if task.get("影子流转状态") not in allowed
    ]
    package_file = PACKAGE_DIR / "税收企业微信证据匹配到分析契约输入包_预演.json"
    package_file.write_text(json.dumps(packages, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "名称": "税收企业微信证据匹配到分析契约输入包",
        "生成时间": now,
        "规则来源": str(RULE),
        "影子流转来源": str(SHADOW_FLOW),
        "输入包文件": str(package_file),
        "运行状态": rule.get("运行状态"),
        "影子任务数量": len(tasks),
        "输入包数量": len(packages),
        "阻断数量": len(blocked),
        "输入包": packages,
        "阻断留痕": blocked,
        "分析契约摘要": {
            "分析契约存在": CONTRACT.exists(),
            "分析契约名称": contract.get("名称", "未读取到"),
            "禁止状态词": contract.get("禁用状态词", []),
        },
        "安全边界": rule.get("安全边界", {}),
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信证据匹配到分析契约输入包",
        "",
        f"- 生成时间：{now}",
        f"- 运行状态：{report['运行状态']}",
        f"- 影子任务数量：{report['影子任务数量']}",
        f"- 输入包数量：{report['输入包数量']}",
        f"- 阻断数量：{report['阻断数量']}",
        "",
        "## 输入包",
        "",
    ]
    for item in packages:
        lines.append(f"- {item['输入包ID']}：消息={item['消息ID']}，状态={item['输入包状态']}，事项={item['业务事项']}，置信度={item['置信度']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": "完成", "输入包数量": len(packages), "阻断数量": len(blocked), "输出": str(OUT_MD)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
