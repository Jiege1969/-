# -*- coding: utf-8 -*-
"""
名称：解析中信行业板块映射.py
作用：把中信证券本机行业/板块资料解析成股票系统可直接使用的结构化映射。
边界：只读 F 盘中信证券目录；只写股票系统 03数据/291；不修改中信目录；不交易。
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


CITIC_ROOT = Path(r"F:\股票工具\中信证券")
HQ_CACHE = CITIC_ROOT / "T0002" / "hq_cache"
CLOUD_CFG = CITIC_ROOT / "T0002" / "cloud_cfg"


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


def normalize_code(market_id: str, digits: str) -> str:
    if market_id == "1":
        return f"sh{digits}"
    if market_id == "2":
        return f"bj{digits}"
    return f"sz{digits}"


def parse_tdxzs_names() -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    for name in ("tdxzs.cfg", "tdxzs3.cfg"):
        path = HQ_CACHE / name
        if not path.exists():
            continue
        for line in read_text(path).splitlines():
            parts = line.strip().split("|")
            if len(parts) < 6:
                continue
            label, index_code, *_, block_code = parts
            if not re.fullmatch(r"[TX]\d+", block_code):
                continue
            mapping.setdefault(block_code, {"名称": label, "指数代码": index_code, "来源": name})
    return mapping


def parse_hy_tree_names() -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    for path in CLOUD_CFG.glob("hy_tree*.xml"):
        text = read_text(path)
        for match in re.finditer(r'caption="([^"]+)"[^>]*blockid="([TX]\d+)"', text):
            label, block_code = match.group(1), match.group(2)
            mapping.setdefault(block_code, {"名称": label, "指数代码": "", "来源": path.name})
    return mapping


def merge_name_maps() -> dict[str, dict[str, str]]:
    merged = parse_hy_tree_names()
    merged.update(parse_tdxzs_names())
    return merged


def parse_tdxhy(name_map: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    path = HQ_CACHE / "tdxhy.cfg"
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        parts = line.strip().split("|")
        if len(parts) < 6:
            continue
        market_id, digits, t_code, _, _, x_code = parts[:6]
        if not re.fullmatch(r"\d{6}", digits):
            continue
        code = normalize_code(market_id, digits)
        t_info = name_map.get(t_code, {})
        x_info = name_map.get(x_code, {})
        rows.append(
            {
                "股票代码": code,
                "市场编号": market_id,
                "原始代码": digits,
                "通达信行业代码": t_code,
                "通达信行业名称": t_info.get("名称", ""),
                "通达信行业指数代码": t_info.get("指数代码", ""),
                "细分行业代码": x_code,
                "细分行业名称": x_info.get("名称", ""),
                "细分行业指数代码": x_info.get("指数代码", ""),
                "来源行号": line_no,
            }
        )
    return rows


def parse_tdxbk() -> list[dict[str, Any]]:
    path = HQ_CACHE / "tdxbk.cfg"
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(read_text(path).splitlines(), start=1):
        parts = line.strip().split("|")
        if len(parts) < 4:
            continue
        rows.append(
            {
                "类型编号": parts[0],
                "短名称": parts[1],
                "完整名称": parts[2],
                "启用标记": parts[3],
                "来源行号": line_no,
            }
        )
    return rows


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def top_counter(rows: list[dict[str, Any]], key: str, n: int = 20) -> list[dict[str, Any]]:
    counter = Counter(row.get(key) or "未命名" for row in rows)
    return [{"名称": name, "数量": count} for name, count in counter.most_common(n)]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 中信行业板块映射 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- {report['结论']}",
        f"- 股票行业映射数：{report['统计']['股票行业映射数']}",
        f"- 行业名称覆盖率：{report['统计']['行业名称覆盖率']}",
        f"- 细分行业名称覆盖率：{report['统计']['细分行业名称覆盖率']}",
        f"- 概念/板块名称数：{report['统计']['概念板块名称数']}",
        "",
        "## 二、前20个通达信行业分布",
        "",
    ]
    for item in report["通达信行业分布Top20"]:
        lines.append(f"- {item['名称']}：{item['数量']} 只")
    lines.extend(["", "## 三、前20个细分行业分布", ""])
    for item in report["细分行业分布Top20"]:
        lines.append(f"- {item['名称']}：{item['数量']} 只")
    lines.extend(["", "## 四、概念/板块名称样例", ""])
    for item in report["概念板块样例"]:
        lines.append(f"- {item['短名称']}：{item['完整名称']}，类型 {item['类型编号']}，启用标记 {item['启用标记']}")
    lines.extend(
        [
            "",
            "## 五、接入股票系统的用途",
            "",
            "- L6 行业主题观察池：用中信行业/细分行业做行业归类和主题聚合。",
            "- L5 深度研究池：补充个股所属行业和行业样本分布，避免候选过度集中。",
            "- 前台报告：把“当前市场位置”落成可读行业名称，而不是技术编码。",
            "- 中信自选板块：后续可按行业/主题生成影子板块，便于在中信软件里观察。",
            "",
            "## 六、边界",
            "",
            "- 这一步只读解析，不修改中信目录。",
            "- `tdxbk.cfg` 当前只解析板块名称，不等于已经解析板块成员。",
            "- 板块成员可能在 `spblock.dat`、`infoharbor_block.dat` 或 BlockMap 数据中，后续单独做影子解析。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    name_map = merge_name_maps()
    stock_rows = parse_tdxhy(name_map)
    concept_rows = parse_tdxbk()
    named_t = sum(1 for row in stock_rows if row["通达信行业名称"])
    named_x = sum(1 for row in stock_rows if row["细分行业名称"])
    report = {
        "名称": "中信行业板块映射",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "已将中信本机行业编码解析成股票系统可读映射；概念/板块名称已入库，成员关系待下一步解析。",
        "源文件状态": {
            "tdxhy.cfg": file_state(HQ_CACHE / "tdxhy.cfg"),
            "tdxbk.cfg": file_state(HQ_CACHE / "tdxbk.cfg"),
            "tdxzs.cfg": file_state(HQ_CACHE / "tdxzs.cfg"),
            "tdxzs3.cfg": file_state(HQ_CACHE / "tdxzs3.cfg"),
            "hy_tree.xml": file_state(CLOUD_CFG / "hy_tree.xml"),
        },
        "统计": {
            "股票行业映射数": len(stock_rows),
            "行业名称已解析数": named_t,
            "细分行业名称已解析数": named_x,
            "行业名称覆盖率": f"{named_t / len(stock_rows) * 100:.2f}%" if stock_rows else "0.00%",
            "细分行业名称覆盖率": f"{named_x / len(stock_rows) * 100:.2f}%" if stock_rows else "0.00%",
            "概念板块名称数": len(concept_rows),
            "行业编码名称数": len(name_map),
        },
        "通达信行业分布Top20": top_counter(stock_rows, "通达信行业名称"),
        "细分行业分布Top20": top_counter(stock_rows, "细分行业名称"),
        "概念板块样例": concept_rows[:30],
        "股票行业映射样例": stock_rows[:30],
        "安全边界": {
            "是否修改中信目录": False,
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否交易": False,
        },
    }
    out_dir = data_root() / "291中信行业板块映射"
    write_json(out_dir / "中信行业板块映射_最新.json", report)
    write_text(out_dir / "中信行业板块映射_最新.md", build_markdown(report))
    write_csv(out_dir / "中信股票行业映射_最新.csv", stock_rows)
    write_csv(out_dir / "中信概念板块名称_最新.csv", concept_rows)
    print(json.dumps({
        "状态": "完成",
        "股票行业映射数": len(stock_rows),
        "行业名称覆盖率": report["统计"]["行业名称覆盖率"],
        "细分行业名称覆盖率": report["统计"]["细分行业名称覆盖率"],
        "概念板块名称数": len(concept_rows),
        "报告": str(out_dir / "中信行业板块映射_最新.md"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
