# -*- coding: utf-8 -*-
"""
名称：验证股票系统完全交付最终验收.py
作用：读取本地闭环、C+++总验收、报告安全边界、企微真实推送复测等状态，判断股票分析系统是否达到完全交付使用。
触发方式：python 验证股票系统完全交付最终验收.py [--open-report]
依赖：C+++总验收、交付总包、企微真实推送复测报告、报告安全边界检查。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地状态文件；只写03数据/158完全交付最终验收和05入口工具；不调用企业微信API；不真实发送企业微信；不触发n8n；不调用券商接口；不自动交易。
标识：stock-final-delivery-acceptance
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_state(path: Path, min_size: int = 1) -> dict[str, Any]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return {
        "路径": str(path),
        "存在": exists,
        "大小": size,
        "通过": bool(exists and size >= min_size),
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if exists else "",
    }


def latest_gray_send_success(root: Path) -> bool:
    """兜底读取正式灰度发送日志，避免复测控制器旧报告误判。"""
    data = load_json(root / "04日志" / "企业微信主动研究灰度发送" / "stock-active-research-wework-gray-send-最新.json", {})
    return bool(
        data.get("结果判定", {}).get("真实发送成功")
        or data.get("实际动作", {}).get("企业微信真实发送成功")
    )


def check_item(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"检查项": name, "通过": bool(ok), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统完全交付最终验收 - {report['生成时间']}",
        "",
        "## 一、验收结论",
        "",
        f"- 结论：{report['验收结论']}",
        f"- 通过：{report['通过数量']} / {report['检查数量']}",
        f"- 失败：{report['失败数量']}",
        f"- 当前交付层级：{report['当前交付层级']}",
        f"- 当前需放行IP：`{report['当前需放行IP'] or '未提取到'}`",
        "",
        "## 二、检查明细",
        "",
        "| 检查项 | 结果 | 说明 |",
        "|---|---|---|",
    ]
    for item in report["检查结果"]:
        lines.append(f"| {item['检查项']} | {'通过' if item['通过'] else '未通过'} | {item['说明']} |")
    lines.extend([
        "",
        "## 三、仍需处理",
        "",
    ])
    if report["仍需处理"]:
        for item in report["仍需处理"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无。")
    lines.extend([
        "",
        "## 四、关键文件",
        "",
    ])
    for name, state in report["关键文件"].items():
        lines.append(f"- {name}：{'存在' if state['存在'] else '缺失'}，`{state['路径']}`")
    lines.extend([
        "",
        "## 五、安全边界",
        "",
        "- 本验收器只读状态，不发送企业微信。",
        "- 不启用n8n自动触发。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(script_path: Path, target: Path) -> Path:
    bat = module_root() / "05入口工具" / "股票系统完全交付最终验收_打开.bat"
    write_text(bat, (
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        f'python "{script_path}"\r\n'
        f'start "" "{target}"\r\n'
    ))
    return bat


def maybe_open(path: Path, enabled: bool) -> None:
    if not enabled:
        return
    try:
        os.startfile(str(path))  # type: ignore[attr-defined]
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--open-report", action="store_true")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    total_path = root / "03数据" / "144交付总包" / "股票系统交付总包_最新.json"
    cppp_path = root / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.json"
    safety_path = root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.json"
    retest_path = root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.json"
    ip_status_path = root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.json"

    total = load_json(total_path, {})
    cppp = load_json(cppp_path, {})
    safety = load_json(safety_path, {})
    retest = load_json(retest_path, {})
    ip_status = load_json(ip_status_path, {})

    level = str(total.get("当前交付层级") or "")
    level_ok = ("C+++" in level) or level.startswith("D")
    daily_text = str(total.get("日常可用结论") or "")
    daily_ok = bool(total.get("日常可用") is True or "可日常使用" in daily_text)
    cppp_ok = int(cppp.get("失败数量") or 0) == 0 and int(cppp.get("通过数量") or 0) >= 14
    safety_ok = safety.get("安全结论") == "通过" and int(safety.get("命中总数") or 0) == 0
    real_push_ok = bool(retest.get("真实发送成功") or ip_status.get("企业微信真实发送已通过") or latest_gray_send_success(root))
    trusted_ip = retest.get("当前需放行IP") or ip_status.get("当前需放行IP") or ""

    checks = [
        check_item("本地日常可用", daily_ok, daily_text),
        check_item("交付层级达到C+++或更高", level_ok, level),
        check_item("C+++日常可用总验收通过", cppp_ok, f"{cppp.get('通过数量')}/{cppp.get('检查数量')}，失败{cppp.get('失败数量')}"),
        check_item("报告安全边界通过", safety_ok, f"安全结论={safety.get('安全结论')}，命中={safety.get('命中总数')}"),
        check_item("企业微信真实主动推送通过", real_push_ok, str(retest.get("复测结论") or "尚未完成真实发送复测")),
    ]

    pending: list[str] = []
    if not real_push_ok:
        pending.append(f"在企业微信后台加入可信IP `{trusted_ip or '未提取到'}` 后，再运行受控真实复测脚本。")
    if not safety_ok:
        pending.append("先运行报告安全边界检查并修复越界表述。")
    if not cppp_ok:
        pending.append("先运行C+++日常可用总验收并修复失败项。")

    failed = [item for item in checks if not item["通过"]]
    conclusion = "完全交付通过：股票分析系统已可完整使用" if not failed else "未完全交付：仍有外部或本地验收项未通过"
    key_files = {
        "交付总包": file_state(root / "03数据" / "144交付总包" / "股票系统交付总包_最新.md", 500),
        "C+++总验收": file_state(root / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.md", 500),
        "报告安全边界": file_state(root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.md", 500),
        "企微真实推送复测": file_state(root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.md", 500),
    }
    report = {
        "名称": "股票系统完全交付最终验收",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "验证股票系统完全交付最终验收.py",
        "当前交付层级": level,
        "当前需放行IP": trusted_ip,
        "验收结论": conclusion,
        "检查数量": len(checks),
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "检查结果": checks,
        "仍需处理": pending,
        "关键文件": key_files,
        "安全边界": {
            "是否调用企业微信API": False,
            "是否企业微信真实发送": False,
            "是否启用n8n自动触发": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }

    output_dir = root / "03数据" / "158完全交付最终验收"
    output_json = output_dir / f"股票系统完全交付最终验收_{stamp}.json"
    output_md = output_dir / f"股票系统完全交付最终验收_{stamp}.md"
    latest_json = output_dir / "股票系统完全交付最终验收_最新.json"
    latest_md = output_dir / "股票系统完全交付最终验收_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    bat = write_entry_open_bat(root / "02脚本" / "验证股票系统完全交付最终验收.py", latest_md)
    maybe_open(latest_md, args.open_report)

    print(json.dumps({
        "状态": "完成",
        "验收结论": conclusion,
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "当前需放行IP": trusted_ip,
        "报告": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
