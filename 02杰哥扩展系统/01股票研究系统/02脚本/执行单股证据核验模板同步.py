# -*- coding: utf-8 -*-
"""
名称：执行单股证据核验模板同步.py
作用：在193闸口允许后，把192预览结果写入172/175/178人工核验模板。
触发方式：手动执行；默认 python 执行单股证据核验模板同步.py 仅 dry-run；写入必须追加 --execute --confirm 允许写入人工模板。
依赖：192单股证据核验台账同步预览、193单股证据核验模板同步执行闸口、172/175/178人工核验模板。
所属系统：02杰哥扩展系统/01股票研究系统。
输出：03数据/194单股证据核验模板同步执行/单股证据核验模板同步执行报告_最新.json 与 .md；执行写入时生成写入前备份。
安全边界：默认dry-run；只有同时传入 --execute 和 --confirm 允许写入人工模板 才写172/175/178；
不写正式档案、不导入正式库、不改评分推荐、不发送企业微信、不触发n8n、不调用券商接口、不自动交易、不更新施工接续包。
标识：single-stock-evidence-template-sync-execute
"""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


CONFIRM_TEXT = "允许写入人工模板"
CHAINS = {
    "公司概况": {
        "模板目录": "172公司概况人工核验模板",
        "模板文件": "公司概况人工核验模板_最新.json",
    },
    "事件风险": {
        "模板目录": "175事件风险证据人工核验模板",
        "模板文件": "事件风险证据人工核验模板_最新.json",
    },
    "行业景气": {
        "模板目录": "178行业景气人工核验模板",
        "模板文件": "行业景气人工核验模板_最新.json",
    },
}


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


def find_index(items: list[dict[str, Any]], code: str) -> int:
    for index, item in enumerate(items):
        if str(item.get("代码") or "").lower() == code.lower():
            return index
    return -1


