# -*- coding: utf-8 -*-
"""
名称：执行宪法级血脉方法论只读检查.py
作用：兼容旧文件名，按当前“底层逻辑”口径检查系统底层逻辑、规则层级、现象本质规律、归纳实践反馈闭环是否已经进入规则库、面板和接续包。
安全边界：只读规则库、面板和接续包；只在总管03数据运行状态输出检查回执；不触发n8n、不发送企业微信、不写正式库、不重启服务。
标识：constitutional-bloodline-methodology-readonly-check
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\杰哥智能化系统")
RULE_DIR = ROOT / "03杰哥进化系统" / "规则库"
MANAGER_DIR = ROOT / "00杰哥系统总管"
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
OUT_JSON = OUT_DIR / "宪法级血脉方法论只读检查_最新.json"
OUT_MD = OUT_DIR / "宪法级血脉方法论只读检查_最新.md"
PANEL = ROOT / "00杰哥系统总管" / "07文档" / "当前施工面板.md"
CONTINUATION = ROOT / "00杰哥系统总管" / "03数据" / "开工上下文" / "一键接续施工包_最新.md"

REQUIRED_RULES = [
    ("系统底层逻辑", MANAGER_DIR / "系统底层逻辑.md"),
    ("归纳总结提炼规则实践反馈闭环", RULE_DIR / "归纳总结提炼规则实践反馈闭环_20260509.md"),
    ("透过现象看本质通过问题看规律", RULE_DIR / "透过现象看本质通过问题看规律_20260509.md"),
    ("规则层级与反向服务链", RULE_DIR / "规则层级与反向服务链_20260509.md"),
    ("稳定版上位目标与自然日样本关系校准", RULE_DIR / "稳定版上位目标与自然日样本关系校准_20260509.md"),
    ("高层方法论轻量落地与防过度治理", RULE_DIR / "高层方法论轻量落地与防过度治理_20260509.md"),
]

REQUIRED_PHRASES = {
    "系统底层逻辑": ["用户主权", "事实优先", "可追溯", "受控真实动作", "实践检验"],
    "归纳总结提炼规则实践反馈闭环": ["实践/问题/反馈", "归纳", "总结", "提炼", "规则", "再实践"],
    "透过现象看本质通过问题看规律": ["现象", "本质", "规律", "机制", "能力"],
    "规则层级与反向服务链": ["红线规则", "稳定版判断规则", "冷启动复验规则", "自然日样本规则"],
    "稳定版上位目标与自然日样本关系校准": ["稳定事实", "日期", "三自然日"],
    "高层方法论轻量落地与防过度治理": ["轻量处理", "标准处理", "宪法级处理", "防过度治理"],
}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def check_rule(name: str, path: Path) -> dict:
    text = read_text(path)
    phrases = REQUIRED_PHRASES[name]
    missing = [phrase for phrase in phrases if phrase not in text]
    return {
        "名称": name,
        "路径": str(path),
        "存在": path.exists(),
        "关键短语缺失": missing,
        "通过": path.exists() and not missing,
    }


def contains_all(path: Path, phrases: list[str]) -> dict:
    text = read_text(path)
    missing = [phrase for phrase in phrases if phrase not in text]
    return {
        "路径": str(path),
        "存在": path.exists(),
        "关键短语缺失": missing,
        "通过": path.exists() and not missing,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rule_checks = [check_rule(name, path) for name, path in REQUIRED_RULES]
    panel_check = contains_all(PANEL, ["系统底层逻辑", "归纳总结提炼", "透过现象看本质", "规则层级", "防过度治理"])
    continuation_check = contains_all(CONTINUATION, ["系统底层逻辑", "规则进化闭环", "认知工作法", "规则层级", "防过度治理"])
    passed = all(item["通过"] for item in rule_checks) and panel_check["通过"] and continuation_check["通过"]

    report = {
        "名称": "底层逻辑血脉方法论只读检查",
        "生成时间": datetime.now().isoformat(timespec="seconds"),
        "总体状态": "pass" if passed else "needs_attention",
        "规则库检查": rule_checks,
        "面板检查": panel_check,
        "接续包检查": continuation_check,
        "能力要求": [
            "系统遇到问题时按现象-本质-规律-机制-能力处理",
            "系统运行按实践/问题/反馈-归纳-总结-提炼-规则-再实践闭环演化",
            "下位规则不得压过上位目标",
            "当前最高入口为系统底层逻辑.md，旧“宪法级”命名材料仅作历史先例",
            "高层方法论轻量落地，按轻量/标准/宪法级三档处理，防止过度治理",
        ],
        "安全边界": {
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "重启服务": False,
            "交易": False,
            "办税": False,
            "发布视频": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 底层逻辑血脉方法论只读检查",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 总体状态：`{report['总体状态']}`",
        "",
        "## 规则库检查",
        "",
    ]
    for item in rule_checks:
        lines.append(f"- {item['名称']}：通过={item['通过']}，缺失={item['关键短语缺失']}")
    lines.extend([
        "",
        "## 面板与接续包",
        "",
        f"- 面板：通过={panel_check['通过']}，缺失={panel_check['关键短语缺失']}",
        f"- 接续包：通过={continuation_check['通过']}，缺失={continuation_check['关键短语缺失']}",
        "",
        "## 能力要求",
        "",
    ])
    lines.extend([f"- {item}" for item in report["能力要求"]])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"总体状态": report["总体状态"], "输出": [str(OUT_JSON), str(OUT_MD)]}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
