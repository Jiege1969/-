# -*- coding: utf-8 -*-
"""
名称：解析中信概念板块成分映射.py
作用：把中信证券本机板块成分资料解析成股票系统可直接使用的“市场位置”映射。
边界：只读 F 盘中信证券目录；只写股票系统 03数据/292；不修改中信目录；不登录券商；不交易。
"""

from __future__ import annotations

import csv
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


CITIC_ROOT = Path(r"F:\股票工具\中信证券")
HQ_CACHE = CITIC_ROOT / "T0002" / "hq_cache"
BLOCKMAP_XML = CITIC_ROOT / "BlockMap" / "BlockMapXML.dat"


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_root() -> Path:
    return module_root() / "03数据"


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "gb18030", "gbk", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def file_state(path: Path) -> dict[str, Any]:
    return {
        "路径": str(path),
        "存在": path.exists(),
        "大小": path.stat().st_size if path.exists() and path.is_file() else 0,
        "更新时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if path.exists() else "",
    }


def normalize_market_code(market_id: str, digits: str) -> str | None:
    if not re.fullmatch(r"\d{6}", digits):
        return None
    if market_id == "1":
        return f"sh{digits}"
    if market_id == "2":
        return f"bj{digits}"
    if digits.startswith(("43", "83", "87", "92")):
        return f"bj{digits}"
    return f"sz{digits}"


def load_industry_rows() -> tuple[list[dict[str, str]], dict[str, dict[str, str]]]:
    path = data_root() / "291中信行业板块映射" / "中信股票行业映射_最新.csv"
    rows: list[dict[str, str]] = []
    by_code: dict[str, dict[str, str]] = {}
    if not path.exists():
        return rows, by_code
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            code = row.get("股票代码", "").strip()
            if not code:
                continue
            rows.append(row)
            by_code[code] = row
    return rows, by_code


def parse_spblock(stock_universe: set[str]) -> list[dict[str, Any]]:
    path = HQ_CACHE / "spblock.dat"
    if not path.exists():
        return []

    blocks: list[dict[str, Any]] = []
    current_name = ""
    current_codes: list[str] = []

    def flush() -> None:
        if not current_name:
            return
        filtered = sorted({code for code in current_codes if code in stock_universe})
        blocks.append(
            {
                "来源文件": "spblock.dat",
                "板块类别": "特殊板块",
                "类别代码": "SP",
                "板块名称": current_name,
                "板块代码": "",
                "声明成分数": len(current_codes),
                "A股成分数": len(filtered),
                "股票代码": filtered,
            }
        )

    for line in read_text(path).splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith("#"):
            flush()
            current_name = text[1:].strip()
            current_codes = []
            continue
        for match in re.finditer(r"\b([012])(\d{6})\b", text):
            code = normalize_market_code(match.group(1), match.group(2))
            if code:
                current_codes.append(code)
    flush()
    return blocks


def parse_infoharbor(stock_universe: set[str]) -> list[dict[str, Any]]:
    path = HQ_CACHE / "infoharbor_block.dat"
    if not path.exists():
        return []

    category_names = {"GN": "概念板块", "FG": "风格板块", "ZS": "指数板块"}
    blocks: list[dict[str, Any]] = []
    current_meta: dict[str, Any] | None = None
    current_codes: list[str] = []

    def parse_header(header: str) -> dict[str, Any]:
        prefix, rest = header.split("_", 1) if "_" in header else ("", header)
        parts = [part.strip() for part in rest.split(",")]
        return {
            "来源文件": "infoharbor_block.dat",
            "板块类别": category_names.get(prefix, prefix or "未分类板块"),
            "类别代码": prefix,
            "板块名称": parts[0] if parts else rest,
            "声明成分数": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
            "板块代码": parts[2] if len(parts) > 2 else "",
            "创建日期": parts[3] if len(parts) > 3 else "",
            "更新日期": parts[4] if len(parts) > 4 else "",
        }

    def flush() -> None:
        if not current_meta:
            return
        filtered = sorted({code for code in current_codes if code in stock_universe})
        item = dict(current_meta)
        item["原始成分数"] = len(current_codes)
        item["A股成分数"] = len(filtered)
        item["股票代码"] = filtered
        blocks.append(item)

    for line in read_text(path).splitlines():
        text = line.strip()
        if not text:
            continue
        if text.startswith("#"):
            flush()
            current_meta = parse_header(text[1:].strip())
            current_codes = []
            continue
        for match in re.finditer(r"\b([012])#(\d{6})\b", text):
            code = normalize_market_code(match.group(1), match.group(2))
            if code:
                current_codes.append(code)
    flush()
    return blocks


