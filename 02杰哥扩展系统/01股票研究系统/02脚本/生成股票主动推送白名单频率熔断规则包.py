# -*- coding: utf-8 -*-
"""
名称：生成股票主动推送白名单频率熔断规则包.py
作用：生成股票主动推送灰度启用前的单人白名单、频率、内容边界、重复发送拦截和熔断规则草案。
触发方式：python 生成股票主动推送白名单频率熔断规则包.py
依赖：Python标准库；247主动推送灰度启用准备包。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只写本地248规则包；不调用企业微信API；不真实发送；不启用或触发n8n；不重载服务；不调用券商接口；不自动交易；不写正式规则库。
创建/修改记录：2026-05-09 创建股票主动推送白名单频率熔断规则包。
标识：stock-active-push-whitelist-rate-circuit-rule-package-generate
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
        "# 股票主动推送白名单频率熔断规则包",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 当前状态：{report['当前状态']}",
        f"- 是否允许真实发送：{report['是否允许真实发送']}",
        f"- 是否允许n8n自动推送：{report['是否允许n8n自动推送']}",
        "",
        "## 单人白名单草案",
        "",
    ]
    whitelist = report["单人白名单草案"]
    for key, value in whitelist.items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 频率规则草案", ""])
    for key, value in report["频率规则草案"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 内容边界", ""])
    for item in report["内容边界"]["允许表达"]:
        lines.append(f"- 允许：{item}")
    for item in report["内容边界"]["禁止表达"]:
        lines.append(f"- 禁止：{item}")
    lines.extend(["", "## 熔断规则", ""])
    for item in report["熔断规则"]:
        lines.append(f"- {item['触发条件']}：{item['动作']}")
    lines.extend(["", "## 重复发送拦截", ""])
    for item in report["重复发送拦截"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["实际动作"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    prep_path = root / "03数据" / "247主动推送灰度启用准备包" / "股票主动推送灰度启用准备包_最新.json"
    prep = load_json(prep_path)

    whitelist = {
        "白名单状态": "草案，未生效",
        "目标范围": "仅允许单人本人灰度，不允许群发、部门群发、客户群发",
        "建议目标用户": "待人工确认，不在本包写入真实外发许可",
        "消息类型": "股票研究摘要草案或单股短答摘要",
        "放行方式": "必须另有人工确认回执；本包不构成真实发送授权",
    }

    rate_rule = {
        "首轮灰度频率": "单日最多1条，且必须人工触发",
        "连续灰度上限": "连续3个自然日通过后再评估是否提高频率",
        "静默时段": "22:00-08:30 不推送",
        "重复窗口": "同一股票、同一核心结论24小时内不得重复推送",
        "n8n定时": "当前禁止启用，只保留dry-run路线",
    }

    content_boundary = {
        "允许表达": [
            "研究价值",
            "风险复核",
            "观察条件",
            "证据缺口",
            "人工复核建议",
            "不构成投资建议",
        ],
        "禁止表达": [
            "买入",
            "卖出",
            "加仓",
            "减仓",
            "满仓",
            "清仓",
            "仓位",
            "下单",
            "交易指令",
            "保证收益",
            "确定上涨",
        ],
    }

    circuit_rules = [
        {"触发条件": "文本命中交易化表达", "动作": "阻断发送，写入熔断日志，转人工复核"},
        {"触发条件": "受控发送闸口未放行", "动作": "阻断真实发送，仅保留本地草案"},
        {"触发条件": "n8n触发开关非关闭", "动作": "阻断自动化，要求回到未激活/dry-run状态"},
        {"触发条件": "目标不是单人白名单", "动作": "阻断发送，不允许群发"},
        {"触发条件": "同一摘要24小时内重复", "动作": "拦截重复发送，保留去重记录"},
        {"触发条件": "股票服务、企业微信公共入口或安全巡检失败", "动作": "停止推送准备，先复跑只读巡检"},
        {"触发条件": "出现券商、交易、下单相关动作", "动作": "立即阻断并登记高风险事件"},
    ]

    duplicate_guard = [
        "按 股票代码 + 摘要哈希 + 自然日 生成去重键。",
        "同一去重键已存在时，只更新本地预览，不进入发送候选。",
        "人工修改摘要后仍需重新通过交易化表达检查。",
        "所有拦截记录只写本地日志，不外发。",
    ]

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源准备包": str(prep_path),
        "来源准备包可推进": prep.get("可以推进准备工作") is True,
        "当前状态": "主动推送灰度规则草案已生成，但未生效为真实发送配置。",
        "是否允许真实发送": False,
        "是否允许n8n自动推送": False,
        "单人白名单草案": whitelist,
        "频率规则草案": rate_rule,
        "内容边界": content_boundary,
        "熔断规则": circuit_rules,
        "重复发送拦截": duplicate_guard,
        "下一步候选": [
            "生成一条股票主动推送dry-run消息样本。",
            "对样本执行交易化表达扫描和重复发送拦截预演。",
            "生成真实灰度人工确认回执模板；仍不真实发送。",
        ],
        "实际动作": {
            "写本地规则草案": True,
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

    out_dir = root / "03数据" / "248主动推送白名单频率熔断规则包"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = out_dir / f"股票主动推送白名单频率熔断规则包_{stamp}.json"
    latest_json = out_dir / "股票主动推送白名单频率熔断规则包_最新.json"
    output_md = out_dir / f"股票主动推送白名单频率熔断规则包_{stamp}.md"
    latest_md = out_dir / "股票主动推送白名单频率熔断规则包_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    markdown = build_markdown(report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"总体状态": "draft_pass", "允许真实发送": False, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
