# -*- coding: utf-8 -*-
"""
名称：生成股票系统可信IP放行后最终验收包.py
作用：生成企业微信可信IP加入白名单后的最终验收操作包，明确复测入口、成功判定和失败处理。
触发方式：python 生成股票系统可信IP放行后最终验收包.py
依赖：企微可信IP修复包、交付总包、C+++总验收、交付控制台。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地状态文件；只写03数据/154可信IP放行后最终验收包和05入口工具bat；不调用企业微信API；不发送企业微信；不触发n8n；不调用券商接口；不自动交易。
标识：stock-trusted-ip-final-acceptance-pack
"""

from __future__ import annotations

import json
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


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
        "大小": path.stat().st_size if path.exists() else 0,
    }


def build_markdown(report: dict[str, Any]) -> str:
    ip = report["当前公网出口IP"] or "未提取到"
    lines = [
        f"# 股票系统可信IP放行后最终验收包 - {report['生成时间']}",
        "",
        "## 一、当前结论",
        "",
        f"- 当前公网出口IP：`{ip}`",
        f"- 当前交付层级：{report['当前交付层级']}",
        f"- C+++总验收：{report['C+++总验收结论']}",
        "- 现在不需要改代码；只等企业微信后台可信IP白名单放行后复测。",
        "",
        "## 二、人工外部动作",
        "",
        "在企业微信管理后台进入对应自建应用，把下面IP加入可信IP白名单：",
        "",
        f"`{ip}`",
        "",
        "## 三、放行后复测入口",
        "",
        "放行后优先打开05入口工具：",
        "",
        f"`{report['复测入口']}`",
        "",
        "该入口会先要求你按键确认，再执行受控真实灰度复测；只有企业微信可信IP已放行时才可能成功。",
        "",
        "放行前可先双击预检入口，不会真实发送：",
        "",
        f"`{report['预检入口']}`",
        "",
        "也可以在命令行执行：",
        "",
        "```powershell",
        r"cd D:\杰哥智能化系统\02杰哥扩展系统\01股票研究系统\02脚本",
        "python 股票系统企微真实推送复测控制器.py --real-send --open-report",
        "```",
        "",
        "## 四、成功判定",
        "",
        "复测成功后应满足：",
        "",
        "- 企业微信真实发送成功为 True。",
        "- 企微真实推送复测报告显示真实发送成功为 True。",
        "- 交付自检中 D真实灰度可用 通过。",
        "- 交付控制台或交付总包不再把可信IP列为剩余硬阻断。",
        "- 再运行 C+++总验收，质量灯号保持绿灯，报告安全边界保持通过。",
        "",
        "## 五、失败处理",
        "",
        "如果仍返回 `60020 not allow to access from your ip`：",
        "",
        "1. 重新打开可信IP修复包，确认当前公网IP是否变化。",
        "2. 若IP变化，把新IP加入企业微信可信IP白名单。",
        "3. 不要重查密钥、模型、n8n、股票脚本；这不是它们的问题。",
        "",
        "## 六、关键文件",
        "",
    ]
    for name, state in report["关键文件"].items():
        lines.append(f"- {name}：{'存在' if state['存在'] else '缺失'}，`{state['路径']}`")
    lines.extend([
        "",
        "## 七、安全边界",
        "",
        "- 本包只生成最终验收说明。",
        "- 不调用企业微信API。",
        "- 不发送企业微信。",
        "- 不触发n8n。",
        "- 不调用券商接口。",
        "- 不自动交易。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(root: Path, target: Path) -> Path:
    bat = root / "05入口工具" / "股票系统可信IP放行后最终验收包_打开.bat"
    write_text(bat, f'@echo off\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    fix_json_path = root / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.json"
    total_json_path = root / "03数据" / "144交付总包" / "股票系统交付总包_最新.json"
    cppp_json_path = root / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.json"
    fix_json = load_json(fix_json_path, {})
    total_json = load_json(total_json_path, {})
    cppp_json = load_json(cppp_json_path, {})

    report = {
        "名称": "股票系统可信IP放行后最终验收包",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统可信IP放行后最终验收包.py",
        "当前公网出口IP": fix_json.get("当前公网出口IP") or "",
        "当前交付层级": total_json.get("当前交付层级") or "",
        "C+++总验收结论": cppp_json.get("验收结论") or "",
        "预检入口": str(root / "05入口工具" / "股票系统企微真实推送复测_预检不发送.bat"),
        "复测入口": str(root / "05入口工具" / "股票系统企微真实推送复测_确认可信IP后真实发送.bat"),
        "命令行复测命令": r"python 股票系统企微真实推送复测控制器.py --real-send --open-report",
        "关键文件": {
            "可信IP修复包": file_state(root / "03数据" / "141企微可信IP修复包" / "企业微信可信IP修复包_最新.md"),
            "交付控制台": file_state(root / "03数据" / "143交付控制台" / "股票系统交付控制台_最新.md"),
            "交付总包": file_state(root / "03数据" / "144交付总包" / "股票系统交付总包_最新.md"),
            "C+++总验收": file_state(root / "03数据" / "153C加加加总验收" / "股票系统C加加加日常可用总验收_最新.md"),
            "企微真实推送复测": file_state(root / "03数据" / "157企微真实推送复测" / "股票系统企微真实推送复测_最新.md"),
        },
        "安全边界": {
            "是否调用企业微信API": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
        },
    }
    output_dir = root / "03数据" / "154可信IP放行后最终验收包"
    output_json = output_dir / f"股票系统可信IP放行后最终验收包_{stamp}.json"
    output_md = output_dir / f"股票系统可信IP放行后最终验收包_{stamp}.md"
    latest_json = output_dir / "股票系统可信IP放行后最终验收包_最新.json"
    latest_md = output_dir / "股票系统可信IP放行后最终验收包_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    bat = write_entry_open_bat(root, latest_md)
    print(json.dumps({
        "状态": "完成",
        "当前公网出口IP": report["当前公网出口IP"],
        "最终验收包": str(latest_md),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
