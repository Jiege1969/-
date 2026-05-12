# -*- coding: utf-8 -*-
"""
名称：验证P4低风险Python缓存真实清理.py
作用：验收 P4 最低风险 Python 缓存真实清理结果和安全边界。
安全边界：只读执行报告和已删除路径状态；只写验收报告；不再执行删除。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"D:\杰哥智能化系统")
OUT_DIR = ROOT / "00杰哥系统总管" / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "P4低风险Python缓存真实清理执行报告_最新.json"
REPORT_MD = OUT_DIR / "P4低风险Python缓存真实清理执行报告_最新.md"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# P4低风险Python缓存真实清理验收",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 通过数量：{report['通过数量']}",
        f"- 失败数量：{report['失败数量']}",
        "",
        "## 检查结果",
        "",
    ]
    for item in report["检查结果"]:
        mark = "通过" if item["通过"] else "失败"
        lines.append(f"- {item['检查项']}：{mark}。{item.get('说明', '')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    data = load_json(REPORT_JSON)
    md = read_text(REPORT_MD)
    text = json.dumps(data, ensure_ascii=False) + "\n" + md
    stats = data.get("统计", {})
    safety = data.get("安全边界", {})
    deleted = data.get("完整成功删除清单", [])
    failed = data.get("完整失败清单", [])
    still_exists = [item for item in deleted[:1000] if Path(item.get("路径", "")).exists()]
    bad_suffix = [item for item in deleted if Path(item.get("路径", "")).suffix.lower() not in {".pyc", ".pyo"}]
    outside_root = []
    for item in deleted:
        path = Path(item.get("路径", ""))
        try:
            path.resolve().relative_to(ROOT.resolve())
        except ValueError:
            outside_root.append(item)

    checks = [
        check(REPORT_JSON.exists() and REPORT_MD.exists(), "执行报告 JSON 和 Markdown 存在", str(OUT_DIR)),
        check(stats.get("候选数量", 0) > 0, "候选数量大于 0", json.dumps(stats, ensure_ascii=False)),
        check(stats.get("成功删除数量", 0) > 0, "成功删除数量大于 0", json.dumps(stats, ensure_ascii=False)),
        check(stats.get("失败数量", 0) == 0 and not failed, "失败数量为 0", json.dumps(stats, ensure_ascii=False)),
        check(stats.get("成功删除数量", 0) == len(deleted), "成功删除清单数量与统计一致", f"清单={len(deleted)}"),
        check(not still_exists, "抽查成功删除文件已不存在", f"仍存在={len(still_exists)}"),
        check(not bad_suffix, "删除对象仅限 .pyc/.pyo", f"异常={len(bad_suffix)}"),
        check(not outside_root, "删除对象均位于系统根目录内", f"异常={len(outside_root)}"),
        check("不删除草稿、日志、历史产物、脚本源码、配置、备份、入口" in text, "执行边界排除业务文件和源码", ""),
        check(safety.get("删除Python缓存") is True, "安全边界仅允许删除 Python 缓存", json.dumps(safety, ensure_ascii=False)),
        check(all(value is False for key, value in safety.items() if key != "删除Python缓存"), "其他安全边界全部为 False", json.dumps(safety, ensure_ascii=False)),
        check("自动交易" in safety and safety.get("自动交易") is False, "自动交易未触发", json.dumps(safety, ensure_ascii=False)),
    ]

    failed_checks = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "P4低风险Python缓存真实清理验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed_checks else "失败",
        "通过数量": len(checks) - len(failed_checks),
        "失败数量": len(failed_checks),
        "检查结果": checks,
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

    latest_json = OUT_DIR / "P4低风险Python缓存真实清理验收_最新.json"
    latest_md = OUT_DIR / "P4低风险Python缓存真实清理验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))

    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