def parse_blockmap_labels() -> list[dict[str, str]]:
    if not BLOCKMAP_XML.exists():
        return []
    labels: list[dict[str, str]] = []
    with zipfile.ZipFile(BLOCKMAP_XML) as zf:
        for name in zf.namelist():
            if not name.endswith(".xml") or name == "blockmap.xml":
                continue
            text = zf.read(name).decode("utf-8", errors="ignore")
            root_info = ""
            root_match = re.search(r'<Root[^>]*info="([^"]+)"', text)
            if root_match:
                root_info = root_match.group(1)
            for match in re.finditer(r'<Label[^>]*id="([^"]+)"[^>]*userstr="([^"]+)"', text):
                labels.append({"来源XML": name, "板块大类": root_info, "板块代码": match.group(1), "板块名称": match.group(2)})
    return labels


def stock_position_summary(position: dict[str, Any]) -> str:
    industry = position.get("行业名称") or "行业未识别"
    fine = position.get("细分行业名称") or "细分行业未识别"
    concepts = position.get("概念板块", [])
    styles = position.get("风格板块", [])
    indices = position.get("指数板块", [])
    specials = position.get("特殊板块", [])
    parts = [f"行业位置：{industry}/{fine}"]
    if concepts:
        parts.append("相关概念：" + "、".join(concepts[:5]))
    if styles:
        parts.append("风格标签：" + "、".join(styles[:4]))
    if indices:
        parts.append("指数归属：" + "、".join(indices[:4]))
    if specials:
        parts.append("交易属性：" + "、".join(specials[:4]))
    return "；".join(parts) + "。"


