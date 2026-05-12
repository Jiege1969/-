# -*- coding: utf-8 -*-
"""
名称：生成01股票池初始种子_从重点关注快照.py
作用：纠正01股票池源头口径，生成真正的全A基础股票池，用于建池发现和历史数据补齐。
边界：只读取公开行情列表并写入股票系统03数据/01股票池；不触发n8n；不发送企业微信；不接券商；不交易。

说明：
旧版本曾用“重点关注池公开行情快照”生成所谓全市场扫描初始种子。
这会把重点池误当全市场根据地。现版本保留脚本名以承接既有调度，但产物内容已纠正为全A基础池。
本脚本生成的是发现源/建池源；最终名单必须通过交易所官方名单校验，后续日常行情不依赖本脚本来源。
"""

from __future__ import annotations

import csv
import contextlib
import io
import json
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


EASTMONEY_QUOTE_URL = "https://push2.eastmoney.com/api/qt/clist/get"
EASTMONEY_FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"
EASTMONEY_FIELDS = ",".join([
    "f12",   # 代码
    "f13",   # 市场代码
    "f14",   # 名称
    "f2",    # 最新价
    "f3",    # 涨跌幅
    "f4",    # 涨跌额
    "f5",    # 成交量，手
    "f6",    # 成交额，元
    "f15",   # 最高
    "f16",   # 最低
    "f17",   # 今开
    "f18",   # 昨收
    "f20",   # 总市值
    "f21",   # 流通市值
    "f8",    # 换手率
    "f9",    # 市盈率
    "f10",   # 量比
    "f100",  # 行业
])


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def to_number(value: Any) -> float | None:
    if value in (None, "", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_url_text(url: str, timeout: int = 30) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "application/json,text/plain,*/*",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        curl = Path(r"C:\Windows\System32\curl.exe")
        if not curl.exists():
            raise
        result = subprocess.run(
            [
                str(curl),
                "-L",
                "--max-time",
                str(timeout),
                "-A",
                "Mozilla/5.0",
                "-e",
                "https://quote.eastmoney.com/",
                url,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=timeout + 5,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"curl failed: {result.returncode}")
        return result.stdout


def eastmoney_url(page: int, page_size: int = 100) -> str:
    params = {
        "pn": page,
        "pz": page_size,
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": EASTMONEY_FS,
        "fields": EASTMONEY_FIELDS,
    }
    return f"{EASTMONEY_QUOTE_URL}?{urllib.parse.urlencode(params)}"


def normalize_code(raw_code: Any, market_code: Any = None) -> str:
    code = str(raw_code or "").strip()
    if not code:
        return ""
    lower = code.lower()
    if lower.startswith(("sh", "sz", "bj")):
        return lower
    if "." in code:
        num, suffix = code.split(".", 1)
        suffix = suffix.upper()
        if suffix == "SH":
            return f"sh{num}"
        if suffix == "SZ":
            return f"sz{num}"
        if suffix == "BJ":
            return f"bj{num}"
    if len(code) == 6 and code.isdigit():
        if code.startswith(("4", "8", "920")):
            return f"bj{code}"
        if str(market_code) == "1" or code.startswith(("6", "9")):
            return f"sh{code}"
        return f"sz{code}"
    return lower


def display_code(code: str) -> str:
    norm = normalize_code(code)
    if norm.startswith("sh"):
        return f"{norm[2:]}.SH"
    if norm.startswith("sz"):
        return f"{norm[2:]}.SZ"
    if norm.startswith("bj"):
        return f"{norm[2:]}.BJ"
    return str(code or "").upper()


def market_name(code: str) -> str:
    norm = normalize_code(code)
    if norm.startswith("sh"):
        return "上交所"
    if norm.startswith("sz"):
        return "深交所"
    if norm.startswith("bj"):
        return "北交所"
    return "未知"


def board_name(code: str) -> str:
    norm = normalize_code(code)
    num = norm[2:] if len(norm) >= 8 else norm
    if norm.startswith("bj"):
        return "北交所"
    if norm.startswith("sh") and num.startswith(("688", "689")):
        return "科创板"
    if norm.startswith("sz") and num.startswith(("300", "301")):
        return "创业板"
    return "主板"


def risk_flags(name: str) -> dict[str, bool]:
    text = str(name or "").upper()
    return {
        "是否ST": "ST" in text,
        "是否退市风险": "退" in text or "退市" in text,
    }


def fetch_eastmoney_full_a() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_reported: int | None = None
    page = 1
    page_size = 100
    max_pages = 100

    while page <= max_pages:
        text = fetch_url_text(eastmoney_url(page, page_size))
        payload = json.loads(text)
        data = payload.get("data") or {}
        diff = data.get("diff") or []
        total_reported = data.get("total", total_reported)
        if not diff:
            break

        for item in diff:
            code = normalize_code(item.get("f12"), item.get("f13"))
            if not code or code in seen:
                continue
            seen.add(code)
            name = str(item.get("f14") or "")
            flags = risk_flags(name)
            rows.append({
                "序号": len(rows) + 1,
                "代码": code,
                "展示代码": display_code(code),
                "名称": name,
                "市场": market_name(code),
                "板块": board_name(code),
                "行业": item.get("f100") or "未分类",
                "是否启用": True,
                "是否ST": flags["是否ST"],
                "是否退市风险": flags["是否退市风险"],
                "最新价": to_number(item.get("f2")),
                "涨跌幅": to_number(item.get("f3")),
                "涨跌额": to_number(item.get("f4")),
                "成交量": to_number(item.get("f5")),
                "成交额": to_number(item.get("f6")),
                "最高": to_number(item.get("f15")),
                "最低": to_number(item.get("f16")),
                "今开": to_number(item.get("f17")),
                "昨收": to_number(item.get("f18")),
                "总市值": to_number(item.get("f20")),
                "流通市值": to_number(item.get("f21")),
                "换手率": to_number(item.get("f8")),
                "市盈率": to_number(item.get("f9")),
                "量比": to_number(item.get("f10")),
                "成交量单位": "手",
                "成交额单位": "元",
                "数据源": "东方财富公开A股行情列表",
                "数据新鲜度": "生成时点公开行情",
            })

        if total_reported and page * page_size >= int(total_reported):
            break
        page += 1
        time.sleep(0.08)

    meta = {
        "来源": "东方财富公开A股行情列表",
        "接口": EASTMONEY_QUOTE_URL,
        "请求页数": page,
        "接口报告总数": total_reported,
        "实际去重数量": len(rows),
    }
    return rows, meta


def dataframe_col(row: Any, names: list[str], fallback_index: int | None = None) -> Any:
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


def fetch_akshare_full_a() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    import akshare as ak  # type: ignore

    # akshare部分接口会输出进度条；这里收口到内存，避免调度日志被进度刷屏。
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        base_df = ak.stock_info_a_code_name()
        spot_df = ak.stock_zh_a_spot()

    quote_map: dict[str, dict[str, Any]] = {}
    for _, row in spot_df.iterrows():
        code = normalize_code(dataframe_col(row, ["代码", "code"], 0))
        if not code:
            continue
        raw_volume = to_number(dataframe_col(row, ["成交量"], None))
        quote_map[code] = {
            "最新价": to_number(dataframe_col(row, ["最新价"], None)),
            "涨跌额": to_number(dataframe_col(row, ["涨跌额"], None)),
            "涨跌幅": to_number(dataframe_col(row, ["涨跌幅"], None)),
            "成交量": round(raw_volume / 100, 2) if raw_volume is not None else None,
            "成交额": to_number(dataframe_col(row, ["成交额"], None)),
            "最高": to_number(dataframe_col(row, ["最高"], None)),
            "最低": to_number(dataframe_col(row, ["最低"], None)),
            "今开": to_number(dataframe_col(row, ["今开"], None)),
            "昨收": to_number(dataframe_col(row, ["昨收"], None)),
            "行情时间": dataframe_col(row, ["时间戳"], None),
        }

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for _, row in base_df.iterrows():
        code = normalize_code(dataframe_col(row, ["code", "代码"], 0))
        name = str(dataframe_col(row, ["name", "名称"], 1) or "").strip()
        if not code or not name or code in seen:
            continue
        seen.add(code)
        quote = quote_map.get(code, {})
        flags = risk_flags(name)
        rows.append({
            "序号": len(rows) + 1,
            "代码": code,
            "展示代码": display_code(code),
            "名称": name,
            "市场": market_name(code),
            "板块": board_name(code),
            "行业": "未分类",
            "是否启用": True,
            "是否ST": flags["是否ST"],
            "是否退市风险": flags["是否退市风险"],
            "最新价": quote.get("最新价"),
            "涨跌幅": quote.get("涨跌幅"),
            "涨跌额": quote.get("涨跌额"),
            "成交量": quote.get("成交量"),
            "成交额": quote.get("成交额"),
            "最高": quote.get("最高"),
            "最低": quote.get("最低"),
            "今开": quote.get("今开"),
            "昨收": quote.get("昨收"),
            "总市值": None,
            "流通市值": None,
            "换手率": None,
            "市盈率": None,
            "量比": None,
            "成交量单位": "手",
            "成交额单位": "元",
            "数据源": "AKShare公开A股基础列表+公开实时行情",
            "数据新鲜度": "生成时点公开行情",
            "行情时间": quote.get("行情时间") or now_text(),
        })

    meta = {
        "来源": "AKShare公开A股基础列表+公开实时行情",
        "基础列表接口": "stock_info_a_code_name",
        "行情接口": "stock_zh_a_spot",
        "基础列表数量": int(len(base_df)),
        "行情数量": int(len(spot_df)),
        "实际去重数量": len(rows),
        "行情匹配数量": len([row for row in rows if row.get("最新价") is not None]),
        "备用源": "东方财富公开A股行情列表",
    }
    return rows, meta


def summarize_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field) or "未知")
        result[key] = result.get(key, 0) + 1
    return dict(sorted(result.items(), key=lambda kv: (-kv[1], kv[0])))


