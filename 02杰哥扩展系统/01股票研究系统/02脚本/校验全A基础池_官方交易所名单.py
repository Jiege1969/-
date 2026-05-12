# -*- coding: utf-8 -*-
"""
名称：校验全A基础池_官方交易所名单.py
作用：用上交所、深交所、北交所官方股票名单校验全A基础股票池，最终以官方名单为准。
边界：只读官方公开名单与本地全A基础池，写校验报告；不触发n8n；不发送企业微信；不接券商；不交易。
"""

from __future__ import annotations

import contextlib
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(code: Any, market: str = "") -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.lower()
        if suffix == "sh":
            return f"sh{num.zfill(6)}"
        if suffix == "sz":
            return f"sz{num.zfill(6)}"
        if suffix == "bj":
            return f"bj{num.zfill(6)}"
    if text.isdigit():
        text = text.zfill(6)
        if market == "北交所" or text.startswith(("4", "8", "920")):
            return f"bj{text}"
        if market == "上交所" or text.startswith(("6", "9")):
            return f"sh{text}"
        return f"sz{text}"
    return text


def df_col(row: Any, names: list[str], fallback_index: int | None = None) -> Any:
    for name in names:
        try:
            value = row.get(name)
        except AttributeError:
            value = None
        if value not in (None, ""):
            return value
    if fallback_index is not None:
        try:
            return row.iloc[fallback_index]
        except Exception:
            return None
    return None


def fetch_official_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import akshare as ak  # type: ignore

    official: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        sh_main = ak.stock_info_sh_name_code(symbol="主板A股")
        sh_star = ak.stock_info_sh_name_code(symbol="科创板")
        sz = ak.stock_info_sz_name_code(symbol="A股列表")
        bj = ak.stock_info_bj_name_code()

    for source_name, market, board, df in [
        ("上交所官方股票列表-主板A股", "上交所", "主板", sh_main),
        ("上交所官方股票列表-科创板", "上交所", "科创板", sh_star),
        ("深交所官方股票列表-A股", "深交所", "", sz),
        ("北交所官方股票列表", "北交所", "北交所", bj),
    ]:
        source_counts[source_name] = int(len(df))
        for _, row in df.iterrows():
            raw_code = df_col(row, ["证券代码", "A股代码", "代码"], 0)
            code = normalize_code(raw_code, market)
            name = str(df_col(row, ["证券简称", "A股简称", "名称"], 1) or "").strip()
            row_board = str(df_col(row, ["板块"], None) or board or "")
            if not row_board:
                row_board = "创业板" if code.startswith("sz3") else "主板"
            if code and name:
                official.append({
                    "代码": code,
                    "展示代码": display_code(code),
                    "名称": name,
                    "市场": market,
                    "板块": row_board,
                    "官方来源": source_name,
                })
    meta = {
        "官方来源": [
            "上交所官方股票列表-主板A股",
            "上交所官方股票列表-科创板",
            "深交所官方股票列表-A股",
            "北交所官方股票列表",
        ],
        "来源数量": source_counts,
        "官方去重数量": len({row["代码"] for row in official}),
    }
    return official, meta


def display_code(code: str) -> str:
    if code.startswith("sh"):
        return f"{code[2:]}.SH"
    if code.startswith("sz"):
        return f"{code[2:]}.SZ"
    if code.startswith("bj"):
        return f"{code[2:]}.BJ"
    return code.upper()


def market_count(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        market = str(row.get("市场") or "未知")
        counts[market] = counts.get(market, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 全A基础池官方交易所名单校验",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 严重问题数：{len(report['严重问题'])}",
        "",
        "## 核心计数",
        "",
    ]
    for key, value in report["核心计数"].items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 官方来源", ""])
    for key, value in report["官方来源"].get("来源数量", {}).items():
        lines.append(f"- {key}：{value}")
    lines.extend(["", "## 严重问题", ""])
    if report["严重问题"]:
        for item in report["严重问题"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 口径声明", ""])
    for item in report["口径声明"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> int:
    root = module_root()
    full_a_path = root / "03数据" / "01股票池" / "全A基础股票池_最新.json"
    output_dir = root / "03数据" / "01股票池"
    full_a = load_json(full_a_path)
    full_rows = list(full_a.get("股票池", []))
    local_by_code = {normalize_code(row.get("代码"), str(row.get("市场") or "")): row for row in full_rows}

    official_rows, official_meta = fetch_official_rows()
    official_by_code = {row["代码"]: row for row in official_rows}
    local_codes = set(local_by_code)
    official_codes = set(official_by_code)
    missing_official = sorted(official_codes - local_codes)
    extra_local = sorted(local_codes - official_codes)

    severe: list[str] = []
    if missing_official:
        severe.append(f"全A基础池缺少官方名单股票：{len(missing_official)}")
    if extra_local:
        severe.append(f"全A基础池存在官方名单外股票：{len(extra_local)}")
    if len(official_codes) < 5000:
        severe.append(f"官方交易所名单数量异常偏低：{len(official_codes)}")

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not severe else "阻断",
        "严重问题": severe,
        "核心计数": {
            "本地全A基础池数量": len(local_codes),
            "官方交易所名单数量": len(official_codes),
            "官方名单缺失于本地": len(missing_official),
            "本地多出官方名单外": len(extra_local),
            "本地市场统计": market_count(full_rows),
            "官方市场统计": market_count(official_rows),
        },
        "官方来源": official_meta,
        "差异样本": {
            "官方有本地缺": [official_by_code[code] for code in missing_official[:50]],
            "本地有官方缺": [local_by_code[code] for code in extra_local[:50]],
        },
        "口径声明": [
            "全A公开来源只用于建池发现、历史补齐和覆盖检查，不作为长期正式行情源。",
            "股票是否属于全A基础池，最终以上交所、深交所、北交所官方公开名单为准。",
            "日常行情与财报等增量数据，后续必须走已搭建的官方/可靠实时渠道，并保留多源复核与降级标记。",
        ],
        "输入": {
            "全A基础股票池": str(full_a_path),
        },
        "安全边界": {
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
        },
    }
    json_path = output_dir / "全A基础池官方校验_最新.json"
    md_path = output_dir / "全A基础池官方校验_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "严重问题数": len(severe),
        "本地全A基础池数量": len(local_codes),
        "官方交易所名单数量": len(official_codes),
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if not severe else 1


if __name__ == "__main__":
    raise SystemExit(main())
