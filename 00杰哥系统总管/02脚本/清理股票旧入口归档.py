# -*- coding: utf-8 -*-
"""
名称：清理股票旧入口归档.py
作用：删除已被当前入口工具替代的桌面 bat 归档目录，并清理停用 AI 接手包中的旧 zip 副本。
触发方式：python 清理股票旧入口归档.py
依赖：Python 标准库。
所属系统：00杰哥系统总管
安全边界：只处理股票系统已停用入口归档；不删除当前 05入口工具 下的现役 bat；不删除 AI 接手包最新说明和最新 zip；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
创建/修改记录：2026-05-06 创建股票旧入口归档清理入口。
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
MANAGER = ROOT / "00杰哥系统总管"
STOCK = ROOT / "02杰哥扩展系统" / "01股票研究系统"
OUT_DIR = MANAGER / "03数据" / "运行状态"
LOG_DIR = MANAGER / "04日志" / "清债执行"

BAT_ARCHIVE_DIRS = [
    STOCK / "05入口工具" / "桌面bat归档_20260502_073720",
    STOCK / "05入口工具" / "桌面bat归档_二次回潮_20260502_0825",
    STOCK / "05入口工具" / "桌面bat归档_源码收口后补充",
]

AI_PACKAGE_DIR = STOCK / "09归档" / "AI接手包_停用归档_20260502_084024" / "152AI接手压缩包"
TIMESTAMP_ZIP_RE = re.compile(r"股票系统AI接手压缩包_\d{8}_\d{6}\.zip$")


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S +08:00")


def dir_stats(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"路径": str(path), "存在": False, "文件数": 0, "目录数": 0, "字节": 0}
    files = [item for item in path.rglob("*") if item.is_file()]
    dirs = [item for item in path.rglob("*") if item.is_dir()]
    return {
        "路径": str(path),
        "存在": True,
        "文件数": len(files),
        "目录数": len(dirs),
        "字节": sum(item.stat().st_size for item in files),
    }


def delete_dir(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    allowed_parent = (STOCK / "05入口工具").resolve()
    if resolved.parent != allowed_parent or "桌面bat归档" not in resolved.name:
        raise RuntimeError(f"拒绝删除非桌面bat归档目录：{resolved}")
    stats = dir_stats(resolved)
    shutil.rmtree(resolved)
    return stats


def delete_file(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved.parent != AI_PACKAGE_DIR.resolve() or not TIMESTAMP_ZIP_RE.match(resolved.name):
        raise RuntimeError(f"拒绝删除非AI接手包旧zip：{resolved}")
    size = resolved.stat().st_size
    resolved.unlink()
    return {"路径": str(resolved), "字节": size}


def build_report() -> dict[str, Any]:
    before_dirs = [dir_stats(path) for path in BAT_ARCHIVE_DIRS]
    deleted_dirs = [delete_dir(path) for path in BAT_ARCHIVE_DIRS if path.exists()]
    old_zips = [
        item for item in AI_PACKAGE_DIR.glob("*.zip")
        if item.is_file() and TIMESTAMP_ZIP_RE.match(item.name)
    ] if AI_PACKAGE_DIR.exists() else []
    deleted_zips = [delete_file(path) for path in old_zips]
    latest_zip = AI_PACKAGE_DIR / "股票系统AI接手压缩包_最新.zip"
    latest_md = AI_PACKAGE_DIR / "股票系统AI接手压缩包_说明_最新.md"
    latest_json = AI_PACKAGE_DIR / "股票系统AI接手压缩包_最新.json"
    failures = []
    for keep in [latest_zip, latest_md, latest_json]:
        if not keep.exists():
            failures.append(f"应保留资产缺失：{keep}")
    return {
        "名称": "股票旧入口归档清理",
        "执行时间": now_text(),
        "当前结论": "通过" if not failures else "未通过",
        "清理前桌面bat归档": before_dirs,
        "删除桌面bat归档目录": deleted_dirs,
        "删除桌面bat归档目录数量": len(deleted_dirs),
        "删除AI接手包旧zip": deleted_zips,
        "删除AI接手包旧zip数量": len(deleted_zips),
        "删除总数量": len(deleted_dirs) + len(deleted_zips),
        "删除总字节": sum(item.get("字节", 0) for item in deleted_dirs) + sum(item.get("字节", 0) for item in deleted_zips),
        "保留AI接手包资产": [str(latest_zip), str(latest_md), str(latest_json)],
        "失败": failures,
        "安全边界": {
            "未删除当前现役bat": True,
            "保留AI接手包最新资产": True,
            "未触发n8n": True,
            "未发送企业微信": True,
            "未调用券商接口": True,
            "未自动交易": True,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 股票旧入口归档清理",
        "",
        f"- 执行时间：{report['执行时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 删除桌面bat归档目录数量：{report['删除桌面bat归档目录数量']}",
        f"- 删除AI接手包旧zip数量：{report['删除AI接手包旧zip数量']}",
        f"- 删除总字节：{report['删除总字节']}",
        "",
        "## 删除桌面bat归档目录",
    ]
    if report["删除桌面bat归档目录"]:
        lines.extend([f"- `{item['路径']}`：{item['文件数']} 文件，{item['字节']} 字节" for item in report["删除桌面bat归档目录"]])
    else:
        lines.append("- 无。")
    lines.extend(["", "## 删除AI接手包旧zip"])
    if report["删除AI接手包旧zip"]:
        lines.extend([f"- `{item['路径']}`：{item['字节']} 字节" for item in report["删除AI接手包旧zip"]])
    else:
        lines.append("- 无。")
    lines.extend(["", "## 保留资产"])
    lines.extend([f"- `{item}`" for item in report["保留AI接手包资产"]])
    lines.extend([
        "",
        "## 安全边界",
        "- 未删除当前现役 bat；保留 AI 接手包最新资产；未触发 n8n；未发送企业微信；未调用券商接口；未自动交易。",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    text = json.dumps(report, ensure_ascii=False, indent=2)
    (OUT_DIR / "股票旧入口归档清理_最新.json").write_text(text, encoding="utf-8")
    (LOG_DIR / "stock-old-entry-archive-cleanup-最新.json").write_text(text, encoding="utf-8")
    (OUT_DIR / "股票旧入口归档清理_最新.md").write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({
        "状态": report["当前结论"],
        "删除目录": report["删除桌面bat归档目录数量"],
        "删除旧zip": report["删除AI接手包旧zip数量"],
        "删除字节": report["删除总字节"],
        "输出": str(OUT_DIR / "股票旧入口归档清理_最新.md"),
    }, ensure_ascii=False))
    return 0 if report["当前结论"] == "通过" else 1


if __name__ == "__main__":
    raise SystemExit(main())
