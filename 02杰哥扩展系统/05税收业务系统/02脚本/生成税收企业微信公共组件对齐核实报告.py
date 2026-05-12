# -*- coding: utf-8 -*-
"""
名称：生成税收企业微信公共组件对齐核实报告.py
作用：核实税收企业微信入口与00公共组件/企业微信接入设置的终端、路由、凭据隔离和安全边界是否对齐。
安全边界：只读公开配置和本地报告；不读取企业微信私密配置、不联网、不启动服务、不真实发送、不触发n8n。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
TAX_ROOT = ROOT / "02杰哥扩展系统" / "05税收业务系统"
WECOM_ROOT = ROOT / "02杰哥扩展系统" / "00公共组件" / "企业微信接入设置"
OUT_DIR = TAX_ROOT / "03数据" / "32税收企业微信正式入口"
OUT_JSON = OUT_DIR / "税收企业微信公共组件对齐核实报告_最新.json"
OUT_MD = OUT_DIR / "税收企业微信公共组件对齐核实报告_最新.md"


PUBLIC_FILES = {
    "杰哥工作秘书配置": WECOM_ROOT / "01配置" / "杰哥工作秘书.json",
    "终端分工总表": WECOM_ROOT / "01配置" / "企业微信机器人终端分工总表.json",
    "统一路由规则": WECOM_ROOT / "01配置" / "企业微信统一指令路由预演规则.json",
    "本地调用规则": WECOM_ROOT / "01配置" / "企业微信统一指令本地调用预演规则.json",
    "双通道接入口径": WECOM_ROOT / "01配置" / "企业微信双通道接入口径.json",
    "凭据隔离规则": WECOM_ROOT / "01配置" / "企业微信凭据隔离规则.json",
    "公共状态摘要": WECOM_ROOT / "03数据" / "07状态摘要" / "wecom-assistant-system-status-summary-最新.json",
}

TAX_FILES = {
    "税收正式入口配置": TAX_ROOT / "01配置" / "税收企业微信正式入口配置.json",
    "税收输入消息契约": TAX_ROOT / "01配置" / "税收企业微信输入消息契约.json",
    "税收接收服务设计": TAX_ROOT / "01配置" / "税收企业微信消息接收服务设计.json",
    "税收全链路预检": TAX_ROOT / "03数据" / "32税收企业微信正式入口" / "税收企业微信正式入口全链路预检_最新.json",
}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def row(name: str, ok: bool, detail: Any) -> dict[str, Any]:
    return {"核实项": name, "是否对齐": bool(ok), "详情": detail}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work_secretary = load_json(PUBLIC_FILES["杰哥工作秘书配置"])
    terminals = load_json(PUBLIC_FILES["终端分工总表"])
    route_rule = load_json(PUBLIC_FILES["统一路由规则"])
    call_rule = load_json(PUBLIC_FILES["本地调用规则"])
    channel_rule = load_json(PUBLIC_FILES["双通道接入口径"])
    credential_rule = load_json(PUBLIC_FILES["凭据隔离规则"])
    public_status = load_json(PUBLIC_FILES["公共状态摘要"])
    tax_config = load_json(TAX_FILES["税收正式入口配置"])
    tax_contract = load_json(TAX_FILES["税收输入消息契约"])
    tax_receive = load_json(TAX_FILES["税收接收服务设计"])
    tax_precheck = load_json(TAX_FILES["税收全链路预检"])

    terminal_rows = terminals.get("终端列表", [])
    work_terminal = next((item for item in terminal_rows if item.get("名称") == "杰哥工作秘书"), {})
    route_names = {item.get("路由") for item in route_rule.get("路由规则", [])}
    tax_route = next((item for item in route_rule.get("路由规则", []) if item.get("路由") == "税收业务待复核分析"), {})
    local_call = call_rule.get("允许本地调用", {}).get("税收业务待复核分析", {})
    public_alignment = tax_config.get("公共组件接入口径", {})
    tax_safety = tax_config.get("安全边界", {})
    receive_safety = tax_receive.get("安全边界", {})
    public_summary = public_status.get("汇总", {})

    checks = [
        row("未读取公共私密配置", True, "本报告只读取公开配置、状态摘要和税收系统配置，不读取企业微信助手私密配置_本机.json。"),
        row("公共杰哥工作秘书配置存在", PUBLIC_FILES["杰哥工作秘书配置"].exists() and work_secretary.get("名称") == "杰哥工作秘书", str(PUBLIC_FILES["杰哥工作秘书配置"])),
        row("公共终端公网路径为work-secretary", "/wecom/work-secretary" in work_secretary.get("建议通讯路径", "") or "/wecom/work-secretary" in str(work_terminal.get("公网/企业微信路径", [])), work_terminal),
        row("公共双通道口径禁用长连接", channel_rule.get("当前主用") == "公网URL回调" and channel_rule.get("长连接通道", {}).get("状态") == "禁用", channel_rule),
        row("公共凭据隔离规则禁止明文", any("不得写入JSON" in item for item in credential_rule.get("凭据存放原则", [])), credential_rule.get("凭据存放原则", [])),
        row("公共税收路由已由暂停改为待复核分析", "税收业务待复核分析" in route_names and "税收业务暂停" not in route_names, sorted(str(item) for item in route_names)),
        row("公共税收路由不产生真实动作", tax_route.get("真实动作") is False and "正式税务结论" in tax_route.get("执行方式", ""), tax_route),
        row("公共本地调用指向税收待复核摘要", local_call.get("方式") == "tax_review_preview" and "税收企业微信待复核草案骨架到分析摘要预演" in str(local_call), local_call),
        row("税收正式入口绑定杰哥工作秘书", tax_config.get("机器人终端", {}).get("机器人名称") == "杰哥工作秘书", tax_config.get("机器人终端", {})),
        row("税收配置登记公共组件入口", public_alignment.get("公共公网回调路径") == "/wecom/work-secretary" and public_alignment.get("是否新增税收公网回调") is False, public_alignment),
        row("税收接收服务不另开公网回调", tax_receive.get("默认端口策略", {}).get("候选路径") == "/wecom/work-secretary" and tax_receive.get("默认端口策略", {}).get("是否新增端口") is False, tax_receive.get("默认端口策略", {})),
        row("税收输入契约仍为待证据匹配", tax_contract.get("机器人终端") == "杰哥工作秘书" and "pending_evidence_match" in tax_contract.get("输入状态词", []), tax_contract),
        row("税收全链路真实发送仍阻断", tax_precheck.get("结论") == "通过" and tax_precheck.get("是否真实发送") is False and tax_precheck.get("发送门禁结论") == "已阻断", tax_precheck),
        row("公共状态摘要健康且不真实发送", public_summary.get("状态") == "healthy" and public_summary.get("是否企业微信真实发送") is False and public_summary.get("是否触发n8n") is False, public_summary),
        row("税收高风险动作全部关闭", tax_safety.get("是否企业微信真实发送") is False and tax_safety.get("是否触发n8n") is False and tax_safety.get("是否接电子税务局") is False and tax_safety.get("是否接财税软件") is False, tax_safety),
        row("税收接收设计高风险动作全部关闭", receive_safety.get("是否启动服务") is False and receive_safety.get("是否新增端口") is False and receive_safety.get("是否读取凭据") is False and receive_safety.get("是否保存凭据") is False, receive_safety),
    ]
    passed = sum(1 for item in checks if item["是否对齐"])
    failed = len(checks) - passed
    report = {
        "名称": "税收企业微信公共组件对齐核实报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 else "需修正",
        "通过数量": passed,
        "失败数量": failed,
        "公共组件路径": str(WECOM_ROOT),
        "税收系统路径": str(TAX_ROOT),
        "读取公开文件": {name: str(path) for name, path in PUBLIC_FILES.items()},
        "读取税收文件": {name: str(path) for name, path in TAX_FILES.items()},
        "核实结果": checks,
        "对齐口径": {
            "企业微信公网入口": "/wecom/work-secretary",
            "公共组件职责": "企业微信回调、统一路由、凭据隔离、公共状态摘要。",
            "税收系统职责": "本地输入队列、政策证据匹配、待复核分析草案、门禁和审计。",
            "禁止越界": "不读取公共凭据、不另开税收公网回调、不真实发送、不生成正式税务结论、不执行办税动作。",
        },
        "安全边界": {
            "是否读取私密配置": False,
            "是否联网": False,
            "是否启动服务": False,
            "是否新增端口": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否生成正式税务结论": False,
            "是否接电子税务局": False,
            "是否接财税软件": False,
        },
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 税收企业微信公共组件对齐核实报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{passed}",
        f"- 失败数量：{failed}",
        f"- 企业微信公网入口：{report['对齐口径']['企业微信公网入口']}",
        "",
        "## 核实结果",
        "",
    ]
    for item in checks:
        lines.append(f"- {item['核实项']}：{'对齐' if item['是否对齐'] else '未对齐'}。{item['详情']}")
    lines.extend(["", "## 对齐口径", ""])
    for key, value in report["对齐口径"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"状态": report["结论"], "通过数量": passed, "失败数量": failed, "报告": str(OUT_MD)}, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
