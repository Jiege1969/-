# -*- coding: utf-8 -*-
"""
名称：生成股票系统AI接手压缩包.py
作用：把股票系统AI接手所需的最小文件集合打成压缩包，便于交给另一个AI读取。
触发方式：python 生成股票系统AI接手压缩包.py
依赖：AI接手指令包、交付总包、日常速查卡、质量面板、报告安全边界检查等最新文件。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地文件；只写03数据/152AI接手压缩包和05入口工具bat；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-ai-handoff-zip-pack
"""

from __future__ import annotations

import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def file_info(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def build_readme(manifest: dict[str, Any]) -> str:
    lines = [
        f"# 股票系统AI接手压缩包说明 - {manifest['生成时间']}",
        "",
        "## 使用方式",
        "",
        "请先读取 `01_先读这个_股票系统AI接手指令包.md`。",
        "读取后直接按其中“下一步施工顺序”执行，不要重新询问已定稿事项。",
        "",
        "## 包内文件",
        "",
    ]
    for item in manifest["文件清单"]:
        lines.append(f"- `{item['包内路径']}`：{item['说明']}；来源：`{item['源路径']}`；存在：{item['存在']}")
    lines.extend([
        "",
        "## 禁止动作",
        "",
        "- 不启用n8n自动触发。",
        "- 不真实发送企业微信，除非用户明确说可信IP已加入并要求复测。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不改旧系统。",
    ])
    return "\n".join(lines)


def write_entry_open_bat(root: Path, target: Path) -> Path:
    bat = root / "05入口工具" / "股票系统AI接手压缩包_打开目录.bat"
    write_text(bat, f'@echo off\r\nstart "" "{target.parent}"\r\n')
    return bat


def main() -> int:
    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    output_dir = root / "03数据" / "152AI接手压缩包"
    zip_path = output_dir / f"股票系统AI接手压缩包_{stamp}.zip"
    latest_zip = output_dir / "股票系统AI接手压缩包_最新.zip"
    latest_manifest = output_dir / "股票系统AI接手压缩包_最新.json"
    latest_readme = output_dir / "股票系统AI接手压缩包_说明_最新.md"

    files = [
        ("01_先读这个_股票系统AI接手指令包.md", root / "03数据" / "151AI接手指令包" / "股票系统AI接手指令包_最新.md", "最小接手指令，先读"),
        ("02_交付总包.md", root / "03数据" / "144交付总包" / "股票系统交付总包_最新.md", "交付状态、日常入口和剩余阻断"),
        ("03_日常速查卡.md", root / "03数据" / "145日常速查卡" / "股票系统日常使用速查卡_最新.md", "用户日常使用方式"),
        ("04_质量观察面板.md", root / "03数据" / "146质量观察面板" / "股票系统质量观察面板_最新.md", "质量灯号和最新运行质量"),
        ("05_报告安全边界检查.md", root / "03数据" / "150报告安全边界检查" / "股票系统报告安全边界检查_最新.md", "报告越界表达检查"),
        ("06_金融专项复核索引.md", root / "03数据" / "149金融专项复核索引" / "股票金融专项复核索引_最新.md", "专业模型复核历史索引"),
        ("07_控制台报告.md", root / "03数据" / "143交付控制台" / "股票系统交付控制台_最新.md", "交付控制台最新状态"),
        ("08_开工上下文.md", Path(r"D:\杰哥智能化系统\00杰哥系统总管\03数据\开工上下文\新对话先读这个.md"), "全局开工上下文"),
        ("09_施工接续卡片.md", Path(r"D:\杰哥智能化系统\00杰哥系统总管\03数据\施工接续\施工接续卡片_最新.md"), "系统总管接续记录"),
        ("10_可信IP放行后最终验收包.md", root / "03数据" / "154可信IP放行后最终验收包" / "股票系统可信IP放行后最终验收包_最新.md", "企业微信可信IP放行后的最终复测步骤"),
        ("11_当前施工面板.md", Path(r"D:\杰哥智能化系统\00杰哥系统总管\07文档\当前施工面板.md"), "当前施工状态面板"),
        ("12_可信IP状态监测.md", root / "03数据" / "155可信IP状态监测" / "股票系统可信IP状态监测_最新.md", "当前可信IP阻断状态和需放行IP"),
        ("13_日常一键运行记录.md", root / "03数据" / "156日常一键运行" / "股票系统日常一键运行_最新.md", "一键日常运行控制器最近执行记录"),
    ]

    manifest_items: list[dict[str, Any]] = []
    for arcname, source, desc in files:
        info = file_info(source)
        manifest_items.append({
            "包内路径": arcname,
            "源路径": str(source),
            "说明": desc,
            "存在": info["存在"],
            "大小": info["大小"],
            "更新时间": info["更新时间"],
        })

    manifest = {
        "名称": "股票系统AI接手压缩包",
        "版本": "2026-05-01",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "生成股票系统AI接手压缩包.py",
        "用途": "交给另一个AI读取，实现股票系统最小上下文接手。",
        "文件数量": len(manifest_items),
        "存在文件数量": sum(1 for item in manifest_items if item["存在"]),
        "文件清单": manifest_items,
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否修改旧系统": False,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    readme = build_readme(manifest)
    write_json(latest_manifest, manifest)
    write_text(latest_readme, readme)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("00_压缩包说明.md", readme)
        zf.writestr("00_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for arcname, source, _desc in files:
            if source.exists():
                zf.write(source, arcname=arcname)

    if latest_zip.exists():
        latest_zip.unlink()
    latest_zip.write_bytes(zip_path.read_bytes())
    bat = write_entry_open_bat(root, latest_zip)

    print(json.dumps({
        "状态": "完成",
        "压缩包": str(latest_zip),
        "说明": str(latest_readme),
        "入口工具": str(bat),
        "存在文件数量": manifest["存在文件数量"],
        "文件数量": manifest["文件数量"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
