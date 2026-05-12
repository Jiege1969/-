# -*- coding: utf-8 -*-
"""
名称：生成股票主动推送灰度链路总索引与操作卡.py
作用：汇总247-255股票主动推送灰度准备链路，生成本地总索引和操作卡。
触发方式：python 生成股票主动推送灰度链路总索引与操作卡.py
依赖：Python标准库；247-255主动推送灰度准备包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写本地256索引包；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易；不写正式规则库。
创建/修改记录：2026-05-09 创建股票主动推送灰度链路总索引与操作卡。
标识：stock-active-push-gray-chain-index-operation-card-generate
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


def state(path: Path) -> dict[str, Any]:
    return {
        "存在": path.exists(),
        "路径": str(path),
        "大小": path.stat().st_size if path.exists() else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票主动推送灰度链路总索引与操作卡",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 总结",
        "",
        f"- 当前结论：{report['当前结论']}",
        f"- 链路完整度：{report['链路完整度']}",
        f"- 是否允许真实发送：{report['是否允许真实发送']}",
        f"- 是否允许n8n自动推送：{report['是否允许n8n自动推送']}",
        "",
        "## 链路索引",
        "",
    ]
    for item in report["链路索引"]:
        lines.append(f"- {item['编号']} {item['名称']}：{item['状态']}，{item['用途']}")
    lines.extend(["", "## 操作卡", ""])
    for item in report["操作卡"]:
        lines.append(f"{item['顺序']}. {item['动作']}：{item['当前结果']}")
    lines.extend(["", "## 禁止绕过", ""])
    for item in report["禁止绕过"]:
        lines.append(f"- {item}")
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
    packages = [
        ("247", "主动推送灰度启用准备包", data / "247主动推送灰度启用准备包" / "股票主动推送灰度启用准备包_最新.json", "判断是否可以推进准备工作。"),
        ("248", "主动推送白名单频率熔断规则包", data / "248主动推送白名单频率熔断规则包" / "股票主动推送白名单频率熔断规则包_最新.json", "定义单人白名单、频率、内容边界和熔断规则。"),
        ("249", "主动推送dry-run消息样本包", data / "249主动推送dry-run消息样本包" / "股票主动推送dry-run消息样本包_最新.json", "生成本地dry-run消息样本。"),
        ("250", "主动推送真实灰度人工确认回执模板包", data / "250主动推送真实灰度人工确认回执模板包" / "股票主动推送真实灰度人工确认回执模板包_最新.json", "提供人工确认回执模板，默认未生效。"),
        ("251", "主动推送交易化表达与重复发送拦截预演包", data / "251主动推送交易化表达与重复发送拦截预演包" / "股票主动推送交易化表达与重复发送拦截预演包_最新.json", "扫描交易化表达并预演重复发送拦截。"),
        ("252", "主动推送真实灰度发送前最终只读总闸口", data / "252主动推送真实灰度发送前最终只读总闸口" / "股票主动推送真实灰度发送前最终只读总闸口_最新.json", "最终只读判定是否可进入真实灰度。"),
        ("253", "主动推送灰度发送日志台账与回滚演练包", data / "253主动推送灰度发送日志台账与回滚演练包" / "股票主动推送灰度发送日志台账与回滚演练包_最新.json", "预演发送台账、失败记录、熔断和回滚。"),
        ("254", "主动推送人工确认回执填写校验与闸口复跑包", data / "254主动推送人工确认回执填写校验与闸口复跑包" / "股票主动推送人工确认回执填写校验与闸口复跑包_最新.json", "检查250人工确认回执是否填全。"),
        ("255", "主动推送单条灰度人工触发执行预案与停止开关包", data / "255主动推送单条灰度人工触发执行预案与停止开关包" / "股票主动推送单条灰度人工触发执行预案与停止开关包_最新.json", "定义单条人工触发执行预案和停止开关。"),
    ]

    index = []
    for code, name, path, purpose in packages:
        doc = load_json(path)
        st = state(path)
        if code == "247":
            passed = doc.get("可以推进准备工作") is True
        elif code == "248":
            passed = doc.get("是否允许真实发送") is False and doc.get("是否允许n8n自动推送") is False
        elif code == "249":
            passed = doc.get("dry_run") is True and doc.get("真实发送") is False
        elif code == "250":
            passed = doc.get("模板状态") == "待人工确认，未生效" and doc.get("是否允许真实发送") is False
        elif code == "251":
            passed = doc.get("总体状态") == "pass" and int(doc.get("交易化表达命中数", -1)) == 0
        elif code == "252":
            passed = doc.get("总体状态") == "blocked" and doc.get("是否允许真实发送") is False
        elif code == "253":
            passed = doc.get("演练通过") is True and doc.get("是否真实发送") is False
        elif code == "254":
            passed = doc.get("总体状态") == "blocked" and doc.get("是否允许真实发送") is False
        else:
            passed = doc.get("预案是否允许执行") is False and doc.get("是否真实发送") is False
        index.append({
            "编号": code,
            "名称": name,
            "路径": st["路径"],
            "存在": st["存在"],
            "状态": "pass" if st["存在"] and passed else "blocked",
            "用途": purpose,
        })

    complete = all(item["存在"] for item in index)
    all_expected = all(item["状态"] == "pass" for item in index)
    current_blockers = [
        "250人工确认回执尚未由人工填写并确认。",
        "252最终只读总闸口仍保持blocked。",
        "255单条人工触发预案仍拒绝执行。",
        "受控发送闸口未放行真实企业微信发送。",
        "n8n自动推送仍不允许启用。",
    ]

    operation_card = [
        {"顺序": 1, "动作": "看256总索引", "当前结果": "确认247-255链路是否齐全"},
        {"顺序": 2, "动作": "看252总闸口", "当前结果": "当前blocked，不允许真实发送"},
        {"顺序": 3, "动作": "如需未来灰度，先填写250人工确认回执", "当前结果": "当前未填写"},
        {"顺序": 4, "动作": "复跑254确认回执校验", "当前结果": "当前blocked"},
        {"顺序": 5, "动作": "复跑252最终只读总闸口", "当前结果": "当前blocked"},
        {"顺序": 6, "动作": "复跑255单条人工触发预案", "当前结果": "当前拒绝执行"},
        {"顺序": 7, "动作": "仍不得启用n8n自动推送", "当前结果": "保持关闭"},
    ]

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "当前结论": "股票主动推送灰度准备链路已形成总索引；当前仍不得真实发送。",
        "链路完整度": f"{sum(1 for item in index if item['存在'])}/{len(index)}",
        "链路判定": "pass" if complete and all_expected else "blocked",
        "是否允许真实发送": False,
        "是否允许n8n自动推送": False,
        "链路索引": index,
        "操作卡": operation_card,
        "禁止绕过": [
            "不得绕过250人工确认回执。",
            "不得绕过252最终只读总闸口。",
            "不得绕过交易化表达扫描。",
            "不得绕过重复发送拦截。",
            "不得把dry-run样本当作真实发送许可。",
            "不得启用n8n自动推送。",
            "不得连接券商或产生交易动作。",
        ],
        "当前阻断项": current_blockers,
        "实际动作": {
            "读取247到255本地包": True,
            "写本地256索引包": True,
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

    out_dir = data / "256主动推送灰度链路总索引与操作卡"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"股票主动推送灰度链路总索引与操作卡_{stamp}.json"
    latest_json = out_dir / "股票主动推送灰度链路总索引与操作卡_最新.json"
    output_md = out_dir / f"股票主动推送灰度链路总索引与操作卡_{stamp}.md"
    latest_md = out_dir / "股票主动推送灰度链路总索引与操作卡_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": report["链路判定"], "链路完整度": report["链路完整度"], "允许真实发送": False, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
