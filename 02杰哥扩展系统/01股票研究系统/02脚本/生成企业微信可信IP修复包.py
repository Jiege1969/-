# -*- coding: utf-8 -*-
"""
名称：生成企业微信可信IP修复包.py
作用：读取企业微信受控发送器最新日志，提取60020可信IP拦截原因，生成后台修复说明包。
触发方式：python 生成企业微信可信IP修复包.py
依赖：00公共组件/04日志/企业微信受控发送器/wework-controlled-sender-最新.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读日志；只写03数据/141企微可信IP修复包；不调用企业微信API；不发送企业微信；不触发n8n；不交易。
标识：stock-wework-trusted-ip-fix-pack
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

FIXED_PUBLIC_EGRESS_IP = "43.167.210.211"

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


def extract_ip(text: str) -> str:
    match = re.search(r"from ip:\s*([0-9]+(?:\.[0-9]+){3})", text or "")
    return match.group(1) if match else ""


def find_latest_sender_log(log_dir: Path) -> tuple[Path, dict[str, Any], str]:
    latest = log_dir / "wework-controlled-sender-最新.json"
    if latest.exists():
        data = load_json(latest, required=True)
        errmsg = str(data.get("发送结果", {}).get("企业微信返回", {}).get("errmsg", ""))
        return latest, data, errmsg
    candidates = sorted(
        [p for p in log_dir.glob("wework-controlled-sender-*.json") if p.name != "wework-controlled-sender-最新.json"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        data = load_json(path)
        send_result = data.get("发送结果", {}).get("企业微信返回", {})
        errmsg = str(send_result.get("errmsg", ""))
        if send_result.get("errcode") == 60020 and extract_ip(errmsg):
            return path, data, errmsg
    for path in candidates:
        data = load_json(path)
        errmsg = str(data.get("发送结果", {}).get("企业微信返回", {}).get("errmsg", ""))
        if errmsg:
            return path, data, errmsg
    return Path(), {}, ""


def build_markdown(data: dict[str, Any]) -> str:
    lines = [
        f"# 企业微信可信IP修复包 - {data['生成时间']}",
        "",
        "## 一、当前结论",
        "",
        f"- 是否命中60020：{data['是否命中60020']}",
        f"- 当前公网出口IP：`{data['当前公网出口IP'] or '未提取到'}`",
        f"- 目标应用档案：`{data['目标应用档案'].get('名称') or '未提取到'}`",
        f"- 企业ID变量：`{data['目标应用档案'].get('企业ID变量') or '未提取到'}`",
        f"- 应用ID变量：`{data['目标应用档案'].get('应用ID变量') or '未提取到'}`",
        f"- 企业微信返回：`{data['企业微信返回errmsg'] or '无'}`",
        "",
        "## 二、修复动作",
        "",
        f"在企业微信管理后台进入上面的目标自建应用，把固定公网出口IP `{FIXED_PUBLIC_EGRESS_IP}` 加入该应用的可信IP白名单。",
        "",
        "完成后重新执行：",
        "",
        "```powershell",
        r"cd D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本",
        "python 股票系统企微真实推送复测控制器.py --real-send --open-report",
        "```",
        "",
        "也可以打开05入口工具：`股票系统企微真实推送复测_确认可信IP后真实发送.bat`。",
        "",
        "## 三、安全边界",
        "",
        "- 本修复包只生成说明，不自动修改企业微信后台。",
        "- 不调用企业微信API。",
        "- 不发送企业微信。",
        "- 不触发n8n。",
        "- 不调用券商接口，不自动交易。",
    ]
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    common_log_dir = root.parents[0] / "00公共组件" / "04日志" / "企业微信受控发送器"
    common_log, log_data, errmsg = find_latest_sender_log(common_log_dir)
    send_result = log_data.get("发送结果", {}).get("企业微信返回", {}) if isinstance(log_data, dict) else {}
    fixed_public = log_data.get("固定公网出口", {}) if isinstance(log_data.get("固定公网出口"), dict) else {}
    hit_60020 = send_result.get("errcode") == 60020
    ip = (
        extract_ip(errmsg)
        if hit_60020
        else str(fixed_public.get("实际出口IP") or fixed_public.get("公网IP") or FIXED_PUBLIC_EGRESS_IP)
    )
    target_profile = log_data.get("目标应用档案") if isinstance(log_data.get("目标应用档案"), dict) else {}
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    report = {
        "名称": "企业微信可信IP修复包",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成企业微信可信IP修复包.py",
        "上游日志": str(common_log),
        "是否命中60020": hit_60020,
        "当前公网出口IP": ip or FIXED_PUBLIC_EGRESS_IP,
        "固定公网出口IP": FIXED_PUBLIC_EGRESS_IP,
        "目标应用档案": {
            "名称": target_profile.get("名称", ""),
            "状态": target_profile.get("状态", ""),
            "企业ID变量": target_profile.get("企业ID变量", ""),
            "应用ID变量": target_profile.get("应用ID变量", ""),
            "应用密钥变量": target_profile.get("应用密钥变量", ""),
            "说明": target_profile.get("说明", ""),
        },
        "企业微信返回errmsg": errmsg,
        "修复建议": f"将固定公网出口IP {FIXED_PUBLIC_EGRESS_IP} 加入企业微信对应自建应用可信IP白名单后，再重新执行真实灰度发送。",
        "安全边界": {
            "是否自动修改企业微信后台": False,
            "是否调用企业微信API": False,
            "是否发送企业微信": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
        "实际动作": {
            "读取公共发送器日志": True,
            "提取公网出口IP": bool(ip),
            "使用固定公网出口": True,
            "写入03数据": True,
            "调用企业微信API": False,
            "发送企业微信": False,
            "触发n8n": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "141企微可信IP修复包"
    output_json = output_dir / f"企业微信可信IP修复包_{stamp}.json"
    output_md = output_dir / f"企业微信可信IP修复包_{stamp}.md"
    latest_json = output_dir / "企业微信可信IP修复包_最新.json"
    latest_md = output_dir / "企业微信可信IP修复包_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({
        "状态": "完成",
        "是否命中60020": report["是否命中60020"],
        "当前公网出口IP": ip,
        "Markdown": str(output_md),
        "JSON": str(output_json),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