def build_report(rows: list[dict[str, Any]], source_meta: dict[str, Any]) -> dict[str, Any]:
    generated = now_text()
    for row in rows:
        row["本池生成时间"] = generated
    return {
        "名称": "全A基础股票池",
        "定位": "股票研究系统的全市场根据地，覆盖公开A股基础列表；本池用于建池发现、历史补齐和覆盖检查，最终名单以交易所官方校验为准。",
        "生成时间": generated,
        "股票数量": len(rows),
        "数据来源": source_meta,
        "覆盖市场统计": summarize_counts(rows, "市场"),
        "覆盖板块统计": summarize_counts(rows, "板块"),
        "行业数量": len({row.get("行业") for row in rows if row.get("行业")}),
        "数据标准口径": {
            "成交量": "手",
            "成交额": "元",
            "价格": "元",
            "涨跌幅": "百分比数值",
            "ST与退市风险": "保留在基础池，不在基础层删除，只打风险标签；下游分析层再过滤或降权。",
        },
        "系统层级关系": [
            "全A基础股票池：根据地，负责完整性、覆盖发现和历史补齐。",
            "官方交易所名单校验：准绳，负责确认全A股票边界，最终以上交所、深交所、北交所官方名单为准。",
            "2000只样本池：代表性研究池，负责行业/政策/优质企业的精细研究。",
            "重点关注池：从样本池和全A扫描中筛出，负责推送与报告。",
            "企业微信报告：只呈现结论，不替代后台分析过程。",
        ],
        "纠正说明": "本脚本历史上从重点关注快照生成初始种子，现已纠正为从公开A股行情列表生成全A基础池，避免把局部样本误称为全市场。",
        "日常数据原则": "本来源不作为后续每日正式行情长期入口；日常价格、成交量、财报、公告等增量数据应走官方/可靠实时渠道，并做多源复核与降级标记。",
        "股票池": rows,
        "安全边界": {
            "是否触发n8n": False,
            "是否真实发送企业微信": False,
            "是否接券商": False,
            "是否交易": False,
            "是否重载服务": False,
        },
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 01股票池全A基础池说明",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 股票数量：{report['股票数量']}",
        f"- 数据来源：{report['数据来源'].get('来源', '')}",
        f"- 接口报告总数：{report['数据来源'].get('接口报告总数', '')}",
        f"- 实际去重数量：{report['数据来源'].get('实际去重数量', '')}",
        "",
        "## 当前定位",
        "",
        report["定位"],
        "",
        "## 已纠正的问题",
        "",
        report["纠正说明"],
        "",
        "## 市场覆盖",
        "",
    ]
    for name, count in report["覆盖市场统计"].items():
        lines.append(f"- {name}：{count}")
    lines.extend(["", "## 板块覆盖", ""])
    for name, count in report["覆盖板块统计"].items():
        lines.append(f"- {name}：{count}")
    lines.extend(["", "## 系统层级关系", ""])
    for item in report["系统层级关系"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def write_outputs(root: Path, report: dict[str, Any]) -> dict[str, str]:
    output_dir = root / "03数据" / "01股票池"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rows = report["股票池"]

    canonical_json = output_dir / f"全A基础股票池_{stamp}.json"
    canonical_latest_json = output_dir / "全A基础股票池_最新.json"
    canonical_csv = output_dir / f"全A基础股票池_{stamp}.csv"
    canonical_latest_csv = output_dir / "全A基础股票池_最新.csv"
    md_path = output_dir / "01股票池全A基础池说明_最新.md"

    legacy_json = output_dir / f"全市场扫描源头股票池_初始种子_{stamp}.json"
    legacy_latest_json = output_dir / "全市场扫描源头股票池_初始种子_最新.json"
    legacy_csv = output_dir / f"全市场扫描源头股票池_初始种子_{stamp}.csv"
    legacy_latest_csv = output_dir / "全市场扫描源头股票池_初始种子_最新.csv"
    legacy_md = output_dir / "01股票池初始种子说明_最新.md"

    write_json(canonical_json, report)
    write_json(canonical_latest_json, report)
    write_csv(canonical_csv, rows)
    write_csv(canonical_latest_csv, rows)
    md = build_markdown(report)
    write_text(md_path, md)

    # 覆盖旧名产物，避免下游继续读取“重点关注池伪全市场”的旧债。
    write_json(legacy_json, report)
    write_json(legacy_latest_json, report)
    write_csv(legacy_csv, rows)
    write_csv(legacy_latest_csv, rows)
    write_text(legacy_md, md)

    return {
        "全A基础股票池最新JSON": str(canonical_latest_json),
        "全A基础股票池最新CSV": str(canonical_latest_csv),
        "兼容旧名最新JSON": str(legacy_latest_json),
        "说明文件": str(md_path),
    }


def main() -> int:
    root = module_root()
    degraded: list[dict[str, str]] = []
    try:
        rows, source_meta = fetch_akshare_full_a()
    except Exception as exc:  # noqa: BLE001
        degraded.append({"数据源": "AKShare公开A股基础列表+公开实时行情", "原因": str(exc)})
        rows, source_meta = fetch_eastmoney_full_a()
    if degraded:
        source_meta["降级记录"] = degraded
    report = build_report(rows, source_meta)
    outputs = write_outputs(root, report)
    status = "pass" if report["股票数量"] >= 5000 else "fail"
    print(json.dumps({
        "总体状态": status,
        "股票数量": report["股票数量"],
        "覆盖市场统计": report["覆盖市场统计"],
        "覆盖板块统计": report["覆盖板块统计"],
        "输出": outputs,
    }, ensure_ascii=False, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
