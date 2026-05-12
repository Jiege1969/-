# -*- coding: utf-8 -*-
"""
名称：采集全A历史日线_中信本机只读.py
作用：只读解析本机中信证券通达信 vipdoc 日线文件，建立券商本机原始日线补充库。
边界：只读本机文件；不登录；不触发交易；不调用券商接口；不修改中信证券软件目录。
定位：券商授权本机辅助源，用于补缺和交叉校验；不直接覆盖正式前复权历史库。
"""

from __future__ import annotations

import argparse
import json
import struct
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


DEFAULT_TDX_ROOT = Path(r"F:\股票工具\中信证券")


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_end_date() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.lower()
        if suffix in {"sh", "sz", "bj"}:
            return f"{suffix}{num.zfill(6)}"
    if text.isdigit():
        text = text.zfill(6)
        if text.startswith(("4", "8", "920")):
            return f"bj{text}"
        if text.startswith(("6", "9")):
            return f"sh{text}"
        return f"sz{text}"
    return text


def display_code(code: str) -> str:
    if code.startswith("sh"):
        return f"{code[2:]}.SH"
    if code.startswith("sz"):
        return f"{code[2:]}.SZ"
    if code.startswith("bj"):
        return f"{code[2:]}.BJ"
    return code.upper()


def tdx_market(code: str) -> str:
    norm = normalize_code(code)
    if norm.startswith("bj"):
        return "bj"
    if norm.startswith("sh"):
        return "sh"
    return "sz"


def tdx_day_file(tdx_root: Path, code: str) -> Path:
    norm = normalize_code(code)
    market = tdx_market(norm)
    return tdx_root / "vipdoc" / market / "lday" / f"{norm}.day"


def output_file(output_dir: Path, code: str) -> Path:
    norm = normalize_code(code)
    return output_dir / "按股票" / tdx_market(norm) / f"{norm}.json"


def date_int_to_text(value: int) -> str:
    text = str(value)
    if len(text) == 8:
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"
    return text


def parse_tdx_day(path: Path, start: str, end: str) -> list[dict[str, Any]]:
    start_i = int(start.replace("-", ""))
    end_i = int(end.replace("-", ""))
    data = path.read_bytes()
    rows: list[dict[str, Any]] = []
    previous_close: float | None = None
    for offset in range(0, len(data) - 31, 32):
        date_i, open_i, high_i, low_i, close_i, amount_f, volume_i, _reserved = struct.unpack(
            "<IIIIIfII", data[offset:offset + 32]
        )
        if date_i < start_i or date_i > end_i:
            continue
        open_p = round(open_i / 100.0, 4)
        high_p = round(high_i / 100.0, 4)
        low_p = round(low_i / 100.0, 4)
        close_p = round(close_i / 100.0, 4)
        pct = None
        diff = None
        amplitude = None
        if previous_close:
            diff = round(close_p - previous_close, 4)
            pct = round(diff / previous_close * 100, 4)
            amplitude = round((high_p - low_p) / previous_close * 100, 4)
        previous_close = close_p
        rows.append({
            "日期": date_int_to_text(date_i),
            "开盘": open_p,
            "收盘": close_p,
            "最高": high_p,
            "最低": low_p,
            "成交量": round(volume_i / 100.0, 2),
            "成交额": round(float(amount_f), 2),
            "成交额是否估算": False,
            "振幅": amplitude,
            "涨跌幅": pct,
            "涨跌额": diff,
            "换手率": None,
            "成交量单位": "手",
            "成交额单位": "元",
            "本机源价格口径": "不复权原始价",
        })
    return rows


def existing_is_fresh(path: Path, end: str) -> bool:
    if not path.exists():
        return False
    try:
        data = load_json(path)
    except Exception:  # noqa: BLE001
        return False
    return str(data.get("采集范围", {}).get("结束", "")) >= end and data.get("记录数", 0) > 0


