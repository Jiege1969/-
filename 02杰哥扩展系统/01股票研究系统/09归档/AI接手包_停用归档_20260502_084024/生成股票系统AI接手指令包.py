# -*- coding: utf-8 -*-
"""
名称：生成股票系统AI接手指令包.py
作用：生成给其他AI读取的最小接手指令包，明确当前状态、默认决策、禁止反问项和下一步动作。
触发方式：python 生成股票系统AI接手指令包.py
依赖：交付总包、质量观察面板、报告安全边界检查、施工接续卡片。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地状态文件；只写03数据/151AI接手指令包和05入口工具bat；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-ai-handoff-instruction-pack
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def system_root() -> Path:
    return Path(r"D:\杰哥智能化系统")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统AI接手指令包 - {report['生成时间']}",
        "",
        "## 一、接手结论",
        "",
        "你接手的是股票主动研究系统，不需要重新讨论架构。",
        f"当前状态：{report['当前状态']}",
        f"日常可用：{report['日常可用']}",
        f"质量灯号：{report['质量灯号']}",
        f"报告安全边界：{report['报告安全边界']}",
        "",
        "## 二、默认决策",
        "",
        "1. L8A/L8B/L8U/L8X 机制已经接入，日常只说“综合候选池”，不要要求用户重新确认分层设计。",
        "2. 每日主流程从交付控制台 `--mode run` 开始，不要逐个问脚本路径。",
        "3. 企业微信真实主动推送尚未成功，原因是可信IP白名单，不要重复排查密钥或模型。",
        "4. n8n 已未激活导入并通过手动受控测试，不要启用自动触发。",
        "5. 金融专项复核是手动增强能力，不进入每日必跑，不自动推送。",
        "6. 报告安全边界检查已经接入控制台 run/all，发现命中时先修报告/清洗规则，不要绕过。",
        "",
        "## 三、禁止反问项",
        "",
        "- 不要问是否采用沪深300+中证500，已定稿为L8A客观基底。",
        "- 不要问是否把用户增强池并入L8A，已定稿为L8U独立标记、L8X统一入口。",
        "- 不要问是否能自动交易，永远不做自动交易。",
        "- 不要问是否直接启用n8n自动触发，当前禁止。",
        "- 不要问是否真实发送企业微信，除非用户明确说可信IP已加入并要求复测。",
        "- 不要要求用户重新提供股票池路径，先读交付总包和控制台。",
        "",
        "## 四、下一步施工顺序",
        "",
        "1. 先运行或查看：`股票系统交付控制台_查看状态.bat`。",
        "2. 需要生成当天结果：运行 `股票系统交付控制台_运行闭环.bat`。",
        "3. 查看 `股票系统质量观察面板_打开.bat`，确认质量灯号和报告安全边界。",
        "4. 如用户说可信IP已加好，再运行 `股票系统交付控制台_企微真实复测_需先加可信IP.bat`。",
        "5. 若继续优化，优先做质量复盘、报告可读性、推送体验，不扩大到税收系统。",
        "",
        "## 五、关键入口",
        "",
    ]
    for name, path in report["关键入口"].items():
        lines.append(f"- {name}：`{path}`")
    lines.extend([
        "",
        "## 六、关键文件",
        "",
    ])
    for name, state in report["关键文件"].items():
        lines.append(f"- {name}：{'存在' if state['存在'] else '缺失'}，`{state['路径']}`")
    lines.extend([
        "",
        "## 七、安全边界",
        "",
        "- 不触发n8n。",
        "- 不发送企业微信真实消息。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不改旧系统。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(root: Path, target: Path) -> Path:
    bat = root / "05入口工具" / "股票系统AI接手指令包_打开.bat"
    write_text(bat, f'@echo off\r\nstart "" "{target}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    sys_root = system_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")

    total_package_path = root / "03数据" / "144交付总包" / "股票系统交付总包_最新.json"
    quality_path = root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.json"
    safety_path = root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.json"
    continuation_path = sys_root / "00杰哥系统总管" / "03数据" / "施工接续" / "施工接续卡片_最新.md"
    startup_path = sys_root / "00杰哥系统总管" / "03数据" / "开工上下文" / "新对话先读这个.md"

    total_package = load_json(total_package_path, {})
    quality = load_json(quality_path, {})
    safety = load_json(safety_path, {})
    quality_light = (quality.get("质量灯号") or {}).get("灯号") or "未知"
    safety_conclusion = safety.get("安全结论") or "未知"

    report = {
        "名称": "股票系统AI接手指令包",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统AI接手指令包.py",
        "当前状态": total_package.get("当前交付层级") or "未知",
        "日常可用": bool(total_package.get("日常可用")),
        "质量灯号": quality_light,
        "报告安全边界": safety_conclusion,
        "关键入口": {
            "查看状态": str(root / "05入口工具" / "股票系统交付控制台_查看状态.bat"),
            "运行闭环": str(root / "05入口工具" / "股票系统交付控制台_运行闭环.bat"),
            "一键运行并查看质量面板": str(root / "05入口工具" / "股票系统一键运行并查看质量面板.bat"),
            "质量观察面板": str(root / "05入口工具" / "股票系统质量观察面板_打开.bat"),
            "报告安全边界检查": str(root / "05入口工具" / "股票系统报告安全边界检查_打开.bat"),
            "金融专项复核": str(root / "05入口工具" / "股票系统金融专项复核_运行L5第一只.bat"),
            "企微真实复测": str(root / "05入口工具" / "股票系统交付控制台_企微真实复测_需先加可信IP.bat"),
        },
        "关键文件": {
            "交付总包": file_state(root / "03数据" / "144交付总包" / "股票系统交付总包_最新.md"),
            "交付控制台": file_state(root / "03数据" / "143交付控制台" / "股票系统交付控制台_最新.md"),
            "质量观察面板": file_state(root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.md"),
            "报告安全边界检查": file_state(root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.md"),
            "施工接续卡片": file_state(continuation_path),
            "开工上下文": file_state(startup_path),
        },
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否修改旧系统": False,
        },
    }

    output_dir = root / "03数据" / "151AI接手指令包"
    output_json = output_dir / f"股票系统AI接手指令包_{stamp}.json"
    output_md = output_dir / f"股票系统AI接手指令包_{stamp}.md"
    latest_json = output_dir / "股票系统AI接手指令包_最新.json"
    latest_md = output_dir / "股票系统AI接手指令包_最新.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    bat = write_entry_open_bat(root, latest_md)

    print(json.dumps({
        "状态": "完成",
        "接手指令包": str(latest_md),
        "入口工具": str(bat),
        "质量灯号": quality_light,
        "报告安全边界": safety_conclusion,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
