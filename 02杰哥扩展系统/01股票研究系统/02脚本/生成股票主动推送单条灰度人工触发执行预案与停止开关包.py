# -*- coding: utf-8 -*-
"""
名称：生成股票主动推送单条灰度人工触发执行预案与停止开关包.py
作用：生成股票主动推送单条真实灰度人工触发前的执行预案和停止开关演练包。
触发方式：python 生成股票主动推送单条灰度人工触发执行预案与停止开关包.py
依赖：Python标准库；252最终只读总闸口；253日志台账与回滚演练；254人工确认回执填写校验。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写本地255预案包；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易；不写正式规则库。
创建/修改记录：2026-05-09 创建股票主动推送单条灰度人工触发执行预案与停止开关包。
标识：stock-active-push-single-gray-manual-trigger-stop-switch-plan-generate
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送单条灰度人工触发执行预案与停止开关包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 当前状态：{report['当前状态']}",
        f"- 预案是否允许执行：{report['预案是否允许执行']}",
        f"- 是否真实发送：{report['是否真实发送']}",
        f"- 是否启用n8n：{report['是否启用n8n']}",
        "",
        "## 人工触发前置条件",
        "",
    ]
    for item in report["人工触发前置条件"]:
        lines.append(f"- {item['条件']}：{item['状态']}")
    lines.extend(["", "## 停止开关", ""])
    for item in report["停止开关"]:
        lines.append(f"- {item['开关']}：{item['触发后动作']}")
    lines.extend(["", "## 执行预案", ""])
    for item in report["执行预案"]:
        lines.append(f"{item['顺序']}. {item['动作']}：{item['当前结果']}")
    lines.extend(["", "## 当前阻断项", ""])
    for item in report["当前阻断项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    data = root / "03数据"
    gate_path = data / "252主动推送真实灰度发送前最终只读总闸口" / "股票主动推送真实灰度发送前最终只读总闸口_最新.json"
    rollback_path = data / "253主动推送灰度发送日志台账与回滚演练包" / "股票主动推送灰度发送日志台账与回滚演练包_最新.json"
    confirm_path = data / "254主动推送人工确认回执填写校验与闸口复跑包" / "股票主动推送人工确认回执填写校验与闸口复跑包_最新.json"

    gate = load_json(gate_path)
    rollback = load_json(rollback_path)
    confirm = load_json(confirm_path)

    prereqs = [
        {"条件": "252总闸口存在", "状态": "pass" if gate_path.exists() else "blocked"},
        {"条件": "252总闸口允许真实发送", "状态": "pass" if gate.get("是否允许真实发送") is True else "blocked"},
        {"条件": "253回滚演练通过", "状态": "pass" if rollback.get("演练通过") is True else "blocked"},
        {"条件": "254人工确认回执校验通过", "状态": "pass" if confirm.get("总体状态") == "ready_for_manual_real_gray_review" else "blocked"},
        {"条件": "n8n保持关闭", "状态": "pass" if gate.get("是否允许n8n自动推送") is False and confirm.get("是否允许n8n") is False else "blocked"},
        {"条件": "券商交易保持关闭", "状态": "pass"},
    ]

    stop_switches = [
        {"开关": "人工撤回确认", "触发后动作": "立即停止本轮发送候选，保持本地blocked。"},
        {"开关": "受控发送闸口未放行", "触发后动作": "不调用企业微信API，不生成msgid。"},
        {"开关": "命中交易化表达", "触发后动作": "阻断发送，写本地失败记录，转人工复核。"},
        {"开关": "重复发送命中", "触发后动作": "拦截重复，不进入发送候选。"},
        {"开关": "目标用户不是单人白名单", "触发后动作": "阻断群发风险。"},
        {"开关": "n8n或Webhook被启用", "触发后动作": "阻断自动化，要求恢复未激活/dry-run。"},
        {"开关": "券商、交易、下单相关动作出现", "触发后动作": "登记高风险事件并停止。"},
    ]

    blocked = any(item["状态"] != "pass" for item in prereqs)
    execution_plan = [
        {"顺序": 1, "动作": "复读252总闸口", "当前结果": "blocked，真实发送未放行"},
        {"顺序": 2, "动作": "复读254人工确认", "当前结果": "blocked，确认字段未填全"},
        {"顺序": 3, "动作": "复读253回滚台账", "当前结果": "pass，可记录失败和回滚"},
        {"顺序": 4, "动作": "执行单条发送前内容扫描", "当前结果": "仅预案，不执行真实发送"},
        {"顺序": 5, "动作": "执行单条灰度发送", "当前结果": "拒绝执行"},
        {"顺序": 6, "动作": "写入本地停止记录", "当前结果": "记录为未发送，无需撤回"},
    ]

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源文件": {
            "252总闸口": str(gate_path),
            "253日志台账与回滚演练": str(rollback_path),
            "254人工确认回执校验": str(confirm_path),
        },
        "当前状态": "blocked，人工确认和真实发送闸口未放行，单条灰度人工触发预案不得执行。",
        "预案是否允许执行": False,
        "是否真实发送": False,
        "是否启用n8n": False,
        "是否触发n8n": False,
        "是否接券商": False,
        "是否交易": False,
        "人工触发前置条件": prereqs,
        "停止开关": stop_switches,
        "执行预案": execution_plan,
        "当前阻断项": [
            item["条件"] for item in prereqs if item["状态"] != "pass"
        ],
        "样例停止记录": {
            "批次ID": "STOCK-PUSH-MANUAL-GRAY-PLAN-DRYRUN-001",
            "停止原因": "人工确认回执未完成或总闸口未放行",
            "真实发送": False,
            "企业微信msgid": "",
            "是否需要撤回": False,
            "处理结论": "未发送，无需撤回；保持blocked。",
        },
        "实际动作": {
            "读取252总闸口": True,
            "读取253回滚演练": True,
            "读取254人工确认校验": True,
            "写本地255预案包": True,
            "调用企业微信API": False,
            "真实发送企业微信": False,
            "启用n8n": False,
            "触发n8n": False,
            "重载19310": False,
            "重载19302": False,
            "调用券商接口": False,
            "自动交易": False,
            "写正式规则库": False,
            "修改总管面板": False,
            "修改一键接续包": False,
        },
    }

    out_dir = data / "255主动推送单条灰度人工触发执行预案与停止开关包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"股票主动推送单条灰度人工触发执行预案与停止开关包_{stamp}.json"
    latest_json = out_dir / "股票主动推送单条灰度人工触发执行预案与停止开关包_最新.json"
    output_md = out_dir / f"股票主动推送单条灰度人工触发执行预案与停止开关包_{stamp}.md"
    latest_md = out_dir / "股票主动推送单条灰度人工触发执行预案与停止开关包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": "blocked" if blocked else "ready", "允许执行": False, "真实发送": False, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
