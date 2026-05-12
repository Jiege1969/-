# -*- coding: utf-8 -*-
"""
名称：验证股票企微前台交互回归.py
作用：验证股票助手和股票分析专家的前台交互口径，防止后续施工把已修好的企微体验改坏。
触发方式：python 验证股票企微前台交互回归.py
依赖：股票助手入口.py；股票企业微信桥接入口.py；本地股票报告和推荐日报数据。
所属系统：02杰哥扩展系统/01股票研究系统
输出：03数据/182企微前台交互回归验收/股票企微前台交互回归验收_最新.md|json。
安全边界：只调用本地脚本；只写03数据验收目录；不触发n8n；不真实发送企业微信；不调用券商接口；不自动交易。
标识：stock-wecom-frontend-regression-check
"""

from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_assistant(root: Path, query: str) -> dict[str, Any]:
    entry = root / "02脚本" / "股票助手入口.py"
    started = datetime.now()
    try:
        proc = subprocess.run(
            [sys.executable, str(entry), query],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=90,
        )
        elapsed_ms = int((datetime.now() - started).total_seconds() * 1000)
        return {
            "query": query,
            "returncode": proc.returncode,
            "elapsed_ms": elapsed_ms,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "output": (proc.stdout or "") + (proc.stderr or ""),
        }
    except Exception as exc:
        elapsed_ms = int((datetime.now() - started).total_seconds() * 1000)
        return {
            "query": query,
            "returncode": -1,
            "elapsed_ms": elapsed_ms,
            "stdout": "",
            "stderr": str(exc),
            "output": str(exc),
        }


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    checks.append({"检查项": name, "通过": bool(ok), "说明": detail})


def contains_all(text: str, words: list[str]) -> bool:
    return all(word in text for word in words)


def contains_none(text: str, words: list[str]) -> bool:
    return all(word not in text for word in words)