def build_record(stock: dict[str, Any], rows: list[dict[str, Any]], source_path: Path, start: str, end: str) -> dict[str, Any]:
    code = normalize_code(stock.get("代码"))
    return {
        "代码": code,
        "展示代码": stock.get("展示代码") or display_code(code),
        "名称": stock.get("名称", ""),
        "市场": stock.get("市场", ""),
        "板块": stock.get("板块", ""),
        "行业": stock.get("行业", ""),
        "采集时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "采集范围": {"开始": start, "结束": end},
        "复权": "不复权原始价",
        "数据源": "中信证券本机通达信日线文件",
        "源文件": str(source_path),
        "官方校验状态": "全A基础池官方校验已通过后只读采集",
        "记录数": len(rows),
        "首日": rows[0].get("日期") if rows else "",
        "末日": rows[-1].get("日期") if rows else "",
        "日线": rows,
        "安全边界": {
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否修改中信目录": False,
            "是否交易": False,
            "是否自动发送": False,
        },
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 中信证券本机日线只读采集批次报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 本批目标数量：{report['本批目标数量']}",
        f"- 成功：{report['成功数量']}",
        f"- 跳过：{report['跳过数量']}",
        f"- 失败：{report['失败数量']}",
        f"- 输出目录：{report['输出目录']}",
        "",
        "## 口径",
        "",
        "- 本脚本只读本机中信证券 vipdoc 日线文件，不登录、不交易、不修改券商目录。",
        "- 本机 .day 日线按不复权原始价归档，独立于正式前复权历史库。",
        "- 该数据源用于补缺、校验和北交所历史日线补强，不能单独作为最终官方口径。",
        "",
        "## 失败样本",
        "",
    ]
    failed = [item for item in report.get("明细", []) if item.get("状态") == "失败"]
    if failed:
        for item in failed[:50]:
            lines.append(f"- {item.get('代码')} {item.get('名称')}：{item.get('原因')}")
    else:
        lines.append("- 无")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="只读采集中信证券本机通达信日线")
    parser.add_argument("--tdx-root", default=str(DEFAULT_TDX_ROOT), help="中信证券软件根目录")
    parser.add_argument("--start", default="19900101", help="开始日期，YYYYMMDD")
    parser.add_argument("--end", default=default_end_date(), help="结束日期，YYYYMMDD；默认上一自然日")
    parser.add_argument("--market", choices=["all", "sh", "sz", "bj"], default="all", help="按市场分批")
    parser.add_argument("--offset", type=int, default=0, help="从筛选后的全A基础池第几只开始")
    parser.add_argument("--limit", type=int, default=20, help="本批采集数量")
    parser.add_argument("--codes", default="", help="指定代码，逗号分隔；指定后忽略offset")
    parser.add_argument("--force", action="store_true", help="即使本地已有文件也重新解析")
    args = parser.parse_args()

    root = module_root()
    full_a_path = root / "03数据" / "01股票池" / "全A基础股票池_最新.json"
    official_path = root / "03数据" / "01股票池" / "全A基础池官方校验_最新.json"
    output_dir = root / "03数据" / "013券商本机历史日线" / "中信证券"
    tdx_root = Path(args.tdx_root)

    full_a = load_json(full_a_path)
    official = load_json(official_path)
    if official.get("结论") != "通过":
        raise RuntimeError("全A基础池官方校验未通过，禁止建立本机券商补充库")
    if not (tdx_root / "vipdoc").exists():
        raise RuntimeError(f"未找到中信证券vipdoc目录：{tdx_root}")

    all_stocks = list(full_a.get("股票池", []))
    if args.market != "all":
        all_stocks = [stock for stock in all_stocks if normalize_code(stock.get("代码")).startswith(args.market)]
    by_code = {normalize_code(stock.get("代码")): stock for stock in all_stocks}
    if args.codes.strip():
        targets = [by_code.get(normalize_code(code), {"代码": normalize_code(code), "名称": ""}) for code in args.codes.split(",") if code.strip()]
    else:
        targets = all_stocks[args.offset:args.offset + args.limit]

    success = 0
    skipped = 0
    failed = 0
    details: list[dict[str, Any]] = []
    for stock in targets:
        code = normalize_code(stock.get("代码"))
        source_path = tdx_day_file(tdx_root, code)
        out_path = output_file(output_dir, code)
        if not source_path.exists():
            failed += 1
            details.append({"代码": code, "名称": stock.get("名称", ""), "状态": "失败", "原因": f"缺少源文件:{source_path}"})
            continue
        if not args.force and existing_is_fresh(out_path, args.end):
            skipped += 1
            details.append({"代码": code, "名称": stock.get("名称", ""), "状态": "跳过", "原因": "本机补充库已有新鲜文件"})
            continue
        try:
            rows = parse_tdx_day(source_path, args.start, args.end)
            if not rows:
                raise RuntimeError("源文件无目标日期范围内记录")
            record = build_record(stock, rows, source_path, args.start, args.end)
            write_json(out_path, record)
            success += 1
            details.append({
                "代码": code,
                "名称": stock.get("名称", ""),
                "状态": "成功",
                "记录数": len(rows),
                "首日": record["首日"],
                "末日": record["末日"],
                "输出": str(out_path),
            })
        except Exception as exc:  # noqa: BLE001
            failed += 1
            details.append({"代码": code, "名称": stock.get("名称", ""), "状态": "失败", "原因": str(exc)})

    report = {
        "名称": "中信证券本机日线只读采集批次报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if failed == 0 and (success + skipped) > 0 else "需复核",
        "中信证券目录": str(tdx_root),
        "输出目录": str(output_dir),
        "采集范围": {"开始": args.start, "结束": args.end},
        "市场": args.market,
        "本批目标数量": len(targets),
        "成功数量": success,
        "跳过数量": skipped,
        "失败数量": failed,
        "明细": details,
        "安全边界": {
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否修改中信目录": False,
            "是否交易": False,
            "是否自动发送": False,
        },
    }
    json_path = output_dir / "中信证券本机日线采集批次报告_最新.json"
    md_path = output_dir / "中信证券本机日线采集批次报告_最新.md"
    write_json(json_path, report)
    write_text(md_path, build_markdown(report))
    print(json.dumps({
        "状态": report["结论"],
        "本批目标数量": len(targets),
        "成功数量": success,
        "跳过数量": skipped,
        "失败数量": failed,
        "报告": str(md_path),
        "数据": str(json_path),
    }, ensure_ascii=False))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
