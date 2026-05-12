# -*- coding: utf-8 -*-
"""
名称：补齐公司经营快照_财报关键指标.py
作用：基于AKShare公开财务摘要，为公司经营快照补齐当前L5股票的财报关键指标。
触发方式：python 补齐公司经营快照_财报关键指标.py
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读03数据与AKShare公开数据；只写03数据/166公司经营快照；不触发n8n；不发送企业微信；不调用券商接口；不自动交易。
标识：stock-company-snapshot-financial-enrich
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def pure_code(code: str) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text[2:]
    if "." in text:
        return text.split(".", 1)[0]
    return text


def normalize_code(code: str) -> str:
    text = str(code or "").strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text
    num = pure_code(text)
    if num.startswith(("6", "9")):
        return "sh" + num
    if num.startswith(("4", "8")):
        return "bj" + num
    return "sz" + num


def to_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def yuan_to_yi(value: Any) -> float | None:
    number = to_float(value)
    if number is None:
        return None
    return round(number / 100000000, 4)


def get_metric(df: Any, option: str, metric: str, period: str) -> Any:
    try:
        rows = df[(df["选项"].astype(str) == option) & (df["指标"].astype(str) == metric)]
        if rows.empty:
            rows = df[df["指标"].astype(str) == metric]
        if rows.empty:
            return None
        return rows.iloc[0][period]
    except Exception:  # noqa: BLE001
        return None


def latest_period(df: Any) -> str | None:
    columns = [str(col) for col in getattr(df, "columns", []) if str(col).isdigit()]
    if not columns:
        return None
    return sorted(columns, reverse=True)[0]


def fetch_financial_snapshot(code: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        import akshare as ak  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return None, f"akshare不可用：{exc}"

    symbol = pure_code(code)
    try:
        df = ak.stock_financial_abstract(symbol=symbol)
    except Exception as exc:  # noqa: BLE001
        return None, f"AKShare stock_financial_abstract失败：{exc}"
    if df is None or getattr(df, "empty", True):
        return None, "AKShare返回空财务摘要"

    period = latest_period(df)
    if not period:
        return None, "未识别最新报告期"

    revenue = get_metric(df, "常用指标", "营业总收入", period)
    net_profit_parent = get_metric(df, "常用指标", "归母净利润", period)
    deduct_profit = get_metric(df, "常用指标", "扣非净利润", period)
    gross_margin = get_metric(df, "常用指标", "毛利率", period)
    net_margin = get_metric(df, "常用指标", "销售净利率", period)
    roe = get_metric(df, "常用指标", "净资产收益率(ROE)", period)
    operating_cash = get_metric(df, "常用指标", "经营现金流量净额", period)
    revenue_growth = get_metric(df, "成长能力", "营业总收入增长率", period)
    profit_growth = get_metric(df, "成长能力", "归属母公司净利润增长率", period)

    cash_quality = "待人工核验"
    op_cash_num = to_float(operating_cash)
    profit_num = to_float(net_profit_parent)
    if op_cash_num is not None and profit_num not in (None, 0):
        cash_quality = f"经营现金流/归母净利润约{op_cash_num / profit_num:.2f}"

    return {
        "最新报告期": period,
        "营业收入_亿元": yuan_to_yi(revenue),
        "营业收入同比": to_float(revenue_growth),
        "归母净利润_亿元": yuan_to_yi(net_profit_parent),
        "扣非净利润_亿元": yuan_to_yi(deduct_profit),
        "利润同比": to_float(profit_growth),
        "毛利率": to_float(gross_margin),
        "净利率": to_float(net_margin),
        "ROE": to_float(roe),
        "经营现金流净额_亿元": yuan_to_yi(operating_cash),
        "现金流质量说明": cash_quality,
    }, None


def target_codes(root: Path, mode: str) -> list[str]:
    data_dir = root / "03数据"
    if mode == "all":
        snapshot = load_json(data_dir / "166公司经营快照" / "公司经营快照_最新.json")
        return [item.get("代码") for item in snapshot.get("股票快照", []) if item.get("代码")]
    l5 = load_json(data_dir / "134深度研究池" / "L5深度研究池_最新.json")
    return [item.get("代码") for item in l5.get("股票池", []) if item.get("代码")]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["l5", "all"], default="l5")
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    data_dir = root / "03数据"
    snapshot_path = data_dir / "166公司经营快照" / "公司经营快照_最新.json"
    snapshot = load_json(snapshot_path)
    if not snapshot.get("股票快照"):
        raise SystemExit("公司经营快照_最新.json不存在或为空，请先运行生成公司经营快照初始模板.py")

    targets = set(normalize_code(code) for code in target_codes(root, args.scope))
    success = 0
    failed = 0
    details: list[dict[str, Any]] = []

    for item in snapshot.get("股票快照", []):
        code = normalize_code(item.get("代码"))
        if code not in targets:
            continue
        financial, error = fetch_financial_snapshot(code)
        if financial:
            item["财报快照"].update(financial)
            item["证据状态"]["财报指标"] = "已接入"
            item["证据状态"]["公司概况"] = item["证据状态"].get("公司概况", "待接入")
            sources = set(item.get("数据来源", []))
            sources.add("AKShare stock_financial_abstract")
            item["数据来源"] = sorted(sources)
            success += 1
            details.append({"代码": code, "名称": item.get("名称"), "状态": "成功", "最新报告期": financial.get("最新报告期")})
        else:
            item["证据状态"]["财报指标"] = "待接入"
            failed += 1
            details.append({"代码": code, "名称": item.get("名称"), "状态": "失败", "原因": error})
        if args.sleep > 0:
            time.sleep(args.sleep)

    snapshot["生成时间"] = now.strftime("%Y-%m-%d %H:%M:%S")
    snapshot["最近财报补齐"] = {
        "补齐时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "范围": args.scope,
        "目标股票数": len(targets),
        "成功数": success,
        "失败数": failed,
        "详情": details,
        "说明": "仅使用公开财务摘要，不编造缺失字段；失败股票保留待接入状态。",
    }

    output_dir = data_dir / "166公司经营快照"
    latest = output_dir / "公司经营快照_最新.json"
    stamped = output_dir / f"公司经营快照_{stamp}.json"
    write_json(latest, snapshot)
    write_json(stamped, snapshot)

    print(json.dumps({
        "状态": "完成",
        "范围": args.scope,
        "目标股票数": len(targets),
        "成功数": success,
        "失败数": failed,
        "最新": str(latest),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
