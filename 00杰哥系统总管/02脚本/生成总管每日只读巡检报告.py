# -*- coding: utf-8 -*-
"""
名称：生成总管每日只读巡检报告.py
作用：只读检查总管配置JSON、关键最新文件和股票阶段性交付状态。
触发方式：python 生成总管每日只读巡检报告.py
所属系统：00杰哥系统总管
安全边界：只读检查并写00总管巡检报告；不触发服务、不发送企业微信、不调用外部接口、不改子系统业务逻辑。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "00杰哥系统总管"
OUT_DIR = MANAGER / "03数据" / "运行状态"
REPORT_JSON = OUT_DIR / "总管每日只读巡检报告_最新.json"
REPORT_MD = OUT_DIR / "总管每日只读巡检报告_最新.md"

CONFIG_FILES = [
    MANAGER / "01配置" / "进度口径规则.json",
    MANAGER / "01配置" / "进度回答标准.json",
    MANAGER / "01配置" / "四大系统验收读取口径.json",
    MANAGER / "01配置" / "各对话框并行施工汇总规则.json",
]
KEY_FILES = [
    ROOT / "杰哥智能化系统全盘架构说明_20260504.md",
    MANAGER / "07文档" / "当前施工面板.md",
    MANAGER / "03数据" / "开工上下文" / "一键接续施工包_最新.md",
    MANAGER / "03数据" / "运行状态" / "股票系统阶段性交付完成读取汇总_最新.md",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "242股票系统全权交付最终收口" / "股票系统全权交付最终收口报告验收_最新.md",
    ROOT / "02杰哥扩展系统" / "01股票研究系统" / "03数据" / "241股票企业微信单条真实灰度发送闭环" / "股票企业微信单条真实灰度发送闭环报告_最新.md",
]


def load_json_status(path: Path) -> dict[str, Any]:
    try:
        json.loads(path.read_text(encoding="utf-8-sig"))
        return {"路径": str(path), "存在": path.exists(), "可解析": True, "错误": ""}
    except Exception as exc:
        return {"路径": str(path), "存在": path.exists(), "可解析": False, "错误": str(exc)}


def file_status(path: Path) -> dict[str, Any]:
    exists = path.exists()
    return {
        "路径": str(path),
        "存在": exists,
        "大小": path.stat().st_size if exists else 0,
        "修改时间": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") if exists else "",
    }


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    config_results = [load_json_status(path) for path in CONFIG_FILES]
    file_results = [file_status(path) for path in KEY_FILES]
    stock_summary = read_text(MANAGER / "03数据" / "运行状态" / "股票系统阶段性交付完成读取汇总_最新.md")
    package_text = read_text(MANAGER / "03数据" / "开工上下文" / "一键接续施工包_最新.md")
    progress_text = read_text(MANAGER / "01配置" / "进度口径规则.json")
    stock_ok = all(
        token in (stock_summary + "\n" + package_text + "\n" + progress_text)
        for token in ["阶段性交付完成", "55-84小时", "45%-50%", "42%-50%", "16-28小时"]
    )
    failures = []
    failures.extend([item for item in config_results if not item["可解析"]])
    failures.extend([item for item in file_results if not item["存在"]])
    if not stock_ok:
        failures.append({"检查项": "股票阶段性交付完成口径", "通过": False})
    report = {
        "名称": "总管每日只读巡检报告",
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "结论": "通过" if not failures else "失败",
        "配置JSON检查": config_results,
        "关键文件检查": file_results,
        "股票阶段性交付完成口径仍有效": stock_ok,
        "失败数量": len(failures),
        "失败项": failures,
        "安全边界": {
            "修改股票系统核心脚本": False,
            "修改知识库业务逻辑": False,
            "修改进化系统规则代码": False,
            "触发n8n": False,
            "发送企业微信": False,
            "调用外部正式发送接口": False,
            "调用券商接口": False,
            "自动交易": False,
        },
    }
    lines = [
        "# 总管每日只读巡检报告",
        "",
        f"- 生成时间：{report['生成时间']}",
        f"- 结论：{report['结论']}",
        f"- 配置 JSON 数量：{len(config_results)}，可解析：{sum(1 for item in config_results if item['可解析'])}",
        f"- 关键文件数量：{len(file_results)}，存在：{sum(1 for item in file_results if item['存在'])}",
        f"- 股票阶段性交付完成口径仍有效：{stock_ok}",
        f"- 失败数量：{len(failures)}",
        "",
        "## 配置 JSON 检查",
        "",
    ]
    for item in config_results:
        status = "通过" if item["可解析"] else "失败"
        lines.append(f"- {Path(item['路径']).name}：{status}")
    lines.extend(["", "## 关键文件检查", ""])
    for item in file_results:
        status = "存在" if item["存在"] else "缺失"
        lines.append(f"- {status}：{item['路径']}")
    lines.extend(["", "## 安全边界", "", "本轮只读巡检并写总管报告；未触发 n8n，未发送企业微信，未调用外部正式发送接口，未调用券商接口，未自动交易。"])
    write_json(REPORT_JSON, report)
    write_text(REPORT_MD, "\n".join(lines))
    print(json.dumps({"状态": report["结论"], "失败数量": len(failures), "报告": str(REPORT_MD)}, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
