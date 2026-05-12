# -*- coding: utf-8 -*-
"""
名称：执行推荐观察股金融复核覆盖.py
作用：按当日企微推荐/观察名单，分批补齐金融专项复核覆盖面。
触发方式：python 执行推荐观察股金融复核覆盖.py [--limit 2] [--dry-run]
安全边界：只读推送草案和复核索引；只调用本地金融复核脚本；只写03数据/186金融复核覆盖面板；
不触发n8n；不发送企业微信；不调用券商接口；不自动交易；不改变推荐排序和评分。
标识：stock-finance-review-coverage-runner
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_code(code: Any) -> str:
    text = str(code or "").strip().lower()
    if not text:
        return ""
    if text.startswith(("sh", "sz", "bj")):
        return text
    if "." in text:
        num, suffix = text.split(".", 1)
        suffix = suffix.upper()
        if suffix == "SH":
            return f"sh{num}"
        if suffix == "SZ":
            return f"sz{num}"
        if suffix == "BJ":
            return f"bj{num}"
    if len(text) == 6 and text.isdigit():
        if text.startswith(("6", "9")):
            return f"sh{text}"
        if text.startswith(("4", "8")):
            return f"bj{text}"
        return f"sz{text}"
    return text


def parse_push_targets(text: str) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    section = "推荐"
    seen: set[str] = set()
    for line in text.splitlines():
        if "可观察股票" in line:
            section = "观察"
        match = re.search(r"\[?([\u4e00-\u9fffA-Za-z0-9]+)\((sh|sz|bj)(\d{6})\)\]?", line, flags=re.IGNORECASE)
        if not match:
            continue
        name = match.group(1)
        code = normalize_code(f"{match.group(2)}{match.group(3)}")
        if code in seen:
            continue
        seen.add(code)
        targets.append({"名称": name, "代码": code, "分组": section})
    return targets


def covered_codes(index: dict[str, Any]) -> set[str]:
    rows = index.get("索引", []) if isinstance(index.get("索引"), list) else []
    codes: set[str] = set()
    for row in rows:
        if row.get("读取成功") and row.get("主模型成功"):
            codes.add(normalize_code(row.get("代码") or row.get("展示代码")))
    return codes


def run_command(args: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    started = datetime.now()
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        elapsed_ms = int((datetime.now() - started).total_seconds() * 1000)
        return {
            "命令": args,
            "返回码": proc.returncode,
            "耗时_ms": elapsed_ms,
            "标准输出": proc.stdout.strip(),
            "标准错误": proc.stderr.strip(),
        }
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((datetime.now() - started).total_seconds() * 1000)
        return {
            "命令": args,
            "返回码": -1,
            "耗时_ms": elapsed_ms,
            "标准输出": "",
            "标准错误": str(exc),
        }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# 推荐观察股金融复核覆盖面板 - {report['生成时间']}",
        "",
        "## 一、结论",
        "",
        f"- 当日推荐/观察股票数：{report['目标数量']}",
        f"- 本轮执行上限：{report['执行上限']}",
        f"- 执行前已覆盖：{report['执行前已覆盖数量']}",
        f"- 本轮计划补充：{len(report['本轮计划'])}",
        f"- 本轮实际执行：{len(report['执行结果'])}",
        f"- 执行后覆盖：{report.get('执行后已覆盖数量', '-')}",
        "",
        "## 二、本轮计划",
        "",
    ]
    if not report["本轮计划"]:
        lines.append("- 暂无需要执行的补充复核。")
    for item in report["本轮计划"]:
        lines.append(f"- {item['名称']}({item['代码']})：{item['分组']}")
    lines.extend(["", "## 三、执行结果", ""])
    if not report["执行结果"]:
        lines.append("- 本轮未执行复核脚本。")
    for item in report["执行结果"]:
        result = item["结果"]
        status = "成功" if result.get("返回码") == 0 else "已生成但需复查/失败"
        lines.append(f"- {item['名称']}({item['代码']})：{status}，耗时{result.get('耗时_ms')}ms")
    lines.extend([
        "",
        "## 四、安全边界",
        "",
        "- 不触发n8n。",
        "- 不发送企业微信。",
        "- 不调用券商接口。",
        "- 不自动交易。",
        "- 不改变推荐排序和评分。",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=2, help="本轮最多补充复核股票数，默认2")
    parser.add_argument("--timeout", type=int, default=240, help="单只股票复核超时秒数，默认240")
    parser.add_argument("--dry-run", action="store_true", help="只生成覆盖计划，不执行复核")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    push_path = root / "03数据" / "136推送草案" / "股票企微推送草案_最新.md"
    index_path = root / "03数据" / "149金融专项复核索引" / "股票金融专项复核索引_最新.json"
    output_dir = root / "03数据" / "186金融复核覆盖面板"
    review_script = root / "02脚本" / "执行股票金融专项复核.py"
    index_script = root / "02脚本" / "生成股票金融专项复核索引.py"

    push_text = push_path.read_text(encoding="utf-8-sig", errors="replace") if push_path.exists() else ""
    targets = parse_push_targets(push_text)
    index = load_json(index_path, {}) or {}
    before_covered = covered_codes(index)
    pending = [item for item in targets if item["代码"] not in before_covered]
    plan = pending[: max(args.limit, 0)]
    results: list[dict[str, Any]] = []

    if not args.dry_run:
        for item in plan:
            result = run_command(
                [sys.executable, str(review_script), "--code", item["代码"]],
                cwd=root,
                timeout=args.timeout,
            )
            results.append({**item, "结果": result})
        run_command([sys.executable, str(index_script)], cwd=root, timeout=120)

    after_index = load_json(index_path, {}) or {}
    after_covered = covered_codes(after_index)
    report = {
        "名称": "推荐观察股金融复核覆盖面板",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "生成工具": "执行推荐观察股金融复核覆盖.py",
        "目标数量": len(targets),
        "目标清单": targets,
        "执行上限": args.limit,
        "dry_run": bool(args.dry_run),
        "执行前已覆盖代码": sorted(before_covered),
        "执行前已覆盖数量": len(before_covered & {item["代码"] for item in targets}),
        "本轮计划": plan,
        "执行结果": results,
        "执行后已覆盖代码": sorted(after_covered),
        "执行后已覆盖数量": len(after_covered & {item["代码"] for item in targets}),
        "安全边界": {
            "是否触发n8n": False,
            "是否企业微信真实发送": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否改变推荐排序或评分": False,
        },
    }
    markdown = build_markdown(report)
    output_json = output_dir / f"推荐观察股金融复核覆盖面板_{stamp}.json"
    output_md = output_dir / f"推荐观察股金融复核覆盖面板_{stamp}.md"
    latest_json = output_dir / "推荐观察股金融复核覆盖面板_最新.json"
    latest_md = output_dir / "推荐观察股金融复核覆盖面板_最新.md"
    write_json(output_json, report)
    write_json(latest_json, report)
    write_text(output_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({
        "状态": "完成",
        "目标数量": report["目标数量"],
        "本轮计划": len(plan),
        "本轮执行": len(results),
        "执行后覆盖数量": report["执行后已覆盖数量"],
        "面板": str(latest_md),
    }, ensure_ascii=False))
    failures = [item for item in results if item["结果"].get("返回码") not in {0}]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
