# -*- coding: utf-8 -*-
"""
名称：验证重点关注池历史K线脚本东方财富增强改造.py
作用：验收正式历史K线生成脚本是否并入东方财富增强请求头和重试机制，且本轮未运行刷新、未覆盖最新快照。
安全边界：只读源码、227影子快照和正式历史K线最新快照；只写232验收报告；不联网、不刷新历史K线、不发送企业微信、不触发 n8n、不交易。
"""

from __future__ import annotations

import hashlib
import json
import py_compile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "03数据" / "232历史K线正式脚本东方财富增强验收"
HISTORY_SCRIPT = ROOT / "02脚本" / "生成重点关注池历史K线快照.py"
SHADOW_227 = ROOT / "03数据" / "227历史K线东方财富增强影子快照" / "历史K线东方财富增强影子快照_最新.json"
SHADOW_227_VERIFY = ROOT / "03数据" / "227历史K线东方财富增强影子快照" / "历史K线东方财富增强影子快照验收_最新.json"
FORMAL_HISTORY_LATEST = ROOT / "03数据" / "11历史行情" / "重点关注池历史K线快照_最新.json"


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


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {"检查项": name, "通过": bool(condition), "说明": detail}


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 重点关注池历史K线脚本东方财富增强改造验收",
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
    source = read_text(HISTORY_SCRIPT)
    shadow = load_json(SHADOW_227)
    shadow_verify = load_json(SHADOW_227_VERIFY)
    formal = load_json(FORMAL_HISTORY_LATEST)
    compile_ok = True
    compile_error = ""
    try:
        py_compile.compile(str(HISTORY_SCRIPT), doraise=True)
    except Exception as exc:  # noqa: BLE001
        compile_ok = False
        compile_error = str(exc)
    formal_sources = sorted({str(item.get("数据源", "")) for item in formal.get("历史K线", []) or []})
    checks = [
        check(HISTORY_SCRIPT.exists(), "历史K线正式生成脚本存在", str(HISTORY_SCRIPT)),
        check(compile_ok, "历史K线正式生成脚本编译通过", compile_error),
        check("code_with_market" in source and "Referer" in source and "quote.eastmoney.com" in source, "东方财富Referer请求头已加入", ""),
        check("Accept" in source and "Connection" in source and "close" in source, "Accept和Connection请求头已加入", ""),
        check("for attempt in range(1, 4)" in source and "time.sleep" in source, "东方财富3次短间隔重试已加入", ""),
        check("parts[6]" in source and '"成交额": to_float(parts[6])' in source, "东方财富成交额字段仍从parts[6]解析", ""),
        check("fetch_tencent_kline" in source and "腾讯历史K线" in source, "腾讯兜底仍保留", ""),
        check(shadow_verify.get("结论") == "通过", "227东方财富增强影子快照验收通过", str(shadow_verify.get("结论"))),
        check(shadow.get("汇总", {}).get("成功数量") == shadow.get("汇总", {}).get("股票数量"), "227影子快照全量成功支撑本次改造", json.dumps(shadow.get("汇总", {}), ensure_ascii=False)),
        check("腾讯历史K线" in formal_sources, "本轮未运行刷新，正式最新快照仍保持原状态", json.dumps(formal_sources, ensure_ascii=False)),
    ]
    failed = [item for item in checks if not item["通过"]]
    now = datetime.now()
    report = {
        "名称": "重点关注池历史K线脚本东方财富增强改造验收",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failed else "失败",
        "通过数量": len(checks) - len(failed),
        "失败数量": len(failed),
        "历史K线脚本sha256": sha256(HISTORY_SCRIPT),
        "正式最新快照来源集合": formal_sources,
        "检查结果": checks,
        "安全边界": {
            "联网请求": False,
            "运行历史K线刷新": False,
            "覆盖历史K线最新快照": False,
            "修改220口径": False,
            "修改221短文": False,
            "修改222影子分支": False,
            "发送企业微信": False,
            "触发n8n": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    latest_json = OUT_DIR / "重点关注池历史K线脚本东方财富增强改造验收_最新.json"
    latest_md = OUT_DIR / "重点关注池历史K线脚本东方财富增强改造验收_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "通过数量": report["通过数量"],
        "失败数量": report["失败数量"],
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
