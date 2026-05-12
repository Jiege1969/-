# -*- coding: utf-8 -*-
"""
名称：生成300只试运行池.py
作用：从公开A股行情列表只读生成300只试运行池，为2000只标准大股票池落地前验证数据源、行业覆盖和轻扫描稳定性。
触发方式：python 生成300只试运行池.py
依赖：Python标准库；300只试运行池生成规则.json；重点关注股票池.json；股票池模板.json；东方财富公开行情列表接口。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读公开行情列表并写入股票模块03数据目录；不触发n8n；不发送企业微信；不写正式库；不写旧系统；不调用券商接口；不自动交易；不重启服务。
创建/修改记录：2026-04-30 创建300只试运行池生成脚本；2026-04-30 增加东方财富分页抓取和curl只读降级；2026-04-30 增加深交所官方列表兜底。
标识：stock-trial-pool-300-generate
"""

from __future__ import annotations

import json
import math
import subprocess
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
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


def normalize_code(code: str, market: str | int | None = None) -> str:
    clean = str(code).strip()
    if clean.startswith(("sh", "sz", "bj")):
        return clean
    if market == 1 or clean.startswith(("6", "9")):
        return f"sh{clean}"
    if market == 0 or clean.startswith(("0", "2", "3")):
        return f"sz{clean}"
    if clean.startswith(("4", "8")):
        return f"bj{clean}"
    return clean


def fetch_url_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://quote.eastmoney.com/",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return response.read().decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        result = subprocess.run(
            ["curl.exe", "-L", "--max-time", "25", "-A", "Mozilla/5.0", "-e", "https://quote.eastmoney.com/", url],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=35,
        )
        if result.returncode != 0 or not result.stdout.strip():
            raise RuntimeError(result.stderr.strip() or f"curl exit {result.returncode}")
        return result.stdout


def fetch_eastmoney_a_share() -> tuple[list[dict[str, Any]], str]:
    fields = "f12,f13,f14,f2,f3,f5,f6,f20,f21,f100"
    all_items: list[dict[str, Any]] = []
    first_url = ""
    for page in range(1, 61):
        params = {
            "pn": str(page),
            "pz": "100",
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f6",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
            "fields": fields,
        }
        url = "https://82.push2.eastmoney.com/api/qt/clist/get?" + urllib.parse.urlencode(params)
        if not first_url:
            first_url = url
        payload = json.loads(fetch_url_text(url))
        data = payload.get("data") or {}
        diff = data.get("diff") or []
        if isinstance(diff, dict):
            diff = list(diff.values())
        if not diff:
            break
        all_items.extend(diff)
        if len(diff) < 100:
            break
        time.sleep(0.05)
    return all_items, first_url


def repair_mojibake(text: str) -> str:
    try:
        return text.encode("latin1").decode("gbk")
    except Exception:  # noqa: BLE001
        return text


def xlsx_cell_text(cell: ET.Element, ns: dict[str, str], shared: list[str]) -> str:
    inline = cell.find("a:is", ns)
    if inline is not None:
        return repair_mojibake("".join(t.text or "" for t in inline.findall(".//a:t", ns)))
    value = cell.find("a:v", ns)
    if value is None:
        return ""
    raw = value.text or ""
    if cell.attrib.get("t") == "s" and raw.isdigit():
        return shared[int(raw)] if int(raw) < len(shared) else raw
    return raw


