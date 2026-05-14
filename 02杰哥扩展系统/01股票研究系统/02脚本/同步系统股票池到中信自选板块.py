# -*- coding: utf-8 -*-
"""
名称：同步系统股票池到中信自选板块.py
作用：把股票分析系统的结果型股票池写入中信证券自选板块，便于在中信软件中直接观察。
边界：只维护结果型自选板块和股票列表；先备份；不触碰交易、委托、账户、券商接口。
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
PRESERVED_MANUAL_BOARD_NAMES = ["杰哥的临时选股"]
BOARD_FILE_CANDIDATES = {
    "杰哥的学习分析股票池": ["JGDXXFXGPC.blk"],
    "杰哥的重点分析股票池": ["JGDZDFXGPC.blk"],
    "杰哥短线池": ["JGDXC.blk"],
}
TARGET_BOARD_NAMES = list(BOARD_FILE_CANDIDATES)
STALE_VISIBLE_BOARD_NAMES = [
    "杰哥的重",
    "杰哥的学",
    "杰哥的重点分析股票",
    "分析股票池",
    *OLD_MANAGED_BOARDS,
    *REMOVED_EMPTY_BOARDS,
]
STALE_GENERATED_BOARD_FILES = [
    "分析股票池.blk",
    "临时.blk",
    "杰哥的学习分析股票池.blk",
    "杰哥的重点分析股票池.blk",
]


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


def read_shortline_report_codes(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    codes: list[str] = []
    for item in data.get("股票", []) if isinstance(data.get("股票"), list) else []:
        if not isinstance(item, dict):
            continue
        code = normalize_code(str(item.get("代码", "")))
        blk_code = citic_blk_code(code) if code else None
        if blk_code and blk_code not in codes:
            codes.append(blk_code)
    return codes


def read_cfg_names() -> list[str]:
    if not CFG_FILE.exists():
        return []
    try:
        raw = CFG_FILE.read_bytes()
    except OSError:
        return []
    names: list[str] = []
    for start in range(0, len(raw), CFG_RECORD_BYTES):
        chunk = raw[start : start + CFG_RECORD_BYTES]
        name = chunk.split(b"\x00", 1)[0].decode(GBK, errors="ignore").strip()
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


def is_stale_visible_name(name: str) -> bool:
    return name in {*STALE_VISIBLE_BOARD_NAMES, *INVALID_AUTO_NAMES}


def cfg_record(name: str) -> bytes:
    raw = name.encode(GBK)
    if len(raw) > CFG_RECORD_BYTES - 1:
        raise ValueError(f"中信板块名称过长：{name}")
    return raw + b"\x00" * (CFG_RECORD_BYTES - len(raw))


def effective_cfg_names(existing_names: list[str]) -> list[str]:
    names: list[str] = []
    for name in PRESERVED_MANUAL_BOARD_NAMES:
        if name not in names:
            names.append(name)
    for name in existing_names:
        if name and not is_stale_visible_name(name) and name not in names:
            names.append(name)
    for name in TARGET_BOARD_NAMES:
        if resolve_existing_board_file(name).exists() and name not in names:
            names.append(name)
    return names


def rewrite_cfg_index(existing_names: list[str]) -> dict[str, Any]:
    target_names = effective_cfg_names(existing_names)
    result: dict[str, Any] = {
        "状态": "未执行",
        "清理前板块": existing_names,
        "清理后板块": target_names,
        "移除板块": [name for name in existing_names if is_stale_visible_name(name)],
        "错误": "",
    }
    if not CFG_FILE.exists():
        result["状态"] = "索引不存在"
        return result
    if existing_names == target_names:
        result["状态"] = "无需清理"
        return result
    try:
        CFG_FILE.write_bytes(b"".join(cfg_record(name) for name in target_names))
    except OSError as exc:
        result["状态"] = "待关闭中信软件后清理"
        result["错误"] = str(exc)
        return result
    result["状态"] = "已清理"
    return result


def write_blk(path: Path, codes: list[str]) -> None:
    content = "\r\n".join(codes) + ("\r\n" if codes else "")
    path.write_bytes(content.encode("ascii"))


def resolve_existing_board_file(board_name: str) -> Path:
    candidates = BOARD_FILE_CANDIDATES.get(board_name, [f"{board_name}.blk"])
    for candidate in candidates:
        path = CITIC_BLOCK_DIR / candidate
        if path.exists():
            return path
    raise FileNotFoundError(
        f"中信软件尚未创建自选板块：{board_name}。"
        f"请先在中信软件里创建该板块；当前约定文件：{', '.join(candidates)}"
    )


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


def backup_existing(paths: list[Path], backup_dir: Path) -> tuple[list[str], list[str]]:
    backup_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    failed: list[str] = []
    unique_paths = list(dict.fromkeys(paths))
    for path in unique_paths:
        if path.exists():
            target = backup_dir / path.name
            try:
                shutil.copy2(path, target)
            except OSError as exc:
                failed.append(f"{path}: {exc}")
                continue
            copied.append(str(target))
    return copied, failed


def build_boards() -> list[dict[str, Any]]:
    learning_pool = data_root() / "01股票池" / "2500只样本股票池_最新.json"
    if not learning_pool.exists():
        learning_pool = data_root() / "01股票池" / "2000只样本股票池_最新.json"
    focus_pool = config_root() / "重点关注股票池.json"
    shortline_pool = data_root() / "260股票n8n日内报告闭环与晨报推送策略包" / "收盘短线观察_基于300只轻扫描_最新.json"
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
        {
            "名称": "杰哥短线池",
            "文件": "杰哥短线池.blk",
            "来源": shortline_pool,
            "类型": "shortline_report",
            "定位": "1-5天短线观察对象，供企业微信短线助手和中信软件同步查看；来源为收盘短线观察报告，按报告顺序写入。",
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
        f"- 当前有效板块：{', '.join(report['同步后板块']) if report['同步后板块'] else '无'}",
        f"- 索引清理：{report['索引清理']['状态']}",
        f"- 已移除旧板块文件：{len(report['已移除旧板块文件'])} 个",
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
            "- 每次同步前备份将要覆盖或清理的中信自选文件。",
            "- 中信前台保留四个板块：杰哥的临时选股、学习分析股票池、重点分析股票池、短线池。",
            "- 系统只覆盖后三个结果型股票池，不覆盖你手工维护的临时选股。",
            "- 中信板块文件约定：`JGDXXFXGPC.blk`、`JGDZDFXGPC.blk`、`JGDXC.blk`。",
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
    old_managed_paths = [
        *[CITIC_BLOCK_DIR / f"{name}.blk" for name in STALE_VISIBLE_BOARD_NAMES],
        *[CITIC_BLOCK_DIR / filename for filename in STALE_GENERATED_BOARD_FILES],
    ]
    planned_paths = [resolve_existing_board_file(board["名称"]) for board in boards]
    backup_files = [CFG_FILE, CLR_FILE, *old_managed_paths, *planned_paths]
    backed_up, backup_failed = backup_existing(backup_files, backup_dir)
    citic_running = is_citic_running()

    board_reports: list[dict[str, Any]] = []
    for board in boards:
        if board["类型"] == "shadow":
            codes = read_shadow_blk(board["来源"])
        elif board["类型"] == "csv":
            codes = read_csv_codes(board["来源"])
        elif board["类型"] == "shortline_report":
            codes = read_shortline_report_codes(board["来源"])
        else:
            codes = read_json_codes(board["来源"])
        target = resolve_existing_board_file(board["名称"])
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
    remove_failed: list[str] = []
    for path in old_managed_paths:
        if path.exists():
            try:
                path.unlink()
            except OSError as exc:
                remove_failed.append(f"{path}: {exc}")
                continue
            removed_old_files.append(str(path))

    cfg_cleanup = rewrite_cfg_index(existing_names)
    final_names = cfg_cleanup["清理后板块"]

    report: dict[str, Any] = {
        "名称": "中信自选板块正式同步",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "状态": "完成",
        "中信板块目录": str(CITIC_BLOCK_DIR),
        "中信软件当前是否运行": citic_running,
        "可见性提示": "中信软件已运行；本次已写入股票列表并尝试收口索引，若界面未刷新可切换板块或重进自选股。" if citic_running else "中信软件未运行；下次启动会读取结果型股票池。",
        "备份目录": str(backup_dir),
        "已备份文件": backed_up,
        "备份失败": backup_failed,
        "已移除旧板块文件": removed_old_files,
        "移除失败": remove_failed,
        "索引清理": cfg_cleanup,
        "已从前台隐藏的内部过程板块": OLD_MANAGED_BOARDS,
        "已删除旧重复板块": [name for name in existing_names if is_stale_visible_name(name)],
        "保留手工板块": PRESERVED_MANUAL_BOARD_NAMES,
        "同步前原有板块": existing_names,
        "同步后板块": final_names,
        "同步板块": board_reports,
        "安全边界": {
            "只写自选板块": True,
            "只向中信已创建板块填股票": True,
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
