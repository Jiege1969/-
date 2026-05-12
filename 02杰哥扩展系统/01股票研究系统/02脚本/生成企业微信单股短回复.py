# -*- coding: utf-8 -*-
"""
名称：生成企业微信单股短回复.py
作用：调用股票助手统一前台模板，生成适合企业微信对话框阅读的单股短回复草稿。
触发方式：python 生成企业微信单股短回复.py --stock 新易盛
依赖：Python标准库；股票助手入口.py；股票前台输出标准_v2.json。
所属系统：02杰哥扩展系统/01股票研究系统
安全边界：只读本地股票研究数据；默认只写03数据/24企业微信短回复和04日志/企业微信短回复；显式 --shadow-v21-dry-run 时额外写231影子对照包；显式 --use-v21-template-dry-run 时将24草稿写为v21正式成交额口径；不触发n8n；不发送企业微信；不写旧系统；不写正式库；不调用券商接口；不自动交易。
创建/修改记录：2026-04-28 创建企业微信单股短回复生成脚本；2026-05-04 改为复用股票助手入口统一单股短答模板，避免旧短回复链路复活旧话术；2026-05-05 增加默认关闭的shadow_v21 dry-run双写参数；2026-05-05 增加默认关闭的v21模板dry-run草稿开关。
标识：stock-wework-single-brief-reply-generate
"""

from __future__ import annotations

import argparse
import importlib.util
import json
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


def value(value: Any) -> str:
    if value is None or value == "":
        return "-"
    return str(value)


def limit_text(text: str, max_chars: int = 900) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 18].rstrip() + "\n...已截断，详见本地完整报告。"


def shadow_v21_source_path(root: Path) -> Path:
    return (
        root
        / "03数据"
        / "230微信短文正式生成器正式成交额口径对照包"
        / "微信短文正式生成器正式成交额口径对照包_最新.json"
    )