def fetch_szse_official_list(temp_dir: Path) -> tuple[list[dict[str, Any]], str]:
    url = "https://www.szse.cn/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=1110&TABKEY=tab1"
    temp_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = temp_dir / "szse_stock_list.xlsx"
    result = subprocess.run(
        ["curl.exe", "-L", "--max-time", "30", "-A", "Mozilla/5.0", url, "-o", str(xlsx_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=40,
    )
    if result.returncode != 0 or not xlsx_path.exists() or xlsx_path.stat().st_size <= 0:
        raise RuntimeError(result.stderr.strip() or f"curl exit {result.returncode}")
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    items: list[dict[str, Any]] = []
    with zipfile.ZipFile(xlsx_path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for si in shared_root.findall("a:si", ns):
                shared.append("".join(t.text or "" for t in si.findall(".//a:t", ns)))
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        for index, row in enumerate(sheet.findall(".//a:row", ns), start=1):
            cells = [xlsx_cell_text(cell, ns, shared) for cell in row.findall("a:c", ns)]
            if index == 1 or len(cells) < 6:
                continue
            board, full_name, code, name = cells[0], cells[1], cells[4], cells[5]
            if not code.isdigit() or not name.strip():
                continue
            if "ST" in name.upper() or "退" in name:
                continue
            total_shares = safe_float(cells[7].replace(",", "") if len(cells) > 7 else 0)
            items.append(
                {
                    "f12": code,
                    "f13": 0,
                    "f14": name.replace(" ", ""),
                    "f2": 0,
                    "f3": 0,
                    "f5": 0,
                    "f6": 0,
                    "f20": total_shares,
                    "f21": total_shares,
                    "f100": board or "深交所",
                    "官方全称": full_name,
                    "官方来源": "深交所官方证券列表",
                }
            )
    return items, url


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "-", ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def score_stock(item: dict[str, Any], focus_codes: set[str]) -> float:
    amount = max(safe_float(item.get("成交额")), 0.0)
    total_mv = max(safe_float(item.get("总市值")), 0.0)
    free_mv = max(safe_float(item.get("流通市值")), 0.0)
    pct = abs(safe_float(item.get("涨跌幅")))
    score = 0.0
    score += min(math.log10(amount + 1) * 8, 40)
    score += min(math.log10(free_mv + 1) * 5, 25)
    score += min(math.log10(total_mv + 1) * 3, 15)
    score += min(pct * 2, 10)
    if item.get("代码") in focus_codes:
        score += 100
    return round(score, 4)


def load_shadow_inflow(root: Path, selected_codes: set[str], limit: int = 30) -> list[dict[str, Any]]:
    path = root / "03数据" / "2000只影子扫描" / "2000只样本池盘后影子轻扫描_最新.json"
    data = load_json(path)
    rows = data.get("股票", []) if isinstance(data.get("股票"), list) else []
    inflow: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        code = normalize_code(item.get("代码", ""))
        if not code or code in selected_codes:
            continue
        if item.get("强势信号") is not True and safe_float(item.get("评分变化")) < 5:
            continue
        inflow.append({
            "代码": code,
            "名称": item.get("名称", ""),
            "市场": item.get("市场", ""),
            "行业": item.get("行业", ""),
            "现价": 0,
            "涨跌幅": 0,
            "成交量": 0,
            "成交额": safe_float(item.get("最新成交额")),
            "总市值": safe_float(item.get("市值")),
            "流通市值": safe_float(item.get("市值")),
            "来源": "2000只影子扫描活水入口",
            "入池原因": f"影子扫描活水补充：{item.get('影子分层', '')}，影子评分{item.get('影子评分')}，评分变化{item.get('评分变化')}",
            "评分": max(850.0, safe_float(item.get("影子评分")) + 800.0),
            "影子评分": item.get("影子评分"),
            "影子评分变化": item.get("评分变化"),
            "影子强势信号": item.get("强势信号"),
        })
        if len(inflow) >= limit:
            break
    return inflow


def build_focus_items(focus: dict[str, Any], merged_pool: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for stock in focus.get("股票池", []):
        code = normalize_code(stock.get("代码", ""))
        if code:
            items[code] = {
                "代码": code,
                "名称": stock.get("名称", ""),
                "市场": stock.get("市场", ""),
                "行业": "",
                "入池原因": "重点关注池强制保留",
                "来源": "重点关注池",
            }
    for stock in merged_pool.get("股票池", []):
        code = normalize_code(stock.get("代码", ""))
        if code and code not in items:
            items[code] = {
                "代码": code,
                "名称": stock.get("名称", ""),
                "市场": stock.get("市场", ""),
                "行业": "",
                "入池原因": "当前合并股票池强制保留",
                "来源": "当前合并股票池",
            }
    return items


def convert_market(market_code: int | str | None, code: str) -> str:
    if str(market_code) == "1" or code.startswith("sh"):
        return "上交所"
    if str(market_code) == "0" or code.startswith("sz"):
        return "深交所"
    if code.startswith("bj"):
        return "北交所"
    return "未知"


def main() -> int:
    root = module_root()
    rule_path = root / "01配置" / "300只试运行池生成规则.json"
    focus_path = root / "01配置" / "重点关注股票池.json"
    merged_path = root / "01配置" / "股票池模板.json"
    rule = load_json(rule_path)
    focus = load_json(focus_path)
    merged = load_json(merged_path)
    target_size = int(rule.get("目标规模", 300))

    focus_items = build_focus_items(focus, merged)
    focus_codes = set(focus_items)
    degraded: list[dict[str, Any]] = []
    raw: list[dict[str, Any]] = []
    source_url = ""
    source_name = "东方财富公开行情列表"
    try:
        raw, source_url = fetch_eastmoney_a_share()
    except Exception as exc:  # noqa: BLE001
        degraded.append({"数据源": "东方财富公开行情列表", "原因": str(exc)})
        try:
            raw, source_url = fetch_szse_official_list(root / "06临时")
            source_name = "深交所官方证券列表"
            degraded.append({"数据源": "深交所官方证券列表", "原因": "东方财富不可用时启用官方列表兜底。"})
        except Exception as official_exc:  # noqa: BLE001
            degraded.append({"数据源": "深交所官方证券列表", "原因": str(official_exc)})

    candidates: list[dict[str, Any]] = []
    for item in raw:
        raw_code = str(item.get("f12", "")).strip()
        name = str(item.get("f14", "")).strip()
        if not raw_code or not name:
            continue
        if "ST" in name.upper() or "退" in name:
            continue
        code = normalize_code(raw_code, item.get("f13"))
        price = safe_float(item.get("f2"))
        amount = safe_float(item.get("f6"))
        if source_name == "东方财富公开行情列表" and (price <= 0 or amount <= 0):
            continue
        stock = {
            "代码": code,
            "名称": name,
            "市场": convert_market(item.get("f13"), code),
            "行业": item.get("f100") or "未分类",
            "现价": price,
            "涨跌幅": safe_float(item.get("f3")),
            "成交量": safe_float(item.get("f5")),
            "成交额": amount,
            "总市值": safe_float(item.get("f20")),
            "流通市值": safe_float(item.get("f21")),
            "来源": source_name,
            "入池原因": "公开行情轻扫描候选",
        }
        stock["评分"] = score_stock(stock, focus_codes)
        candidates.append(stock)

    by_code = {item["代码"]: item for item in candidates}
    selected: list[dict[str, Any]] = []
    for code, focus_item in focus_items.items():
        merged_item = by_code.get(code, {})
        stock = {**focus_item, **merged_item}
        stock["代码"] = code
        stock["入池原因"] = focus_item["入池原因"]
        stock.setdefault("现价", 0)
        stock.setdefault("涨跌幅", 0)
        stock.setdefault("成交量", 0)
        stock.setdefault("成交额", 0)
        stock.setdefault("总市值", 0)
        stock.setdefault("流通市值", 0)
        stock["评分"] = max(safe_float(stock.get("评分")), 999.0)
        selected.append(stock)

    industry_counts: dict[str, int] = {}
    selected_codes = {item["代码"] for item in selected}
    shadow_inflow = load_shadow_inflow(root, selected_codes)
    for item in shadow_inflow:
        if len(selected) >= target_size:
            break
        if item["代码"] in selected_codes:
            continue
        selected.append(item)
        selected_codes.add(item["代码"])

    ranked = sorted(candidates, key=lambda item: item.get("评分", 0), reverse=True)
    for item in ranked:
        if len(selected) >= target_size:
            break
        if item["代码"] in selected_codes:
            continue
        industry = item.get("行业") or "未分类"
        if industry_counts.get(industry, 0) >= 18:
            continue
        item["入池原因"] = "成交活跃、市值代表性和行业覆盖综合入池"
        selected.append(item)
        selected_codes.add(item["代码"])
        industry_counts[industry] = industry_counts.get(industry, 0) + 1

    if len(selected) < target_size:
        for item in ranked:
            if len(selected) >= target_size:
                break
            if item["代码"] in selected_codes:
                continue
            item["入池原因"] = "行业分散后补齐试运行池规模"
            selected.append(item)
            selected_codes.add(item["代码"])

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "规则文件": str(rule_path),
        "目标规模": target_size,
        "实际数量": len(selected),
        "数据源": {
            "名称": source_name,
            "URL": source_url,
            "原始候选数量": len(raw),
            "过滤后候选数量": len(candidates),
            "降级": degraded,
        },
        "强制保留数量": len(focus_items),
        "影子活水入口": {
            "来源": str(root / "03数据" / "2000只影子扫描" / "2000只样本池盘后影子轻扫描_最新.json"),
            "纳入数量": len([item for item in selected[:target_size] if item.get("来源") == "2000只影子扫描活水入口"]),
            "候选数量": len(shadow_inflow),
        },
        "安全边界": rule.get("安全边界", {}),
        "股票池": selected[:target_size],
        "实际动作": {
            "真实联网只读": bool(raw),
            "触发n8n": False,
            "企业微信真实发送": False,
            "写正式库": False,
            "写旧系统": False,
            "调用券商接口": False,
            "自动交易": False,
            "重启服务": False,
        },
    }
    output_dir = root / "03数据" / "91试运行池"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"300只试运行池_{stamp}.json"
    latest = output_dir / "300只试运行池_最新.json"
    write_json(output, report)
    write_json(latest, report)
    time.sleep(0.1)
    print(json.dumps({"目标规模": target_size, "实际数量": len(selected), "原始候选数量": len(raw), "输出": str(output)}, ensure_ascii=False))
    return 0 if len(selected) > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
