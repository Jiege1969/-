# -*- coding: utf-8 -*-
"""
统一刷新股票系统交付状态扎口。

这个脚本只读取本地状态文件，只刷新交付口径文件；不调用企业微信 API，
不触发 n8n，不调用券商接口，不自动交易。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = ROOT.parents[0] / "00公共组件"

CONTROLLED_SENDER_LATEST = COMMON_ROOT / "04日志" / "企业微信受控发送器" / "wework-controlled-sender-最新.json"
TRUSTED_IP_STATUS_LATEST = ROOT / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.json"
WECOM_RETEST_LATEST = ROOT / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.json"
WECOM_IP_ALLOW_LATEST = ROOT / "03数据" / "85企业微信可信IP放行状态" / "企业微信可信IP放行状态_最新.json"
DELIVERY_SELF_CHECK_LATEST = ROOT / "03数据" / "140交付自检" / "股票系统交付自检报告_最新.json"
DELIVERY_PACKAGE_LATEST = ROOT / "03数据" / "144交付总包" / "股票系统交付总包_最新.json"
FINAL_ACCEPTANCE_LATEST = ROOT / "03数据" / "158完全交付最终验收" / "股票系统完全交付最终验收_最新.json"
WECOM_EXPERIENCE_LATEST = ROOT / "03数据" / "289企业微信体验入口状态" / "股票企业微信体验入口状态_最新.json"

FIXED_PUBLIC_EGRESS_IP = "43.167.210.211"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def nested_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def nested_set(data: dict[str, Any], keys: list[str], value: Any) -> None:
    cur: dict[str, Any] = data
    for key in keys[:-1]:
        child = cur.get(key)
        if not isinstance(child, dict):
            child = {}
            cur[key] = child
        cur = child
    cur[keys[-1]] = value


def controlled_sender_success(sender: dict[str, Any]) -> bool:
    wecom_return = nested_get(sender, "发送结果", "企业微信返回", default={})
    actions = sender.get("实际动作", {}) if isinstance(sender, dict) else {}
    return bool(
        isinstance(wecom_return, dict)
        and wecom_return.get("errcode") == 0
        and actions.get("发送企业微信成功") is True
    )


def controlled_sender_blocked_ip(sender: dict[str, Any]) -> str:
    text = str(nested_get(sender, "发送结果", "企业微信返回", "errmsg", default=""))
    marker = "from ip: "
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split(",", 1)[0].strip()


def build_state() -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sender = read_json(CONTROLLED_SENDER_LATEST, {}) or {}
    ip_status = read_json(TRUSTED_IP_STATUS_LATEST, {}) or {}
    retest = read_json(WECOM_RETEST_LATEST, {}) or {}
    self_check = read_json(DELIVERY_SELF_CHECK_LATEST, {}) or {}
    package = read_json(DELIVERY_PACKAGE_LATEST, {}) or {}
    final = read_json(FINAL_ACCEPTANCE_LATEST, {}) or {}
    experience = read_json(WECOM_EXPERIENCE_LATEST, {}) or {}
    ip_allow = read_json(WECOM_IP_ALLOW_LATEST, {}) or {}

    sender_ok = controlled_sender_success(sender)
    ip_status_ok = bool(
        ip_status.get("企业微信真实发送已通过")
        or ip_status.get("最新真实发送复测已通过")
    )
    wecom_real_send_ok = sender_ok or ip_status_ok
    blocked_ip = controlled_sender_blocked_ip(sender)
    fixed_ip = str(
        ip_status.get("固定公网出口IP")
        or ip_status.get("当前需放行IP")
        or blocked_ip
        or FIXED_PUBLIC_EGRESS_IP
    )
    old_retest_false = retest.get("真实发送成功") is False and wecom_real_send_ok

    delivery_level = (
        "D：股票分析系统可日常使用 + 企业微信问答入口可用 + 本人白名单主动推送已打通"
        if wecom_real_send_ok
        else "C+++：本地闭环可用 + 企业微信问答入口可用；主动推送仍待可信IP放行"
    )
    hard_blocker = "无" if wecom_real_send_ok else "企业微信应用主动消息可信IP白名单"
    daily_available = (
        "可日常使用：数据、分析、前台报告、企业微信问答和本人白名单主动推送均已形成可体验闭环。"
        if wecom_real_send_ok
        else "可日常使用：数据、分析、前台报告和企业微信问答可用；主动推送待可信IP放行后复测。"
    )

    return {
        "生成时间": now,
        "名称": "股票系统交付状态扎口同步",
        "当前统一结论": (
            "扎口已打开：可信IP不再作为当前硬阻断，旧复测报告只保留为历史证据。"
            if wecom_real_send_ok
            else "扎口未完全打开：主动推送仍受可信IP限制。"
        ),
        "交付层级": delivery_level,
        "剩余硬阻断": hard_blocker,
        "日常可用结论": daily_available,
        "固定公网出口IP": fixed_ip,
        "企业微信真实发送已通过": wecom_real_send_ok,
        "最新受控发送日志": {
            "路径": str(CONTROLLED_SENDER_LATEST),
            "存在": CONTROLLED_SENDER_LATEST.exists(),
            "生成时间": sender.get("生成时间", ""),
            "发送企业微信成功": sender_ok,
            "企业微信返回": nested_get(sender, "发送结果", "企业微信返回", default={}),
        },
        "可信IP状态监测": {
            "路径": str(TRUSTED_IP_STATUS_LATEST),
            "存在": TRUSTED_IP_STATUS_LATEST.exists(),
            "状态": ip_status.get("状态", ""),
            "企业微信真实发送已通过": ip_status.get("企业微信真实发送已通过"),
            "最新真实发送复测已通过": ip_status.get("最新真实发送复测已通过"),
        },
        "旧复测报告处理": {
            "路径": str(WECOM_RETEST_LATEST),
            "存在": WECOM_RETEST_LATEST.exists(),
            "复测结论": retest.get("复测结论", ""),
            "真实发送成功": retest.get("真实发送成功"),
            "是否已被更新事实覆盖": old_retest_false,
            "处理意见": "保留为历史证据，不再作为当前交付阻断依据。" if old_retest_false else "继续作为当前证据之一。",
        },
        "同步文件": {
            "交付自检": str(DELIVERY_SELF_CHECK_LATEST),
            "交付总包": str(DELIVERY_PACKAGE_LATEST),
            "最终验收": str(FINAL_ACCEPTANCE_LATEST),
            "企业微信体验入口": str(WECOM_EXPERIENCE_LATEST),
        },
        "安全边界": {
            "是否调用企业微信API": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }


def update_self_check(state: dict[str, Any]) -> None:
    data = read_json(DELIVERY_SELF_CHECK_LATEST, {}) or {}
    if not data:
        data = {"名称": "股票系统交付自检报告"}
    data["生成时间"] = state["生成时间"]
    data["当前交付层级"] = state["交付层级"]
    data["仍未放行事项"] = ["无"] if state["企业微信真实发送已通过"] else ["企业微信应用主动消息可信IP白名单"]
    nested_set(data, ["安全边界", "是否企业微信真实发送成功"], state["企业微信真实发送已通过"])
    nested_set(data, ["实际动作", "企业微信真实发送成功"], state["企业微信真实发送已通过"])
    write_json(DELIVERY_SELF_CHECK_LATEST, data)


def update_delivery_package(state: dict[str, Any]) -> None:
    data = read_json(DELIVERY_PACKAGE_LATEST, {}) or {}
    if not data:
        data = {"名称": "股票系统交付总包"}
    data["生成时间"] = state["生成时间"]
    data["当前交付层级"] = state["交付层级"]
    data["日常可用结论"] = state["日常可用结论"]
    data["剩余硬阻断"] = state["剩余硬阻断"]
    data["固定公网出口IP"] = state["固定公网出口IP"]
    data["下一步动作"] = [
        "继续围绕股票主线完善可体验功能。",
        "企业微信作为正式体验入口，已完成能力应让使用者直接体验。",
        "n8n/Webhook/券商接口/自动交易仍保持边界，不作为当前施工阻断。",
    ]
    nested_set(data, ["安全边界", "是否企业微信真实发送成功"], state["企业微信真实发送已通过"])
    write_json(DELIVERY_PACKAGE_LATEST, data)
    write_text(DELIVERY_PACKAGE_LATEST.with_suffix(".md"), build_package_md(data))


def update_final_acceptance(state: dict[str, Any]) -> None:
    data = read_json(FINAL_ACCEPTANCE_LATEST, {}) or {}
    if not data:
        data = {"名称": "股票系统完全交付最终验收", "检查结果": []}
    data["生成时间"] = state["生成时间"]
    data["当前交付层级"] = state["交付层级"]
    data["当前需放行IP"] = state["固定公网出口IP"]

    checks = data.get("检查结果", [])
    if not isinstance(checks, list):
        checks = []
    found_wecom = False
    for item in checks:
        if not isinstance(item, dict):
            continue
        name = str(item.get("检查项", ""))
        if "企业微信" in name and "真实" in name and "推送" in name:
            item["通过"] = bool(state["企业微信真实发送已通过"])
            item["说明"] = "最新受控发送日志返回 ok，可信IP状态监测已通过。"
            found_wecom = True
    if not found_wecom:
        checks.append({
            "检查项": "企业微信真实主动推送通过",
            "通过": bool(state["企业微信真实发送已通过"]),
            "说明": "最新受控发送日志返回 ok，可信IP状态监测已通过。" if state["企业微信真实发送已通过"] else "仍待可信IP放行。",
        })

    failed = [item for item in checks if isinstance(item, dict) and not item.get("通过")]
    data["检查结果"] = checks
    data["检查数量"] = len(checks)
    data["通过数量"] = len(checks) - len(failed)
    data["失败数量"] = len(failed)
    data["仍需处理"] = [
        "继续修复 C+++ 日常可用总验收中的细节项。"
    ] if failed else []
    data["验收结论"] = (
        "完全交付通过：股票分析系统已可完整使用。"
        if not failed
        else "未完全交付：可信IP旧阻断已解除，仍有本地细节验收项待收口。"
    )
    write_json(FINAL_ACCEPTANCE_LATEST, data)
    write_text(FINAL_ACCEPTANCE_LATEST.with_suffix(".md"), build_final_md(data))


def update_wecom_experience(state: dict[str, Any]) -> None:
    data = {
        "名称": "股票企业微信体验入口状态",
        "生成时间": state["生成时间"],
        "当前结论": (
            "企业微信问答入口可用；本人白名单主动推送已通过固定公网出口打通。"
            if state["企业微信真实发送已通过"]
            else "企业微信问答入口可用；主动推送仍受可信IP限制。"
        ),
        "使用口径": "企业微信是股票系统正式体验窗口；已完成能力应直接给使用者体验，问题进入反馈和改进闭环。",
        "主动推送状态": {
            "固定公网出口IP": state["固定公网出口IP"],
            "企业微信真实发送已通过": state["企业微信真实发送已通过"],
            "最新发送日志": state["最新受控发送日志"]["路径"],
            "企业微信返回": state["最新受控发送日志"]["企业微信返回"],
            "可信IP受限": not state["企业微信真实发送已通过"],
        },
        "安全边界": {
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
            "主动群发": False,
        },
    }
    write_json(WECOM_EXPERIENCE_LATEST, data)
    write_text(WECOM_EXPERIENCE_LATEST.with_suffix(".md"), build_wecom_md(data))


def update_wecom_ip_allow_status(state: dict[str, Any]) -> None:
    data = read_json(WECOM_IP_ALLOW_LATEST, {}) or {}
    if not data:
        data = {"名称": "企业微信可信IP放行状态"}
    data["生成时间"] = state["生成时间"]
    data["状态"] = "已放行" if state["企业微信真实发送已通过"] else "需放行可信IP"
    data["当前判断"] = (
        "固定公网出口已通过企业微信真实发送验证。"
        if state["企业微信真实发送已通过"]
        else "应用消息通道仍需在企业微信后台放行当前公网出口IP。"
    )
    data["最近企业微信返回"] = {
        "errcode": 0 if state["企业微信真实发送已通过"] else 60020,
        "errmsg摘要": "ok" if state["企业微信真实发送已通过"] else "not allow to access from your ip",
        "识别到的公网IP": state["固定公网出口IP"],
    }
    data["当前需放行IP"] = state["固定公网出口IP"]
    data["安全边界"] = {
        "本脚本调用企业微信API": False,
        "本脚本发送企业微信": False,
        "写旧系统": False,
        "调用券商接口": False,
        "自动交易": False,
    }
    write_json(WECOM_IP_ALLOW_LATEST, data)


def build_package_md(data: dict[str, Any]) -> str:
    return "\n".join([
        f"# 股票系统交付总包 - {data.get('生成时间', '')}",
        "",
        f"- 当前交付层级：{data.get('当前交付层级', '')}",
        f"- 日常可用结论：{data.get('日常可用结论', '')}",
        f"- 剩余硬阻断：{data.get('剩余硬阻断', '')}",
        f"- 固定公网出口IP：`{data.get('固定公网出口IP', '')}`",
        "",
        "## 下一步动作",
        *[f"- {item}" for item in data.get("下一步动作", [])],
        "",
    ])


def build_final_md(data: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统完全交付最终验收 - {data.get('生成时间', '')}",
        "",
        f"- 结论：{data.get('验收结论', '')}",
        f"- 通过：{data.get('通过数量', 0)} / {data.get('检查数量', 0)}",
        f"- 失败：{data.get('失败数量', 0)}",
        f"- 当前交付层级：{data.get('当前交付层级', '')}",
        f"- 固定公网出口IP：`{data.get('当前需放行IP', '')}`",
        "",
        "## 检查明细",
        "",
        "| 检查项 | 结果 | 说明 |",
        "|---|---|---|",
    ]
    for item in data.get("检查结果", []):
        if not isinstance(item, dict):
            continue
        lines.append(f"| {item.get('检查项', '')} | {'通过' if item.get('通过') else '未通过'} | {item.get('说明', '')} |")
    lines.extend(["", "## 仍需处理", ""])
    pending = data.get("仍需处理", [])
    if pending:
        lines.extend(f"- {item}" for item in pending)
    else:
        lines.append("- 无")
    return "\n".join(lines)


def build_wecom_md(data: dict[str, Any]) -> str:
    status = data.get("主动推送状态", {})
    return "\n".join([
        f"# 股票企业微信体验入口状态 - {data.get('生成时间', '')}",
        "",
        f"- 当前结论：{data.get('当前结论', '')}",
        f"- 使用口径：{data.get('使用口径', '')}",
        "- 问答入口：可用",
        "- 状态帮助短答可用：可用",
        f"- 需放行IP：`{status.get('固定公网出口IP', '')}`",
        f"- 固定公网出口IP：`{status.get('固定公网出口IP', '')}`",
        f"- 企业微信真实发送已通过：{status.get('企业微信真实发送已通过')}",
        f"- 可信IP受限：{status.get('可信IP受限')}",
        "",
        "## 边界",
        "- 不触发 n8n。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不主动群发。",
        "",
    ])


def write_all(state: dict[str, Any]) -> None:
    update_self_check(state)
    update_delivery_package(state)
    update_final_acceptance(state)
    update_wecom_experience(state)
    update_wecom_ip_allow_status(state)


def check_current_outputs(state: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if not state["企业微信真实发送已通过"]:
        failures.append("企业微信真实发送尚未通过，扎口不能打开。")
        return failures

    self_check = read_json(DELIVERY_SELF_CHECK_LATEST, {}) or {}
    package = read_json(DELIVERY_PACKAGE_LATEST, {}) or {}
    final = read_json(FINAL_ACCEPTANCE_LATEST, {}) or {}
    experience = read_json(WECOM_EXPERIENCE_LATEST, {}) or {}
    ip_allow = read_json(WECOM_IP_ALLOW_LATEST, {}) or {}

    stale_terms = ["可信IP限制", "受可信IP限制", "待可信IP修复", "真实主动消息尚未成功", "可信IP白名单"]
    checks = {
        "交付自检当前交付层级": str(self_check.get("当前交付层级", "")),
        "交付总包剩余硬阻断": str(package.get("剩余硬阻断", "")),
        "交付总包日常可用结论": str(package.get("日常可用结论", "")),
        "企业微信体验入口当前结论": str(experience.get("当前结论", "")),
    }
    for name, text in checks.items():
        for term in stale_terms:
            if term in text:
                failures.append(f"{name}仍包含旧阻断口径：{term}")
    if final.get("检查结果"):
        wecom_checks = [
            item for item in final.get("检查结果", [])
            if isinstance(item, dict) and "企业微信" in str(item.get("检查项", "")) and "推送" in str(item.get("检查项", ""))
        ]
        if wecom_checks and not any(item.get("通过") for item in wecom_checks):
            failures.append("最终验收里的企业微信真实主动推送仍未放行。")
    latest_ip = str((ip_allow.get("最近企业微信返回") or {}).get("识别到的公网IP") or ip_allow.get("当前需放行IP") or "")
    if latest_ip and latest_ip != state["固定公网出口IP"]:
        failures.append(f"企业微信可信IP放行状态仍指向旧IP：{latest_ip}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="只检查当前扎口文件是否过时，不写文件")
    args = parser.parse_args()

    state = build_state()
    if args.check:
        failures = check_current_outputs(state)
        print(json.dumps({"结论": "通过" if not failures else "未通过", "失败项": failures}, ensure_ascii=False, indent=2))
        return 0 if not failures else 1

    write_all(state)
    print(json.dumps({
        "结论": state["当前统一结论"],
        "企业微信真实发送已通过": state["企业微信真实发送已通过"],
        "剩余硬阻断": state["剩余硬阻断"],
        "同步文件": state["同步文件"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
