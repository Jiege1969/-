# -*- coding: utf-8 -*-
"""
名称：同步系统股票池到中信自选板块.py
作用：把股票分析系统的核心股票池写入中信证券自选板块目录，便于在中信软件中直接观察。
边界：只写 T0002/blocknew 下的自选板块文件和 blocknew.cfg；先备份；不触碰交易、委托、账户、券商接口。
"""

from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


CITIC_BLOCK_DIR = Path(r"F:\股票工具\中信证券\T0002\blocknew")
CFG_FILE = CITIC_BLOCK_DIR / "blocknew.cfg"
CFG_RECORD_BYTES = 40
GBK = "gbk"
CODE_RE = re.compile(r"\b(?:sh|sz|bj)?(?:60|68|90|00|30|20|43|83|87|92)\d{4}\b", re.IGNORECASE)


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_root() -> Path:
    return module_root() / "03数据"


def normalize_code(raw: str) -> str | None:
    text = raw.strip().lower()
    match = CODE_RE.search(text)
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


def read_shadow_blk(path: Path) -> list[str]:
    codes: list[str] = []
    if not path.exists():
        return codes
    for line in path.read_text(encoding="ascii", errors="ignore").splitlines():
        text = line.strip()
        if re.fullmatch(r"[01]\d{6}", text):
            codes.append(text)
    return sorted(dict.fromkeys(codes))


def read_csv_codes(path: Path, column: str = "股票代码") -> list[str]:
    if not path.exists():
        return []
    codes: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            code = normalize_code(row.get(column, ""))
            blk_code = citic_blk_code(code) if code else None
            if blk_code:
                codes.append(blk_code)
    return sorted(dict.fromkeys(codes))


def read_cfg_names() -> list[str]:
    if not CFG_FILE.exists():
        return []
    raw = CFG_FILE.read_bytes()
    names: list[str] = []
    for start in range(0, len(raw), CFG_RECORD_BYTES):
        chunk = raw[start : start + CFG_RECORD_BYTES]
        name = chunk.decode(GBK, errors="ignore").strip("\x00").strip()
        if name:
            names.append(name)
    return names


def encode_cfg_name(name: str) -> bytes:
    raw = name.encode(GBK, errors="ignore")
    if len(raw) > CFG_RECORD_BYTES:
        raise ValueError(f"板块名称超过 {CFG_RECORD_BYTES} 字节：{name}")
    return raw + b"\x00" * (CFG_RECORD_BYTES - len(raw))


def write_cfg_names(names: list[str]) -> None:
    unique_names = list(dict.fromkeys([name for name in names if name.strip()]))
    CFG_FILE.write_bytes(b"".join(encode_cfg_name(name) for name in unique_names))


def write_blk(path: Path, codes: list[str]) -> None:
    content = "\r\n".join(codes) + ("\r\n" if codes else "")
    path.write_bytes(content.encode("ascii"))


def backup_existing(paths: list[Path], backup_dir: Path) -> list[str]:
    backup_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for path in paths:
        if path.exists():
            target = backup_dir / path.name
            shutil.copy2(path, target)
            copied.append(str(target))
    return copied


