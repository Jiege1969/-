# -*- coding: utf-8 -*-
"""
名称：税收人工入口资料下载闸口.py
作用：读取最新待下载清单和下载选择模板，默认只生成下载申请单；只有显式传入--confirm-download YES且已勾选条目，才调用下载器执行小批量下载。
触发方式：
  python 税收人工入口资料下载闸口.py
  python 税收人工入口资料下载闸口.py --confirm-download YES --max-files 5
依赖：Python标准库；税收人工入口资料下载器.py；税收人工入口资料下载器配置.json；税收人工入口资料待下载清单_最新.json；税收人工入口资料下载选择模板_最新.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：默认不下载；确认参数不为YES时只生成申请单；下载仍只进预演目录，不进正式政策目录、不写向量库、不触发n8n、不推送企微、不标记正式依据。
创建/修改记录：2026-04-30 创建人工入口资料下载闸口脚本。
标识：tax-manual-url-download-gate
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def selected_items_from_template(selection: dict[str, Any]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for item in selection.get("选择区", []):
        if item.get("选择下载") is True:
            selected.append(
                {
                    "序号": len(selected) + 1,
                    "标题": item.get("标题", ""),
                    "链接": item.get("链接", ""),
                    "域名": item.get("域名", ""),
                    "后缀": item.get("后缀", ""),
                    "入选原因": item.get("入选原因", "人工勾选"),
                    "允许下载": True,
                    "正式依据状态": "不得自动标记，待人工复核",
                    "人工备注": item.get("人工备注", "")
                }
            )
    return selected


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# 税收人工入口资料下载申请单",
        "",
        f"生成时间：{report['生成时间']}",
        f"入口网址：{report['入口网址']}",
        f"候选数量：{report['候选数量']}",
        f"已勾选下载数量：{report['已勾选下载数量']}",
        f"选择模板状态：{report['选择模板状态']}",
        f"本次最大下载数量：{report['本次最大下载数量']}",
        f"是否允许执行下载：{report['是否允许执行下载']}",
        f"当前结论：{report['当前结论']}",
        "",
        "## 候选资料",
        "",
    ]
    for item in report.get("候选资料预览", []):
        lines.append(f"- {item.get('序号')}：{item.get('标题')}；{item.get('链接')}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_application(config: dict[str, Any], manifest: dict[str, Any], selected: list[dict[str, Any]], selection_status: str, max_files: int, confirmed: bool) -> dict[str, Any]:
    candidates = list(manifest.get("候选资料", []))
    selected_preview = selected[:max_files]
    if selection_status != "匹配当前清单":
        conclusion = f"选择模板状态为{selection_status}，拒绝下载；请重新生成选择模板并逐项勾选。"
        allowed = False
    elif confirmed and not selected_preview:
        conclusion = "已收到确认参数，但未勾选任何下载条目，拒绝下载。"
        allowed = False
    elif confirmed:
        conclusion = "已确认且存在人工勾选条目，可调用下载器执行小批量预演下载。"
        allowed = True
    else:
        conclusion = "未收到显式确认，只生成申请单，不执行下载。"
        allowed = False
    return {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "入口网址": manifest.get("入口网址", ""),
        "来源清单生成时间": manifest.get("生成时间", ""),
        "候选数量": len(candidates),
        "已勾选下载数量": len(selected),
        "选择模板状态": selection_status,
        "本次最大下载数量": max_files,
        "是否允许执行下载": allowed,
        "当前结论": conclusion,
        "候选资料预览": selected_preview if selected_preview else candidates[:max_files],
        "是否写入正式政策目录": False,
        "是否写入向量库": False,
        "是否触发n8n": False,
        "是否企业微信真实发送": False,
        "是否标记正式依据": False,
        "安全边界": config.get("安全边界", {})
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-download", default="", help="必须填写YES才会执行下载。")
    parser.add_argument("--max-files", type=int, default=0, help="本次最大下载数量，默认使用配置。")
    args = parser.parse_args()
    root = module_root()
    config = load_json(root / "01配置" / "税收人工入口资料下载器配置.json")
    output_dir = root / config["输出"]["数据目录"]
    manifest_path = output_dir / config["输出"]["清单最新文件"]
    if not manifest_path.exists():
        print(json.dumps({"错误": "未找到待下载清单，请先运行税收人工入口资料清单一键生成.py", "清单": str(manifest_path)}, ensure_ascii=False))
        return 1
    manifest = load_json(manifest_path)
    selection_path = output_dir / config["输出"].get("下载选择模板最新文件", "税收人工入口资料下载选择模板_最新.json")
    if selection_path.exists():
        selection = load_json(selection_path)
    else:
        selection = {"选择区": []}
    if not selection_path.exists():
        selection_status = "不存在"
        selected = []
    elif str(selection.get("入口网址", "")) != str(manifest.get("入口网址", "")):
        selection_status = "与当前清单不匹配"
        selected = []
    else:
        selection_status = "匹配当前清单"
        selected = selected_items_from_template(selection)
    max_files = args.max_files or int(config.get("下载策略", {}).get("默认最大下载数量", 10))
    confirmed = args.confirm_download == "YES"
    application = build_application(config, manifest, selected=selected, selection_status=selection_status, max_files=max_files, confirmed=confirmed)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    app_json = output_dir / f"税收人工入口资料下载申请单_{stamp}.json"
    app_latest_json = output_dir / "税收人工入口资料下载申请单_最新.json"
    app_md = output_dir / f"税收人工入口资料下载申请单_{stamp}.md"
    app_latest_md = output_dir / "税收人工入口资料下载申请单_最新.md"
    write_json(app_json, application)
    write_json(app_latest_json, application)
    write_markdown(app_md, application)
    write_markdown(app_latest_md, application)
    if not application["是否允许执行下载"]:
        print(json.dumps({"是否执行下载": False, "申请单": str(app_latest_md)}, ensure_ascii=False))
        return 0
    entry_url = str(manifest.get("入口网址", ""))
    if not entry_url:
        print(json.dumps({"错误": "清单缺少入口网址，拒绝下载", "申请单": str(app_latest_md)}, ensure_ascii=False))
        return 2
    downloader = root / "02脚本" / "税收人工入口资料下载器.py"
    selected_manifest = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "入口网址": manifest.get("入口网址", ""),
        "最终网址": manifest.get("最终网址", manifest.get("入口网址", "")),
        "页面标题": manifest.get("页面标题", ""),
        "候选资料": selected[:max_files],
        "候选数量": len(selected[:max_files]),
        "是否执行下载": True,
        "来源": "税收人工入口资料下载闸口已勾选清单",
        "是否写入正式政策目录": False,
        "是否写入向量库": False,
        "是否触发n8n": False,
        "是否企业微信真实发送": False,
        "是否标记正式依据": False,
        "安全边界": config.get("安全边界", {})
    }
    selected_manifest_path = output_dir / "税收人工入口资料待下载清单_已选择_最新.json"
    write_json(selected_manifest_path, selected_manifest)
    run = subprocess.run(
        [sys.executable, str(downloader), "--manifest", str(selected_manifest_path), "--download", "--max-files", str(max_files)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    print(run.stdout.strip() or run.stderr.strip())
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
