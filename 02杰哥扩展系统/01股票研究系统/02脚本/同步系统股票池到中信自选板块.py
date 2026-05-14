# -*- coding: utf-8 -*-
"""
名称：同步系统股票池到中信自选板块.py
作用：把股票分析系统的结果型股票池写入中信证券自选板块目录，便于在中信软件中直接观察。
边界：只写 T0002/blocknew 下的自选板块文件和自选板块登记文件；先备份；不触碰交易、委托、账户、券商接口。
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


CITIC_BLOCK_DIR = Path(r"F:\股票工具\中信证券\T0002\blocknew")
CFG_FILE = CITIC_BLOCK_DIR / "blocknew.cfg"
CFG_RECORD_BYTES = 40
CLR_FILE = CITIC_BLOCK_DIR / "blocknew.clr"
CLR_RECORD_BYTES = 100
CLR_NAME_BYTES = 50
CLR_SLOT_COUNT = 16
GBK = "gbk"
CODE_RE = re.compile(r"\b(?:sh|sz|bj)?(?:60|68|90|00|30|20|43|83|87|92)\d{4}\b", re.IGNORECASE)
PROCESS_NAME = "TdxW.exe"
OLD_MANAGED_BOARDS = [
    "杰哥L8X综合候选池",
    "杰哥L7可观察过滤池",
    "杰哥L6行业主题观察池",
    "杰哥L5深度研究池",
    "杰哥人工确认观察池",
    "杰哥L6市场位置增强池",
    "杰哥L5市场位置增强池",
]
REMOVED_EMPTY_BOARDS = ["临时"]
INVALID_AUTO_NAMES = {"殚"}


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def data_root() -> Path:
    return module_root() / "03数据"


def config_root() -> Path:
    return module_root() / "01配置"


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


def read_json_codes(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    codes: list[str] = []

    def collect_structured(value: Any) -> None:
        if isinstance(value, dict):
            for key in ("代码", "股票代码", "证券代码"):
                if key in value:
                    code = normalize_code(str(value[key]))
                    blk_code = citic_blk_code(code) if code else None
                    if blk_code:
                        codes.append(blk_code)
            for item in value.values():
                collect_structured(item)
        elif isinstance(value, list):
            for item in value:
                collect_structured(item)

    collect_structured(data)
    if codes:
        return sorted(dict.fromkeys(codes))

    for value in walk_values(data):
        for match in CODE_RE.finditer(str(value)):
            code = normalize_code(match.group(0))
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
        if name and name not in INVALID_AUTO_NAMES:
            names.append(name)
    return names


def read_clr_names() -> list[str]:
    if not CLR_FILE.exists():
        return []
    raw = CLR_FILE.read_bytes()
    names: list[str] = []
    for start in range(0, len(raw), CLR_RECORD_BYTES):
        chunk = raw[start : start + CLR_NAME_BYTES]
        name = chunk.split(b"\x00", 1)[0].decode(GBK, errors="ignore").strip()
        if name and name not in INVALID_AUTO_NAMES:
            names.append(name)
    return names


def encode_cfg_name(name: str) -> bytes:
    raw = name.encode(GBK, errors="ignore")
    if len(raw) > CFG_RECORD_BYTES:
        raise ValueError(f"板块名称超过 {CFG_RECORD_BYTES} 字节：{name}")
    return raw + b"\x00" * (CFG_RECORD_BYTES - len(raw))


def write_cfg_names(names: list[str]) -> None:
    unique_names = list(dict.fromkeys([name for name in names if name.strip() and name not in INVALID_AUTO_NAMES]))
    CFG_FILE.write_bytes(b"".join(encode_cfg_name(name) for name in unique_names))


def encode_clr_name(name: str) -> bytes:
    raw = name.encode(GBK, errors="ignore")
    if len(raw) > CLR_NAME_BYTES:
        raise ValueError(f"板块名称超过 {CLR_NAME_BYTES} 字节：{name}")
    return raw + b"\x00" * (CLR_NAME_BYTES - len(raw))


def write_clr_names(names: list[str]) -> None:
    unique_names = list(dict.fromkeys([name for name in names if name.strip() and name not in INVALID_AUTO_NAMES]))
    if len(unique_names) > CLR_SLOT_COUNT:
        raise ValueError(f"中信自选板块登记槽位不足：{len(unique_names)} > {CLR_SLOT_COUNT}")

    if CLR_FILE.exists() and CLR_FILE.stat().st_size >= CLR_RECORD_BYTES:
        raw = bytearray(CLR_FILE.read_bytes())
    else:
        raw = bytearray(CLR_RECORD_BYTES * CLR_SLOT_COUNT)
    required_len = CLR_RECORD_BYTES * CLR_SLOT_COUNT
    if len(raw) < required_len:
        raw.extend(b"\x00" * (required_len - len(raw)))

    for index in range(CLR_SLOT_COUNT):
        start = index * CLR_RECORD_BYTES
        raw[start : start + CLR_NAME_BYTES] = b"\x00" * CLR_NAME_BYTES
        if index < len(unique_names):
            raw[start : start + CLR_NAME_BYTES] = encode_clr_name(unique_names[index])
    CLR_FILE.write_bytes(bytes(raw[:required_len]))


def write_blk(path: Path, codes: list[str]) -> None:
    content = "\r\n".join(codes) + ("\r\n" if codes else "")
    path.write_bytes(content.encode("ascii"))


def is_citic_running() -> bool:
    completed = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {PROCESS_NAME}", "/NH"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return PROCESS_NAME.lower() in (completed.stdout or "").lower()


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
    learning_pool = data_root() / "01股票池" / "2500只样本股票池_最新.json"
    if not learning_pool.exists():
        learning_pool = data_root() / "01股票池" / "2000只样本股票池_最新.json"
    focus_pool = config_root() / "重点关注股票池.json"
    return [
        {
            "名称": "杰哥的学习分析股票池",
            "文件": "杰哥的学习分析股票池.blk",
            "来源": learning_pool,
            "类型": "json",
            "定位": "大样本承载、长期学习、方法验证、减少系统重复基础计算压力。",
        },
        {
            "名称": "杰哥的重点分析股票池",
            "文件": "杰哥的重点分析股票池.blk",
            "来源": focus_pool,
            "类型": "json",
            "定位": "当前重点跟踪、重点报告、重点复盘；数量随系统分析结果动态变化，按条件入池，按失效条件退出，不按固定数量凑数。",
        },
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
                f"- 定位：{item['定位']}",
                f"- 前20只：{', '.join(item['代码样例']) if item['代码样例'] else '无'}",
                "",
            ]
        )
    lines.extend(
        [
            "## 边界",
            "",
            "- 只同步自选板块，方便观察和复盘。",
            "- 中信前台只放结果型股票池，不暴露 L5-L8 内部分析过程。",
            "- 重点分析股票池不是固定规模池，数量由系统方法和市场条件共同决定。",
            "- 不调用券商交易接口。",
            "- 不读取账户，不委托，不自动交易。",
            "- 每次同步前备份自选板块登记文件和将要覆盖的同名 `.blk` 文件。",
            "- 如果中信软件已经打开，新板块通常要完全退出并重新打开后才会出现在界面。",
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
    existing_names = list(dict.fromkeys([*read_clr_names(), *read_cfg_names()]))
    old_managed_paths = [CITIC_BLOCK_DIR / f"{name}.blk" for name in [*OLD_MANAGED_BOARDS, *REMOVED_EMPTY_BOARDS]]
    planned_paths = [CITIC_BLOCK_DIR / board["文件"] for board in boards]
    backup_files = [CFG_FILE, CLR_FILE, *old_managed_paths, *planned_paths]
    backed_up = backup_existing(backup_files, backup_dir)
    citic_running = is_citic_running()

    board_reports: list[dict[str, Any]] = []
    for board in boards:
        if board["类型"] == "shadow":
            codes = read_shadow_blk(board["来源"])
        elif board["类型"] == "csv":
            codes = read_csv_codes(board["来源"])
        else:
            codes = read_json_codes(board["来源"])
        target = CITIC_BLOCK_DIR / board["文件"]
        write_blk(target, codes)
        board_reports.append(
            {
                "名称": board["名称"],
                "文件": str(target),
                "来源": str(board["来源"]),
                "股票数": len(codes),
                "定位": board["定位"],
                "代码样例": codes[:20],
            }
        )

    removed_old_files: list[str] = []
    for path in old_managed_paths:
        if path.exists():
            path.unlink()
            removed_old_files.append(str(path))

    preserved_names = [name for name in existing_names if name not in [*OLD_MANAGED_BOARDS, *REMOVED_EMPTY_BOARDS, *INVALID_AUTO_NAMES]]
    final_names = list(dict.fromkeys([*preserved_names, *[board["名称"] for board in boards]]))
    write_cfg_names(final_names)
    write_clr_names(final_names)

    report: dict[str, Any] = {
        "名称": "中信自选板块正式同步",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "完成",
        "中信板块目录": str(CITIC_BLOCK_DIR),
        "中信软件当前是否运行": citic_running,
        "可见性提示": "中信软件已运行，需完全退出并重新打开后才能稳定看到最新自选板块。" if citic_running else "中信软件未运行，下次启动会读取最新自选板块。",
        "备份目录": str(backup_dir),
        "已备份文件": backed_up,
        "已移除旧内部过程板块文件": removed_old_files,
        "已从前台隐藏的内部过程板块": OLD_MANAGED_BOARDS,
        "已删除空板块": REMOVED_EMPTY_BOARDS,
        "同步前原有板块": existing_names,
        "同步后板块": final_names,
        "同步板块": board_reports,
        "安全边界": {
            "只写自选板块": True,
            "中信前台只放结果型股票池": True,
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
    print(json.dumps({
        "状态": report["状态"],
        "同步板块数": len(board_reports),
        "中信软件当前是否运行": citic_running,
        "同步后板块": final_names,
        "备份目录": str(backup_dir),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
