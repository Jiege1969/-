# -*- coding: utf-8 -*-
"""
名称：执行P4低风险Python缓存真实清理.py
作用：执行 P4 中最低风险的 Python 缓存真实清理，仅删除 P1 影子清单中无引用、无保护命中、源脚本存在的 .pyc/.pyo 缓存。
安全边界：只处理可再生成 Python 缓存；不删除草稿、日志、历史产物、配置、备份、入口、脚本源码、数据库、模型、n8n、凭据；不移动、不压缩、不归档、不合并脚本、不替换入口。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
P1_REPORT = OUT_DIR / "P1可清理候选引用检查与影子删除清单_最新.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def in_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def is_safe_cache_candidate(item: dict[str, Any]) -> bool:
    path = Path(item.get("路径", ""))
    suffix = path.suffix.lower()
    return (
        item.get("可进入影子删除清单") is True
        and item.get("类型") == "Python缓存"
        and item.get("源脚本存在") is True
        and item.get("引用命中数量", 0) == 0
        and item.get("保护命中") is False
        and suffix in {".pyc", ".pyo"}
        and "__pycache__" in str(path)
        and in_root(path)
    )


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P4低风险Python缓存真实清理执行报告",
        "",
        f"- 执行时间：{report['执行时间']}",
        f"- 当前结论：{report['当前结论']}",
        f"- 候选数量：{report['统计']['候选数量']}",
        f"- 成功删除：{report['统计']['成功删除数量']}",
        f"- 已不存在：{report['统计']['已不存在数量']}",
        f"- 失败数量：{report['统计']['失败数量']}",
        f"- 释放字节：{report['统计']['成功释放字节']}",
        "",
        "## 一、执行边界",
        "",
    ]
    for item in report["执行边界"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 二、成功删除样例", ""])
    for item in report["成功删除样例"]:
        lines.append(f"- `{item['相对路径']}`：{item['大小']} 字节")
    lines.extend(["", "## 三、失败样例", ""])
    for item in report["失败样例"]:
        lines.append(f"- `{item['相对路径']}`：{item['错误']}")
    lines.extend(["", "## 四、安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    now = datetime.now()
    p1 = load_json(P1_REPORT)
    items = p1.get("完整P1候选清单", [])
    candidates = [item for item in items if is_safe_cache_candidate(item)]

    deleted: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    for item in candidates:
        path = Path(item["路径"])
        card = {
            "路径": str(path),
            "相对路径": item.get("相对路径", str(path)),
            "大小": int(item.get("大小", 0) or 0),
            "源脚本": item.get("源脚本", ""),
        }
        if not path.exists():
            missing.append(card)
            continue
        try:
            path.unlink()
            deleted.append(card)
        except OSError as exc:
            card["错误"] = str(exc)
            failed.append(card)

    report = {
        "名称": "P4低风险Python缓存真实清理执行报告",
        "执行时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "依据文件": str(P1_REPORT),
        "当前结论": "已执行 P4 最低风险 Python 缓存真实清理；仅删除可再生成缓存文件，未处理草稿、日志、历史产物、脚本源码、配置、备份或入口。",
        "统计": {
            "候选数量": len(candidates),
            "成功删除数量": len(deleted),
            "已不存在数量": len(missing),
            "失败数量": len(failed),
            "成功释放字节": sum(item["大小"] for item in deleted),
        },
        "执行边界": [
            "只删除 P1 影子清单中类型为 Python缓存 的 `.pyc/.pyo` 文件。",
            "必须满足可进入影子删除清单、源脚本存在、引用命中数量为 0、保护命中为 False。",
            "路径必须位于 `D:\\杰哥智能化系统` 下且包含 `__pycache__`。",
            "不删除草稿、日志、历史产物、脚本源码、配置、备份、入口、数据库、模型、n8n、凭据。",
            "回滚方式为重新运行对应 Python 源脚本或相关验收，缓存会按需再生成。",
        ],
        "成功删除样例": deleted[:80],
        "失败样例": failed[:80],
        "已不存在样例": missing[:40],
        "完整成功删除清单": deleted,
        "完整失败清单": failed,
        "安全边界": {
            "删除Python缓存": True,
            "删除草稿": False,
            "删除日志": False,
            "删除历史产物": False,
            "删除脚本源码": False,
            "移动文件": False,
            "压缩文件": False,
            "真实归档": False,
            "合并脚本": False,
            "替换入口": False,
            "修改计划任务": False,
            "重启服务": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }

    latest_json = OUT_DIR / "P4低风险Python缓存真实清理执行报告_最新.json"
    latest_md = OUT_DIR / "P4低风险Python缓存真实清理执行报告_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))

    print(json.dumps({
        "状态": "完成" if not failed else "部分失败",
        "候选数量": len(candidates),
        "成功删除数量": len(deleted),
        "已不存在数量": len(missing),
        "失败数量": len(failed),
        "成功释放字节": report["统计"]["成功释放字节"],
        "输出": {"json": str(latest_json), "markdown": str(latest_md)},
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
