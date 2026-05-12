# -*- coding: utf-8 -*-
"""
名称：生成股票主动推送人工确认回执填写校验与闸口复跑包.py
作用：校验250人工确认回执是否填写完整，并复核252总闸口和253回滚演练状态。
触发方式：python 生成股票主动推送人工确认回执填写校验与闸口复跑包.py
依赖：Python标准库；250人工确认回执模板包；252最终只读总闸口；253日志台账与回滚演练包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地包并写入254校验包；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易；不写正式规则库。
创建/修改记录：2026-05-09 创建股票主动推送人工确认回执填写校验与闸口复跑包。
标识：stock-active-push-human-confirmation-fill-check-gate-rerun-generate
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


def present_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送人工确认回执填写校验与闸口复跑包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 总体状态：{report['总体状态']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 是否允许真实发送：{report['是否允许真实发送']}",
        f"- 是否允许n8n：{report['是否允许n8n']}",
        "",
        "## 回执字段校验",
        "",
    ]
    for item in report["回执字段校验"]:
        lines.append(f"- {item['字段']}：{item['通过']}，{item['说明']}")
    lines.extend(["", "## 闸口复核", ""])
    for item in report["闸口复核"]:
        lines.append(f"- {item['检查项']}：{item['通过']}，{item['说明']}")
    lines.extend(["", "## 当前阻断项", ""])
    for item in report["阻断项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    data = root / "03数据"
    receipt_path = data / "250主动推送真实灰度人工确认回执模板包" / "股票主动推送真实灰度人工确认回执模板包_最新.json"
    gate_path = data / "252主动推送真实灰度发送前最终只读总闸口" / "股票主动推送真实灰度发送前最终只读总闸口_最新.json"
    rollback_path = data / "253主动推送灰度发送日志台账与回滚演练包" / "股票主动推送灰度发送日志台账与回滚演练包_最新.json"

    receipt_doc = load_json(receipt_path)
    gate = load_json(gate_path)
    rollback = load_json(rollback_path)
    receipt = receipt_doc.get("确认回执模板", {})

    field_checks = [
        {"字段": "确认人", "通过": present_text(receipt.get("确认人")), "说明": receipt.get("确认人", "") or "未填写"},
        {"字段": "确认时间", "通过": present_text(receipt.get("确认时间")), "说明": receipt.get("确认时间", "") or "未填写"},
        {"字段": "目标用户", "通过": present_text(receipt.get("目标用户")), "说明": receipt.get("目标用户", "") or "未填写"},
        {"字段": "单人白名单确认", "通过": receipt.get("单人白名单确认") is True, "说明": receipt.get("单人白名单确认")},
        {"字段": "首轮消息条数", "通过": receipt.get("首轮消息条数") == 1, "说明": receipt.get("首轮消息条数")},
        {"字段": "频率确认", "通过": receipt.get("频率确认") is True, "说明": receipt.get("频率确认")},
        {"字段": "内容边界确认", "通过": receipt.get("内容边界确认") is True, "说明": receipt.get("内容边界确认")},
        {"字段": "熔断规则确认", "通过": receipt.get("熔断规则确认") is True, "说明": receipt.get("熔断规则确认")},
        {"字段": "回滚方式确认", "通过": receipt.get("回滚方式确认") is True, "说明": receipt.get("回滚方式确认")},
        {"字段": "是否允许真实发送", "通过": receipt.get("是否允许真实发送") is True, "说明": receipt.get("是否允许真实发送")},
    ]

    rerun_checks = [
        {"检查项": "250回执模板存在", "通过": receipt_path.exists(), "说明": str(receipt_path)},
        {"检查项": "252总闸口存在", "通过": gate_path.exists(), "说明": str(gate_path)},
        {"检查项": "253回滚演练存在", "通过": rollback_path.exists(), "说明": str(rollback_path)},
        {"检查项": "252当前仍保持blocked", "通过": gate.get("总体状态") == "blocked", "说明": gate.get("总体状态")},
        {"检查项": "253回滚演练通过", "通过": rollback.get("演练通过") is True, "说明": rollback.get("演练通过")},
        {"检查项": "250模板包未启用n8n", "通过": receipt_doc.get("是否启用n8n") is False and receipt_doc.get("是否触发n8n") is False, "说明": {"启用": receipt_doc.get("是否启用n8n"), "触发": receipt_doc.get("是否触发n8n")}},
        {"检查项": "250模板包未接券商交易", "通过": receipt_doc.get("是否接券商") is False and receipt_doc.get("是否交易") is False, "说明": {"券商": receipt_doc.get("是否接券商"), "交易": receipt_doc.get("是否交易")}},
    ]

    missing = [item["字段"] for item in field_checks if not item["通过"]]
    rerun_failed = [item["检查项"] for item in rerun_checks if not item["通过"]]
    all_ready = not missing and not rerun_failed

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "ready_for_manual_real_gray_review" if all_ready else "blocked",
        "当前结论": "人工确认回执尚未填写完整；当前不得进入真实灰度发送。" if not all_ready else "人工确认字段已填全，但仍需受控发送闸口另行放行后才可真实发送。",
        "是否允许真实发送": False,
        "是否允许n8n": False,
        "来源文件": {
            "250人工确认回执模板": str(receipt_path),
            "252最终只读总闸口": str(gate_path),
            "253日志台账与回滚演练": str(rollback_path),
        },
        "回执字段校验": field_checks,
        "闸口复核": rerun_checks,
        "阻断项": [f"回执字段未通过：{item}" for item in missing] + [f"闸口复核未通过：{item}" for item in rerun_failed],
        "建议下一步": [
            "保持blocked，不真实发送。",
            "如未来要进入单条真实灰度，先由人工填写250回执所有字段。",
            "填写后复跑254，再复跑252总闸口；仍不得启用n8n自动推送。",
        ],
        "实际动作": {
            "读取250人工确认回执": True,
            "读取252总闸口": True,
            "读取253回滚演练": True,
            "写本地254校验包": True,
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

    out_dir = data / "254主动推送人工确认回执填写校验与闸口复跑包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"股票主动推送人工确认回执填写校验与闸口复跑包_{stamp}.json"
    latest_json = out_dir / "股票主动推送人工确认回执填写校验与闸口复跑包_最新.json"
    output_md = out_dir / f"股票主动推送人工确认回执填写校验与闸口复跑包_{stamp}.md"
    latest_md = out_dir / "股票主动推送人工确认回执填写校验与闸口复跑包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": report["总体状态"], "阻断项": len(report["阻断项"]), "允许真实发送": False, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