def load_stock_assistant(root: Path) -> Any:
    script = root / "02脚本" / "股票助手入口.py"
    spec = importlib.util.spec_from_file_location("jiege_stock_assistant_entry", script)
    if not spec or not spec.loader:
        raise RuntimeError(f"无法加载股票助手入口：{script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def generate_unified_reply(root: Path, stock: str) -> dict[str, Any]:
    assistant = load_stock_assistant(root)
    result = assistant.build_analysis(f"分析{stock}", refresh=True, remember_context=False, entrance_role="助手")
    reply = str(result.get("企业微信回复") or result.get("回复") or "").strip()
    if result.get("状态") != "完成" or not reply:
        raise RuntimeError(f"统一股票助手短答生成失败：{result.get('状态')} {result.get('回复')}")
    return {
        "状态": result.get("状态"),
        "股票": result.get("股票", {}),
        "短回复": limit_text(reply),
        "标准报告v2路径": result.get("标准报告v2路径", ""),
        "股票助手结果": {
            "问题": result.get("问题"),
            "状态": result.get("状态"),
            "安全边界": result.get("安全边界", {}),
        },
    }


def build_shadow_v21_package(root: Path, package: dict[str, Any], reply: str) -> dict[str, Any]:
    source_path = shadow_v21_source_path(root)
    source = load_json(source_path, {}) or {}
    shadow_text = str(source.get("正式成交额口径影子短文") or "").strip()
    compare = source.get("对照结果", {}) if isinstance(source, dict) else {}
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "shadow_v21_dry_run_dual_write",
        "来源": str(source_path),
        "股票": package.get("股票", {}),
        "正式短回复草稿": reply,
        "正式短回复长度": len(reply),
        "shadow_v21正式成交额口径短文": shadow_text,
        "shadow_v21短文长度": len(shadow_text),
        "对照结果": compare,
        "准入结论": {
            "上游230存在": source_path.exists(),
            "230建议默认切换正式入口": compare.get("建议默认切换正式入口") is True,
            "230建议仅实现默认关闭dry_run双写": compare.get("建议仅实现默认关闭dry_run双写") is True,
            "本次是否替换正式短回复": False,
            "本次是否发送企业微信": False,
        },
        "实际动作": {
            "覆盖正式短回复": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }


def load_v21_template_text(root: Path) -> str:
    source = load_json(shadow_v21_source_path(root), {}) or {}
    return str(source.get("正式成交额口径影子短文") or "").strip()


def write_shadow_v21_dry_run(root: Path, package: dict[str, Any], reply: str, timestamp: str, name: str) -> dict[str, str]:
    shadow_package = build_shadow_v21_package(root, package, reply)
    output_dir = root / "03数据" / "231企业微信短回复shadow_v21_dry_run"
    log_dir = root / "04日志" / "企业微信短回复shadow_v21_dry_run"
    json_path = output_dir / f"企业微信单股短回复_shadow_v21_{name}_{timestamp}.json"
    latest_json = output_dir / "企业微信单股短回复_shadow_v21_最新.json"
    md_path = output_dir / f"企业微信单股短回复_shadow_v21_{name}_{timestamp}.md"
    latest_md = output_dir / "企业微信单股短回复_shadow_v21_最新.md"
    log_path = log_dir / f"stock-wework-single-brief-shadow-v21-{timestamp}.json"
    markdown = "\n".join([
        "# 企业微信单股短回复 shadow_v21 dry-run 对照包",
        "",
        "## 正式短回复草稿",
        "",
        shadow_package["正式短回复草稿"],
        "",
        "## shadow_v21正式成交额口径短文",
        "",
        shadow_package["shadow_v21正式成交额口径短文"],
        "",
        "## 准入结论",
        "",
        *[f"- {key}：{value}" for key, value in shadow_package["准入结论"].items()],
        "",
        "## 实际动作",
        "",
        *[f"- {key}：{value}" for key, value in shadow_package["实际动作"].items()],
        "",
    ])
    write_json(json_path, shadow_package)
    write_json(latest_json, shadow_package)
    write_text(md_path, markdown)
    write_text(latest_md, markdown)
    write_json(log_path, shadow_package)
    return {
        "json": str(json_path),
        "latest_json": str(latest_json),
        "md": str(md_path),
        "latest_md": str(latest_md),
        "log": str(log_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", default="新易盛")
    parser.add_argument(
        "--shadow-v21-dry-run",
        action="store_true",
        default=False,
        help="默认关闭；显式开启时额外写出shadow_v21正式成交额口径对照包，不替换正式短回复、不发送企业微信。",
    )
    parser.add_argument(
        "--use-v21-template-dry-run",
        action="store_true",
        default=False,
        help="默认关闭；显式开启时将本地24短回复草稿写为v21正式成交额口径，不发送企业微信。",
    )
    args = parser.parse_args()
    root = module_root()
    generated = generate_unified_reply(root, args.stock)
    original_reply = generated["短回复"]
    reply = original_reply
    template_mode = "default_unified_reply"
    if args.use_v21_template_dry_run:
        v21_reply = load_v21_template_text(root)
        if not v21_reply:
            raise RuntimeError("启用--use-v21-template-dry-run失败：缺少230正式成交额口径影子短文")
        reply = limit_text(v21_reply)
        template_mode = "v21_template_dry_run"
    package = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "模式": "dry_run_reply_brief_only",
        "模板模式": template_mode,
        "模板来源": str(root / "01配置" / "股票前台输出标准_v2.json"),
        "v21模板来源": str(shadow_v21_source_path(root)) if args.use_v21_template_dry_run else "",
        "统一入口": str(root / "02脚本" / "股票助手入口.py"),
        "股票": generated.get("股票", {}),
        "短回复": reply,
        "短回复长度": len(reply),
        "旧统一短回复": original_reply if args.use_v21_template_dry_run else "",
        "单股报告": {
            "标准报告v2路径": generated.get("标准报告v2路径", ""),
        },
        "股票助手结果": generated.get("股票助手结果", {}),
        "实际动作": {
            "联网": False,
            "触发n8n": False,
            "发送企业微信": False,
            "写旧系统": False,
            "写正式库": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    output_dir = root / "03数据" / "24企业微信短回复"
    log_dir = root / "04日志" / "企业微信短回复"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"{package['股票'].get('名称', args.stock)}_{package['股票'].get('代码', '')}".replace("/", "")
    json_path = output_dir / f"企业微信单股短回复_{name}_最新.json"
    latest_json = output_dir / "企业微信单股短回复_最新.json"
    md_path = output_dir / f"企业微信单股短回复_{name}_最新.md"
    latest_md = output_dir / "企业微信单股短回复_最新.md"
    log_path = log_dir / "stock-wework-single-brief-reply-generate-最新.json"
    write_json(json_path, package)
    write_json(latest_json, package)
    write_text(md_path, "# 企业微信单股短回复草稿\n\n" + reply)
    write_text(latest_md, "# 企业微信单股短回复草稿\n\n" + reply)
    write_json(log_path, package)
    result = {"股票": package["股票"].get("名称"), "长度": len(reply), "输出": str(latest_md)}
    if args.shadow_v21_dry_run:
        result["shadow_v21_dry_run"] = write_shadow_v21_dry_run(root, package, reply, timestamp, name)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
