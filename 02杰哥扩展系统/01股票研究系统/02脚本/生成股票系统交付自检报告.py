# -*- coding: utf-8 -*-
"""
名称：生成股票系统交付自检报告.py
作用：检查股票主动研究系统当前交付状态，生成交付自检报告。
触发方式：python 生成股票系统交付自检报告.py
依赖：本地闭环日志、AI报告、推送草案、企微灰度发送记录、放行包、n8n草案、复盘报告等。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地文件；只写03数据/140交付自检与04日志/主动研究闭环；不触发n8n；不发送企业微信；不写正式库；不调用券商接口；不自动交易。
标识：stock-delivery-self-check-report
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"必需文件不存在: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def exists_info(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def status_label(ok: bool) -> str:
    return "通过" if ok else "未通过"


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统交付自检报告 - {report['生成时间']}",
        "",
        "## 一、总状态",
        "",
        f"- 当前交付层级：{report['当前交付层级']}",
        f"- 本地可用：{status_label(report['层级验收']['A本地可用']['是否通过'])}",
        f"- 企业微信草案可用：{status_label(report['层级验收']['B企业微信草案可用']['是否通过'])}",
        f"- 企业微信通道检查：{status_label(report['层级验收']['B2企业微信通道检查']['是否通过'])}",
        f"- n8n草案可用：{status_label(report['层级验收']['Cn8n草案可用']['是否通过'])}",
        f"- n8n未激活导入：{status_label(report['层级验收']['C2n8n未激活导入']['是否通过'])}",
        f"- n8n手动受控测试：{status_label(report['层级验收']['C3n8n手动受控测试']['是否通过'])}",
        f"- 真实灰度：{status_label(report['层级验收']['D真实灰度可用']['是否通过'])}",
        f"- 交付可用：{status_label(report['层级验收']['E交付可用']['是否通过'])}",
        "",
        "## 二、关键验收项",
        "",
    ]
    for name, item in report["关键验收项"].items():
        lines.append(f"- {name}：{status_label(item['是否通过'])}；{item.get('说明', '')}")
    lines.extend([
        "",
        "## 三、关键文件",
        "",
    ])
    for name, item in report["关键文件"].items():
        lines.append(f"- {name}：{'存在' if item['存在'] else '缺失'}，`{item['路径']}`")
    lines.extend([
        "",
        "## 四、仍未放行事项",
        "",
    ])
    for item in report["仍未放行事项"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## 五、安全边界",
        "",
        "- 未触发n8n。",
        f"- n8n已导入未激活：{report['安全边界']['是否n8n已导入未激活']}。",
        "- 未启用n8n。",
        f"- 企业微信真实发送成功：{report['安全边界']['是否企业微信真实发送成功']}。",
        "- 未调用券商接口。",
        "- 未自动交易。",
    ])
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    paths = {
        "一键闭环日志": root / "04日志" / "主动研究闭环" / "本地主动研究闭环运行日志_最新.json",
        "AI分析报告": root / "03数据" / "135分层日报" / "AI分析报告_最新.md",
        "AI分析报告JSON": root / "03数据" / "135分层日报" / "AI分析报告_最新.json",
        "企微推送草案": root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md",
        "企微灰度发送记录": root / "04日志" / "企业微信主动研究灰度发送" / "stock-active-research-wework-gray-send-最新.json",
        "企微灰度发送演练记录": root / "04日志" / "企业微信主动研究灰度发送" / "stock-active-research-wework-gray-send-最新演练.json",
        "企微灰度发送真实记录": root / "04日志" / "企业微信主动研究灰度发送" / "stock-active-research-wework-gray-send-最新真实.json",
        "企微可信IP修复包": root / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.md",
        "推送前放行包": root / "03数据" / "138推送前放行包" / "股票企微推送前放行包_最新.md",
        "n8n未激活草案": root / "03数据" / "139n8n主动研究编排草案" / "股票主动研究n8n未激活编排草案_最新.md",
        "n8n未激活导入工件": root / "03数据" / "142n8n未激活导入工件" / "股票主动研究闭环_n8n未激活导入_最新.json",
        "n8n未激活导入记录": root / "04日志" / "n8n未激活导入" / "stock-active-research-n8n-inactive-import-最新.json",
        "n8n手动受控测试记录": root / "04日志" / "n8n本地手动测试" / "stock-active-research-n8n-local-manual-execute-最新.json",
        "轻量复盘": root / "03数据" / "137复盘报告" / "股票周复盘_轻量_最新.md",
        "使用说明": root / "07文档" / "股票主动研究系统本地使用说明_20260501.md",
    }
    run_log = load_json(paths["一键闭环日志"])
    ai_json = load_json(paths["AI分析报告JSON"])
    approval_json = load_json(root / "03数据" / "138推送前放行包" / "股票企微推送前放行包_最新.json")
    n8n_json = load_json(root / "03数据" / "139n8n主动研究编排草案" / "股票主动研究n8n未激活编排草案_最新.json")
    n8n_import_json = load_json(paths["n8n未激活导入记录"])
    n8n_manual_json = load_json(paths["n8n手动受控测试记录"])
    wework_gray_json = load_json(paths["企微灰度发送记录"])
    wework_dry_json = load_json(paths["企微灰度发送演练记录"])
    wework_real_json = load_json(paths["企微灰度发送真实记录"])
    common_sender_json = load_json(root.parents[0] / "00公共组件" / "04日志" / "企业微信受控发送器" / "wework-controlled-sender-最新.json")
    trusted_ip_fix_json = load_json(root / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.json")
    sender_result = common_sender_json.get("发送结果", {}).get("企业微信返回", {})
    trusted_ip_blocked = sender_result.get("errcode") == 60020 or bool(trusted_ip_fix_json.get("是否命中60020"))

    local_ok = bool(run_log.get("是否成功")) and ai_json.get("数据健康度", {}).get("分析股票数", 0) > 0
    wecom_draft_ok = paths["企微推送草案"].exists() and paths["推送前放行包"].exists()
    wecom_channel_check_ok = bool(
        wework_dry_json.get("结果判定", {}).get("是否通过公共发送器检查")
        or wework_gray_json.get("结果判定", {}).get("是否通过公共发送器检查")
    )
    n8n_draft_ok = paths["n8n未激活草案"].exists() and n8n_json.get("是否已导入n8n") is False
    n8n_inactive_import_ok = bool(
        n8n_import_json.get("导入后保持未激活")
        and (n8n_import_json.get("是否导入n8n") or n8n_import_json.get("已存在未重复导入"))
    )
    n8n_manual_ok = bool(n8n_manual_json.get("通过") and n8n_manual_json.get("执行后保持未激活"))
    real_gray_ok = bool(wework_real_json.get("结果判定", {}).get("真实发送成功")) and not trusted_ip_blocked
    delivery_ok = local_ok and wecom_draft_ok and n8n_draft_ok and real_gray_ok
    sender_error = sender_result.get("errmsg", "") or trusted_ip_fix_json.get("企业微信返回errmsg", "")
    current_level = (
        "D：本地闭环 + 企微真实灰度已成功"
        if delivery_ok else
        "C+++：本地闭环可用 + n8n已未激活导入并通过手动受控测试 + 企微通道检查通过；真实主动消息尚未成功"
        if local_ok and wecom_draft_ok and wecom_channel_check_ok and n8n_inactive_import_ok and n8n_manual_ok else
        "C++：本地闭环可用 + n8n已未激活导入 + 企微通道检查通过；真实主动消息尚未成功"
        if local_ok and wecom_draft_ok and wecom_channel_check_ok and n8n_inactive_import_ok else
        "C+：本地闭环可用 + 企微通道检查通过；真实主动消息尚未成功"
        if local_ok and wecom_draft_ok and wecom_channel_check_ok and n8n_draft_ok else
        "C：本地闭环可用 + 企微/n8n草案可用；真实灰度未放行"
        if n8n_draft_ok else
        "A/B：本地可用或草案不完整"
    )

    report = {
        "名称": "股票系统交付自检报告",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统交付自检报告.py",
        "当前交付层级": current_level,
        "层级验收": {
            "A本地可用": {"是否通过": local_ok, "说明": "一键闭环与AI报告可用。"},
            "B企业微信草案可用": {"是否通过": wecom_draft_ok, "说明": "推送草案和放行包已生成。"},
            "B2企业微信通道检查": {"是否通过": wecom_channel_check_ok, "说明": "已通过公共受控发送器检查；真实主动消息若失败，多半受企业微信可信IP限制。"},
            "Cn8n草案可用": {"是否通过": n8n_draft_ok, "说明": "n8n未激活草案已生成，但未导入、未启用。"},
            "C2n8n未激活导入": {"是否通过": n8n_inactive_import_ok, "说明": f"目标容器：{n8n_import_json.get('目标容器', '')}；目标工作流：{n8n_import_json.get('目标工作流', '')}。"},
            "C3n8n手动受控测试": {"是否通过": n8n_manual_ok, "说明": f"工作流ID：{n8n_manual_json.get('工作流ID', '')}；桥接触发：{n8n_manual_json.get('桥接触发成功', False)}。"},
            "D真实灰度可用": {"是否通过": real_gray_ok, "说明": "真实企业微信灰度发送成功。" if real_gray_ok else f"真实主动消息未成功。最近原因：{sender_error or '未发现企业微信返回原因'}"},
            "E交付可用": {"是否通过": delivery_ok, "说明": "需真实灰度稳定后再判定。"},
        },
        "关键验收项": {
            "一键闭环成功": {"是否通过": bool(run_log.get("是否成功")), "说明": f"步骤数：{len(run_log.get('步骤结果', []))}"},
            "AI报告生成": {"是否通过": paths["AI分析报告"].exists(), "说明": f"分析数：{ai_json.get('数据健康度', {}).get('分析股票数', 0)}"},
            "推送草案生成": {"是否通过": paths["企微推送草案"].exists(), "说明": "仅草案，未发送。"},
            "企微通道检查": {"是否通过": wecom_channel_check_ok, "说明": f"最近演练模式：{wework_dry_json.get('模式', wework_gray_json.get('模式', ''))}"},
            "放行包安全": {"是否通过": approval_json.get("是否允许真实发送") is False, "说明": "默认不允许真实发送。"},
            "n8n草案安全": {"是否通过": n8n_json.get("是否已导入n8n") is False and n8n_json.get("是否已启用n8n") is False, "说明": "未导入，未启用。"},
            "n8n未激活导入安全": {"是否通过": n8n_inactive_import_ok, "说明": "已导入但保持active=false，未触发。"},
            "n8n手动受控测试安全": {"是否通过": n8n_manual_ok, "说明": "手动执行后仍保持active=false，企业微信仅dry-run。"},
            "复盘可用": {"是否通过": paths["轻量复盘"].exists(), "说明": "轻量复盘已生成。"},
        },
        "关键文件": {name: exists_info(path) for name, path in paths.items()},
        "仍未放行事项": [
            "企业微信应用主动消息真实发送稳定化" if not real_gray_ok else "企业微信应用主动消息真实发送已通过首条灰度",
            "若企业微信返回60020，需要在企业微信管理后台把当前公网出口IP加入应用可信IP白名单",
            "n8n启用前人工受控测试",
            "n8n启用",
            "券商接口",
            "自动交易",
        ],
        "安全边界": {
            "是否自动交易": False,
            "是否调用券商接口": False,
            "是否触发n8n": False,
            "是否n8n已导入未激活": n8n_inactive_import_ok,
            "是否n8n手动受控测试通过": n8n_manual_ok,
            "是否企业微信真实发送成功": real_gray_ok,
            "是否写旧系统": False,
            "是否写正式库": False,
        },
        "实际动作": {
            "读取本地状态文件": True,
            "生成自检报告": True,
            "写入03数据": True,
            "写入04日志": True,
            "触发n8n": False,
            "导入n8n未激活工作流": n8n_inactive_import_ok,
            "n8n手动受控测试": n8n_manual_ok,
            "启用n8n": False,
            "企业微信真实发送": bool(wework_real_json.get("实际动作", {}).get("企业微信真实发送")),
            "企业微信真实发送成功": real_gray_ok,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    output_dir = root / "03数据" / "140交付自检"
    output_json = output_dir / f"股票系统交付自检报告_{stamp}.json"
    output_md = output_dir / f"股票系统交付自检报告_{stamp}.md"
    latest_json = output_dir / "股票系统交付自检报告_最新.json"
    latest_md = output_dir / "股票系统交付自检报告_最新.md"
    log_dir = root / "04日志" / "主动研究闭环"
    log_path = log_dir / f"股票系统交付自检日志_{stamp}.json"
    log_latest_path = log_dir / "股票系统交付自检日志_最新.json"
    markdown = build_markdown(report)

    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, {
        "名称": "股票系统交付自检日志",
        "生成时间": report["生成时间"],
        "当前交付层级": report["当前交付层级"],
        "层级验收": report["层级验收"],
        "输出文件": {"JSON": str(output_json), "Markdown": str(output_md)},
        "安全边界": report["安全边界"],
        "实际动作": report["实际动作"],
    })
    write_json(log_latest_path, load_json(log_path, required=True))

    print(json.dumps({
        "状态": "完成",
        "当前交付层级": current_level,
        "A本地可用": local_ok,
        "B企业微信草案可用": wecom_draft_ok,
        "Cn8n草案可用": n8n_draft_ok,
        "D真实灰度可用": real_gray_ok,
        "Markdown": str(output_md),
        "JSON": str(output_json),
    }, ensure_ascii=False))
    return 0 if local_ok and wecom_draft_ok and n8n_draft_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
