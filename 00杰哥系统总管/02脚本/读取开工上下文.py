# -*- coding: utf-8 -*-
"""读取开工上下文。

只读读取开工上下文索引，生成继续施工前摘要。
不删除、不覆盖业务文件、不重启服务、不触发 n8n、不发送企业微信。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


MANAGER = Path(__file__).resolve().parents[1]
INDEX = MANAGER / "01配置" / "开工上下文索引.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_head(path: Path, limit: int = 1200) -> str:
    if not path.exists():
        return "文件不存在"
    return path.read_text(encoding="utf-8-sig", errors="replace")[:limit].strip()


def file_info(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    exists = path.exists()
    return {
        "路径": path_text,
        "存在": exists,
        "大小": path.stat().st_size if exists else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if exists else "",
        "摘要": read_head(path) if exists and path.suffix.lower() in {".md", ".txt"} else "",
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# 开工上下文摘要",
        "",
        f"生成时间：{report['生成时间']}",
        "",
        "## 开工提醒",
        "",
    ]
    for item in report["开工提醒"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 收工检查项", ""])
    for item in report["收工检查项"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 必读文件状态", ""])
    for item in report["必读文件"]:
        status = "存在" if item["存在"] else "缺失"
        lines.append(f"- {status}：{item['路径']}")
    lines.extend(["", "## 重点状态文件", ""])
    for item in report["重点状态文件"]:
        status = "存在" if item["存在"] else "缺失"
        lines.append(f"- {status}：{item['路径']}")
    lines.extend(["", "## 安全边界", ""])
    for key, value in report["安全边界"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def main() -> int:
    config = load_json(INDEX)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = {
        "生成时间": now,
        "索引文件": str(INDEX),
        "开工提醒": config.get("开工提醒", []),
        "收工检查项": config.get("收工检查项", []),
        "必读文件": [file_info(path) for path in config.get("必读文件", [])],
        "重点状态文件": [file_info(path) for path in config.get("重点状态文件", [])],
        "安全边界": config.get("安全边界", {}),
    }
    data_dir = Path(config["输出"]["数据目录"])
    log_dir = Path(config["输出"]["日志目录"])
    latest_json = data_dir / "开工上下文摘要_最新.json"
    latest_md = data_dir / "开工上下文摘要_最新.md"
    latest_log = log_dir / "start-context-read-最新.json"
    write_json(latest_json, report)
    write_json(latest_log, report)
    text = build_markdown(report)
    write_text(latest_md, text)
    missing = [item["路径"] for item in report["必读文件"] + report["重点状态文件"] if not item["存在"]]
    print(json.dumps({"必读文件": len(report["必读文件"]), "重点状态文件": len(report["重点状态文件"]), "缺失": len(missing), "输出": str(latest_json)}, ensure_ascii=False))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