def build_boards() -> list[dict[str, Any]]:
    shadow_dir = data_root() / "289中信自选板块影子同步" / "shadow_blocknew"
    enhanced_dir = data_root() / "293中信市场位置增强样本池"
    return [
        {"名称": "杰哥L8X综合候选池", "文件": "杰哥L8X综合候选池.blk", "来源": shadow_dir / "JG_L8X.blk", "类型": "shadow"},
        {"名称": "杰哥L7可观察过滤池", "文件": "杰哥L7可观察过滤池.blk", "来源": shadow_dir / "JG_L7.blk", "类型": "shadow"},
        {"名称": "杰哥L6行业主题观察池", "文件": "杰哥L6行业主题观察池.blk", "来源": shadow_dir / "JG_L6.blk", "类型": "shadow"},
        {"名称": "杰哥L5深度研究池", "文件": "杰哥L5深度研究池.blk", "来源": shadow_dir / "JG_L5.blk", "类型": "shadow"},
        {"名称": "杰哥人工确认观察池", "文件": "杰哥人工确认观察池.blk", "来源": shadow_dir / "JG_MANUAL.blk", "类型": "shadow"},
        {"名称": "杰哥L6市场位置增强池", "文件": "杰哥L6市场位置增强池.blk", "来源": enhanced_dir / "L6市场位置增强排序_最新.csv", "类型": "csv"},
        {"名称": "杰哥L5市场位置增强池", "文件": "杰哥L5市场位置增强池.blk", "来源": enhanced_dir / "L5市场位置增强排序_最新.csv", "类型": "csv"},
    ]


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 中信自选板块正式同步 - {report['生成时间']}",
        "",
        "## 结论",
        "",
        f"- 状态：{report['状态']}",
        f"- 中信目录：`{report['中信板块目录']}`",
        f"- 备份目录：`{report['备份目录']}`",
        f"- 保留原有板块：{', '.join(report['同步前原有板块']) if report['同步前原有板块'] else '无'}",
        "",
        "## 已同步板块",
        "",
    ]
    for item in report["同步板块"]:
        lines.extend(
            [
                f"### {item['名称']}",
                "",
                f"- 文件：`{item['文件']}`",
                f"- 来源：`{item['来源']}`",
                f"- 股票数：{item['股票数']}",
                f"- 前20只：{', '.join(item['代码样例']) if item['代码样例'] else '无'}",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "- 只同步自选板块，方便观察和复盘。",
            "- 不调用券商交易接口。",
            "- 不读取账户，不委托，不自动交易。",
            "- 每次同步前备份 `blocknew.cfg` 和将要覆盖的同名 `.blk` 文件。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    now = datetime.now()
    out_dir = data_root() / "295中信自选板块正式同步"
    backup_dir = out_dir / f"backup_{now.strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not CITIC_BLOCK_DIR.exists():
        raise FileNotFoundError(f"中信自选板块目录不存在：{CITIC_BLOCK_DIR}")

    boards = build_boards()
    existing_names = read_cfg_names()
    planned_paths = [CITIC_BLOCK_DIR / board["文件"] for board in boards]
    backup_files = [CFG_FILE, *planned_paths]
    backed_up = backup_existing(backup_files, backup_dir)

    board_reports: list[dict[str, Any]] = []
    for board in boards:
        if board["类型"] == "shadow":
            codes = read_shadow_blk(board["来源"])
        else:
            codes = read_csv_codes(board["来源"])
        target = CITIC_BLOCK_DIR / board["文件"]
        write_blk(target, codes)
        board_reports.append(
            {
                "名称": board["名称"],
                "文件": str(target),
                "来源": str(board["来源"]),
                "股票数": len(codes),
                "代码样例": codes[:20],
            }
        )

    final_names = list(dict.fromkeys([*existing_names, *[board["名称"] for board in boards]]))
    write_cfg_names(final_names)

    report: dict[str, Any] = {
        "名称": "中信自选板块正式同步",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "完成",
        "中信板块目录": str(CITIC_BLOCK_DIR),
        "备份目录": str(backup_dir),
        "已备份文件": backed_up,
        "同步前原有板块": existing_names,
        "同步后板块": final_names,
        "同步板块": board_reports,
        "安全边界": {
            "只写自选板块": True,
            "不触碰交易接口": True,
            "不读取账户": True,
            "不自动交易": True,
        },
    }
    (out_dir / "中信自选板块正式同步_最新.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "中信自选板块正式同步_最新.md").write_text(build_markdown(report), encoding="utf-8")
    print(json.dumps({"状态": report["状态"], "同步板块数": len(board_reports), "备份目录": str(backup_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