def build_positions(blocks: list[dict[str, Any]], industry_by_code: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    positions: dict[str, dict[str, Any]] = {}
    for code, row in industry_by_code.items():
        positions[code] = {
            "股票代码": code,
            "行业名称": row.get("通达信行业名称", ""),
            "细分行业名称": row.get("细分行业名称", ""),
            "概念板块": [],
            "风格板块": [],
            "指数板块": [],
            "特殊板块": [],
            "板块总数": 0,
        }

    for block in blocks:
        category = block["板块类别"]
        name = block["板块名称"]
        for code in block["股票代码"]:
            if code not in positions:
                continue
            if category in positions[code]:
                positions[code][category].append(name)

    for item in positions.values():
        for key in ("概念板块", "风格板块", "指数板块", "特殊板块"):
            item[key] = sorted(set(item[key]))
        item["板块总数"] = sum(len(item[key]) for key in ("概念板块", "风格板块", "指数板块", "特殊板块"))
        item["市场位置摘要"] = stock_position_summary(item)
    return sorted(positions.values(), key=lambda row: (-row["板块总数"], row["股票代码"]))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_membership_rows(blocks: list[dict[str, Any]], industry_by_code: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for block in blocks:
        for code in block["股票代码"]:
            industry = industry_by_code.get(code, {})
            rows.append(
                {
                    "股票代码": code,
                    "板块类别": block["板块类别"],
                    "类别代码": block["类别代码"],
                    "板块名称": block["板块名称"],
                    "板块代码": block.get("板块代码", ""),
                    "来源文件": block["来源文件"],
                    "行业名称": industry.get("通达信行业名称", ""),
                    "细分行业名称": industry.get("细分行业名称", ""),
                }
            )
    return rows


def top_blocks(blocks: list[dict[str, Any]], category: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    filtered = [block for block in blocks if category is None or block["板块类别"] == category]
    top = sorted(filtered, key=lambda item: item["A股成分数"], reverse=True)[:limit]
    return [
        {
            "板块类别": item["板块类别"],
            "板块名称": item["板块名称"],
            "A股成分数": item["A股成分数"],
            "板块代码": item.get("板块代码", ""),
            "来源文件": item["来源文件"],
        }
        for item in top
    ]


def top_stock_positions(positions: list[dict[str, Any]], limit: int = 30) -> list[dict[str, Any]]:
    return [
        {
            "股票代码": item["股票代码"],
            "行业名称": item["行业名称"],
            "细分行业名称": item["细分行业名称"],
            "板块总数": item["板块总数"],
            "市场位置摘要": item["市场位置摘要"],
        }
        for item in positions[:limit]
    ]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 中信概念板块成分映射 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- {report['结论']}",
        f"- 已解析板块数：{report['统计']['板块数']}",
        f"- 已解析板块成分关系：{report['统计']['A股板块成分关系数']}",
        f"- 覆盖股票数：{report['统计']['覆盖股票数']} / {report['统计']['行业股票总数']}",
        f"- 覆盖率：{report['统计']['覆盖率']}",
        "",
        "## 二、板块来源",
        "",
        "- `infoharbor_block.dat`：主要提供概念、风格、指数板块成分。",
        "- `spblock.dat`：提供融资融券、沪深港通、指数成分、ETF等特殊板块成分；本脚本只保留股票系统行业表内的A股。",
        "- `BlockMapXML.dat`：提供中信板块地图里的板块标签，用来核对板块名称和分类。",
        "",
        "## 三、前20个大板块",
        "",
    ]
    for item in report["大板块Top20"]:
        lines.append(f"- {item['板块类别']} / {item['板块名称']}：{item['A股成分数']} 只")
    lines.extend(["", "## 四、前20个概念板块", ""])
    for item in report["概念板块Top20"]:
        lines.append(f"- {item['板块名称']}：{item['A股成分数']} 只")
    lines.extend(["", "## 五、市场位置样例", ""])
    for item in report["市场位置样例"]:
        lines.append(f"- {item['股票代码']}：{item['市场位置摘要']}")
    lines.extend(
        [
            "",
            "## 六、接入股票系统的用途",
            "",
            "- L6行业主题观察池：用板块成分关系判断一只股票是否处在多个活跃主题交叉点。",
            "- L5深度研究池：补充“市场位置摘要”，让单股报告不再只写个股自身。",
            "- 前台报告：可直接输出“属于什么行业、关联哪些主题、是否有融资融券/沪深港通/指数归属”等结果。",
            "- 中信协同：后续可把系统样本池与中信板块位置互相校验，形成使用、反馈、复盘、改进闭环。",
            "",
            "## 七、安全边界",
            "",
            "- 只读中信本机资料，不修改中信软件目录。",
            "- 不登录券商，不调用交易接口，不产生任何交易动作。",
            "- 板块关系只用于研究、筛选、报告表达和复盘学习。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    industry_rows, industry_by_code = load_industry_rows()
    stock_universe = set(industry_by_code)

    info_blocks = parse_infoharbor(stock_universe)
    special_blocks = parse_spblock(stock_universe)
    blocks = info_blocks + special_blocks
    membership_rows = build_membership_rows(blocks, industry_by_code)
    positions = build_positions(blocks, industry_by_code)
    covered_stocks = {row["股票代码"] for row in membership_rows}
    category_counts = Counter(block["板块类别"] for block in blocks)
    membership_counts = Counter(row["板块类别"] for row in membership_rows)
    blockmap_labels = parse_blockmap_labels()

    report = {
        "名称": "中信概念板块成分映射",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "已把中信本机板块成分解析为股票系统可用的市场位置表，下一步可接入单股报告和L6/L5样本池验收。",
        "源文件状态": {
            "spblock.dat": file_state(HQ_CACHE / "spblock.dat"),
            "infoharbor_block.dat": file_state(HQ_CACHE / "infoharbor_block.dat"),
            "BlockMapXML.dat": file_state(BLOCKMAP_XML),
            "中信股票行业映射_最新.csv": file_state(data_root() / "291中信行业板块映射" / "中信股票行业映射_最新.csv"),
        },
        "统计": {
            "行业股票总数": len(stock_universe),
            "板块数": len(blocks),
            "infoharbor板块数": len(info_blocks),
            "特殊板块数": len(special_blocks),
            "A股板块成分关系数": len(membership_rows),
            "覆盖股票数": len(covered_stocks),
            "覆盖率": f"{len(covered_stocks) / len(stock_universe) * 100:.2f}%" if stock_universe else "0.00%",
            "BlockMap标签数": len(blockmap_labels),
            "板块分类统计": dict(category_counts),
            "板块成分分类统计": dict(membership_counts),
        },
        "大板块Top20": top_blocks(blocks),
        "概念板块Top20": top_blocks(blocks, "概念板块"),
        "市场位置样例": top_stock_positions(positions),
        "BlockMap标签样例": blockmap_labels[:50],
        "安全边界": {
            "是否修改中信目录": False,
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否交易": False,
        },
    }

    out_dir = data_root() / "292中信概念板块成分映射"
    write_json(out_dir / "中信概念板块成分映射_最新.json", report)
    write_text(out_dir / "中信概念板块成分映射_最新.md", build_markdown(report))
    write_csv(
        out_dir / "中信板块成分关系_最新.csv",
        membership_rows,
        ["股票代码", "板块类别", "类别代码", "板块名称", "板块代码", "来源文件", "行业名称", "细分行业名称"],
    )
    write_csv(
        out_dir / "中信股票市场位置_最新.csv",
        [
            {
                "股票代码": item["股票代码"],
                "行业名称": item["行业名称"],
                "细分行业名称": item["细分行业名称"],
                "概念板块": "、".join(item["概念板块"]),
                "风格板块": "、".join(item["风格板块"]),
                "指数板块": "、".join(item["指数板块"]),
                "特殊板块": "、".join(item["特殊板块"]),
                "板块总数": item["板块总数"],
                "市场位置摘要": item["市场位置摘要"],
            }
            for item in positions
        ],
        ["股票代码", "行业名称", "细分行业名称", "概念板块", "风格板块", "指数板块", "特殊板块", "板块总数", "市场位置摘要"],
    )

    print(
        json.dumps(
            {
                "状态": "完成",
                "板块数": report["统计"]["板块数"],
                "成分关系数": report["统计"]["A股板块成分关系数"],
                "覆盖股票数": report["统计"]["覆盖股票数"],
                "覆盖率": report["统计"]["覆盖率"],
                "报告": str(out_dir / "中信概念板块成分映射_最新.md"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
