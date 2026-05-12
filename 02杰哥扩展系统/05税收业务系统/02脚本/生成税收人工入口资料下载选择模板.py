# -*- coding: utf-8 -*-
"""
名称：生成税收人工入口资料下载选择模板.py
作用：基于最新待下载清单生成逐项勾选模板；默认全部不选择，人工将“选择下载”改为true后，下载闸口才允许下载。
触发方式：python 生成税收人工入口资料下载选择模板.py
依赖：Python标准库；税收人工入口资料下载器配置.json；税收人工入口资料待下载清单_最新.json。
所属系统：02杰哥扩展系统/05税收业务系统
安全边界：只生成选择模板；不联网、不下载、不入库、不触发n8n、不推送企微、不标记正式依据。
创建/修改记录：2026-04-30 创建人工入口资料下载选择模板脚本。
标识：tax-manual-url-download-selection-template-generate
"""

from __future__ import annotations

import json
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


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(selection: dict[str, Any]) -> str:
    lines = [
        "# 税收人工入口资料下载选择模板",
        "",
        f"生成时间：{selection['生成时间']}",
        f"入口网址：{selection['入口网址']}",
        f"候选数量：{selection['候选数量']}",
        "",
        "## 使用方式",
        "",
        "打开同名 JSON 文件，把需要下载条目的 `选择下载` 从 false 改成 true。",
        "未勾选任何条目时，下载闸口即使收到确认参数也会拒绝下载。",
        "",
        "## 候选资料",
        "",
    ]
    for item in selection.get("选择区", []):
        lines.append(f"- {item['序号']}：{item['标题']}；选择下载：{item['选择下载']}")
        lines.append(f"  - 链接：{item['链接']}")
        lines.append(f"  - 备注：{item['人工备注']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in selection.get("安全边界", {}).items():
        lines.append(f"- {key}：{value}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    root = module_root()
    config = load_json(root / "01配置" / "税收人工入口资料下载器配置.json")
    output_dir = root / config["输出"]["数据目录"]
    manifest_path = output_dir / config["输出"]["清单最新文件"]
    if not manifest_path.exists():
        print(json.dumps({"错误": "未找到待下载清单，请先生成清单", "清单": str(manifest_path)}, ensure_ascii=False))
        return 1
    manifest = load_json(manifest_path)
    rows = []
    for item in manifest.get("候选资料", []):
        rows.append(
            {
                "序号": item.get("序号"),
                "标题": item.get("标题", ""),
                "链接": item.get("链接", ""),
                "域名": item.get("域名", ""),
                "后缀": item.get("后缀", ""),
                "入选原因": item.get("入选原因", ""),
                "选择下载": False,
                "人工备注": ""
            }
        )
    selection = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "来源清单": str(manifest_path),
        "入口网址": manifest.get("入口网址", ""),
        "候选数量": len(rows),
        "已选择数量": 0,
        "选择区": rows,
        "是否执行下载": False,
        "安全边界": config.get("安全边界", {})
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_json = output_dir / config["输出"]["下载选择模板最新文件"]
    dated_json = output_dir / f"税收人工入口资料下载选择模板_{stamp}.json"
    latest_md = output_dir / config["输出"]["下载选择模板Markdown最新文件"]
    dated_md = output_dir / f"税收人工入口资料下载选择模板_{stamp}.md"
    write_json(dated_json, selection)
    write_json(latest_json, selection)
    markdown = build_markdown(selection)
    write_text(dated_md, markdown)
    write_text(latest_md, markdown)
    print(json.dumps({"候选数量": len(rows), "已选择数量": 0, "输出": str(latest_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
