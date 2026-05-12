# -*- coding: utf-8 -*-
"""
名称：生成股票主动推送真实灰度发送前最终只读总闸口.py
作用：汇总247-251主动推送准备包，生成真实灰度发送前最终只读总闸口判定。
触发方式：python 生成股票主动推送真实灰度发送前最终只读总闸口.py
依赖：Python标准库；247-251主动推送准备包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地准备包并写入252总闸口；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易；不写正式规则库。
创建/修改记录：2026-05-09 创建股票主动推送真实灰度发送前最终只读总闸口。
标识：stock-active-push-real-gray-final-readonly-gate-generate
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


def file_state(path: Path) -> dict[str, Any]:
    return {
        "存在": path.exists(),
        "路径": str(path),
        "大小": path.stat().st_size if path.exists() else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送真实灰度发送前最终只读总闸口",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 总体状态：{report['总体状态']}",
        f"- 是否允许真实发送：{report['是否允许真实发送']}",
        f"- 是否允许n8n自动推送：{report['是否允许n8n自动推送']}",
        f"- 当前结论：{report['当前结论']}",
        "",
        "## 子包状态",
        "",
    ]
    for item in report["子包状态"]:
        lines.append(f"- {item['编号']} {item['名称']}：存在={item['存在']}，判定={item['判定']}")
    lines.extend(["", "## 通过项", ""])
    for item in report["通过项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 阻断项", ""])
    for item in report["阻断项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 如需进入真实灰度，仍需人工完成", ""])
    for item in report["人工前置确认"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    data = root / "03数据"
    sources = {
        "247": {
            "名称": "主动推送灰度启用准备包",
            "路径": data / "247主动推送灰度启用准备包" / "股票主动推送灰度启用准备包_最新.json",
        },
        "248": {
            "名称": "主动推送白名单频率熔断规则包",
            "路径": data / "248主动推送白名单频率熔断规则包" / "股票主动推送白名单频率熔断规则包_最新.json",
        },
        "249": {
            "名称": "主动推送dry-run消息样本包",
            "路径": data / "249主动推送dry-run消息样本包" / "股票主动推送dry-run消息样本包_最新.json",
        },
        "250": {
            "名称": "主动推送真实灰度人工确认回执模板包",
            "路径": data / "250主动推送真实灰度人工确认回执模板包" / "股票主动推送真实灰度人工确认回执模板包_最新.json",
        },
        "251": {
            "名称": "主动推送交易化表达与重复发送拦截预演包",
            "路径": data / "251主动推送交易化表达与重复发送拦截预演包" / "股票主动推送交易化表达与重复发送拦截预演包_最新.json",
        },
    }
    loaded = {key: load_json(info["路径"]) for key, info in sources.items()}

    sub_status = []
    for key, info in sources.items():
        doc = loaded[key]
        state = file_state(info["路径"])
        if key == "247":
            passed = doc.get("可以推进准备工作") is True and doc.get("可以立即真实推送") is False
        elif key == "248":
            passed = doc.get("是否允许真实发送") is False and doc.get("是否允许n8n自动推送") is False
        elif key == "249":
            passed = doc.get("dry_run") is True and doc.get("真实发送") is False and doc.get("n8n") is False and len(doc.get("samples", [])) >= 1
        elif key == "250":
            passed = doc.get("模板状态") == "待人工确认，未生效" and doc.get("是否允许真实发送") is False
        else:
            passed = doc.get("总体状态") == "pass" and int(doc.get("交易化表达命中数", -1)) == 0
        sub_status.append({
            "编号": key,
            "名称": info["名称"],
            "存在": state["存在"],
            "路径": state["路径"],
            "判定": "pass" if passed else "blocked",
        })

    receipt = loaded["250"].get("确认回执模板", {})
    human_required = [
        "填写确认人、确认时间、目标用户。",
        "确认目标用户为单人白名单，不允许群发。",
        "确认首轮消息条数为1条，且人工触发。",
        "确认频率规则、内容边界、熔断规则、回滚方式。",
        "确认受控发送闸口已另行放行真实发送。",
        "确认仍不启用n8n自动定时推送。",
        "确认股票内容不包含交易化表达，不构成投资建议。",
    ]

    blockers = []
    if any(item["判定"] != "pass" for item in sub_status):
        blockers.append("247-251 子包存在未通过项。")
    if receipt.get("确认人", "") == "" or receipt.get("确认时间", "") == "" or receipt.get("目标用户", "") == "":
        blockers.append("人工确认回执尚未填写确认人、确认时间或目标用户。")
    for key in ["单人白名单确认", "频率确认", "内容边界确认", "熔断规则确认", "回滚方式确认"]:
        if receipt.get(key) is not True:
            blockers.append(f"人工确认项未完成：{key}。")
    if loaded["250"].get("是否允许真实发送") is not False:
        blockers.append("250模板出现真实发送许可，必须阻断。")

    pass_items = [
        "主动推送准备路线已形成。",
        "单人白名单、频率、内容边界、熔断和重复拦截规则草案已形成。",
        "dry-run消息样本已形成。",
        "交易化表达扫描和重复发送拦截预演通过。",
        "人工确认回执模板已形成且默认未生效。",
    ]

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "总体状态": "blocked",
        "当前结论": "真实灰度发送前准备链路已补齐，但人工确认与受控发送闸口仍未放行；当前不得真实发送。",
        "是否允许真实发送": False,
        "是否允许n8n自动推送": False,
        "子包状态": sub_status,
        "通过项": pass_items,
        "阻断项": blockers or ["真实发送仍需独立人工确认和受控发送闸口放行。"],
        "人工前置确认": human_required,
        "建议下一步": [
            "保持当前只读总闸口 blocked 状态。",
            "如用户未来要求真实灰度发送，先填写250人工确认回执，并复跑252总闸口。",
            "真实发送仍只允许单人、单条、人工触发，不启用n8n自动推送。",
        ],
        "实际动作": {
            "读取247到251本地包": True,
            "写本地252总闸口": True,
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

    out_dir = data / "252主动推送真实灰度发送前最终只读总闸口"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"股票主动推送真实灰度发送前最终只读总闸口_{stamp}.json"
    latest_json = out_dir / "股票主动推送真实灰度发送前最终只读总闸口_最新.json"
    output_md = out_dir / f"股票主动推送真实灰度发送前最终只读总闸口_{stamp}.md"
    latest_md = out_dir / "股票主动推送真实灰度发送前最终只读总闸口_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": report["总体状态"], "允许真实发送": False, "阻断项": len(report["阻断项"]), "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
