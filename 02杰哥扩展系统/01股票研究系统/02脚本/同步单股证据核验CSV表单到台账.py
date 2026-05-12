# -*- coding: utf-8 -*-
"""
名称：同步单股证据核验CSV表单到台账.py
作用：把191 CSV表单中“填写值”列同步回191人工填写台账JSON/Markdown。
触发方式：默认由197预演检查以 --dry-run 调用；写入191时必须人工确认后显式运行。
依赖：191人工填写CSV表单、191人工填写台账JSON、生成单股证据核验人工填写台账.py 的Markdown构建函数。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/191单股证据核验人工填写台账/单股证据核验CSV表单同步到台账_最新.json 与 .md；非dry-run时更新191台账。
安全边界：--dry-run只生成预检报告；非dry-run只写191人工填写台账和同步报告；不写172/175/178模板、不写正式档案、不导入正式模板、不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易。
标识：single-stock-evidence-csv-sync-to-ledger
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


CHAINS = ["公司概况", "事件风险", "行业景气"]


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "gbk"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        except UnicodeDecodeError:
            continue
    raise ValueError(f"CSV编码无法识别：{path}")


def nonempty(value: Any) -> bool:
    return bool(str(value or "").strip())


def chain_status(fill: dict[str, Any], status_key: str = "核验状态") -> dict[str, Any]:
    required = [key for key in fill.keys() if not key.startswith("人工备注")]
    missing = [key for key in required if not nonempty(fill.get(key))]
    verified = str(fill.get(status_key) or "").strip() == "已核验"
    return {
        "必填数量": len(required),
        "已填数量": len(required) - len(missing),
        "缺失字段": missing,
        "核验状态是否已核验": verified,
        "是否可进入预览": not missing and verified,
    }


def load_ledger_markdown_builder(root: Path):
    script_path = root / "02脚本" / "生成单股证据核验人工填写台账.py"
    spec = importlib.util.spec_from_file_location("manual_ledger_generator", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载台账Markdown生成器：{script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_markdown


def apply_rows_to_ledger(ledger: dict[str, Any], rows: list[dict[str, str]]) -> dict[str, Any]:
    target = ledger.get("目标股票", {}) if isinstance(ledger.get("目标股票"), dict) else {}
    target_code = str(target.get("代码") or "").strip()
    changes: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []
    for row in rows:
        row_code = str(row.get("股票代码") or "").strip()
        chain_name = str(row.get("链路") or "").strip()
        field = str(row.get("字段") or "").strip()
        value = str(row.get("填写值") or "").strip()
        if row_code and target_code and row_code != target_code:
            ignored.append({"原因": "股票代码不匹配", "行": row})
            continue
        if chain_name not in CHAINS or not field:
            ignored.append({"原因": "链路或字段无效", "行": row})
            continue
        chain = ledger.get(chain_name)
        if not isinstance(chain, dict) or not isinstance(chain.get("人工填写"), dict):
            ignored.append({"原因": "台账中不存在该链路", "行": row})
            continue
        fill = chain["人工填写"]
        if field not in fill:
            ignored.append({"原因": "台账中不存在该字段", "行": row})
            continue
        old_value = str(fill.get(field) or "")
        if old_value != value:
            changes.append({"链路": chain_name, "字段": field, "旧值": old_value, "新值": value})
        fill[field] = value
    for chain_name in CHAINS:
        chain = ledger.get(chain_name, {})
        if isinstance(chain, dict) and isinstance(chain.get("人工填写"), dict):
            chain["完成状态"] = chain_status(chain["人工填写"])
    statuses = [ledger[name]["完成状态"] for name in CHAINS if isinstance(ledger.get(name), dict)]
    ledger["汇总"] = {
        "链路数": 3,
        "可进入预览链路数": sum(1 for item in statuses if item["是否可进入预览"]),
        "缺失字段总数": sum(len(item["缺失字段"]) for item in statuses),
    }
    ledger["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ledger["当前状态"] = "人工填写完成待预览" if ledger["汇总"]["缺失字段总数"] == 0 else "待人工填写"
    return {"台账": ledger, "变更": changes, "忽略": ignored}


def build_sync_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 单股证据核验CSV表单同步到台账报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 执行模式：{'只预检不写入' if report['只预检'] else '已写入191台账'}",
        f"- 目标股票：{report['目标股票']}",
        f"- 读取行数：{report['读取行数']}",
        f"- 变更字段数：{len(report['变更'])}",
        f"- 忽略行数：{len(report['忽略'])}",
        f"- 可进入预览链路数：{report['汇总']['可进入预览链路数']} / 3",
        f"- 缺失字段总数：{report['汇总']['缺失字段总数']}",
        "",
        "## 变更字段",
        "",
    ]
    if report["变更"]:
        for item in report["变更"]:
            lines.append(f"- {item['链路']} / {item['字段']}：`{item['旧值']}` -> `{item['新值']}`")
    else:
        lines.append("- 无。")
    lines.extend(["", "## 忽略行", ""])
    if report["忽略"]:
        for item in report["忽略"]:
            lines.append(f"- {item['原因']}：{item['行']}")
    else:
        lines.append("- 无。")
    lines.extend([
        "",
        "## 安全边界",
        "",
        "- 本脚本只同步到191人工填写台账，不写正式档案，不导入正式模板，不改评分推荐。",
        "- 仍需192台账同步预览和193模板同步执行闸口确认后，才允许后续显式执行。",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="只生成同步预检报告，不写回191台账")
    args = parser.parse_args()

    root = module_root()
    out_dir = root / "03数据" / "191单股证据核验人工填写台账"
    csv_path = out_dir / "单股证据核验人工填写CSV表单_最新.csv"
    ledger_json = out_dir / "单股证据核验人工填写台账_最新.json"
    ledger_md = out_dir / "单股证据核验人工填写台账_最新.md"
    if not csv_path.exists():
        raise SystemExit(f"CSV表单不存在：{csv_path}")
    ledger = load_json(ledger_json, {}) or {}
    if not ledger.get("目标股票", {}).get("代码"):
        raise SystemExit("191人工填写台账不存在或目标股票不明确。")
    rows = read_csv_rows(csv_path)
    result = apply_rows_to_ledger(ledger, rows)
    updated = result["台账"]
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not args.dry_run:
        markdown_builder = load_ledger_markdown_builder(root)
        markdown = markdown_builder(updated)
        write_json(ledger_json, updated)
        write_text(ledger_md, markdown)
        target_code = updated["目标股票"].get("代码")
        write_json(out_dir / f"单股证据核验人工填写台账_{target_code}_{stamp}.json", updated)
        write_text(out_dir / f"单股证据核验人工填写台账_{target_code}_{stamp}.md", markdown)

    report = {
        "名称": "单股证据核验CSV表单同步到台账报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "只预检": bool(args.dry_run),
        "目标股票": f"{updated['目标股票'].get('名称')}({updated['目标股票'].get('代码')})",
        "CSV表单": str(csv_path),
        "读取行数": len(rows),
        "变更": result["变更"],
        "忽略": result["忽略"],
        "汇总": updated["汇总"],
    }
    latest_json = out_dir / "单股证据核验CSV表单同步到台账_最新.json"
    latest_md = out_dir / "单股证据核验CSV表单同步到台账_最新.md"
    write_json(latest_json, report)
    write_text(latest_md, build_sync_markdown(report))
    write_json(out_dir / f"单股证据核验CSV表单同步到台账_{stamp}.json", report)
    write_text(out_dir / f"单股证据核验CSV表单同步到台账_{stamp}.md", build_sync_markdown(report))
    print(json.dumps({
        "状态": "完成",
        "只预检": bool(args.dry_run),
        "读取行数": len(rows),
        "变更字段数": len(result["变更"]),
        "忽略行数": len(result["忽略"]),
        "报告": str(latest_md),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
