# -*- coding: utf-8 -*-
"""
名称：生成中信自选板块影子文件.py
作用：把股票分析系统已有股票池转换为中信证券/通达信可识别的 .blk 自选板块影子文件。
边界：只读系统股票池和中信现有自选文件；只写本系统 03数据/289；不直接修改中信证券目录；不交易。
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


CITIC_BLOCK_DIR = Path(r"F:\股票工具\中信证券\T0002\blocknew")
CODE_RE = re.compile(r"\b(?:sh|sz|bj)?(?:60|68|90|00|30|20|43|83|87|92)\d{4}\b", re.IGNORECASE)


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_root() -> Path:
    return module_root() / "03数据"


def latest_json(folder_prefix: str, name_hint: str | None = None) -> Path | None:
    folders = [p for p in data_root().iterdir() if p.is_dir() and p.name.startswith(folder_prefix)]
    if not folders:
        return None
    folder = folders[0]
    files = list(folder.glob("*.json"))
    if name_hint:
        hinted = [p for p in files if name_hint in p.name]
        files = hinted or files
    latest_named = [p for p in files if "最新" in p.name]
    candidates = latest_named or files
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def walk_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                values.append(key)
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    elif isinstance(value, str):
        values.append(value)
    elif isinstance(value, (int, float)):
        text = str(value)
        if len(text) == 6:
            values.append(text)
    return values


def normalize_code(raw: str) -> str | None:
    raw = raw.strip().lower()
    match = CODE_RE.search(raw)
    if not match:
        return None
    code = match.group(0).lower()
    if code.startswith(("sh", "sz", "bj")):
        market, digits = code[:2], code[2:]
    else:
        digits = code[-6:]
        if digits.startswith(("60", "68", "90")):
            market = "sh"
        elif digits.startswith(("00", "30", "20")):
            market = "sz"
        elif digits.startswith(("43", "83", "87", "92")):
            market = "bj"
        else:
            return None
    return f"{market}{digits}"


def citic_blk_code(code: str) -> str | None:
    market, digits = code[:2], code[2:]
    if market == "sh":
        return f"1{digits}"
    if market in {"sz", "bj"}:
        return f"0{digits}"
    return None


def extract_codes_from_json(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for value in walk_values(data):
        for match in CODE_RE.finditer(value):
            code = normalize_code(match.group(0))
            if code:
                found.add(code)
    return sorted(found)


def read_existing_zxg() -> list[str]:
    path = CITIC_BLOCK_DIR / "zxg.blk"
    if not path.exists():
        return []
    codes: list[str] = []
    for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
        text = line.strip()
        if re.fullmatch(r"[01]\d{6}", text):
            if text.startswith("1"):
                codes.append(f"sh{text[1:]}")
            else:
                digits = text[1:]
                market = "bj" if digits.startswith(("43", "83", "87", "92")) else "sz"
                codes.append(f"{market}{digits}")
    return sorted(set(codes))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["板块文件", "板块名称", "来源", "股票数", "股票代码"]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_blk(path: Path, codes: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\r\n".join(codes) + ("\r\n" if codes else "")
    path.write_bytes(content.encode("ascii"))


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 中信自选板块影子同步 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 结论：{report['结论']}",
        f"- 影子目录：`{report['影子目录']}`",
        f"- 板块数量：{len(report['板块清单'])}",
        f"- 总股票数：{report['总去重股票数']}",
        "",
        "## 二、生成的板块",
        "",
    ]
    for item in report["板块清单"]:
        lines.extend(
            [
                f"### {item['板块名称']}",
                "",
                f"- 文件：`{item['板块文件']}`",
                f"- 来源：`{item['来源文件']}`",
                f"- 股票数：{item['股票数']}",
                f"- 前20只：{', '.join(item['股票代码'][:20]) if item['股票代码'] else '无'}",
                "",
            ]
        )
    lines.extend(
        [
            "## 三、三层协同路线",
            "",
        ]
    )
    for item in report["三层协同路线"]:
        lines.extend(
            [
                f"### {item['层级']}",
                "",
                f"- 目标：{item['目标']}",
                f"- 当前状态：{item['当前状态']}",
                f"- 下一步：{item['下一步']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 四、使用原则",
            "",
            "- 当前只生成影子 .blk 文件，不直接写入中信证券目录。",
            "- 确认中信软件识别规则后，再增加受控同步脚本，把影子文件复制到 `T0002/blocknew`。",
            "- 自选板块用于观察、验证和复盘，不表示交易指令。",
            "- 后续可把中信自带指标结果反向读取进系统，用于比较、学习和方法优化。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    out_dir = data_root() / "289中信自选板块影子同步"
    shadow_dir = out_dir / "shadow_blocknew"
    shadow_dir.mkdir(parents=True, exist_ok=True)

    sources = [
        {"板块文件": "JG_L8X.blk", "板块名称": "杰哥L8X综合候选池", "目录前缀": "130X", "名称提示": "L8X"},
        {"板块文件": "JG_L7.blk", "板块名称": "杰哥L7可观察过滤池", "目录前缀": "132", "名称提示": "L7"},
        {"板块文件": "JG_L6.blk", "板块名称": "杰哥L6行业主题观察池", "目录前缀": "133", "名称提示": "L6"},
        {"板块文件": "JG_L5.blk", "板块名称": "杰哥L5深度研究池", "目录前缀": "134", "名称提示": "L5"},
        {"板块文件": "JG_MANUAL.blk", "板块名称": "杰哥人工确认观察池", "目录前缀": "135", "名称提示": "人工确认"},
    ]

    board_reports: list[dict[str, Any]] = []
    csv_rows: list[dict[str, Any]] = []
    all_codes: set[str] = set()

    for source in sources:
        src = latest_json(source["目录前缀"], source["名称提示"])
        codes = extract_codes_from_json(src) if src else []
        blk_codes = [citic_blk_code(code) for code in codes]
        blk_codes = [code for code in blk_codes if code]
        write_blk(shadow_dir / source["板块文件"], blk_codes)
        all_codes.update(codes)
        board_reports.append(
            {
                "板块文件": source["板块文件"],
                "板块名称": source["板块名称"],
                "来源文件": str(src) if src else "",
                "股票数": len(codes),
                "股票代码": codes,
                "中信blk代码样例": blk_codes[:20],
            }
        )
        csv_rows.append(
            {
                "板块文件": source["板块文件"],
                "板块名称": source["板块名称"],
                "来源": str(src) if src else "",
                "股票数": len(codes),
                "股票代码": ",".join(codes),
            }
        )

    existing = read_existing_zxg()
    report = {
        "名称": "中信自选板块影子同步",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "已把系统分层股票池转换为中信 .blk 影子板块；下一步可做受控同步和中信指标互证。",
        "中信板块目录": str(CITIC_BLOCK_DIR),
        "影子目录": str(shadow_dir),
        "中信现有自选股数量": len(existing),
        "中信现有自选股样例": existing[:30],
        "总去重股票数": len(all_codes),
        "板块清单": board_reports,
        "三层协同路线": [
            {
                "层级": "第一层：中信结果为我所用",
                "目标": "读取中信本地行情、板块、财务/F10、软件自带分析线索，与系统结果互证；表现好的线索进入复盘学习。",
                "当前状态": "已完成资料能力盘点、更新监测和自选板块影子文件；尚未直接读取中信自带指标结果。",
                "下一步": "解析中信基础资料、行业板块和可导出的分析结果，形成中信证据卡。",
            },
            {
                "层级": "第二层：我方方法反向进入中信",
                "目标": "把系统确认有效的股票池、观察名单和部分稳定指标，转成中信自选板块或指标公式，减少重复计算并方便人工观察。",
                "当前状态": "已生成 5 个 .blk 影子自选板块；未直接写入中信目录。",
                "下一步": "确认 .blk 导入稳定后，增加带备份的受控同步；再盘点中信公式/指标文件格式。",
            },
            {
                "层级": "第三层：系统主责学习进化，中信主责本地呈现与辅助筛选",
                "目标": "我们的系统负责方法学习、复盘、评分和前台报告；中信软件负责本地行情、图形观察、分组展示和部分指标运行。",
                "当前状态": "方向成立，已建立自选板块桥梁；指标公式桥梁待影子验证。",
                "下一步": "建立“系统结果 -> 中信板块 -> 使用反馈 -> 复盘学习 -> 方法修正”的闭环日报。",
            },
        ],
        "安全边界": {
            "是否修改中信目录": False,
            "是否登录券商": False,
            "是否调用券商接口": False,
            "是否交易": False,
        },
    }
    write_json(out_dir / "中信自选板块影子同步_最新.json", report)
    write_text(out_dir / "中信自选板块影子同步_最新.md", build_markdown(report))
    write_csv(out_dir / "中信自选板块影子同步_最新.csv", csv_rows)
    print(json.dumps({"状态": "完成", "板块数量": len(board_reports), "总股票数": len(all_codes), "影子目录": str(shadow_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