def normalize_company_item(item: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(item)
    filled = normalized.get("待填内容")
    if isinstance(filled, dict):
        normalized["待填写"] = deepcopy(filled)
    return normalized


def changed_fields(before: Any, after: Any, prefix: str = "") -> list[str]:
    if isinstance(before, dict) and isinstance(after, dict):
        keys = sorted(set(before.keys()) | set(after.keys()))
        result: list[str] = []
        for key in keys:
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            result.extend(changed_fields(before.get(key), after.get(key), child_prefix))
        return result
    if before != after:
        return [prefix or "<root>"]
    return []


def load_paths(root: Path) -> dict[str, Path]:
    return {
        "192": root / "03数据" / "192单股证据核验台账同步预览" / "单股证据核验台账同步预览_最新.json",
        "193": root / "03数据" / "193单股证据核验模板同步执行闸口" / "单股证据核验模板同步执行闸口_最新.json",
    }


def apply_chain(root: Path, chain_name: str, preview: dict[str, Any], code: str, stamp: str, execute: bool) -> dict[str, Any]:
    config = CHAINS[chain_name]
    template_path = root / "03数据" / config["模板目录"] / config["模板文件"]
    template = load_json(template_path, {}) or {}
    items = template.get("核验模板", []) if isinstance(template.get("核验模板"), list) else []
    index = find_index(items, code)
    if index < 0:
        return {
            "链路": chain_name,
            "允许写入": False,
            "执行写入": False,
            "模板": str(template_path),
            "阻断原因": [f"模板中未找到股票代码 {code}"],
            "变化字段": [],
        }
    mapped = deepcopy(preview[chain_name].get("预览模板片段", {}))
    if chain_name == "公司概况":
        mapped = normalize_company_item(mapped)
    before = deepcopy(items[index])
    changes = changed_fields(before, mapped)
    if execute:
        backup_path = root / "03数据" / "194单股证据核验模板同步执行" / "写入前备份" / f"{config['模板文件'].replace('_最新.json', '')}_{stamp}.json"
        write_json(backup_path, template)
        items[index] = mapped
        template["生成时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        template["最近单股同步"] = {
            "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "股票代码": code,
            "股票名称": preview.get("目标股票", {}).get("名称", ""),
            "来源": "192单股证据核验台账同步预览",
        }
        write_json(template_path, template)
    return {
        "链路": chain_name,
        "允许写入": True,
        "执行写入": execute,
        "模板": str(template_path),
        "阻断原因": [],
        "变化字段": changes,
    }


def build_markdown(report: dict[str, Any]) -> str:
    target = report["目标股票"]
    lines = [
        f"# 单股证据核验模板同步执行报告 - {target.get('名称')}({target.get('代码')})",
        "",
        "## 一、执行结论",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 执行模式：{'已写入人工模板' if report['执行写入'] else 'dry-run未写入'}",
        f"- 193闸口允许：{report['193闸口允许']}",
        f"- 总结论：{report['总结论']}",
        "",
        "## 二、链路结果",
        "",
        "| 链路 | 执行写入 | 变化字段数 | 阻断原因 |",
        "|---|---|---:|---|",
    ]
    for item in report["链路结果"]:
        reasons = "；".join(item.get("阻断原因", [])) or "无"
        lines.append(f"| {item['链路']} | {item['执行写入']} | {len(item.get('变化字段', []))} | {reasons} |")
    lines.extend([
        "",
        "## 三、安全边界",
        "",
        "- 本执行器只写172/175/178人工核验模板。",
        "- 不写正式档案，不导入正式库，不改评分推荐。",
        "- 不发送企业微信，不触发n8n，不调用券商接口，不自动交易。",
        "- 正式档案仍必须经过173/176/179预览、180总览和181导入执行闸口。",
    ])
    return "\n".join(lines) + "\n"


def write_open_bat(target: Path) -> Path:
    bat = module_root() / "05入口工具" / "单股证据核验模板同步执行报告_打开.bat"
    safe_target = module_root() / "03数据" / "197单股证据核验191完成后预演检查" / "单股证据核验191完成后预演检查_最新.md"
    write_text(
        bat,
        '@echo off\r\n'
        'chcp 65001 >nul\r\n'
        'echo 本入口为兼容跳转：已改为打开197完成后预演检查，避免绕过198质量闸口和197预演。\r\n'
        f'start "" "{safe_target}"\r\n',
    )
    return bat


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="执行写入172/175/178人工模板")
    parser.add_argument("--confirm", default="", help=f"确认文本，必须为：{CONFIRM_TEXT}")
    parser.add_argument("--report-scope", choices=["latest", "temp"], default="latest", help="latest写最新报告；temp只写验证临时报表")
    args = parser.parse_args()

    root = module_root()
    now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    paths = load_paths(root)
    preview = load_json(paths["192"], {}) or {}
    gate = load_json(paths["193"], {}) or {}
    target = preview.get("目标股票", {}) if isinstance(preview.get("目标股票"), dict) else {}
    code = str(target.get("代码") or "")
    if not code:
        raise SystemExit("192预览缺少目标股票代码，禁止执行。")
    gate_allowed = bool(gate.get("是否允许进入模板同步执行器"))
    execute = bool(args.execute and args.confirm == CONFIRM_TEXT and gate_allowed)
    blocked_reason = []
    if args.execute and args.confirm != CONFIRM_TEXT:
        blocked_reason.append("确认文本不匹配")
    if args.execute and not gate_allowed:
        blocked_reason.append("193闸口未允许")

    chain_results = [
        apply_chain(root, chain_name, preview, code, stamp, execute)
        for chain_name in ["公司概况", "事件风险", "行业景气"]
    ]
    failed = [item for item in chain_results if item.get("阻断原因")]
    report = {
        "名称": "单股证据核验模板同步执行报告",
        "版本": "2026-05-03",
        "生成时间": now.strftime("%Y-%m-%d %H:%M:%S"),
        "目标股票": target,
        "输入文件": {"192": str(paths["192"]), "193": str(paths["193"])},
        "请求执行": bool(args.execute),
        "执行写入": execute,
        "193闸口允许": gate_allowed,
        "阻断原因": blocked_reason,
        "链路结果": chain_results,
        "总结论": "已写入172/175/178人工模板" if execute and not failed else ("dry-run通过，未写入人工模板" if not failed else "禁止或部分失败"),
        "安全边界": {
            "是否写172公司概况模板": execute,
            "是否写175事件风险模板": execute,
            "是否写178行业景气模板": execute,
            "是否写正式档案": False,
            "是否导入执行": False,
            "是否修改评分或推荐": False,
            "是否企业微信真实发送": False,
            "是否触发n8n": False,
            "是否调用券商接口": False,
            "是否自动交易": False,
            "是否更新施工接续包": False,
        },
    }
    out_dir = root / "03数据" / "194单股证据核验模板同步执行"
    if args.report_scope == "temp":
        out_dir = out_dir / "dry-run验证"
    latest_json = out_dir / "单股证据核验模板同步执行报告_最新.json"
    latest_md = out_dir / "单股证据核验模板同步执行报告_最新.md"
    output_json = out_dir / f"单股证据核验模板同步执行报告_{code}_{stamp}.json"
    output_md = out_dir / f"单股证据核验模板同步执行报告_{code}_{stamp}.md"
    markdown = build_markdown(report)
    write_json(output_json, report)
    write_text(output_md, markdown)
    if args.report_scope == "latest":
        write_json(latest_json, report)
        write_text(latest_md, markdown)
        bat = write_open_bat(latest_md)
    else:
        bat = ""
    print(json.dumps({
        "状态": "完成",
        "执行写入": execute,
        "总结论": report["总结论"],
        "报告": str(latest_md if args.report_scope == "latest" else output_md),
        "报告JSON": str(latest_json if args.report_scope == "latest" else output_json),
        "入口工具": str(bat),
    }, ensure_ascii=False))
    return 0 if not failed and not blocked_reason else 1


if __name__ == "__main__":
    raise SystemExit(main())