def load_bridge_module(root: Path) -> Any:
    path = root / "02脚本" / "股票企业微信桥接入口.py"
    spec = importlib.util.spec_from_file_location("stock_wecom_bridge_for_regression", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法加载股票企业微信桥接入口.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def simulate_encrypted_app_reply(bridge: Any, content: str) -> str:
    """模拟普通企业微信应用加密XML被动回复，只做本地加解密回环，不连接企业微信。"""
    timestamp = str(int(time.time()))
    nonce = "stock-ordinary-app-regression"
    data = {
        "ToUserName": "corp-regression",
        "FromUserName": "jiege-regression",
        "MsgType": "text",
        "Content": "请推荐一下股票",
        "__encrypted_request": True,
        "__timestamp": timestamp,
        "__nonce": nonce,
    }
    app_content = bridge.prepare_wecom_app_content(content)
    plain_xml = bridge.build_wecom_text_xml_reply(data, app_content)
    encrypted_xml = bridge.encrypt_wecom_xml_reply(plain_xml, timestamp, nonce, bot=False)
    outer = ET.fromstring(encrypted_xml)
    reply_plain = bridge.decrypt_wecom_cipher(
        outer.findtext("Encrypt") or "",
        outer.findtext("MsgSignature") or "",
        outer.findtext("TimeStamp") or timestamp,
        outer.findtext("Nonce") or nonce,
        bot=False,
    )
    reply_root = ET.fromstring(reply_plain)
    return reply_root.findtext("Content") or ""


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    today = now.strftime("%Y-%m-%d")
    output_dir = root / "03数据" / "182企微前台交互回归验收"

    checks: list[dict[str, Any]] = []
    samples: dict[str, dict[str, Any]] = {}

    recommend = run_assistant(root, "请推荐一下股票")
    samples["请推荐一下股票"] = {k: recommend[k] for k in ("query", "returncode", "elapsed_ms", "output")}
    add_check(
        checks,
        "每日推荐_直接回答",
        recommend["returncode"] == 0
        and "今日推荐" in recommend["output"]
        and "你想看哪只股票" not in recommend["output"]
        and "我没有收到可分析的股票文本" not in recommend["output"],
        "推荐类自然语言应直接走每日推荐，不反问；手机端长文本可能截断，不能用“完整报告”作为硬条件。",
    )
    add_check(
        checks,
        "每日推荐_含详情入口",
        "详情：" in recommend["output"] or "点击股票名称查看详细报告" in recommend["output"],
        "每日推荐应提供单股详情入口。",
    )
    add_check(
        checks,
        "每日推荐_手机端分段显示",
        "\n\n【建议策略】：\n\n" in recommend["output"]
        and "\n\n【参考价位】：\n\n" in recommend["output"]
        and "\n\n【主要风险】：\n\n" in recommend["output"],
        "手机企业微信会吞单换行，三项核心内容必须按“空行+栏目名+空行+正文”显示。",
    )
    try:
        bridge = load_bridge_module(root)
        app_text = bridge.prepare_wecom_app_content("【杰哥股票研究助手】\n" + recommend["output"])
        encrypted_app_text = simulate_encrypted_app_reply(bridge, "【杰哥股票研究助手】\n" + recommend["output"])
    except Exception as exc:
        app_text = f"桥接普通应用文本生成失败：{exc}"
        encrypted_app_text = f"普通应用加密XML回复生成失败：{exc}"
    samples["普通应用推荐文本"] = {"query": "prepare_wecom_app_content", "returncode": 0, "elapsed_ms": 0, "output": app_text}
    samples["普通应用加密XML推荐文本"] = {"query": "simulate_encrypted_app_reply", "returncode": 0, "elapsed_ms": 0, "output": encrypted_app_text}
    add_check(
        checks,
        "普通应用_不显示Markdown链接外壳",
        contains_none(app_text, ["[龙芯中科", "](", "[中微公司", "[摩尔线程"]),
        "普通企业微信应用按纯文本展示，不能出现Markdown原文链接。",
    )
    add_check(
        checks,
        "普通应用_不重复无文本提示",
        "我没有收到可分析的股票文本" not in app_text,
        "普通企业微信应用推荐回复中不能夹带无文本事件提示。",
    )
    add_check(
        checks,
        "普通应用_手机端分段显示",
        "\n\n【建议策略】：\n\n" in app_text
        and "\n\n【参考价位】：\n\n" in app_text
        and "\n\n【主要风险】：\n\n" in app_text,
        "普通企业微信应用端也要按“空行+栏目名+空行+正文”的手机友好格式显示三项核心内容。",
    )
    add_check(
        checks,
        "普通应用_加密XML被动回复可读",
        "今日推荐" in encrypted_app_text
        and "我没有收到可分析的股票文本" not in encrypted_app_text
        and "](" not in encrypted_app_text
        and "【建议策略】" in encrypted_app_text
        and "【参考价位】" in encrypted_app_text
        and "【主要风险】" in encrypted_app_text,
        "【杰哥的股票分析专家】这类普通企业微信应用应能通过加密XML被动回复返回纯文本推荐摘要。",
    )
    try:
        expert_result = bridge.process_message({"text": "请推荐一下股票"}, robot_stream=False)
        expert_text = str(expert_result.get("企业微信内容") or expert_result.get("回复") or "")
    except Exception as exc:
        expert_text = f"专家入口本地回归失败：{exc}"
    samples["专家入口推荐文本"] = {"query": "bridge.process_message 普通应用专家入口", "returncode": 0, "elapsed_ms": 0, "output": expert_text}
    add_check(
        checks,
        "专家入口_日报摘要与图文入口",
        "专家总览" in expert_text
        and "完整图文报告" in expert_text
        and "/wecom-bot/message?view=stock-reco" in expert_text
        and "重点关注⭐⭐⭐⭐⭐" in expert_text
        and "风险观察线" not in expert_text,
        "【杰哥的股票分析专家】负责市场总览摘要和图文报告入口，不复用助手线单股价位模板。",
    )
    add_check(
        checks,
        "专家入口_可进入单股详情",
        "打开后可点股票名称查看单股详细分析" in expert_text
        and "今日推荐以下0只" not in expert_text,
        "专家入口应明确从图文报告进入单股详情，且不能退化为0只推荐。",
    )
    add_check(
        checks,
        "专家入口_普通应用长度安全",
        len(expert_text.encode("utf-8")) <= 1800
        and expert_text.find("/wecom-bot/message?view=stock-reco") < 140,
        "普通企业微信应用回复需按UTF-8字节保守控制，且完整图文报告入口必须出现在前段，避免手机端截断后看不到入口。",
    )

    detail_names = ["摩尔线程", "华虹公司", "湖南裕能", "协创数据", "格林美"]
    for name in detail_names:
        result = run_assistant(root, f"分析{name}")
        samples[f"分析{name}"] = {k: result[k] for k in ("query", "returncode", "elapsed_ms", "output")}
        output = result["output"]
        add_check(
            checks,
            f"单股详情_{name}_不误反问",
            result["returncode"] == 0 and "你想看哪只股票" not in output,
            f"{name} 来自推荐日报或股票池时，必须能直接打开详情。",
        )
        add_check(
            checks,
            f"单股详情_{name}_L3结论型短答",
            contains_all(output, ["分析对象：", "结论：", "一句话：", "现在怎么处理：", "观察条件：", "风险线：", "为什么：", "缺口："])
            and contains_none(output, ["当前判断：", "操作策略：", "关注条件：", "转强条件：", "成交标准：", "图文详情："]),
            f"{name} 详情应使用L3结论型短答，不能回退旧企微模板。",
        )
        add_check(
            checks,
            f"单股详情_{name}_不裸露入口URL行",
            contains_none(output, ["图形报告：http", "详细图文报告：http"]),
            "图形报告由企业微信图文卡或图文详情页承载，正文不再裸露旧入口URL。",
        )
        add_check(
            checks,
            f"单股详情_{name}_前台口径",
            contains_none(output, ["<font", "</font>", "买入机会", "操作检查清单"]),
            "前台不能出现HTML标签、买入机会措辞或旧版操作检查清单标题。",
        )
        add_check(
            checks,
            f"单股详情_{name}_关键价位非空",
            bool(__import__("re").search(r"\d+\.\d{2}元", output))
            and "观察承接：-" not in output
            and "风险观察线：-" not in output
            and "强度确认位：-" not in output,
            "单股前台短答必须有具体价位，不能因字段名不同退化成“-”。",
        )

    huahong = samples.get("分析华虹公司", {}).get("output", "")
    add_check(
        checks,
        "单股详情_华虹公司_L3结论口径",
        contains_all(huahong, ["分析对象：华虹公司", "结论：", "一句话：", "现在怎么处理：", "为什么："])
        and contains_none(huahong, ["重点推荐", "常规推荐", "当前判断：", "操作策略："]),
        "华虹公司详情应保持L3结论口径，不应出现旧推荐等级升级话术。",
    )

    holding = run_assistant(root, "我持仓天齐锂业还能不能拿")
    samples["我持仓天齐锂业还能不能拿"] = {k: holding[k] for k in ("query", "returncode", "elapsed_ms", "output")}
    holding_output = holding["output"]
    add_check(
        checks,
        "持仓诊断_直接回答",
        holding["returncode"] == 0
        and "分析对象：天齐锂业" in holding_output
        and "结论：" in holding_output
        and "现在怎么处理：" in holding_output
        and "你想看哪只股票" not in holding_output,
        "持仓类自然语言应直接给L3结论型研究短答，不退化成反问。",
    )
    add_check(
        checks,
        "持仓诊断_L3核心栏目完整",
        contains_all(holding_output, ["分析对象：", "结论：", "一句话：", "现在怎么处理：", "观察条件：", "风险线：", "为什么：", "缺口："])
        and contains_none(holding_output, ["当前判断：", "操作策略：", "关注条件：", "转强条件：", "成交标准：", "图文详情："]),
        "持仓诊断也应遵循L3结论型短答，不回退旧栏目。",
    )
    add_check(
        checks,
        "持仓诊断_不执行交易指令",
        contains_none(holding_output, ["自动下单", "立即买入", "立即卖出", "满仓", "清仓"]),
        "持仓诊断可以给研究观察口径，但不能输出自动交易或强指令。",
    )

    missing_object = run_assistant(root, "帮我分析一下")
    samples["帮我分析一下"] = {k: missing_object[k] for k in ("query", "returncode", "elapsed_ms", "output")}
    add_check(
        checks,
        "缺对象_只追问股票",
        missing_object["returncode"] == 0 and "请告诉我股票名称或代码" in missing_object["output"],
        "意图明确但缺股票对象时，只追问股票名或代码，并使用当前前台口径。",
    )

    trade = run_assistant(root, "能不能买天齐锂业")
    samples["能不能买天齐锂业"] = {k: trade[k] for k in ("query", "returncode", "elapsed_ms", "output")}
    add_check(
        checks,
        "交易动作_拦截并转研究",
        trade["returncode"] == 0
        and ("不能执行" in trade["output"] or "不执行任何交易指令" in trade["output"])
        and ("研究" in trade["output"] or "分析" in trade["output"]),
        "交易动作不执行，但应引导为研究辅助。",
    )

    failed = [item for item in checks if not item["通过"]]
    report = {
        "名称": "股票企微前台交互回归验收",
        "日期": today,
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "通过" if not failed else "存在失败",
        "通过数": len(checks) - len(failed),
        "失败数": len(failed),
        "安全边界": {
            "是否真实发送企业微信": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否修改源数据": False,
        },
        "检查项": checks,
        "样本输出": samples,
    }

    json_path = output_dir / f"股票企微前台交互回归验收_{stamp}.json"
    latest_json = output_dir / "股票企微前台交互回归验收_最新.json"
    md_path = output_dir / f"股票企微前台交互回归验收_{stamp}.md"
    latest_md = output_dir / "股票企微前台交互回归验收_最新.md"

    write_json(json_path, report)
    write_json(latest_json, report)

    lines = [
        f"# 股票企微前台交互回归验收 - {today}",
        "",
        f"- 状态：{report['状态']}",
        f"- 通过数：{report['通过数']}",
        f"- 失败数：{report['失败数']}",
        "- 安全边界：未真实发送企业微信、未触发n8n、未调用券商接口、未自动交易。",
        "",
        "## 检查项",
        "",
    ]
    for item in checks:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {mark}：{item['检查项']} - {item['说明']}")
    write_text(md_path, "\n".join(lines) + "\n")
    write_text(latest_md, "\n".join(lines) + "\n")

    print(json.dumps({
        "状态": report["状态"],
        "通过数": report["通过数"],
        "失败数": report["失败数"],
        "报告": str(latest_md),
        "数据": str(latest_json),
    }, ensure_ascii=False))

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
